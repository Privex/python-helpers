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
from os.path import dirname, abspath, join

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




