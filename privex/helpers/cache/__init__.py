"""
Helper functions/classes related to caching.

This module acts as a singleton wrapper, allowing for easily setting a framework-independent global cache API.

To make the module easy to use, :py:func:`.adapter_get` initialises an instance of :class:`.MemoryCache` if no
global cache adapter instance has been setup. This means you can use the various alias functions in this module
without having to configure a cache adapter.

Available Cache Adapters
^^^^^^^^^^^^^^^^^^^^^^^^

**Standard Synchronous Adapters**

Four synchronous cache adapters are included by default - :class:`.MemoryCache` (dependency free),
:class:`.MemcachedCache` (needs ``pylibmc`` library), :class:`.SqliteCache` (needs ``privex-db`` library),
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
    :class:`.MemcachedCache`         A cache adapter for `Memcached`_ using the synchronous python library ``pylibmc``
    :class:`.RedisCache`             A cache adapter for `Redis`_ using the python library ``redis``
    :class:`.SqliteCache`            A cache adapter for `SQLite3`_ using the standard Python module :mod:`sqlite3` + :mod:`privex.db`
    ==============================   ==================================================================================================

**Asynchronous (Python AsyncIO) Adapters**

Over the past few years, Python's AsyncIO has grown more mature and has gotten a lot of attention. Thankfully, whether you use
AsyncIO or not, we've got you covered.

Four AsyncIO cache adapters are included by default - :class:`.AsyncMemoryCache` (dependency free),
:class:`.AsyncRedisCache` (needs ``aioredis`` library), :class:`.AsyncSqliteCache` (needs ``aiosqlite`` library),
and :class:`.AsyncMemcachedCache` (needs ``aiomcache`` library).

    ==============================   ==================================================================================================
    Adapter                          Description
    ==============================   ==================================================================================================
    :class:`.AsyncCacheAdapter`      This is the base class for all AsyncIO cache adapters (abstract class, only implements get_or_set)
    :class:`.AsyncMemoryCache`       A cache adapter which stores cached items in memory using a dict. Fully functional incl. timeout.
    :class:`.AsyncRedisCache`        A cache adapter for `Redis`_ using the AsyncIO python library ``aioredis``
    :class:`.AsyncMemcachedCache`    A cache adapter for `Memcached`_ using the AsyncIO python library ``aiomcache``
    :class:`.AsyncSqliteCache`       A cache adapter for `SQLite3`_ using the AsyncIO python library ``aiosqlite``
    ==============================   ==================================================================================================


.. _Redis: https://redis.io/
.. _Memcached: https://www.memcached.org/
.. _SQLite3: https://www.sqlite.org/

Setting / updating the global cache adapter instance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First import the ``cache`` module.

    >>> from privex.helpers import cache

When setting an adapter using :func:`.adapter_set`, if your application has a user configurable cache adapter via
a plain text configuration file (e.g. a ``.env`` file), or you simply don't have any need to manually instantiate a cache adapter,
then you can pass either an alias name (``memory``, ``redis``, ``memcached``, ``sqlite3``), or a full adapter class name
(such as ``MemoryCache``, ``MemcachedCache``, ``RedisCache``, ``SqliteCache``). Example usage::

    >>> cache.adapter_set('memcached')
    >>> cache.adapter_set('MemcachedCache')

Alternatively, you may instantiate your cache adapter of choice before passing it to :py:func:`.adapter_set` - which updates
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

Important info about using the cache abstraction layer with AsyncIO
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

While ``cached`` **usually works** in AsyncIO contexts, due to the synchronous backwards compatibility wrappers, the standard
:class:`.CacheWrapper` can behave strangely in complex AsyncIO applications.

If your application / library is **primarily AsyncIO**, you should use :attr:`.async_cached` ( :class:`.AsyncCacheWrapper` )
instead of the standard :attr:`.cached` - and similarly, the adapter management functions :func:`.async_adapter_get` and
:func:`.async_adapter_set`.

The :class:`.AsyncCacheWrapper` adapter wrapper class - as the name implies - is generally **only** usable from async functions/methods,
and maintains a separate cache adapter instance than :class:`.CacheWrapper` ( :attr:`.cached` ), which **must be an AsyncIO adapter**
such as :class:`.AsyncRedisCache`

The AsyncIO cache abstraction layer / wrapper works pretty much exactly the same as the "hybrid" :class:`.CacheWrapper`,
but to make it clear how it can be used, here's some example code which shows setting/getting the global Async adapter, and
using the cache abstraction layer.

**Examples**

First we'll import the three main AsyncIO cache abstraction functions, plus :class:`.AsyncRedisCache` ::

    >>> from privex.helpers.cache import async_cached, async_adapter_get, async_adapter_set, AsyncRedisCache

We can use the global AsyncIO cache adapter instance (defaults to :class:`.AsyncMemoryCache`) via ``async_cached``::

    >>> await async_cached.set('hello', 'world')
    >>> await async_cached.get('hello')
    'world'

Much like the standard :class:`.CacheWrapper`, you can get and set keys using dict-like syntax, however
since ``__getitem__`` and ``__setitem__`` can't be natively async without Python complaining, they use the wrapper decorator
:func:`.awaitable` for getting, and the synchronous async wrapper function :func:`.loop_run` for setting. The use of these wrappers
may cause problems in certain scenarios, so it's recommended to avoid using the dict-like cache syntax within AsyncIO code::
 
    >>> await async_cached['hello']
    'world'
    >>> async_cached['lorem'] = 'ipsum'

To set / replace the global AsyncIO cache adapter, use :func:`.async_adapter_set` - similarly, you can use :func:`.async_adapter_get`
to get the current adapter instance (e.g. a direct instance of :class:`.AsyncRedisCache` if that's the current adapter)::

    >>> async_adapter_set(AsyncRedisCache())    # Either pass an instance of an async cache adapter class
    >>> async_adapter_set('redis')              # Or pass a simple string alias name, such as: redis, memcached, memory, sqlite3
    >>> adp = async_adapter_get()
    >>> await adp.set('lorem', 'test')  # Set 'lorem' using the AsyncRedisCache instance directly
    >>> await adp.get('lorem')          # Get 'lorem' using the AsyncRedisCache instance directly
    'test'
    >>> await async_cached.get('lorem') # Get 'lorem' using the global AsyncIO cache wrapper
    'test'




Plug-n-play usage
^^^^^^^^^^^^^^^^^

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

    Copyright 2020     Privex Inc.   ( https://www.privex.io )


Cache API Docs
^^^^^^^^^^^^^^

(the above heading is for sidebar display purposes on the docs)


"""
import asyncio
import logging
import importlib
from inspect import isclass

