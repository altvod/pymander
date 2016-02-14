PyMander
========

Introduction
------------

PyMander (short for Python Commander) is a library for writing interactive command-line interface (CLI) applications in Python.

Quick Usage Example
-------------------

Let's say, we need a CLI app that has two commands: ``date`` and ``time`` that print the current date and time respectively. Then you would do something like this:

.. code-block:: python

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


Now, imagine you decide to spice things up and add some time travel functionality to your app. Adding a lot of commands to the same function as if blocks is not a very good idea, besides you might want to keep warping of the Universe separate from the code that just shows the date and time, so go ahead and create a new handler:

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

Command contexts are a way of combining several handlers in a single scope so that they can work together. Having said that, let's run it using a ``StandardPrompt`` command context:

.. code-block:: python

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


It's worth mentioning that ``run_with_handler(handler)`` is basically an acronym for ``run_with_context(StandardPrompt([handler]))``.

``StandardPrompt`` is a simple command context that includes the following features:

- prints the ``">>> "`` when prompting for a new command
- writes "Invalid command: ..." when it cannot recognize a command
- adds the ``EchoLineHandler`` and ``ExitLineHandler`` handlers, which implement the ``echo`` and ``exit`` commands familiar to everyone


More Examples
-------------

Moving on to more complicated examples...

****

**Using regular expresssions (RegexLineHandler)**

Example:

.. code-block:: python

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


****

**Using argparse (ArgparseLineHandler)**

Example:

.. code-block:: python

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

Sometimes you might find it useful to be able to use both approaches together or be able to switch from one to another without making a mess of a whole bunch of handlers.

``PrebuiltCommandContext`` allows you to use decorators to assign its own methods as either argparse or regex commands in a single (command context) class without having to define the handlers yourself:

.. code-block:: python

    from pymander import PrebuiltCommandContext, StandardPrompt, run_with_context
    
    class SaladContext(PrebuiltCommandContext, StandardPrompt):
        class Registry(PrebuiltCommandContext.Registry):
            pass

        @Registry.bind_regex(r'(?P<do_what>eat|cook) caesar')
        def caesar_salad(self, do_what):
            self.write('{0}ing caesar salad...\n'.format(do_what.capitalize()))

        @Registry.bind_argparse('buy', {
            'kind_of_salad': {},
            ('--price', '-p'): {'default': None}
        })
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


The ``PrebuiltCommandContext.Registry`` class includes for decorators for assigning methods to specific handlers:

- ``bind_exact(command)`` binds to ``ExactLineHandler`` (matches the line exactly to the specified string, e.g. the ``exit`` command)
- ``bind_argparse(command, options)`` binds to ``ArgparseLineHandler`` (uses argparse to evaluate the line)
- ``bind_regex(regex)`` binds to ``RegexLineHandler`` (matches the line to regular expressions)

and one generic decorator:

- ``bind_to_handler(handler_class, *args)``

binds to any given LineHandler subclass with one requirement: it must have a nested ``Registry`` class with classmethod ``bind`` (ideally a parameterized decorator). Like this:

.. code-block:: python

    class MyLineHandler(LineHandler):
        class Registry:
            @classmethod
            def bind(cls, *args):
                def decorator(method):
                    # register it to cls somehow...
                    return method
                return decorator
        
        def try_execute(self, line):
            # go over registered methods in self.Registry, choose one and call it
            # otherwise raise CantParseLine
            pass


And then use it like this:

.. code-block:: python

    class MyPrebuiltContext(PrebuiltCommandContext, StandardPrompt):
        class Registry(PrebuiltCommandContext.Registry):
            pass

        @Registry.bind_to_handler(MyLineHandler, 'some', 'arguments')
        def do_whatever(self, *your_method_args):
            self.write('Whaterver, bro\n')


At this point you might be wondering, why we always also use ``StandardPrompt`` when inheriting from ``PrebuiltCommandContext``. That's because ``PrebuiltCommandContext`` is and abstract class and does not implement some of the required CommandContext methods. So this is where I'd normally send you to the full documentation of the project, but it's not finished yet, so, for now, you can just browse the source code of the examples and the ``pymander`` package itself :)
