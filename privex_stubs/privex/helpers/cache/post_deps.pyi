import sqlite3
from collections import namedtuple
from datetime import datetime
from typing import Any, Coroutine, List, Optional, Tuple, Union

import aiosqlite
from async_property import async_property
from privex.db.query.asyncx.sqlite import SqliteAsyncQueryBuilder

from privex.db.sqlite import SqliteWrapper, SqliteAsyncWrapper

from privex.db import SqliteQueryBuilder

from privex.helpers.types import Number

SqliteCacheResult = namedtuple('SqliteCacheResult', 'name value expires_at')


def sqlite_cache_set_dbfolder(folder_path: str): ...


def sqlite_cache_set_dbname(name: str): ...


class _SQManagerBase:
    def _conv_result(self, f: Optional[Union[dict, tuple]]) -> Optional[Union[SqliteCacheResult, List[SqliteCacheResult]]]: ...
    
    def _datetime_to_unix(self, dt: datetime) -> float: ...
    
    def _calc_expires(self, expires_at: Union[float, datetime] = None, expires_secs: float = None) -> Optional[float]: ...


class SqliteCacheManager(SqliteWrapper, _SQManagerBase):
    DEFAULT_DB_FOLDER: str
    DEFAULT_DB_NAME: str
    DEFAULT_DB: str
    SCHEMAS: List[Tuple[str, str]]
    
    def make_connection(self, *args, **kwargs) -> sqlite3.Connection: ...
    
    @property
    def conn(self) -> sqlite3.Connection: ...
    
    @property
    def cache_builder(self) -> SqliteQueryBuilder: ...
    
    def get_cache_all(self) -> List[SqliteCacheResult]: ...
    
    def find_cache_key(self, name: str) -> Optional[SqliteCacheResult]: ...
    
    def cache_key_exists(self, name: str) -> bool: ...
    
    def insert_cache_key(self, name: str, value: Any, expires_secs: Number = None, expires_at: Union[Number, datetime] = None): ...
    
    def update_cache_key(self, name: str, value: Any, expires_secs: Number = None, expires_at: Union[Number, datetime] = None): ...
    
    def set_cache_key(self, name: str, value: Any, expires_secs: Number = None, expires_at: Union[Number, datetime] = None): ...
    
    def delete_cache_key(self, name: str) -> int: ...
    
    def purge_expired(self) -> int: ...
    
    def close(self, clean_all=False, thread_id=None): ...


class AsyncSqliteCacheManager(SqliteAsyncWrapper, _SQManagerBase):
    DEFAULT_DB_FOLDER: str
    DEFAULT_DB_NAME: str
    DEFAULT_DB: str
    SCHEMAS: List[Tuple[str, str]]
    
    def make_connection(self, *args, **kwargs) -> Union[aiosqlite.Connection, Coroutine[Any, Any, aiosqlite.Connection]]: ...
    
    async def _make_connection(self, *args, **kwargs) -> aiosqlite.Connection: ...
    
    @async_property
    async def conn(self) -> aiosqlite.Connection: ...
    
    @property
    def cache_builder(self) -> SqliteAsyncQueryBuilder: ...
    
    async def get_cache_all(self) -> List[SqliteCacheResult]: ...
    
    async def find_cache_key(self, name: str) -> Optional[SqliteCacheResult]: ...
    
    async def cache_key_exists(self, name: str) -> bool: ...
    
    async def insert_cache_key(self, name: str, value: Any, expires_secs: Number = None, expires_at: Union[Number, datetime] = None): ...
    
    async def update_cache_key(self, name: str, value: Any, expires_secs: Number = None, expires_at: Union[Number, datetime] = None): ...
    
    async def set_cache_key(self, name: str, value: Any, expires_secs: Number = None, expires_at: Union[Number, datetime] = None): ...
    
    async def delete_cache_key(self, name: str) -> int: ...
    
    async def purge_expired(self) -> int: ...
    
    async def close(self, clean_all=False, thread_id=None): ...
