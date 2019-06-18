"""
Common functions and classes that don't fit into a specific category

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
import random
import string
import argparse
import logging
import sys
from typing import Sequence

log = logging.getLogger(__name__)

SAFE_CHARS = 'abcdefhkmnprstwxyz23456789ACDEFGHJKLMNPRSTWXYZ'
"""Characters that shouldn't be mistaken, avoiding users confusing an o with a 0 or an l with a 1 or I"""

ALPHANUM = string.ascii_uppercase + string.digits + string.ascii_lowercase
"""All characters from a-z, A-Z, and 0-9 - for random strings where there's no risk of user font confusion"""

def random_str(size:int = 50, chars: Sequence = SAFE_CHARS) -> str:
    """
    Generate a random string of arbitrary length using a given character set (string / list / tuple). Uses Python's 
    SystemRandom class to provide relatively secure randomness from the OS. (On Linux, uses /dev/urandom)

    By default, uses the character set :py:attr:`.SAFE_CHARS` which contains letters a-z / A-Z and numbers 2-9
    with commonly misread characters removed (such as 1, l, L, 0 and o). Pass :py:attr:`.ALPHANUM` as `chars` if 
    you needthe full set of upper/lowercase + numbers.

    Usage:

        >>> from privex.helpers import random_str
        >>> # Default random string - 50 character alphanum without easily mistaken chars
        >>> password = random_str()
        'MrCWLYMYtT9A7bHc5ZNE4hn7PxHPmsWaT9GpfCkmZASK7ApN8r'
        >>> # Customised random string - 12 characters using only the characters `abcdef12345` 
        >>> custom = random_str(12, chars='abcdef12345')
        'aba4cc14a43d'

    Warning: As this relies on the OS's entropy features, it may not be cryptographically secure on non-Linux platforms:

    > The returned data should be unpredictable enough for cryptographic applications, though its exact quality 
    > depends on the OS implementation.

    :param int size:  Length of random string to generate (default 50 characters)
    :param str chars: Characterset to generate with ( default is :py:attr:`.SAFE_CHARS` - a-z/A-Z/0-9 with 
                      often misread chars removed)

    """
    return ''.join(random.SystemRandom().choice(chars) for _ in range(size))

def empty(v, zero: bool = False, itr: bool = False) -> bool:
    """
    Quickly check if a variable is empty or not. By default only '' and None are checked, use `itr` and `zero` to
    test for empty iterable's and zeroed variables.

    Returns True if a variable is None or '', returns False if variable passes the tests

    Example usage:

        >>> x, y = [], None
        >>> if empty(y):
        ...     print('Var y is None or a blank string')
        ...
        >>> if empty(x, itr=True):
        ...     print('Var x is None, blank string, or an empty dict/list/iterable')

    :param v:    The variable to check if it's empty
    :param zero: if zero=True, then return True if the variable is 0
    :param itr:  if itr=True, then return True if the variable is ``[]``, ``{}``, or is an iterable and has 0 length
    :return bool is_blank: True if a variable is blank (``None``, ``''``, ``0``, ``[]`` etc.)
    :return bool is_blank: False if a variable has content (or couldn't be checked properly)
    """

    _check = [None, '']
    if zero: _check.append(0)
    if v in _check: return True
    if itr:
        if v == [] or v == {}: return True
        if hasattr(v, '__len__') and len(v) == 0: return True

    return False

def is_true(v) -> bool:
    """
    Check if a given bool/str/int value is some form of True:
    boolean: True // string: 'true', 'yes', 'y', '1' // integer: 1
    
    (note: strings are automatically .lower()'d)

    Usage:

    >>> is_true('true')
    True
    >>> is_true('no')
    False

    :param Any v:          The value to check for truthfulness
    :return bool is_true:  True if the value appears to be truthy, otherwise False.
    """
    v = v.lower() if type(v) is str else v
    return v in [True, 'true', 'yes', 'y', '1', 1]

def is_false(v, chk_none: bool = True) -> bool:
    """
    **Warning:** Unless you specifically need to verify a value is Falsey, it's usually safer to 
    check for truth :py:func:`.is_true` and invert the result, i.e. ``if not is_true(v)``
    
    Check if a given bool/str/int value is some form of False::

        boolean: False // string: 'false', 'no', 'n', '0' // integer: 0

    If ``chk_none`` is True (default), will also consider the below values to be Falsey::

        boolean: None // string: 'null', 'none', ''
    
    (note: strings are automatically .lower()'d)

    Usage:

    >>> is_false(0)
    True
    >>> is_false('yes')
    False

    :param Any v:          The value to check for falseyness
    :param bool chk_none:  If True, treat None/'none'/'null' as Falsey (default True)
    :return bool is_False: True if the value appears to be falsey, otherwise False.
    """
    v = v.lower() if type(v) is str else v
    chk = [False, 'false', 'no', 'n', '0', 0]
    chk += [None, 'none', 'null', ''] if chk_none else []
    return v in chk


class ErrHelpParser(argparse.ArgumentParser):
    """
    ErrHelpParser - Use this instead of :py:class:`argparse.ArgumentParser` to automatically get full
    help output as well as the error message when arguments are invalid, instead of just an error message.

    >>> parser = ErrHelpParser(description='My command line app')
    >>> parser.add_argument('nums', metavar='N', type=int, nargs='+')

    """
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)
