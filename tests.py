#!/usr/bin/env python3.7
"""
This file contains test cases for Privex's Python Helper's (privex-helpers).

Before running the tests:

    - Ensure you have any mandatory requirements installed (see setup.py's install_requires)
    - You may wish to install any optional requirements listed in README.md for best results
    - Python 3.7 is recommended at the time of writing this. See README.md in-case this has changed.

To run the tests, simply execute ``./tests.py`` in your shell::

    user@the-matrix ~/privex-helpers $ ./tests.py
    ............................
    ----------------------------------------------------------------------
    Ran 28 tests in 0.001s

    OK

If for some reason you don't have the executable ``python3.7`` in your PATH, try running by hand with ``python3`` ::

    user@the-matrix ~/privex-helpers $ python3 tests.py
    ............................
    ----------------------------------------------------------------------
    Ran 28 tests in 0.001s

    OK

For more verbosity, simply add ``-v`` to the end of the command::

    user@the-matrix ~/privex-helpers $ ./tests.py -v
    test_empty_combined (__main__.TestBoolHelpers) ... ok
    test_isfalse_truthy (__main__.TestBoolHelpers) ... ok
    test_v4_arpa_boundary_16bit (__main__.TestIPReverseDNS)
    Test generating 16-bit v4 boundary ... ok
    test_v4_arpa_boundary_24bit (__main__.TestIPReverseDNS)
    Test generating 24-bit v4 boundary ... ok
    test_kval_single (__main__.TestParseHelpers)
    Test that a single value still returns a list ... ok
    test_kval_spaced (__main__.TestParseHelpers)
    Test key:val csv parsing with excess outer whitespace, and value whitespace ... ok
    # Truncated excess output in this PyDoc example, as there are many more lines showing 
    # the results of each individual testcase, wasting space and adding bloat...
    ----------------------------------------------------------------------
    Ran 28 tests in 0.001s

    OK

You can also use the ``pytest`` tool (used by default for our Travis CI)::

    user@host: ~/privex-helpers $ pip3 install pytest
    # You can add `-v` for more detailed output, just like when running tests.py directly.
    user@host: ~/privex-helpers $ pytest tests.py

    ===================================== test session starts =====================================
    platform darwin -- Python 3.7.0, pytest-5.0.1, py-1.8.0, pluggy-0.12.0
    rootdir: /home/user/privex-helpers
    collected 33 items                                                                            

    tests.py .................................                                              [100%]

    ====================================== warnings summary =======================================
    /Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/jinja2/utils.py:485
    /Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/jinja2/utils.py:485: 
    DeprecationWarning: Using or importing the ABCs from 'collections' instead of from 'collections.abc' 
    is deprecated, and in 3.8 it will stop working
        from collections import MutableMapping
    ============================ 33 passed, 2 warnings in 0.17 seconds ============================


**Copyright**::

    Copyright 2019         Privex Inc.   ( https://www.privex.io )
    License: X11 / MIT     Github: https://github.com/Privex/python-helpers


"""
import unittest
import logging
import os
from time import sleep

from privex import helpers
from privex.loghelper import LogHelper
from privex.helpers import ping, ip_to_rdns, BoundaryException, plugin, r_cache, random_str, CacheAdapter, env_bool

if env_bool('DEBUG', False) is True:
    LogHelper('privex.helpers', level=logging.DEBUG).add_console_handler(logging.DEBUG)
else:
    LogHelper('privex.helpers', level=logging.CRITICAL)  # Silence non-critical log messages


class EmptyIter(object):
    """A mock iterable object with zero length for testing empty()"""
    def __len__(self):
        return 0


class PrivexBaseCase(unittest.TestCase):
    """
    Base test-case for module test cases to inherit.

    Contains useful class attributes such as ``falsey`` and ``empty_vals`` that are used
    across different unit tests.
    """

    falsey = ['false', 'FALSE', False, 0, '0', 'no']
    """Normal False-y values, as various types"""

    falsey_empty = falsey + [None, '', 'null']
    """False-y values, plus 'empty' values like '' and None"""

    truthy = [True, 'TRUE', 'true', 'yes', 'y', '1', 1]
    """Truthful values, as various types"""

    empty_vals = [None, '']
    empty_lst = empty_vals + [[], (), set(), {}, EmptyIter()]
    empty_zero = empty_vals + [0, '0']


