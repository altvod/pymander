from pymander.exceptions import CantParseLine
from pymander.handlers import LineHandler, RegexLineHandler, ArgparseLineHandler
from pymander.contexts import StandardPrompt
from pymander.commander import Commander
from pymander.decorators import bind_command


class DeeperLineHandler(LineHandler):
    def try_execute(self, line):
        if line.strip() == 'deeper':
            deeper_context = self.context.clone()
            deeper_context.name = '{0} / ctx {1}'.format(self.context.name, id(deeper_context))
            self.context.write('Going deeper!\nNow in: {0}\n'.format(deeper_context))
            return deeper_context

        raise CantParseLine(line)


class RaynorLineHandler(LineHandler):
    def try_execute(self, line):
        if line.strip() == 'kerrigan':
            self.context.write('Oh, Sarah...\n')
            return

        raise CantParseLine(line)


class BerryLineHandler(RegexLineHandler):
    @bind_command(r'pick a (?P<berry_kind>\w+)')
    def pick_berry(self, berry_kind):
        self.context.write('Picked a {0}\n'.format(berry_kind))

    @bind_command(r'make (?P<berry_kind>\w+) jam')
    def make_jam(self, berry_kind):
        self.context.write('Made some {0} jam\n'.format(berry_kind))


class GameLineHandler(ArgparseLineHandler):
    @bind_command('play', [
        ['game', {'type': str, 'default': 'nothing'}],
        ['--well', {'action': 'store_true'}],
    ])
    def play(self, game, well):
        self.context.write('I play {0}{1}\n'.format(game, ' very well' if well else ''))

    @bind_command('win')
    def win(self):
        self.context.write('I just won!\n')


def main():
    com = Commander(
        StandardPrompt([
            DeeperLineHandler(),
            BerryLineHandler(),
            GameLineHandler(),
            RaynorLineHandler(),
        ])
    )
    com.mainloop()


if __name__ == '__main__':
    main()
