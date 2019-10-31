"""
Command classes for Distutils/setup.py to assist with Python package building/usage/management.

For basic :class:`.BumpCommand` usage, see either the class documentation itself, or the :py:mod:`.bump` module
documentation.

**Registering distutils commands in setup.py**

Below is a very basic setup.py showing how to load the commands :class:`.BumpCommand` and :class:`.ExtrasCommand`
into setup.py, so they can be used via ``./setup.py bump`` and ``./setup.py extras`` respectively.

.. code-block:: python
        
        from setuptools import setup, find_packages
        from privex.helpers import settings, BumpCommand, ExtrasCommand
        
        # For BumpCommand, specify the file which contains "VERSION = '1.2.3'"
        settings.VERSION_FILE = '/home/john/mypackage/mypackage/__init__.py'
        
        # For ExtrasCommand / extras_require, you may wish to change EXTRAS_FOLDER if you want to store your
        # extras requirements.txt files in a different folder structure.
        # By default, EXTRAS_FOLDER is 'extras' (a folder, relative to the current working directory)
        settings.EXTRAS_FOLDER = 'requirements/extras'
        
        # Load the extra requirements files requirements/extras/cache.txt and requirements/extras/tests.txt
        extensions = ['cache', 'tests']
        
        setup(
            extras_require=extras_require(extensions),
            cmdclass={
                'bump': BumpCommand,
                'extras': ExtrasCommand,
            },
        );

"""
import os
import subprocess
import sys
from distutils.cmd import Command
from io import BufferedWriter
from tempfile import NamedTemporaryFile
from typing import Optional

from privex.helpers import settings
from privex.helpers.setuppy import extras, EXTRAS_FOLDER


