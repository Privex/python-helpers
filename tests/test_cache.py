"""
Test cases for the cache decorator :py:func:`.r_cache` plus cache layers :class:`.RedisCache` and :class:`.MemoryCache`

**Copyright**::

        +===================================================+
        |                 © 2019 Privex Inc.                |
        |               https://www.privex.io               |
        +===================================================+
        |                                                   |
        |        Originally Developed by Privex Inc.        |
        |                                                   |
        |        Core Developer(s):                         |
        |                                                   |
        |          (+)  Chris (@someguy123) [Privex]        |
        |          (+)  Kale (@kryogenic) [Privex]          |
        |                                                   |
        +===================================================+

    Copyright 2019     Privex Inc.   ( https://www.privex.io )

    Permission is hereby granted, free of charge, to any person obtaining a copy of
    this software and associated documentation files (the "Software"), to deal in
    the Software without restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
    Software, and to permit persons to whom the Software is furnished to do so,
    subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
    INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
    PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
    OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
    SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


"""
import time
import warnings
from time import sleep
from typing import Any, Callable, Union

from privex import helpers
from privex.helpers import r_cache, random_str, plugin, CacheAdapter

from privex.helpers.plugin import HAS_MEMCACHED

from privex.helpers.common import empty_if
from tests.base import PrivexBaseCase
from privex.helpers.collections import Mocker

try:
    from privex.helpers.cache.extras import CacheManagerMixin, z_cache
    HAS_CACHE_EXTRA = True
except Exception as e:
    HAS_CACHE_EXTRA = False
    warnings.warn(f'WARNING: Could not import CacheManagerMixin and/or z_cache from privex.helpers.cache.extra - '
                  f'possibly missing required packages? Error is: {type(e)} - {str(e)}')
    CacheManagerMixin, z_cache = Mocker.make_mock_class('CacheManagerMixin'), Mocker.make_mock_class('z_cache')

try:
    import pytest
    
    HAS_PYTEST = True
except ImportError:
    warnings.warn('WARNING: Could not import pytest. You should run "pip3 install pytest" to ensure tests work best')
    from privex.helpers.mockers import pytest
    HAS_PYTEST = False

HAS_REDIS = plugin.HAS_REDIS

try:
    from privex.helpers.cache import SqliteCache

    HAS_SQLITE_CACHE = True
except ImportError:
    warnings.warn('WARNING: Could not import SqliteCache. You may need to run "pip3 install -U privex-db aiosqlite" to be able to '
                  'run the SQLite3 cache tests...')
    SqliteCache = Mocker.make_mock_class('SqliteCache')
    HAS_SQLITE_CACHE = False

import logging

log = logging.getLogger(__name__)


