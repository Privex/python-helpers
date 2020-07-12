import asyncio
import pickle
from typing import Any, Union, Optional
from async_property import async_property
from privex.helpers.common import empty, byteify
from privex.helpers.exceptions import CacheNotFound
from privex.helpers.settings import DEFAULT_CACHE_TIMEOUT
from privex.helpers.plugin import get_memcached_async, close_memcached_async
from privex.helpers.cache.asyncx.base import AsyncCacheAdapter
import aiomcache
import logging

log = logging.getLogger(__name__)


class AsyncMemcachedCache(AsyncCacheAdapter):
    """
    A Memcached backed implementation of :class:`.AsyncCacheAdapter`. Uses the global Memcached instance from
    :py:mod:`privex.helpers.plugin` by default, however custom Memcached instances can be passed in via
    the constructor argument ``mcache_instance``.

    To allow for a wide variety of Python objects to be safely stored and retrieved from Memcached, this class
    uses the :py:mod:`pickle` module for serialising + un-serialising values to/from Memcached.

    **Basic Usage**::

        >>> from privex.helpers import AsyncMemcachedCache
        >>> rc = AsyncMemcachedCache()
        >>> await rc.set('hello', 'world')
        >>> rc['hello']
        'world'


    **Disabling Pickling**

    In some cases, you may need interoperable caching with other languages. The :py:mod:`pickle` serialisation
    technique is extremely specific to Python and is largely unsupported outside of Python. Thus if you need
    to share Memcached cache data with applications in other languages, then you must disable pickling.

    **WARNING:** If you disable pickling, then you must perform your own serialisation + de-serialization on
    complex objects such as ``dict``, ``list``, ``Decimal``, or arbitrary classes/functions after getting
    or setting cache keys.

    **Disabling Pickle per instance**

    Pass ``use_pickle=False`` to the constructor, or access the attribute directly to disable pickling for a
    single instance of MemcachedCache (not globally)::

        >>> rc = AsyncMemcachedCache(use_pickle=False)  # Opt 1. Disable pickle in constructor
        >>> rc.use_pickle = False                       # Opt 2. Disable pickle on an existing instance


    **Disabling Pickle by default on any new instances**

    Change the static attribute :py:attr:`.pickle_default` to ``False`` to disable the use of pickle by default
    across any new instances of AsyncMemcachedCache::

        >>> AsyncMemcachedCache.pickle_default = False



    """
    
    pickle_default: bool = True
    """
    Change this to ``False`` to disable the use of :py:mod:`pickle` by default for any new instances
    of this class.
    """
    
    use_pickle: bool
    """If ``True``, will use :py:mod:`pickle` for serializing objects before inserting into Memcached, and
    un-serialising objects retrieved from Memcached. This attribute is set in :py:meth:`.__init__`.

    Change this to ``False`` to disable the use of :py:mod:`pickle` - instead values will be passed to / returned
    from Memcached as-is, with no serialisation (this may require you to manually serialize complex types such
    as ``dict`` and ``Decimal`` before insertion, and un-serialise after retrieval).
    """

    adapter_enter_reconnect: bool = True
    adapter_exit_close: bool = True

    _mcache: Optional[aiomcache.Client]
    
    def __init__(self, use_pickle: bool = None, mcache_instance: aiomcache.Client = None, *args, **kwargs):
        """
        AsyncMemcachedCache by default uses the global Memcached instance from :py:mod:`privex.helpers.plugin`.

        It's recommended to use :py:func:`privex.helpers.plugin.configure_memcached_async` if you need to change any
        Memcached settings, as this will adjust the global settings and re-instantiate the global instance if required.

        Alternatively, you may pass an instance of :class:`aiomcache.Client` as ``mcache_instance``, then that will
        be used instead of the global instance from :py:func:`.get_memcached_async`

        :param bool use_pickle: (Default: ``True``) Use the built-in ``pickle`` to serialise values before
                                storing in Memcached, and un-serialise when loading from Memcached

        :param aiomcache.Client mcache_instance: If this isn't ``None`` / ``False``, then this Memcached instance will be
                                                 used instead of the global one from :py:func:`.get_memcached_async`
        
        :keyword bool enter_reconnect: Pass ``enter_reconnect=False`` to disable calling :meth:`.reconnect` when entering this cache
                                       adapter as a context manager (:meth:`.__aenter__`)
        :keyword bool exit_close: Pass ``exit_close=False`` to disable calling :meth:`.close` when exiting this cache
                                  adapter as a context manager (:meth:`.__aexit__`)
        """
        super().__init__(*args, **kwargs)
        self._mcache = None if not mcache_instance else mcache_instance
        self.use_pickle = self.pickle_default if use_pickle is None else use_pickle
    
    @async_property
    async def mcache(self) -> aiomcache.Client:
        # We can't recycle connections with aiomcache, so we need to make sure to get a new connection for every instance.
        # if self._mcache is None:
        #     self._mcache = await get_memcached_async(new_connection=True)
        return await self.connect()
    
    async def get(self, key: Union[bytes, str], default: Any = None, fail: bool = False) -> Any:
        key = byteify(key)
        r = await self.mcache
        res = await r.get(key)
        if empty(res):
            if fail: raise CacheNotFound(f'Cache key "{key}" was not found.')
            return default
        return pickle.loads(res) if self.use_pickle else res
    
    async def set(self, key: Union[bytes, str], value: Any, timeout: Optional[int] = DEFAULT_CACHE_TIMEOUT):
        r: aiomcache.Client = await self.mcache
        v = pickle.dumps(value) if self.use_pickle else value
        return await r.set(byteify(key), v, exptime=timeout)
    
    async def remove(self, *key: Union[bytes, str]) -> bool:
        removed = 0
        for k in key:
            k = byteify(k)
            try:
                await self.get(k, fail=True)
                r = await self.mcache
                await r.delete(k)
                removed += 1
            except CacheNotFound:
                pass
        
        return removed == len(key)
    
    async def update_timeout(self, key: str, timeout: int = DEFAULT_CACHE_TIMEOUT) -> Any:
        key, timeout = str(key), int(timeout)
        v = await self.get(key=key, fail=True)
        await self.set(key=key, value=v, timeout=timeout)
        return v

    async def connect(self, *args, new_connection=True, **kwargs) -> aiomcache.Client:
        # We can't recycle connections with aiomcache, so we need to make sure to get a new connection for every instance.
        if not self._mcache:
            self._mcache = await get_memcached_async(*args, new_connection=new_connection, **kwargs)
        return self._mcache

    async def close(self):
        if self._mcache is not None:
            log.debug("Closing AsyncIO Memcached instance %s._mcache", self.__class__.__name__)
            await self._mcache.close()
        self._mcache = None
        return await close_memcached_async()

