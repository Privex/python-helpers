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

# Tl;Dr; Install and use Privex Helpers

Install from PyPi (detailed install info at [Install](#Install) and [Using package extras](#minimal-dependencies))

```sh
pipenv install privex-helpers    # If you use pipenv (and you should!)
pip3 install privex-helpers      # Otherwise, standard pip installation

# If you're using privex-helpers in a project, then you may want to install with the "full" extras
# which installs all optional requirements (other than Django/tests), so you can use **everything** in privex-helpers
pipenv install 'privex-helpers[full]'    # If you use pipenv (and you should!)
pip3 install 'privex-helpers[full]'      # Otherwise, standard pip installation
```

Very import and basic usage (detailed examples at [Example Uses](#example-uses))

```python
from privex.helpers import is_true, empty
if is_true('yes'):
    print('yes is truthful')

if empty(''):
    print("'' is empty")
```

# Table of Contents (Github README)

**NOTE:** The below Table of Contents is designed to work on Github. The links do NOT work on PyPi's description,
and may not work if you're reading this README.md elsewhere.


1. [Why use Privex Helpers?](#why-use-privex-helpers)

    1.1. [Lightweight](#lightweight)
    
    1.2. [Keeps your code DRY (Don't repeat yourself!)](#keeps-your-code-dry-dont-repeat-yourself)
    
    1.3. [Makes your life just plain easier](#makes-your-life-just-plain-easier)
    
    1.4. [Thorough unit tests](#thorough-unit-tests)
    
    1.5. [Overview of what's included](#overview-of-whats-included)
    
2. [Install](#Install)

    2.1 [Via PyPi (pip)](#download-and-install-from-pypi)
    
    2.2 [Manually via Git](#alternative-manual-install-from-git)

3. [Documentation](#documentation)
4. [License](#License)
5. [Example Uses](#example-uses)
6. [Minimal Dependencies / Using package extras](#minimal-dependencies)

    6.1 [Modules with dependencies](#modules-with-dependencies)
    
    6.2 [Using Setuptools Extras](#using-setuptools-extras)
    
    6.3 [Installing extras when using the cloned repository](#installing-extras-when-using-the-cloned-repository)

7. [Unit Tests](#unit-tests)
8. [Contributing](#contributing)


# Why use Privex Helpers?

Privex helpers was created with a very simple goal in mind: make developing Python applications easy, fun, simple,
and **painless**.

### Lightweight

Whether you're using it in a library, or in your project, you'll be pleased to know that the `privex-helpers` and
all of it's *required dependencies* make up less than **200kb total**. For comparison, the `Django` package alone
(that's excluding it's dependencies) is a whopping 26 MEGABYTES.

Most of `privex-helpers` can be used without any additional dependencies. Some modules, or parts of modules
may require a certain dependency, but will cleanly disable themselves if the necessary dependency isn't available.

See [Modules with dependencies](#modules-with-dependencies) to see which modules only work if you have a certain
package installed, and modules which are dependency-free but enable additional functionality if you install
extra packages.

### Keeps your code DRY (Don't repeat yourself!)

Tired of writing those same long `if` statements to check if a user entered value was some sort-of boolean value?
Use `is_true` and `is_false` - trim those long if statements into a single function call. Less typing, and more 
readable.

### Makes your life just plain easier

Writing a library and need caching? Not sure whether you should just force your users to use Redis, whether you
should just make this a Django plugin, or write some sort-of rudimentary caching system yourself? `privex-helpers`
includes a modular caching abstraction layer that Just Works™ out of the box, without forcing tons of dependencies on
your users.

Maybe you just need to encrypt a string, or generate an RSA keypair. But you tried taking a look at the
popular [cryptography](https://cryptography.io/en/latest/) package docs, and it looks like you're going to be writing
scaffolding code for hours just to do that... Say hello to `privex.helpers.crypto` - whether you're dealing with
symmetric or asymmetric encryption, it's just **one import line, a few lines of code and you're DONE.**

### Thorough unit tests

Included in the `tests/` folder, is a collection of over 70 individual unit tests, which is constantly
having more unit tests added over time.

This project uses Travis for continuous integration (automatic testing with each commit), and CodeCov keeping
track of how much of the codebase is covered by unit tests. See [Unit Tests](#unit-tests) for more details. 

This ensures that `privex-helpers` is reliable and robust - if a part of the library is broken with a new update,
then we'll be alerted shortly after pushing out the update that our tests are failing, so we can fix the issue ASAP.

### Overview of what's included

This is not an exhaustive list, and may sometimes be a little outdated. To see everything that's available in
`privex-helpers` then check out the [Documentation](https://python-helpers.readthedocs.io/en/latest/index.html).

 - `common` - a melting pot of functions and classes that will generally just make developing python code 100x easier, 
   and make it 10x more readable. some of the most useful include:
     - `empty` - checking if a value is "empty", e.g. `None`, `''`, `0`, `'0'`, `[]` etc.
     - `is_true` - fuzzy "true" testing, checks for common forms of true, e.g. `True`, `"true"`, `"yes"`, `1`
     - `is_false` - fuzzy "false" testing, checks for common forms of false, e.g. `False`, `"false"`, `"no"`, `0`
     - `env_csv` - load an environment variable like a CSV, allowing for list representation in env vars
     - `env_keyval` - load an environment variable like a key value map, allowing for tuple pair / dict 
      representation in env vars
     - `dec_round` - round a python `Decimal` using the built-in Quantize method, but without the hassle.
     - `Dictable` - easily create your Python 3.7 `dataclass` from a dictionary, plus enable them to be casted
      into a plain dict using `dict(mydataclass)`
     - and MORE, check the [documentation!](https://python-helpers.readthedocs.io/en/latest/helpers/privex.helpers.common.html)

 - `cache` - a dependency-free, framework agnostic caching layer, with support for:
     - automatic timeouts
     - ability to extend the timeout of a cache item (even after it's already "expired" on some cache adapters)
     - get_or_set with callback function/method support
     - can optionally use Redis if you'd prefer (requires an optional dependency)

 - `crypto` - classes which make both symmetric and asymmetric encryption extremely easy to use
      - `EncryptHelper` - for symmetric AES-128 encryption / decryption with a shared key, with the ability to generate 
       either a secure random shared key, or a shared key generated from a password + salt
      - `KeyManager` - for asymmetric signing / verification, plus encryption/decryption if you use RSA. supports 
       generating/loading RSA, ECDSA, and Ed25519 keys, as well as outputting them in a variety of formats 
       and encodings.

 - `setuppy` - a module with various functions to help with making python packages or dealing with 
   requirements.txt files
     - `common.extras_require` - A helper function which allows you to generate an `extras_require` setting in
       setup.py simply by passing a list of extras names, e.g. `extras_require=extras_require(['cache', 'net']),`
     - `bump.bump_version` - Bumps a certain part of a package's semver version number and updates the file containing
       the version
     - `commands.BumpCommand` - A setup.py command class, which allows you to use `bump.bump_version` within
       your package, just by typing a command such as `./setup.py bump --minor` (bumps your package's minor 0.x.0
       version and updates the file which contains the version)
     - `commands.ExtrasCommand` - Exposes various functionality for managing `extras_require` in your package,
       including easily generating/saving requirements.txt files for your extras, installing the requirements, 
       and outputting a list of extras.
 
 - `decorators` - various decorators to simplify your code
     - `retry_on_err` - automatically re-run a function/method when exceptions are thrown, with a variety of
      customization available
     - `r_cache` - automatic caching of a function/property, with support for caching based on parameters or a lambda
 
 - `net` - various networking functions, including:
     - handling IP addresses
     - generating reverse DNS records
     - looking up ASN names based on their number
     - checking if an IP is up (via ping) - with both IPv4 and IPv6 support
 
 - `asyncx` - various async helper functions, to help synchronous code play nicely with async code
 - `django` various Django helper functions, most of which you'll probably question "why is this not built into django?" 
 - `exceptions` - various exception classes, most of which are used by privex-helpers functions/classes, but can be 
   used in any python project to save you re-inventing an exception name

     




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

### Using Setuptools Extras

As of version 2.0.0 - Privex Helpers now supports **Setuptools Extras**, allowing you
to specify extra dependencies related to privex-helpers in your requirements.txt, or when running
**pip3 install**.

**What is each extra for?**

Extras designed for using the `privex-helpers` package in a project/package:

 - **full**     - A meta-extra which includes most other extras required for full functionality of the library.
     - It does **NOT** include the `django` extra, because the `Django` package and it's sub-dependencies results in
       a good 30-50mb of packages being installed, and those who would use the `django` module probably already 
       have `Django` installed...
     - It does **NOT** include the `docs` or `tests` extras, as those two are only required for building the
       documentation, or running the unit tests.
 - **crypto**   - Install dependencies required to use the `crypto` module
 - **cache**    - Install optional dependencies to enable all cache backends in `cache`
 - **django**   - Install dependencies related to the `django` module (including `Django` itself)
 - **net**      - Install optional dependencies to enable full functionality of the `net` module
 - **setuppy**  - Install optional dependencies to enable full functionality of the `setuppy` modules

Extras designed for use when developing, testing, documenting, or building `privex-helpers`:

 - **dev**      - Includes everything required for development and related activities with `privex-helper`.
                  Generally includes ALL extras, unlike `full` this includes `django`, `docs` and `tests`
 - **docs**     - This extra is not required for privex-helpers modules. It contains requirements for building the docs.
 - **tests**    - Not required for privex-helpers module usage. Contains requirements for running the unit tests.

**Using the extras with pip install**

```
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

### Installing extras when using the cloned repository

First, it's recommended to install the requirements in `extras/setuppy.txt` to ensure setup.py functions fully.

```bash
pip3 install -r extras/setuppy.txt
```

As of privex-helpers 2.1.0, you can use the handy setup.py `extras` command to install individual extras requirements,
or all extra requirements painlessly:

```bash
# Install ALL extras requirements (including Django and unit testing related)
./setup.py extras -i

# Install an individual extras requirements, for example 'cache' or 'net'
./setup.py extras -i -e cache
```

If you just want to install the `privex-helpers` package from source, then you can use pip to install
the current folder, and specify the extras you want:

```bash
# Standard "full" install, excluding Django and development packages for docs/testing
pip3 install '.[full]'
# Full development installation, includes everything in 'full', with the addition of the django, docs, and tests extras
pip3 install '.[dev]'
``` 
 
### Modules with dependencies

If you're using `privex-helpers` within a normal project (not a package), then it's recommended to simply
install `privex-helpers[full]` which includes all main dependencies for full functionality. 

If you're using it inside of a package, then you should only require the extras that are critical to your package
functioning. Anything non-essential should be placed in the `extras_require` of your setup.py to avoid 
un-necessary packages being installed on your users.


**Modules which require a dependency to use them**

 - `crypto` - This module won't work at all without the `cryptography` library (or `privex-helpers[crypto]`)
 - `django` - Django related helpers obviously don't work without `Django` installed. But since they're intended
    for use within a Django project, you'd already have `Django` installed anyway if you needed them :)

**Dynamic modules which simply enable additional features if you install certain packages**

 - `setuppy` - The `common` sub-module should generally work without any dependencies, but to be able to use all 
   functionality of this module such as the `bump` and `commands` sub-modules, you'll need to install with the
   `setuppy` extra, e.g. `privex-helpers[setuppy]`
 - `net` - Some functions are dependent on `dnspython` (or `privex-helpers[net]`), but the majority of the module 
   is dependency-free
 - `cache` - The cache layer works just fine without any dependencies. If you're using `privex-helper` within a project,
   then you may want to install `redis` (or `privex-helpers[cache]`) to make the Redis cache adapter available.
 - `plugin` - While this module isn't very often used within other projects/packages, it does expose some
   Redis singleton management functions (and possibly others at the time of writing). If you plan on using
   this module, we recommend using `privex-helpers[full]` for the best experience.


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

**If this project has helped you, consider [grabbing a VPS or Dedicated Server from Privex](https://www.privex.io).**

**Prices start at as little as US$8/mo (we take cryptocurrency!)**
