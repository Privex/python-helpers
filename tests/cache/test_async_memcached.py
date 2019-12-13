import asyncio
import pytest
import logging

from privex.helpers.exceptions import CacheNotFound

log = logging.getLogger(__name__)

try:
    from privex.helpers.cache.asyncx import AsyncMemcachedCache
    
    # r = AsyncRedisCache()
except ImportError:
    pytest.skip(msg="Failed to import AsyncMemcachedCache (???)", allow_module_level=True)
    AsyncMemcachedCache = object
    # r = None

cleanup_keys = []


def _cleanup(key: str):
    global cleanup_keys
    cleanup_keys += [key]


@pytest.fixture()
async def rcache():
    global cleanup_keys
    async with AsyncMemcachedCache() as r:
        yield r
    # _rd = await r.redis
    # _rd.close()
    # await _rd.wait_close()
    log.info("Removing keys listed in cleanup_keys: %s", cleanup_keys)
    await AsyncMemcachedCache().remove(*cleanup_keys)
    cleanup_keys = []


@pytest.mark.asyncio
async def test_cache_set(rcache: AsyncMemcachedCache):
    _cleanup('test_cache_set')
    
    await rcache.set('test_cache_set', 'hello world')
    val = await rcache.get('test_cache_set')
    assert val == 'hello world'


@pytest.mark.asyncio
async def test_cache_expire(rcache: AsyncMemcachedCache):
    k, v = 'test_cache_expire', 'testing expire'
    _cleanup(k)
    await rcache.set(k, v, timeout=2)
    assert await rcache.get(k) == v
    
    await asyncio.sleep(3)
    assert await rcache.get(k) is None


@pytest.mark.asyncio
async def test_cache_update_timeout(rcache: AsyncMemcachedCache):
    """Test that cache.update_timeout extends timeouts correctly"""
    k, v = 'test_cache_update_timeout', 'update expiry test'
    _cleanup(k)
    await rcache.set(k, v, timeout=3)
    
    assert await rcache.get(k) == v
    await asyncio.sleep(1.5)
    
    await rcache.update_timeout(k, timeout=10)
    await asyncio.sleep(2.5)
    assert await rcache.get(k) == v


@pytest.mark.asyncio
async def test_cache_update_timeout_raise(rcache: AsyncMemcachedCache):
    try:
        await rcache.update_timeout('test_cache_update_timeout_raise', timeout=10)
        assert False
    except CacheNotFound:
        assert True


@pytest.mark.asyncio
async def test_cache_remove(rcache: AsyncMemcachedCache):
    k, v = 'test_cache_remove', 'test cache removal'
    _cleanup(k)
    await rcache.set(k, v, timeout=30)
    assert await rcache.get(k) == v
    await rcache.remove(k)
    assert await rcache.get(k) is None







