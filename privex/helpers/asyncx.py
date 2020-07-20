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
import inspect
import queue
import threading
import warnings
from asyncio.subprocess import PIPE, STDOUT
from typing import Tuple, Callable, Any, Union, Coroutine, List, Type, Awaitable, Optional

from privex.helpers.common import byteify, shell_quote
from privex.helpers.types import T, STRBYTES, NO_RESULT
import logging

log = logging.getLogger(__name__)


__all__ = [
    'awaitable', 'AWAITABLE_BLACKLIST_MODS', 'AWAITABLE_BLACKLIST', 'AWAITABLE_BLACKLIST_FUNCS', 'run_sync', 'aobject',
    'call_sys_async', 'async_sync', 'awaitable_class', 'AwaitableMixin', 'loop_run', 'is_async_context', 'await_if_needed',
    'get_async_type', 'run_coro_thread', 'run_coro_thread_async', 'run_coro_thread_base', 'coro_thread_func'
]


def _is_coro(obj: Any) -> bool:
    """
    Small helper function to test an object against :meth:`inspect.iscoroutinefunction` and
    :meth:`inspect.iscoroutine` with a try/except to protect against a missing ``_is_coroutine`` attribute
    causing an error.
    
    :param Any obj: The object to check
    :return bool is_coro: ``True`` if ``obj`` is a coroutine function or a coroutine. Otherwise ``False``.
    """
    try:
        if inspect.iscoroutinefunction(obj) or inspect.iscoroutine(obj):
            return True
        return False
    except (AttributeError, KeyError) as e:
        # iscoroutine / iscoroutinefunction can sometimes throw a KeyError / AttributeError when checking
        # for the '_is_coroutine' key / attribute. If we encounter such an error, it's probably not a coroutine.
        log.debug(
            "exception while checking if object '%s' is coroutine in asyncx._is_coro: %s %s",
            obj, type(e), str(e)
        )
    return False


_coro_thread_queue = queue.Queue()


