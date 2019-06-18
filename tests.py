#!/usr/bin/env python3.7
import unittest
import logging
from collections import namedtuple
from privex import helpers
from privex.loghelper import LogHelper


class TestParseHelpers(unittest.TestCase):
    """Test the parsing functions csv_parse and keyval_parse"""

    def test_csv_spaced(self):
        """Test csv parsing with excess outer whitespace, and value whitespace"""
        c = helpers.csv_parse('  valid  , spaced out,   csv  ')
        self.assertListEqual(c, ['valid', 'spaced out', 'csv'])
    
    def test_csv_single(self):
        """Test that a single value still returns a list"""
        self.assertListEqual(helpers.csv_parse('single'), ['single'])
    
    def test_kval_clean(self):
        """Test that a clean key:val csv is parsed correctly"""
        self.assertListEqual(
            helpers.keyval_parse('John:Doe,Jane:Smith'), 
            [('John', 'Doe'), ('Jane', 'Smith')]
        )
    
    def test_kval_spaced(self):
        """Test key:val csv parsing with excess outer whitespace, and value whitespace"""
        self.assertListEqual(
            helpers.keyval_parse(' John  : Doe  , Jane :  Smith '), 
            [('John', 'Doe'), ('Jane', 'Smith')]
        )
    
    def test_kval_single(self):
        """Test that a single value still returns a list"""
        self.assertListEqual(
            helpers.keyval_parse('John:Doe'), 
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