class BumpCommand(Command):
    """
    Distutils/setup.py command class for bumping the package version using :func:`.bump_version`
    
    **Usage in setup.py:**
    
    .. code-block:: python
            
            from setuptools import setup, find_packages
            from privex.helpers import settings, BumpCommand
            
            # The file which contains "VERSION = '1.2.3'"
            settings.VERSION_FILE = '/home/john/mypackage/mypackage/__init__.py'
            
            setup(
                cmdclass={
                    'bump': BumpCommand
                },
            );
    
    **Usage on the command line:**
    
    .. code-block:: bash
    
        ./setup.py bump --patch
        # Bumping 'patch' version part
        # Updating version stored in file @ /tmp/helpers/privex/helpers/__init__.py
        # Package version has been bumped from 2.0.0 to 2.0.1 and written to the file
        # /tmp/helpers/privex/helpers/__init__.py
        
        ./setup.py bump --minor
        # ... version has been bumped from 2.0.0 to 2.1.0 and written to the file ...
        
        ./setup.py bump --pre
        # ... version has been bumped from 2.1.0 to 2.1.0-rc.1 ...
        
        ./setup.py bump --build
        # ... version has been bumped from 2.2.0 to 2.2.0+build.1 ...
    
    The options ``--pre`` and ``--build`` also allow an extra option ``--token=xxx`` which allows you to
    change the **token** from the respective ``-rc.x`` and ``+build.x`` to your own label.
    
    If a token is found in the version string, then it will automatically use the one in the version string
    until you either clean off the pre/build suffixes with a normal version bump e.g. ``--patch``
    or you manually remove the suffixes from the version number in the file.
    
    .. code-block:: bash
        
        # NOTE: to change the suffix token, the version must be plain x.y.z without -xxx.y appended.
        ./setup.py bump --pre --token=alpha
        # ... version has been bumped from 2.1.0 to 2.1.0-alpha.1 ...

        ./setup.py bump --pre
        # ... version has been bumped from 2.1.0-alpha.1 to 2.1.0-alpha.2 ...
       
    
    """
    description = 'Bumps the package version using privex.helpers.setuppy.bump_version'
    user_options = [
        ('dry', None, 'If specified, will output the updated file contents, but will not write them'),
        ('patch', None, 'Bump patch version (0.0.x)'),
        ('minor', None, 'Bump minor version (0.x.0'),
        ('major', None, 'Bump major version (x.0.0)'),
        ('build', None, 'Bump build version (0.0.0+build.x)'),
        ('pre', None, 'Bump prerelease version (0.0.0-rc.x)'),
        ('token=', None, 'For build/pre, use this argument value instead of "build" / "rc"'),
    ]
    """Option arguments which can be specified by the user on the command line for this command"""
    
    patch: Optional[int]
    """Bump patch version. If ``--patch`` is passed, this should change from ``None`` to ``1``"""
    
    minor: Optional[int]
    """Bump minor version. If ``--minor`` is passed, this should change from ``None`` to ``1``"""
    
    major: Optional[int]
    """Bump major version. If ``--major`` is passed, this should change from ``None`` to ``1``"""
    
    build: Optional[int]
    """Bump build version. If ``--build`` is passed, this should change from ``None`` to ``1``"""
    
    pre: Optional[int]
    """Bump prerelease version. If ``--pre`` is passed, this should change from ``None`` to ``1``"""
    
    token: Optional[str]
    """
    If bumping :py:attr:`.pre` or :py:attr:`.build` then the user may specify ``--token`` to configure the
    version token e.g. ``rc`` or ``alpha``
    """
    
    dry: Optional[int]
    """
    Enable dry run mode if not ``None``. Dry mode means the contents of the file that would be modified would be
    returned to the console so you can see how it would modify the file, without actually writing to it.
    
    If ``--dry`` is specified, this should change from from ``None`` to ``1``
    """
    
    version_part: Optional[str]
    """Stores the chosen version part to bump, e.g. ``'pre'`` or ``'major'``"""
    
    def initialize_options(self):
        self.patch = None
        self.minor = None
        self.major = None
        self.build = None
        self.pre = None
        self.token = None
        self.version_part = None
        self.dry = None
    
    def finalize_options(self):
        exclusive = ['patch', 'minor', 'major', 'build', 'pre']
        ex_set = False
        for ex in exclusive:
            
            if getattr(self, ex) is not None:
                assert not ex_set, f'Error: Version portion arguments are mutually exclusive.' \
                                   f'Only pass ONE of these options: {", ".join(exclusive)}'
                ex_set = True
                self.version_part = ex
        assert ex_set, f'Please pass at least ONE of these options: --{", --".join(exclusive)}'
    
    def run(self):
        from privex.helpers.setuppy.bump import bump_version
        ver_file = settings.VERSION_FILE
        ver_args = dict(part=self.version_part)
        if self.token is not None:
            self.announce(f'Using version token "{self.token}"', level=4)
            ver_args['token'] = self.token
        if self.dry is not None:
            ver_args['dry'] = True
            self.announce("##############################################################", level=4)
            self.announce("# !!! DRY RUN !!!", level = 4)
            self.announce(f"# Modified contents of {ver_file} (not written back to file)", level=4)
            self.announce("##############################################################", level=4)
            contents = bump_version(**ver_args)
            self.announce(contents, level=4)
            self.announce("##############################################################", level=4)
            self.announce("# !!! END DRY RUN !!!", level=4)
            self.announce(f"# Above is modified contents of {ver_file} (not written back to file)", level=4)
            self.announce("##############################################################", level=4)
            return

        self.announce(f"Bumping '{self.version_part}' version part", level=4)
        self.announce(f"Updating version stored in file @ {ver_file}", level=4)
        new_version, old_version = bump_version(**ver_args)
        self.announce(f"Package version has been bumped from {old_version} to {new_version} and "
                      f"written to the file {ver_file}", level=4)


