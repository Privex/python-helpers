import logging

log = logging.getLogger(__name__)

__all__ = []

try:
    from .base import AsyncCacheAdapter

    __all__ += ['AsyncCacheAdapter']
except ImportError:
    log.exception("[%s] Failed to import %s from %s (unknown error!)", __name__, 'AsyncCacheAdapter', f'{__name__}.base')

try:
    from .AsyncMemoryCache import AsyncMemoryCache

    __all__ += ['AsyncMemoryCache']
except ImportError:
    log.exception("[%s] Failed to import %s from %s (unknown error!)", __name__, 'AsyncMemoryCache', f'{__name__}.AsyncMemoryCache')

from .AsyncMemoryCache import AsyncMemoryCache

try:
    from .AsyncRedisCache import AsyncRedisCache

    __all__ += ['AsyncRedisCache']
except ImportError:
    log.exception("[%s] Failed to import %s from %s (missing package 'aioredis' maybe?)",
                  __name__, 'AsyncRedisCache', f'{__name__}.AsyncRedisCache')

try:
    from .AsyncMemcachedCache import AsyncMemcachedCache
    
    __all__ += ['AsyncMemcachedCache']
except ImportError:
    log.exception("[%s] Failed to import %s from %s (missing package 'aioredis' maybe?)",
                  __name__, 'AsyncMemcachedCache', f'{__name__}.AsyncMemcachedCache')
