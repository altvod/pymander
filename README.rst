PyMander
========

Introduction
------------

PyMander (short for Python Commander) is a library for writing interactive command-line interface (CLI)
applications in Python.

Quick Start
-----------

Let's say, we need a CLI app that has two commands: ``date`` and ``time`` that print the current date
and time respectively. Then you would do something like this:

.. code-block:: python

    import time
    from pymander.handlers import LineHandler
    from pymander.exceptions import CantParseLine
    from pymander.shortcuts import run_with_handler
    
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


Let's spice things up and add some time travel functionality to your app. Adding a lot of commands
to the same function as if-blocks is not a very good idea, besides you might want to keep warping of the Universe
separate from the code that just shows the date and time, so go ahead and create a new handler:

.. code-block:: python

    import re

    class TimeTravelLineHandler(LineHandler):
        def try_execute(self, line):
            cmd_match = re.match('go to date (?P<new_date>.*?)\s*$', line)
            if cmd_match:
                new_date = line.split(' ', 2)[-1]
                self.context.write('Traveling to date: {0}\n'.format(cmd_match.group('new_date')))
            else:
                raise CantParseLine(line)

At this point we have a problem: how do we use the two handlers in our app  simultaneously?

Command contexts are a way of combining several handlers in a single scope so that they can work together.
Having said that, let's run it using a ``StandardPrompt`` command context:

.. code-block:: python

    from pymander.contexts import StandardPrompt
    from pymander.shortcuts import run_with_context
    
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


It's worth mentioning that ``run_with_handler(handler)`` is basically a shortcut
for ``run_with_context(StandardPrompt([handler]))``.

``StandardPrompt`` is a simple command context that includes the following features:

- prints the ``">>> "`` when prompting for a new command
- writes "Invalid command: ..." when it cannot recognize a command
- adds the ``EchoLineHandler`` and ``ExitLineHandler`` handlers, which implement the ``echo`` and ``exit`` commands, which do pretty much what you expect them to do


More Examples
-------------

Moving on to more complicated examples...

****

**Using regular expresssions (RegexLineHandler)**

Example:

.. code-block:: python

    from pymander.decorators import bind_command

    class BerryLineHandler(RegexLineHandler):
        @bind_command(r'pick a (?P<berry_kind>\w+)')
        def pick_berry(self, berry_kind):
            self.context.write('Picked a {0}\n'.format(berry_kind))

        @bind_command(r'make (?P<berry_kind>\w+) jam')
        def make_jam(self, berry_kind):
            self.context.write('Made some {0} jam\n'.format(berry_kind))

Output:

::

    >>> pick a strawberry
    Picked a strawberry
    >>> make blueberry jam
    Made some blueberry jam


****

**Using argparse (ArgparseLineHandler)**

Example:

.. code-block:: python

    from pymander.decorators import bind_command

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


Output:

::

    >>> play chess --well
    I play chess very well
    >>> play monopoly
    I play monopoly
    >>> win
    I just won!


****

**Combining argparse and regexes using PrebuiltCommandContext**

Sometimes you might find it useful to be able to use both approaches together or be able to switch
from one to another without making a mess of a whole bunch of handlers.

``PrebuiltCommandContext`` allows you to use decorators to assign its own methods
as either argparse or regex commands in a single (command context) class without having to define the handlers yourself:

.. code-block:: python

    from pymander.contexts import PrebuiltCommandContext, StandardPrompt
    from pymander.shortcuts import run_with_context
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
    
    run_with_context(SaladContext())


Example:

::

    >>> cook caesar
    Cooking caesar salad...
    >>> buy greek
    Buying greek salad...
    >>> buy russian --price $5
    Buying russian salad for $5...


The ``PrebuiltCommandContext`` class can be used with three decorators for assigning methods to specific handlers:

- ``bind_exact(command)`` binds to ``ExactLineHandler`` (matches the line exactly to the specified string, e.g. the ``exit`` command)
- ``bind_argparse(command, options)`` binds to ``ArgparseLineHandler`` (uses argparse to evaluate the line)
- ``bind_regex(regex)`` binds to ``RegexLineHandler`` (matches the line to regular expressions)

and one generic decorator:

- ``bind_to_handler(handler_class, *bind_args, **bind_kwargs)``

binds to any given LineHandler subclass. The handler class can then access its autogenerated methods
via the ``self.command_methods`` attribute:

.. code-block:: python

    class MyLineHandler(LineHandler):
        def try_execute(self, line):
            for command_info in self.command_methods:
                # where: command_info = {"method": <callable>, "args": <bind_args>, "kwargs": <bind_kwargs>}
                # your logic goes here:
                #     determine whether <line> matches the <args> and <kwargs> options)
                #     and call the callable if it does
                pass

            # if no suitable match was found:
            raise CantParseLine


And then use it like this:

.. code-block:: python

    class MyPrebuiltContext(PrebuiltCommandContext, StandardPrompt):
        @bind_to_handler(MyLineHandler, 'some', 'arguments')
        def do_whatever(self, *your_method_args):
            self.write('Whatever, bro\n')


At this point you might be wondering, why we always also use ``StandardPrompt`` when inheriting
from ``PrebuiltCommandContext``. That's because ``PrebuiltCommandContext`` is an abstract class and does not
implement some of the required ``CommandContext`` methods. So this is where I'd normally send you
to the full documentation of the project, but it's not finished yet, so, for now, you can just browse
the source code of the examples and the ``pymander`` package itself :)

Using Nested Contexts
---------------------

An obvious extension would be the ability to enter a new context on some commands and then exit them
(multi-step commands, entering and exiting a file editor, etc.).
All you have to do to use this is return an instance of a new ``CommandContext`` from your command,
and you're in! Just don't forget to supply this context with an ``exit``, or you'll be stuck in there forever.

See ``DeeperLineHandler`` in the `simple <https://github.com/altvod/pymander/blob/master/examples/simple.py>`_ example.


Using Multiline Commands (text input)
-------------------------------------

Check out the `multi <https://github.com/altvod/pymander/blob/master/examples/multi.py>`_ and `fswalk <https://github.com/altvod/pymander/blob/master/examples/fswalk.py>`_ examples.


Major TODOs
-----------

Here I'll be listing some of the major fetures that are not yet implemented, but are crucial to the library's usability.

#. an easy to use help mechanism. It should be able to list possible commands and how they should be used (like in argparse)
#. read input by character instead of by line to handle special characters (`Esc`, `Ctrl`, arrows keys, etc.). This might also mean using OS-specific adapters for the console