class ExtrasCommand(Command):
    """
    Distutils/setup.py command for managing package extras, including displaying/saving requirements, installing them,
    and more.
    
    **Usage in setup.py:**
    
    .. code-block:: python
            
            from setuptools import setup, find_packages
            from privex.helpers import ExtrasCommand
            
            
            setup(
                cmdclass={
                    'extras': ExtrasCommand
                },
            );
    
    **Command usage examples**
    
    Print all requirements listed for each extra in ``extras_require``
    
    .. code-block:: bash
    
        ./setup.py extras
        #### Example output: ####
        # # Extra [cache] - file: extras/cache.txt
        # redis>=3.3
        # # Extra [crypto] - file: extras/crypto.txt
        # cryptography>=2.8
        # Extra [django] - file: extras/django.txt
        # Django
        ...
    
    
    Print only the requirements for a specific extra:
    
    .. code-block:: bash
        
        ./setup.py extras --extra=cache
        #### Example output: ####
        # # Extra [cache] - file: extras/cache.txt
        # redis>=3.3
    
    
    Install requirements for a specific extra using pip
    
    
    .. code-block:: bash
    
        ./setup.py extras --install --extra=cache
        # running extras
        # Installing the following requirements: redis>=3.3
        # Requirement already up-to-date: redis>=3.3 in ./venv/lib/python3.7/site-packages (3.3.11)
        # Done.
    
    Install **ALL** extras requirements using pip
    
    .. code-block:: bash
        
        ./setup.py extras --install
    
    List extras entered in ``extras_require``
    
    .. code-block:: bash
    
        ./setup.py extras --list
        # # Extras available:
        # full
        # cache
        # crypto
        ...
    
    """
    user_options = [
        ('save=', 'o', 'Output extras in requirements.txt format to this file'),
        ('extra=', 'e', 'List requirements for this specific extra name, e.g. --extra=cache'),
        ('list', 'l', 'Only list extra names, not the requirements they include'),
        ('install', 'i', 'Install all extras requirements, or if --extra/-e is specified, only that extra.')
    ]
    description = 'Manage distutils extras. Prints/saves requirements, prints extras, and can ' \
                  'install extras via pip'
    
    def initialize_options(self):
        self.save = None
        self.extra = None
        self.list = None
        self.install = None
        return
    
    def finalize_options(self):
        return
    
    def _get_extra(self, name, comments=True) -> list:
        """
        Return a list of requirements for the extra ``name``
        
        :param str name: Name of the extra, e.g. ``'cache'``
        :param bool comments: (Default: ``True``) If True, add a comment to the start containing the extra name
                              and path to it's requirements file
        :return list reqs: The extras requirements, as a list
        """
        ex_file = name + ".txt"
        extra_list = extras(ex_file)
        if comments:
            extra_list.insert(0, f'# Extra [{name}] - file: {os.path.join(EXTRAS_FOLDER, ex_file)}')
        return extra_list

    def _get_all_extras(self, comments=True) -> list:
        """
        Return a combined list of requirements for all package extras.
        
        :param bool comments: (Default: ``True``) If True, add a comment to the start of each extras requirements
                              containing the extra name and path to it's requirements file
        :return list reqs: The extras requirements, as a list
        """
        from distutils.dist import Distribution
        dis: Distribution = self.distribution
        ext = dis.metadata.provides_extras
        extra_list = []
        for ex in ext:
            extra_list = extra_list + self._get_extra(ex, comments=comments)
        return extra_list
    
    def install_extras(self):
        """
        Installs extras requirements using ``python -m pip install -U -r requirements.txt``
        
        The python executable is determined using ``sys.executable``, and the requirements.txt file is generated
        into a temporary file which is deleted after the install is finished.
        
        If the argument ``--extra`` / ``-e``  ( :py:attr:`.extra` ) is passed, then this will install
        only the requirements for that extra.
        
        **Example** (assuming this class is registered as ``extras``)
        
        .. code-block:: bash
            
            # Install ALL extras requirements
            ./setup.py extras --install
            
            # Install only the requirements for the extra 'cache'
            ./setup.py extras --install --extra=cache
            # Shorthand version (YMMV based on setuptools/distutils version)
            ./setup.py extras -i -e cache
        
            
        """
        with NamedTemporaryFile() as req_file:
            extras_list = self._get_extra(self.extra, False) if self.extra else self._get_all_extras(False)
            print('Installing the following requirements:', ', '.join(extras_list))
            self.save_list(extra_list=extras_list, out_file=req_file.name)
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-U', '-r', req_file.name])

            print('Done.')

    def run(self):
        if self.install:
            return self.install_extras()
        
        from distutils.dist import Distribution
        dis: Distribution = self.distribution
        ext = dis.metadata.provides_extras
        if self.list:
            print("# Extras available:\n")
            for ex in ext:
                print(ex)
            return
        if self.extra:
            extra_list = self._get_extra(self.extra)
            if self.save:
                self.save_list(extra_list)
                self.announce(f"Wrote extra '{self.extra}' requirements to file {self.save}", level=4)
                return
            for ex in extra_list:
                print(ex)
            return
        
        extra_list = self._get_all_extras()
        if self.save:
            self.save_list(extra_list)
            self.announce(f"Wrote all extras requirements to file {self.save}", level=4)
            return
        
        # ex_file = ex + ".txt"
        # print(f'# Extra [{ex}] - file: {os.path.join(EXTRAS_FOLDER, ex_file)}')
        for r in extra_list:
            print(r)

    def save_list(self, extra_list, out_file=None):
        out_file = self.save if not out_file else out_file
        if isinstance(out_file, BufferedWriter):
            for ex in extra_list:
                out_file.write(ex + "\n")
            return
        
        with open(out_file, 'w') as fp:
            for ex in extra_list:
                fp.write(ex + "\n")
