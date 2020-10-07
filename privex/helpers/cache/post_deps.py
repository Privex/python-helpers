import asyncio
import sqlite3
import sys
import time
from collections import namedtuple
from datetime import datetime
from decimal import Decimal
from os import getenv as env
from os.path import basename, expanduser, join
from typing import Any, Callable, Coroutine, List, Optional, Tuple, Union

from async_property import async_property

from privex.helpers import settings
from privex.helpers.asyncx import await_if_needed, awaitable

from privex.db import SqliteQueryBuilder, SqliteWrapper
from privex.helpers.converters import YEAR
from privex.helpers.common import empty
from privex.helpers.plugin import _get_threadstore, _set_threadstore, clean_threadstore
import logging

# SQLITE_APP_DB_NAME = env('SQLITE_APP_DB_NAME', basename(sys.argv[0]))
# SQLITE_APP_DB_FOLDER = env('SQLITE_APP_DB_FOLDER', '~/.privex_cache')
from privex.helpers.types import Number, T

log = logging.getLogger(__name__)

__all__ = [
    'SqliteCacheResult', 'sqlite_cache_set_dbfolder', 'sqlite_cache_set_dbname', 'SqliteCacheManager'
]

SqliteCacheResult = namedtuple('SqliteCacheResult', 'name value expires_at')


def sqlite_cache_set_dbfolder(folder_path: str):
    SqliteCacheManager.DEFAULT_DB_FOLDER = folder_path
    if 'AsyncSqliteCacheManager' in __all__:
        AsyncSqliteCacheManager.DEFAULT_DB_FOLDER = folder_path
        AsyncSqliteCacheManager.DEFAULT_DB = join(AsyncSqliteCacheManager.DEFAULT_DB_FOLDER, AsyncSqliteCacheManager.DEFAULT_DB_NAME)
    SqliteCacheManager.DEFAULT_DB = join(SqliteCacheManager.DEFAULT_DB_FOLDER, SqliteCacheManager.DEFAULT_DB_NAME)


def sqlite_cache_set_dbname(name: str):
    SqliteCacheManager.DEFAULT_DB_NAME = name
    if 'AsyncSqliteCacheManager' in __all__:
        AsyncSqliteCacheManager.DEFAULT_DB_NAME = name
        AsyncSqliteCacheManager.DEFAULT_DB = join(AsyncSqliteCacheManager.DEFAULT_DB_FOLDER, AsyncSqliteCacheManager.DEFAULT_DB_NAME)
    SqliteCacheManager.DEFAULT_DB = join(SqliteCacheManager.DEFAULT_DB_FOLDER, SqliteCacheManager.DEFAULT_DB_NAME)


class _SQManagerBase:
    def _conv_result(self, f: Optional[Union[dict, tuple]]) -> Optional[Union[SqliteCacheResult, List[SqliteCacheResult]]]:
        if f is not None:
            if isinstance(f, (list, tuple)) and len(f) > 0 and isinstance(f[0], (tuple, dict)):
                return [self._conv_result(k) for k in f]
            if isinstance(f, dict):
                return SqliteCacheResult(**f)
            return SqliteCacheResult(*f)
        return None

    def _datetime_to_unix(self, dt: datetime) -> float:
        diff = dt - datetime.now()
        diff_secs = float(diff.total_seconds())
        unix_now = time.time()
        return unix_now + diff_secs

    def _calc_expires(self, expires_at: Union[Number, datetime] = None, expires_secs: Number = None) -> Optional[float]:
        if not empty(expires_at, zero=True):
            if isinstance(expires_at, datetime): return float(self._datetime_to_unix(expires_at))
            if isinstance(expires_at, (int, str, Decimal)): return self._calc_expires(expires_at=float(expires_at))
            if isinstance(expires_at, float): return float(time.time() + expires_at) if expires_at < float(YEAR * 5) else expires_at
            raise ValueError(f"{self.__class__.__name__}._calc_expires expected expires_at to be a datetime or numeric object. "
                             f"object passed was type: {type(expires_at)} || repr: {repr(expires_at)}")
        return time.time() + float(expires_secs) if not empty(expires_secs, zero=True) else None
    

