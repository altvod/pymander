from .contexts import StandardPrompt
from .commander import Commander


def run_with_context(context):
    Commander(context).mainloop()


def run_with_handler(handler):
    run_with_context(StandardPrompt([handler]))
