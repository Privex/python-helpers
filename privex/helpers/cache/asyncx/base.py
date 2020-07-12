"""
Core classes/functions used by AsyncIO Cache Adapters, including the base class :class:`.AsyncCacheAdapter`

"""
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Optional

from privex.helpers.common import empty_if
from privex.helpers.exceptions import CacheNotFound

from privex.helpers.cache.CacheAdapter import CacheAdapter
from privex.helpers.settings import DEFAULT_CACHE_TIMEOUT
from privex.helpers.types import VAL_FUNC_CORO


class AsyncCacheAdapter(CacheAdapter, ABC):
    """
    **AsyncCacheAdapter** is an abstract base class based on :class:`.CacheAdapter`, but with all methods designated as coroutines.
    
    Cache adapters which make use of AsyncIO, including via asyncio compatible libraries (e.g. ``aioredis``), should use this class
    as their parent instead of :class:`.CacheAdapter`.
    
    To retain the functionality of :meth:`.__getitem__` and :meth:`.__setitem__`, it obtains an event loop
    using :func:`asyncio.get_event_loop`, and then wraps :meth:`.get` or :meth:`.set` respectively using
    ``loop.run_until_complete`` to be able to run them within the synchronous get/setitem magic methods.
    
    It overrides :meth:`.get_or_set` to convert it into an async method, and overrides :meth:`.get_or_set_async` so that
    :meth:`.get` and :meth:`.set` are correctly awaited within the method.
    
    """
    adapter_enter_reconnect: bool = True
    """
    Controls whether :meth:`.__aenter__` automatically calls :meth:`.reconnect` to clear and re-create any previous
    connections/instances for the adapter.
    """
    adapter_exit_close: bool = True
    """
    Controls whether :meth:`.__aexit__` automatically calls :meth:`.close` to close any connections/instances and destroy
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
        super().__init__(*args, **kwargs)
    
    async def get_or_set(self, key: str, value: VAL_FUNC_CORO, timeout: int = DEFAULT_CACHE_TIMEOUT) -> Any:
        return await self.get_or_set_async(key=key, value=value, timeout=timeout)

    async def get_or_set_async(self, key: str, value: VAL_FUNC_CORO, timeout: int = DEFAULT_CACHE_TIMEOUT) -> Any:
        key, timeout = str(key), int(timeout)
        try:
            k = await self.get(key, fail=True)
        except CacheNotFound:
            k = value
            
            if asyncio.iscoroutinefunction(value):
                k = await value(key)
            if asyncio.iscoroutine(value):
                k = await value
            elif callable(value):
                k = value(key)
            await self.set(key=key, value=k, timeout=timeout)
        return k
    
    @abstractmethod
    async def get(self, key: str, default: Any = None, fail: bool = False) -> Any:
        raise NotImplemented(f'{self.__class__.__name__} must implement .get()')

    @abstractmethod
    async def set(self, key: str, value: Any, timeout: Optional[int] = DEFAULT_CACHE_TIMEOUT):
        raise NotImplemented(f'{self.__class__.__name__} must implement .set()')

    @abstractmethod
    async def remove(self, *key: str) -> bool:
        raise NotImplemented(f'{self.__class__.__name__} must implement .remove()')

    @abstractmethod
    async def update_timeout(self, key: str, timeout: int = DEFAULT_CACHE_TIMEOUT) -> Any:
        raise NotImplemented(f'{self.__class__.__name__} must implement .extend_timeout()')

    async def close(self, *args, **kwargs) -> Any:
        """
        Close any cache library connections, and destroy their local class instances by setting them to ``None``.
        """
        return f"close() is not implemented by {self.__class__.__name__}"

    async def connect(self, *args, **kwargs) -> Any:
        """
        Create an instance of the library used to interact with the caching system, ensure it's connection is open,
        and store the instance on this class instance - only if not already connected.
        
        Should return the class instance which was created.
        """
        return f"close() is not implemented by {self.__class__.__name__}"

    async def reconnect(self, *args, **kwargs) -> Any:
        """
        Calls :meth:`.close` to close any previous connections and cleanup instances, then re-create the
        connection(s)/instance(s) by calling :meth:`.connect`
        """
        await self.close()
        return await self.connect()

    def __getitem__(self, item):
        loop = asyncio.get_event_loop()
        try:
            return loop.run_until_complete(self.get(key=item, fail=True))
        except CacheNotFound:
            raise KeyError(f'Key "{item}" not found in cache.')
    
    def __setitem__(self, key, value):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.set(key=key, value=value))
    
    # async def __aenter__(self):
    #     """
    #     Before starting a context manager, we close and cleanup any previous connection and re-create a fresh connection
    #     and instance, ensuring no conflicts such as connections/instances attached to other AsyncIO event loops :)
    #     """
    #     if self.ins_enter_reconnect:
    #         await self.reconnect()
    #     return self
    #
    # async def __aexit__(self, exc_type, exc_val, exc_tb):
    #     """
    #     Once a context manager is finished, we close and cleanup any instances / connections, ensuring no conflicts
    #     for code that might want to use the cache adapter in a different event loops.
    #     """
    #     if self.ins_exit_close:
    #         await self.close()

    def __enter__(self):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.__aenter__())

    def __exit__(self, exc_type, exc_val, exc_tb):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.__aexit__(exc_type, exc_val, exc_tb))

