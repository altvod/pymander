class CantParseLine(Exception):
    pass


class SkipExecution(Exception):
    pass


class ExitContext(Exception):
    pass


class ExitMainloop(Exception):
    pass


__all__ = [CantParseLine, SkipExecution, ExitContext, ExitMainloop]
