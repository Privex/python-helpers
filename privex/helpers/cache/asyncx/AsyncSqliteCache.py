import pickle
import time
import logging
from os import makedirs
from os.path import dirname, exists, isabs, join
from typing import Any, Optional

from privex.helpers.cache.asyncx.base import AsyncCacheAdapter
from privex.helpers.exceptions import CacheNotFound
from privex.helpers.common import empty, empty_if, is_true
from privex.helpers import settings
from async_property import async_property

from privex.helpers.types import Number, T

log = logging.getLogger(__name__)


def _cache_result_expired(res, _auto_purge=True) -> bool:
    if empty(res): return False
    if empty(res.expires_at, zero=True) or not _auto_purge: return False
    return float(res.expires_at) <= time.time()


class AsyncSqliteCache(AsyncCacheAdapter):
    """
    An SQLite3 backed implementation of :class:`.AsyncCacheAdapter`. Creates and uses a semi-global Sqlite instance via
    :py:mod:`privex.helpers.plugin` by default.

    To allow for a wide variety of Python objects to be safely stored and retrieved from Sqlite, this class
    uses the :py:mod:`pickle` module for serialising + un-serialising values to/from Sqlite.

    **Basic Usage**::

        >>> from privex.helpers import AsyncSqliteCache
        >>> rc = AsyncSqliteCache()
        >>> await rc.set('hello', 'world')
        >>> await rc.get('hello')
        'world'
        >>> rc['hello']
        'world'


    **Disabling Pickling**

    In some cases, you may need interoperable caching with other languages. The :py:mod:`pickle` serialisation
    technique is extremely specific to Python and is largely unsupported outside of Python. Thus if you need
    to share Sqlite cache data with applications in other languages, then you must disable pickling.

    **WARNING:** If you disable pickling, then you must perform your own serialisation + de-serialization on
    complex objects such as ``dict``, ``list``, ``Decimal``, or arbitrary classes/functions after getting
    or setting cache keys.

    **Disabling Pickle per instance**

    Pass ``use_pickle=False`` to the constructor, or access the attribute directly to disable pickling for a
    single instance of SqliteCache (not globally)::

        >>> rc = AsyncSqliteCache(use_pickle=False)  # Opt 1. Disable pickle in constructor
        >>> rc.use_pickle = False              # Opt 2. Disable pickle on an existing instance


    **Disabling Pickle by default on any new instances**

    Change the static attribute :py:attr:`.pickle_default` to ``False`` to disable the use of pickle by default
    across any new instances of SqliteCache::

        >>> AsyncSqliteCache.pickle_default = False



    """
    
    pickle_default: bool = True
    """
    Change this to ``False`` to disable the use of :py:mod:`pickle` by default for any new instances
    of this class.
    """
    
    use_pickle: bool
    """If ``True``, will use :py:mod:`pickle` for serializing objects before inserting into Redis, and
    un-serialising objects retrieved from Sqlite3. This attribute is set in :py:meth:`.__init__`.

    Change this to ``False`` to disable the use of :py:mod:`pickle` - instead values will be passed to / returned
    from Sqlite3 as-is, with no serialisation (this may require you to manually serialize complex types such
    as ``dict`` and ``Decimal`` before insertion, and un-serialise after retrieval).
    """
    
    last_purged_expired: Optional[int] = None
    
    def __init__(self, db_file: str = None, memory_persist=False, use_pickle: bool = None, connection_kwargs: dict = None, *args, **kwargs):
        """
        :class:`.AsyncSqliteCache` uses an auto-generated database filename / path by default, based on the name of the currently running
        script ( retrieved from ``sys.argv[0]`` ), allowing for persistent caching - without any manual configuration of the adapter,
        nor the requirement for any running background services such as ``redis`` / ``memcached``.
        
        

        :param str db_file:     (Optional) Name of / path to Sqlite3 database file to create/use for the cache.
        
        :param bool memory_persist: Use a shared in-memory database, which can be accessed by other instances of this class (in this
                                    process) - which is cleared after all memory connections are closed.
                                    Shortcut for ``db_file='file::memory:?cache=shared'``

        :param bool use_pickle: (Default: ``True``) Use the built-in ``pickle`` to serialise values before
                                storing in Sqlite3, and un-serialise when loading from Sqlite3
        
        :param dict connection_kwargs: (Optional) Additional / overriding kwargs to pass to :meth:`sqlite3.connect` when
                                        :class:`.AsyncSqliteCacheManager` initialises it's sqlite3 connection.
        
        :keyword int purge_every: (Default: 300) Expired + abandoned cache records are purged using the DB manager method
                                  :meth:`.AsyncSqliteCacheManager.purge_expired` during :meth:`.get` / :meth:`.set` calls. To avoid
                                  performance issues, the actual :meth:`.AsyncSqliteCacheManager.purge_expired` method is only called
                                  if at least ``purge_every`` seconds have passed since the last purge was
                                  triggered ( :attr:`.last_purged_expired` )

        """
        from privex.helpers.cache.post_deps import AsyncSqliteCacheManager
        super().__init__(*args, **kwargs)
        self.db_file: str = empty_if(db_file, AsyncSqliteCacheManager.DEFAULT_DB)
        self.db_folder = None
        if ':memory:' not in self.db_file:
            if not isabs(self.db_file): self.db_file = join(AsyncSqliteCacheManager.DEFAULT_DB_FOLDER, self.db_file)
            self.db_folder = dirname(self.db_file)
            if not exists(self.db_folder):
                log.debug("Folder for database doesn't exist. Creating: %s", self.db_folder)
                makedirs(self.db_folder)
        self.connection_kwargs = empty_if(connection_kwargs, {}, itr=True)
        self.memory_persist = is_true(memory_persist)
        self._wrapper = None
        self.purge_every = kwargs.get('purge_every', 300)
        self.use_pickle = self.pickle_default if use_pickle is None else use_pickle
    
    @property
    def purge_due(self) -> bool:
        lpe = AsyncSqliteCache.last_purged_expired
        return empty(lpe, zero=True) or (time.time() - lpe) >= self.purge_every
    
    @async_property
    async def wrapper(self):
        if not self._wrapper:
            await self.connect()

        await self._wrapper.create_schemas()
        return self._wrapper
    
    async def purge_expired(self, force=False) -> Optional[int]:
        if self.purge_due or force:
            log.debug("%s - Expired items purge is due (or force is True). Purging expired cache items...", self.__class__.__name__)
            res = await (await self.wrapper).purge_expired()
            log.debug("Finished purging expired items. Total expired cache items deleted: %s", res)
            AsyncSqliteCache.last_purged_expired = time.time()
            return res
        return None
    
    async def get(self, key: str, default: Any = None, fail: bool = False, _auto_purge=True) -> Any:
        key = str(key)
        _not_found_msg = f'Cache key "{key}" was not found.'
        if _auto_purge: await self.purge_expired()
        
        res = await (await self.wrapper).find_cache_key(key)
        if _cache_result_expired(res, _auto_purge=_auto_purge):
            log.debug("Caller attempted to retrieve expired key '%s', but _auto_purge is True - auto-removing expired key %s", key, key)
            await self.remove(key)
            _not_found_msg += ' (key was expired - auto-removed)'
            res = None
        
        if empty(res):
            if fail: raise CacheNotFound(_not_found_msg)
            return default
        return pickle.loads(res.value) if self.use_pickle else res.value
    
    async def set(self, key: str, value: T, timeout: Optional[Number] = settings.DEFAULT_CACHE_TIMEOUT, _auto_purge=True) -> T:
        if _auto_purge: await self.purge_expired()
        v = pickle.dumps(value) if self.use_pickle else value
        return await (await self.wrapper).set_cache_key(str(key), v, expires_secs=timeout)
    
    async def remove(self, *key: str) -> bool:
        removed = 0
        for k in key:
            k = str(k)
            try:
                await self.get(k, fail=True, _auto_purge=False)
                await (await self.wrapper).delete_cache_key(k)
                removed += 1
            except CacheNotFound:
                pass
        
        return removed == len(key)
    
    async def update_timeout(self, key: str, timeout: Number = settings.DEFAULT_CACHE_TIMEOUT) -> Any:
        key, timeout = str(key), int(timeout)
        v = await self.get(key=key, fail=True, _auto_purge=False)
        await self.set(key=key, value=v, timeout=timeout, _auto_purge=False)
        return v

    async def connect(self, db=None, *args, connection_kwargs=None, memory_persist=None, **kwargs):
        return self._connect(db, *args, connection_kwargs=connection_kwargs, memory_persist=memory_persist, **kwargs)

    def _connect(self, db=None, *args, connection_kwargs=None, memory_persist=None, **kwargs):
        c_kwargs = dict(
            connection_kwargs=empty_if(connection_kwargs, self.connection_kwargs),
            memory_persist=empty_if(memory_persist, self.memory_persist)
        )
        c_kwargs = {**c_kwargs, **kwargs}
        from privex.helpers.cache.post_deps import AsyncSqliteCacheManager
        self._wrapper = AsyncSqliteCacheManager(empty_if(db, self.db_file), *args, **c_kwargs)
        return self._wrapper

    # noinspection PyProtectedMember
    async def close(self):
        cls_name = self.__class__.__name__
        if self._wrapper is not None:
            log.debug("Closing AsyncIO Sqlite3 instance %s._wrapper", cls_name)
            # if self._wrapper._conn:
            try:
                await self._wrapper.close()
            except Exception:
                log.exception("Unexpected error while closing %s._wrapper", cls_name)
            # self._wrapper._conn = None
            self._wrapper = None

