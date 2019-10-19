"""
Test cases for boolean helper functions, such as :py:func:`.is_true`, :py:func:`.is_false`, and :py:func:`.empty`

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
from privex import helpers
from tests.base import PrivexBaseCase


class TestBoolHelpers(PrivexBaseCase):
    """Test the boolean check functions is_true, is_false, as well as empty()"""

    def test_isfalse_falsey(self):
        """Test :py:func:`.is_false` with falsey values"""
        for f in self.falsey_empty:
            self.assertTrue(helpers.is_false(f), msg=f"is_false({repr(f)}")
    
    def test_isfalse_truthy(self):
        """Test :py:func:`.is_false` with truthy values"""
        for f in self.truthy:
            self.assertFalse(helpers.is_false(f), msg=f"!is_false({repr(f)}")
    
    def test_istrue_truthy(self):
        """Test :py:func:`.is_true` with truthy values"""
        for f in self.truthy:
            self.assertTrue(helpers.is_true(f), msg=f"is_true({repr(f)}")

    def test_istrue_falsey(self):
        """Test :py:func:`.is_true` with falsey values"""
        for f in self.falsey_empty:
            self.assertFalse(helpers.is_true(f), msg=f"!is_true({repr(f)}")
    
    def test_empty_vals(self):
        """Test :py:func:`.empty` with empty values"""
        for f in self.empty_vals:
            self.assertTrue(helpers.empty(f), msg=f"empty({repr(f)})")

    def test_empty_lst(self):
        """Test :py:func:`.empty` with empty iterables"""
        for f in self.empty_lst:
            self.assertTrue(helpers.empty(f, itr=True), msg=f"empty({repr(f)})")
    
    def test_empty_zero(self):
        """Test :py:func:`.empty` with different representations of ``0``"""
        for f in self.empty_zero:
            self.assertTrue(helpers.empty(f, zero=True), msg=f"empty({repr(f)})")

    def test_empty_combined(self):
        """Test :py:func:`.empty` with empty iterables AND different representations of ``0``"""
        for f in self.empty_zero + self.empty_lst:
            self.assertTrue(helpers.empty(f, zero=True, itr=True), msg=f"empty({repr(f)})")
    
    def test_notempty(self):
        """Test :py:func:`.empty` with non-empty values"""
        # Basic string test
        self.assertFalse(helpers.empty('hello'))
        # Integer test
        self.assertFalse(helpers.empty(1, zero=True))
        # Iterable tests
        self.assertFalse(helpers.empty(['world'], itr=True))
        self.assertFalse(helpers.empty(('world',), itr=True))
        self.assertFalse(helpers.empty({'hello': 'world'}, itr=True))
