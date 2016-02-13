import abc
import argparse
import copy
import json
import re
import sys


class CantParseLine(Exception):
    pass


class SkipExecution(Exception):
    pass


class ExitContext(Exception):
    pass


class ExitMainloop(Exception):
    pass


class LineHandler(metaclass=abc.ABCMeta):
    def __init__(self):
        self.context = None

    def set_context(self, context):
        self.context = context

    @abc.abstractmethod
    def try_execute(self, line):
        """Try to parse and execute a command. Must raise CantParseLine if the command is unacceptable"""
        raise NotImplementedError

    def clone(self):
        return self.__class__()


class RegexLineHandler(LineHandler):
    """Interprets commands via matching to regular expressions."""
    command_methods = []

    class Registry:
        command_methods = []

        @classmethod
        def bind(cls, expr):
            if not cls.command_methods:
                # redefine cls.command_methods so that this list is independent of the superclass's
                cls.command_methods = []

            def decorator(method):
                cls.command_methods.append([expr, method])
                return method

            return decorator

    def __init__(self):
        super().__init__()
        self.registry = self.Registry()

    def try_execute(self, line):
        for expr, method in self.registry.command_methods:
            match = re.match(expr, line)
            if match:
                return method(self, **match.groupdict())

        raise CantParseLine(line)


class ArgumentParserWrapper(argparse.ArgumentParser):
    """Just a helper class for ArgparseLineHandler."""
    def __init__(self, *args, **kwargs):
        self.line_handler = kwargs.pop('line_handler', None)
        self.allow_help = kwargs.pop('allow_help', False)
        super().__init__(*args, **kwargs)

    def exit(self, *args, **kwargs):
        raise SkipExecution

    def error(self, *args, **kwargs):
        raise CantParseLine

    def print_usage(self, *args, **kwargs):
        if not self.allow_help:
            raise CantParseLine

        if self.line_handler:
            super().print_usage(file=self.line_handler.context.out_stream)

    def print_help(self, *args, **kwargs):
        if not self.allow_help:
            raise CantParseLine

        if self.line_handler:
            super().print_help(file=self.line_handler.context.out_stream)


class ArgparseLineHandler(LineHandler):
    """Interprets commands via the standard argparse tool."""
    common_options = {}

    class Registry:
        command_methods = []

        @classmethod
        def bind(cls, command, options=None):
            options = options or {}
            if not cls.command_methods:
                # redefine cls.command_methods so that this list is independent of the superclass's
                cls.command_methods = []

            def decorator(method):
                cls.command_methods.append([method, command, options])
                return method

            return decorator

    def __init__(self):
        super().__init__()
        self.registry = self.Registry()

        self.handler = ArgumentParserWrapper(prog='')
        for option, option_args in self.common_options.items():
            if not isinstance(option, tuple):
                option = (option,)
            self.handler.add_argument(*option, **option_args)

        subparsers = self.handler.add_subparsers()
        for method, command, options in self.registry.command_methods:
            subparser = subparsers.add_parser(
                command, allow_help=True, line_handler=self, help=options.get('help', '')
            )
            subparser.set_defaults(_command_method=method)
            for option, option_args in options.items():
                if not isinstance(option, tuple):
                    option = (option,)
                subparser.add_argument(*option, **option_args)

    def try_execute(self, line):
        if not line.strip():
            raise CantParseLine

        try:
            args = self.handler.parse_args(line.split())
        except SkipExecution:
            return

        kwargs = vars(args).copy()
        kwargs.pop('_command_method')
        return args._command_method(self, **kwargs)


class ExitLineHandler(LineHandler):
    """Exits the context when an 'exit' command is received."""
    def try_execute(self, line):
        if line.strip() == 'exit':
            self.context.write('Bye!\n')
            self.context.exit()
            return

        raise CantParseLine(line)


class EmptyLineHandler(LineHandler):
    """Just ignores empty lines."""
    def try_execute(self, line):
        if line.strip():
            raise CantParseLine(line)


class EchoLineHandler(RegexLineHandler):
    """Imitates the 'echo' shell command."""
    class Registry(RegexLineHandler.Registry):
        pass

    @Registry.bind(r'^echo (?P<what>.*)\n?')
    def echo(self, what):
        self.context.write('{0}\n'.format(what))


class CommandContext(metaclass=abc.ABCMeta):
    default_handlers = []
    force_handlers = []

    def __init__(self, handlers=None, name='', ignore_force_handlers=False):
        # cosntruct handler list
        self.handlers = copy.copy(handlers) or [handler_class() for handler_class in self.default_handlers]
        if not ignore_force_handlers:
            self.handlers += [handler_class() for handler_class in self.force_handlers]

        self.name = name
        self.out_stream = None

        for handler in self.handlers:
            handler.set_context(self)

    def set_out_stream(self, out_stream):
        self.out_stream = out_stream

    def execute(self, line):
        """
        Try to interpret a line by applying every handler in the list until one succeeds.
        If none do, then execute the error handler self.on_cant_execute
        """
        for handler in self.handlers:
            try:
                return handler.try_execute(line)

            except CantParseLine:
                pass

        self.on_cant_execute(line)

    def write(self, text):
        """Write to the current output stream."""
        if self.out_stream:
            self.out_stream.write(text)
            self.out_stream.flush()

    def exit(self):
        raise ExitContext(self)

    def clone(self, *args, **kwargs):
        kwargs['ignore_force_handlers'] = True
        return self.__class__([handler.clone() for handler in self.handlers], *args, **kwargs)

    @abc.abstractmethod
    def prompt(self):
        raise NotImplementedError

    @abc.abstractmethod
    def on_cant_execute(self, line):
        raise NotImplementedError