class TestParseHelpers(PrivexBaseCase):
    """Test the parsing functions parse_csv and parse_keyval"""

    def test_csv_spaced(self):
        """Test csv parsing with excess outer whitespace, and value whitespace"""
        c = helpers.parse_csv('  valid  , spaced out,   csv  ')
        self.assertListEqual(c, ['valid', 'spaced out', 'csv'])
    
    def test_csv_single(self):
        """Test that a single value still returns a list"""
        self.assertListEqual(helpers.parse_csv('single'), ['single'])
    
    def test_kval_clean(self):
        """Test that a clean key:val csv is parsed correctly"""
        self.assertListEqual(
            helpers.parse_keyval('John:Doe,Jane:Smith'), 
            [('John', 'Doe'), ('Jane', 'Smith')]
        )
    
    def test_kval_spaced(self):
        """Test key:val csv parsing with excess outer whitespace, and value whitespace"""
        self.assertListEqual(
            helpers.parse_keyval(' John  : Doe  , Jane :  Smith '), 
            [('John', 'Doe'), ('Jane', 'Smith')]
        )
    
    def test_kval_single(self):
        """Test that a single value still returns a list"""
        self.assertListEqual(
            helpers.parse_keyval('John:Doe'), 
            [('John', 'Doe')]
        )
    
    def test_kval_custom_clean(self):
        """
        Test that a clean key:val csv with custom split characters is parsed correctly
        (pipe for kv, semi-colon for pair separation)
        """
        self.assertListEqual(
            helpers.parse_keyval('John|Doe;Jane|Smith', valsplit='|', csvsplit=';'), 
            [('John', 'Doe'), ('Jane', 'Smith')]
        )
    
    def test_kval_custom_spaced(self):
        """Test key:val csv parsing with excess outer/value whitespace, and custom split characters."""
        self.assertListEqual(
            helpers.parse_keyval('  John  |   Doe ;  Jane  |Smith  ', valsplit='|', csvsplit=';'), 
            [('John', 'Doe'), ('Jane', 'Smith')]
        )

    def test_env_nonexist_bool(self):
        """Test env_bool returns default with non-existant env var"""
        k = 'EXAMPLE_NOEXIST'
        if k in os.environ: del os.environ[k]   # Ensure the env var we're testing definitely does not exist.
        self.assertIsNone(helpers.env_bool(k))
        self.assertEqual(helpers.env_bool(k, 'error'), 'error')
    
    def test_env_bool_true(self):
        """Test env_bool returns True boolean with valid env var"""
        k = 'EXAMPLE_EXIST'
        for v in self.truthy:
            os.environ[k] = str(v)
            self.assertTrue(helpers.env_bool(k, 'fail'), msg=f'env_bool({v}) === True')
    
    def test_env_bool_false(self):
        """Test env_bool returns False boolean with valid env var"""
        k = 'EXAMPLE_EXIST'
        for v in self.falsey:
            os.environ[k] = str(v)
            self.assertFalse(helpers.env_bool(k, 'fail'), msg=f'env_bool({v}) === False')


class TestBoolHelpers(PrivexBaseCase):
    """Test the boolean check functions is_true, is_false, as well as empty()"""

    def test_isfalse_falsey(self):
        for f in self.falsey_empty:
            self.assertTrue(helpers.is_false(f), msg=f"is_false({repr(f)}")
    
    def test_isfalse_truthy(self):
        for f in self.truthy:
            self.assertFalse(helpers.is_false(f), msg=f"!is_false({repr(f)}")
    
    def test_istrue_truthy(self):
        for f in self.truthy:
            self.assertTrue(helpers.is_true(f), msg=f"is_true({repr(f)}")

    def test_istrue_falsey(self):
        for f in self.falsey_empty:
            self.assertFalse(helpers.is_true(f), msg=f"!is_true({repr(f)}")
    
    def test_empty_vals(self):
        for f in self.empty_vals:
            self.assertTrue(helpers.empty(f), msg=f"empty({repr(f)})")

    def test_empty_lst(self):
        for f in self.empty_lst:
            self.assertTrue(helpers.empty(f, itr=True), msg=f"empty({repr(f)})")
    
    def test_empty_zero(self):
        for f in self.empty_zero:
            self.assertTrue(helpers.empty(f, zero=True), msg=f"empty({repr(f)})")

    def test_empty_combined(self):
        for f in self.empty_zero + self.empty_lst:
            self.assertTrue(helpers.empty(f, zero=True, itr=True), msg=f"empty({repr(f)})")
    
    def test_notempty(self):
        # Basic string test
        self.assertFalse(helpers.empty('hello'))
        # Integer test
        self.assertFalse(helpers.empty(1, zero=True))
        # Iterable tests
        self.assertFalse(helpers.empty(['world'], itr=True))
        self.assertFalse(helpers.empty(('world',), itr=True))
        self.assertFalse(helpers.empty({'hello': 'world'}, itr=True))


