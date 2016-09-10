from . import base_handlers


__all__ = (
    'bind_to_handler', 'bind_command', 'bind_exact', 'bind_regex', 'bind_argparse'
)


def bind_to_handler(handler_class, *args, **kwargs):
    def decorator(method):
        method._bound_command = True
        method._handler_class = handler_class
        method._args = args
        method._kwargs = kwargs
        return method

    return decorator


def bind_command(*args, **kwargs):
    return bind_to_handler(None, *args, **kwargs)


def bind_exact(*args, **kwargs):
    return bind_to_handler(base_handlers.ExactLineHandler, *args, **kwargs)


def bind_regex(*args, **kwargs):
    return bind_to_handler(base_handlers.RegexLineHandler, *args, **kwargs)


def bind_argparse(*args, **kwargs):
    return bind_to_handler(base_handlers.ArgparseLineHandler, *args, **kwargs)
