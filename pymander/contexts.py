import abc
import copy
import json

from .exceptions import CantParseLine, ExitContext
from .handlers import LineHandler, EmptyLineHandler, EchoLineHandler, ExitLineHandler, \
    ExactLineHandler, ArgparseLineHandler, RegexLineHandler


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
        if self.out_stream:
            if self.name:
                self.out_stream.write('{0} > '.format(self.name))
            else:
                self.out_stream.write('>>> ')
            self.out_stream.flush()

    def on_cant_execute(self, line):
        self.write('Invalid command: {0}'.format(line))


class PrebuiltCommandContext(CommandContext):
    class Registry:
        bound_handler_classes = {}

        @classmethod
        def bind_to_handler(cls, handler_cls, *bind_args):
            """Bind the context's method to a LineParser class with a nested Registry class."""
            def decorator(method):
                if not cls.bound_handler_classes:
                    # re-initialize cls.cls.bound_handler_classes so that it's independent of the superclass's
                    cls.bound_handler_classes = {}

                own_cls_name = cls.__name__
                handler_cls_name = handler_cls.__name__
                # add handler class to cls.bound_handler_classes not added already
                if handler_cls_name not in cls.bound_handler_classes:
                    cls.bound_handler_classes[handler_cls_name] = type(
                        '{0}.{1}'.format(own_cls_name, handler_cls_name), (handler_cls,), {}
                    )
                    cls.bound_handler_classes[handler_cls_name].Registry = type(
                        '{0}.{1}.Registry'.format(own_cls_name, handler_cls_name), (handler_cls.Registry,), {}
                    )

                def redirect_method(handler_self, *args, **kwargs):
                    return method(handler_self.context, *args, **kwargs)

                cls.bound_handler_classes[handler_cls_name].Registry.bind(*bind_args)(redirect_method)

            return decorator

        @classmethod
        def bind_exact(cls, *bind_args):
            return cls.bind_to_handler(ExactLineHandler, *bind_args)

        @classmethod
        def bind_regex(cls, *bind_args):
            return cls.bind_to_handler(RegexLineHandler, *bind_args)

        @classmethod
        def bind_argparse(cls, *bind_args):
            return cls.bind_to_handler(ArgparseLineHandler, *bind_args)

    def __init__(self, handlers=None, name=''):
        handlers = copy.copy(handlers) or []
        handlers = handlers + [
            handler_class() for handler_class in self.Registry.bound_handler_classes.values()
        ]
        super().__init__(handlers=handlers, name=name)
