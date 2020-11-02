"""
This module handles connection objects for databases, APIs etc. by exposing functions which initialise and
store class instances for re-use.

It's primarily intended to be used to enable database, caching and third-party API connectivity for the helpers in this
package, however, you're free to use the functions / classes / attributes exposed in this module for your own apps.

Classes are generally initialised using the settings from :py:mod:`.settings` - see the docs for that module to learn
how to override the settings if the defaults don't work for you.


**Copyright**::

        +===================================================+
        |                 © 2019 Privex Inc.                |
        |               https://www.privex.io               |
        +===================================================+
        |                                                   |
        |        Originally Developed by Privex Inc.        |
        |        License: X11 / MIT                         |
        |                                                   |
        |        Core Developer(s):                         |
        |                                                   |
        |          (+)  Chris (@someguy123) [Privex]        |
        |          (+)  Kale (@kryogenic) [Privex]          |
        |                                                   |
        +===================================================+

    Copyright 2019     Privex Inc.   ( https://www.privex.io )


"""
import logging
import threading
from os import path
from typing import Any, Union, Optional, Generator, Tuple, Dict

from privex.helpers.collections import DictObject

from privex.helpers import settings
from privex.helpers.types import T
from privex.helpers.common import empty_if, empty
from privex.helpers.exceptions import GeoIPDatabaseNotFound

log = logging.getLogger(__name__)

__all__ = [
    'HAS_REDIS', 'HAS_ASYNC_REDIS', 'HAS_ASYNC_MEMCACHED', 'HAS_DNSPYTHON', 'HAS_CRYPTO', 'HAS_SETUPPY_BUMP',
    'HAS_SETUPPY_COMMANDS', 'HAS_SETUPPY_COMMON', 'HAS_GEOIP', 'HAS_MEMCACHED', 'HAS_PRIVEX_DB', 'clean_threadstore'
]

HAS_REDIS = False
"""If the ``redis`` module was imported successfully, this will change to True."""

HAS_ASYNC_REDIS = False
"""If the ``aioredis`` module was imported successfully, this will change to True."""

HAS_ASYNC_MEMCACHED = False
HAS_DNSPYTHON = False
"""If the ``dns.resolver`` module was imported successfully, this will change to True."""

HAS_CRYPTO = False
"""If :py:mod:`privex.helpers.crypto` was imported successfully, this will change to True"""

HAS_SETUPPY_COMMON = False
"""If :py:mod:`privex.helpers.setuppy.common` was imported successfully, this will change to True"""

HAS_SETUPPY_BUMP = False
"""If :py:mod:`privex.helpers.setuppy.bump` was imported successfully, this will change to True"""

HAS_SETUPPY_COMMANDS = False
"""If :py:mod:`privex.helpers.setuppy.commands` was imported successfully, this will change to True"""

HAS_GEOIP = False
"""If :py:mod:`privex.helpers.geoip` was imported successfully, this will change to True"""

HAS_MEMCACHED = False

HAS_PRIVEX_DB = None
"""If the ``privex.db`` module was imported successfully, this will change to True."""

__STORE = dict(threads={})
"""This ``dict`` is used to store initialised classes for connections to databases, APIs etc."""


def _get_threadstore(name=None, fallback=None, thread_id=None) -> Any:
    thread_id = empty_if(thread_id, threading.get_ident())
    if thread_id not in __STORE['threads']:
        __STORE['threads'][thread_id] = {}
    thread_store: dict = __STORE['threads'][thread_id]
    if name is None:
        return thread_store
    
    return thread_store.get(name, fallback)


def _get_all_threadstore(name=None) -> Generator[Tuple[Union[int, str], Union[Dict[str, Any], Any]], None, None]:
    """
    
    Get the ``'redis'`` key from every thread in the thread store::
    
        >>> for t_id, inst in _get_all_threadstore('redis'):
        ...     inst.close()
        ...
        >>> clean_threadstore(name='redis')
    
    Get the thread store for every single thread::
        
        >>> for t_id, ts in _get_all_threadstore():
        ...     if 'redis' in ts: print(t_id, 'has redis instance!')
        ...     if 'aiomemcached' in ts: print(t_id, 'has asyncio memcached instance!')
    
    
    :param str name: Yield only this key from each thread store (if it exists)
    :return Generator store_gen: A generator of tuples containing either ``(thread_id, thread_store: dict)``, or ``(t_id, value)``
                                 depending on whether ``name`` is empty or not.
    """
    for t_id, ts in __STORE['threads'].items():
        if empty(name):
            yield t_id, ts
        elif name in ts:
            yield t_id, ts[name]