class TestCacheDecoratorMemory(PrivexBaseCase):
    """
    Test that the decorator :py:func:`privex.helpers.decorators.r_cache` caches correctly, with adapter
    :class:`privex.helpers.cache.MemoryCache.MemoryCache` and also verifies dynamic cache key generation
    works as expected.
    """

    cache = helpers.cache.cached
    
    @classmethod
    def setUpClass(cls):
        helpers.cache.adapter_set(helpers.MemoryCache())

    def test_rcache_rand(self):
        """Decorate random string function with r_cache - test that two calls return the same string"""
        @r_cache('pxhelpers_test_rand')
        def r_test():
            return random_str()

        val1 = r_test()
        val2 = r_test()
        self.assertEqual(val1, val2, msg=f"'{repr(val1)}' == '{repr(val2)}'")

    def test_rcache_rand_dynamic(self):
        """Decorate random string function with r_cache and use format_args for dynamic cache string testing"""

        @r_cache('pxhelpers_rand_dyn:{}:{}', format_args=[0, 1, 'x', 'y'])
        def r_test(x, y):
            return random_str()

        a, b, c, d = r_test(1, 1), r_test(1, 2), r_test(x=1, y=2), r_test(y=2, x=1)
        e, f, g, h = r_test(1, 1), r_test(1, 2), r_test(x=1, y=2), r_test(y=2, x=1)

        # Test random cached strings using 1,1 and 1,2 as positional args
        self.assertEqual(a, e, msg="r_test(1,1) == r_test(1,1)")
        self.assertEqual(b, f, msg="r_test(1,2) == r_test(1,2)")
        # Test positional arg cache is equivalent to kwarg cache
        self.assertEqual(b, c, msg="r_test(1,2) == r_test(y=1,x=2)")
        self.assertEqual(b, g, msg="r_test(1,2) == r_test(x=1,y=2)")
        self.assertEqual(b, d, msg="r_test(1,2) == r_test(y=2,x=1)")
        # Test kwarg cache is equivalent to inverted kwarg cache
        self.assertEqual(h, c, msg="r_test(y=2, x=1) == r_test(x=1, y=2)")
        # To be sure they aren't all producing the same string, make sure that 1,2 and 1,1
        # (positional and kwarg) are not equal
        self.assertNotEqual(a, b, msg="r_test(1,1) != r_test(1,2)")
        self.assertNotEqual(g, a, msg="r_test(x=1, y=2) != r_test(1,1)")

    def test_rcache_callable(self):
        """Decorate random string function - use a lambda callable to determine a cache key"""
        @r_cache(lambda x, y: f"{x}")
        def r_test(x, y):
            return random_str()

        a, b = r_test(1, 1), r_test(1, 1)
        c, d = r_test(2, 1), r_test(1, 2)

        # If the first argument is the same, then we'll get the same result. The second argument is ignored.
        self.assertEqual(a, b, msg='r_test(1,1) == r_test(1,1)')
        self.assertEqual(a, d, msg='r_test(1,1) == r_test(1,2)')
        # If the first argument is different (1 and 2), then we should get a different result.
        self.assertNotEqual(a, c, msg='r_test(1,1) != r_test(2,1)')

    def tearDown(self):
        """Remove any Redis keys used during test, to avoid failure on re-run"""
        self.cache.remove('pxhelpers_test_rand', 'pxhelpers_rand_dyn:1:1', 'pxhelpers_rand_dyn:1:2',
                          'pxhelpers_rand_dyn:2:1')
        super(TestCacheDecoratorMemory, self).tearDown()


@pytest.mark.skipif(not HAS_REDIS, reason="TestCacheDecoratorRedis requires package 'redis'")
class TestCacheDecoratorRedis(TestCacheDecoratorMemory):
    """
    Test decorator :py:func:`privex.helpers.decorators.r_cache` with adapter
    :class:`privex.helpers.cache.RedisCache.RedisCache`
    
    (See :class:`.TestCacheDecoratorMemory`)
    """
    
    @classmethod
    def setUpClass(cls):
        if not plugin.HAS_REDIS:
            warnings.warn(f'The package "redis" is not installed, skipping Redis dependent tests ({cls.__name__}).')
            return cls.tearDownClass()
        helpers.cache.adapter_set(helpers.RedisCache())


class TestMemoryCache(PrivexBaseCase):
    """:class:`.MemoryCache` Test cases for caching related functions/classes in :py:mod:`privex.helpers.cache`"""
    
    cache_keys = [
        'test_cache_set',
        'test_expire',
        'test_update_timeout',
        'test_update_timeout_noexist',
        'test_cache_remove',
    ]
    """A list of all cache keys used during the test case, so they can be removed by :py:meth:`.tearDown` once done."""
    
    cache: CacheAdapter
    
    @classmethod
    def setUpClass(cls):
        """Set the current cache adapter to an instance of MemoryCache() and make it available through ``self.cache``"""
        helpers.cache.adapter_set(helpers.MemoryCache())
        cls.cache = helpers.cached
    
    @classmethod
    def tearDownClass(cls):
        for k in cls.cache_keys:
            cls.cache.remove(k)
            sleep(0.1)   # A small sleep to give cache backends time to fully remove each item.
    
    def test_cache_set(self):
        """Test basic cache.set and cache.get"""
        key, c = self.cache_keys[0], self.cache
        self.assertIs(c.get(key), None)

        c.set(key=key, value='TestingValue')
        self.assertEqual(c.get(key), 'TestingValue')

    def test_cache_expire(self):
        """Test that cache keys are removed after the specified timeout"""
        key, c = self.cache_keys[1], self.cache
        self.assertIs(c.get(key), None)
        
        c.set(key, 'ExpiryTest', timeout=2)
        self.assertEqual(c.get(key), 'ExpiryTest')
        sleep(3)
        self.assertEqual(c.get(key), None)
    
    def test_cache_update_timeout(self):
        """Test that cache.update_timeout extends timeouts correctly"""
        key, c = self.cache_keys[2], self.cache
        c.set(key, 'UpdateExpiryTest', timeout=3)
        self.assertEqual(c.get(key), 'UpdateExpiryTest')
        sleep(1.5)
        c.update_timeout(key, timeout=10)
        sleep(2.5)
        self.assertEqual(c.get(key), 'UpdateExpiryTest')
    
    def test_cache_update_timeout_raise(self):
        """Test that cache.update_timeout raises :class:`.CacheNotFound` if the key does not exist"""
        key, c = self.cache_keys[3], self.cache
        with self.assertRaises(helpers.CacheNotFound):
            c.update_timeout(key, timeout=10)

    def test_cache_remove(self):
        """Test that cache.remove correctly removes cache keys"""
        key, c = self.cache_keys[4], self.cache
        c.set(key, 'RemoveTest', timeout=30)
        self.assertEqual(c.get(key), 'RemoveTest')
        c.remove(key)
        self.assertIs(c.get(key), None)


