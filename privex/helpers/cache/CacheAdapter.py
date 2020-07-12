import asyncio
from abc import ABC, abstractmethod
from typing import Any, Optional, Union, Coroutine, Awaitable

from privex.helpers.asyncx import await_if_needed
from privex.helpers.common import empty_if

from privex.helpers.exceptions import CacheNotFound
from privex.helpers.settings import DEFAULT_CACHE_TIMEOUT
from privex.helpers.types import VAL_FUNC_CORO


class CacheAdapter(ABC):
    """
    **CacheAdapter** is an abstract base class which scaffolds methods for implementing a Cache, allowing for
    consistent methods and method signatures across all child classes which implement it.
    
    This class cannot be instantiated by itself, only child classes which extend :class:`.CacheAdapter` and implement
    all methods marked with ``@abstractmethod`` can be instantiated.
    
    For an example implementation of CacheAdapter, see :class:`privex.helpers.cache.MemoryCache`
    
    """

    adapter_enter_reconnect: bool = True
    """
    Controls whether :meth:`.__enter__` automatically calls :meth:`.reconnect` to clear and re-create any previous
    connections/instances for the adapter.
    """
    adapter_exit_close: bool = True
    """
    Controls whether :meth:`.__exit__` automatically calls :meth:`.close` to close any connections/instances and destroy
    library class instances from the current adapter instance.
    """

    ins_enter_reconnect: bool
    """
    Per-instance version of :attr:`.adapter_enter_reconnect`, which is set via ``enter_reconnect`` the constructor.
    When ``__init__`` ``enter_reconnect`` is empty, it inherits the class attribute  value from :attr:`.adapter_enter_reconnect`
    """
    ins_exit_close: bool
    """
    Per-instance version of :attr:`.adapter_exit_close`, which is set via ``exit_close`` the constructor.
    When ``__init__`` ``exit_close`` is empty, it inherits the class attribute  value from :attr:`.adapter_exit_close`
    """
    
    def __init__(self, *args, enter_reconnect: Optional[bool] = None, exit_close: Optional[bool] = None, **kwargs):
        self.ins_enter_reconnect = empty_if(enter_reconnect, self.adapter_enter_reconnect)
        self.ins_exit_close = empty_if(exit_close, self.adapter_exit_close)
    
    @abstractmethod
    def get(self, key: str, default: Any = None, fail: bool = False) -> Any:
        """
        Return the value of cache key ``key``. If the key wasn't found, or it was expired, then ``default`` will be
        returned.
        
        Optionally, you may choose to pass ``fail=True``, which will cause this method to raise :class:`.CacheNotFound`
        instead of returning ``default`` when a key is non-existent / expired.
        
        :param str key: The cache key (as a string) to get the value for, e.g. ``example:test``
        :param Any default: If the cache key ``key`` isn't found / is expired, return this value (Default: ``None``)
        :param bool fail: If set to ``True``, will raise :class:`.CacheNotFound` instead of returning ``default``
                          when a key is non-existent / expired.
        
        :raises CacheNotFound: Raised when ``fail=True`` and ``key`` was not found in cache / expired.
        
        :return Any value: The value of the cache key ``key``, or ``default`` if it wasn't found.
        """
        raise NotImplemented(f'{self.__class__.__name__} must implement .get()')

    @abstractmethod
    def set(self, key: str, value: Any, timeout: Optional[int] = DEFAULT_CACHE_TIMEOUT):
        """
        Set the cache key ``key`` to the value ``value``, and automatically expire the key after ``timeout`` seconds
        from now.
        
        If ``timeout`` is ``None``, then the key will never expire (unless the cache implementation loses it's
        persistence, e.g. memory caches with no disk writes).
        
        :param str key: The cache key (as a string) to set the value for, e.g. ``example:test``
        :param Any value: The value to store in the cache key ``key``
        :param int timeout: The amount of seconds to keep the data in cache. Pass ``None`` to disable expiration.
        """
        raise NotImplemented(f'{self.__class__.__name__} must implement .set()')

    @abstractmethod
    def remove(self, *key: str) -> bool:
        """
        Remove one or more keys from the cache.
        
        If all cache keys existed before removal, ``True`` will be returned. If some didn't exist (and thus couldn't
        remove), then ``False`` will be returned.
        
        :param str key: The cache key(s) to remove
        :return bool removed: ``True`` if ``key`` existed and was removed
        :return bool removed: ``False`` if ``key`` didn't exist, and no action was taken.
        """
        raise NotImplemented(f'{self.__class__.__name__} must implement .remove()')

    @abstractmethod
    def update_timeout(self, key: str, timeout: int = DEFAULT_CACHE_TIMEOUT) -> Any:
        """
        Update the timeout for a given ``key`` to ``datetime.utcnow() + timedelta(seconds=timeout)``
        
        This method should accept keys which are already expired, allowing expired cache keys to have their timeout
        extended **after** expiry.
        
        **Example**::
        
            >>> c = CacheAdapter()
            >>> c.set('example', 'test', timeout=60)
            >>> sleep(70)
            >>> c.update_timeout('example', timeout=60)   # Reset the timeout for ``'example'`` to ``now + 60 seconds``
            >>> c.get('example')
            'test'
        
        :param str key: The cache key to update the timeout for
        :param int timeout: Reset the timeout to this many seconds from ``datetime.utcnow()``
        :raises CacheNotFound: Raised when ``key`` was not found in cache (thus cannot extend timeout)
        :return Any value: The value of the cache key
        """
        raise NotImplemented(f'{self.__class__.__name__} must implement .extend_timeout()')

    def get_or_set(self, key: str, value: Union[Any, callable], timeout: int = DEFAULT_CACHE_TIMEOUT) -> Any:
        """
        Attempt to return the value of ``key`` in the cache. If ``key`` doesn't exist or is expired, then it will be
        set to ``value``, and ``value`` will be returned.

        The ``value`` parameter can be any standard type such as ``str`` or ``dict`` - or it can be a callable
        function / method which returns the value to set and return.

        **Basic Usage**::

            >>> c = CacheAdapter()
            >>> c.get('testing')
            None
            >>> c.get_or_set('testing', 'hello world')
            'hello world'
            >>> c.get('testing')
            'hello world'

        **Set and get the value from a function if ``key`` didn't exist / was expired**::

            >>> def my_func(key): return "hello {} world".format(key)
            >>> c = CacheAdapter()
            >>> c.get_or_set('example', my_func)
            'hello example world'
            >>> c.get('example')
            'hello example world'

        :param str key: The cache key (as a string) to get/set the value for, e.g. ``example:test``
        :param Any value: The value to store in the cache key ``key``. Can be a standard type, or a callable function.
        :param int timeout: The amount of seconds to keep the data in cache. Pass ``None`` to disable expiration.
        :return Any value: The value of the cache key ``key``, or ``value`` if it wasn't found.
        """
        key, timeout = str(key), int(timeout)
        try:
            k = self.get(key, fail=True)
        except CacheNotFound:
            k = value(key) if callable(value) else value
            self.set(key=key, value=k, timeout=timeout)
        return k

    async def get_or_set_async(self, key: str, value: VAL_FUNC_CORO, timeout: int = DEFAULT_CACHE_TIMEOUT) -> Any:
        """
        Async coroutine compatible version of :meth:`.get_or_set`.
        
        **Example with Async function**::
        
            >>> async def my_coro(key): return f"hello {key} world"
            >>> c = CacheAdapter()
            >>> await c.get_or_set_async('coro_example', my_coro)
            'hello example world'
            >>> c.get('coro_example')
            'hello example world'
        
        **Also works with non-async functions**::
            
            >>> def my_func(key): return f"hello {key} world"
            >>> await c.get_or_set_async('func_example', my_func)
            'hello example world'
            >>> c.get('func_example')
            'hello example world'
        
        :param str key: The cache key (as a string) to get/set the value for, e.g. ``example:test``
        :param Any value: The value to store in the cache key ``key``. Can be a standard type, a coroutine / awaitable,
                          or a plain callable function.
        :param int timeout: The amount of seconds to keep the data in cache. Pass ``None`` to disable expiration.
        :return Any value: The value of the cache key ``key``, or ``value`` if it wasn't found.
        """
        key, timeout = str(key), int(timeout)
        try:
            k = self.get(key, fail=True)
        except CacheNotFound:
            k = value
            if asyncio.iscoroutinefunction(value):
                k = await value(key)
            if asyncio.iscoroutine(value):
                k = await value
            elif callable(value):
                k = value(key)
            self.set(key=key, value=k, timeout=timeout)
        return k

    def close(self, *args, **kwargs) -> Any:
        """
        Close any cache library connections, and destroy their local class instances by setting them to ``None``.
        """
        return f"close() is not implemented by {self.__class__.__name__}"

    def connect(self, *args, **kwargs) -> Any:
        """
        Create an instance of the library used to interact with the caching system, ensure it's connection is open,
        and store the instance on this class instance - only if not already connected.

        Should return the class instance which was created.
        """
        return f"close() is not implemented by {self.__class__.__name__}"

    def reconnect(self, *args, **kwargs) -> Any:
        """
        Calls :meth:`.close` to close any previous connections and cleanup instances, then re-create the
        connection(s)/instance(s) by calling :meth:`.connect`
        """
        self.close()
        return self.connect()

    def __getitem__(self, item):
        try:
            return self.get(key=item, fail=True)
        except CacheNotFound:
            raise KeyError(f'Key "{item}" not found in cache.')

    def __setitem__(self, key, value):
        return self.set(key=key, value=value)
    
    async def __aenter__(self):
        """
        Before starting a context manager, we close and cleanup any previous connection and re-create a fresh connection
        and instance, ensuring no conflicts such as connections/instances attached to other AsyncIO event loops :)
        """
        if self.ins_enter_reconnect:
            await await_if_needed(self.reconnect())
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Once a context manager is finished, we close and cleanup any instances / connections, ensuring no conflicts
        for code that might want to use the cache adapter in a different event loops.
        """
        if self.ins_exit_close:
            await await_if_needed(self.reconnect())
        return None
    
    def __enter__(self):
        """
        Before starting a context manager, we close and cleanup any previous connection and re-create a fresh connection
        and instance, ensuring no conflicts such as connections/instances attached to other threads :)
        """
        if self.ins_enter_reconnect:
            self.reconnect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Once a context manager is finished, we close and cleanup any instances / connections, ensuring no conflicts
        for code that might want to use the cache adapter in a different threads / event loops.
        """
        if self.ins_exit_close:
            self.close()
        return None