def _set_threadstore(name, obj: T, thread_id=None) -> T:
    thread_store = _get_threadstore(thread_id=thread_id)
    thread_store[name] = obj
    return obj


def clean_threadstore(thread_id=None, name=None, clean_all: bool = False) -> bool:
    """
    Remove the per-thread instance storage in :attr:`.__STORE`, usually called when a thread is exiting.

    Can also be used to clear a certain key in all thread stores, or completely clear every key from every thread store.

    Example::

        >>> def some_thread():
        ...     r = get_redis()
        ...     print('doing something')
        ...     print('cleaning up...')
        ...     clean_threadstore()       # With no arguments, it cleans the thread store for the thread that called it.
        >>> t = threading.Thread(target=some_thread)
        >>> t.start()
        >>> t.join()

    Usage outside of a thread::

        >>> t = threading.Thread(target=some_thread)
        >>> t.start()
        >>> thread_id = t.ident                      # Get the thread ID for the started thread
        >>> t.join()                                 # Wait for the thread to finish
        >>> if thread_id is not None:                # Make sure the thread ID isn't None
        ...     clean_threadstore(thread_id)         # Cleanup any leftover instances, if there are any.
        ...

    Removing an individual item from thread store::
        
        >>> def some_thread():
        ...     r = get_redis()
        ...     print('doing something')
        ...     print('cleaning up...')
        ...     clean_threadstore(name='redis')   # Delete only the key 'redis' from the thread store
    
    Removing an individual item from the thread store for **ALL thread ID's**::
    
        >>> # Remove the redis instance from every thread store
        >>> clean_threadstore(name='redis', clean_all=True)
    
    Clearing the entire thread store for every thread ID::
    
        >>> clean_threadstore(clean_all=True)
    
    
    :param thread_id: The ID of the thread (usually from :func:`threading.get_ident`) to clean the storage for.
                      If left as None, will use the ID returned by :func:`threading.get_ident`.
    
    :param name:      If specified, then only the key ``name`` will be deleted from the thread store, instead of the entire thread store.
    :param bool clean_all: (default: ``False``) If ``True`` - when ``name`` is non-empty - that key will be removed from every
                           thread ID's thread store - while if ``name`` is empty, every single thread ID's thread store is cleared.
    """
    thread_id = empty_if(thread_id, threading.get_ident())

    if clean_all:
        for t_id, ts in __STORE['threads'].items():
            ts: dict
            if empty(name):
                log.debug("[clean_threadstore] (clean_all True) Cleaning entire thread store for thread ID '%s'", t_id)
                for n in ts.keys():
                    log.debug("[clean_threadstore] Cleaning '%s' key for thread ID '%s'", name, t_id)
                    del ts[n]
                continue
            log.debug("[clean_threadstore] (clean_all True) Cleaning '%s' key for thread ID '%s'", name, t_id)
            if name in ts:
                log.debug("[clean_threadstore] Found %s in thread ID %s - deleting...", name, ts)
                del ts[name]
        return True
    
    if thread_id in __STORE['threads']:
        ts = __STORE['threads'][thread_id]
        if name is None:
            del __STORE['threads'][thread_id]
            return True
        elif name in ts:
            del ts[name]
            return True
    return False