@pytest.mark.skipif(not HAS_REDIS, reason="TestRedisCache requires package 'redis'")
class TestRedisCache(TestMemoryCache):
    """
    :class:`.RedisCache` Test cases for caching related functions/classes in :py:mod:`privex.helpers.cache`
    
    This is **simply a child class** for :class:`.TestMemoryCache` - but with an overridden :class:`.setUpClass`
    to ensure the cache adapter is set to :class:`.RedisCache` for this re-run.
    """
    
    cache_keys: list
    """A list of all cache keys used during the test case, so they can be removed by :py:meth:`.tearDown` once done."""

    @classmethod
    def setUpClass(cls):
        """Set the current cache adapter to an instance of RedisCache() and make it available through ``self.cache``"""
        if not plugin.HAS_REDIS:
            warnings.warn(f'The package "redis" is not installed, skipping Redis dependent tests ({cls.__name__}).')
            return cls.tearDownClass()
        helpers.cache.adapter_set(helpers.RedisCache())
        cls.cache = helpers.cached


@pytest.mark.skipif(not HAS_MEMCACHED, reason="TestMemcachedCache requires package 'pylibmc'")
class TestMemcachedCache(TestMemoryCache):
    """
    :class:`.MemcachedCache` Test cases for caching related functions/classes in :py:mod:`privex.helpers.cache`

    This is **simply a child class** for :class:`.TestMemoryCache` - but with an overridden :class:`.setUpClass`
    to ensure the cache adapter is set to :class:`.MemcachedCache` for this re-run.
    """
    
    cache_keys: list
    """A list of all cache keys used during the test case, so they can be removed by :py:meth:`.tearDown` once done."""
    
    @classmethod
    def setUpClass(cls):
        """Set the current cache adapter to an instance of RedisCache() and make it available through ``self.cache``"""
        if not plugin.HAS_MEMCACHED:
            warnings.warn(f'The package "pylibmc" is not installed, skipping Memcached dependent tests ({cls.__name__}).')
            return cls.tearDownClass()
        helpers.cache.adapter_set(helpers.MemcachedCache())
        cls.cache = helpers.cached


@pytest.mark.skipif(not HAS_SQLITE_CACHE, reason="TestSqliteCache requires package 'privex-db'")
class TestSqliteCache(TestMemoryCache):
    """
    :class:`.SqliteCache` Test cases for caching related functions/classes in :py:mod:`privex.helpers.cache`

    This is **simply a child class** for :class:`.TestMemoryCache` - but with an overridden :class:`.setUpClass`
    to ensure the cache adapter is set to :class:`.SqliteCache` for this re-run.
    """
    
    cache_keys: list
    """A list of all cache keys used during the test case, so they can be removed by :py:meth:`.tearDown` once done."""
    
    @classmethod
    def setUpClass(cls):
        """Set the current cache adapter to an instance of RedisCache() and make it available through ``self.cache``"""
        if not plugin.HAS_REDIS:
            warnings.warn(f'The package "redis" is not installed, skipping Redis dependent tests ({cls.__name__}).')
            return cls.tearDownClass()
        helpers.cache.adapter_set(SqliteCache('pvx-helpers-tests.sqlite3'))
        cls.cache = helpers.cached


