from pymander.contexts import PrebuiltCommandContext, StandardPrompt
from pymander.commander import Commander
from pymander.decorators import bind_argparse, bind_regex


class SaladContext(PrebuiltCommandContext, StandardPrompt):
    @bind_regex(r'(?P<do_what>eat|cook) caesar')
    def caesar_salad(self, do_what):
        self.write('{0}ing caesar salad...\n'.format(do_what.capitalize()))

    @bind_argparse('buy', [
        'kind_of_salad',
        ['--price', '-p', {'default': None}]
    ])
    def buy_salad(self, kind_of_salad, price):
        self.write('Buying {0} salad{1}...\n'.format(
            kind_of_salad, ' for {0}'.format(price) if price else '')
        )


def main():
    Commander(SaladContext()).mainloop()


if __name__ == '__main__':
    main()
