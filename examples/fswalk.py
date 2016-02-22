import os

from pymander import PrebuiltCommandContext, MultiLineContext, StandardPrompt, run_with_context


class FileWriterContext(MultiLineContext):
    FinishedHandler = MultiLineContext.OverOn2EmptyLines

    def __init__(self, *args, **kwargs):
        self.callback = kwargs.pop('callback', lambda data: None)
        self.error = kwargs.pop('error', self.write)
        super().__init__(*args, **kwargs)

    def on_finished(self):
        self.callback(self.buffer)
        self.exit()

    def prompt(self):
        self.write('... ')

    def on_cant_execute(self, line):
        pass


class FsContext(PrebuiltCommandContext, StandardPrompt):
    class Registry(PrebuiltCommandContext.Registry):
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_dir = os.path.abspath('.')

    @Registry.bind_argparse('cd', ['dirname'])
    def cd(self, dirname):
        full_dirname = os.path.abspath(os.path.join(self.current_dir, dirname))
        if not os.path.exists(full_dirname):
            self.write('No such dir: {0}\n'.format(dirname))
            return

        self.current_dir = full_dirname

    @Registry.bind_regex('^ls(\s+(?P<dirname>\w+))?')
    def ls(self, dirname):
        if dirname:
            full_dirname = os.path.abspath(os.path.join(self.current_dir, dirname))
        else:
            full_dirname = self.current_dir

        if not os.path.exists(full_dirname):
            self.write('No such dir: {0}\n'.format(dirname))
            return

        if not os.path.isdir(full_dirname):
            self.write('{0}\n'.format(dirname))
            return

        self.write('{0}\n'.format('\n'.join(sorted(os.listdir(full_dirname)))))

    @Registry.bind_argparse('mkdir', ['dirname'])
    def mkdir(self, dirname):
        if not os.path.exists(self.current_dir):
            self.write('No such dir: {0}\n'.format(dirname))
            return

        full_dirname = os.path.abspath(os.path.join(self.current_dir, dirname))
        os.mkdir(full_dirname)

    @Registry.bind_argparse('new', ['filename'])
    def new(self, filename):
        if not os.path.exists(self.current_dir):
            self.write('No such dir: {0}\n'.format(filename))
            return

        full_filename = os.path.abspath(os.path.join(self.current_dir, filename))
        if os.path.exists(full_filename):
            self.write('{0} already exists!\n'.format(filename))
            return

        self.write('< Enter content of new file "{0}" (2 empty lines to exit editor)>\n'.format(filename))
        def save_to_file(text):
            with open(full_filename, 'w') as f:
                f.write(text)

        return FileWriterContext(callback=save_to_file)

    def prompt(self):
        self.write('@ {0} > '.format(os.path.basename(self.current_dir)))


if __name__ == '__main__':
    run_with_context(FsContext())