try:
    import redis


    def connect_redis(*args, **rd_config):
        from privex.helpers.common import extract_settings
        # return redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
        return redis.Redis(*args, **extract_settings('REDIS_', settings, merge_conf=dict(rd_config)))
    
    def get_redis(new_connection=False, thread_id=None, **rd_config) -> redis.Redis:
        """Get a Redis connection object. Create one if it doesn't exist."""
        from privex.helpers.common import empty_if, extract_settings

        if new_connection:
            return connect_redis(**rd_config)
        # if thread_id not in __STORE['threads']: __STORE['threads'][thread_id] = {}

        # thread_store = __STORE['threads'][thread_id]
        rd = _get_threadstore('redis', thread_id=thread_id)
        
        if rd is None:
            rd = connect_redis(**rd_config)
            _set_threadstore('redis', rd, thread_id=thread_id)
        return rd
        # if 'redis' in thread_store and not new_connection: return thread_store['redis']
        # if rd is not None and not new_connection:
        #
        # # if 'redis' not in thread_store:
        #     if new_connection:
        #         return rd
        #     thread_store['redis'] = rd
        # return thread_store['redis']
    
    def close_redis(thread_id=None, close_all=False) -> bool:
        """
        Close the global Redis connection and delete the instance.
        
        :param thread_id: Close and delete the Redis instance for this thread ID, instead of the detected current thread
        :param bool close_all: Close all AsyncIO Redis instances for every thread ID, then purge their thread store keys.
        :return bool deleted: ``True`` if an instance was found and deleted. ``False`` if there was no existing Redis instance.
        """
        if close_all:
            for t_id, rd in _get_all_threadstore('redis'):
                if rd is None:
                    continue
                log.debug("Closing redis for thread ID %s", t_id)
                try:
                    rd.close()
                except Exception:
                    log.exception("Exception while closing redis for thread ID %s", t_id)
            return clean_threadstore(name='redis', clean_all=True)
    
        rd: Union[str, redis.Redis] = _get_threadstore('redis', 'NOT_FOUND', thread_id=thread_id)
        if rd != 'NOT_FOUND':
            rd.close()
            clean_threadstore(thread_id=thread_id, name='redis')
            return True
        return False

    def reset_redis(thread_id=None) -> redis.Redis:
        """Close the global Redis connection, delete the instance, then re-instantiate it"""
        close_redis(thread_id=thread_id)
        return _set_threadstore('redis', get_redis(True, thread_id), thread_id=thread_id)
    
    def configure_redis(host=settings.REDIS_HOST, port: int = settings.REDIS_PORT, db: int = settings.REDIS_DB, **kwargs):
        """Update global Redis settings and re-instantiate the global Redis instance with the new settings."""
        thread_id = kwargs.get('thread_id', None)
        settings.REDIS_DB = db
        settings.REDIS_PORT = port
        settings.REDIS_HOST = host
        return reset_redis(thread_id=thread_id)


    __all__ += ['get_redis', 'reset_redis', 'configure_redis', 'close_redis', 'connect_redis']
    HAS_REDIS = True

except ImportError:
    log.debug('privex.helpers __init__ failed to import "redis", Redis dependent helpers will be disabled.')
except Exception as e:
    log.debug('privex.helpers __init__ failed to import "redis", (unknown exception), '
              'Redis dependent helpers will be disabled. Exception: %s %s', type(e), str(e))

