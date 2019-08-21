"""
This module handles connection objects for databases, APIs etc. by exposing functions which initialise and
store class instances for re-use.

It's primarily intended to be used to enable database, caching and third-party API connectivity for the helpers in this
package, however, you're free to use the functions / classes / attributes exposed in this module for your own apps.

Classes are generally initialised using the settings from :py:mod:`.settings` - see the docs for that module to learn
how to override the settings if the defaults don't work for you.


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
import logging
from privex.helpers import settings

log = logging.getLogger(__name__)
HAS_REDIS = False
"""If the ``redis`` module was imported successfully, this will change to True."""

__STORE = {}
"""This ``dict`` is used to store initialised classes for connections to databases, APIs etc."""


try:
    import redis

    def get_redis() -> redis.Redis:
        """Get a Redis connection object. Create one if it doesn't exist."""
        if 'redis' not in __STORE:
            __STORE['redis'] = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
        return __STORE['redis']

    HAS_REDIS = True

except ImportError:
    log.debug('privex.helpers __init__ failed to import "redis", Redis dependent helpers will be disabled.')
except Exception:
    log.debug('privex.helpers __init__ failed to import "redis", (unknown exception), '
              'Redis dependent helpers will be disabled.')

