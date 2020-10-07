"""
AsyncIO-oriented cache adapters for Privex Helpers' caching API.

All cache adapters in this module are designed to be used within AsyncIO functions/methods, as most methods (apart from the constructor)
must be ``await``'ed.

The AsyncIO cache adapters can be used with both sync/async code if they're configured as the global cache adapter with
:func:`privex.helpers.cache.adapter_set` - as the cache wrapper :attr:`privex.helpers.cache.cached` uses the decorator
:func:`.awaitable` to transparently run async functions/methods in an event loop when methods are called from non-async code, while
returning the original async coroutine when called from asynchronous code.

**Using AsyncIO cache adapters with global cache adapter**

First import ``cached``, :func:`.adapter_set`, and the AsyncIO cache adapter(s) you want to set as the shared global adapter.

Create an instance of the cache adapter you want to use, and pass it to ``adapter_set`` like so::

    >>> from privex.helpers.cache import cached, adapter_set, AsyncMemoryCache
    >>>
    >>> aio_mcache = AsyncMemoryCache()
    >>> adapter_set(aio_mcache)         # Set the shared global adapter (cached) to an instance of AsyncMemoryCache
    >>>

When using :attr:`privex.helpers.cache.cached` from a non-async context with an async adapter, you can call methods such as ``get`` and
``set`` as if they were normal synchronous methods - thanks to the decorator :func:`.awaitable`. Example::

    >>> # The variable 'cached' is a reference to a global shared instance of CacheWrapper, which proxies method calls
    >>> # to the current global adapter set using 'adapter_set' (currently AsyncMemoryCache).
    >>> # Thanks to '@awaitable' we can call the async method .set() from a non-async context without needing await
    >>> cached.set('example', 'hello world')
    >>> cached['example'] = 'hello world'
    >>> print('synchronous REPL (cache "example" after):', cached['example'])
    synchronous REPL (cache "example" after): hello world

When using ``cached`` from an asynchronous context (e.g. an async function/method), you should make sure to ``await`` any method
calls - since when an asynchronous context is detected, the :func:`.awaitable` decorator will return async co-routines which
must be awaited, just like any async function::

    >>> # While 'some_async_func' is in an async context, thus it await's method calls as they're plain co-routines
    >>> async def some_async_func():
    ...     print('some_async_func (cache "example" before):', await cached.get('example'))
    ...     await cached.set('example', 'lorem ipsum')
    ...     print('some_async_func (cache "example" after):', await cached.get('example'))
    ...
    >>> await some_async_func()
    some_async_func (cache "example" before): hello world
    some_async_func (cache "example" after): lorem ipsum


**Available Cache Adapters**

 * :class:`.AsyncMemoryCache` - Stores cache entries in your application's memory using a plain ``dict``. Dependency free.

 * :class:`.AsyncRedisCache` - Stores cache entries using a Redis server. Depends on the package ``aioredis``

 * :class:`.AsyncMemcachedCache` - Stores cache entries using a Memcached server. Depends on the package ``aiomcache``

 
"""
import logging

log = logging.getLogger(__name__)

HAS_ASYNC_MEMORY = False
HAS_ASYNC_REDIS = False
HAS_ASYNC_MEMCACHED = False
HAS_ASYNC_SQLITE = False

__all__ = ['HAS_ASYNC_REDIS', 'HAS_ASYNC_MEMORY', 'HAS_ASYNC_MEMCACHED', 'HAS_ASYNC_SQLITE']

try:
    from privex.helpers.cache.asyncx.base import AsyncCacheAdapter
    
    __all__ += ['AsyncCacheAdapter']
except ImportError:
    log.exception("[%s] Failed to import %s from %s (unknown error!)", __name__, 'AsyncCacheAdapter', f'{__name__}.base')

try:
    from privex.helpers.cache.asyncx.AsyncMemoryCache import AsyncMemoryCache

    HAS_ASYNC_MEMORY = True
    __all__ += ['AsyncMemoryCache']
except ImportError:
    log.exception("[%s] Failed to import %s from %s (unknown error!)", __name__, 'AsyncMemoryCache', f'{__name__}.AsyncMemoryCache')

# from privex.helpers.cache.asyncx.AsyncMemoryCache import AsyncMemoryCache

try:
    from privex.helpers.cache.asyncx.AsyncRedisCache import AsyncRedisCache
    
    HAS_ASYNC_REDIS = True
    __all__ += ['AsyncRedisCache']
except ImportError:
    log.debug("[%s] Failed to import %s from %s (missing package 'aioredis' maybe?)",
              __name__, 'AsyncRedisCache', f'{__name__}.AsyncRedisCache')

try:
    from privex.helpers.cache.asyncx.AsyncMemcachedCache import AsyncMemcachedCache
    
    HAS_ASYNC_MEMCACHED = True
    __all__ += ['AsyncMemcachedCache']
except ImportError:
    log.debug("[%s] Failed to import %s from %s (missing package 'aioredis' maybe?)",
              __name__, 'AsyncMemcachedCache', f'{__name__}.AsyncMemcachedCache')

try:
    from privex.helpers.cache.asyncx.AsyncSqliteCache import AsyncSqliteCache
    
    HAS_ASYNC_SQLITE = True
    __all__ += ['AsyncSqliteCache']
except ImportError:
    log.debug("[%s] Failed to import %s from %s (missing package 'privex-db' or 'aiosqlite' maybe?)",
              __name__, 'AsyncSqliteCache', f'{__name__}.AsyncSqliteCache')