try:
    import aioredis
    HAS_ASYNC_REDIS = True


    async def connect_redis_async(**rd_config) -> aioredis.Redis:
        from privex.helpers.common import extract_settings
        cf = extract_settings('REDIS_', settings, merge_conf=dict(rd_config))
        _addr = f"redis://{cf.pop('host', 'localhost')}:{cf.pop('port', 6379)}"
        return await aioredis.create_redis_pool(
            address=_addr, **cf
        )


    async def get_redis_async(new_connection=False, thread_id=None, **rd_config) -> aioredis.connection:
        """
        Get an Async Redis connection object. Create one if it doesn't exist.
        
        Usage::
            
            >>> redis_conn = await get_redis_async()
            >>> redis = await redis_conn
            >>> await redis.set('some_key', 'example')
            >>> await redis.get('some_key')
            'example'
            
        
        """
        from privex.helpers.common import empty_if, extract_settings
    
        if new_connection: return await connect_redis_async(**rd_config)
        rd: Optional[aioredis.Redis] = _get_threadstore('aioredis', thread_id=thread_id)
    
        if rd is None:
            rd: aioredis.Redis = _set_threadstore('aioredis', await connect_redis_async(**rd_config), thread_id=thread_id)
        return rd

    async def close_redis_async(thread_id=None, close_all=False) -> bool:
        """
        Close the global Async Redis connection and delete the instance.

        :param thread_id: Close and delete the Redis instance for this thread ID, instead of the detected current thread
        :param bool close_all: Close all AsyncIO Redis instances for every thread ID, then purge their thread store keys.
        :return bool deleted: ``True`` if an instance was found and deleted. ``False`` if there was no existing Redis instance.
        """
        rd: Optional[Union[aioredis.connection, aioredis.Redis]]
        if close_all:
            for t_id, rd in _get_all_threadstore('aioredis'):
                if rd is None:
                    continue
                log.debug("Closing aioredis for thread ID %s", t_id)
                try:
                    rd.close()
                    await rd.wait_closed()
                except RuntimeError as err:
                    log.warning("[ignored] RuntimeError while closing aioredis (thread %s): %s - %s", thread_id, type(err), str(err))
                except Exception:
                    log.exception("Exception while closing aioredis for thread ID %s", t_id)
            return clean_threadstore(name='aioredis', clean_all=True)
        
        rd = _get_threadstore('aioredis', 'NOT_FOUND', thread_id=thread_id)
        if rd != 'NOT_FOUND':
            try:
                rd.close()
                await rd.wait_closed()
            except RuntimeError as err:
                log.warning("[ignored] RuntimeError while closing aioredis (thread %s): %s - %s", thread_id, type(err), str(err))
            clean_threadstore(thread_id=thread_id, name='aioredis')
            return True
        return False


    async def reset_redis_async(thread_id=None) -> aioredis.connection:
        """Close the global Async Redis connection, delete the instance, then re-instantiate it"""
        await close_redis_async(thread_id=thread_id)
        return await _set_threadstore('aioredis', get_redis_async(True, thread_id), thread_id=thread_id)


    async def configure_redis_async(host=settings.REDIS_HOST, port: int = settings.REDIS_PORT, db: int = settings.REDIS_DB, **kwargs):
        """Update global Redis settings and re-instantiate the global Async Redis instance with the new settings."""
        thread_id = kwargs.get('thread_id', None)
        settings.REDIS_DB = db
        settings.REDIS_PORT = port
        settings.REDIS_HOST = host
        return await reset_redis_async(thread_id=thread_id)


    __all__ += ['get_redis_async', 'reset_redis_async', 'configure_redis_async', 'close_redis_async', 'connect_redis_async']


except ImportError:
    log.debug('privex.helpers __init__ failed to import "aioredis", Async Redis dependent helpers will be disabled.')
except Exception as e:
    log.debug('privex.helpers __init__ failed to import "aioredis", (unknown exception), '
              'Async Redis dependent helpers will be disabled. Exception: %s %s', type(e), str(e))

try:
    import aiomcache
    HAS_ASYNC_MEMCACHED = True

    async def connect_memcached_async(**rd_config) -> aiomcache.Client:
        from privex.helpers.common import extract_settings
        cf = extract_settings('MEMCACHED_', settings, merge_conf=dict(rd_config))
        # if 'loop' not in cf:
        #     cf['loop'] = asyncio.get_event_loop()
        return aiomcache.Client(**cf)


    async def get_memcached_async(new_connection=False, thread_id=None, **rd_config) -> aiomcache.Client:
        """Get an Async Memcached connection object. Create one if it doesn't exist."""
        from privex.helpers.common import empty_if, extract_settings
    
        if new_connection: return await connect_memcached_async(**rd_config)
        rd: Optional[aiomcache.Client] = _get_threadstore('aiomemcached', thread_id=thread_id)
    
        if rd is None:
            rd: aiomcache.Client = _set_threadstore('aiomemcached', await connect_memcached_async(**rd_config), thread_id=thread_id)
        return rd


    async def close_memcached_async(thread_id=None, close_all=False) -> bool:
        """
        Close the global Async Memcached connection and delete the instance.

        :param thread_id: Close and delete the Memcached instance for this thread ID, instead of the detected current thread
        :param bool close_all: Close all AsyncIO Memcached instances for every thread ID, then purge their thread store keys.
        :return bool deleted: ``True`` if an instance was found and deleted. ``False`` if there was no existing Memcached instance.
        """
        if close_all:
            for t_id, rd in _get_all_threadstore('aiomemcached'):
                if rd is None:
                    continue
                log.debug("Closing aiomemcached for thread ID %s", t_id)
                try:
                    await rd.close()
                except Exception:
                    log.exception("Exception while closing aiomemcached for thread ID %s", t_id)
            return clean_threadstore(name='aiomemcached', clean_all=True)
        
        rd: Union[str, aiomcache.Client] = _get_threadstore('aiomemcached', 'NOT_FOUND', thread_id=thread_id)
        if rd != 'NOT_FOUND':
            await rd.close()
            clean_threadstore(thread_id=thread_id, name='aiomemcached')
            return True
        return False


    async def reset_memcached_async(thread_id=None) -> aiomcache.Client:
        """Close the global Async Memcached connection, delete the instance, then re-instantiate it"""
        await close_memcached_async(thread_id=thread_id)
        return await _set_threadstore('aiomemcached', get_memcached_async(True, thread_id), thread_id=thread_id)


    async def configure_memcached_async(host=settings.MEMCACHED_HOST, port: int = settings.MEMCACHED_PORT, **kwargs):
        """Update global Memcached settings and re-instantiate the global Async Redis instance with the new settings."""
        thread_id = kwargs.get('thread_id', None)
        settings.MEMCACHED_PORT = port
        settings.MEMCACHED_HOST = host
        return await reset_memcached_async(thread_id=thread_id)


    __all__ += ['get_memcached_async', 'reset_memcached_async', 'configure_memcached_async', 'close_memcached_async', 'connect_memcached_async']