from privex.helpers import plugin, settings
from privex.helpers.common import empty_if, LayeredContext
from privex.helpers.asyncx import awaitable, await_if_needed, loop_run

from privex.helpers.collections import DictObject

log = logging.getLogger(__name__)

from typing import Any, Optional, Union, Type, List
from privex.helpers.cache.CacheAdapter import CacheAdapter
from privex.helpers.cache.MemoryCache import MemoryCache


if plugin.HAS_PRIVEX_DB in [True, None]:
    try:
        from privex.helpers.cache.SqliteCache import SqliteCache
        plugin.HAS_PRIVEX_DB = True
    except ImportError:
        plugin.HAS_PRIVEX_DB = False
        log.debug(
            "[%s] Failed to import %s from %s (missing package 'privex-db' maybe?)", __name__, 'SqliteCache', f'{__name__}.SqliteCache'
        )
else:
    log.debug("[%s] Not attempting to import %s from %s as plugin check var '%s' is False.",
              __name__, 'SqliteCache', f'{__name__}.SqliteCache', 'HAS_PRIVEX_DB')

try:
    from privex.helpers.cache.RedisCache import RedisCache
except ImportError:
    log.debug("[%s] Failed to import %s from %s (missing package 'redis' maybe?)", __name__, 'RedisCache', f'{__name__}.RedisCache')

try:
    from privex.helpers.cache.MemcachedCache import MemcachedCache
