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
        |        License: X11 / MIT                         |
        |                                                   |
        |        Core Developer(s):                         |
        |                                                   |
        |          (+)  Chris (@someguy123) [Privex]        |
        |          (+)  Kale (@kryogenic) [Privex]          |
        |                                                   |
        +===================================================+

    Copyright 2019     Privex Inc.   ( https://www.privex.io )


"""
import asyncio
import shlex
import subprocess
from asyncio.subprocess import PIPE, STDOUT
from typing import Tuple

from privex.helpers.common import STRBYTES, byteify, shell_quote


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


async def call_sys_async(proc, *args, write: STRBYTES = None, **kwargs) -> Tuple[bytes, bytes]:
    """
    Async version of :func:`.call_sys` - works exactly the same, other than needing to be ``await``'d.
    Run a process ``proc`` with the arguments ``*args``, optionally piping data (``write``) into the
    process's stdin - then returns the stdout and stderr of the process.
    
    By default, ``stdout`` and ``stdin`` are set to :attr:`asyncio.PIPE` while stderr defaults to
    :attr:`asyncio.STDOUT`. You can override these by passing new values as keyword arguments.
    
    While it's recommended to use the file descriptor types from the :mod:`asyncio` module, they're generally just
    aliases to the types in :mod:`subprocess`, meaning :attr:`subprocess.PIPE` should work the same
    as :attr:`asyncio.PIPE`.
    
    
    **Simple Example**::
        
        >>> from privex.helpers import call_sys_async, stringify
        >>> # All arguments are automatically quoted if required, so spaces are completely fine.
        >>> folders, _ = await call_sys_async('ls', '-la', '/tmp/spaces are fine/hello world')
        >>> print(stringify(folders))
        total 0
        drwxr-xr-x  3 user  wheel  96  6 Dec 17:46 .
        drwxr-xr-x  3 user  wheel  96  6 Dec 17:46 ..
        -rw-r--r--  1 user  wheel   0  6 Dec 17:46 example

    
    **Piping data into a process**::
    
        >>> data = "hello world"
        >>> # The data "hello world" will be piped into wc's stdin, and wc's stdout + stderr will be returned
        >>> out, _ = await call_sys_async('wc', '-c', write=data)
        >>> int(out)
        11
    
    
    
    :param str proc: The process to execute.
    :param str args: Any arguments to pass to the process ``proc`` as positional arguments.
    :param bytes|str write: If this is not ``None``, then this data will be piped into the process's STDIN.
    
    :key stdout: The subprocess file descriptor for stdout, e.g. :attr:`asyncio.PIPE` or :attr:`asyncio.STDOUT`
    :key stderr: The subprocess file descriptor for stderr, e.g. :attr:`asyncio.PIPE` or :attr:`asyncio.STDOUT`
    :key stdin: The subprocess file descriptor for stdin, e.g. :attr:`asyncio.PIPE` or :attr:`asyncio.STDIN`
    :key cwd: Set the current/working directory of the process to this path, instead of the CWD of your calling script.
    
    :return tuple output: A tuple containing the process output of stdout and stderr
    """
    stdout, stderr, stdin = kwargs.pop('stdout', PIPE), kwargs.pop('stderr', STDOUT), kwargs.pop('stdin', PIPE)
    args = [proc] + list(args)
    cmd = shell_quote(*args)
    handle = await asyncio.subprocess.create_subprocess_shell(cmd, stdin=stdin, stdout=stdout, stderr=stderr, **kwargs)
    c = await handle.communicate(input=byteify(write)) if write is not None else await handle.communicate()
    stdout, stderr = c
    return stdout, stderr