except ImportError:
    log.debug('%s failed to import "aiomcache", Async Memcached dependent helpers will be disabled.', __name__)
except Exception as e:
    log.debug('%s failed to import "aiomcache", (unknown exception), Async Memcached dependent helpers '
              'will be disabled. Exception: %s %s', __name__, type(e), str(e))

try:
    import pylibmc
    
    HAS_MEMCACHED = True
    
    
    def connect_memcached(**rd_config) -> pylibmc.Client:
        from privex.helpers.common import extract_settings
        cf = extract_settings('MEMCACHED_', settings, merge_conf=dict(rd_config))
        # If MEMCACHED_HOST isn't a list/tuple/set, then we need to make it into one, since pylibmc expects a LIST of servers.
        # It also doesn't have an argument for a port, so we combine that with the host.
        host, port = cf.pop('host', 'localhost'), cf.pop('port', 11211)
        if isinstance(host, (list, tuple, set)):
            fhost = host
        else:
            fhost = [f"{host}:{port}" if port != 11211 else host]
        return pylibmc.Client(fhost,  **cf)
    
    
    def get_memcached(new_connection=False, thread_id=None, **rd_config) -> pylibmc.Client:
        """Get a synchronous Memcached connection object. Create one if it doesn't exist."""
        from privex.helpers.common import empty_if, extract_settings
        
        if new_connection: return connect_memcached(**rd_config)
        rd: Optional[pylibmc.Client] = _get_threadstore('memcached', thread_id=thread_id)
        
        if rd is None:
            rd: pylibmc.Client = _set_threadstore('memcached', connect_memcached(**rd_config), thread_id=thread_id)
        return rd
    
    
    def close_memcached(thread_id=None, close_all=False) -> bool:
        """
        Close the global synchronous Memcached connection and delete the instance.

        :param thread_id: Close and delete the Memcached instance for this thread ID, instead of the detected current thread
        :param bool close_all: Close all synchronous Memcached instances for every thread ID, then purge their thread store keys.
        :return bool deleted: ``True`` if an instance was found and deleted. ``False`` if there was no existing Memcached instance.
        """
        if close_all:
            for t_id, rd in _get_all_threadstore('memcached'):
                if rd is None:
                    continue
                log.debug("Closing memcached for thread ID %s", t_id)
                rd: pylibmc.Client
                try:
                    rd.disconnect_all()
                except Exception:
                    log.exception("Exception while closing memcached for thread ID %s", t_id)
            return clean_threadstore(name='memcached', clean_all=True)
        
        rd: Union[str, pylibmc.Client] = _get_threadstore('memcached', 'NOT_FOUND', thread_id=thread_id)
        if rd != 'NOT_FOUND':
            rd.disconnect_all()
            clean_threadstore(thread_id=thread_id, name='memcached')
            return True
        return False
    
    
    def reset_memcached(thread_id=None) -> pylibmc.Client:
        """Close the global synchronous Memcached connection, delete the instance, then re-instantiate it"""
        close_memcached(thread_id=thread_id)
        return _set_threadstore('memcached', get_memcached(True, thread_id), thread_id=thread_id)
    
    
    def configure_memcached(host=settings.MEMCACHED_HOST, port: int = settings.MEMCACHED_PORT, **kwargs) -> pylibmc.Client:
        """Update global Memcached settings and re-instantiate the global Memcached instance with the new settings."""
        thread_id = kwargs.get('thread_id', None)
        settings.MEMCACHED_PORT = port
        settings.MEMCACHED_HOST = host
        return reset_memcached(thread_id=thread_id)
    
    
    __all__ += ['get_memcached', 'reset_memcached', 'configure_memcached', 'close_memcached',
                'connect_memcached']

