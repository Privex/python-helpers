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
import sys
from datetime import datetime
from os import getcwd, getenv as env
from os import path
from os.path import basename, dirname, abspath, join, expanduser
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

DEFAULT_CACHE_TIMEOUT = _env_int('PRIVEX_CACHE_TIMEOUT', 300)

"""Default cache timeout in seconds, used by cache adapters in the module :py:mod:`.cache`"""

DEFAULT_CACHE_ADAPTER = env('PRIVEX_CACHE_ADAPTER', 'memory')
"""
The default cache adapter to use by default, with the framework-agnostic cache abstraction layer ( :mod:`privex.helpers.cache` ).

Can be one of the following:

  ( more options may be available since the time of writing, see :attr:`privex.helpers.cache.ADAPTER_MAP` )
  
  * ``memory`` / ``mem`` / ``ram`` - Dependency-free memory cache inside of your application's memory.
  
    **Requires:** N/A - no dependencies
    
    **Class:** :class:`.MemoryCache` (sync) // :class:`.AsyncMemoryCache` (async)
    
  * ``redis`` - Caching via a local or remote Redis server
     
     **Requires**: ``redis`` (sync) and/or ``aioredis`` (async) libraries
     
     **Class:** :class:`.RedisCache` (sync) // :class:`.AsyncRedisCache` (async)
     
  * ``memcached`` / ``memcache`` / ``mcache`` - Caching via a local or remote Memcached server
  
    **Requires**: ``pylibmc`` (sync) and/or // ``aiomcache`` (async) libraries
    
    **Class:** :class:`.MemcachedCache` (sync) // :class:`.AsyncMemcachedCache` (async)

  * ``sqlite3`` / ``sqlite`` / ``sqlitedb`` - Caching via an SQLite3 database stored on the filesystem
  
    **Requires**: ``privex-db`` (for both sync and async) and ``aiosqlite`` (only for async) libraries
    
    **Class:** :class:`.SqliteCache` (sync) // :class:`.AsyncSqliteCache` (async)


"""

DEFAULT_ASYNC_CACHE_ADAPTER = env('PRIVEX_ASYNC_CACHE_ADAPTER', DEFAULT_CACHE_ADAPTER)
"""
The default cache adapter for the AsyncIO caching system. :mod:`privex.helpers.cache` / :mod:`privex.helpers.cache.asyncx`

This defaults to :attr:`.DEFAULT_CACHE_ADAPTER` - since at the time of writing, all cache adapter alias names are also valid
for the AsyncIO cache system.

For example, when ``'redis'`` is specified to :attr:`.DEFAULT_ASYNC_CACHE_ADAPTER` , the :class:`.AsyncRedisCache` AsyncIO cache adapter
will be loaded for the async cache system, while when specified to the standard ``DEFAULT_CACHE_ADAPTER``, the
synchronous :class:`.RedisCache` adapter is loaded for use with the synchronous cache APIs.

Available adapters ( same as :attr:`.DEFAULT_CACHE_ADAPTER` ):

  * ``memory`` / ``mem`` / ``ram`` - Dependency-free memory cache inside of your application's memory.
  * ``redis`` - Caching via a local or remote Redis server
  * ``memcached`` / ``memcache`` / ``mcache`` - Caching via a local or remote Memcached server
  * ``sqlite3`` / ``sqlite`` / ``sqlitedb`` - Caching via an SQLite3 database stored on the filesystem


"""

########
# Redis Settings
########

REDIS_HOST = env('PRIVEX_REDIS_HOST', 'localhost')
"""Hostname / IP address where redis-server is running on"""
REDIS_PORT = _env_int('PRIVEX_REDIS_PORT', 6379)
"""Port number that Redis is running on at ``REDIS_HOST``"""
REDIS_DB = _env_int('PRIVEX_REDIS_DB', 0)
"""Redis database to use (number)"""

########
# Memcached Settings
########

MEMCACHED_HOST = env('PRIVEX_MEMCACHED_HOST', 'localhost')
"""Hostname / IP address where Memcached is running on"""
MEMCACHED_PORT = _env_int('PRIVEX_MEMCACHED_PORT', 11211)
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

DEFAULT_USER_AGENT = env('PRIVEX_USER_AGENT', "Python Privex Helpers ( https://github.com/Privex/python-helpers )")

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


def _bdir_plus_fname(f, sep='-', rem_ext=True):
    bpath, fname = path.split(f)
    _, bname = path.split(bpath)
    if rem_ext:
        fname, _ = path.splitext(fname)
    return f"{bname}{sep}{fname}"
    

SQLITE_APP_DB_NAME = env('SQLITE_APP_DB_NAME', _bdir_plus_fname(abspath(sys.argv[0])))
"""
This environment variable controls the default database file "name" portion for the SQLite3 database
wrappers in :mod:`privex.helpers.cache.post_deps` (used by the sync and async sqlite3 cache adapters)

If not set, it defaults to a combination of the **containing folder name** and the **base filename** of the currently
executing script - with the file extension (e.g. ``.py``) removed if it's present.

The folder name + base filename is retrieved from ``sys.argv[0]``. For example, if you ran an
application / script via ``./some/app/example.py``, then this would default to: ``app-example``

If you set this variable in your environment, for example, ``SQLITE_APP_DB_NAME=my_app`` would result in a default DB path
which looks like::

    /home/exampleuser/.privex_cache/my_app.sqlite3


"""

SQLITE_APP_DB_FOLDER = expanduser(env('SQLITE_APP_DB_FOLDER', '~/.privex_cache'))
"""
This environment variable controls the default base folder used to store database files for the SQLite3 database
wrappers in :mod:`privex.helpers.cache.post_deps` (used by the sync and async sqlite3 cache adapters).

The variable is only used if a user / application either doesn't specify a path to a DB file with the sync/async SQLite3
cache adapters, or they specify a relative path ( e.g. ``my_app/cache/cache_db.sqlite3`` ).

You may reference the current user's home directory (the user currently executing the python app/script that uses privex-helpers)
simply by using the character ``~``. For example, on a standard Linux system, if the executing user was ``john``, and
the ``SQLITE_APP_DB_FOLDER`` is set to ``~/.example``, then the folder would resolve to ``/home/john/.example``.

If not set, it defaults to ``~/.privex_cache``, a hidden folder directly within the current user's home directory.

This env var is used in conjunction with :attr:`.SQLITE_APP_DB_NAME` to produce a path to an SQLite3

"""