VALID_V4_1 = '172.131.22.17'
VALID_V4_1_16BOUND = '131.172.in-addr.arpa'
VALID_V4_1_24BOUND = '22.131.172.in-addr.arpa'

VALID_V4_2 = '127.0.0.1'
VALID_V4_2_RDNS = '1.0.0.127.in-addr.arpa'

VALID_V6_1 = '2001:dead:beef::1'
VALID_V6_1_RDNS = '1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.f.e.e.b.d.a.e.d.1.0.0.2.ip6.arpa'
VALID_V6_1_16BOUND = '1.0.0.2.ip6.arpa'
VALID_V6_1_32BOUND = 'd.a.e.d.1.0.0.2.ip6.arpa'


class TestIPReverseDNS(PrivexBaseCase):
    """
    Unit testing for the reverse DNS functions in :py:mod:`privex.helpers.net`

    Covers: 
     - positive resolution tests (generate standard rDNS domain from clean input)
     - positive boundary tests (confirm valid results with range of boundaries)
     - negative address tests (ensure errors thrown for invalid v4/v6 addresses)
     - negative boundary tests (ensure errors thrown for invalid v4/v6 rDNS boundaries)
    
    """

    ####
    # Positive tests (normal resolution)
    ####

    def test_v4_to_arpa(self):
        """Test generating rDNS for standard v4"""
        rdns = ip_to_rdns(VALID_V4_2)
        self.assertEqual(rdns, VALID_V4_2_RDNS)

    def test_v6_to_arpa(self):
        """Test generating rDNS for standard v6"""
        rdns = ip_to_rdns(VALID_V6_1)
        self.assertEqual(rdns, VALID_V6_1_RDNS)

    ####
    # Positive tests (boundaries)
    ####

    def test_v4_arpa_boundary_24bit(self):
        """Test generating 24-bit v4 boundary"""
        rdns = ip_to_rdns(VALID_V4_1, boundary=True, v4_boundary=24)
        self.assertEqual(rdns, VALID_V4_1_24BOUND)

    def test_v4_arpa_boundary_16bit(self):
        """Test generating 16-bit v4 boundary"""
        rdns = ip_to_rdns(VALID_V4_1, boundary=True, v4_boundary=16)
        self.assertEqual(rdns, VALID_V4_1_16BOUND)

    def test_v6_arpa_boundary_16bit(self):
        """Test generating 16-bit v6 boundary"""
        rdns = ip_to_rdns(VALID_V6_1, boundary=True, v6_boundary=16)
        self.assertEqual(rdns, VALID_V6_1_16BOUND)

    def test_v6_arpa_boundary_32bit(self):
        """Test generating 32-bit v6 boundary"""
        rdns = ip_to_rdns(VALID_V6_1, boundary=True, v6_boundary=32)
        self.assertEqual(rdns, VALID_V6_1_32BOUND)

    ####
    # Negative tests (invalid addresses)
    ####
    def test_v4_invalid(self):
        """Raise if IPv4 address has < 4 octets"""
        with self.assertRaises(ValueError):
            ip_to_rdns('127.0.0')

    def test_v4_invalid_2(self):
        """Raise if IPv4 address has octet out of range"""
        with self.assertRaises(ValueError):
            ip_to_rdns('127.0.0.373')

    def test_v6_invalid(self):
        """Raise if IPv6 address has invalid block formatting"""
        with self.assertRaises(ValueError):
            ip_to_rdns('2001::ff::a')

    def test_v6_invalid_2(self):
        """Raise if v6 address has invalid chars"""
        with self.assertRaises(ValueError):
            ip_to_rdns('2001::fh')

    ####
    # Negative tests (invalid boundaries)
    ####

    def test_v4_inv_boundary(self):
        """Raise if IPv4 boundary isn't divisable by 8"""
        with self.assertRaises(BoundaryException):
            ip_to_rdns(VALID_V4_2, boundary=True, v4_boundary=7)

    def test_v4_inv_boundary_2(self):
        """Raise if IPv4 boundary is too short"""
        with self.assertRaises(BoundaryException):
            ip_to_rdns(VALID_V4_2, boundary=True, v4_boundary=0)

    def test_v6_inv_boundary(self):
        """Raise if IPv6 boundary isn't dividable by 4"""
        with self.assertRaises(BoundaryException):
            ip_to_rdns(VALID_V6_1, boundary=True, v6_boundary=9)

    def test_v6_inv_boundary_2(self):
        """Raise if IPv6 boundary is too short"""
        with self.assertRaises(BoundaryException):
            ip_to_rdns(VALID_V6_1, boundary=True, v6_boundary=0)


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
            print('The package "redis" is not installed, skipping Redis dependent tests (%s).' % (cls.__name__,))
            return cls.tearDownClass()
        helpers.cache.adapter_set(helpers.RedisCache())


