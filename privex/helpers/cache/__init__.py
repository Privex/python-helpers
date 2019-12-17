"""
Helper functions/classes related to caching.

This module acts as a singleton wrapper, allowing for easily setting a framework-independent global cache API.

To make the module easy to use, :py:func:`.adapter_get` initialises an instance of :class:`.MemoryCache` if no
global cache adapter instance has been setup. This means you can use the various alias functions in this module
without having to configure a cache adapter.

Available Cache Adapters
----------------------------------------------------

**Standard Synchronous Adapters**

Two synchronous cache adapters are included by default - :class:`.MemoryCache` (dependency free), and
:class:`.RedisCache` (needs ``redis`` library).

While these synchronous classes don't support coroutines for most methods, as of privex-helpers 2.7 the method
:meth:`privex.helpers.cache.CacheAdapter.CacheAdapter.get_or_set_async` is an async version of :meth:`.CacheAdapter.get_or_set`,
and is available on all :class:`.CacheAdapter` sub-classes (both :class:`.MemoryCache` and :class:`.RedisCache`).
``get_or_set_async`` allows a coroutine or coroutine function/method reference to be passed as the fallback value.

    ==============================   ==================================================================================================
    Adapter                          Description
    ==============================   ==================================================================================================
    :class:`.CacheAdapter`           This is the base class for all synchronous cache adapters (doesn't do anything)
    :class:`.MemoryCache`            A cache adapter which stores cached items in memory using a dict. Fully functional incl. timeout.
    :class:`.RedisCache`             A cache adapter for `Redis`_ using the python library ``redis``
    ==============================   ==================================================================================================

**Asynchronous (Python AsyncIO) Adapters**

Over the past few years, Python's AsyncIO has grown more mature and has gotten a lot of attention. Thankfully, whether you use
AsyncIO or not, we've got you covered.

Three AsyncIO cache adapters are included by default - :class:`.AsyncMemoryCache` (dependency free),
:class:`.AsyncRedisCache` (needs ``aioredis`` library), and :class:`.AsyncMemcachedCache` (needs ``aiomcache`` library).

    ==============================   ==================================================================================================
    Adapter                          Description
    ==============================   ==================================================================================================
    :class:`.AsyncCacheAdapter`      This is the base class for all AsyncIO cache adapters (abstract class, only implements get_or_set)
    :class:`.AsyncMemoryCache`       A cache adapter which stores cached items in memory using a dict. Fully functional incl. timeout.
    :class:`.AsyncRedisCache`        A cache adapter for `Redis`_ using the AsyncIO python library ``aioredis``
    :class:`.AsyncMemcachedCache`    A cache adapter for `Memcached`_ using the AsyncIO python library ``aiomcache``
    ==============================   ==================================================================================================


.. _Redis: https://redis.io/
.. _Memcached: https://www.memcached.org/


Setting / updating the global cache adapter instance
----------------------------------------------------

First import the ``cache`` module.

    >>> from privex.helpers import cache

You must instantiate your cache adapter of choice before passing it to :py:func:`.adapter_set` - which updates
the global cache adapter instance.

    >>> my_adapter = cache.MemoryCache()
    >>> cache.adapter_set(my_adapter)

Once you've set the adapter, you can use the module functions such as :py:func:`.get` and :py:func:`.set` - or you
can import ``cached`` to enable dictionary-like cache item access.

    >>> cache.set('hello', 'world')
    >>> cache.get('hello')
    'world'
    >>> from privex.helpers import cached
    >>> cached['hello']
    'world'
    >>> cached['otherkey'] = 'testing'

You can also use AsyncIO adapters with the global cache adapter wrapper. :class:`.CacheWrapper` uses :func:`.awaitable` to
ensure that AsyncIO adapters can work synchronously when being called from a synchronous function, while working asynchronously
from a non-async function.


    >>> my_adapter = cache.AsyncRedisCache()
    >>> cache.adapter_set(my_adapter)
    >>>
    >>> # get_hello_async() is async, so @awaitable returns the normal .get() coroutine for awaiting
    >>> async def get_hello_async():
    ...     result = await cached.get('hello')
    ...     return result
    ...
    >>> # get_hello() is synchronous, so @awaitable seamlessly runs .get() in an event loop and returns
    >>> # the result - get_hello() can treat it as if it were just a normal synchronous function.
    >>> def get_hello():
    ...     return cached.get('hello')
    ...
    >>> get_hello()
    'world'
    >>> await get_hello_async()
    'world'


Plug-n-play usage
-----------------

As explained near the start of this module's documentation, you don't have to set the global adapter if you only
plan on using the simple :class:`.MemoryCache` adapter.

Just start using the global cache API via either :py:mod:`privex.helpers.cache` or :py:mod:`privex.helpers.cache.cached`
and MemoryCache will automatically be instantiated as the global adapter as soon as something attempts to access
the global instance.

We recommend importing ``cached`` rather than ``cache``, as it acts as a wrapper that allows dictionary-like
cache key getting/setting, and is also immediately aware when the global cache adapter is set/replaced.

    >>> from privex.helpers import cached

You can access ``cached`` like a dictionary to get and set cache keys (they will use the default expiry time of
:py:attr:`privex.helpers.settings.DEFAULT_CACHE_TIMEOUT`)

    >>> cached['testing'] = 123
    >>> cached['testing']
    123


You can also call methods such as :py:func:`.get` and :py:func:`.set` for getting/setting cache items with more
control, for example:

1. Setting a custom expiration, or disabling expiration by setting timeout to ``None``
  
    >>> cached.set('example', 'test', timeout=30)   # Drop 'example' from the cache after 30 seconds from now.
    >>> cached.set('this key', 'is forever!', timeout=None) # A timeout of ``None`` disables automatic expiration.

2. Fallback values when a key isn't found, or have it throw an exception if it's not found instead.

    >>> cached.get('example', 'NOT FOUND')          # If the key 'example' doesn't exist, return 'NOT FOUND'
    'test'
    
    >>> try:   # By setting ``fail`` to True, ``get`` raises ``CacheNotFound`` if the key doesn't exist / is expired
    ...     cached.get('nonexistent', fail=True)
    ... except CacheNotFound:
    ...     log.error('The cache key "nonexistent" does not exist!')
    >>>

3. Using :py:func:`.get_or_set` you can specify either a standard type (e.g. ``str``, ``int``, ``dict``), or even
   a custom function to call to obtain the value to set and return.
 
    >>> cached.get_or_set('hello', lambda key: 'world', timeout=60)
    >>> cached['hello']
    'world'


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
import logging

from privex.helpers.asyncx import awaitable

log = logging.getLogger(__name__)

from typing import Any, Optional, Union, Type

from privex.helpers.cache.CacheAdapter import CacheAdapter
from privex.helpers.cache.MemoryCache import MemoryCache

try:
    from privex.helpers.cache.RedisCache import RedisCache
except ImportError:
    log.debug("[%s] Failed to import %s from %s (missing package 'redis' maybe?)", __name__, 'RedisCache', f'{__name__}.RedisCache')

try:
    from privex.helpers.cache.asyncx import *
except ImportError:
    log.exception("[%s] Failed to import %s from %s (unknown error!)", __name__, '*', f'{__name__}.asyncx')
    
# try:
#     from privex.helpers.cache.asyncx import AsyncMemoryCache
#     from privex.helpers.cache.asyncx import AsyncCacheAdapter
# except ImportError:
#     log.exception(
#         "[%s] Failed to import AsyncMemoryCache and/or AsyncCacheAdapter from privex.helpers.cache.asyncx...", __name__
#     )

from privex.helpers.exceptions import NotConfigured, CacheNotFound
from privex.helpers.settings import DEFAULT_CACHE_TIMEOUT


__STORE = {}

__STORE['adapter']: CacheAdapter


class CacheWrapper(object):
    """
    **CacheWrapper** is a small class designed to wrap an instance of :class:`.CacheAdapter` and allow
    the adapter to be switched out at any time, using the static class attribute :py:attr:`.cache_instance`.
    
    This class is used for the singleton global variable :py:attr:`.cached`
    
    For convenience, if :py:attr:`.cache_instance` isn't set-up when something makes an adapter-dependant call, then
    the adapter class in :py:attr:`.default_adapter` will be instantiated and stored in :py:class:`.cache_instance`
    
        >>> # Using the ``: CacheAdapter`` type hinting will allow most IDEs to treat the wrapper as if it were
        >>> # a normal CacheAdapter child class, thus showing appropriate completion / usage warnings
        >>> c: CacheAdapter = CacheWrapper()
        >>> c.set('hello', 'world')
        >>> c['hello']
        'world'
    
    You can replace the cache adapter singleton using the module function :py:func:`.adapter_set` (recommended)
    
        >>> from privex.helpers import cache, CacheWrapper
        >>> cache.adapter_set(cache.MemoryCache())   # Set the current adapter for both the cache module, and wrapper.

    If you only plan to use this wrapper, then you can use :py:meth:`.set_adapter` to update the current cache adapter
    instance.
    
        >>> CacheWrapper.set_adapter(cache.MemoryCache())  # Set the adapter only for the wrapper (aka ``cached``)
    
    """
    cache_instance: CacheAdapter = None
    """Holds the singleton instance of a :class:`.CacheAdapter` implementation"""
    
    default_adapter: Type[CacheAdapter] = MemoryCache
    """The default adapter class to instantiate if :py:attr:`.cache_instance` is ``None``"""
    
    @staticmethod
    def get_adapter(default: Type[CacheAdapter] = default_adapter, *args, **kwargs) -> CacheAdapter:
        """
        Attempt to get the singleton cache adapter from :py:attr:`.cache_instance` - if the instance is ``None``, then
        attempt to instantiate ``default()``
        
        If any ``*args`` or ``**kwargs`` are passed, they will be passed through to ``default(*args, **kwargs)`` so
        that any necessary configuration parameters can be passed to the class.
        """
        if not CacheWrapper.cache_instance:
            CacheWrapper.cache_instance = default(*args, **kwargs)
        return CacheWrapper.cache_instance

    @staticmethod
    def set_adapter(adapter: CacheAdapter) -> CacheAdapter:
        CacheWrapper.cache_instance = adapter
        return CacheWrapper.cache_instance

    def __getattr__(self, item):
        if hasattr(super(), item):
            return getattr(self, item)
        
        @awaitable
        def _wrapper(*args, **kwargs):
            with CacheWrapper.get_adapter() as a:
                return getattr(a, item)(*args, **kwargs)
        
        return _wrapper
    
    @awaitable
    def __getitem__(self, item):
        try:
            with CacheWrapper.get_adapter() as a:
                return a.get(key=item, fail=True)
        except CacheNotFound:
            raise KeyError(f'Key "{item}" not found in cache.')

    @awaitable
    def __setitem__(self, key, value):
        with CacheWrapper.get_adapter() as a:
            return a.set(key=key, value=value)


cached: CacheAdapter = CacheWrapper()
"""
This module attribute acts as a singleton, containing an instance of :class:`.CacheWrapper` which is designed
to allow painless usage of this caching module.


