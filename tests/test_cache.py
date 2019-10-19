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
import warnings
from time import sleep
from privex import helpers
from privex.helpers import r_cache, random_str, plugin, CacheAdapter
from tests.base import PrivexBaseCase


class TestCacheDecoratorMemory(PrivexBaseCase):
    """
    Test that the decorator :py:func:`privex.helpers.decorators.r_cache` caches correctly, with adapter
    :class:`helpers.MemoryCache` and also verifies dynamic cache key generation works as expected.
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


class TestCacheDecoratorRedis(TestCacheDecoratorMemory):
    """
    Test decorator :py:func:`privex.helpers.decorators.r_cache` with adapter
    :class:`helpers.RedisCache`
    
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
        """Test that cache.update_timeout raises :class:`.helpers.CacheNotFound` if the key does not exist"""
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