class CacheManagerExample(CacheManagerMixin):
    cache_prefix = 'example'
    default_cache_time = 20
    default_cache_key_time = 15
    
    default_sleep_multiplier = 1
    sleep_multiplier = 0.5

    @classmethod
    @z_cache()
    def testing(cls, hello: str = 'world', banana: str = 'testing'):
        sm = cls.sleep_multiplier
        log.debug(f"Fake sleep {sm} secs ({sm} secs / {sm * 2} secs)...")
        sleep(sm)
        log.debug(f"Fake sleep {sm} secs ({sm * 2} secs / {sm * 2} secs)...")
        sleep(sm)
        return f"Hello! You are: {hello} || Your banana is called: {banana}"

    @classmethod
    @z_cache(cache_key=lambda cls, hello='world', banana='testing': f"lorem:ipsum:{hello}:{banana}")
    def lorem(cls, hello: str = 'world', banana: str = 'testing'):
        sm = cls.sleep_multiplier
        log.debug(f"(lorem) Fake sleep {sm / 2} secs ({sm / 2} secs / {sm} secs)...")
        sleep(sm / 2)
        log.debug(f"(lorem) Fake sleep {sm / 2} secs ({sm} secs / {sm} secs)...")
        sleep(sm / 2)
        return f"(lorem) Hello! You are: {hello} || Your banana is called: {banana}"
    
    @staticmethod
    def set_sleep_time(secs: int = None):
        CacheManagerExample.sleep_multiplier = float(empty_if(secs, CacheManagerExample.default_sleep_multiplier))


XNUM = Union[int, float]
XFUNC = Callable[[Any], Any]


def _lorem_key(hello='world', banana='testing') -> str:
    return f"{CacheManagerExample.cache_prefix}{CacheManagerExample.cache_sep}lorem:ipsum:{hello}:{banana}"


cmst = CacheManagerExample.sleep_multiplier