except ImportError:
    log.debug("[%s] Failed to import %s from %s (missing package 'pylibmc' maybe?)", __name__, 'MemcachedCache',
              f'{__name__}.MemcachedCache')

try:
    from privex.helpers.cache.asyncx import *
except ImportError:
    log.exception("[%s] Failed to import %s from %s (unknown error!)", __name__, '*', f'{__name__}.asyncx')

from privex.helpers.exceptions import NotConfigured, CacheNotFound
from privex.helpers.settings import DEFAULT_CACHE_TIMEOUT


__STORE = {}

__STORE['adapter']: CacheAdapter
__STORE['async_adapter']: AsyncCacheAdapter


CLSCacheAdapter = Union[Type[CacheAdapter], Type[AsyncCacheAdapter]]
INSCacheAdapter = Union[CacheAdapter, AsyncCacheAdapter]
ANYCacheAdapter = Union[CLSCacheAdapter, INSCacheAdapter, str]

ADAPTER_MAP = DictObject(
    sync=DictObject(
        memory='privex.helpers.cache.MemoryCache.MemoryCache',
        redis='privex.helpers.cache.RedisCache.RedisCache',
        memcached='privex.helpers.cache.MemcachedCache.MemcachedCache',
        sqlite3='privex.helpers.cache.SqliteCache.SqliteCache',
    ),
    asyncio=DictObject(
        memory='privex.helpers.cache.asyncx.AsyncMemoryCache.AsyncMemoryCache',
        redis='privex.helpers.cache.asyncx.AsyncRedisCache.AsyncRedisCache',
        memcached='privex.helpers.cache.asyncx.AsyncMemcachedCache.AsyncMemcachedCache',
        sqlite3='privex.helpers.cache.asyncx.AsyncSqliteCache.AsyncSqliteCache',
    ),
    
)

_AM = ADAPTER_MAP

_AM.sync.ram, _AM.asyncio.ram = _AM.sync.mem, _AM.asyncio.mem = _AM.sync.memory, _AM.asyncio.memory
_AM.sync.mcache, _AM.asyncio.mcache = _AM.sync.memcache, _AM.asyncio.memcache = _AM.sync.memcached, _AM.asyncio.memcached
_AM.sync.sqlitedb, _AM.asyncio.sqlitedb = _AM.sync.sqlite, _AM.asyncio.sqlite = _AM.sync.sqlite3, _AM.asyncio.sqlite3

_AM.shared = DictObject(
    # Synchronous cache adapters
    MemoryCache=_AM.sync.memory, RedisCache=_AM.sync.redis, MemcachedCache=_AM.sync.memcached,
    SqliteCache=_AM.sync.sqlite3,
    # Synchronous cache adapters (xxxAdapter aliases)
    MemoryAdapter=_AM.sync.memory, RedisAdapter=_AM.sync.redis, MemcachedAdapter=_AM.sync.memcached,
    SqliteAdapter=_AM.sync.sqlite3,
    # AsyncIO cache adapters
    AsyncMemoryCache=_AM.asyncio.memory, AsyncRedisCache=_AM.asyncio.redis, AsyncMemcachedCache=_AM.asyncio.memcached,
    AsyncSqliteCache=_AM.asyncio.sqlite3,
    # AsyncIO cache adapters (xxxAdapter aliases)
    AsyncMemoryAdapter=_AM.asyncio.memory, AsyncRedisAdapter=_AM.asyncio.redis, AsyncMemcachedAdapter=_AM.asyncio.memcached,
    AsyncSqliteAdapter=_AM.asyncio.sqlite3
)


def import_adapter_path(full_path: str) -> Type[Union[CacheAdapter, AsyncCacheAdapter]]:
    """
    This function imports a fully qualified module path, with a class/function/attribute name as the final component
    of the dot delimitered string.
    
    Example::
    
        >>> # Equivalent to: from privex.helpers.cache.MemcachedCache import MemcachedCache as _MemcachedCache
        >>> _MemcachedCache = import_adapter_path('privex.helpers.cache.MemcachedCache.MemcachedCache')
        
    :param str full_path: A fully qualified module path, with a class/function/attribute name as the final component
                          of the dot delimitered string.
    :return type obj:     The class/function/variable that was imported from the module in ``full_path``
    """
    
    split_mod = full_path.split('.')
    path_mod, path_class = '.'.join(split_mod[:-1]), split_mod[-1]
    mod = importlib.import_module(path_mod)
    return getattr(mod, path_class)


