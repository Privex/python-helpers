import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Union

from privex.helpers.exceptions import CacheNotFound
from privex.helpers.settings import DEFAULT_CACHE_TIMEOUT
from privex.helpers.cache.CacheAdapter import CacheAdapter

log = logging.getLogger(__name__)


class MemoryCache(CacheAdapter):
    """
    A very basic cache adapter which implements :class:`.CacheAdapter` - stores the cache in memory using
    the static attribute :py:attr:`.__CACHE`
    
    As the cache is simply stored in memory, any python object can be cached without needing any form of serialization.
    
    Fully supports cache expiration.
    
    **Basic Usage**::
        
        >>> from time import sleep
        >>> c = MemoryCache()
        >>> c.set('test:example', 'hello world', timeout=60)
        >>> c.get('test:example')
        'hello world'
        >>> sleep(60)
        >>> c.get('test:example', 'NOT FOUND')
        'NOT FOUND'
    
    """
    __CACHE = {}
    
    def get(self, key: str, default: Any = None, fail: bool = False) -> Any:
        key = str(key)
        c = self.__CACHE
        if key in c:
            log.debug('Cache key "%s" found in __CACHE. Checking expiry...', key)
            vc = c[key]
            if str(vc['timeout']) != 'never' and vc['timeout'] < datetime.utcnow():
                log.debug('Cache key "%s" has expired. Removing from cache.')
                del c[key]
                if fail:
                    raise CacheNotFound(f'Cache key "{key}" was expired.')
                return default
            log.debug('Cache key "%s" is valid and not expired. Returning value "%s"', key, vc)
            return vc['value']
        if fail:
            raise CacheNotFound(f'Cache key "{key}" was not found.')
        log.debug('Cache key "%s" was not found in __CACHE. Returning default value.', key)
        return default

    def set(self, key: str, value: Any, timeout: Optional[int] = DEFAULT_CACHE_TIMEOUT):
        key, timeout = str(key), int(timeout)
        c = self.__CACHE
        log.debug('Setting cache key "%s" to value "%s" with timeout %s', key, value, timeout)
        c[key] = dict(value=value, timeout=datetime.utcnow() + timedelta(seconds=timeout))
        return c[key]

    def get_or_set(self, key: str, value: Union[Any, callable], timeout: int = DEFAULT_CACHE_TIMEOUT) -> Any:
        key, timeout = str(key), int(timeout)
        try:
            k = self.get(key, fail=True)
        except CacheNotFound:
            k = value(key) if callable(value) else value
            self.set(key=key, value=k, timeout=timeout)
        return k
    
    def remove(self, *key: str) -> bool:
        removed = 0
        for k in key:
            k = str(k)
            if k in self.__CACHE:
                del self.__CACHE[k]
                removed += 1
        return removed == len(key)

    def update_timeout(self, key: str, timeout: int = DEFAULT_CACHE_TIMEOUT) -> Any:
        key, timeout = str(key), int(timeout)
        v = self.get(key=key, fail=True)
        self.__CACHE[key]['timeout'] = datetime.utcnow() + timedelta(seconds=timeout)
        return v
