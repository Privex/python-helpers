"""
General test cases for various un-categorized functions / classes e.g. :py:func:`.chunked` and :py:func:`.ping`

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
import platform
import warnings

from privex import helpers
from privex.helpers import ping
from tests.base import PrivexBaseCase


class TestGeneral(PrivexBaseCase):
    """General test cases that don't fit under a specific category"""
    
    def setUp(self):
        self.tries = 0
    
    def test_ping(self):
        """Test success & failure cases for ping function with IPv4, as well as input validation"""
        try:
            with self.assertRaises(ValueError):
                ping('127.0.0.1', -1)
            with self.assertRaises(ValueError):
                ping('127.0.0.1', 0)
            with self.assertRaises(ValueError):
                ping('notavalidip', 1)
            self.assertTrue(ping('127.0.0.1', 3))
            self.assertFalse(ping('192.0.2.0', 3))
        except NotImplementedError as e:
            warnings.warn(f"Skipping test TestGeneral.test_ping as platform is not supported: {str(e)}")
            return

    def test_ping_v6(self):
        """Test success & failure cases for ping function with IPv6, as well as input validation"""
        try:
            with self.assertRaises(ValueError):
                ping('::1', -1)
            with self.assertRaises(ValueError):
                ping('::1', 0)
            with self.assertRaises(ValueError):
                ping('notavalidip', 1)
            self.assertTrue(ping('::1', 3))
            self.assertFalse(ping('fd06:dead::beef:ab12', 3))
        except NotImplementedError as e:
            warnings.warn(f"Skipping test TestGeneral.test_ping_v6 as platform is not supported: \"{str(e)}\"")
            return

    def _check_asn(self, asn, expected_name):
        if not helpers.plugin.HAS_DNSPYTHON:
            return warnings.warn(f"Skipping asn_to_name tests as dnspython is not installed...")
        name = helpers.asn_to_name(asn)
        self.assertEqual(name, expected_name, msg=f"asn_to_name({asn}) '{name}' == '{expected_name}'")
        
    def test_asn_to_name_int(self):
        """Test Privex's ASN (as an int) 210083 resolves to 'PRIVEX, SE'"""
        self._check_asn(210083, 'PRIVEX, SE')

    def test_asn_to_name_str(self):
        """Test Cloudflare's ASN (as a str) '13335' resolves to 'CLOUDFLARENET - Cloudflare, Inc., US'"""
        self._check_asn('13335', 'CLOUDFLARENET - Cloudflare, Inc., US')
    
    def test_asn_to_name_erroneous(self):
        """Test asn_to_name returns 'Unknown ASN' when quiet, otherwise throws a KeyError for ASN 'nonexistent'"""
        self.assertEqual(helpers.asn_to_name('nonexistent'), 'Unknown ASN')
        with self.assertRaises(KeyError):
            helpers.asn_to_name('nonexistent', quiet=False)

    def test_asn_to_name_erroneous_2(self):
        """Test asn_to_name returns 'Unknown ASN' when quiet, otherwise throws KeyError for the ASN 999999999"""
        self.assertEqual(helpers.asn_to_name(999999999), 'Unknown ASN')
        with self.assertRaises(KeyError):
            helpers.asn_to_name(999999999, quiet=False)

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
    
    def test_inject_items(self):
        """Test :py:func:`helpers.inject_items` injecting into a list after position 1"""
        a = ['a', 'b', 'g']
        b = ['c', 'd', 'e', 'f']
        # Position 1 is the 2nd element of ``a`` - which is the letter 'b'
        c = helpers.inject_items(b, a, 1)
        self.assertListEqual(c, ['a', 'b', 'c', 'd', 'e', 'f', 'g'])

    def test_inject_items_2(self):
        """Test :py:func:`helpers.inject_items` injecting into a list after position 3"""
        a = ['a', 'b', 'c', 'd', 'h']
        b = ['e', 'f', 'g']
        # Position 3 is the 4th element of ``a`` - which is the letter 'd'
        c = helpers.inject_items(b, a, 3)
        self.assertListEqual(c, ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])

