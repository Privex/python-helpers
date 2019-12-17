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
from typing import Any, Union, Optional

from privex.helpers import settings
from privex.helpers.types import T
from privex.helpers.common import empty_if

log = logging.getLogger(__name__)

__all__ = [
    'HAS_REDIS', 'HAS_ASYNC_REDIS', 'HAS_DNSPYTHON', 'HAS_CRYPTO', 'HAS_SETUPPY_BUMP',
    'HAS_SETUPPY_COMMANDS', 'HAS_SETUPPY_COMMON'
]

HAS_REDIS = False
"""If the ``redis`` module was imported successfully, this will change to True."""

HAS_ASYNC_REDIS = False
"""If the ``aioredis`` module was imported successfully, this will change to True."""

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


def _set_threadstore(name, obj: T, thread_id=None) -> T:
    thread_store = _get_threadstore(thread_id=thread_id)
    thread_store[name] = obj
    return obj


def clean_threadstore(thread_id=None, name=None):
    """
    Remove the per-thread instance storage in :attr:`.__STORE`, usually called when a thread is exiting.

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
    

    :param thread_id: The ID of the thread (usually from :func:`threading.get_ident`) to clean the storage for.
                      If left as None, will use the ID returned by :func:`threading.get_ident`.
    
    :param name:      If specified, then only the key ``name`` will be deleted from the thread store, instead of the entire thread store.
    """
    thread_id = empty_if(thread_id, threading.get_ident())
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
    
    def close_redis(thread_id=None) -> bool:
        """
        Close the global Redis connection and delete the instance.
        
        :param thread_id: Close and delete the Redis instance for this thread ID, instead of the detected current thread
        :return bool deleted: ``True`` if an instance was found and deleted. ``False`` if there was no existing Redis instance.
        """
        
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

    async def close_redis_async(thread_id=None) -> bool:
        """
        Close the global Async Redis connection and delete the instance.

        :param thread_id: Close and delete the Redis instance for this thread ID, instead of the detected current thread
        :return bool deleted: ``True`` if an instance was found and deleted. ``False`` if there was no existing Redis instance.
        """
    
        rd: Union[str, aioredis.connection] = _get_threadstore('aioredis', 'NOT_FOUND', thread_id=thread_id)
        if rd != 'NOT_FOUND':
            rd.close()
            await rd.wait_close()
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


    def close_memcached_async(thread_id=None) -> bool:
        """
        Close the global Async Memcached connection and delete the instance.

        :param thread_id: Close and delete the Memcached instance for this thread ID, instead of the detected current thread
        :return bool deleted: ``True`` if an instance was found and deleted. ``False`` if there was no existing Memcached instance.
        """
    
        rd: Union[str, aiomcache.Client] = _get_threadstore('aiomemcached', 'NOT_FOUND', thread_id=thread_id)
        if rd != 'NOT_FOUND':
            rd.close()
            clean_threadstore(thread_id=thread_id, name='aiomemcached')
            return True
        return False


    async def reset_memcached_async(thread_id=None) -> aiomcache.Client:
        """Close the global Async Memcached connection, delete the instance, then re-instantiate it"""
        close_memcached_async(thread_id=thread_id)
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

