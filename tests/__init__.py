"""


This module contains test cases for Privex's Python Helper's (privex-helpers).

Testing pre-requisites
----------------------

    - Ensure you have any mandatory requirements installed (see setup.py's install_requires)
    - You may wish to install any optional requirements listed in README.md for best results
    - Python 3.7 is recommended at the time of writing this. See README.md in-case this has changed.

Running via PyTest
------------------

To run the tests, we strongly recommend using the ``pytest`` tool (used by default for our Travis CI)::

    # Install PyTest if you don't already have it.
    user@host: ~/privex-helpers $ pip3 install pytest
    # You can add `-v` for more detailed output, just like when running the tests directly.
    user@host: ~/privex-helpers $ pytest

    ===================================== test session starts =====================================
    platform darwin -- Python 3.7.0, pytest-5.0.1, py-1.8.0, pluggy-0.12.0
    rootdir: /home/user/privex-helpers
    collected 56 items

    tests/test_bool.py .........                                                      [ 16%]
    tests/test_cache.py ................                                              [ 44%]
    tests/test_general.py .......                                                     [ 57%]
    tests/test_parse.py ..........                                                    [ 75%]
    tests/test_rdns.py ..............                                                 [100%]

    ============================ 56 passed, 1 warnings in 0.17 seconds ============================

Running directly using Python Unittest
--------------------------------------

Alternatively, you can run the tests by hand with ``python3.7`` ( or just ``python3`` ) ::

    user@the-matrix ~/privex-helpers $ python3.7 -m tests
    ............................
    ----------------------------------------------------------------------
    Ran 28 tests in 0.001s

    OK

For more verbosity, simply add ``-v`` to the end of the command::

    user@the-matrix ~/privex-helpers $ python3 -m tests -v
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



**Copyright**::

    Copyright 2019         Privex Inc.   ( https://www.privex.io )
    License: X11 / MIT     Github: https://github.com/Privex/python-helpers


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
import logging
import unittest
from privex.loghelper import LogHelper
from privex.helpers import env_bool
from tests.base import PrivexBaseCase, EmptyIter
from tests.test_cache import *
from tests.test_general import *
from tests.test_crypto import *
from tests.test_bool import TestBoolHelpers
from tests.test_rdns import TestIPReverseDNS
from tests.test_parse import TestParseHelpers

if env_bool('DEBUG', False) is True:
    LogHelper('privex.helpers', level=logging.DEBUG).add_console_handler(logging.DEBUG)
else:
    LogHelper('privex.helpers', level=logging.CRITICAL)  # Silence non-critical log messages

if __name__ == '__main__':
    unittest.main()