def coro_thread_func(func: callable, *t_args, _output_queue: Optional[Union[queue.Queue, str]] = None, **t_kwargs):
    """
    This function is not intended to be called directly. It's designed to be used as the target of a :class:`threading.Thread`.
    
    Runs the coroutine function ``func`` using a new event loop for the thread this function is running within, and relays
    the result or an exception (if one was raised) via the :class:`queue.Queue` ``_output_queue``
    
    See the higher level :func:`.run_coro_thread` for more info.
    
    :param callable func: A reference to the ``async def`` coroutine function that you want to run
    :param t_args:        Positional arguments to pass-through to the coroutine function
    
    :param _output_queue: (default: ``None``) The :class:`queue.Queue` to emit the result or raised exception through. This can also be
                          set to ``None`` to disable transmitting the result/exception via a queue.
                          
                          This can also be set to the string ``"default"``, which means the result/exception will be transmitted
                          via the :mod:`.asyncx` private queue :attr:`._coro_thread_queue`
    
    :param t_kwargs:      Keyword arguments to pass-through to the coroutine function
    
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        res = loop.run_until_complete(func(*t_args, **t_kwargs))
        if _output_queue is not None:
            _output_queue.put(res)
    except Exception as e:
        if _output_queue is not None:
            _output_queue.put(e)
    loop.close()


def run_coro_thread_base(func: callable, *args, _daemon_thread=False, **kwargs) -> threading.Thread:
    """
    This is a wrapper function which runs :func:`.coro_thread_func` within a thread, passing ``func``, ``args`` and ``kwargs``
    to it.
    
    See the higher level :func:`.run_coro_thread` for more info.
    
    :param callable func: A reference to the ``async def`` coroutine function that you want to run
    :param args:          Positional arguments to pass-through to the coroutine function
    
    :param bool _daemon_thread: (Default: ``False``) Must be specified as a kwarg. Controls whether or not the
                                generated :class:`thread.Thread` is set as a **daemon thread** or not.
    
    :param kwargs:        Keyword arguments to pass-through to the coroutine function
    
    :keyword queue.Queue _output_queue: A :class:`queue.Queue` for ;func:`.coro_thread_func` to transmit the coroutine's result, or
                                        any raised exceptions via.
    
    :return threading.Thread t_co: A started (but not joined) thread object for your caller to manage.
    """
    t_co = threading.Thread(target=coro_thread_func, args=[func] + list(args), kwargs=dict(kwargs))
    t_co.daemon = _daemon_thread
    t_co.start()
    return t_co


def run_coro_thread(func: callable, *args, **kwargs) -> Any:
    """
    Run a Python AsyncIO coroutine function within a new event loop using a thread, and return the result / raise any exceptions
    as if it were ran normally within an AsyncIO function.
    
    
    .. Caution:: If you're wanting to run a coroutine within a thread from an AsyncIO function/method, then you should
                 use :func:`.run_coro_thread_async` instead, which uses :func:`asyncio.sleep` while waiting for a result/exception
                 to be transmitted via a queue.
             
                 This allows you to run and wait for multiple coroutine threads simultaneously, as there's no synchronous blocking
                 wait - unlike this function.
    
    
    This will usually allow you to run coroutines from a synchronous function without running into the dreaded "Event loop is already
    running" error - since the coroutine will be ran inside of a thread with it's own dedicated event loop.
    
    **Example Usage**::
    
        >>> async def example_func(lorem: int, ipsum: int):
        ...     if lorem > 100: raise AttributeError("lorem is greater than 100!")
        ...     return f"example: {lorem + ipsum}"
        >>> run_coro_thread(example_func, 10, 20)
        example: 30
        >>> run_coro_thread(example_func, 3, ipsum=6)
        example: 9
        >>> run_coro_thread(example_func, lorem=40, ipsum=1)
        example: 41
        >>> run_coro_thread(example_func, 120, 50)
        File "", line 2, in example_func
            if lorem > 100: raise AttributeError("lorem is greater than 100!")
        AttributeError: lorem is greater than 100!
    
    Creates a new :class:`threading.Thread` with the target :func:`.coro_thread_func` (via :func:`.run_coro_thread_base`), passing
    the coroutine ``func`` along with the passed positional ``args`` and keyword ``kwargs``, which creates a new event loop, and
    then runs ``func`` within that thread event loop.
    
    Uses the private :class:`queue.Queue` threading queue :attr:`._coro_thread_queue` to safely relay back to the calling thread -
    either the result from the coroutine, or an exception if one was raised while trying to run the coroutine.
    
    :param callable func: A reference to the ``async def`` coroutine function that you want to run
    :param args:          Positional arguments to pass-through to the coroutine function
    :param kwargs:        Keyword arguments to pass-through to the coroutine function
    :return Any coro_res: The result returned from the coroutine ``func``
    """
    t_co = run_coro_thread_base(func, *args, **kwargs, _output_queue=_coro_thread_queue)
    t_co.join()
    
    res = _coro_thread_queue.get(block=True, timeout=10)
    if isinstance(res, (Exception, BaseException)):
        raise res
    return res


async def run_coro_thread_async(func: callable, *args, _queue_timeout=30.0, _queue_sleep=0.05, **kwargs) -> Any:
    """
    AsyncIO version of :func:`.run_coro_thread` which uses :func:`asyncio.sleep` while waiting on a result from the queue,
    allowing you to run multiple AsyncIO coroutines which call blocking synchronous code - simultaneously,
    e.g. by using :func:`asyncio.gather`
    
    Below is an example of running an example coroutine ``hello`` which runs the synchronous blocking ``time.sleep``.
    Using :func:`.run_coro_thread_async` plus :func:`asyncio.gather` - we can run ``hello`` 4 times simultaneously,
    despite the use of the blocking :func:`time.sleep`.
    
    **Basic usage**::
    
        >>> import asyncio
        >>> from privex.helpers.asyncx import run_coro_thread_async
        >>> async def hello(world):
        ...     time.sleep(1)
        ...     return world * 10
        >>> await asyncio.gather(run_coro_thread_async(hello, 5), run_coro_thread_async(hello, 15),
        ...                      run_coro_thread_async(hello, 90), run_coro_thread_async(hello, 25))
        [50, 150, 900, 250]
    
    
    :param callable func: A reference to the ``async def`` coroutine function that you want to run
    :param args:          Positional arguments to pass-through to the coroutine function
    :param kwargs:        Keyword arguments to pass-through to the coroutine function
    :param float|int _queue_timeout: (default: ``30``) Maximum amount of seconds to wait for a result or exception
                                     from ``func`` before giving up.
    :param _queue_sleep: (default: ``0.05``) Amount of time to AsyncIO sleep between each check of the result queue
    :return Any coro_res: The result returned from the coroutine ``func``
    """
    _queue_timeout, _queue_sleep = float(_queue_timeout), float(_queue_sleep)
    thread_waited = 0.0
    q = queue.Queue()
    t_co = run_coro_thread_base(func, *args, **kwargs, _output_queue=q)
    
    res = NO_RESULT
    while res == NO_RESULT:
        if thread_waited >= _queue_timeout:
            raise TimeoutError(f"No thread result after waiting {thread_waited} seconds...")
        try:
            _res = q.get_nowait()
            if isinstance(_res, (Exception, BaseException)):
                raise _res
            res = _res
        except queue.Empty:
            thread_waited += _queue_sleep
            await asyncio.sleep(_queue_sleep)
    t_co.join(5)
    
    return res


def run_sync(func, *args, **kwargs):
    """
    Run an async function synchronously (useful for REPL testing async functions). (TIP: Consider using :func:`.loop_run` instead)

    .. Attention:: For most cases, you should use the function :func:`.loop_run` instead of this. Unlike ``run_sync``, :func:`.loop_run`
                   is able to handle async function references, coroutines, as well as coroutines / async functions which are wrapped
                   in an outer non-async function (e.g. an ``@awaitable`` wrapper).
                   
                   :func:`.loop_run` also supports using a custom event loop, instead of being limited to :func:`asyncio.get_event_loop`

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


