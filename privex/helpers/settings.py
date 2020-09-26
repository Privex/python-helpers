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
        |        License: X11 / MIT                         |
        |                                                   |
        |        Core Developer(s):                         |
        |                                                   |
        |          (+)  Chris (@someguy123) [Privex]        |
        |          (+)  Kale (@kryogenic) [Privex]          |
        |                                                   |
        +===================================================+

    Copyright 2019     Privex Inc.   ( https://www.privex.io )


"""
import random
from datetime import datetime
from os import getcwd, getenv as env
from os.path import dirname, abspath, join, expanduser
from typing import Optional

BASE_DIR = dirname(dirname(dirname(abspath(__file__))))
"""The root folder of this project (i.e. where setup.py is)"""

VERSION_FILE = join(BASE_DIR, 'privex', 'helpers', '__init__.py')
"""The file containing the package version (for :py:func:`.setuppy.bump_version`)"""

EXTRAS_FOLDER = 'extras'
"""Folder where additional requirements files can be found for :py:func:`privex.helpers.setuppy.common.extras`"""


def _is_true(v):
    return (v.lower() if type(v) is str else v) in [True, 'true', 'yes', 'y', '1', 1]


def _env_bool(v, d) -> bool: return _is_true(env(v, d))


def _env_int(v, d) -> int: return int(env(v, d))


########################################
#                                      #
#       Cache Module Settings          #
#                                      #
#       privex.helpers.cache           #
#                                      #
########################################

########
# General Cache Settings
########

DEFAULT_CACHE_TIMEOUT = 300
"""Default cache timeout in seconds, used by cache adapters in the module :py:mod:`.cache`"""

########
# Redis Settings
########

REDIS_HOST = 'localhost'
"""Hostname / IP address where redis-server is running on"""
REDIS_PORT = 6379
"""Port number that Redis is running on at ``REDIS_HOST``"""
REDIS_DB = 0
"""Redis database to use (number)"""

########
# Memcached Settings
########

MEMCACHED_HOST = 'localhost'
"""Hostname / IP address where Memcached is running on"""
MEMCACHED_PORT = 11211
"""Port number that Memcached is running on at ``MEMCACHED_HOST``"""

########################################
#                                      #
#       GeoIP Module Settings          #
#                                      #
#       privex.helpers.geoip           #
#                                      #
########################################

search_geoip = [
    '/usr/share/GeoIP',
    '/usr/lib/GeoIP',
    '/var/lib/GeoIP',
    '/usr/local/share/GeoIP',
    '/usr/local/var/GeoIP',
    '/var/GeoIP',
    join(getcwd(), 'GeoIP'),
    expanduser('~/GeoIP'),
    expanduser('~/.GeoIP'),
]


GEOIP_DIR = env('GEOIP_DIR', '/usr/share/GeoIP')
GEOASN_NAME = env('GEOASN_NAME', 'GeoLite2-ASN.mmdb')
GEOCITY_NAME = env('GEOCITY_NAME', 'GeoLite2-City.mmdb')
GEOCOUNTRY_NAME = env('GEOCOUNTRY_NAME', 'GeoLite2-Country.mmdb')

GEOASN_DETECTED, GEOCITY_DETECTED, GEOCOUNTRY_DETECTED = False, False, False

GEOCITY, GEOASN, GEOCOUNTRY = join(GEOIP_DIR, GEOCITY_NAME), join(GEOIP_DIR, GEOASN_NAME), join(GEOIP_DIR, GEOCOUNTRY_NAME)

TERMBIN_HOST, TERMBIN_PORT = 'termbin.com', 9999

CHECK_CONNECTIVITY: bool = _env_bool('CHECK_CONNECTIVITY', True)

HAS_WORKING_V4: Optional[bool] = None
"""
This is a storage variable - becomes either ``True`` or ``False`` after :func:`.check_v4` has been ran.

 * ``None`` - The connectivity checking function has never been ran - unsure where this IP version works or not.
 * ``True`` - This IP version appears to be fully functional - at least it was the last time the IP connectivity checking function was ran
 * ``False`` - This IP version appears to be broken - at least it was the last time the IP connectivity checking function was ran

"""
HAS_WORKING_V6: Optional[bool] = None
"""
This is a storage variable - becomes either ``True`` or ``False`` after :func:`.check_v6` has been ran.
 
 * ``None`` - The connectivity checking function has never been ran - unsure where this IP version works or not.
 * ``True`` - This IP version appears to be fully functional - at least it was the last time the IP connectivity checking function was ran
 * ``False`` - This IP version appears to be broken - at least it was the last time the IP connectivity checking function was ran

"""

SSL_VERIFY_CERT: bool = _env_bool('SSL_VERIFY_CERT', True)
SSL_VERIFY_HOSTNAME: bool = _env_bool('SSL_VERIFY_HOSTNAME', True)

DEFAULT_USER_AGENT = "Python Privex Helpers ( https://github.com/Privex/python-helpers )"

# V4_CHECKED_AT: Optional[datetime] = None
# """
# This is a storage variable - used by :func:`.check_v4` to determine how long it's been since the host's IPv4 was tested.
# """
#
# V6_CHECKED_AT: Optional[datetime] = None
# """
# This is a storage variable - used by :func:`.check_v6` to determine how long it's been since the host's IPv6 was tested.
# """

NET_CHECK_TIMEOUT: int = _env_int('NET_CHECK_TIMEOUT', 3600)
"""
Number of seconds to cache the functional status of an IP version (caching applies to both positive and negative test results).
"""

NET_CHECK_HOST_COUNT: int = _env_int('NET_CHECK_HOST_COUNT', 3)
"""
Number of hosts in :attr:`.V4_TEST_HOSTS` / :attr:`.V6_TEST_HOSTS` that must be accessible - before that IP protocol
is considered functional.
"""

NET_CHECK_HOST_COUNT_TRY: int = _env_int('NET_CHECK_HOST_COUNT', 8)
"""
Maximum number of hosts in :attr:`.V4_TEST_HOSTS` / :attr:`.V6_TEST_HOSTS` that will be tested by :func:`.check_v4` / :func:`.check_v6`
"""

V4_TEST_HOSTS = [
    '185.130.44.10:80', '8.8.4.4:53', '1.1.1.1:53', '185.130.44.20:53', 'privex.io:80', 'files.privex.io:80',
    'google.com:80', 'www.microsoft.com:80', 'facebook.com:80', 'python.org:80'
]

V6_TEST_HOSTS = [
    '2a07:e00::333:53', '2001:4860:4860::8888:53', '2606:4700:4700::1111:53', '2a07:e00::abc:80',
    'privex.io:80', 'files.privex.io:80', 'google.com:80', 'facebook.com:80', 'bitbucket.org:80'
]

random.shuffle(V4_TEST_HOSTS)
random.shuffle(V6_TEST_HOSTS)

DEFAULT_SOCKET_TIMEOUT = 45

DEFAULT_READ_TIMEOUT = _env_int('DEFAULT_READ_TIMEOUT', 60)
DEFAULT_WRITE_TIMEOUT = _env_int('DEFAULT_WRITE_TIMEOUT', DEFAULT_READ_TIMEOUT)

DEFAULT_READ_TIMEOUT = None if DEFAULT_READ_TIMEOUT == 0 else DEFAULT_READ_TIMEOUT
DEFAULT_WRITE_TIMEOUT = None if DEFAULT_WRITE_TIMEOUT == 0 else DEFAULT_WRITE_TIMEOUT
