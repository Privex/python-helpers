"""
This module contains test cases for Privex's Python Helper's (privex-helpers).


Testing pre-requisites
----------------------

    - Ensure you have any mandatory requirements installed (see setup.py's install_requires)
    - You should install ``pytest`` to run the tests, it works much better than standard python unittest.
    - You may wish to install any optional requirements listed in README.md for best results
    - Python 3.7 is recommended at the time of writing this. See README.md in-case this has changed.

For the best testing experience, it's recommended to install the ``dev`` extra, which includes every optional
dependency, as well as development requirements such as ``pytest`` , ``coverage`` as well as requirements for
building the documentation.


Running via PyTest
------------------

To run the tests, we strongly recommend using the ``pytest`` tool (used by default for our Travis CI)::

    # Install PyTest if you don't already have it.
    user@host: ~/privex-helpers $ pip3 install pytest
    
    # We recommend adding the option ``-rxXs`` which will show information about why certain tests were skipped
    # as well as info on xpass / xfail tests
    # You can add `-v` for more detailed output, just like when running the tests directly.
    user@host: ~/privex-helpers $ pytest -rxXs
    
    # NOTE: If you're using a virtualenv, sometimes you may encounter strange conflicts between a global install
    # of PyTest, and the virtualenv PyTest, resulting in errors related to packages not being installed.
    # A simple workaround is just to call pytest as a module from the python3 executable:
    
    user@host: ~/privex-helpers $ python3 -m pytest -rxXs

    ============================== test session starts ==============================
    platform darwin -- Python 3.7.0, pytest-5.2.2, py-1.8.0, pluggy-0.13.0
    rootdir: /home/user/privex-helpers
    collected 99 items
    
    tests/test_bool.py .........                                              [  9%]
    tests/test_cache.py ................                                      [ 25%]
    tests/test_crypto.py .........................                            [ 50%]
    tests/test_general.py ...................                                 [ 69%]
    tests/test_net.py ssss.s                                                  [ 75%]
    tests/test_parse.py ..........                                            [ 85%]
    tests/test_rdns.py ..............                                         [100%]
    
    ============================ short test summary info ============================
    SKIPPED [1] tests/test_net.py:76: Requires package 'dnspython'
    SKIPPED [1] tests/test_net.py:83: Requires package 'dnspython'
    SKIPPED [1] tests/test_net.py:66: Requires package 'dnspython'
    SKIPPED [1] tests/test_net.py:71: Requires package 'dnspython'
    SKIPPED [1] /home/user/privex-helpers/tests/test_net.py:56: Skipping test TestGeneral.test_ping_v6 as platform is
    not supported: "privex.helpers.net.ping is not fully supported on platform 'Darwin'..."
    ================== 94 passed, 5 skipped, 1 warnings in 21.66s ===================


Running individual test modules
-------------------------------

Some test modules such as ``test_cache`` can be quite slow, as sometimes it's required to call sleep, e.g. ``sleep(2)``
either to prevent interference from previous/following tests, or when testing that an expiration/timeout works.

Thankfully, PyTest allows you to run individual test modules like this::
    
    user@host: ~/privex-helpers $ pytest -rxXs -v tests/test_parse.py
    
    ============================== test session starts ==============================
    platform darwin -- Python 3.7.0, pytest-5.2.2, py-1.8.0, pluggy-0.13.0
    cachedir: .pytest_cache
    rootdir: /home/user/privex-helpers
    plugins: cov-2.8.1
    collected 10 items
    
    tests/test_parse.py::TestParseHelpers::test_csv_single PASSED             [ 10%]
    tests/test_parse.py::TestParseHelpers::test_csv_spaced PASSED             [ 20%]
    tests/test_parse.py::TestParseHelpers::test_env_bool_false PASSED         [ 30%]
    tests/test_parse.py::TestParseHelpers::test_env_bool_true PASSED          [ 40%]
    tests/test_parse.py::TestParseHelpers::test_env_nonexist_bool PASSED      [ 50%]
    tests/test_parse.py::TestParseHelpers::test_kval_clean PASSED             [ 60%]
    tests/test_parse.py::TestParseHelpers::test_kval_custom_clean PASSED      [ 70%]
    tests/test_parse.py::TestParseHelpers::test_kval_custom_spaced PASSED     [ 80%]
    tests/test_parse.py::TestParseHelpers::test_kval_single PASSED            [ 90%]
    tests/test_parse.py::TestParseHelpers::test_kval_spaced PASSED            [100%]
    
    ============================== 10 passed in 0.09s ===============================


Running directly using Python Unittest
--------------------------------------

Alternatively, you can run the tests by hand with ``python3.7`` ( or just ``python3`` ), however we strongly
recommend using PyTest as our tests use various PyTest functionality to allow for things such as skipping tests
when you don't have a certain dependency installed.

Running via python unittest ::

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


if env_bool('DEBUG', False) is True:
    LogHelper('privex.helpers', level=logging.DEBUG).add_console_handler(logging.DEBUG)
else:
    LogHelper('privex.helpers', level=logging.CRITICAL)  # Silence non-critical log messages

if __name__ == '__main__':
    unittest.main()
    from tests.test_cache import *
    from tests.general import *
    from tests.test_crypto import *
    from tests.test_bool import TestBoolHelpers
    from tests.test_rdns import TestIPReverseDNS
    from tests.test_parse import TestParseHelpers
    from tests.test_net import TestNet
    from tests.test_collections import TestIsNamedTuple, TestDictableNamedtuple, TestDictObject
    from tests.test_extras import TestAttrs
