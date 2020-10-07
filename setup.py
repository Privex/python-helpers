#!/usr/bin/env python3
"""
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
import warnings

from setuptools import setup, find_packages
from os.path import join, dirname, abspath
from privex.helpers import VERSION, extras_require

BASE_DIR = dirname(abspath(__file__))

with open(join(BASE_DIR, "README.md"), "r") as fh:
    long_description = fh.read()

extensions = ['full', 'cache', 'crypto', 'django', 'docs', 'dev', 'dev_general', 'extras', 'geoip', 'net', 'tests', 'setuppy']

extra_commands = {}

try:
    # noinspection PyUnresolvedReferences
    import privex.helpers.setuppy.commands
    extra_commands['extras'] = privex.helpers.setuppy.commands.ExtrasCommand
    extra_commands['bump'] = privex.helpers.setuppy.commands.BumpCommand
except (ImportError, AttributeError) as e:
    warnings.warn('Failed to import privex.helpers.setuppy.commands - the commands "extras" and "bump" may not work.')
    warnings.warn(f'Error Reason: {type(e)} - {str(e)}')


setup(
    name='privex_helpers',

    version=VERSION,

    description='A variety of helper functions and classes, useful for many different projects',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Privex/python-helpers",
    author='Chris (Someguy123) @ Privex',
    author_email='chris@privex.io',

    license='MIT',
    install_requires=[
        'privex-loghelper>=1.0.4', 'python-dateutil', 'sniffio', 'async-property', 'attrs'
    ],
    cmdclass=extra_commands,
    extras_require=extras_require(extensions),
    packages=find_packages(exclude=['tests', 'tests.*', 'test.*', 'privex.db', 'privex.db.*']),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