@pytest.mark.skipif(not HAS_CACHE_EXTRA, reason="TestCacheManager requires privex.helpers.cache.extra to be imported without errors...")
class TestCacheManager(PrivexBaseCase):
    _testing_fmt_str = 'Hello! You are: {} || Your banana is called: {}'
    _lorem_fmt_str = f"(lorem) {_testing_fmt_str}"
    _delta = 0.4
    
    def tearDown(self) -> None:
        CacheManagerExample.clear_all_cache_keys()
    
    def time_trial(self, func: XFUNC, assert_time: XNUM, delta: XNUM, *args, **kwargs):
        t_start = time.time()
        res = func(*args, **kwargs)
        t_end = time.time()
        self.assertAlmostEqual(t_end - t_start, assert_time, delta=delta)
        return res
    
    def _check_testing_method(self, func: XFUNC, assert_time: XNUM, delta: XNUM, *args, **kwargs):
        fmt_str = 'Hello! You are: {} || Your banana is called: {}'
        if str(func.__name__).endswith('lorem'): fmt_str = f"(lorem) {fmt_str}"
        args, kwargs = list(args), dict(kwargs)
        hello = args[0] if len(args) > 0 else kwargs.get('hello', 'world')
        banana = args[1] if len(args) > 1 else kwargs.get('banana', 'testing')
        res = self.time_trial(func, assert_time, delta, *args, **kwargs)
        self.assertEqual(res, fmt_str.format(hello, banana))
        return res

    def test_z_cache_simple(self):
        """Test :func:`.z_cache` by calling a wrapped classmethod twice, and comparing the times"""
        self._check_testing_method(CacheManagerExample.testing, cmst * 2, self._delta)
        self._check_testing_method(CacheManagerExample.testing, 0.2, self._delta)

    def test_z_cache_simple_args(self):
        """
        Test :func:`.z_cache` by calling a wrapped classmethod with different arguments, to confirm argument changes result
        in a different cache key
        """
        self._check_testing_method(CacheManagerExample.testing, cmst * 2, self._delta, 'example')
        self._check_testing_method(CacheManagerExample.testing, 0.2, self._delta, 'example')

        self._check_testing_method(CacheManagerExample.testing, cmst * 2, self._delta, 'example', 'two')
        self._check_testing_method(CacheManagerExample.testing, 0.2, self._delta, 'example', 'two')

        self._check_testing_method(CacheManagerExample.testing, cmst * 2, self._delta, hello='another', banana='example')
        self._check_testing_method(CacheManagerExample.testing, 0.2, self._delta, hello='another', banana='example')

        self._check_testing_method(CacheManagerExample.testing, cmst * 2, self._delta, 'and', banana='another')
        self._check_testing_method(CacheManagerExample.testing, 0.2, self._delta, 'and', banana='another')
        
    def test_z_cache_lambda_key(self):
        """Test :func:`.z_cache` by calling a wrapped classmethod twice (which uses a lambda cache_key), and comparing the times"""
        self._check_testing_method(CacheManagerExample.lorem, cmst, self._delta)
        self._check_testing_method(CacheManagerExample.lorem, 0.2, self._delta)

    def test_z_cache_lambda_key_args(self):
        """
        Test :func:`.z_cache` by calling a wrapped classmethod twice (which uses a lambda cache_key), with a mixture of
        positional and keyword arguments, differing each call, plus comparing the execution times
        """
        self._check_testing_method(CacheManagerExample.lorem, cmst, self._delta, 'example')
        self._check_testing_method(CacheManagerExample.lorem, 0.2, self._delta, 'example')

        self._check_testing_method(CacheManagerExample.lorem, cmst, self._delta, 'example', 'two')
        self._check_testing_method(CacheManagerExample.lorem, 0.2, self._delta, 'example', 'two')

        self._check_testing_method(CacheManagerExample.lorem, cmst, self._delta, hello='another', banana='example')
        self._check_testing_method(CacheManagerExample.lorem, 0.2, self._delta, hello='another', banana='example')

        self._check_testing_method(CacheManagerExample.lorem, cmst, self._delta, 'and', banana='another')
        self._check_testing_method(CacheManagerExample.lorem, 0.2, self._delta, 'and', banana='another')

    def test_z_cache_lambda_check_cache(self):
        """
        Confirms lambda ``cache_key`` arguments are respected when using :func:`.z_cache` - by looking up the custom cache key
        after calling a method.
        
        To be extra sure that the lambda ``cache_key`` used with ``lorem`` is actually being used, this test calls ``lorem`` with some
        arguments twice (to confirm successfully cached), then manually looks up the expected cache key generated by lorem's lambda,
        comparing it's contents against the :attr:`._lorem_fmt_str` format string to ensure the data stored in the cache key
        matches ``lorem``'s expected output.
        """
        # First we call lorem twice - first to prime the cache key, and second to confirm it's cached
        self._check_testing_method(CacheManagerExample.lorem, cmst, self._delta, 'example', 'two')
        self._check_testing_method(CacheManagerExample.lorem, 0.2, self._delta, 'example', 'two')
        # Generate the cache key that lorem() would've used for our previous call
        ck = _lorem_key('example', 'two')
        from privex.helpers.cache import cached
        # Retrieve the cache key and confirm it contains lorem's string, formatted with our parameters
        c_res = cached.get(ck)
        f_str = self._lorem_fmt_str.format('example', 'two')
        self.assertEqual(c_res, f_str, msg=f"(cache key: {ck}) '{c_res}' == '{f_str}'")

    def test_clear_cache_keys(self):
        """Test :meth:`CacheManagerExample.clear_cache_keys` can clear individual cache keys"""
        self._check_testing_method(CacheManagerExample.lorem, cmst, self._delta, 'example')
        ck = _lorem_key('example')
        self.assertIn('Hello! You are: example', CacheManagerExample.cache_get(ck))
        
        self.assertTrue(CacheManagerExample.clear_cache_keys(ck))
        self.assertIsNone(CacheManagerExample.cache_get(ck))

    def test_clear_all_cache_keys(self):
        """Test :meth:`.CacheManagerExample.clear_all_cache_keys` appears to clear all cache keys"""
        # call testing + lorem to ensure 2 cache keys exist
        self._check_testing_method(CacheManagerExample.testing, cmst * 2, self._delta, 'example')
        self._check_testing_method(CacheManagerExample.lorem, cmst, self._delta, 'example')
        # confirm they're cached
        self._check_testing_method(CacheManagerExample.testing, 0.2, self._delta, 'example')
        self._check_testing_method(CacheManagerExample.lorem, 0.2, self._delta, 'example')
        # check get_all_cache_keys confirms there are 2 cached keys
        self.assertEqual(len(CacheManagerExample.get_all_cache_keys()), 2)
        # clear all cache keys
        CacheManagerExample.clear_all_cache_keys()
        # check get_all_cache_keys confirms there are no cache keys after we've cleared them
        self.assertEqual(len(CacheManagerExample.get_all_cache_keys()), 0)
        # run testing + lorem again, and assert that the runtime matches non-cached time.
        self._check_testing_method(CacheManagerExample.testing, cmst * 2, self._delta, 'example')
        self._check_testing_method(CacheManagerExample.lorem, cmst, self._delta, 'example')
