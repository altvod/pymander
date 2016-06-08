from unittest import TestCase

from pymander.contexts import CommandContext
from pymander.handlers import LineHandler
from pymander.exceptions import CantParseLine, ExitContext


class FuncLineHandler(LineHandler):
    def __init__(self, func):
        super().__init__()
        self.func = func

    def try_execute(self, line):
        return self.func(line)


class SimpleStream:
    def write(self, line):
        pass


class CantExecute(Exception):
    pass


class DummyCommandContext(CommandContext):
    def prompt(self):
        pass

    def on_cant_execute(self, line):
        raise CantExecute


class DummyOutStream:
    def __init__(self):
        self.written = False
        self.flushed = False

    def write(self, line):
        self.written = True

    def flush(self):
        self.flushed = True


def _pass(*args, **kwargs):
    pass

def _raise(*args, **kwargs):
    raise CantParseLine


class CommandContextCase(TestCase):
    def test_execute(self):
        # check successful execution
        ctx = DummyCommandContext(handlers=[
            FuncLineHandler(_pass),
            FuncLineHandler(_pass),
        ])
        ctx.execute('qwerty')

        ctx = DummyCommandContext(handlers=[
            FuncLineHandler(_raise),
            FuncLineHandler(_pass),
        ])
        ctx.execute('qwerty')

        # check unsuccessful execution
        ctx = DummyCommandContext(handlers=[
            FuncLineHandler(_raise),
            FuncLineHandler(_raise),
        ])
        with self.assertRaises(CantExecute):
            ctx.execute('qwerty')

    def test_exit(self):
        ctx = DummyCommandContext()
        with self.assertRaises(ExitContext):
            ctx.exit()

    def test_write(self):
        ctx = DummyCommandContext()
        stream = DummyOutStream()
        ctx.set_out_stream(stream)

        ctx.write('')
        self.assertTrue(stream.written, 'Not written')
        self.assertTrue(stream.flushed, 'Not flushed')