except ImportError:
    log.debug('%s failed to import "pylibmc", Synchronous Memcached dependent helpers will be disabled.', __name__)
except Exception as e:
    log.debug('%s failed to import "pylibmc", (unknown exception), Synchronous Memcached dependent helpers '
              'will be disabled. Exception: %s %s', __name__, type(e), str(e))

try:
    import geoip2
    import geoip2.database

    def connect_geoip(*args, **geo_config) -> geoip2.database.Reader:
        return geoip2.database.Reader(*args, **geo_config)

    def get_geodbs() -> DictObject:
        return DictObject({
            'city':    DictObject(
                name=settings.GEOCITY_NAME, path=settings.GEOCITY, detected=settings.GEOCITY_DETECTED
            ),
            'country': DictObject(
                name=settings.GEOCOUNTRY_NAME, path=settings.GEOCOUNTRY, detected=settings.GEOCOUNTRY_DETECTED
            ),
            'asn': DictObject(
                name=settings.GEOASN_NAME, path=settings.GEOASN, detected=settings.GEOASN_DETECTED
            ),
        })

    def _find_geoip(geo_type: str) -> Optional[str]:
        _geo_dbs = get_geodbs()

        if geo_type not in _geo_dbs:
            raise AttributeError("_find_geoip: geo_type must be 'city', 'asn' or 'country'")
        log.debug("Locating GeoIP %s - _geo_dbs = %s", geo_type.capitalize(), _geo_dbs)
        for p in settings.search_geoip:
            g_p = path.join(p, _geo_dbs[geo_type].name)
            log.debug("Checking if %s exists...", g_p)
            if path.exists(g_p):
                log.debug("Found GeoIP %s (%s) in path: %s", geo_type, _geo_dbs[geo_type], g_p)
                return g_p
        log.warning("Failed to find GeoIP %s in search paths %s", geo_type.capitalize(), settings.search_geoip)
        return None
        

    def get_geoip_db(geo_type: str) -> str:
        """
        Return the full path to the GeoIP2 database for ``geo_type``.
        
        If we haven't yet scanned the search paths for the database, then :func:`._find_geoip` will be called
        to try and locate the database file.
        
        If the database is found, the ``_DETECTED`` boolean setting will be changed to ``True`` so we know that the
        path contained in the :func:`.get_geodbs` result is valid in the future, avoiding unnecessary searches.
        
        If the database can't be found anywhere within the search paths, :class:`.GeoIPDatabaseNotFound` will be raised.
        
        :param str geo_type: The GeoIP database type: either 'city', 'asn' or 'country'
        :raises GeoIPDatabaseNotFound: If the database for ``geo_type`` could not be found.
        :return str path: The full path to the detected GeoIP database
        """
        _geo_dbs = get_geodbs()
    
        if geo_type not in _geo_dbs:
            raise AttributeError("get_geoip_db: geo_type must be 'city', 'asn' or 'country'")
        gdb = _geo_dbs[geo_type]
        if gdb.detected:
            return gdb.path
        
        gp = _find_geoip(geo_type)
        if not gp:
            log.error("Failed to locate GeoIP ASN + City in alternative search folders.")
            log.error(f" [!!!] ERROR - Missing GeoIP files. The following files do not exist:\n")
            log.error(f"\t{gdb.path}")
            log.error(f"\nCurrent environment settings for GeoIP location:\n")
    
            log.error(f"GEOIP_DIR={settings.GEOIP_DIR}")
            log.error(f"GEOASN_NAME={settings.GEOASN_NAME}")
            log.error(f"GEOCITY_NAME={settings.GEOCITY_NAME}\n")
            log.error(f"GEOCOUNTRY_NAME={settings.GEOCOUNTRY_NAME}\n")
    
            log.error("Please download the GeoLite2 City and ASN GeoIP databases (Maxmind Binary Database format) "
                      "for FREE from the following URL:\n")
            log.error("\thttps://dev.maxmind.com/geoip/geoip2/geolite2/\n")
            log.error("It's recommended to place the .mmdb files in the default folder '/usr/share/GeoIP/' - "
                      "as most applications which use Maxmind GeoIP2 will use that folder by default.\n")
            log.error("You can alternatively place the .mmdb files into any of these folders:\n")
            for p in settings.search_geoip:
                log.error("\t - %s", p)
            log.error("")
            log.error("For most functionality, you'll need both GeoIP2 City + GeoIP2 ASN. The GeoIP2 City database generally provides "
                      "everything in the Country database, plus City data - making the Country database generally redundant.\n")
            raise GeoIPDatabaseNotFound(f"Failed to locate GeoIP {geo_type.capitalize()} ({gdb.name})")
        
        if geo_type == 'city':
            settings.GEOCITY, settings.GEOCITY_DETECTED = gp, True
        if geo_type == 'country':
            settings.GEOCOUNTRY, settings.GEOCOUNTRY_DETECTED = gp, True
        if geo_type == 'asn':
            settings.GEOASN, settings.GEOASN_DETECTED = gp, True
        
        return gp
        

    def get_geoip(geo_type: str, new_connection=False, thread_id=None, **geo_config) -> geoip2.database.Reader:
        """Get a GeoIP Reader object. Create one if it doesn't exist."""
        from privex.helpers.common import empty_if, extract_settings
        
        gdb = get_geoip_db(geo_type)
        _geo_dbs = get_geodbs()
        
        if geo_type not in _geo_dbs:
            raise AttributeError("get_geoip: geo_type must be 'city', 'asn' or 'country'")
        
        if new_connection:
            return connect_geoip(gdb, **geo_config)

        tsname = f'geoip_{geo_type}'
        geo = _get_threadstore(tsname, thread_id=thread_id)
    
        if geo is None:
            geo = connect_geoip(gdb, **geo_config)
            _set_threadstore(tsname, geo, thread_id=thread_id)
        return geo


    def close_geoip(geo_type: str, thread_id=None, close_all=False) -> bool:
        """
        Close the global GeoIP connection and delete the instance.
        
        :param str geo_type: The GeoIP database type: either 'city', 'asn' or 'country'
        :param thread_id: Close and delete the Redis instance for this thread ID, instead of the detected current thread
        :param bool close_all: Close all GeoIP ``geo_type`` instances for every thread ID, then purge their thread store keys.
        :return bool deleted: ``True`` if an instance was found and deleted. ``False`` if there was no existing Redis instance.
        """
        tsname = f'geoip_{geo_type}'

        if close_all:
            for t_id, geo in _get_all_threadstore(tsname):
                if geo is None:
                    continue
                log.debug("Closing %s for thread ID %s", tsname, t_id)
                try:
                    geo.close()
                except Exception:
                    log.exception("Exception while closing %s for thread ID %s", tsname, t_id)
            return clean_threadstore(name=tsname, clean_all=True)
        
        geo: Union[str, geoip2.database.Reader] = _get_threadstore(tsname, 'NOT_FOUND', thread_id=thread_id)
        if geo != 'NOT_FOUND':
            geo.close()
            clean_threadstore(thread_id=thread_id, name=tsname)
            return True
        return False


    def reset_geoip(geo_type: str, thread_id=None) -> geoip2.database.Reader:
        """Close the global GeoIP connection, delete the instance, then re-instantiate it"""
        close_geoip(geo_type, thread_id=thread_id)
        return get_geoip(geo_type, thread_id=thread_id)


    __all__ += ['get_geoip', 'get_geoip_db', 'get_geodbs', 'reset_geoip', 'close_geoip', 'connect_geoip']
    HAS_GEOIP = True
except ImportError:
    log.debug('%s failed to import "geoip2", GeoIP2 dependent helpers will be disabled.', __name__)