def import_adapter(name: str, cat: str = 'sync', fallback_shared=True) -> Type[Union[CacheAdapter, AsyncCacheAdapter]]:
    """
    Import a cache adapter class using either it's class name, or config/human-friendly alias name.
    
    By default, ``fallback_shared`` is enabled, which allows importing adapter names that are in the ``shared`` category, such as
    ``AsyncRedisCache`` / ``MemcachedCache`` while ``cat`` is set to ``asyncio`` / ``sync``
    
    Adapter Categories::
    
      * ``shared`` - Contains full cache adapter class names, e.g. ``RedisCache``, ``AsyncMemcachedCache`` etc.
      * ``sync`` (default) - Contains synchronous cache adapters with simple alias names, e.g. ``redis``, ``memory``, ``memcached``
      * ``asyncio`` / ``async`` - Contains AsyncIO cache adapters with simple alias names, e.g. ``redis``, ``memory``, ``memcached``
    
    Examples::
        
        >>> _MemcachedCache = import_adapter('memcached')
        >>> _AsyncRedisCache = import_adapter('redis', 'asyncio')
        >>> _SqliteCache = import_adapter('SqliteCache')
        
        >>> mc = _MemcachedCache()
        >>> mc.set('hello', 'world')
        >>> mc['hello']
        'world'
    
    :param str name: The dictionary key / name for the adapter, e.g. ``memcached`` / ``sqlite3``, or full adapter class name
                      such as ``AsyncMemoryCache`` if ``cat`` is ``'shared'``
    
    :param str cat: (default: ``'sync'``) One of: ``'sync'``, ``'asyncio'``, ``'async'``, or ``'shared'``
    
    :param bool fallback_shared: (default: ``True``) When set to ``True``, if ``name`` can't be found in the current ``cat`` category,
                                 check if it exists in the ``shared`` category - if it does, then retrieve the module path from that.
    
    :raises KeyError: When the adapter name ``name`` isn't found in the category (nor in ``shared`` if ``fallback_shared`` is enabled)
    :raises AttributeError: When the category ``cat`` isn't found in :attr:`.ADAPTER_MAP`
    
    :return Type[Union[CacheAdapter, AsyncCacheAdapter]] adp_class: The uninstantiated class for the cache adapter that was imported.
    """
    cat = 'asyncio' if cat == 'async' else cat.lower()
    dkeys = list(_AM.keys())
    if cat not in dkeys:
        raise AttributeError(f"Invalid category. You must specify one of the following categories (aka 'cat'): {dkeys}")
    modx: dict = _AM[cat]
    try:
        mpath = modx[name if name in modx else name.lower()]
    except (KeyError, IndexError) as e:
        if fallback_shared and (name.endswith('Cache') or name.endswith('Adapter')) and name in _AM['shared']:
            log.info(f"Adapter name '{name}' wasn't found in category '{cat}' - but WAS found in the shared category, and "
                     f"fallback_shared is enabled. Falling back to: _AM['shared']['{name}']")
            mpath = _AM['shared'][name]
        else:
            raise KeyError(f"Adapter name '{name}' not found in category '{cat}'. Available adapters in '{cat}': {modx.keys()}")
    return import_adapter_path(mpath)
    

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
    cache_instance: Optional[INSCacheAdapter] = None
    """Holds the singleton instance of a :class:`.CacheAdapter` implementation"""
    
    default_adapter: Union[Type[CLSCacheAdapter], str] = settings.DEFAULT_CACHE_ADAPTER
    """The default adapter class to instantiate if :py:attr:`.cache_instance` is ``None``"""

    instance_args = []
    instance_kwargs = {}
    is_adapter_async: bool = False
    
    max_context_layers: int = 1
    _ctx_tracker: Optional[LayeredContext] = None
    
    @classmethod
    def get_context_tracker(cls, reset: bool = False) -> LayeredContext:
        return cls.reset_context_tracker() if reset or not cls._ctx_tracker else cls._ctx_tracker
    
    @classmethod
    def reset_context_tracker(cls) -> LayeredContext:
        cls._ctx_tracker = LayeredContext(cls.cache_instance, max_layers=cls.max_context_layers)
        return cls._ctx_tracker

    @classmethod
    def get_adapter(cls, default: CLSCacheAdapter = default_adapter, *args, **kwargs) -> INSCacheAdapter:
        """
        Attempt to get the singleton cache adapter from :py:attr:`.cache_instance` - if the instance is ``None``, then
        attempt to instantiate ``default()``

        If any ``*args`` or ``**kwargs`` are passed, they will be passed through to ``default(*args, **kwargs)`` so
        that any necessary configuration parameters can be passed to the class.
        """
        if not cls.cache_instance:
            cls.instance_args, cls.instance_kwargs = list(args), dict(kwargs)
            if isinstance(default, str): default = import_adapter(default, 'asyncio' if cls.is_adapter_async else 'sync')
            cls.set_adapter(default(*args, **kwargs))
        return cls.cache_instance

    @classmethod
    def set_adapter(cls, adapter: ANYCacheAdapter, *args, **kwargs) -> INSCacheAdapter:
        cls.instance_args, cls.instance_kwargs = list(args), dict(kwargs)
        cls.cache_instance = None
        if isinstance(adapter, str): adapter = import_adapter(adapter, 'asyncio' if cls.is_adapter_async else 'sync')

        cls.cache_instance = cls.get_adapter(adapter, *args, **kwargs) if isclass(adapter) else adapter
        cls.reset_context_tracker()
        return cls.cache_instance

    @classmethod
    def reset_adapter(cls, default: CLSCacheAdapter = default_adapter, *args, **kwargs) -> INSCacheAdapter:
        """
        Re-create the adapter instance at :attr:`.cache_instance` with the same adapter class (assuming it's set)
        """
        adp = cls.get_adapter(default, *args, **kwargs)
        n_args, n_kwargs = empty_if(args, cls.instance_args, itr=True), {**cls.instance_kwargs, **kwargs}
        c = adp.__class__
        cls.cache_instance = c.__init__(c(), *n_args, **n_kwargs)
        return cls.cache_instance

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

    async def __aenter__(self):
        """Pass-through to :meth:`.cache_instance.__aenter__` instance AsyncIO context enter method"""
        self.get_adapter()  # Make sure cache_instance exists by calling get_adapter (which will set the default if it doesn't)
        return await self.get_context_tracker().aenter()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Pass-through to :meth:`.cache_instance.__aexit__` instance AsyncIO context exit method"""
        return await self.get_context_tracker().aexit(exc_type, exc_val, exc_tb)

    def __enter__(self):
        """Pass-through to :meth:`.cache_instance.__enter__` instance context enter method"""
        self.get_adapter()  # Make sure cache_instance exists by calling get_adapter (which will set the default if it doesn't)
        return self.get_context_tracker().enter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Pass-through to :meth:`.cache_instance.__exit__` instance context exit method"""
        return self.get_context_tracker().exit(exc_type, exc_val, exc_tb)


