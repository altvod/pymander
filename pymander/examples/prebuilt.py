from commander import PrebuiltCommandContext, StandardPrompt, Commander


class SaladContext(PrebuiltCommandContext, StandardPrompt):
    class Registry(PrebuiltCommandContext.Registry):
        pass

    @Registry.bind_regex(r'^(?P<do_what>eat|cook) caesar')
    def caesar_salad(self, do_what):
        self.write('{0}ing caesar salad...\n'.format(do_what.capitalize()))

    @Registry.bind_argparse('buy', {'kind_of_salad': {}})
    def buy_salad(self, kind_of_salad):
        self.write('Buying {0} salad...\n'.format(kind_of_salad))


def main():
    Commander(SaladContext()).mainloop()


if __name__ == '__main__':
    main()
