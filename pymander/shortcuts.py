from .contexts import StandardPrompt
from .commander import Commander


__all__ = ('Commander', 'run_with_context', 'run_with_handler')


def run_with_context(context):
    Commander(context).mainloop()


def run_with_handler(handler):
    run_with_context(StandardPrompt([handler]))
