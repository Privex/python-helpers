"""
Class Method / Function decorators

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
import functools
import logging
from enum import Enum
from time import sleep
from typing import Any, Union, List

from privex.helpers.cache import cached, async_adapter_get
from privex.helpers.common import empty, is_true
from privex.helpers.asyncx import await_if_needed

DEF_RETRY_MSG = "Exception while running '%s', will retry %d more times."
DEF_FAIL_MSG = "Giving up after attempting to retry function '%s' %d times."

log = logging.getLogger(__name__)

try:
    from privex.helpers.asyncx import async_sync
except ImportError:
    log.debug('privex.helpers __init__ failed to import "asyncx", not loading async helpers')
    pass


def retry_on_err(max_retries: int = 3, delay: Union[int, float] = 3, **retry_conf):
    """
    Decorates a function or class method, wraps the function/method with a try/catch block, and will automatically
    re-run the function with the same arguments up to `max_retries` time after any exception is raised, with a
    ``delay`` second delay between re-tries.

    If it still throws an exception after ``max_retries`` retries, it will log the exception details with ``fail_msg``,
    and then re-raise it.

    Usage (retry up to 5 times, 1 second between retries, stop immediately if IOError is detected)::

        >>> @retry_on_err(5, 1, fail_on=[IOError])
        ... def my_func(self, some=None, args=None):
        ...     if some == 'io': raise IOError()
        ...      raise FileExistsError()

    This will be re-ran 5 times, 1 second apart after each exception is raised, before giving up::

        >>> my_func()

    Where-as this one will immediately re-raise the caught IOError on the first attempt, as it's passed in ``fail_on``::

        >>> my_func('io')


    .. Attention:: For safety reasons, by default ``max_ignore`` is set to ``100``. This means after 100 retries where an
                       exception was ignored, the decorator will give up and raise the last exception.
                       
                       This is to prevent the risk of infinite loops hanging your application. If you are 100% certain that the
                       function you've wrapped, and/or the exceptions passed in ``ignore`` cannot cause an infinite retry loop, then
                       you can pass ``max_ignore=False`` to the decorator to disable failure after ``max_ignore`` ignored exceptions.
    


    :param int max_retries:  Maximum total retry attempts before giving up
    :param float delay:      Amount of time in seconds to sleep before re-trying the wrapped function
    :param retry_conf:       Less frequently used arguments, pass in as keyword args (see below)

    :key list fail_on:  A list() of Exception types that should result in immediate failure (don't retry, raise)
    
    :key list ignore:   A list() of Exception types that should be ignored (will retry, but without incrementing the failure counter)
    
    :key int|bool max_ignore: (Default: ``100``) If an exception is raised while retrying, and more than this
             many exceptions (listed in ``ignore``) have been ignored during retry attempts, then give up
             and raise the last exception.
             
             This feature is designed to prevent "ignored" exceptions causing an infinite retry loop. By
             default ``max_ignore`` is set to ``100``, but you can increase/decrease this as needed.
             
             You can also set it to ``False`` to disable raising when too many exceptions are ignored - however, it's
             strongly not recommended to disable ``max_ignore``, especially if you have ``instance_match=True``,
             as it could cause an infinite retry loop which hangs your application.
      
    
    :key bool instance_match: (Default: ``False``) If this is set to ``True``, then the exception type comparisons for ``fail_on``
            and ``ignore`` will compare using ``isinstance(e, x)`` instead of ``type(e) is x``.
            
            If this is enabled, then exceptions listed in ``fail_on`` and ``ignore`` will also **match sub-classes** of
            the listed exceptions, instead of exact matches.

    :key str retry_msg: Override the log message used for retry attempts. First message param %s is func name,
                        second message param %d is retry attempts remaining

    :key str fail_msg: Override the log message used after all retry attempts are exhausted. First message param %s
                       is func name, and second param %d is amount of times retried.

    """
    retry_msg: str = retry_conf.get('retry_msg', DEF_RETRY_MSG)
    fail_msg: str = retry_conf.get('fail_msg', DEF_FAIL_MSG)
    instance_match: bool = is_true(retry_conf.get('instance_match', False))
    fail_on: List[type] = list(retry_conf.get('fail_on', []))
    ignore_ex: List[type] = list(retry_conf.get('ignore', []))
    max_ignore: Union[bool, int] = retry_conf.get('max_ignore', 100)

    def _decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            retries = int(kwargs.pop('retry_attempts', 0))
            ignore_count = int(kwargs.pop('ignore_count', 0))
            
            try:
                return f(*args, **kwargs)
            except Exception as e:
                _fail = isinstance(e, tuple(fail_on)) if instance_match else type(e) in fail_on
                if _fail:
                    log.warning('Giving up. Re-raising exception %s (as requested by `fail_on` arg)', type(e))
                    raise e
                
                if max_ignore is not False and ignore_count > max_ignore:
                    log.warning('Giving up. Ignored too many exceptions (max_ignore: %d, ignore_count: %d). '
                                'Re-raising exception %s.', max_ignore, ignore_count, type(e))
                    raise e
                
                if retries < max_retries:
                    log.info('%s - %s', type(e), str(e))
                    log.info(retry_msg, f.__name__, max_retries - retries)
                    sleep(delay)
                    
                    # If 'instance_match' is enabled, we check if the exception was an instance of any of the passed exception types,
                    # otherwise we use exact exception type comparison against the list.
                    # _ignore is True if we should ignore this exception (don't increment retries), or False if we should increment.
                    _ignore = isinstance(e, tuple(ignore_ex)) if instance_match else type(e) in ignore_ex
                    if _ignore:
                        log.debug(
                            " >> (?) Ignoring exception '%s' as exception is in 'ignore' list. Ignore Count: %d // "
                            "Max Ignores: %d // Instance Match: %s", type(e), ignore_count, max_ignore, instance_match
                        )
                    kwargs['retry_attempts'] = retries if _ignore else retries + 1
                    kwargs['ignore_count'] = ignore_count + 1 if _ignore else ignore_count
                    
                    return wrapper(*args, **kwargs)
                log.exception(fail_msg, f.__name__, max_retries)
                raise e
        return wrapper
    return _decorator


def async_retry(max_retries: int = 3, delay: Union[int, float] = 3, **retry_conf):
    """
    AsyncIO coroutine compatible version of :func:`.retry_on_err` - for painless automatic retry-on-exception for async code.
    
    Decorates an AsyncIO coroutine (``async def``) function or class method, wraps the function/method with a try/catch block, and
    will automatically re-run the function with the same arguments up to `max_retries` time after any exception is raised, with a
    ``delay`` second delay between re-tries.

    If it still throws an exception after ``max_retries`` retries, it will log the exception details with ``fail_msg``,
    and then re-raise it.
    
    Usage (retry up to 5 times, 1 second between retries, stop immediately if IOError is detected)::
    
        >>> from privex.helpers import async_retry
        >>>
        >>> @async_retry(5, 1, fail_on=[IOError])
        ... async def my_func(some=None, args=None):
        ...     if some == 'io': raise IOError()
        ...     raise FileExistsError()
        ...
    
    This will be re-ran 5 times, 1 second apart after each exception is raised, before giving up::

        >>> await my_func()

    Where-as this one will immediately re-raise the caught IOError on the first attempt, as it's passed in ``fail_on``::

        >>> await my_func('io')
    
    We can also use ``ignore_on`` to "ignore" certain exceptions. Ignored exceptions cause the function to be retried with a delay, as
    normal, but without incrementing the total retries counter.
    
        >>> from privex.helpers import async_retry
        >>> import random
        >>>
        >>> @async_retry(5, 1, fail_on=[IOError], ignore=[ConnectionResetError])
        ... async def my_func(some=None, args=None):
        ...     if random.randint(1,10) > 7: raise ConnectionResetError()
        ...     if some == 'io': raise IOError()
        ...     raise FileExistsError()
        ...
    
    To show this at work, we've enabled debug logging for you to see::
        
        >>> await my_func()
        [INFO]    <class 'ConnectionResetError'> -
        [INFO]    Exception while running 'my_func', will retry 5 more times.
        [DEBUG]   >> (?) Ignoring exception '<class 'ConnectionResetError'>' as exception is in 'ignore' list.
                  Ignore Count: 0 // Max Ignores: 100 // Instance Match: False
        
        [INFO]    <class 'FileExistsError'> -
        [INFO]    Exception while running 'my_func', will retry 5 more times.
        
        [INFO]    <class 'ConnectionResetError'> -
        [INFO]    Exception while running 'my_func', will retry 4 more times.
        [DEBUG]   >> (?) Ignoring exception '<class 'ConnectionResetError'>' as exception is in 'ignore' list.
                  Ignore Count: 1 // Max Ignores: 100 // Instance Match: False
        
        [INFO]    <class 'FileExistsError'> -
        [INFO]    Exception while running 'my_func', will retry 4 more times.
    
    As you can see above, when an ignored exception (``ConnectionResetError``) occurs, the remaining retry attempts doesn't go down.
    Instead, only the "Ignore Count" goes up.
    
    .. Attention:: For safety reasons, by default ``max_ignore`` is set to ``100``. This means after 100 retries where an
                   exception was ignored, the decorator will give up and raise the last exception.
                   
                   This is to prevent the risk of infinite loops hanging your application. If you are 100% certain that the
                   function you've wrapped, and/or the exceptions passed in ``ignore`` cannot cause an infinite retry loop, then
                   you can pass ``max_ignore=False`` to the decorator to disable failure after ``max_ignore`` ignored exceptions.
    
    
    :param int max_retries:  Maximum total retry attempts before giving up
    :param float delay:      Amount of time in seconds to sleep before re-trying the wrapped function
    :param retry_conf:       Less frequently used arguments, pass in as keyword args (see below)
    
    :key list fail_on:  A list() of Exception types that should result in immediate failure (don't retry, raise)
    
    :key list ignore:   A list() of Exception types that should be ignored (will retry, but without incrementing the failure counter)

    :key int|bool max_ignore: (Default: ``100``) If an exception is raised while retrying, and more than this
             many exceptions (listed in ``ignore``) have been ignored during retry attempts, then give up
             and raise the last exception.
             
             This feature is designed to prevent "ignored" exceptions causing an infinite retry loop. By
             default ``max_ignore`` is set to ``100``, but you can increase/decrease this as needed.
             
             You can also set it to ``False`` to disable raising when too many exceptions are ignored - however, it's
             strongly not recommended to disable ``max_ignore``, especially if you have ``instance_match=True``,
             as it could cause an infinite retry loop which hangs your application.
      
    
    :key bool instance_match: (Default: ``False``) If this is set to ``True``, then the exception type comparisons for ``fail_on``
            and ``ignore`` will compare using ``isinstance(e, x)`` instead of ``type(e) is x``.
            
            If this is enabled, then exceptions listed in ``fail_on`` and ``ignore`` will also **match sub-classes** of
            the listed exceptions, instead of exact matches.

    :key str retry_msg: Override the log message used for retry attempts. First message param %s is func name,
                        second message param %d is retry attempts remaining

    :key str fail_msg: Override the log message used after all retry attempts are exhausted. First message param %s
                       is func name, and second param %d is amount of times retried.
    
    """
    retry_msg: str = retry_conf.get('retry_msg', DEF_RETRY_MSG)
    fail_msg: str = retry_conf.get('fail_msg', DEF_FAIL_MSG)
    instance_match: bool = is_true(retry_conf.get('instance_match', False))
    fail_on: List[type] = list(retry_conf.get('fail_on', []))
    ignore_ex: List[type] = list(retry_conf.get('ignore', []))
    max_ignore: Union[bool, int] = retry_conf.get('max_ignore', 100)
    
    def _decorator(f):
        @functools.wraps(f)
        async def wrapper(*args, **kwargs):
            retries = int(kwargs.pop('retry_attempts', 0))
            ignore_count = int(kwargs.pop('ignore_count', 0))
            
            try:
                return await f(*args, **kwargs)
            except Exception as e:
                # If instance_match is enabled, check exception type using isinstance, otherwise use exact type matches
                _fail = isinstance(e, tuple(fail_on)) if instance_match else type(e) in fail_on
                if _fail:
                    log.warning('Giving up. Re-raising exception %s (as requested by `fail_on` arg)', type(e))
                    raise e
                
                if max_ignore is not False and ignore_count > max_ignore:
                    log.warning('Giving up. Ignored too many exceptions (max_ignore: %d, ignore_count: %d). '
                                'Re-raising exception %s.', max_ignore, ignore_count, type(e))
                    raise e
                
                if retries < max_retries:
                    log.info('%s - %s', type(e), str(e))
                    log.info(retry_msg, f.__name__, max_retries - retries)
                    await asyncio.sleep(delay)
                    
                    # If 'instance_match' is enabled, we check if the exception was an instance of any of the passed exception types,
                    # otherwise we use exact exception type comparison against the list.
                    # _ignore is True if we should ignore this exception (don't increment retries), or False if we should increment.
                    _ignore = isinstance(e, tuple(ignore_ex)) if instance_match else type(e) in ignore_ex
                    if _ignore:
                        log.debug(
                            " >> (?) Ignoring exception '%s' as exception is in 'ignore' list. Ignore Count: %d // "
                            "Max Ignores: %d // Instance Match: %s", type(e), ignore_count, max_ignore, instance_match
                        )
                    kwargs['retry_attempts'] = retries if _ignore else retries + 1
                    kwargs['ignore_count'] = ignore_count + 1 if _ignore else ignore_count
                    
                    return await wrapper(*args, **kwargs)
                log.exception(fail_msg, f.__name__, max_retries)
                raise e
        
        return wrapper
    
    return _decorator


class FormatOpt(Enum):
    """
    This enum represents various options available for :py:func:`.r_cache` 's ``format_opt`` parameter.

    To avoid bloating the PyDoc for ``r_cache`` too much, descriptions for each formatting option is available as a
    short PyDoc comment under each enum option.

    Usage:

    >>> @r_cache('mykey', format_args=[0, 'x'], format_opt=FormatOpt.POS_AUTO)

    """
    POS_AUTO = 'force_pos'
    """
    First attempt to format using ``*args`` whitelisted in ``format_args``, if that causes a KeyError/IndexError,
    then pass kwarg values in the order they're listed in ``format_args``
    (only includes kwarg names listed in ``format_args``)

    # def func(x, y)
    func('a', 'b')      # assuming 0 and 1 are in format_args, then it would use .format('a', 'b')
    func(y='b', x='a')  # assuming format_args = ``['x','y']``, then it would use .format('a', 'b')
    """

    POS_ONLY = 'pos_only'
    """Only use positional args for formatting the cache key, kwargs will be ignored completely."""

    KWARG_ONLY = 'kwarg'
    """Only use kwargs for formatting the cache key - requires named format placeholders, i.e. ``mykey:{x}``"""

    MIX = 'mix'
    """
    Use both ``*args`` and ``**kwargs`` to format the cache_key (assuming mixed placeholders e.g. ``mykey:{}:{y}``
    """


FO = FormatOpt


def _format_key(args, kwargs, cache_key: str, whitelist: bool = True, fmt_opt: FO = FO.POS_AUTO, fmt_args: list = None):
    """Internal function used by :func:`.r_cache` and :func:`.r_cache_async` for formatting a cache key e.g. ``pvx:{}:{}``"""
    pos_args = args
    kw_args = kwargs
    if whitelist:
        # Whitelisted positional arguments
        pos_args = [args[i] for i in fmt_args if type(i) is int and len(args) > i]
        # Whitelisted keyword args, as a dict
        kw_args = {i: kwargs[i] for i in fmt_args if type(i) is str and i in kwargs}
    
    if fmt_opt == FormatOpt.POS_AUTO:
        log.debug('Format: POS_AUTO - Formatting with *args, fallback on err to positional **kwargs values')
        try:
            log.debug('Attempting to format with args: %s', pos_args)
            rk = cache_key.format(*pos_args)
        except (KeyError, IndexError):
            pos_kwargs = [v for _, v in kw_args.items()]
            log.debug('Failed to format with pos args, now trying positional kwargs: %s', pos_kwargs)
            rk = cache_key.format(*pos_kwargs)
        return rk
    
    if fmt_opt == FormatOpt.KWARG_ONLY:  # Only attempt to format cache_key using kwargs
        log.debug('Format: KWARG_ONLY - Formatting using only **kwargs')
        return cache_key.format(**kw_args)
    
    if fmt_opt == FormatOpt.POS_ONLY:  # Only attempt to format cache_key using positional args
        log.debug('Format: POS_ONLY - Formatting using only *args')
        return cache_key.format(*pos_args)
    
    if fmt_opt == FormatOpt.MIX:  # Format cache_key with both positional and kwargs as-is
        log.debug('Format: MIX - Formatting using passthru *args and **kwargs')
        return cache_key.format(*pos_args, **kw_args)


def r_cache_async(cache_key: Union[str, callable], cache_time=300, format_args: list = None, format_opt: FO = FO.POS_AUTO, **opts) -> Any:
    """
    Async function/method compatible version of :func:`.r_cache` - see docs for :func:`.r_cache`
    
    You can bypass caching by passing ``r_cache=False`` to the wrapped function.
    
    Basic usage::
    
        >>> from privex.helpers import r_cache_async
        >>> @r_cache_async('my_cache_key')
        >>> async def some_func(some: int, args: int = 2):
        ...     return some + args
        >>> await some_func(5, 10)
        15
        
        >>> # If we await some_func a second time, we'll get '15' again because it was cached.
        >>> await some_func(2, 3)
        15
    
    Async ``cache_key`` generation (you can also use normal synchronous functions/lambdas)::
    
        >>> from privex.helpers import r_cache_async
        >>>
        >>> async def make_key(name, title):
        ...     return f"mycache:{name}"
        ...
        >>> @r_cache_async(make_key)
        ... async def who(name, title):
        ...     return "Their name is {title} {name}"
        ...
        
    :param FormatOpt format_opt: (default: :py:attr:`.FormatOpt.POS_AUTO`) "Format option" - how should args/kwargs be
                                 used when filling placeholders in the ``cache_key`` (see comments on FormatOption)
    :param list format_args: A list of positional arguments numbers (e.g. ``[0, 1, 2]``) and/or kwargs
                             ``['x', 'y', 'z']`` that should be used to format the `cache_key`
    :param str cache_key: The cache key to store the cached data into, e.g. `mydata`
    :param int cache_time: The amount of time in seconds to cache the result for (default: 300 seconds)
    :keyword bool whitelist: (default: ``True``) If True, only use specified arg positions / kwarg keys when formatting
                             ``cache_key`` placeholders. Otherwise, trust whatever args/kwargs were passed to the func.
    :return Any res: The return result, either from the wrapped function, or from the cache.
    """
    fmt_args = [] if not format_args else format_args
    # Using normal 'cached' often results in "event loop already running" errors due to the synchronous async wrapper
    # in CacheWrapper. So to be safe, we get the adapter directly to avoid issues.
    cache_adapter = async_adapter_get()
    whitelist = opts.get('whitelist', True)
    
    def _decorator(f):
        @functools.wraps(f)
        async def wrapper(*args, **kwargs):
            
            # Extract r_cache and r_cache_key from the wrapped function's kwargs if they're specified,
            # then remove them from the kwargs so they don't interfere with the wrapped function.
            enable_cache, rk = kwargs.get('r_cache', True), kwargs.get('r_cache_key', cache_key)
            if 'r_cache' in kwargs: del kwargs['r_cache']
            if 'r_cache_key' in kwargs: del kwargs['r_cache_key']

            if not isinstance(rk, str):
                rk = await await_if_needed(rk, *args, **kwargs)
            elif not empty(fmt_args, itr=True) or not whitelist:
                # If the cache key contains a format placeholder, e.g. {somevar} - then attempt to replace the
                # placeholders using the function's kwargs
                log.debug('Format_args not empty (or whitelist=False), formatting cache_key "%s"', cache_key)
                rk = _format_key(args, kwargs, cache_key=cache_key, whitelist=whitelist, fmt_opt=format_opt, fmt_args=format_args)
            # To ensure no event loop / thread cache instance conflicts, we use the cache adapter as a context manager, which
            # is supposed to disconnect + destroy the connection library instance, and re-create it in the current loop/thread.
            async with cache_adapter as r:
                # If using an async cache adapter, r.get might be async...
                log.debug('Trying to load "%s" from cache', rk)
                data = await await_if_needed(r.get, rk)
                
                if empty(data) or not enable_cache:
                    log.debug('Not found in cache, or "r_cache" set to false. Calling wrapped async function.')
                    data = await await_if_needed(f, *args, **kwargs)
    
                    # If using an async cache adapter, r.get might be async...
                    await await_if_needed(r.set, rk, data, timeout=cache_time)
            
            return data
        
        return wrapper
    
    return _decorator


def r_cache(cache_key: Union[str, callable], cache_time=300, format_args: list = None,
            format_opt: FO = FO.POS_AUTO, **opts) -> Any:
    """
    This is a decorator which caches the result of the wrapped function with the global cache adapter from
    :py:mod:`privex.helpers.cache` using the key ``cache_key`` and with an expiry of ``cache_time`` seconds.

    Future calls to the wrapped function would then load the data from cache until the cache expires, upon which it
    will re-run the original code and re-cache it.

    To bypass the cache, pass kwarg ``r_cache=False`` to the wrapped function. To override the cache key on demand,
    pass ``r_cache_key='mykey'`` to the wrapped function.

    **Example usage**:

        >>> from privex.helpers import r_cache
        >>>
        >>> @r_cache('mydata', cache_time=600)
        ... def my_func(*args, **kwargs):
        ...     time.sleep(60)
        ...     return "done"

        This will run the function and take 60 seconds to return while it sleeps

        >>> my_func()
        done

        This will run instantly because "done" is now cached for 600 seconds

        >>> my_func()
        done

        This will take another 60 seconds to run because ``r_cache`` is set to `False` (disables the cache)

        >>> my_func(r_cache=False)
        done

    **Using a dynamic cache_key**:

        **Simplest and most reliable - pass ``r_cache_key`` as an additional kwarg**

        If you don't mind passing an additional kwarg to your function, then the most reliable method is to override
        the cache key by passing ``r_cache_key`` to your wrapped function.

        Don't worry, we remove both ``r_cache`` and ``r_cache_key`` from the kwargs that actually hit your function.

        >>> my_func(r_cache_key='somekey')    # Use the cache key 'somekey' when caching data for this function

        **Option 2. Pass a callable which takes the same arguments as the wrapped function**

        In the example below, ``who`` takes two arguments: ``name`` and ``title`` - we then pass the function
        ``make_key`` which takes the same arguments - ``r_cache`` will detect that the cache key is a function
        and call it with the same ``(*args, **kwargs)`` passed to the wrapped function.

        >>> from privex.helpers import r_cache
        >>>
        >>> def make_key(name, title):
        ...     return f"mycache:{name}"
        ...
        >>> @r_cache(make_key)
        ... def who(name, title):
        ...     return "Their name is {title} {name}"
        ...

        We can also obtain the same effect with a ``lambda`` callable defined directly inside of the cache_key.

        >>> @r_cache(lambda name,title: f"mycache:{name}")
        ... def who(name, title):
        ...     return "Their name is {title} {name}"

        **Option 3. Can be finnicky - using ``format_args`` to integrate with existing code**

        If you can't change how your existing function/method is called, then you can use the ``format_args`` feature.

        **NOTE:** Unless you're forcing the usage of kwargs with a function/method, it's strongly recommended that you
        keep ``force_pos`` enabled, and specify both the positional argument ID, and the kwarg name.

        Basic Example:

        >>> from privex.helpers import r_cache
        >>> import time
        >>>
        >>> @r_cache('some_cache:{}:{}', cache_time=600, format_args=[0, 1, 'x', 'y'])
        ... def some_func(x=1, y=2):
        ...     time.sleep(5)
        ...     return 'x + y = {}'.format(x + y)
        >>>

        Using positional arguments, we can see from the debug log that it's formatting the ``{}:{}`` in the key
        with ``x:y``

        >>> some_func(1, 2)
        2019-08-21 06:58:29,823 lg  DEBUG    Trying to load "some_cache:1:2" from cache
        2019-08-21 06:58:29,826 lg  DEBUG    Not found in cache, or "r_cache" set to false. Calling wrapped function.
        'x + y = 3'
        >>> some_func(2, 3)
        2019-08-21 06:58:34,831 lg  DEBUG    Trying to load "some_cache:2:3" from cache
        2019-08-21 06:58:34,832 lg  DEBUG    Not found in cache, or "r_cache" set to false. Calling wrapped function.
        'x + y = 5'

        When we passed ``(1, 2)`` and ``(2, 3)`` it had to re-run the function for each. But once we re-call it for
        the previously ran ``(1, 2)`` - it's able to retrieve the cached result just for those args.

        >>> some_func(1, 2)
        2019-08-21 06:58:41,752 lg  DEBUG    Trying to load "some_cache:1:2" from cache
        'x + y = 3'

        Be warned that the default format option ``POS_AUTO`` will make kwargs' values be specified in the same order as
        they were listed in ``format_args``

        >>> some_func(y=1, x=2)   # ``format_args`` has the kwargs in the order ``['x', 'y']`` thus ``.format(x,y)``
        2019-08-21 06:58:58,611 lg  DEBUG    Trying to load "some_cache:2:1" from cache
        2019-08-21 06:58:58,611 lg  DEBUG    Not found in cache, or "r_cache" set to false. Calling wrapped function.
        'x + y = 3'


    :param FormatOpt format_opt: (default: :py:attr:`.FormatOpt.POS_AUTO`) "Format option" - how should args/kwargs be
                                 used when filling placeholders in the ``cache_key`` (see comments on FormatOption)
    :param list format_args: A list of positional arguments numbers (e.g. ``[0, 1, 2]``) and/or kwargs
                             ``['x', 'y', 'z']`` that should be used to format the `cache_key`
    :param str cache_key: The cache key to store the cached data into, e.g. `mydata`
    :param int cache_time: The amount of time in seconds to cache the result for (default: 300 seconds)
    :keyword bool whitelist: (default: ``True``) If True, only use specified arg positions / kwarg keys when formatting
                             ``cache_key`` placeholders. Otherwise, trust whatever args/kwargs were passed to the func.
    :return Any res: The return result, either from the wrapped function, or from the cache.
    """
    fmt_args = [] if not format_args else format_args
    r = cached
    whitelist = opts.get('whitelist', True)

    def _decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):

            # Extract r_cache and r_cache_key from the wrapped function's kwargs if they're specified,
            # then remove them from the kwargs so they don't interfere with the wrapped function.
            enable_cache, rk = kwargs.get('r_cache', True), kwargs.get('r_cache_key', cache_key)
            if 'r_cache' in kwargs: del kwargs['r_cache']
            if 'r_cache_key' in kwargs: del kwargs['r_cache_key']

            if callable(rk):
                rk = rk(*args, **kwargs)
            elif not empty(fmt_args, itr=True) or not whitelist:
                # If the cache key contains a format placeholder, e.g. {somevar} - then attempt to replace the
                # placeholders using the function's kwargs
                log.debug('Format_args not empty (or whitelist=False), formatting cache_key "%s"', cache_key)
                rk = _format_key(args, kwargs, cache_key=cache_key, whitelist=whitelist, fmt_opt=format_opt, fmt_args=format_args)
            log.debug('Trying to load "%s" from cache', rk)
            data = r.get(rk)

            if empty(data) or not enable_cache:
                log.debug('Not found in cache, or "r_cache" set to false. Calling wrapped function.')
                data = f(*args, **kwargs)
                r.set(rk, data, timeout=cache_time)

            return data

        return wrapper

    return _decorator


def mock_decorator(*dec_args, **dec_kwargs):
    """
    This decorator is a pass-through decorator which does nothing other than be a decorator.
    
    It's designed to be used with the :class:`privex.helpers.common.Mocker` class when mocking classes/modules,
    allowing you to add fake decorators to the mock class/method which do nothing, other than act like a decorator
    without breaking your functions/methods.
    """
    def _decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper
    return _decorator

