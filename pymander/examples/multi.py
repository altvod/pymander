import json

from pymander import ArgparseLineHandler, JsonContext, StandardPrompt, Commander


class StarTrekLineHandler(ArgparseLineHandler):
    class Registry(ArgparseLineHandler.Registry):
        pass

    @Registry.bind('boldly_read', {
        ('--format', '-f'): {'dest': 'text_format', 'default': 'plain'}
    })
    def boldly_read(self, text_format):
        if text_format != 'json':
            self.context.write('Unbold format: {0}\n'.format(text_format))
            return

        self.context.write('Boldly go on:\n')
        def finish(data):
            self.context.write('Boldly done!\nJSON is valid: {0}\n'.format(json.dumps(data)))

        return JsonContext(callback=finish)


def main():
    Commander(StandardPrompt([StarTrekLineHandler()])).mainloop()


if __name__ == '__main__':
    main()