def loop_run(coro: Union[Coroutine, Type[Coroutine], Callable], *args, _loop=None, **kwargs) -> Any:
    """
    Run the coroutine or async function ``coro`` synchronously, using an AsyncIO event loop.
    
    If the keyword argument ``_loop`` isn't specified, it defaults to the loop returned by :func:`asyncio.get_event_loop`

    If ``coro`` doesn't appear to be a coroutine or async function:
        
    * If ``coro`` is a normal ``callable`` object e.g. a function, then it'll be called.
        
        * If the object returned after calling ``coro(*args, **kwargs)`` **is a co-routine / async func**, then it'll call
          ``loop_run`` again, passing the object returned from calling it, and returning the result from that recursive call.
        
        * If the returned object isn't an async func / co-routine, then the object will be returned as-is.
        
    *  Otherwise, ``coro`` will just be returned back to the caller.
    
    **Example Usage**
    
    First we'll define the async function ``some_func`` to use as an example::
    
        >>> async def some_func(x, y):
        ...     return x + y
    
    Option 1 - Call an async function directly with any args/kwargs required, then pass the coroutine returned::
    
        >>> loop_run(some_func(3, 4))
        7
    
    Option 2 - Pass a reference to the async function, and pass any required args/kwargs straight to :func:`.loop_run` - the
    function will be ran with the args/kwargs you provide, then the coroutine ran in an event loop::
    
        >>> loop_run(some_func, 10, y=20)    # Opt 2. Pass the async function and include any args/kwargs for the call
        30
    
    
    :param coro:     A co-routine, or reference to an async function to be ran synchronously
    :param args:     Any positional arguments to pass to ``coro`` (if it's a function reference and not a coroutine)
    :param _loop:    (kwarg only!) If passed, will run ``coro`` in this event loop, instead of :func:`asyncio.get_event_loop`
    :param kwargs:   Any keyword arguments to pass to ``coro`` (if it's a function reference and not a coroutine)
    
    :type _loop: asyncio.base_events.BaseEventLoop
    
    :return Any coro_result: The returned data from executing the coroutine / async function
    """
    if not _is_coro(coro):
        log.debug("Passed 'coro' object isn't a co-routine or async func. Actual type: %s", coro)
        if callable(coro):
            log.debug("Passed 'coro' object is a callable. Calling coro object with args: %s // kwargs: %s", args, kwargs)
            x = coro(*args, **kwargs)
            if _is_coro(x):
                log.debug("Call result from 'coro(*args, **kwargs)' is a coro / async func. Re-running loop_run. ")
                return loop_run(x, *args, _loop=_loop, **kwargs)
            log.debug("Call result from 'coro(*args, **kwargs)' isn't async func / coro. Returning object: %s ", x)
            return x
        log.debug("'coro' object isn't callable. Returning original 'coro' object: %s", coro)
        return coro
    
    loop = _loop
    if loop is None: loop = asyncio.get_event_loop()
    if asyncio.iscoroutinefunction(coro): coro = coro(*args, **kwargs)
    
    return loop.run_until_complete(coro)


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


