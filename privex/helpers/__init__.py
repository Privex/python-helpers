"""
Privex's Python Helpers - https://github.com/privex/python-helpers

X11 / MIT License

**Submodules**:

  * :py:mod:`.common` - Uncategorized functions and classes, including bool checks and data parsing
  * :py:mod:`.decorators` - Class / function decorators
  * :py:mod:`.django` - Django-specific functions/classes, only available if Django package is installed
  * :py:mod:`.net` - Network related functions/classes such as ASN name lookup, and IP version bool checks
  * :py:mod:`.exceptions` - Exception classes used either by our helpers, or generic exceptions for use in projects


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
import warnings

from privex.helpers.common import *
from privex.helpers.collections import *
from privex.helpers.decorators import *
from privex.helpers.net import *
from privex.helpers.exceptions import *
from privex.helpers.plugin import *
from privex.helpers.cache import CacheNotFound, CacheAdapter, CacheWrapper, MemoryCache, cached

from privex.helpers import plugin

log = logging.getLogger(__name__)


try:
    from privex.helpers.cache.RedisCache import RedisCache
    plugin.HAS_REDIS = True
except ImportError:
    log.debug('privex.helpers __init__ failed to import "RedisCache", not loading RedisCache')

try:
    from privex.helpers.cache.MemcachedCache import MemcachedCache
    
    plugin.HAS_MEMCACHED = True
except ImportError:
    log.debug('privex.helpers __init__ failed to import "MemcachedCache", not loading MemcachedCache')

try:
    from privex.helpers.cache.asyncx import *
except ImportError:
    log.debug('privex.helpers __init__ failed to import "cache.asyncx.*", not loading async cache adapters')

try:
    from privex.helpers.cache.extras import *
except ImportError:
    log.exception("[%s] Failed to import %s from %s (unknown error!)", __name__, '*', f'privex.helpers.cache.extras')

try:
    from privex.helpers.asyncx import *
except ImportError:
    log.debug('privex.helpers __init__ failed to import "asyncx", not loading async helpers')

try:
    from privex.helpers.crypto import Format, KeyManager, EncryptHelper, auto_b64decode, is_base64
    plugin.HAS_CRYPTO = True
except ImportError:
    log.debug('privex.helpers __init__ failed to import "crypto", not loading cryptography helpers')

try:
    from privex.helpers.setuppy.common import extras_require, reqs
    plugin.HAS_SETUPPY_COMMON = True
except ImportError:
    log.debug('privex.helpers __init__ failed to import "setuppy.common", not loading packaging helpers')

try:
    from privex.helpers.setuppy.commands import BumpCommand, ExtrasCommand
    plugin.HAS_SETUPPY_COMMANDS = True
except ImportError:
    log.debug('privex.helpers __init__ failed to import "setuppy.commands", not loading packaging helpers')

try:
    from privex.helpers.setuppy.bump import bump_version, get_current_ver
    plugin.HAS_SETUPPY_BUMP = True
except ImportError:
    log.debug('privex.helpers __init__ failed to import "setuppy.bump", not loading packaging helpers')

try:
    from privex.helpers.extras import *
except ImportError:
    log.debug('privex.helpers __init__ failed to import "extras", cannot load any extras.* modules...')

try:
    from privex.helpers.converters import *
except ImportError:
    log.debug('privex.helpers __init__ failed to import "converter", cannot load any converter.* modules...')

try:
    from privex.helpers.geoip import *
    
    plugin.HAS_GEOIP = True
except ImportError:
    log.debug('privex.helpers __init__ failed to import "geoip", not loading GeoIP2 helpers')

try:
    from privex.helpers.thread import *
except ImportError:
    log.debug('privex.helpers __init__ failed to import "thread", not loading python threading helpers')


def _setup_logging(level=logging.WARNING):
    """
    Set up logging for the entire module ``privex.helpers`` . Since this is a package, we don't add any
    console or file logging handlers, we purely just set our minimum logging level to WARNING to avoid
    spamming the logs of any application importing it.
    """
    try:
        from privex.loghelper import LogHelper
        lh = LogHelper(__name__, level=level)
        return lh.get_logger()
    except ImportError:
        warnings.warn(f'{__name__} failed to import privex.loghelper. Logging may not work as expected.')
        lh = logging.getLogger(__name__)
        lh.setLevel(logging.WARNING)
        return log
    

log = _setup_logging()
name = 'helpers'

VERSION = '3.2.0'