class MultiLineContext(CommandContext):
    class FinishedHandler(LineHandler):
        @abc.abstractmethod
        def is_finished(self, line):
            raise NotImplementedError

        def try_execute(self, line):
            if self.is_finished(line):
                self.context.on_finished()

            else:
                self.context.to_buffer(line)

    class OverOn2EmptyLines(FinishedHandler):
        def __init__(self):
            super().__init__()
            self.empty_line_count = 0

        def is_finished(self, line):
            if not line.strip():
                self.empty_line_count += 1
                if self.empty_line_count > 1:
                    return True

            else:
                self.empty_line_count = 0

            return False

    def __init__(self, *args, **kwargs):
        self.force_handlers = [self.FinishedHandler]
        super().__init__(*args, **kwargs)
        self.buffer = ''

    def execute(self, line):
        super().execute(line)

    def to_buffer(self, line):
        self.buffer += line

    @abc.abstractmethod
    def on_finished(self):
        raise NotImplementedError


class JsonContext(MultiLineContext):
    FinishedHandler = MultiLineContext.OverOn2EmptyLines

    def __init__(self, *args, **kwargs):
        self.callback = kwargs.pop('callback', lambda data: None)
        self.error = kwargs.pop('error', lambda err: self.write('{0}\n'.format(str(err))))
        super().__init__(*args, **kwargs)

    def on_finished(self):
        try:
            data = json.loads(self.buffer)

        except ValueError as err:
            self.error(err)
            self.exit()
            return

        self.callback(data)
        self.exit()

    def prompt(self):
        self.write('... ')

    def on_cant_execute(self, line):
        pass


class StandardPrompt(CommandContext):
    force_handlers = [EmptyLineHandler, EchoLineHandler, ExitLineHandler]

    def prompt(self):
        if self.name:
            self.write('{0} > '.format(self.name))
        else:
            self.write('>>> ')

    def on_cant_execute(self, line):
        self.write('Invalid command: {0}'.format(line))


class PrebuiltCommandContext(CommandContext):
    class Registry:
        re_handler_class = RegexLineHandler
        ap_handler_class = ArgparseLineHandler
        re_handler_initialized = False
        ap_handler_initialized = False

        @classmethod
        def bind_regex(cls, regex):
            def decorator(method):
                if not cls.re_handler_initialized:
                    cls.re_handler_class = type('{0}_RegexLineHandler'.format(cls.__name__), (RegexLineHandler,), {})
                    cls.re_handler_class.Registry = type(
                        '{0}_RegexLineHandler_Registry'.format(cls.__name__), (RegexLineHandler.Registry,), {}
                    )
                    cls.re_handler_initialized = True

                def redirect_method(handler_self, *args, **kwargs):
                    return method(handler_self.context, *args, **kwargs)

                cls.re_handler_class.Registry.bind(regex)(redirect_method)

            return decorator

        @classmethod
        def bind_argparse(cls, command, options):
            def decorator(method):
                if not cls.ap_handler_initialized:
                    cls.ap_handler_class = type('{0}_ArgparseLineHandler'.format(cls.__name__), (ArgparseLineHandler,), {})
                    cls.ap_handler_class.Registry = type(
                        '{0}_ArgparseLineHandler_Registry'.format(cls.__name__), (ArgparseLineHandler.Registry,), {}
                    )
                    cls.ap_handler_initialized = True

                def redirect_method(handler_self, *args, **kwargs):
                    return method(handler_self.context, *args, **kwargs)

                cls.ap_handler_class.Registry.bind(command, options)(redirect_method)

            return decorator

    def __init__(self, handlers=None, name=''):
        self.re_handler = self.Registry.re_handler_class()
        self.ap_handler = self.Registry.ap_handler_class()
        handlers = copy.copy(handlers) or []
        handlers = handlers + [self.re_handler, self.ap_handler]
        super().__init__(handlers=handlers, name=name)


class Commander:
    """
    Main class that orchestrates everything:
        - reading from input in a loop
        - entering and exiting contexts
    """
    def __init__(self, context, in_stream=None, out_stream=None):
        self.context_stack = []
        self.in_stream = None
        self.out_stream = None

        self.set_streams(in_stream, out_stream)
        self.enter_context(context)

    @property
    def context(self):
        if self.context_stack:
            return self.context_stack[-1]

        return None

    def set_streams(self, in_stream=None, out_stream=None):
        self.in_stream = in_stream or self.in_stream or sys.stdin
        self.out_stream = out_stream or self.out_stream or sys.stdout
        for context in self.context_stack:
            context.set_out_stream(self.out_stream)

    def execute(self, line):
        try:
            result = self.context.execute(line)
            if isinstance(result, CommandContext):
                # the command requested to enter a new context by returning its instance
                self.enter_context(result)

        except ExitContext:
            self.exit_current_context()

    def mainloop(self):
        """Main commander loop: read lines and interpret them."""
        while True:
            try:
                self.context.prompt()
                line = self.in_stream.readline()
                self.execute(line)

            except ExitMainloop:
                break

    def write(self, text):
        self.out_stream.write(text)

    def enter_context(self, context):
        context.set_out_stream(self.out_stream)
        self.context_stack.append(context)

    def exit_current_context(self):
        if len(self.context_stack) == 1:
            raise ExitMainloop

        self.context_stack.pop()


# shortcut functions ##################################

def run_with_context(context):
    Commander(context).mainloop()


def run_with_handler(handler):
    Commander(StandardPrompt([handler])).mainloop()
