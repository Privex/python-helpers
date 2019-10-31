"""
Automated Python package version bumping

Summary
-------

Included is a standalone function :py:func:`.bump_version` - which when called, loads the file
:py:attr:`.settings.VERSION_FILE` , extracts the current version, bumps the requested part of the version,
then replaces the version line inside of the file so that it contains the newly bumped version.

There's also a setup.py command class :py:class:`.BumpCommand` which allows you to use :py:func:`.bump_version`
as a ``setup.py`` command, making it simple to increment your package's version without having to manually edit
the file.

If the package :py:mod:`semver` is detected, the version bumping helper :py:func:`.bump_version` becomes available.

If the module :py:mod:`distutils` is detected, the setup.py command class :py:class:`.BumpCommand` also becomes
available.


How to version your package for best compatibility
--------------------------------------------------

To avoid having to write your own version detection / replacement functions, we recommend placing your package
version inside of a python module file, such as ``__init__.py`` - as the string variable ``VERSION``

Example, ``mypackage/__init__.py``


.. code-block:: python

    from mypackage.somemodule import x
    from mypackage.othermodule import y

    VERSION = '1.2.3'


If you cannot store your package version this way for some reason, then you can write a custom detection/replacement
function and register it as the default.

See the docs for :py:func:`.bump_version` to learn how to write a custom version detection/replacement function.


Using the BumpCommand distutils command in your setup.py
--------------------------------------------------------

For :class:`.BumpCommand` to function, you must at least set :py:attr:`privex.helpers.settings.VERSION_FILE`
to an absolute path to the file which contains your package version attribute.

If your package version isn't defined as shown in the previous section on how to version your package,
then you'll **also need to set up custom version detection/replacement functions**.
(see docs at :py:func:`.bump_version`)

Below is an example ``setup.py`` file, which configures the VERSION_FILE setting to point to ``mypackage/__init__.py``
relative to the folder setup.py is in, then calls :py:func:`setuptools.setup` with the package version and command
dictionary.

.. code-block:: python

    from os import join, dirname, abspath
    from setuptools import setup, find_packages
    from privex.helpers import settings, BumpCommand
    # If you placed your version in your package __init__ then you can import it for use in setup.py building
    from mypackage import VERSION

    # This results in an absolute path to the folder where this setup.py file is contained
    BASE_DIR = dirname(abspath(__file__))

    # The file which contains "VERSION = '1.2.3'"
    settings.VERSION_FILE = join(BASE_DIR, 'mypackage', '__init__.py')

    # Register BumpCommand as a command in your setup() function.
    setup(
        version=VERSION,
        cmdclass={
            'bump': BumpCommand
        },
    );


Basic usage of the bump command with setup.py
---------------------------------------------

Once you've configured  :py:attr:`privex.helpers.settings.VERSION_FILE` and registered the command class in the
``setup()`` function, you can now use the ``bump`` command from your ``setup.py`` and it will automatically bump
your version.

Below is an example of basic usage. If you need more help on usage, type ``./setup.py bump --help`` - or for
detailed documentation on the command, see the class documentation :class:`.BumpCommand`

.. code-block:: bash

    ./setup.py bump --patch
    # Bumping 'patch' version part
    # Updating version stored in file @ /tmp/helpers/privex/helpers/__init__.py
    # Package version has been bumped from 2.0.0 to 2.0.1 and written to the file
    # /tmp/helpers/privex/helpers/__init__.py

    ./setup.py bump --minor
    # ... version has been bumped from 2.0.0 to 2.1.0 and written to the file ...


"""
import re
import logging
import semver
from privex.helpers import settings
try:
    from privex.helpers.setuppy.commands import BumpCommand
except ImportError:
    pass


log = logging.getLogger(__name__)

_find_ver = re.compile(r'VERSION = \'?\"?([0-9a-zA-Z-._]+)\'?\"?')
"""Regex used for finding/replacing version line"""


def version_replace(data: str, old_version: str, new_version: str) -> str:
    """
    Replace the version line in ``data`` containing ``old_version`` with a version line containing ``new_version``
    
    Example::
    
        >>> data = "# Example\\nVERSION = '1.2.3' # Some comment"
        >>> version_replace(data=data, old_version='1.2.3', new_version='1.3.0')
        "# Example\\nVERSION = '1.3.0' # Some comment"
    
    
    As shown in the above example, it shouldn't affect surrounding lines, or even in-line comments.
    
    Note: ``old_version`` isn't really used by this function. It exists for compatibility with user drop-in
    replacement functions that may need to know the old version to replace it.
    
    :param str data: The string contents containing ``VERSION = 'x.y.z'``
    :param str old_version: The existing version number, e.g. ``'1.2.3'``
    :param str new_version: The new version to replace it with, e.g. ``'1.3.0'``
    :return str replaced: ``data`` with the VERSION line updated.
    """
    return _find_ver.sub(f"VERSION = '{new_version}'", data)


def get_current_ver(data: str = None):
    return str(_find_ver.search(data).group(1))


default_replace_func = version_replace
"""If no version replacement function is passed to :py:func:`.bump_version`, then this function will be used."""

