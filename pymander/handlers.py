import abc
import argparse
import re

from .exceptions import CantParseLine, SkipExecution


__all__ = ['LineHandler', 'RegexLineHandler', 'ExactLineHandler', 'ArgparseLineHandler',
           'ExitLineHandler', 'EmptyLineHandler', 'EchoLineHandler']


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

    class Registry:
        def __init__(self):
            self.command_methods = []

        def bind(self, expr):
            def decorator(method):
                self.command_methods.append([expr, method])
                return method

            return decorator

    registry = Registry()

    def __init__(self):
        super().__init__()

    def try_execute(self, line):
        for expr, method in self.registry.command_methods:
            match = re.match(expr, line)
            if match:
                return method(self, **match.groupdict())

        raise CantParseLine(line)


class ExactLineHandler(LineHandler):
    """Matches line to exact expressions."""

    class Registry:
        def __init__(self):
            self.command_methods = []

        def bind(self, expr):
            def decorator(method):
                self.command_methods.append([expr, method])
                return method

            return decorator

    registry = Registry()

    def __init__(self):
        super().__init__()

    def try_execute(self, line):
        for expr, method in self.registry.command_methods:
            if line.strip() == expr:
                return method(self)

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
        def __init__(self):
            self.command_methods = []

        def bind(self, command, options=None, help=''):
            options = options or ()

            def decorator(method):
                self.command_methods.append([method, command, options, help])
                return method

            return decorator

    registry = Registry()

    def __init__(self):
        super().__init__()

        self.handler = ArgumentParserWrapper(prog='')
        for option, option_args in self.common_options.items():
            if not isinstance(option, tuple):
                option = (option,)
            self.handler.add_argument(*option, **option_args)

        subparsers = self.handler.add_subparsers()
        for method, command, options, help in self.registry.command_methods:
            subparser = subparsers.add_parser(
                command, allow_help=True, line_handler=self, help=help
            )
            subparser.set_defaults(_command_method=method)
            for option in options:
                if isinstance(option, str):
                    option = (option,)
                option_args = [item for item in option if isinstance(item, str)]
                option_kwargs_l = [item for item in option if isinstance(item, dict)]
                option_kwargs = option_kwargs_l[0] if option_kwargs_l else {}
                subparser.add_argument(*option_args, **option_kwargs)

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


class ExitLineHandler(ExactLineHandler):
    """Exits the context when an 'exit' command is received."""
    registry = ExactLineHandler.Registry()

    @registry.bind('exit')
    def exit(self):
        self.context.write('Bye!\n')
        self.context.exit()


class EmptyLineHandler(LineHandler):
    """Just ignores empty lines."""
    def try_execute(self, line):
        if line.strip():
            raise CantParseLine(line)


class EchoLineHandler(RegexLineHandler):
    """Imitates the 'echo' shell command."""
    registry = RegexLineHandler.Registry()

    @registry.bind(r'^echo (?P<what>.*)\n?')
    def echo(self, what):
        self.context.write('{0}\n'.format(what))