class SqliteCacheManager(SqliteWrapper, _SQManagerBase):
    ###
    # If a database path isn't specified, then the class attribute DEFAULT_DB will be used.
    ###
    DEFAULT_DB_FOLDER: str = settings.SQLITE_APP_DB_FOLDER
    DEFAULT_DB_NAME: str = settings.SQLITE_APP_DB_NAME + '.sqlite3'
    DEFAULT_DB: str = join(DEFAULT_DB_FOLDER, DEFAULT_DB_NAME)
    
    ###
    # The SCHEMAS class attribute contains a list of tuples, with each tuple containing the name of a
    # table, as well as the SQL query required to create the table if it doesn't exist.
    ###
    SCHEMAS: List[Tuple[str, str]] = [
        ('pvcache', "CREATE TABLE pvcache ("
                    "name TEXT PRIMARY KEY, "
                    "value BLOB, "
                    "expires_at REAL DEFAULT NULL"
                    ");"
         ),
        # ('items', "CREATE TABLE items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT);"),
    ]
    
    def make_connection(self, *args, **kwargs) -> sqlite3.Connection:
        return self.connector_func(*args, **kwargs)
    
    @property
    def conn(self) -> sqlite3.Connection:
        k = 'sqlite3cache_conn'
        t = _get_threadstore(k)
        if t is None:
            return _set_threadstore(k, self.make_connection(*self.connector_args, **self.connector_kwargs))
        return t
    
    @property
    def cache_builder(self) -> SqliteQueryBuilder:
        return self.builder('pvcache')
    
    def get_cache_all(self):
        return self._conv_result(self.fetchall("SELECT * FROM pvcache;"))
    
    def find_cache_key(self, name: str) -> Optional[SqliteCacheResult]:
        # self.cache_builder.select('*').where('name', name).fetch()
        f = self.fetchone("SELECT * FROM pvcache WHERE name = ?;", [name])
        return self._conv_result(f)
    
    def cache_key_exists(self, name: str) -> bool:
        return isinstance(self.find_cache_key(name), SqliteCacheResult)

    def insert_cache_key(self, name: str, value: Any, expires_secs: Number = None, expires_at: Union[Number, datetime] = None):
        expires_at = self._calc_expires(expires_at=expires_at, expires_secs=expires_secs)
        log.debug("Inserting cache key '%s' with expires_at = '%s' and value: %s", name, expires_at, value)
        # return self.action(
        #     "INSERT INTO pvcache (name, value, expires_at) VALUES (?, ?, ?) "
        #     "ON CONFLICT(name) DO UPDATE SET value=?,expires_at=?;",
        #     (name, value, expires_at, value, expires_at)
        # )
        return self.action(
            "INSERT INTO pvcache (name, value, expires_at) VALUES (?, ?, ?);",
            (name, value, expires_at)
        )
    
    def update_cache_key(self, name: str, value: Any, expires_secs: Number = None, expires_at: Union[Number, datetime] = None):
        expires_at = self._calc_expires(expires_at=expires_at, expires_secs=expires_secs)
        log.debug("Updating cache key '%s' with expires_at = '%s' and value: %s", name, expires_at, value)
        # return self.insert_cache_key(name, value, expires_at=expires_at, expires_secs=expires_secs)
        return self.action("UPDATE pvcache SET value = ?, expires_at = ? WHERE name = ?;", (value, expires_at, name))

    def set_cache_key(self, name: str, value: Any, expires_secs: Number = None, expires_at: Union[Number, datetime] = None):
        # expires_at = self._calc_expires(expires_at=expires_at, expires_secs=expires_secs)
        cfunc: Callable = self.update_cache_key if self.cache_key_exists(name) else self.insert_cache_key
        return cfunc(name=name, value=value, expires_at=expires_at, expires_secs=expires_secs)

    def delete_cache_key(self, name: str) -> int:
        return self.action("DELETE FROM pvcache WHERE name = ?;", [name])

    def purge_expired(self) -> int:
        return self.action("DELETE FROM pvcache WHERE expires_at <= ?;", [time.time()])

    def close(self, clean_all=False, thread_id=None):
        self.close_cursor()
        k = 'sqlite3cache_conn'
        t: Optional[sqlite3.Connection] = _get_threadstore(k)
        if t is not None:
            t.close()
            del t
        return clean_threadstore(thread_id=thread_id, name=k, clean_all=clean_all)


