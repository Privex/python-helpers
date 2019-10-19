"""
Test cases for parsing functions, such as :py:func:`.parse_csv`, :py:func:`.env_keyval` etc.

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
import os

from privex import helpers
from tests.base import PrivexBaseCase


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

