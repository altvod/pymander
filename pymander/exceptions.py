__all__ = ('CantParseLine', 'SkipExecution', 'ExitContext', 'ExitMainloop')


class CantParseLine(Exception):
    pass


class SkipExecution(Exception):
    pass


class ExitContext(Exception):
    pass


class ExitMainloop(Exception):
    pass
