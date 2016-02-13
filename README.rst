PyMander
========

Introduction
------------

PyMander is a library for writing interactive command-line interface (CLI) applications in Python.

Quick Usage Example
-------------------

Let's say, we need a CLI app that has two commands: ``date`` and ``time`` that print the current date and time respectively. Then you would do something like this:
::

    import time
    from pymander import LineHandler, CantParseLine, run_with_handler
    
    class DatetimeLineHandler(LineHandler):
        def try_execute(self, line):
            if line.strip() == 'time':
                self.context.write(time.strftime('%H:%M:%S\n'))
            elif line.strip() == 'date':
                self.context.write(time.strftime('%Y.%d.%d\n'))
            else:
                raise CantParseLine(line)
    
    
    run_with_handler(DatetimeLineHandler())

And you'll get... (just type ``exit`` to exit the loop)
::

    >>> date
    2016.14.14
    >>> time 
    01:00:00
    >>> exit 
    Bye!


Now, imagine you decide to spice things up and add some time travel functionality to your app. It might be a good idea to keep this separate from the code that just shows the date and time, so go ahead and create a new handler:
::

    import re

    class TimeTravelLineHandler(LineHandler):
        def try_execute(self, line):
            cmd_match = re.match('go to date (?P<new_date>.*?)\s*$', line)
            if cmd_match:
                new_date = line.split(' ', 2)[-1]
                self.context.write('Traveling to date: {0}\n'.format(cmd_match.group('new_date')))
            else:
                raise CantParseLine(line)

This is where we get to the problem of using the two handlers in our little app.

Command contexts are a way of combining several handlers in a single scope so that they can work together. Having said that, let's run it using a ``StandardPrompt`` command context:
::

    from pymander import StandardPrompt, run_with_context
    
    run_with_context(
        StandardPrompt([
            DatetimeLineHandler(),
            TimeTravelLineHandler()
        ])
    )

And back to the future we go!
::
    >>> date
    2016.14.14
    >>> go to date October 10 2058
    Traveling to date: October 10 2058

It's worth mentioning that ``run_with_handler(context)`` is really a shortcut for ``run_with_context(StandardPrompt([context]))``.

``StandardPrompt`` is a simple command context that includes the following features:

- prints the ``">>> "`` when prompting for a new command
- writes "Invalid command: ..." when it cannot recognize a command
- adds the ``EchoLineHandler`` and ``ExitLineHandler`` handlers, which implement the ``echo`` and ``exit`` commands familiar to everyone


Advanced Examples
-----------------

Moving on to more complicated examples...

****
**Using regular expresssions**
Example:
::

    class BerryLineHandler(RegexLineHandler):
        class Registry(RegexLineHandler.Registry):
            pass

        @Registry.bind(r'pick a (?P<berry_kind>\w+)')
        def pick_berry(self, berry_kind):
            self.context.write('Picked a {0}\n'.format(berry_kind))

        @Registry.bind(r'make (?P<berry_kind>\w+) jam')
        def make_jam(self, berry_kind):
            self.context.write('Made some {0} jam\n'.format(berry_kind))

Output:
::

    >>> pick a strawberry
    Picked a strawberry
    >>> make blueberry jam
    Made some blueberry jam
