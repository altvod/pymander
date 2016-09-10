from .exceptions import CantParseLine, SkipExecution
from .base_handlers import LineHandler, RegexLineHandler, ExactLineHandler, ArgparseLineHandler

from . import decorators


__all__ = (
    'LineHandler', 'RegexLineHandler', 'ExactLineHandler', 'ArgparseLineHandler',
    'ExitLineHandler', 'EmptyLineHandler', 'EchoLineHandler'
)


class ExitLineHandler(ExactLineHandler):
    """Exits the context when an 'exit' command is received."""
    @decorators.bind_command('exit')
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
    @decorators.bind_command(r'^echo (?P<what>.*)\n?')
    def echo(self, what):
        self.context.write('{0}\n'.format(what))
