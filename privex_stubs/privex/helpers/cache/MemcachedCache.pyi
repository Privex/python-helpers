import pylibmc
from privex.helpers.cache.CacheAdapter import CacheAdapter as CacheAdapter
from privex.helpers.common import byteify as byteify, empty as empty, stringify as stringify
from privex.helpers.exceptions import CacheNotFound as CacheNotFound
from privex.helpers.plugin import close_memcached as close_memcached, get_memcached as get_memcached
from privex.helpers.settings import DEFAULT_CACHE_TIMEOUT as DEFAULT_CACHE_TIMEOUT
from typing import Any, Optional, Union

log: Any

class MemcachedCache(CacheAdapter):
    pickle_default: bool = ...
    use_pickle: bool
    adapter_enter_reconnect: bool = ...
    adapter_exit_close: bool = ...
    def __init__(self, use_pickle: bool=..., mcache_instance: pylibmc.Client=..., *args: Any, **kwargs: Any) -> None: ...
    @property
    def mcache(self) -> pylibmc.Client: ...
    def get(self, key: Union[bytes, str], default: Any=..., fail: bool=...) -> Any: ...
    def set(self, key: Union[bytes, str], value: Any, timeout: Optional[int]=...) -> Any: ...
    def remove(self, *key: Union[bytes, str]) -> bool: ...
    def update_timeout(self, key: str, timeout: int=...) -> Any: ...
    def connect(self, *args: Any, new_connection: Any=..., **kwargs: Any) -> pylibmc.Client: ...
    def close(self): ...