cached: Union[CacheAdapter, CacheWrapper] = CacheWrapper()
"""
This module attribute acts as a singleton, containing an instance of :class:`.CacheWrapper` which is designed
to allow painless usage of this caching module.
"""


class AsyncCacheWrapper(CacheWrapper):
    """
    For applications/packages which are primarily AsyncIO, :class:`.CacheWrapper` can cause problems such as the
    common ``event loop is already running`` - and unfortunately, :mod:`nest_asyncio` isn't always able to fix it.
    
    This wrapper - :class:`.AsyncCacheWrapper` is ONLY compatible with AsyncIO code, and holds a different
    adapter instance in :attr:`.cache_instance` than :class:`.CacheWrapper`, as it expects the adapter instance to
    always be based on :class:`.AsyncCacheAdapter` - along with the fact it generally returns coroutines.
    
        >>> from privex.helpers.cache import async_cached, async_adapter_set, AsyncRedisCache
        >>> async_adapter_set(AsyncRedisCache())
        >>> c = async_cached      # We alias async_cached to 'c' for convenience.
        >>> c['hello'] = 'world'  # We can set cache keys as if the wrapper was a dictionary
        >>> c['hello']            # Similarly we can also get keys like normal
        'world'
        >>> await c['hello']      # It's safest to use ``await`` when getting keys within an async context
        'world'
        >>> await c.get('hello')  # We can also use the coroutines .get, .set, .get_or_set etc.
        'world'
    
    
    """
    cache_instance: AsyncCacheAdapter = None
    """Holds the singleton instance of a :class:`.AsyncCacheAdapter` implementation"""
    
    instance_args = []
    instance_kwargs = {}
    is_adapter_async: bool = True
    
    default_adapter: Union[Type[AsyncCacheAdapter], str] = settings.DEFAULT_ASYNC_CACHE_ADAPTER
    """The default adapter class to instantiate if :py:attr:`.cache_instance` is ``None``"""

    max_context_layers: int = 1
    _ctx_tracker: Optional[LayeredContext] = None
    
    @classmethod
    def get_adapter(cls, default: Union[Type[AsyncCacheAdapter], str] = default_adapter, *args, **kwargs) -> AsyncCacheAdapter:
        
        # if not cls.cache_instance:
        #     cls.instance_args, cls.instance_kwargs = list(args), dict(kwargs)
        #     cls.cache_instance = default(*args, **kwargs)
        return super(AsyncCacheWrapper, cls).get_adapter(default, *args, **kwargs)

    @classmethod
    def set_adapter(cls, adapter: Union[AsyncCacheAdapter, str], *args, **kwargs) -> AsyncCacheAdapter:
        return super(AsyncCacheWrapper, cls).set_adapter(adapter, *args, **kwargs)
        # cls.cache_instance = adapter
        # return cls.cache_instance
    
    @classmethod
    def reset_adapter(cls, default: Type[AsyncCacheAdapter] = default_adapter, *args, **kwargs) -> AsyncCacheAdapter:
        """
        Re-create the adapter instance at :attr:`.cache_instance` with the same adapter class (assuming it's set)
        """
        # adp = cls.get_adapter(default, *args, **kwargs)
        # n_args, n_kwargs = empty_if(args, cls.instance_args, itr=True), {**cls.instance_kwargs, **kwargs}
        # c = adp.__class__
        # cls.cache_instance = c.__init__(c(), *n_args, **n_kwargs)
        return super(AsyncCacheWrapper, cls).reset_adapter(default, *args, **kwargs)
    
    def __getattr__(self, item):
        if hasattr(super(), item):
            return getattr(self, item)
        
        async def _wrapper(*args, **kwargs):
            async with AsyncCacheWrapper.get_adapter() as a:
                return await await_if_needed(getattr(a, item)(*args, **kwargs))
        
        return _wrapper

    @awaitable
    def __getitem__(self, item):
        async def _wrapper():
            try:
                async with AsyncCacheWrapper.get_adapter() as a:
                    return await await_if_needed(a.get(key=item, fail=True))
            except CacheNotFound:
                raise KeyError(f'Key "{item}" not found in cache.')
        return _wrapper()

    def __setitem__(self, key, value):
        async def _wrapper():
            async with AsyncCacheWrapper.get_adapter() as a:
                return await await_if_needed(a.set(key=key, value=value))
        return loop_run(_wrapper())
    
    # async def __aenter__(self):
    #     """Pass-through to :meth:`.cache_instance.__aenter__` instance AsyncIO context enter method"""
    #     return await self.get_adapter().__aenter__()
    #
    # async def __aexit__(self, exc_type, exc_val, exc_tb):
    #     """Pass-through to :meth:`.cache_instance.__aexit__` instance AsyncIO context exit method"""
    #     return await self.get_adapter().__aexit__(exc_type, exc_val, exc_tb)
    def __enter__(self):
        self.get_adapter()  # Make sure cache_instance exists by calling get_adapter (which will set the default if it doesn't)
        # Because this is an AsyncIO-only cache adapter, generally __enter__ isn't used, instead the AsyncIO `__aenter__` and
        # `__aexit__` are used. So, we can try to convert any attempts to use the classic `with x as y` into `async with x as y`
        # by grabbing the event loop and trying to run `__aenter__` in the AsyncIO event loop.
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.get_context_tracker().aenter())

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Because this is an AsyncIO-only cache adapter, generally __exit__ isn't used, instead the AsyncIO `__aenter__` and
        # `__aexit__` are used. So, we can try to convert any attempts to use the classic `with x as y` into `async with x as y`
        # by grabbing the event loop and trying to run `__aexit__` in the AsyncIO event loop.
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.get_context_tracker().aexit(exc_type, exc_val, exc_tb))


