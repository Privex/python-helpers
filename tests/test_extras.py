"""
Test cases for :py:mod:`privex.helpers.extras`

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
import pytest
import logging
from privex.helpers import extras
from tests.base import PrivexBaseCase

log = logging.getLogger(__name__)

# Fallback objects to avoid undeclared variables despite pytest skip
attr, AttribDictable, Example = object, object, object

# We only import `attr` and `AttribDictable` if `attrs` is installed.
# We also create the `Example` class for use in test cases.
if extras.HAS_ATTRS:
    import attr
    from privex.helpers.extras import AttribDictable
    
    @attr.s
    class Example(AttribDictable):
        hello = attr.ib(type=str)
        testing = attr.ib(type=bool, default=True)


@pytest.mark.skipif(extras.HAS_ATTRS is False, reason='extras.HAS_ATTRS is False (is `attrs` installed?)')
class TestAttrs(PrivexBaseCase):
    
    def test_dictable_set_get(self):
        """Test setting and getting attributes on a :class:`.AttribDictable` attrs instance"""
        x = Example(hello='world')
        self.assertEqual(x.hello, 'world')
        self.assertEqual(x['hello'], 'world')
        
        x.hello = 'lorem'
        self.assertEqual(x.hello, 'lorem')
        self.assertEqual(x['hello'], 'lorem')
        
        x['hello'] = 'ipsum'
        self.assertEqual(x.hello, 'ipsum')
        self.assertEqual(x['hello'], 'ipsum')

    def test_dictable_cast_dict(self):
        """Test casting an :class:`.AttribDictable` attrs instance to a dict"""
        x = Example(hello='world')
        d = dict(x)
        self.assertIsInstance(d, dict)
        self.assertEqual(d, dict(hello='world', testing=True))


