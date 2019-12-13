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
import warnings
from asyncio.subprocess import PIPE, STDOUT
from typing import Tuple, Callable, Any, Union, Coroutine, List

from privex.helpers.common import STRBYTES, byteify, shell_quote
import logging

log = logging.getLogger(__name__)


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
    # return asyncio.run(future)


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


AWAITABLE_BLACKLIST_FUNCS: List[str] = []
"""
A list of plain function names - for which :func:`.awaitable` decorated function/methods should always
run synchronously.
"""

AWAITABLE_BLACKLIST_MODS: List[str] = []
"""
A list of fully qualified module names - for which :func:`.awaitable` decorated function/methods should always
run synchronously.
"""

AWAITABLE_BLACKLIST: List[str] = []
"""
A list of fully qualified module paths to functions/methods, if any of these functions/methods call an :func:`.awaitable`
decorated function/method, then the awaitable will be ran synchronously regardless of whether there's an active
AsyncIO context or not.
"""


def awaitable(func: Callable) -> Callable:
    """
    Decorator which helps with creation of async wrapper functions.
    
    **Usage**
    
    Define your async function as normal, then create a standard python function using this decorator - the function
    should just call your async function and return it.
    
        >>> async def some_func_async(a: str, b: str):
        ...     c = a + b
        ...     return c
        ...
        >>> @awaitable
        >>> def some_func(a, b) -> Union[str, Coroutine[Any, Any, str]]:
        ...     return some_func_async(a, b)
        ...
    
    Now, inside of async functions, we just ``await`` the wrapper function as if it were the original async function.
    
        >>> async def my_async_func():
        ...     res = await some_func("hello", "world")
        ...
    
    While inside of synchronous functions, we call the wrapper function as if it were a normal synchronous function.
    The decorator will create an asyncio event loop, run the function, then return the result - transparent to the
    calling function.
    
        >>> def my_sync_func():
        ...     res = some_func("hello world")
        ...
    
    **Blacklists**
    
    If you mix a lot of synchronous and asynchronous code, :mod:`sniffio` may return coroutines to synchronous functions
    that were called from asynchronous functions, which can of course cause problems.
    
    To avoid this issue, you can blacklist function names, module names (and their sub-modules), and/or fully qualified
    module paths to functions/methods.
    
    Three blacklists are available in this module, which allow you to specify caller functions/methods, modules, or
    fully qualified module paths to functions/methods for which :func:`.awaitable` wrapped functions/methods
    should **always** execute in an event loop and return synchronously.
    
    Example::
        
        >>> from privex.helpers import asyncx
        >>> # All code within the module 'some.module' and it's sub-modules will always have awaitable's run their wrapped
        >>> # functions synchronously.
        >>> asyncx.AWAITABLE_BLACKLIST_MODS += ['some.module']
        >>> # Whenever a function with the name 'example_func' (in any module) calls an awaitable, it will always run synchronously
        >>> asyncx.AWAITABLE_BLACKLIST_FUNCS += ['example_func']
        >>> # Whenever the specific class method 'other.module.SomeClass.some_sync' calls an awaitable, it will always run synchronously.
        >>> asyncx.AWAITABLE_BLACKLIST += ['other.module.SomeClass.some_sync']
    
    
    Original source: https://github.com/encode/httpx/issues/572#issuecomment-562179966
    
    """
    def wrapper(*args: Any, **kwargs: Any) -> Union[Any, Coroutine[Any, Any, Any]]:
        coroutine = func(*args, **kwargs)

        # The wrapped function isn't a coroutine function, nor a coroutine. This may be caused by an adapter wrapper class which deals
        # with both synchronous and asynchronous adapters.
        # Since it doesn't appear to be a coroutine, just return the result.
        if not asyncio.iscoroutinefunction(coroutine) and not asyncio.iscoroutine(coroutine):
            return coroutine

        try:
            from privex.helpers.black_magic import calling_module, calling_function, caller_name
            
            if caller_name() in AWAITABLE_BLACKLIST:
                return asyncio.get_event_loop().run_until_complete(coroutine)
            elif calling_function() in AWAITABLE_BLACKLIST_FUNCS:
                return asyncio.get_event_loop().run_until_complete(coroutine)
            else:
                _mod = calling_module()
                if _mod in AWAITABLE_BLACKLIST_MODS:
                    return asyncio.get_event_loop().run_until_complete(coroutine)
                for _m in AWAITABLE_BLACKLIST_MODS:
                    if not _m.startswith(_mod + '.'):
                        continue
                    return asyncio.get_event_loop().run_until_complete(coroutine)
        except Exception:
            log.exception("Failed to check blacklist for awaitable function. Falling back to standard async sniffing.")
            
        try:
            import sniffio
        except ImportError as e:
            raise ImportError(f"Decorator @awaitable unavailable - 'sniffio' not installed. Exc: {type(e)} {str(e)} ")
        try:
            # Detect if we're in async context
            sniffio.current_async_library()
        except sniffio.AsyncLibraryNotFoundError:
            # Not in async context, run coroutine in event loop.
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(coroutine)
        else:
            # We're in async context, return the coroutine for await usage
            return coroutine
    
    return wrapper


# noinspection All
class aobject(object):
    """
    Inheriting this class allows you to define an async __init__.

    To use async constructors, you must construct your class using ``await MyClass(params)``
    
    **Example**::
        
        >>> class SomeClass(aobject):
        ...     async def __init__(self, some_param='x'):
        ...         self.some_param = some_param
        ...         self.example = await self.test_async()
        ...
        ...     async def test_async(self):
        ...         return "hello world"
        ...
        >>> async def main():
        ...     some_class = await SomeClass('testing')
        ...     print(some_class.example)
        ...
    
    **Note:** Some IDEs like PyCharm may complain about having async ``__new__`` and ``__init__``, but it **does**
    work with Python 3.6+.
    
    You may be able to work-around the syntax error in your sub-class by defining your ``__init__`` method under a
    different name, and then assigning ``__init__ = _your_real_init`` much like this class does.
    
    Original source: https://stackoverflow.com/a/45364670
    """

    # noinspection PyUnresolvedReferences
    async def __aobject_new(cls, *a, **kw):
        instance = super().__new__(cls)
        # noinspection PyArgumentList
        await instance.__init__(*a, **kw)
        return instance

    async def __aobject_init(self):
        pass

    __new__ = __aobject_new
    __init__ = __aobject_init