default_current_ver = get_current_ver
"""If no version retrieval function is passed to :py:func:`.bump_version`, then this function will be used."""


def bump_version(part='patch', dry=False, **kwargs):
    """
    Bump semver version and replace version line inside of :py:attr:`.settings.VERSION_FILE`
    
     * Obtains the current package version using ``version_func``
     * Uses :py:mod:`semver` to increment the ``part`` portion and resets any lower portions to zero
     * Reads the file :py:attr:`.settings.VERSION_FILE` and passes it to ``replace_func`` along with the original
       version and new bumped version to obtain the modified file contents.
     * Writes the file contents containing the updated version number back to :py:attr:`.settings.VERSION_FILE`
    
    Basic usage:
    
        >>> from privex.helpers import settings, setuppy
        >>> bump_version('minor')
    
    If you want to use this function outside of privex-helpers, for your own package/project, ensure you
    adjust the settings and version functions as required.
    
    To change the file which contains your package version, as well as the function used to get the
    current version::
    
        >>> import mypackage
        >>> from privex.helpers import settings
        
        >>> settings.VERSION_FILE = '/home/john/mypackage/mypackage/__init__.py'
        
    If you use the same version line format at privex-helpers, like this::
    
        VERSION = '1.2.3'   # In-line comments are fine, as are double quotes instead of single quotes.
    
    Then you don't need to make a custom version retrieval or replacement function.
    
    Otherwise... this is how you write and register a custom version retrieval and replacement function:
    
    .. code-block:: python
       :force:
        
        import re
        from privex.helpers.setuppy import bump
        
        # Regex to find the string: version='x.y.z'
        # and extract the version x.y.z on it's own.
        my_regex = re.compile(r'version=\'?\"?([0-9a-zA-Z-._]+)\'?\"?')

        def my_version_finder(data: str):
            return str(my_regex.search(data).group(1))
        
        # Set your function `my_version_finder` as the default used to obtain the current package version
        bump.default_current_ver = my_version_finder
        
        def my_version_replacer(data: str, old_version: str, new_version: str):
            # This is an example of a version replacer if you just put your version straight into setup.py
            return data.replace(f"version='{old_version}'", f"version='{new_version}'")
            
            # Alternatively use regex substitution
            return my_regex.sub(f"version='{new_version}'", data)
        
        # Set your function `my_version_replacer` as the default used to replace the version in a file.
        bump.default_replace_func = my_version_replacer
        
        
    
    :param bool dry: If set to ``True``, will only return the modified file contents instead of overwriting
                     the file :py:attr:`.settings.VERSION_FILE`
    :param str part: The part of the version to bump: ``patch``, ``minor``, ``major``, ``build`` or ``prerelease``
    :key callable replace_func: Custom version replacement function. Should take the arguments
                                (data, old_version, new_version) and return ``data`` with the version line replaced.
    :key callable version_func: Custom version retrieval function. Takes no args, returns curr version as a string.
    :key str token: If using part ``build`` or ``prerelease``, this overrides the version token
    :return:
    """
    replace_func = kwargs.get('replace_func', default_replace_func)
    get_version = kwargs.get('version_func', default_current_ver)

    ver_path = settings.VERSION_FILE
    log.debug('Reading file %s to replace version line', ver_path)
    with open(ver_path) as fp:
        ver_file = str(fp.read())

    curr_ver = get_version(ver_file)
    new_ver = _bump_version(version=curr_ver, part=part, **kwargs)
    log.debug('Current version: %s ||| Bumped version: %s', curr_ver, new_ver)
    
    new_ver_file = replace_func(data=ver_file, old_version=curr_ver, new_version=new_ver)
    if dry:
        log.debug('Dry kwarg was True. Returning modified file instead of outputting it.')
        return new_ver_file

    log.debug('Attempting to write updated contents back to %s', ver_path)
    with open(ver_path, 'w') as fp:
        fp.write(new_ver_file)
    
    return new_ver, curr_ver


def _bump_version(version: str, part: str, **kwargs) -> str:
    """
    Bumps the semver part ``part`` in the version ``version`` and returns it as a string.
    
    Used internally by :py:func:`.bump_version`
    
        >>> _bump_version('1.2.3', 'minor')
        '1.3.0'
    
    :param version: The version to bump as a string e.g. ``'1.2.3'```
    :param part: The part of the version to bump, e.g. ``minor`` or ``major``
    :key str token: If using part ``build`` or ``prerelease``, this overrides the version token
    :raises AttributeError: If ``part`` isn't a supported version part.
    :return str new_ver: The bumped version number
    """
    bumps = dict(
        minor=semver.bump_minor,
        major=semver.bump_major,
        patch=semver.bump_patch,
        build=semver.bump_build,
        prerelease=semver.bump_prerelease,
        pre=semver.bump_prerelease,
    )
    if part not in bumps:
        raise AttributeError(f'The "part" argument must be one of the following: {",".join(bumps.keys())}')
    ver_args = dict(version=version)
    if 'token' in kwargs:
        ver_args['token'] = kwargs['token']
        print('_bump_version token:', ver_args['token'])
    new_ver = bumps[part](**ver_args)
    return new_ver


