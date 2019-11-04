"""
Class Method / Function decorators

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
import functools
import logging
from enum import Enum
from time import sleep
from typing import Any, Union

from privex.helpers.cache import cached
from privex.helpers.common import empty


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

    Usage (retry up to 5 times, 1 second between retries, stop immediately if IOError is detected):

        >>> @retry_on_err(5, 1, fail_on=[IOError])
        ... def my_func(self, some=None, args=None):
        ...     if some == 'io': raise IOError()
        ...      raise FileExistsError()

    This will be re-ran 5 times, 1 second apart after each exception is raised, before giving up:

        >>> my_func()

    Where-as this one will immediately re-raise the caught IOError on the first attempt, as it's passed in ``fail_on``:

        >>> my_func('io')


    :param int max_retries:  Maximum total retry attempts before giving up
    :param float delay:      Amount of time in seconds to sleep before re-trying the wrapped function
    :param retry_conf:       Less frequently used arguments, pass in as keyword args:

    - (list) fail_on:  A list() of Exception types that should result in immediate failure (don't retry, raise)

    - (str) retry_msg: Override the log message used for retry attempts. First message param %s is func name,
      second message param %d is retry attempts remaining

    - (str) fail_msg:  Override the log message used after all retry attempts are exhausted. First message param %s
      is func name, and second param %d is amount of times retried.

    """
    retry_msg = retry_conf['retry_msg'] if 'retry_msg' in retry_conf else DEF_RETRY_MSG
    fail_msg = retry_conf['fail_msg'] if 'fail_msg' in retry_conf else DEF_FAIL_MSG
    fail_on = list(retry_conf['fail_on']) if 'fail_on' in retry_conf else []

    def _decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            retries = 0
            if 'retry_attempts' in kwargs:
                retries = int(kwargs['retry_attempts'])
                del kwargs['retry_attempts']

            try:
                return f(*args, **kwargs)
            except Exception as e:
                if type(e) in fail_on:
                    log.warning('Giving up. Re-raising exception %s (as requested by `fail_on` arg)', type(e))
                    raise e
                if retries < max_retries:
                    log.info('%s - %s', type(e), str(e))
                    log.info(retry_msg, f.__name__, max_retries - retries)
                    sleep(delay)
                    kwargs['retry_attempts'] = retries + 1
                    return wrapper(*args, **kwargs)
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

    :param bool whitelist: (default: ``True``) If True, only use specified arg positions / kwarg keys when formatting
                           ``cache_key`` placeholders. Otherwise, trust whatever args/kwargs were passed to the func.
    :param FormatOpt format_opt: (default: :py:attr:`.FormatOpt.POS_AUTO`) "Format option" - how should args/kwargs be
                                 used when filling placeholders in the ``cache_key`` (see comments on FormatOption)
    :param list format_args: A list of positional arguments numbers (e.g. ``[0, 1, 2]``) and/or kwargs
                             ``['x', 'y', 'z']`` that should be used to format the `cache_key`
    :param str cache_key: The cache key to store the cached data into, e.g. `mydata`
    :param int cache_time: The amount of time in seconds to cache the result for (default: 300 seconds)
    :return Any res: The return result, either from the wrapped function, or from the cache.
    """
    fmt_args = [] if not format_args else format_args
    r = cached
    whitelist = opts.get('whitelist', True)

    def format_key(args, kwargs):
        pos_args = args
        kw_args = kwargs
        if whitelist:
            # Whitelisted positional arguments
            pos_args = [args[i] for i in fmt_args if type(i) is int and len(args) > i]
            # Whitelisted keyword args, as a dict
            kw_args = {i: kwargs[i] for i in fmt_args if type(i) is str and i in kwargs}

        if format_opt == FormatOpt.POS_AUTO:
            log.debug('Format: POS_AUTO - Formatting with *args, fallback on err to positional **kwargs values')
            try:
                log.debug('Attempting to format with args: %s', pos_args)
                rk = cache_key.format(*pos_args)
            except (KeyError, IndexError):
                pos_kwargs = [v for _, v in kw_args.items()]
                log.debug('Failed to format with pos args, now trying positional kwargs: %s', pos_kwargs)
                rk = cache_key.format(*pos_kwargs)
            return rk

        if format_opt == FormatOpt.KWARG_ONLY:  # Only attempt to format cache_key using kwargs
            log.debug('Format: KWARG_ONLY - Formatting using only **kwargs')
            return cache_key.format(**kw_args)

        if format_opt == FormatOpt.POS_ONLY:  # Only attempt to format cache_key using positional args
            log.debug('Format: POS_ONLY - Formatting using only *args')
            return cache_key.format(*pos_args)

        if format_opt == FormatOpt.MIX:  # Format cache_key with both positional and kwargs as-is
            log.debug('Format: MIX - Formatting using passthru *args and **kwargs')
            return cache_key.format(*pos_args, **kw_args)

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
                rk = format_key(args, kwargs)
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

