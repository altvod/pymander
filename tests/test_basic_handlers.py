from unittest import TestCase

from pymander.exceptions import ExitContext, CantParseLine
from pymander.handlers import ExitLineHandler, EchoLineHandler, EmptyLineHandler, \
    ExactLineHandler, RegexLineHandler, ArgparseLineHandler


class FakeContext:
    def __init__(self):
        self.text = ''

    def clear(self):
        self.text = ''

    def write(self, text):
        self.text += text

    def exit(self):
        raise ExitContext


class SimpleLineHandlerCase(TestCase):
    handler_class = None

    def setUp(self):
        self.fake_context = FakeContext()
        self.handler = self.handler_class()
        self.handler.set_context(self.fake_context)


class ExitLineHandlerCase(SimpleLineHandlerCase):
    handler_class = ExitLineHandler

    def test_valid_command(self):
        with self.assertRaises(ExitContext):
            self.handler.try_execute('exit')

    def test_invalid_command(self):
        with self.assertRaises(CantParseLine):
            self.handler.try_execute('qwerty')


class EchoLineHandlerCase(SimpleLineHandlerCase):
    handler_class = EchoLineHandler

    def test_valid_command(self):
        self.handler.try_execute('echo qwerty uiop')
        self.assertEqual('qwerty uiop\n', self.fake_context.text)

    def test_invalid_command(self):
        with self.assertRaises(CantParseLine):
            self.handler.try_execute('qwerty')


class EmptyLineHandlerCase(SimpleLineHandlerCase):
    handler_class = EmptyLineHandler

    def test_valid_command(self):
        self.handler.try_execute('')
        self.handler.try_execute('   ')
        self.handler.try_execute('\t')

    def test_invalid_command(self):
        with self.assertRaises(CantParseLine):
            self.handler.try_execute('qwerty')


class ExactLineHandlerCase(SimpleLineHandlerCase):
    class TestExactLineHandler(ExactLineHandler):
        registry = ExactLineHandler.Registry()

        @registry.bind('do this')
        def do_this(self):
            self.context.write('This is done')

    handler_class = TestExactLineHandler

    def test_valid_command(self):
        self.handler.try_execute('do this')
        self.assertEqual('This is done', self.fake_context.text)

    def test_invalid_command(self):
        with self.assertRaises(CantParseLine):
            self.handler.try_execute('qwerty')


class RegexLineHandlerCase(SimpleLineHandlerCase):
    class TestRegexLineHandler(RegexLineHandler):
        registry = RegexLineHandler.Registry()

        @registry.bind('go to warp (?P<warp_factor>\d(\.\d+))')
        def go_to_warp(self, warp_factor):
            self.context.write('At warp {0}'.format(warp_factor))

        @registry.bind('(?P<action>raise|drop) shields')
        def manage_shields(self, action):
            self.context.write('Shields {0}'.format('raised' if action == 'raise' else 'dropped'))

    handler_class = TestRegexLineHandler

    def test_valid_command(self):
        self.handler.try_execute('go to warp 9.99')
        self.assertEqual('At warp 9.99', self.fake_context.text)

        self.fake_context.clear()
        self.handler.try_execute('raise shields')
        self.assertEqual('Shields raised', self.fake_context.text)

    def test_invalid_command(self):
        with self.assertRaises(CantParseLine):
            self.handler.try_execute('qwerty')

        with self.assertRaises(CantParseLine):
            self.handler.try_execute('remodulate shields')

        with self.assertRaises(CantParseLine):
            self.handler.try_execute('go to warp NaN')


class ArgparseLineHandlerCase(SimpleLineHandlerCase):
    class TestArgparseLineHandler(ArgparseLineHandler):
        registry = ArgparseLineHandler.Registry()

        @registry.bind('do', [['what'], ['--joy', {'action': 'store_true'}]])
        def do(self, what, joy):
            self.context.write('Doing {0}{1}'.format(what, ' with joy' if joy else ''))

    handler_class = TestArgparseLineHandler

    def test_valid_command(self):
        self.handler.try_execute('do chores')
        self.assertEqual('Doing chores', self.fake_context.text)

        self.fake_context.clear()
        self.handler.try_execute('do homework --joy')
        self.assertEqual('Doing homework with joy', self.fake_context.text)

    def test_invalid_command(self):
        with self.assertRaises(CantParseLine):
            self.handler.try_execute('qwerty')

        with self.assertRaises(CantParseLine):
            self.handler.try_execute('do')

        with self.assertRaises(CantParseLine):
            self.handler.try_execute('do something somethingelse')
