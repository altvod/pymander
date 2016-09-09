
def bind_command(*args, **kwargs):
    def decorator(method):
        method._bound_command = True
        method._args = args
        method._kwargs = kwargs
        return method

    return decorator
