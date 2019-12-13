import asyncio
import pytest
import logging

from privex.helpers.decorators import async_retry

log = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_async_retry():
    @async_retry(5, 0.1)
    async def _do_retry(obj):
        obj['tries'] += 1
        
        if obj['tries'] < 4:
            raise Exception
        return "finished"
    
    o = {'tries': 0}
    
    res = await _do_retry(o)
    
    assert res == "finished"
    assert o['tries'] == 4


@pytest.mark.asyncio
async def test_async_retry_fail_on():
    @async_retry(5, 0.1, fail_on=[ConnectionError])
    async def _do_retry(obj):
        obj['tries'] += 1
        
        if obj['tries'] < 3:
            raise Exception
        
        raise ConnectionError

    o = {'tries': 0}
    try:
        await _do_retry(o)
        assert False
    except ConnectionError:
        assert o['tries'] == 3


@pytest.mark.asyncio
async def test_async_retry_ignore():
    @async_retry(3, 0.1, ignore=[IOError])
    async def _do_retry(obj):
        obj['tries'] += 1
        
        if obj['tries'] < 3:
            raise IOError
        
        raise ConnectionError
    
    o = {'tries': 0}
    try:
        await _do_retry(o)
        assert False
    except ConnectionError:
        assert o['tries'] == 6

