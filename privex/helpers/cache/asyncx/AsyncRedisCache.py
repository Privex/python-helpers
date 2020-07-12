import asyncio
import pickle
from typing import Any, Union, Optional

from aioredis.commands import ContextRedis
from async_property import async_property

from privex.helpers.common import empty

# from privex.helpers import plugin
# from privex.helpers.cache.CacheAdapter import CacheAdapter
from privex.helpers.exceptions import CacheNotFound
from privex.helpers.settings import DEFAULT_CACHE_TIMEOUT
from privex.helpers.types import VAL_FUNC_CORO

# if plugin.HAS_ASYNC_REDIS:
from privex.helpers.plugin import get_redis_async, close_redis_async
from privex.helpers.cache.asyncx.base import AsyncCacheAdapter
import aioredis
import logging

log = logging.getLogger(__name__)


class AsyncRedisCache(AsyncCacheAdapter):
    """
    A Redis backed implementation of :class:`.AsyncCacheAdapter`. Uses the global Redis instance from
    :py:mod:`privex.helpers.plugin` by default, however custom Redis instances can be passed in via
    the constructor argument ``redis_instance``.

    To allow for a wide variety of Python objects to be safely stored and retrieved from Redis, this class
    uses the :py:mod:`pickle` module for serialising + un-serialising values to/from Redis.

    **Basic Usage**::

        >>> from privex.helpers import AsyncRedisCache
        >>> rc = AsyncRedisCache()
        >>> await rc.set('hello', 'world')
        >>> rc['hello']
        'world'


    **Disabling Pickling**

    In some cases, you may need interoperable caching with other languages. The :py:mod:`pickle` serialisation
    technique is extremely specific to Python and is largely unsupported outside of Python. Thus if you need
    to share Redis cache data with applications in other languages, then you must disable pickling.

    **WARNING:** If you disable pickling, then you must perform your own serialisation + de-serialization on
    complex objects such as ``dict``, ``list``, ``Decimal``, or arbitrary classes/functions after getting
    or setting cache keys.

    **Disabling Pickle per instance**

    Pass ``use_pickle=False`` to the constructor, or access the attribute directly to disable pickling for a
    single instance of RedisCache (not globally)::

        >>> rc = AsyncRedisCache(use_pickle=False)  # Opt 1. Disable pickle in constructor
        >>> rc.use_pickle = False                   # Opt 2. Disable pickle on an existing instance


    **Disabling Pickle by default on any new instances**

    Change the static attribute :py:attr:`.pickle_default` to ``False`` to disable the use of pickle by default
    across any new instances of RedisCache::

        >>> AsyncRedisCache.pickle_default = False

    """
    
    pickle_default: bool = True
    """
    Change this to ``False`` to disable the use of :py:mod:`pickle` by default for any new instances
    of this class.
    """
    
    use_pickle: bool
    """If ``True``, will use :py:mod:`pickle` for serializing objects before inserting into Redis, and
    un-serialising objects retrieved from Redis. This attribute is set in :py:meth:`.__init__`.

    Change this to ``False`` to disable the use of :py:mod:`pickle` - instead values will be passed to / returned
    from Redis as-is, with no serialisation (this may require you to manually serialize complex types such
    as ``dict`` and ``Decimal`` before insertion, and un-serialise after retrieval).
    """
    adapter_enter_reconnect: bool = True
    adapter_exit_close: bool = True
    
    _redis_conn: Optional[Union[aioredis.Redis, aioredis.ConnectionsPool]]
    _redis: Optional[ContextRedis]
    
    def __init__(self, use_pickle: bool = None, redis_instance: aioredis.Redis = None, *args, **kwargs):
        """
        RedisCache by default uses the global Redis instance from :py:mod:`privex.helpers.plugin`.

        It's recommended to use :py:func:`privex.helpers.plugin.configure_redis` if you need to change any
        Redis settings, as this will adjust the global settings and re-instantiate the global instance if required.

        Alternatively, you may pass an instance of :class:`redis.Redis` as ``redis_instance``, then that will
        be used instead of the global instance from :py:func:`.get_redis`

        :param bool use_pickle: (Default: ``True``) Use the built-in ``pickle`` to serialise values before
                                storing in Redis, and un-serialise when loading from Redis

        :param redis.Redis redis_instance: If this isn't ``None`` / ``False``, then this Redis instance will be
                                           used instead of the global one from :py:func:`.get_redis`
        
        :keyword bool enter_reconnect: Pass ``enter_reconnect=False`` to disable calling :meth:`.reconnect` when entering this cache
                                       adapter as a context manager (:meth:`.__aenter__`)
        :keyword bool exit_close: Pass ``exit_close=False`` to disable calling :meth:`.close` when exiting this cache
                                  adapter as a context manager (:meth:`.__aexit__`)
        """
        super().__init__(*args, **kwargs)
        self._redis = None if not redis_instance else redis_instance
        self._redis_conn = None
        self.use_pickle = self.pickle_default if use_pickle is None else use_pickle
    
    @async_property
    async def redis(self) -> aioredis.Redis:
        # if self._redis_conn is None:
        #     self._redis_conn = await get_redis_async()
        # if self._redis is not None:
        #     return self._redis
        # return self._redis
        # if self._redis is None:
        #     self._redis = await self.connect()
        return await self.connect()

    async def get(self, key: str, default: Any = None, fail: bool = False) -> Any:
        key = str(key)
        r = await self.redis
        res = await r.get(key)
        if empty(res):
            if fail: raise CacheNotFound(f'Cache key "{key}" was not found.')
            return default
        return pickle.loads(res) if self.use_pickle else res
    
    async def set(self, key: str, value: Any, timeout: Optional[int] = DEFAULT_CACHE_TIMEOUT):
        r: aioredis.Redis = await self.redis
        v = pickle.dumps(value) if self.use_pickle else value
        return await r.set(str(key), v, expire=timeout)

    # async def get_or_set(self, key: str, value: VAL_FUNC_CORO, timeout: int = DEFAULT_CACHE_TIMEOUT) -> Any:
    #     return await self.get_or_set_async(key=key, value=value, timeout=timeout)
    
    async def remove(self, *key: str) -> bool:
        removed = 0
        for k in key:
            k = str(k)
            try:
                await self.get(k, fail=True)
                r: aioredis.Redis = await self.redis
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
    
    async def connect(self, *args, **kwargs) -> ContextRedis:
        if not self._redis_conn:
            self._redis_conn = await get_redis_async()
        if not self._redis:
            self._redis = await self._redis_conn
        return self._redis
    
    async def close(self):
        if self._redis is not None:
            log.debug("Closing AsyncIO Redis instance %s._redis", self.__class__.__name__)
            self._redis.close()
            self._redis = None
        # Closing the Redis connection directly from this method usually leads to problems...
        # It's safest to just set it to None and then call close_redis_async()
        if self._redis_conn is not None:
            log.debug("Clearing AsyncIO Redis connection pool %s._redis_conn", self.__class__.__name__)
            self._redis_conn = None
        await close_redis_async()

