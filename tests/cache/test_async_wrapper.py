import asyncio
from typing import Union

import pytest
import logging

from privex.helpers.exceptions import CacheNotFound
from privex.helpers.plugin import close_redis_async

log = logging.getLogger(__name__)

try:
    from privex.helpers.cache import async_cached, AsyncRedisCache, AsyncMemoryCache, AsyncCacheWrapper
    from privex.helpers.cache import async_adapter_get, async_adapter_set, __STORE
    # r = AsyncRedisCache()
except ImportError:
    pytest.skip(msg="Failed to import async_cached / AsyncRedisCache / AsyncMemoryCache (???)", allow_module_level=True)
    async_cached, AsyncMemoryCache, AsyncRedisCache, AsyncCacheWrapper = object, object, object, object
    async_adapter_get = async_adapter_set = lambda *args, **kwargs: ''
    __STORE = {}
    # r = None


cleanup_keys = set()

CacheTypes = Union[AsyncMemoryCache, AsyncRedisCache, AsyncCacheWrapper]


def _cleanup(key: str):
    global cleanup_keys
    cleanup_keys.add(key)


@pytest.fixture()
async def rcache():
    global cleanup_keys
    # async with AsyncMemcachedCache() as r:
    async with async_cached as ac:
        yield ac
    # _rd = await r.redis
    # _rd.close()
    # await _rd.wait_close()
    # await close_redis_async(close_all=True)
    async_cached.reset_adapter()
    async with async_cached as ac:
        log.info("Removing keys listed in cleanup_keys: %s", cleanup_keys)
        await ac.remove(*cleanup_keys)
    if 'async_adapter' in __STORE:
        del __STORE['async_adapter']
    cleanup_keys = set()


@pytest.mark.asyncio
async def test_adapter_set_get(rcache: CacheTypes):
    async_adapter_set(AsyncRedisCache())
    assert isinstance(async_adapter_get(), AsyncRedisCache)
    
    del __STORE['async_adapter']
    assert isinstance(async_adapter_get(), AsyncMemoryCache)


@pytest.mark.asyncio
async def test_cache_set(rcache: CacheTypes):
    _cleanup('test_cache_set')
    
    await rcache.set('test_cache_set', 'hello world')
    val = await rcache.get('test_cache_set')
    assert val == 'hello world'


@pytest.mark.asyncio
async def test_cache_set_redis(rcache: CacheTypes):
    _cleanup('test_cache_set_redis')

    async_adapter_set(AsyncRedisCache())
    assert isinstance(async_adapter_get(), AsyncRedisCache)
    
    await rcache.set('test_cache_set_redis', 'hello redis world')
    val = await rcache.get('test_cache_set_redis')
    assert val == 'hello redis world'


@pytest.mark.asyncio
async def test_cache_expire(rcache: CacheTypes):
    k, v = 'test_cache_expire', 'testing expire'
    _cleanup(k)
    await rcache.set(k, v, timeout=2)
    assert await rcache.get(k) == v
    
    await asyncio.sleep(3)
    assert await rcache.get(k) is None


@pytest.mark.asyncio
async def test_cache_update_timeout(rcache: CacheTypes):
    """Test that cache.update_timeout extends timeouts correctly"""
    k, v = 'test_cache_update_timeout', 'update expiry test'
    _cleanup(k)
    await rcache.set(k, v, timeout=4)
    
    assert await rcache.get(k) == v
    await asyncio.sleep(1.5)
    
    await rcache.update_timeout(k, timeout=10)
    await asyncio.sleep(3.5)
    assert await rcache.get(k) == v


@pytest.mark.asyncio
async def test_cache_update_timeout_raise(rcache: CacheTypes):
    try:
        await rcache.update_timeout('test_cache_update_timeout_raise', timeout=10)
        assert False
    except CacheNotFound:
        assert True


@pytest.mark.asyncio
async def test_cache_remove(rcache: CacheTypes):
    k, v = 'test_cache_remove', 'test cache removal'
    _cleanup(k)
    await rcache.set(k, v, timeout=30)
    assert await rcache.get(k) == v
    await rcache.remove(k)
    assert await rcache.get(k) is None







