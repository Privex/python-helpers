"""
Helpers for setup.py, e.g. requirements.txt parsing, version bumping, custom setup.py commands


Inside of :py:mod:`privex.helpers.setuppy.common` there's a variety of functions related to generating
requirements.txt files, parsing requirements.txt files which recursively import other requirements.txt files,
and handing automatic generation of ``extras_require`` from a folder containing requirements txt files.

Inside of :py:mod:`privex.helpers.setuppy.bump` - most notably is :py:func:`.bump_version` - a function which
detects a package's version, increments the appropriate part of the version number, and then updates the python
file containing the version number (e.g. an ``__init__.py``)


Inside of :py:mod:`privex.helpers.setuppy.commands` there are command classes which can be loaded into setup.py to
assist with building python packages, generating requirements.txt files from extras, as well as general management
such as a :class:`.BumpCommand` which allows you to bump your package version with a simple ``./setup.py bump --minor``

More detailed usage documentation is available within each individual module's documentation.

"""

try:
    from privex.helpers.setuppy.common import *
except ImportError:
    log.debug('%s failed to import "setuppy.common", not loading ...', __name__)
try:
    from privex.helpers.setuppy.bump import *
except ImportError:
    log.debug('%s failed to import "setuppy.bump", not loading ...', __name__)
try:
    from privex.helpers.setuppy.commands import *
except ImportError:
    log.debug('%s failed to import "setuppy.commands", not loading ...', __name__)
