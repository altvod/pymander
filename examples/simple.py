from pymander import CantParseLine, LineHandler, RegexLineHandler, ArgparseLineHandler, \
    StandardPrompt, Commander


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
    class Registry(RegexLineHandler.Registry):
        pass

    @Registry.bind(r'pick a (?P<berry_kind>\w+)')
    def pick_berry(self, berry_kind):
        self.context.write('Picked a {0}\n'.format(berry_kind))

    @Registry.bind(r'make (?P<berry_kind>\w+) jam')
    def make_jam(self, berry_kind):
        self.context.write('Made some {0} jam\n'.format(berry_kind))


class GameLineHandler(ArgparseLineHandler):
    class Registry(ArgparseLineHandler.Registry):
        pass

    @Registry.bind('play', {
        'game': {'type': str, 'default': 'nothing'},
        '--well': {'action': 'store_true'},
    })
    def play(self, game, well):
        self.context.write('I play {0}{1}\n'.format(game, ' very well' if well else ''))

    @Registry.bind('win')
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