async_cached: Union[AsyncCacheAdapter, AsyncCacheWrapper] = AsyncCacheWrapper()


def async_adapter_set(adapter: Union[AsyncCacheAdapter, str]) -> AsyncCacheAdapter:
    """
    Same as :func:`.adapter_set` but sets ``__STORE['async_adapter']`` instead of ``'adapter'``,
    and sets the adapter for async-only :attr:`.async_cached` ( :class:`.AsyncCacheWrapper` ) instead of
    the dual-sync :attr:`.cached` ( :class:`.CacheWrapper` )
    
    Example::
    
        >>> from privex.helpers.cache import AsyncRedisCache, async_adapter_set
        >>> # Passing an instantiated adapter class
        >>> async_adapter_set(AsyncRedisCache())
        >>> # Passing a simple string adapter name to be imported and instantiated
        >>> async_adapter_set('memcached')          # You can either pass a simple "alias" name
        >>> async_adapter_set('AsyncSqliteCache')   # Or you can pass a full adapter class name
    
    """
    if isinstance(adapter, str):
        c_adapter = import_adapter(adapter, 'asyncio')
        adapter = c_adapter()
    __STORE['async_adapter'] = adapter
    async_cached.set_adapter(adapter)
    return __STORE['async_adapter']


def async_adapter_get(default: Union[Type[AsyncCacheAdapter], str] = settings.DEFAULT_ASYNC_CACHE_ADAPTER) -> AsyncCacheAdapter:
    """Same as :func:`.adapter_get` but gets ``__STORE['async_adapter']`` instead of ``'adapter'``"""
    if 'async_adapter' not in __STORE or __STORE['async_adapter'] is None:
        if not default:
            raise NotConfigured('No async cache adapter has been configured for privex.helpers.cache!')
        if isinstance(default, str):
            default = import_adapter(default, 'asyncio')
        async_adapter_set(default())
    return __STORE['async_adapter']


def adapter_set(adapter: Union[CacheAdapter, str]) -> CacheAdapter:
    """
    Set the global cache adapter instance to ``adapter`` - which should be an instantiated adapter class which
    implements :class:`.CacheAdapter`
    
    **Example**::
    
        >>> from privex.helpers import cache
        >>> cache.adapter_set(cache.MemoryCache())   # Passing an instantiated adapter class
        >>> cache.adapter_set('redis')               # Alternatively, you can pass a string alias name of an adapter
        >>> cache.adapter_set('SqliteCache')         # Or the full class name of an adapter
    
    :param CacheAdapter adapter: An instance of a class which implements :class:`.CacheAdapter` for global use.
    :return CacheAdapter adapter: A reference to your adapter from ``__STORE['adapter']``
    """
    if isinstance(adapter, str):
        c_adapter = import_adapter(adapter, 'sync')
        adapter = c_adapter()
    __STORE['adapter'] = adapter
    cached.set_adapter(adapter)
    
    return __STORE['adapter']


def adapter_get(default: Union[Type[CacheAdapter], str] = settings.DEFAULT_CACHE_ADAPTER) -> CacheAdapter:
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
        if isinstance(default, str):
            default = import_adapter(default, 'sync')
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

