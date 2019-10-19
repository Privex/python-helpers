"""
Various classes / functions / attributes used by test cases (no actual test cases in here)

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
import unittest


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