async def await_if_needed(func: Union[callable, Coroutine, Awaitable, Any], *args, **kwargs):
    """
    Call, await, and/or simply return ``func`` depending on whether it's an async function reference (coroutine function),
    a non-awaited coroutine, a standard synchronous function, or just a plain old string.
    
    Helps take the guess work out of parameters which could be a string, a synchronous function, an async function, or
    a coroutine which hasn't been awaited.
    
        >>> def sync_func(hello, world=1):
        ...     return f"sync hello: {hello} {world}"
        >>> async def async_func(hello, world=1):
        ...     return f"async hello: {hello} {world}"
        >>> await await_if_needed(sync_func, 3, world=2)
        'sync hello: 3 2'
        >>> await await_if_needed(async_func, 5, 4)
        'async hello: 5 4'
        >>> f = async_func(5, 4)
        >>> await await_if_needed(f)
        'async hello: 5 4'
    
    :param callable|Coroutine|Awaitable|Any func: The function/object to await/call if needed.
    :param args: If ``func`` is a function/method, will forward any positional arguments to the function
    :param kwargs: If ``func`` is a function/method, will forward any keyword arguments to the function
    :return Any func_data: The result of the awaited ``func``, or the original ``func`` if not a coroutine nor callable/awaitable
    """
    as_type = get_async_type(func)
    f = func
    
    if as_type == 'coro func':
        f = await func(*args, **kwargs)
    elif as_type in ['coro', 'awaitable']:
        return await func
    elif as_type == 'sync func':
        f = func(*args, **kwargs)
    
    if isinstance(f, Awaitable):
        return await f
    return f


def get_async_type(obj) -> str:
    """
    Detects if ``obj`` is an async object/function that needs awaited / called, whether it's a synchronous callable,
    or whether it's unknown (probably not async)
    
        >>> def sync_func(hello, world=1): return f"sync hello: {hello} {world}"
        >>> async def async_func(hello, world=1): return f"async hello: {hello} {world}"
        >>> get_async_type(async_func)
        'coro func'
        >>> get_async_type(async_func(5))
        'coro'
        >>> get_async_type(sync_func)
        'sync func'
        >>> get_async_type(sync_func(10))
        'unknown'
    
    :param Any obj: Object to check for async type
    :return str async_type: Either ``'coro func'``, ``'coro'``, ``'awaitable'``, ``'sync func'`` or ``'unknown'``
    """
    if _is_coro(obj):
        if asyncio.iscoroutinefunction(obj): return "coro func"
        if asyncio.iscoroutine(obj): return "coro"
    if isinstance(obj, Awaitable): return "awaitable"
    if callable(obj): return "sync func"
    return "unknown"


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


def is_async_context() -> bool:
    """Returns ``True`` if currently in an async context, otherwise ``False``"""
    try:
        import sniffio
    except ImportError as e:
        raise ImportError(f"is_async_context / @awaitable unavailable - 'sniffio' not installed. Exc: {type(e)} {str(e)} ")
    try:
        # Detect if we're in async context
        sniffio.current_async_library()
        return True
    except sniffio.AsyncLibraryNotFoundError:
        return False


def _awaitable_blacklisted(skip=3) -> bool:
    """
    Returns ``True`` if the caller of the function calling ``_awaitable_blacklisted`` is present in the awaitable
    blacklists such as :attr:`.AWAITABLE_BLACKLIST` - otherwise ``False`` if they're not blacklisted.

    :param int skip: Scan the caller function this far up the stack
                     (2 = callee of _awaitable_blacklisted, 3 = callee of callee #2, 4 = callee of #3, 5 = callee of #4 etc.)

    :return bool is_blacklisted: ``True`` if the calling method/module/function is blacklisted, otherwise ``False``.
    """
    try:
        from privex.helpers.black_magic import calling_module, calling_function, caller_name
        
        # Exact module + function/method path match
        if caller_name(skip=skip) in AWAITABLE_BLACKLIST:
            return True
        # Plain function name match
        if calling_function(skip=skip) in AWAITABLE_BLACKLIST_FUNCS:
            return True
        
        _mod = calling_module(skip=skip)
        # Exact module path match
        if _mod in AWAITABLE_BLACKLIST_MODS:
            return True
        # Sub-modules path match (e.g. if hello.world is blacklisted, then hello.world.example is also blacklisted)
        for _m in AWAITABLE_BLACKLIST_MODS:
            if _mod.startswith(_m + '.'):
                return True
    
    except Exception:
        log.exception("Failed to check blacklist for awaitable function. Falling back to standard async sniffing.")
    
    return False


