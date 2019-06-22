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


Copyright::

    Copyright 2019         Privex Inc.   ( https://www.privex.io )
    License: X11 / MIT     Github: https://github.com/Privex/python-helpers


"""
import unittest
import logging
from collections import namedtuple
from privex import helpers
from privex.loghelper import LogHelper
from privex.helpers import ip_to_rdns, BoundaryException

class TestParseHelpers(unittest.TestCase):
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

class EmptyIter(object):
    """A mock iterable object with zero length for testing empty()"""
    def __len__(self):
        return 0

class TestBoolHelpers(unittest.TestCase):
    """Test the boolean check functions is_true, is_false, as well as empty()"""

    falsey = ['false', 'FALSE', None, False, '', 0, '0', 'no', 'null']
    truthy = [True, 'TRUE', 'true', 'yes', 'y', '1', 1]
    empty_vals = [None, '']
    empty_lst = empty_vals + [[], (), set(), {}, EmptyIter()]
    empty_zero = empty_vals + [0, '0']

    def test_isfalse_falsey(self):
        for f in self.falsey:
            self.assertTrue(helpers.is_false(f), msg=f"is_false({repr(f)}")
    
    def test_isfalse_truthy(self):
        for f in self.truthy:
            self.assertFalse(helpers.is_false(f), msg=f"!is_false({repr(f)}")
    
    def test_istrue_truthy(self):
        for f in self.truthy:
            self.assertTrue(helpers.is_true(f), msg=f"is_true({repr(f)}")

    def test_istrue_falsey(self):
        for f in self.falsey:
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


class TestIPReverseDNS(unittest.TestCase):
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