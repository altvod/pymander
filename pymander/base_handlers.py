import abc
import argparse
import inspect
import re

from .exceptions import CantParseLine, SkipExecution


__all__ = (
    'LineHandler', 'RegexLineHandler', 'ExactLineHandler', 'ArgparseLineHandler',
)


class LineHandler(metaclass=abc.ABCMeta):
    def __init__(self):
        self.context = None
        self.command_methods = []
        methods = inspect.getmembers(self.__class__, predicate=inspect.isfunction)
        for method_tuple in methods:
            method = method_tuple[1]
            if getattr(method, '_bound_command', False):
                self.command_methods.append(
                    {'method': method, 'args': method._args, 'kwargs': method._kwargs}
                )

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
                self.command_methods.append(
                    {'method': method, 'args': (expr,), 'kwargs': {}}
                )
                return method

            return decorator

    registry = Registry()

    def __init__(self):
        super().__init__()
        self.command_methods += self.registry.command_methods

    def try_execute(self, line):
        for command_info in self.command_methods:
            expr = command_info['args'][0]
            match = re.match(expr, line)
            if match:
                return command_info['method'](self, **match.groupdict())

        raise CantParseLine(line)


class ExactLineHandler(LineHandler):
    """Matches line to exact expressions."""

    class Registry:
        def __init__(self):
            self.command_methods = []

        def bind(self, expr):
            def decorator(method):
                self.command_methods.append(
                    {'method': method, 'args': (expr,), 'kwargs': {}}
                )
                return method

            return decorator

    registry = Registry()

    def __init__(self):
        super().__init__()
        self.command_methods += self.registry.command_methods

    def try_execute(self, line):
        for command_info in self.command_methods:
            expr = command_info['args'][0]
            if line.strip() == expr:
                return command_info['method'](self)

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
                self.command_methods.append(
                    {'method': method, 'args': (command, options), 'kwargs': {'help': help}}
                )
                return method

            return decorator

    registry = Registry()

    def __init__(self):
        super().__init__()
        self.command_methods += self.registry.command_methods

        self.handler = ArgumentParserWrapper(prog='')
        for option, option_args in self.common_options.items():
            if not isinstance(option, tuple):
                option = (option,)
            self.handler.add_argument(*option, **option_args)

        subparsers = self.handler.add_subparsers()
        for command_info in self.command_methods:
            command, options = command_info['args'][0], {}
            if len(command_info['args']) > 1:
                options = command_info['args'][1]
            help = command_info['kwargs'].get('help', '')
            subparser = subparsers.add_parser(
                command, allow_help=True, line_handler=self, help=help
            )
            subparser.set_defaults(_command_method=command_info['method'])
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
