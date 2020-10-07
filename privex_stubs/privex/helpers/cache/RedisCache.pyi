from privex.helpers import plugin as plugin
from privex.helpers.cache.CacheAdapter import CacheAdapter as CacheAdapter
from privex.helpers.common import empty as empty
from privex.helpers.exceptions import CacheNotFound as CacheNotFound
from privex.helpers.plugin import close_redis as close_redis, get_redis as get_redis
from privex.helpers.settings import DEFAULT_CACHE_TIMEOUT as DEFAULT_CACHE_TIMEOUT
from redis import Redis
from typing import Any, Optional

log: Any

class RedisCache(CacheAdapter):
    pickle_default: bool = ...
    use_pickle: bool
    def __init__(self, use_pickle: bool=..., redis_instance: Redis=..., *args: Any, **kwargs: Any) -> None: ...
    @property
    def redis(self) -> Redis: ...
    def get(self, key: str, default: Any=..., fail: bool=...) -> Any: ...
    def set(self, key: str, value: Any, timeout: Optional[int]=...) -> Any: ...
    def remove(self, *key: str) -> bool: ...
    def update_timeout(self, key: str, timeout: int=...) -> Any: ...
    def connect(self, *args: Any, **kwargs: Any) -> Redis: ...
    def close(self): ...