"""


def adapter_set(adapter: CacheAdapter):
    """
    Set the global cache adapter instance to ``adapter`` - which should be an instantiated adapter class which
    implements :class:`.CacheAdapter`
    
    **Example**::
    
        >>> from privex.helpers import cache
        >>> cache.adapter_set(cache.MemoryCache())
    
    
    :param CacheAdapter adapter: An instance of a class which implements :class:`.CacheAdapter` for global use.
    :return CacheAdapter adapter: A reference to your adapter from ``__STORE['adapter']``
    """
    __STORE['adapter'] = adapter
    cached.set_adapter(adapter)
    
    return __STORE['adapter']


def adapter_get(default: Type[CacheAdapter] = MemoryCache) -> CacheAdapter:
    """
    Get the global cache adapter instance. If there isn't one, then by default this function will initialise
    :class:`.MemoryAdapter` and set it as the global cache adapter.
    
    To set the global cache adapter instance, use :py:func:`.adapter_set`
    
    To use a different fallback class, pass a class name which implements :class:`.CacheAdapter` like so:
    
        >>> adapter_get(default=MemoryCache)
    
    :param default:
    :return:
    """
    if 'adapter' not in __STORE or __STORE['adapter'] is None:
        if not default:
            raise NotConfigured('No cache adapter has been configured for privex.helpers.cache!')
        __STORE['adapter'] = default()
    return __STORE['adapter']


def get(key: str, default: Any = None, fail: bool = False) -> Any:
    """
    Return the value of cache key ``key``. If the key wasn't found, or it was expired, then ``default`` will be
    returned.
    
    Optionally, you may choose to pass ``fail=True``, which will cause this method to raise :class:`.CacheNotFound`
    instead of returning ``default`` when a key is non-existent / expired.
    
    :param str key: The cache key (as a string) to get the value for, e.g. ``example:test``
    :param Any default: If the cache key ``key`` isn't found / is expired, return this value (Default: ``None``)
    :param bool fail: If set to ``True``, will raise :class:`.CacheNotFound` instead of returning ``default``
                      when a key is non-existent / expired.
    
    :raises CacheNotFound: Raised when ``fail=True`` and ``key`` was not found in cache / expired.
    
    :return Any value: The value of the cache key ``key``, or ``default`` if it wasn't found.
    """
    a = adapter_get()
    return a.get(key=key, default=default, fail=fail)


def set(key: str, value: Any, timeout: Optional[int] = DEFAULT_CACHE_TIMEOUT):
    """
    Set the cache key ``key`` to the value ``value``, and automatically expire the key after ``timeout`` seconds
    from now.
    
    If ``timeout`` is ``None``, then the key will never expire (unless the cache implementation loses it's
    persistence, e.g. memory caches with no disk writes).
    
    :param str key: The cache key (as a string) to set the value for, e.g. ``example:test``
    :param Any value: The value to store in the cache key ``key``
    :param int timeout: The amount of seconds to keep the data in cache. Pass ``None`` to disable expiration.
    """
    a = adapter_get()
    return a.set(key=key, value=value, timeout=timeout)


def get_or_set(key: str, value: Union[Any, callable], timeout: int = DEFAULT_CACHE_TIMEOUT) -> Any:
    """
    Attempt to return the value of ``key`` in the cache. If ``key`` doesn't exist or is expired, then it will be
    set to ``value``, and ``value`` will be returned.
    
    The ``value`` parameter can be any standard type such as ``str`` or ``dict`` - or it can be a callable
    function / method which returns the value to set and return.
    
    **Basic Usage**::
    
        >>> from privex.helpers import cache as c
        >>> c.get('testing')
        None
        >>> c.get_or_set('testing', 'hello world')
        'hello world'
        >>> c.get('testing')
        'hello world'
    
    **Set and get the value from a function if ``key`` didn't exist / was expired**::
    
        >>> def my_func(): return "hello world"
        >>> c.get_or_set('example', my_func)
        'hello world'
        >>> c.get('example')
        'hello world'
    
    :param str key: The cache key (as a string) to get/set the value for, e.g. ``example:test``
    :param Any value: The value to store in the cache key ``key``. Can be a standard type, or a callable function.
    :param int timeout: The amount of seconds to keep the data in cache. Pass ``None`` to disable expiration.
    :return Any value: The value of the cache key ``key``, or ``value`` if it wasn't found.
    """
    a = adapter_get()
    return a.get_or_set(key=key, value=value, timeout=timeout)


def remove(*key: str) -> bool:
    """
    Remove one or more keys from the cache.

    If all cache keys existed before removal, ``True`` will be returned. If some didn't exist (and thus couldn't
    remove), then ``False`` will be returned.

    :param str key: The cache key(s) to remove
    :return bool removed: ``True`` if ``key`` existed and was removed
    :return bool removed: ``False`` if ``key`` didn't exist, and no action was taken.
    """
    a = adapter_get()
    return a.remove(*key)


def update_timeout(key: str, timeout: int = DEFAULT_CACHE_TIMEOUT) -> Any:
    """
    Update the timeout for a given ``key`` to ``datetime.utcnow() + timedelta(seconds=timeout)``

    This method allows keys which are already expired, allowing expired cache keys to have their timeout
    extended **after** expiry.

    **Example**::

        >>> from privex.helpers import cache
        >>> from time import sleep
        >>> cache.set('example', 'test', timeout=60)
        >>> sleep(70)
        >>> cache.update_timeout('example', timeout=60)   # Reset the timeout for ``'example'`` to ``now + 60 seconds``
        >>> cache.get('example')
        'test'

    :param str key: The cache key to update the timeout for
    :param int timeout: Reset the timeout to this many seconds from ``datetime.utcnow()``
    :raises CacheNotFound: Raised when ``key`` was not found in cache (thus cannot extend timeout)
    :return Any value: The value of the cache key
    """
    a = adapter_get()
    return a.update_timeout(key=key, timeout=timeout)

