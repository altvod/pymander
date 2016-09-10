import sys

from .exceptions import ExitMainloop, ExitContext
from .contexts import CommandContext


__all__ = ('Commander',)


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

    def read_and_execute(self):
        self.context.prompt()
        line = self.in_stream.readline()
        self.execute(line)

    def mainloop(self):
        """Main commander loop: read lines and interpret them."""
        while True:
            try:
                self.read_and_execute()

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