class TestGeneral(PrivexBaseCase):
    """General test cases that don't fit under a specific category"""
    
    def setUp(self):
        self.tries = 0
    
    def test_ping(self):
        """Test success & failure cases for ping function, as well as input validation"""
        with self.assertRaises(ValueError):
            ping('127.0.0.1', -1)
        with self.assertRaises(ValueError):
            ping('127.0.0.1', 0)
        with self.assertRaises(ValueError):
            ping('notavalidip', 1)
        self.assertTrue(ping('127.0.0.1', 3))
        self.assertFalse(ping('192.0.2.0', 3))

    def test_chunked(self):
        """Create a 20 element long list, split it into 4 chunks, and verify the chunks are correctly made"""
        x = list(range(0, 20))
        c = list(helpers.chunked(x, 4))
        self.assertEqual(len(c), 4)
        self.assertEqual(c[0], [0, 1, 2, 3, 4])
        self.assertEqual(c[1], [5, 6, 7, 8, 9])

    async def _tst_async(self, a, b):
        """Basic async function used for testing async code"""
        return a * 2, b * 3

    def test_run_sync(self):
        """Test helpers.async.run_sync by running an async function from this synchronous test"""
        x, y = helpers.run_sync(self._tst_async, 5, 10)
        d, e = helpers.run_sync(self._tst_async, 1, 2)
        self.assertEqual(x, 10)
        self.assertEqual(y, 30)
        self.assertEqual(d, 2)
        self.assertEqual(e, 6)

    @helpers.async_sync
    def test_async_decorator(self):
        """Test the async_sync decorator by wrapping this unit test"""

        x, y = yield from self._tst_async(5, 10)
        d, e = yield from self._tst_async(1, 2)

        self.assertEqual(x, 10)
        self.assertEqual(y, 30)
        self.assertEqual(d, 2)
        self.assertEqual(e, 6)

    def test_async_decorator_return(self):
        """Test the async_sync decorator handles returning async data from synchronous function"""

        async_func = self._tst_async

        @helpers.async_sync
        def non_async(a, b):
            f, g = yield from async_func(a, b)
            return f, g

        x, y = non_async(5, 10)
        d, e = non_async(1, 2)

        self.assertEqual(x, 10)
        self.assertEqual(y, 30)
        self.assertEqual(d, 2)
        self.assertEqual(e, 6)
    
    def test_retry_on_err(self):
        """Test that the :class:`helpers.retry_on_err` decorator retries a function 3 times as expected"""
        
        @helpers.retry_on_err(max_retries=3, delay=0.2)
        def retry_func(cls):
            cls.tries += 1
            raise Exception
        
        with self.assertRaises(Exception):
            retry_func(self)
        
        # The first run should cause tries = 1, then after 3 re-tries it should reach 4 tries in total.
        self.assertEqual(self.tries, 4)

    def test_retry_on_err_return(self):
        """Test that the :class:`helpers.retry_on_err` decorator can return correctly after some retries"""
    
        @helpers.retry_on_err(max_retries=3, delay=0.2)
        def retry_func(cls):
            if cls.tries < 3:
                cls.tries += 1
                raise Exception
            return 'success'
        
        ret = retry_func(self)
    
        # retry_func stops raising exceptions after the 2nd retry (try 3), thus 3 tries in total
        self.assertEqual(self.tries, 3)
        self.assertEqual(ret, 'success')


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
        cls.cache = helpers.cache
    
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
            print('The package "redis" is not installed, skipping Redis dependent tests (%s).' % (cls.__name__,))
            return cls.tearDownClass()
        helpers.cache.adapter_set(helpers.RedisCache())
        cls.cache = helpers.cache


if __name__ == '__main__':
    unittest.main()

"""
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
