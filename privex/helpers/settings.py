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
from os import getcwd, getenv as env
from os.path import dirname, abspath, join, expanduser

BASE_DIR = dirname(dirname(dirname(abspath(__file__))))
"""The root folder of this project (i.e. where setup.py is)"""

VERSION_FILE = join(BASE_DIR, 'privex', 'helpers', '__init__.py')
"""The file containing the package version (for :py:func:`.setuppy.bump_version`)"""

EXTRAS_FOLDER = 'extras'
"""Folder where additional requirements files can be found for :py:func:`privex.helpers.setuppy.common.extras`"""

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


