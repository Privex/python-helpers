import pickle
from typing import Any, Union, Optional
from privex.helpers.common import empty

from privex.helpers import plugin
from privex.helpers.cache.CacheAdapter import CacheAdapter
from privex.helpers.exceptions import CacheNotFound
from privex.helpers.settings import DEFAULT_CACHE_TIMEOUT
import logging

log = logging.getLogger(__name__)


if plugin.HAS_REDIS:
    from privex.helpers.plugin import get_redis, close_redis
    from redis import Redis
    import redis
    
    class RedisCache(CacheAdapter):
        """
        A Redis backed implementation of :class:`.CacheAdapter`. Uses the global Redis instance from
        :py:mod:`privex.helpers.plugin` by default, however custom Redis instances can be passed in via
        the constructor argument ``redis_instance``.
        
        To allow for a wide variety of Python objects to be safely stored and retrieved from Redis, this class
        uses the :py:mod:`pickle` module for serialising + un-serialising values to/from Redis.
        
        **Basic Usage**::
        
            >>> from privex.helpers import RedisCache
            >>> rc = RedisCache()
            >>> rc.set('hello', 'world')
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
        
            >>> rc = RedisCache(use_pickle=False)  # Opt 1. Disable pickle in constructor
            >>> rc.use_pickle = False              # Opt 2. Disable pickle on an existing instance
        
        
        **Disabling Pickle by default on any new instances**
        
        Change the static attribute :py:attr:`.pickle_default` to ``False`` to disable the use of pickle by default
        across any new instances of RedisCache::
        
            >>> RedisCache.pickle_default = False
        
        
        
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
        
        _redis: Optional[Redis]
        
        def __init__(self, use_pickle: bool = None, redis_instance: Redis = None, *args, **kwargs):
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
            
            """
            super().__init__(*args, **kwargs)
            self._redis = get_redis() if not redis_instance else redis_instance
            self.use_pickle = self.pickle_default if use_pickle is None else use_pickle
        
        @property
        def redis(self) -> Redis:
            return self.connect()
        
        def get(self, key: str, default: Any = None, fail: bool = False) -> Any:
            key = str(key)
            res = self.redis.get(key)
            if empty(res):
                if fail: raise CacheNotFound(f'Cache key "{key}" was not found.')
                return default
            return pickle.loads(res) if self.use_pickle else res

        def set(self, key: str, value: Any, timeout: Optional[int] = DEFAULT_CACHE_TIMEOUT):
            v = pickle.dumps(value) if self.use_pickle else value
            return self.redis.set(str(key), v, ex=timeout)

        def remove(self, *key: str) -> bool:
            removed = 0
            for k in key:
                k = str(k)
                try:
                    self.get(k, fail=True)
                    self.redis.delete(k)
                    removed += 1
                except CacheNotFound:
                    pass

            return removed == len(key)

        def update_timeout(self, key: str, timeout: int = DEFAULT_CACHE_TIMEOUT) -> Any:
            key, timeout = str(key), int(timeout)
            v = self.get(key=key, fail=True)
            self.set(key=key, value=v, timeout=timeout)
            return v

        def connect(self, *args, **kwargs) -> Redis:
            if not self._redis:
                self._redis = get_redis()
            return self._redis

        def close(self):
            if self._redis is not None:
                log.debug("Closing Synchronous Redis instance %s._redis", self.__class__.__name__)
                self._redis.close()
                self._redis = None
            return close_redis()
        
        # def __enter__(self):
        #     if not self.redis:
        #         self._redis = get_redis()
        #     return self
        #
        # def __exit__(self, exc_type, exc_val, exc_tb):
        #     close_redis()
        #     self._redis = None
        #     return None
