from async_property import async_property
from privex.helpers import settings as settings
from privex.helpers.cache.asyncx.base import AsyncCacheAdapter as AsyncCacheAdapter
from privex.helpers.common import empty as empty, empty_if as empty_if, is_true as is_true
from privex.helpers.exceptions import CacheNotFound as CacheNotFound
from typing import Any, Optional

from privex.helpers.cache.post_deps import AsyncSqliteCacheManager, SqliteCacheResult

log: Any


def _cache_result_expired(res: SqliteCacheResult, _auto_purge=True) -> bool: ...

class AsyncSqliteCache(AsyncCacheAdapter):
    pickle_default: bool = ...
    use_pickle: bool
    last_purged_expired: Optional[int] = ...
    db_file: Any = ...
    db_folder: Any = ...
    connection_kwargs: Any = ...
    memory_persist: Any = ...
    purge_every: Any = ...
    _wrapper: Optional[AsyncSqliteCacheManager] = ...
    wrapper: AsyncSqliteCacheManager = ...
    
    def __init__(self, db_file: str=..., memory_persist: Any=..., use_pickle: bool=..., connection_kwargs: dict=..., *args: Any, **kwargs: Any) -> None: ...
    @property
    def purge_due(self) -> bool: ...
    
    @async_property
    async def wrapper(self) -> AsyncSqliteCacheManager: ...
    
    async def purge_expired(self, force: Any=...) -> Optional[int]: ...
    async def get(self, key: str, default: Any=..., fail: bool=..., _auto_purge: Any=...) -> Any: ...
    async def set(self, key: str, value: Any, timeout: Optional[int]=..., _auto_purge: Any=...) -> Any: ...
    async def remove(self, *key: str) -> bool: ...
    async def update_timeout(self, key: str, timeout: int=...) -> Any: ...
    async def connect(self, db: Any=..., *args: Any, connection_kwargs: Any=..., memory_persist: Any=..., **kwargs: Any) -> AsyncSqliteCacheManager: ...
    def _connect(self, db: Any=..., *args: Any, connection_kwargs: Any=..., memory_persist: Any=..., **kwargs: Any) -> AsyncSqliteCacheManager: ...
    async def close(self) -> None: ...
