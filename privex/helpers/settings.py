"""
Configuration options for helpers, and services they depend on, such as Redis.

To override settings from your app::

    >>> from privex.helpers import settings
    >>> settings.REDIS_HOST = 'redis.example.org'
    >>> settings.REDIS_PORT = 1234


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
from os.path import dirname, abspath, join

BASE_DIR = dirname(dirname(dirname(abspath(__file__))))
"""The root folder of this project (i.e. where setup.py is)"""

VERSION_FILE = join(BASE_DIR, 'privex', 'helpers', '__init__.py')
"""The file containing the package version (for :py:func:`.setuppy.bump_version`)"""

REDIS_HOST = 'localhost'
"""Hostname / IP address where redis-server is running on"""

REDIS_PORT = 6379
"""Port number that Redis is running on at ``REDIS_HOST``"""

REDIS_DB = 0
"""Redis database to use (number)"""

DEFAULT_CACHE_TIMEOUT = 300
"""Default cache timeout in seconds, used by cache adapters in the module :py:mod:`.cache`"""

EXTRAS_FOLDER = 'extras'
"""Folder where additional requirements files can be found for :py:func:`privex.helpers.setuppy.common.extras`"""