class AwaitableMixin:
    def __getattribute__(self, item):
        a = object.__getattribute__(self, item)
        
        if not _is_coro(a): return a

        def _wrp(*args, **kwargs):
            return a if is_async_context() and not _awaitable_blacklisted() else loop_run(a, *args, **kwargs)

        return _wrp


def awaitable_class(cls: Type[T]) -> Type[T]:
    """
    Wraps a class, allowing all async methods to be used in non-async code as if they were normal synchronous methods.
    
    **Example Usage**
    
    Simply decorate your class with ``@awaitable_class`` (no brackets! takes no arguments), and once you create an instance of your
    class, all of your async methods can be used by synchronous code as-if they were plain functions::
    
        >>> from privex.helpers import awaitable_class
        >>>
        >>> @awaitable_class
        >>> class ExampleAsyncCls:
        >>>     async def example_async(self):
        >>>         return "hello async world"
        >>>
        >>>     def example_sync(self):
        >>>         return "hello non-async world"
        >>>
    
    NOTE - You can also wrap a class without using a decorator - just pass the class as the first argument like so::
        
        >>> class _OtherExample:
        ...     async def hello(self):
        ...         return 'world'
        >>> OtherExample = awaitable_class(_OtherExample)
    
    If we call ``.example_async()`` on the above class from a synchronous REPL, it will return ``'hello async world'`` as if it were a
    normal synchronous method. We can also call the non-async ``.example_sync()`` which works like normal::
    
        >>> k = ExampleAsyncCls()
        >>> k.example_async()
        'hello async world'
        >>> k.example_sync()
        'hello non-async world'
    
    However, inside of an async context (e.g. an async function), ``awaitable_class`` will be returning coroutines, so you should
    ``await`` the methods, as you would expect when dealing with an async function::
        
        >>> async def test_async():
        >>>     exmp = ExampleAsyncCls()
        >>>     return await exmp.example_async()
        >>>
        >>> await test_async()
        'hello async world'

        
    :param type cls: The class to wrap
    :return type wrapped_class: The class after being wrapped
    """
    cls: Type[object]
    
    class _AwaitableClass(cls):
        __AWAITABLE_CLS = True
        """
        This sub-class is modified to appear as if it were the original class being sub-classed, unfortunately this means
        it would be difficult to check whether or not a class has been wrapped with _AwaitableClass.
        
        To allow you to check whether or not a class has been sub-classed by _AwaitableClass, this class private attribute
        is present on the returned class and any instances of it.
        """
        
        def __getattribute__(self, item):
            a: Union[Coroutine, callable, Any] = super().__getattribute__(item)
            cls_name = super().__getattribute__('__class__').__name__
            # full_attr = f"{self.__class__.__name__}.{item}"
            full_attr = f"{cls_name}.{item}"
            if not _is_coro(a):
                log.debug("Attribute %s is not a coroutine or coro function. Returning normally.", full_attr)
                return a
            # return awaitable(a) if inspect.iscoroutinefunction(a) else a
            
            def _wrp(*args, **kwargs):
                if is_async_context() and not _awaitable_blacklisted():
                    log.debug("Currently in async context. Returning %s as coroutine", full_attr)
                    return a(*args, **kwargs)
                log.debug("Not in async context or attribute is blacklisted. Returning %s as coroutine", full_attr)
                return loop_run(a, *args, **kwargs)
            return _wrp
    
    _AwaitableClass.__name__ = cls.__name__
    _AwaitableClass.__qualname__ = cls.__qualname__
    _AwaitableClass.__module__ = cls.__module__
    
    return _AwaitableClass


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

        # The wrapped function isn't a coroutine function, nor a coroutine. This may be caused by an adapter
        # wrapper class which deals with both synchronous and asynchronous adapters.
        # Since it doesn't appear to be a coroutine, just return the result.
        if not _is_coro(coroutine):
            return coroutine

        # Always run the coroutine in an event loop if the caller function is blacklisted in the AWAITABLE_BLACKLIST* lists
        if _awaitable_blacklisted():
            return asyncio.get_event_loop().run_until_complete(coroutine)
            
        if is_async_context():           # We're in async context, return the coroutine for await usage
            return coroutine
        loop = asyncio.get_event_loop()  # Not in async context, run coroutine in event loop.
        return loop.run_until_complete(coroutine)
    
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