try:
    from privex.db import SqliteAsyncWrapper, SqliteAsyncQueryBuilder
    import aiosqlite

    class AsyncSqliteCacheManager(SqliteAsyncWrapper, _SQManagerBase):
        ###
        # If a database path isn't specified, then the class attribute DEFAULT_DB will be used.
        ###
        DEFAULT_DB_FOLDER: str = settings.SQLITE_APP_DB_FOLDER
        DEFAULT_DB_NAME: str = settings.SQLITE_APP_DB_NAME + '.sqlite3'
        DEFAULT_DB: str = join(DEFAULT_DB_FOLDER, DEFAULT_DB_NAME)
    
        ###
        # The SCHEMAS class attribute contains a list of tuples, with each tuple containing the name of a
        # table, as well as the SQL query required to create the table if it doesn't exist.
        ###
        SCHEMAS: List[Tuple[str, str]] = [
            ('pvcache', "CREATE TABLE pvcache ("
                        "name TEXT PRIMARY KEY, "
                        "value BLOB, "
                        "expires_at REAL DEFAULT NULL"
                        ");"
             ),
            # ('items', "CREATE TABLE items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT);"),
        ]

        @awaitable
        def make_connection(self, *args, **kwargs) -> Union[aiosqlite.Connection, Coroutine[Any, Any, aiosqlite.Connection]]:
            return self._make_connection(*args, **kwargs)

        async def _make_connection(self, *args, **kwargs) -> aiosqlite.Connection:
            await_conn = kwargs.pop('await_conn', True)
            conn = self.connector_func(*args, **kwargs)
            if asyncio.iscoroutine(conn) and await_conn:
                c = await conn
                await self.create_schemas()
                return c
            return conn

        @async_property
        async def conn(self) -> aiosqlite.Connection:
            k = 'sqlite3cache_async_conn'
            t = _get_threadstore(k)
            if t is None:
                conn = await self._make_connection(*self.connector_args, **self.connector_kwargs)
                return _set_threadstore(k, conn)
            return t
    
        @property
        def cache_builder(self) -> SqliteAsyncQueryBuilder:
            return self.builder('pvcache')
    
        async def get_cache_all(self):
            return self._conv_result(await await_if_needed(self.fetchall("SELECT * FROM pvcache;")))
    
        async def find_cache_key(self, name: str) -> Optional[SqliteCacheResult]:
            # self.cache_builder.select('*').where('name', name).fetch()
            f = await await_if_needed(self.fetchone("SELECT * FROM pvcache WHERE name = ?;", [name]))
            return self._conv_result(f)
    
        async def cache_key_exists(self, name: str) -> bool:
            return isinstance(await self.find_cache_key(name), SqliteCacheResult)
    
        async def insert_cache_key(self, name: str, value: Any, expires_secs: Number = None, expires_at: Union[Number, datetime] = None):
            expires_at = self._calc_expires(expires_at=expires_at, expires_secs=expires_secs)
            log.debug("Inserting cache key '%s' with expires_at = '%s' and value: %s", name, expires_at, value)
            # return await await_if_needed(self.action(
            #     "INSERT INTO pvcache (name, value, expires_at) VALUES (?, ?, ?) "
            #     "ON CONFLICT(name) DO UPDATE SET value=?,expires_at=?;",
            #     (name, value, expires_at, value, expires_at)
            # ))
            return await await_if_needed(self.action(
                "INSERT INTO pvcache (name, value, expires_at) VALUES (?, ?, ?);",
                (name, value, expires_at)
            ))
    
        async def update_cache_key(self, name: str, value: Any, expires_secs: Number = None, expires_at: Union[Number, datetime] = None):
            expires_at = self._calc_expires(expires_at=expires_at, expires_secs=expires_secs)
            log.debug("Updating cache key '%s' with expires_at = '%s' and value: %s", name, expires_at, value)
            # return await self.insert_cache_key(name, value, expires_at=expires_at, expires_secs=expires_secs)
            return await await_if_needed(
                self.action("UPDATE pvcache SET value = ?, expires_at = ? WHERE name = ?;", (value, expires_at, name))
            )
    
        async def set_cache_key(self, name: str, value: T, expires_secs: Number = None, expires_at: Union[Number, datetime] = None) -> T:
            expires_at = self._calc_expires(expires_at=expires_at, expires_secs=expires_secs)
            cfunc: Callable = self.update_cache_key if await self.cache_key_exists(name) else self.insert_cache_key
            await cfunc(name=name, value=value, expires_at=expires_at, expires_secs=expires_secs)
            return value
    
        async def delete_cache_key(self, name: str) -> int:
            return await await_if_needed(self.action("DELETE FROM pvcache WHERE name = ?;", [name]))
    
        async def purge_expired(self) -> int:
            return await await_if_needed(self.action("DELETE FROM pvcache WHERE expires_at < ?;", [time.time()]))
    
        async def close(self, clean_all=False, thread_id=None):
            await await_if_needed(self.close_cursor())
            k = 'sqlite3cache_async_conn'
            t: Optional[aiosqlite.Connection] = _get_threadstore(k)
            if t is not None:
                await t.close()
                del t
            return clean_threadstore(thread_id=thread_id, name=k, clean_all=clean_all)


    __all__ += ['AsyncSqliteCacheManager']
except ImportError as e:
    log.warning(f"[{__name__}] Failed to import SqliteAsyncWrapper and/or SqliteAsyncQueryBuilder from privex.db. Reason: {type(e)} - {str(e)}")

