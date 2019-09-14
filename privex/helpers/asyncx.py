"""
Functions and classes related to working with Python's native asyncio support

To avoid issues with the ``async`` keyword, this file is named ``asyncx`` instead of ``async``

**Copyright**::

        +===================================================+
        |                 © 2019 Privex Inc.                |
        |               https://www.privex.io               |
        +===================================================+
        |                                                   |
        |        Originally Developed by Privex Inc.        |
        |                                                   |
        |        Core Developer(s):                         |
        |                                                   |
        |          (+)  Chris (@someguy123) [Privex]        |
        |          (+)  Kale (@kryogenic) [Privex]          |
        |                                                   |
        +===================================================+

    Copyright 2019     Privex Inc.   ( https://www.privex.io )

    Permission is hereby granted, free of charge, to any person obtaining a copy of
    this software and associated documentation files (the "Software"), to deal in
    the Software without restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
    Software, and to permit persons to whom the Software is furnished to do so,
    subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
    INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
    PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
    OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
    SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
import asyncio


def run_sync(func, *args, **kwargs):
    """
    Run an async function synchronously (useful for REPL testing async functions)

    Usage:

        >>> async def my_async_func(a, b, x=None, y=None):
        ...     return a, b, x, y
        >>>
        >>> run_sync(my_async_func, 1, 2, x=3, y=4)
        (1, 2, 3, 4,)

    :param callable func: An asynchronous function to run
    :param args:          Positional arguments to pass to ``func``
    :param kwargs:        Keyword arguments to pass to ``func``

    """
    coro = asyncio.coroutine(func)
    future = coro(*args, **kwargs)
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(future)


def async_sync(f):
    """
    Async Synchronous Decorator, borrowed from https://stackoverflow.com/a/23036785/2648583 - added this PyDoc comment
    and support for returning data from a synchronous function

    Allows a non-async function to run async functions using ``yield from`` - and can also return data

    Useful for unit testing, since unittest.TestCase functions are synchronous.

    Example async function:

        >>> async def my_async_func(a, b, x=None, y=None):
        ...     return a, b, x, y
        ...

    Using the above async function with a non-async function:

        >>> @async_sync
        ... def sync_function():
        ...     result = yield from my_async_func(1, 2, x=3, y=4)
        ...     return result
        ...
        >>> r = sync_function()
        >>> print(r)
        (1, 2, 3, 4,)
        >>> print(r[1])
        2


    """

    def wrapper(*args, **kwargs):
        coro = asyncio.coroutine(f)
        future = coro(*args, **kwargs)
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(future)

    return wrapper
