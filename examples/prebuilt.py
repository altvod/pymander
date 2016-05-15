from pymander import PrebuiltCommandContext, StandardPrompt, Commander


class SaladContext(PrebuiltCommandContext, StandardPrompt):
    registry = PrebuiltCommandContext.Registry()

    @registry.bind_regex(r'(?P<do_what>eat|cook) caesar')
    def caesar_salad(self, do_what):
        self.write('{0}ing caesar salad...\n'.format(do_what.capitalize()))

    @registry.bind_argparse('buy', [
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
