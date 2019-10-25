# Privex's Python Helpers

[![Documentation Status](https://readthedocs.org/projects/python-helpers/badge/?version=latest)](https://python-helpers.readthedocs.io/en/latest/?badge=latest) 
[![Build Status](https://travis-ci.com/Privex/python-helpers.svg?branch=master)](https://travis-ci.com/Privex/python-helpers) 
[![Codecov](https://img.shields.io/codecov/c/github/Privex/python-helpers)](https://codecov.io/gh/Privex/python-helpers)
[![PyPi Version](https://img.shields.io/pypi/v/privex-helpers.svg)](https://pypi.org/project/privex-helpers/)
![License Button](https://img.shields.io/pypi/l/privex-helpers) 
![PyPI - Downloads](https://img.shields.io/pypi/dm/privex-helpers)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/privex-helpers) 
![GitHub last commit](https://img.shields.io/github/last-commit/Privex/python-helpers)

This small Python 3 module is comprised of various small functions and classes that were often
copied and pasted across our projects.

Each of these "helper" functions, decorators or classes are otherwise too small to be independently
packaged, and so we've amalgamated them into this PyPi package, `privex-helpers`.


```
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
```

# Table of Contents (Github README)

1. [Install](#Install)
    1.1 [Via PyPi (pip)](#download-and-install-from-pypi)
    1.2 [Manually via Git](#alternative-manual-install-from-git)
2. [Documentation](#documentation)
3. [License](#License)
4. [Example Uses](#example-uses)
5. [Minimal Dependencies / Using package extras](#minimal-dependencies)
6. [Unit Tests](#unit-tests)
7. [Contributing](#contributing)


# Install

### Download and install from PyPi 

**Using [Pipenv](https://pipenv.kennethreitz.org/en/latest/) (recommended)**

```sh
pipenv install privex-helpers
```

**Using standard Python pip** 

```sh
pip3 install privex-helpers
```

### (Alternative) Manual install from Git

**Option 1 - Use pip to install straight from Github**

```sh
pip3 install git+https://github.com/Privex/python-helpers
```

**Option 2 - Clone and install manually**

```bash
# Clone the repository from Github
git clone https://github.com/Privex/python-helpers
cd python-helpers

# RECOMMENDED MANUAL INSTALL METHOD
# Use pip to install the source code
pip3 install .

# ALTERNATIVE MANUAL INSTALL METHOD
# If you don't have pip, or have issues with installing using it, then you can use setuptools instead.
python3 setup.py install
```

# Documentation

[![Read the Documentation](https://read-the-docs-guidelines.readthedocs-hosted.com/_images/logo-wordmark-dark.png)](
https://python-helpers.readthedocs.io/en/latest/)

Full documentation for this project is available above (click the Read The Docs image), including:

 - How to install the application and it's dependencies 
 - How to use the various functions and classes
 - General documentation of the modules and classes for contributors

**To build the documentation:**

```bash
git clone https://github.com/Privex/python-helpers
cd python-helpers/docs
pip3 install -r requirements.txt

# It's recommended to run make clean to ensure old HTML files are removed
# `make html` generates the .html and static files in docs/build for production
make clean && make html

# After the files are built, you can live develop the docs using `make live`
# then browse to http://127.0.0.1:8100/
# If you have issues with content not showing up correctly, try make clean && make html
# then run make live again.
make live
```

# License

This Python module was created by [Privex Inc. of Belize City](https://www.privex.io), and licensed under the X11/MIT License.
See the file [LICENSE](https://github.com/Privex/python-helpers/blob/master/LICENSE) for the license text.

**TL;DR; license:**

We offer no warranty. You can copy it, modify it, use it in projects with a different license, and even in commercial (paid for) software.

The most important rule is - you **MUST** keep the original license text visible (see `LICENSE`) in any copies.

# Example uses

We export all of the submodule's contents in `privex/helpers/__init__.py`, so you can import any 
function/class/attribute straight from `privex.helper` without needing several import lines.

Here are some of the most useful examples (part of our `.common` module, no dependencies)

```python
from privex.helpers import empty, is_true, random_str, ip_is_v4, ip_is_v6

####
# Our empty() helper is very convenient and easy to remember. It allows you to quick check if a variable is "empty" 
# (a blank string, None, zero, or an empty list/dict/tuple).
#
#   empty(v, zero: bool = False, itr: bool = False) -> bool
#
# For safety, it only returns True for empty iterables / integer zero (0) if you enable `zero` and/or `itr` respectively.
####

x = ''
if empty(x):
    print('Var x is empty: either None or empty string')

y = []
if empty(y, itr=True):
    print('Var y is empty: either None, empty string, or empty iterable')

####
# Our is_true() / is_false() helpers are designed to ease checking boolean values from plain text config files
# such as .env files, or values passed in an API call
####

# The strings 'true' / 'y' / 'yes' / '1' are all considered truthy, plus int 1 / bool True
enable_x = 'YES'    # String values are automatically cast to lowercase, so even 'YeS' and 'TrUe' are fine.
if is_true(enable_x):
    print('Enabling feature X')

####
# Need to generate a random alphanumeric string for a password / API key? Try random_str(), which uses SystemRandom()
# for cryptographically secure randomness, and by default uses our SAFE_CHARS character set, removing look-alike 
# characters such as 1 and l, or o and 0
####

# Default random string - 50 character alphanum without easily mistaken chars
random_str()   # outputs: 'MrCWLYMYtT9A7bHc5ZNE4hn7PxHPmsWaT9GpfCkmZASK7ApN8r'

# Customised random string - 12 characters using only the characters `abcdef12345` 
random_str(12, chars='abcdef12345') # outputs: 'aba4cc14a43d'

####
# As a server hosting provider, we deal with IP addresses a lot :)
# The helper functions ip_is_v4 and ip_is_v6 do exactly as their name says, they return a boolean
# if an IP is IPv4 or IPv6 respectively.
####

ip_is_v4('192.168.1.1') # True
ip_is_v4('2a07:e00::1') # False

ip_is_v6('192.168.1.1') # False
ip_is_v6('2a07:e00::1') # True

```

# Minimal dependencies

Most of our helper code is independent, and does not result in any extra dependencies being installed. 

Some of our helpers are dependant on external libraries or frameworks, such as Django or Flask. To avoid
large Python packages such as Django being installed needlessly, we programatically enable/disable some
of the helpers based on whether you have the required dependency installed.

This package only requires (and automatically installs if needed) a single dependency - our 
[privex-loghelper](https://github.com/Privex/python-loghelper) package, which itself is lightweight
and dependency free.

As of version 1.6.0 - Privex Helpers now supports **Setuptools Extras**, allowing you
to specify extra dependencies related to privex-helpers in your requirements.txt, or when running
**pip3 install**.

```
# full: Install all extra dependencies if they aren't already installed
#   NOTE: Excludes the `django` extras, because Django + sub-deps weighs ~30-50mb - plus you'd normally only
#   be using the `django` module in a Django project, where you'd have the deps installed anyway...
#
# crypto:   Install dependencies related to the `crypto` module
# cache:    Install dependencies related to the `cache` module
# django:   Install dependencies related to the `django` module
# net:      Install dependencies related to the `net` module

# Example: Install privex-helpers AND all optional dependencies (excluding django), for full functionality
pip3 install 'privex-helpers[full]'

# Example: Install privex-helpers with only the crypto and cache module dependencies
pip3 install 'privex-helpers[cache,crypto]'

# Example: Install just privex-helpers and REQUIRED dependencies (i.e. critical to basic functionality)
pip3 install privex-helpers
```


Alternatively, just `pip3 install` extra packages depending on the helpers you require:

```
# For all Django-specific helpers in privex.helpers.django
Django
# For certain DNS dependant helpers in privex.helpers.net
dnspython>=1.16.0
# For using Redis with the privex.helpers.cache module
redis>=3.3.8
# For using the privex.helpers.crypto module
cryptography>=2.8
```

# Unit Tests

As of late October 2019, we have over 70 individual unit tests in the `tests/` folder, which are split into several
`test_xxxx` files, with each file holding tests for a specific module or smaller area of code. This library 
consistently maintains on average 70-80% test coverage, helping to show this package is highly tested to ensure
reliable and robust code.

We use [Travis CI](https://travis-ci.com/Privex/python-helpers) for continuous integration, which runs the test
suite every time a new commit, tag, or branch is pushed to this Github repo.

We also use [CodeCov](https://codecov.io/gh/Privex/python-helpers) which integrates with our Travis CI setup, and
provides test coverage statistics, so ourselves and contributors can visually see how much of the code is covered
by our unit tests 

TL;Dr; Run the tests:

```
pip3 install -r docs/requirements.txt
pytest -v
```

For more information about using the unit tests, see the 
[How to use the unit tests](https://python-helpers.readthedocs.io/en/latest/helpers/tests.html) section of 
the documentation. 

# Contributing

We're happy to accept pull requests, no matter how small.

Please make sure any changes you make meet these basic requirements:

 - No additional dependencies. We want our helper package to be lightweight and painless to install.
 - Any code taken from other projects should be compatible with the MIT License
 - This is a new project, and as such, supporting Python versions prior to 3.4 is very low priority.
 - However, we're happy to accept PRs to improve compatibility with older versions of Python, as long as it doesn't:
   - drastically increase the complexity of the code
   - OR cause problems for those on newer versions of Python.

**Legal Disclaimer for Contributions**

Nobody wants to read a long document filled with legal text, so we've summed up the important parts here.

If you contribute content that you've created/own to projects that are created/owned by Privex, such as code or 
documentation, then you might automatically grant us unrestricted usage of your content, regardless of the open source 
license that applies to our project.

If you don't want to grant us unlimited usage of your content, you should make sure to place your content
in a separate file, making sure that the license of your content is clearly displayed at the start of the file 
(e.g. code comments), or inside of it's containing folder (e.g. a file named LICENSE). 

You should let us know in your pull request or issue that you've included files which are licensed
separately, so that we can make sure there's no license conflicts that might stop us being able
to accept your contribution.

If you'd rather read the whole legal text, it should be included as `privex_contribution_agreement.txt`.


# Thanks for reading!

**If this project has helped you, consider [grabbing a VPS or Dedicated Server from Privex](https://www.privex.io) - prices start at as little as US$8/mo (we take cryptocurrency!)**