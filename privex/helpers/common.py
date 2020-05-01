"""
Common functions and classes that don't fit into a specific category

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
import inspect
import math
import os
import random
import re
import shlex
import string
import argparse
import logging
import subprocess
import sys
from collections import OrderedDict
from decimal import Decimal, getcontext
from os import getenv as env
from subprocess import PIPE, STDOUT
from typing import Sequence, List, Union, Tuple, Type, Dict, Any, Iterable, Optional, BinaryIO, Generator, Mapping

from privex.helpers import settings

from privex.helpers.collections import DictObject, OrderedDictObject
from privex.helpers.types import T, K, V, C, USE_ORIG_VAR, STRBYTES, Number, NumberStr

log = logging.getLogger(__name__)

SAFE_CHARS = 'abcdefhkmnprstwxyz23456789ACDEFGHJKLMNPRSTWXYZ'
"""Characters that shouldn't be mistaken, avoiding users confusing an o with a 0 or an l with a 1 or I"""

ALPHANUM = string.ascii_uppercase + string.digits + string.ascii_lowercase
"""All characters from a-z, A-Z, and 0-9 - for random strings where there's no risk of user font confusion"""


def random_str(size: int = 50, chars: Sequence = SAFE_CHARS) -> str:
    """
    Generate a random string of arbitrary length using a given character set (string / list / tuple). Uses Python's 
    SystemRandom class to provide relatively secure randomness from the OS. (On Linux, uses /dev/urandom)

    By default, uses the character set :py:attr:`.SAFE_CHARS` which contains letters a-z / A-Z and numbers 2-9
    with commonly misread characters removed (such as ``1``, ``l``, ``L``, ``0`` and ``o``). Pass 
    :py:attr:`.ALPHANUM` as `chars` if you need the full set of upper/lowercase + numbers.

    Usage:

        >>> from privex.helpers import random_str
        >>> # Default random string - 50 character alphanum without easily mistaken chars
        >>> password = random_str()
        'MrCWLYMYtT9A7bHc5ZNE4hn7PxHPmsWaT9GpfCkmZASK7ApN8r'
        >>> # Customised random string - 12 characters using only the characters `abcdef12345` 
        >>> custom = random_str(12, chars='abcdef12345')
        'aba4cc14a43d'

    Warning: As this relies on the OS's entropy features, it may not be cryptographically secure on non-Linux platforms:

    > The returned data should be unpredictable enough for cryptographic applications, though its exact quality 
    > depends on the OS implementation.

    :param int size:  Length of random string to generate (default 50 characters)
    :param str chars: Characterset to generate with ( default is :py:attr:`.SAFE_CHARS` - a-z/A-Z/0-9 with 
                      often misread chars removed)

    """
    return ''.join(random.SystemRandom().choice(chars) for _ in range(size))


def empty(v, zero: bool = False, itr: bool = False) -> bool:
    """
    Quickly check if a variable is empty or not. By default only '' and None are checked, use ``itr`` and ``zero`` to
    test for empty iterable's and zeroed variables.

    Returns ``True`` if a variable is ``None`` or ``''``, returns ``False`` if variable passes the tests

    Example usage:

        >>> x, y = [], None
        >>> if empty(y):
        ...     print('Var y is None or a blank string')
        ...
        >>> if empty(x, itr=True):
        ...     print('Var x is None, blank string, or an empty dict/list/iterable')

    :param v:    The variable to check if it's empty
    :param zero: if ``zero=True``, then return ``True`` if the variable is int ``0`` or str ``'0'``
    :param itr:  if ``itr=True``, then return ``True`` if the variable is ``[]``, ``{}``, or is an iterable and has 0 length
    :return bool is_blank: ``True`` if a variable is blank (``None``, ``''``, ``0``, ``[]`` etc.)
    :return bool is_blank: ``False`` if a variable has content (or couldn't be checked properly)
    """

    _check = [None, '']
    if zero: _check += [0, '0']
    if v in _check: return True
    if itr:
        if v == [] or v == {}: return True
        if hasattr(v, '__len__') and len(v) == 0: return True

    return False


def empty_if(v: V, is_empty: K = None, not_empty: T = USE_ORIG_VAR, **kwargs) -> Union[T, K, V]:
    """
    Syntactic sugar for ``x if empty(y) else z``. If ``not_empty`` isn't specified, then the original value ``v``
    will be returned if it's not empty.
    
    **Example 1**::
    
        >>> def some_func(name=None):
        ...     name = empty_if(name, 'John Doe')
        ...     return name
        >>> some_func("")
        John Doe
        >>> some_func("Dave")
        Dave
    
    **Example 2**::
    
        >>> empty_if(None, 'is empty', 'is not empty')
        is empty
        >>> empty_if(12345, 'is empty', 'is not empty')
        is not empty
    
    
    :param Any v:     The value to test for emptiness
    :param is_empty:  The value to return if ``v`` is empty (defaults to ``None``)
    :param not_empty: The value to return if ``v`` is not empty (defaults to the original value ``v``)
    :param kwargs:    Any additional kwargs to pass to :func:`.empty`
    
    :key zero: if ``zero=True``, then v is empty if it's int ``0`` or str ``'0'``
    :key itr:  if ``itr=True``,  then v is empty if it's ``[]``, ``{}``, or is an iterable and has 0 length
    
    :return V orig_var:  The original value ``v`` is returned if ``not_empty`` isn't specified.
    :return K is_empty:  The value specified as ``is_empty`` is returned if ``v`` is empty
    :return T not_empty: The value specified as ``not_empty`` is returned if ``v`` is not empty
                         (and not_empty was specified)
    """
    not_empty = v if not_empty == USE_ORIG_VAR else not_empty
    return is_empty if empty(v, **kwargs) else not_empty


def is_true(v) -> bool:
    """
    Check if a given bool/str/int value is some form of ``True``:
    
        * **bool**: ``True`` 
        * **str**: ``'true'``, ``'yes'``, ``'y'``, ``'1'``
        * **int**: ``1``
    
    (note: strings are automatically .lower()'d)

    Usage:

    >>> is_true('true')
    True
    >>> is_true('no')
    False

    :param Any v:          The value to check for truthfulness
    :return bool is_true:  ``True`` if the value appears to be truthy, otherwise ``False``.
    """
    v = v.lower() if type(v) is str else v
    return v in [True, 'true', 'yes', 'y', '1', 1]


def is_false(v, chk_none: bool = True) -> bool:
    """
    **Warning:** Unless you specifically need to verify a value is Falsey, it's usually safer to 
    check for truth :py:func:`.is_true` and invert the result, i.e. ``if not is_true(v)``
    
    Check if a given bool/str/int value is some form of ``False``:

        * **bool**: ``False``
        * **str**: ``'false'``, ``'no'``, ``'n'``, ``'0'``
        * **int**: ``0``

    If ``chk_none`` is True (default), will also consider the below values to be Falsey::

        boolean: None // string: 'null', 'none', ''
    
    (note: strings are automatically .lower()'d)

    Usage:

    >>> is_false(0)
    True
    >>> is_false('yes')
    False

    :param Any v:          The value to check for falseyness
    :param bool chk_none:  If ``True``, treat ``None``/``'none'``/``'null'`` as Falsey (default ``True``)
    :return bool is_False: ``True`` if the value appears to be falsey, otherwise ``False``.
    """
    v = v.lower() if type(v) is str else v
    chk = [False, 'false', 'no', 'n', '0', 0]
    chk += [None, 'none', 'null', ''] if chk_none else []
    return v in chk


def parse_keyval(line: str, valsplit: str = ':', csvsplit=',') -> List[Tuple[str, str]]:
    """
    Parses a csv with key:value pairs such as::

        John Alex:Doe,Jane Sarah:Doe
    

    Into a list with tuple pairs (can be easily converted to a dict)::

        [
            ('John Alex', 'Doe'), 
            ('Jane Sarah', 'Doe')
        ]


    By default, uses a colons ``:`` to split the key/value, and commas ``,`` to terminate the end of 
    each keyval pair. This can be overridden by changing valsplit/csvsplit.

    :param str line: A string of key:value pairs separated by commas e.g. ``John Alex:Doe,Jane Sarah:Doe``
    :param str valsplit: A character (or several) used to split the key from the value (default: colon ``:``)
    :param str csvsplit: A character (or several) used to terminate each keyval pair (default: comma ``,``)
    :return List[Tuple[str,str]] parsed_data:  A list of (key, value) tuples that can easily be casted to a dict()
    """
    cs, vs = csvsplit, valsplit
    line = [tuple(a.split(vs)) for a in line.split(cs)] if line != '' else []
    return [(a.strip(), b.strip()) for a, b in line]


def parse_csv(line: str, csvsplit: str = ',') -> List[str]:
    """
    Quick n' dirty parsing of a simple comma separated line, with automatic whitespace stripping
    of both the ``line`` itself, and the values within the commas.

    Example:
    
        >>> parse_csv('  hello ,  world, test')
        ['hello', 'world', 'test']
        >>> parse_csv(' world  ;   test   ; example', csvsplit=';')
        ['world', 'test', 'example']


    :param str line: A string of columns separated by commas e.g. ``hello,world,foo``
    :param str csvsplit: A character (or several) used to terminate each value in the list. Default: comma ``,``
    """
    return [x.strip() for x in line.strip().split(csvsplit)]


def env_csv(env_key: str, env_default = None, csvsplit=',') -> List[str]:
    """
    Quick n' dirty parsing of simple CSV formatted environment variables, with fallback
    to user specified ``env_default`` (defaults to None)

    Example:

        >>> os.setenv('EXAMPLE', '  hello ,  world, test')
        >>> env_csv('EXAMPLE', [])
        ['hello', 'world', 'test']
        >>> env_csv('NONEXISTANT', [])
        []
    
    :param str env_key:     Environment var to attempt to load
    :param any env_default: Fallback value if the env var is empty / not set (Default: None)
    :param str csvsplit: A character (or several) used to terminate each value in the list. Default: comma ``,``
    :return List[str] parsed_data: A list of str values parsed from the env var
    """
    d = env(env_key)
    return env_default if empty(d) else parse_csv(d, csvsplit=csvsplit)


def env_keyval(env_key: str, env_default=None, valsplit=':', csvsplit=',') -> List[Tuple[str, str]]:
    """
    Parses an environment variable containing ``key:val,key:val`` into a list of tuples [(key,val), (key,val)]
    
    See :py:meth:`parse_keyval`

    :param str env_key:     Environment var to attempt to load
    :param any env_default: Fallback value if the env var is empty / not set (Default: None)
    :param str valsplit: A character (or several) used to split the key from the value (default: colon ``:``)
    :param str csvsplit: A character (or several) used to terminate each keyval pair (default: comma ``,``)
    """
    d = env(env_key)
    return env_default if empty(d) else parse_keyval(d, valsplit=valsplit, csvsplit=csvsplit)


def env_cast(env_key: str, cast: callable, env_default=None):
    """
    Obtains an environment variable ``env_key``, if it's empty or not set, ``env_default`` will be returned.
    Otherwise, it will be converted into a type of your choice using the callable ``cast`` parameter

    Example:

        >>> os.environ['HELLO'] = '1.234'
        >>> env_cast('HELLO', Decimal, Decimal('0'))
        Decimal('1.234')


    :param callable cast:   A function to cast the user's env data such as ``int`` ``str`` or ``Decimal`` etc.
    :param str env_key:     Environment var to attempt to load
    :param any env_default: Fallback value if the env var is empty / not set (Default: None)
    """
    return env_default if empty(env(env_key)) else cast(env(env_key))


def env_bool(env_key: str, env_default=None) -> Union[bool, None]:
    """
    Obtains an environment variable ``env_key``, if it's empty or not set, ``env_default`` will be returned.
    Otherwise, it will be converted into a boolean using :py:func:`.is_true`

    Example:

        >>> os.environ['HELLO_WORLD'] = '1'
        >>> env_bool('HELLO_WORLD')
        True
        >>> env_bool('HELLO_NOEXIST')
        None
        >>> env_bool('HELLO_NOEXIST', 'error')
        'error'
    
    :param str env_key:     Environment var to attempt to load
    :param any env_default: Fallback value if the env var is empty / not set (Default: None)
    """
    return env_cast(env_key=env_key, cast=is_true, env_default=env_default)


def env_int(env_key: str, env_default=None) -> int:
    """Alias for :py:func:`.env_cast` with ``int`` casting"""
    return env_cast(env_key=env_key, cast=int, env_default=env_default)


def env_decimal(env_key: str, env_default=None) -> Decimal:
    """Alias for :py:func:`.env_cast` with ``Decimal`` casting"""
    return env_cast(env_key=env_key, cast=Decimal, env_default=env_default)


def extract_settings(prefix: str, _settings=settings, defaults=None, merge_conf=None, **kwargs) -> dict:
    """
    Extract prefixed settings from a given module, dictionary, class, or instance.

    This helper function searches the object ``_settings`` for keys starting with ``prefix``, and for any matching keys, it removes
    the prefix from each key, converts the remaining portion of each key to lowercase (unless you've set ``_case_sensitive=True``),
    and then returns the keys their linked values as a ``dict``.

    For example, if you had a file called ``myapp/settings.py`` which contained ``REDIS_HOST = 'localhost'``
    and ``REDIS_PORT = 6379``, you could then run::

        >>> # noinspection PyUnresolvedReferences
        >>> from myapp import settings
        >>> extract_settings('REDIS_', settings)
        {'host': 'localhost', 'port': 6379}


    Example uses
    ^^^^^^^^^^^^


    Example settings module at ``myapp/settings.py``

    .. code-block:: python

        from os.path import dirname, abspath, join

        BASE_DIR = dirname(dirname(dirname(abspath(__file__))))
        VERSION_FILE = join(BASE_DIR, 'privex', 'helpers', '__init__.py')

        REDIS_HOST = 'localhost'
        REDIS_PORT = 6379
        REDIS_DB = 0

        DEFAULT_CACHE_TIMEOUT = 300


    **Example - Extract Redis settings**::

        >>> # noinspection PyUnresolvedReferences
        >>> from myapp import settings
        >>> from privex.helpers import extract_settings
        >>>
        >>> # All keyword arguments (apart from _settings_mod and _keys_lower) are converted into a dictionary
        >>> # and merged with the extracted settings
        >>> # noinspection PyTypeChecker
        >>> extract_settings('REDIS_', _settings=settings, port=6479, debug=True)
        {'host': 'localhost', 'port': 6379, 'db': 0, 'debug': True}
        >>> extract_settings('REDIS_', _settings=settings, merge_conf=dict(port=6479))
        {'host': 'localhost', 'port': 6479, 'db': 0}


    **Example - Extract Redis settings - case sensitive mode**::

        >>> extract_settings('REDIS_', _settings=settings, _case_sensitive=True)
        {'HOST': 'localhost', 'PORT': 6379, 'DB': 0}


    **Example - Extract database settings from the environment**

    The below dict comprehension is just so you can see the original environment keys before we run ``extract_settings``::

        >>> import os
        >>> from privex.helpers import extract_settings
        >>>
        >>> {k: v for k,v in os.environ.items() if 'DB_' in k}
        {'DB_USER': 'root',
         'DB_PASS': 'ExamplePass',
         'DB_NAME': 'example_db'}


    We'll now call ``extract_settings`` using :attr:`os.environ` converted into a dictionary, and attempt to quickly
    obtain the database settings - with lowercase keys, and without their ``DB_`` prefix.

    Below, you'll see extract_settings extracted all keys starting with DB_, removed the DB_ prefix, converted the
    remaining portion of the key to lowercase, and also merged in the default setting 'host' since DB_HOST didn't exist.

    The outputted dictionary is perfect for passing to many database library constructors::

        >>> extract_settings('DB_', dict(os.environ), host='localhost')
        {'user': 'root',
         'pass': 'ExamplePass',
         'name': 'example_db',
         'host': 'localhost'}


    :param str prefix: The prefix (including the first underscore (``_``) or other separator) to search for in the settings
    :param Module|dict|object _settings: The object to extract the settings from. The object can be one of the following:

         * A ``module``, for example passing ``settings`` after running ``from myapp import settings``

         * A ``dict``, for example ``extract_settings('X_', dict(X_A=1, X_B=2))``

         * A class which has the desired settings defined on it's ``.__dict__`` (e.g. any standard user
           class - ``class MyClass:``, with settings defined as static class attributes)

         * An instance of a class, which has all desired settings defined inside of ``.__dict__`` (e.g. any standard user class instance,
           with static and/or instance attributes for each setting)

         * Any other type which supports being casted to a dictionary via ``dict(obj)``.


    :param dict merge_conf: Optionally you may specify a dictionary of "override" settings to merge with the extracted settings.
                            The values in this dictionary take priority over both ``defaults``, and the keys from ``_settings``.

    :param dict defaults:   Optionally you may specify a dictionary of default settings to merge **before** the extracted settings,
                            meaning values are only used if the key wasn't present in the extracted settings nor ``merge_conf``.

    :param kwargs: Additional settings as keyword arguments (see below). Any keyword argument keys which aren't valid settings will
                   be added to the ``defaults`` dictionary.
                   This means that defaults can also be specified as kwargs - as long as they don't clash with any
                   used kwarg settings (see below).

    :key _case_sensitive: (Default ``False``) If ``True``, ``prefix`` is compared against ``_settings`` keys case sensitively.
                          If ``False``, then both ``prefix`` and each ``_settings`` key is converted to lowercase before comparison.

    :key _keys_lower:     Defaults to ``True`` if _case_sensitive is False, and ``False`` if _case_sensitive is True.
                          If ``True``, each extracted settings key is converted to lowercase before returning them - otherwise they're
                          returned with the same case as they were in ``_settings``.

    :return dict config:  The extracted configuration keys (without their prefixes) and values as a dictionary.
                          Based on the extracted keys from ``_settings``, the fallback settings in ``defaults`` (and excess ``kwargs``),
                          plus the override settings in ``merge_conf``.
    """
    case_sensitive = kwargs.pop('_case_sensitive', False)
    keys_lower = kwargs.pop('_keys_lower', not case_sensitive)
    
    defaults = {} if defaults is None else dict(defaults)
    merge_conf = {} if merge_conf is None else dict(merge_conf)
    
    if isinstance(_settings, dict):
        set_dict = dict(_settings)
    elif type(_settings).__name__ == 'module' or isinstance(_settings, object) or inspect.isclass(_settings):
        set_dict = dict(_settings.__dict__)
    else:
        try:
            # noinspection PyTypeChecker
            set_dict = dict(_settings)
            # noinspection PyTypeChecker
            if len(set_dict.keys()) < 1 <= len(_settings): raise Exception()
        except Exception:
            set_dict = dict(_settings.__dict__)
    
    set_conf = {}
    for k, v in set_dict.items():
        l = len(prefix)
        matched = (k[:l] == prefix) if case_sensitive else (k[:l].lower() == prefix.lower())
        if matched:
            _key = k[l:]
            _key = _key.lower() if keys_lower else _key
            set_conf[_key] = v
    
    return {**defaults, **set_conf, **kwargs, **merge_conf}


def dec_round(amount: Decimal, dp: int = 2, rounding=None) -> Decimal:
    """
    Round a Decimal to x decimal places using ``quantize`` (``dp`` must be >= 1 and the default dp is 2)

    If you don't specify a rounding option, it will use whatever rounding has been set in :py:func:`decimal.getcontext`
    (most python versions have this default to ``ROUND_HALF_EVEN``)

    Basic Usage:

        >>> from decimal import Decimal, getcontext, ROUND_FLOOR
        >>> x = Decimal('1.9998')
        >>> dec_round(x, 3)
        Decimal('2.000')

    Custom Rounding as an argument:

        >>> dec_round(x, 3, rounding=ROUND_FLOOR)
        Decimal('1.999')

    Override context rounding to set the default:

        >>> getcontext().rounding = ROUND_FLOOR
        >>> dec_round(x, 3)
        Decimal('1.999')


    :param Decimal   amount: The amount (as a Decimal) to round
    :param int           dp: Number of decimal places to round ``amount`` to. (Default: 2)
    :param str     rounding: A :py:mod:`decimal` rounding option, e.g. ``ROUND_HALF_EVEN`` or ``ROUND_FLOOR``
    :return Decimal rounded: The rounded Decimal amount
    """
    dp = int(dp)
    if dp <= 0:
        raise ArithmeticError('dec_round expects dp >= 1')
    rounding = getcontext().rounding if not rounding else rounding
    dp_str = '.' + str('0' * (dp - 1)) + '1'
    return Decimal(amount).quantize(Decimal(dp_str), rounding=rounding)


def chunked(iterable, n):
    """ Split iterable into ``n`` iterables of similar size

    Examples::
        >>> l = [1, 2, 3, 4]
        >>> list(chunked(l, 4))
        [[1], [2], [3], [4]]

        >>> l = [1, 2, 3]
        >>> list(chunked(l, 4))
        [[1], [2], [3], []]

        >>> l = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        >>> list(chunked(l, 4))
        [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]

    Taken from: https://stackoverflow.com/a/24484181/2648583

    """
    chunksize = int(math.ceil(len(iterable) / n))
    return (iterable[i * chunksize:i * chunksize + chunksize] for i in range(n))


def inject_items(items: list, dest_list: list, position: int) -> List[str]:
    """
    Inject a list ``items`` after a certain element in ``dest_list``.
    
    **NOTE:** This does NOT alter ``dest_list`` - it returns a **NEW list** with ``items`` injected after the
    given ``position`` in ``dest_list``.
    
    **Example Usage**::

        >>> x = ['a', 'b', 'e', 'f', 'g']
        >>> y = ['c', 'd']
        >>> # Inject the list 'y' into list 'x' after element 1 (b)
        >>> inject_items(y, x, 1)
        ['a', 'b', 'c', 'd', 'e', 'f', 'g']
    
    :param list items: A list of items to inject into ``dest_list``
    :param list dest_list: The list to inject ``items`` into
    :param int position: Inject ``items`` after this element (0 = 1st item) in ``dest_list``
    :return List[str] injected: :py:attr:`.dest_list` with the passed ``items`` list injected at ``position``
    """
    before = list(dest_list[0:position+1])
    after = list(dest_list[position+1:])
    return before + items + after


def byteify(data: Optional[Union[str, bytes]], encoding='utf-8', if_none=None) -> bytes:
    """
    Convert a piece of data into bytes if it isn't already::
        
        >>> byteify("hello world")
        b"hello world"
    
    By default, if ``data`` is ``None``, then a :class:`TypeError` will be raised by :func:`bytes`.
    
    If you'd rather convert ``None`` into a blank bytes string, use ``if_node=""``, like so::
        
        >>> byteify(None)
        TypeError: encoding without a string argument
        >>> byteify(None, if_none="")
        b''
    
    """
    if data is None and if_none is not None:
        return bytes(if_none, encoding) if type(if_none) is not bytes else if_none
    return bytes(data, encoding) if type(data) is not bytes else data


def stringify(data: Optional[Union[str, bytes]], encoding='utf-8', if_none=None) -> str:
    """
    Convert a piece of data into a string (from bytes) if it isn't already::

        >>> stringify(b"hello world")
        "hello world"
    
    By default, if ``data`` is ``None``, then ``None`` will be returned.
    
    If you'd rather convert ``None`` into a blank string, use ``if_node=""``, like so::
        
        >>> repr(stringify(None))
        'None'
        >>> stringify(None, if_none="")
        ''
    
    """
    if data is None: return if_none
    return data.decode(encoding) if type(data) is bytes else data


class ErrHelpParser(argparse.ArgumentParser):
    """
    ErrHelpParser - Use this instead of :py:class:`argparse.ArgumentParser` to automatically get full
    help output as well as the error message when arguments are invalid, instead of just an error message.

    >>> parser = ErrHelpParser(description='My command line app')
    >>> parser.add_argument('nums', metavar='N', type=int, nargs='+')

    """
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)


first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def camel_to_snake(name: STRBYTES) -> str:
    """
    Convert ``name`` from camel case (``HelloWorld``) to snake case (``hello_world``).
    
    ``name`` can be either a ``str`` or ``bytes``.
    
    Example::
    
        >>> camel_to_snake("HelloWorldLoremIpsum")
        'hello_world_lorem_ipsum'
    
    
    :param str|bytes name: A camel case (class style) name, e.g. ``HelloWorld``
    :return str snake_case: ``name`` converted to snake case ``hello_world``
    """

    s1 = first_cap_re.sub(r'\1_\2', stringify(name))
    return all_cap_re.sub(r'\1_\2', s1).lower()


def human_name(class_name: Union[str, bytes, callable, Type[object]]) -> str:
    """
    This function converts a class/function name into a Title Case name. It also directly accepts classes/functions.
    
    Input names can be either snake case ``my_function``, or InitialCaps ``MyClass`` - though mixtures of the two
    may work, such as ``some_functionName`` - however ``some_FunctionName`` will not (causes double spaces).
    
    **Examples**
    
    Using a plain string or bytes::
    
        >>> human_name(b'_some_functionName')
        'Some Function Name'
        >>> human_name('SomeClassName')
        'Some Class Name'
    
    Using a reference to a function::
    
        >>> def some_func():
        ...     pass
        >>> human_name(some_func)
        'Some Func'
    
    Using a reference to a class, or an instance of a class::
    
        >>> class MyExampleClass:
        ...     pass
        >>> my_instance = MyExampleClass()
        >>> human_name(MyExampleClass)
        'My Example Class'
        >>> human_name(my_instance)
        'My Example Class'
    
    :param class_name: The name of a class/function specified either in InitialCaps or snake_case.
                       You may also pass a function reference, class reference, or class instance. (see examples)
    :return str human_name: The humanised Title Case name of ``class_name``
    """
    # First we figure out what type ``class_name`` actually **is**.
    # Bytes simply get decoded back into a string, while strings are untouched
    if type(class_name) in [str, bytes]:
        class_name = stringify(class_name)
    # References to classes (not instances) and functions means we need .__name__
    elif type(class_name) is type or str(type(class_name)) == "<class 'function'>":
        class_name = class_name.__name__
    # If it's not a class/function reference, but is an instance of object, then it's a class instance.
    elif isinstance(class_name, object):
        class_name = class_name.__class__.__name__

    # Then we convert it into a normal string.
    class_name = str(class_name)
    
    # Strip any underlines at the start or end of the class name.
    name = class_name.strip('_').strip('-')
    # We can't alter an object as we iterate it, so we copy `name` into a new list which we'll modify instead
    new_name = list(name)
    
    # Capitalise the first letter of the name, if it isn't already.
    if name[0].islower():
        new_name[0] = name[0].upper()

    # When we inject spaces where there weren't any before, we need to track how this changes the length,
    # so that we can correctly reference positions in `new_name`
    offset = 0
    # Iterate over each character in the original name (ignoring the first letter because it's probably capital)
    for i, c in enumerate(name[1:]):
        pos = (i + 1) + offset
        # If the current character is uppercase, then inject a space before this character and increment `offset`
        if c.isupper():
            new_name = inject_items([' '], new_name, pos - 1)
            offset += 1
            continue
        # If the character is an underline or dash, replace it with a space, and uppercase the character in-front of it.
        if c in ['_', '-']:
            new_name[pos] = ' '
            if str(name[i + 2]).isalpha():
                new_name[pos + 1] = new_name[pos + 1].upper()
    
    return ''.join(new_name).strip()


def shell_quote(*args: str) -> str:
    """
    Takes command line arguments as positional args, and properly quotes each argument to make it safe to
    pass on the command line. Outputs a string containing all passed arguments properly quoted.
    
    Uses :func:`shlex.join` on Python 3.8+, and a for loop of :func:`shlex.quote` on older versions.
    
    Example::
    
        >>> print(shell_quote('echo', '"orange"'))
        echo '"orange"'
    
    
    """
    return shlex.join(args) if hasattr(shlex, 'join') else " ".join([shlex.quote(a) for a in args]).strip()


def call_sys(proc, *args, write: STRBYTES = None, **kwargs) -> Tuple[bytes, bytes]:
    """
    A small wrapper around :class:`subprocess.Popen` which allows executing processes, while optionally piping
    data (``write``) into the process's stdin, then finally returning the process's output and error results.
    Designed to be easier to use than using :class:`subprocess.Popen` directly.
    
    **Using AsyncIO?** - there's a native python asyncio version of this function available in :func:`.call_sys_async`,
    which uses the native :func:`asyncio.subprocess.create_subprocess_shell`, avoiding blocking IO.
    
    By default, ``stdout`` and ``stdin`` are set to :attr:`subprocess.PIPE` while stderr defaults to
    :attr:`subprocess.STDOUT`. You can override these by passing new values as keyword arguments.
    
    **NOTE:** The first positional argument is executed, and all other positional arguments are passed to the process
    in the order specified. To use call_sys's arguments ``write``, ``stdout``, ``stderr`` and/or ``stdin``, you
    **MUST** specify them as keyword arguments, otherwise they'll just be passed to the process you're executing.
    
    Any keyword arguments not specified in the ``:param`` or ``:key`` pydoc specifications will simply be forwarded to
    the :class:`subprocess.Popen` constructor.
    
    **Simple Example**::
        
        >>> # All arguments are automatically quoted if required, so spaces are completely fine.
        >>> folders, _ = call_sys('ls', '-la', '/tmp/spaces are fine/hello world')
        >>> print(stringify(folders))
        backups  cache   lib  local  lock  log  mail  opt  run  snap  spool  tmp
    
    **Piping data into a process**::
    
        >>> data = "hello world"
        >>> # The data "hello world" will be piped into wc's stdin, and wc's stdout + stderr will be returned
        >>> out, _ = call_sys('wc', '-c', write=data)
        >>> int(out)
        11
    
    
    
    :param str proc: The process to execute.
    :param str args: Any arguments to pass to the process ``proc`` as positional arguments.
    :param bytes|str write: If this is not ``None``, then this data will be piped into the process's STDIN.
    
    :key stdout: The subprocess file descriptor for stdout, e.g. :attr:`subprocess.PIPE` or :attr:`subprocess.STDOUT`
    :key stderr: The subprocess file descriptor for stderr, e.g. :attr:`subprocess.PIPE` or :attr:`subprocess.STDOUT`
    :key stdin: The subprocess file descriptor for stdin, e.g. :attr:`subprocess.PIPE` or :attr:`subprocess.STDIN`
    :key cwd: Set the current/working directory of the process to this path, instead of the CWD of your calling script.
    
    :return tuple output: A tuple containing the process output of stdout and stderr
    """
    stdout, stderr, stdin = kwargs.pop('stdout', PIPE), kwargs.pop('stderr', STDOUT), kwargs.pop('stdin', PIPE)
    args = [proc] + list(args)
    handle = subprocess.Popen(args, stdout=stdout, stderr=stderr, stdin=stdin, **kwargs)
    stdout, stderr = handle.communicate(input=byteify(write)) if write is not None else handle.communicate()
    return stdout, stderr


def reverse_io(f: BinaryIO, blocksize: int = 4096) -> Generator[bytes, None, None]:
    """
    Read file as series of blocks from end of file to start.

    The data itself is in normal order, only the order of the blocks is reversed.
    ie. "hello world" -> ["ld","wor", "lo ", "hel"]
    Note that the file must be opened in binary mode.

    Original source: https://stackoverflow.com/a/136354
    """
    if 'b' not in f.mode.lower():
        raise Exception("File must be opened using binary mode.")
    size = os.stat(f.name).st_size
    fullblocks, lastblock = divmod(size, blocksize)
    
    # The first(end of file) block will be short, since this leaves
    # the rest aligned on a blocksize boundary.  This may be more
    # efficient than having the last (first in file) block be short
    f.seek(-lastblock, 2)
    yield f.read(lastblock)
    
    for i in range(fullblocks - 1, -1, -1):
        f.seek(i * blocksize)
        yield f.read(blocksize)


def io_tail(f: BinaryIO, nlines: int = 20, bsz: int = 4096) -> Generator[List[str], None, None]:
    """
    NOTE: If you're only loading a small amount of lines, e.g. less than 1MB, consider using the much easier :func:`.tail`
          function - it only requires one call and returns the lines as a singular, correctly ordered list.
    
    This is a generator function which works similarly to ``tail`` on UNIX systems. It efficiently retrieves lines in reverse order using
    the passed file handle ``f``.
    
    WARNING: This function is a generator which returns "chunks" of lines - while the lines within each chunk are in the correct order,
    the chunks themselves are backwards, i.e. each chunk retrieves lines prior to the previous chunk.
    
    This function was designed as a generator to allow for **memory efficient handling of large files**, and tailing large amounts of lines.
    It only loads ``bsz`` bytes from the file handle into memory with each iteration, allowing you to process each chunk of lines as
    they're read from the file, instead of having to load all ``nlines`` lines into memory at once.
    
    To ensure your retrieved lines are in the correct order, with each iteration you must PREPEND the outputted chunk to your final result,
    rather than APPEND. Example::
     
        >>> from privex.helpers import io_tail
        >>> lines = []
        >>> with open('/tmp/example', 'rb') as fp:
        ...     # We prepend each chunk from 'io_tail' to our result variable 'lines'
        ...     for chunk in io_tail(fp, nlines=10):
        ...         lines = chunk + lines
        >>> print('\\n'.join(lines))

    Modified to be more memory efficient, but originally based on this SO code snippet: https://stackoverflow.com/a/136354

    :param BinaryIO f: An open file handle for the file to tail, must be in **binary mode** (e.g. ``rb``)
    :param int nlines: Total number of lines to retrieve from the end of the file
    :param int bsz:    Block size (in bytes) to load with each iteration (default: 4096 bytes). DON'T CHANGE UNLESS YOU
                       UNDERSTAND WHAT THIS MEANS.
    :return Generator chunks: Generates chunks (in reverse order) of correctly ordered lines as ``List[str]``
    """
    buf = ''
    lines_read = 0
    # Load 4096 bytes at a time, from file handle 'f' in reverse
    for block in reverse_io(f, blocksize=int(bsz)):
        # Incase we had a partial line during our previous iteration, we append leftover bytes from
        # the previous iteration to the end of the newly loaded block
        buf = stringify(block) + buf
        lines = buf.splitlines()
    
        # Return all lines except the first (since may be partial)
        if lines:
            # First line may not be complete, since we're loading blocks from the bottom of the file.
            # We yield from line 2 onwards, storing line 1 back into 'buf' to be appended to the next block.
            result = lines[1:]
            res_lines = len(result)
        
            # If we've retrieved enough lines to meet the requested 'nlines', then we just calculate how many
            # more lines the caller wants, yield them, then return to finish execution.
            if (lines_read + res_lines) >= nlines:
                rem_lines = nlines - lines_read
                lines_read += rem_lines
                yield result[-rem_lines:]
                return
        
            # Yield the lines we've loaded so far
            if res_lines > 0:
                lines_read += res_lines
                yield result
        
            # Replace the buffer with the discarded 1st line from earlier.
            buf = lines[0]
    # If the loop is broken, it means we've probably reached the start of the file, and we're missing the first line...
    # Thus we have to yield the buffer, which should contain the first line of the file.
    yield [buf]


def tail(filename: str, nlines: int = 20, bsz: int = 4096) -> List[str]:
    """
    Pure python equivalent of the UNIX ``tail`` command. Simply pass a filename and the number of lines you want to load
    from the end of the file, and a ``List[str]`` of lines (in forward order) will be returned.
    
    This function is simply a wrapper for the highly efficient :func:`.io_tail`, designed for usage with a small (<10,000) amount
    of lines to be tailed. To allow for the lines to be returned in the correct order, it must load all ``nlines`` lines into memory
    before it can return the data.
    
    If you need to ``tail`` a large amount of data, e.g. 10,000+ lines of a logfile, you should consider using the lower level
    function :func:`.io_tail` - which acts as a generator, only loading a certain amount of bytes into memory per iteration.
    
    Example file ``/tmp/testing``::
        
        this is an example 1
        this is an example 2
        this is an example 3
        this is an example 4
        this is an example 5
        this is an example 6
    
    Example usage::
    
        >>> from privex.helpers import tail
        >>> lines = tail('/tmp/testing', nlines=3)
        >>> print("\\n".join(lines))
        this is an example 4
        this is an example 5
        this is an example 6
    
    
    :param str filename: Path to file to tail. Relative or absolute path. Absolute path is recommended for safety.
    :param int nlines:   Total number of lines to retrieve from the end of the file
    :param int bsz:      Block size (in bytes) to load with each iteration (default: 4096 bytes). DON'T CHANGE UNLESS YOU
                         UNDERSTAND WHAT THIS MEANS.
    :return List[str] lines: The last 'nlines' lines of the file 'filename' - in forward order.
    """
    res = []
    with open(filename, 'rb') as fp:
        for chunk in io_tail(f=fp, nlines=nlines, bsz=bsz):
            res = chunk + res
    return res


def filter_form(form: Mapping, *keys, cast: callable = None) -> Dict[str, Any]:
    """
    Extract the keys ``keys`` from the dict-like ``form`` if they exist and return a dictionary containing the keys and values found.

    Optionally, if ``cast`` isn't ``None``, then ``cast`` will be called to cast each ``form`` value to the desired type,
    e.g. ``int``, ``Decimal``, or ``str``.

    Example usage::
    
        >>> a = dict(a=1, c=2, d=3)
        >>> filter_form(a, 'a', 'c', 'e')
        {'a': 1, 'c': 2}
        >>> b = dict(lorem=1, ipsum='2', dolor=5.67)
        >>> filter_form(b, 'lorem', 'ipsum', 'dolor', cast=int)
        {'lorem': 1, 'ipsum': 2, 'dolor': 5}


    :param Mapping form: A dict-like object to extract ``key`` from.
    :param str|Any keys: One or more keys to extract from ``form``
    :param callable cast: Cast the value of any extract ``form`` key using this callable
    :return dict filtered_form: A dict containing the extracted keys and respective values from ``form``
    """
    filtered = {k: form[k] for k in keys if k in form}
    if cast is not None:
        filtered = {k: cast(v) for k, v in filtered.items()}
    return filtered


def almost(compare: NumberStr, *numbers: NumberStr, tolerance: NumberStr = Decimal('0.01'), **kwargs) -> bool:
    """
    Compare two or more numbers, returning ``True`` if all ``numbers`` are no more than ``tolerance``
    greater or smaller than than ``compare`` - otherwise ``False``.
    
    Works similarly to :py:meth:`unittest.TestCase.assertAlmostEqual`
    
    Basic usage with two numbers + default tolerance (``0.01``)::
    
        >>> almost('5', '5.001')
        True
        >>> almost('5', '5.5')
        False
    
    Multiple numbers + custom tolerance::
    
        >>> almost('5', '5.14', '4.85', '5.08', tolerance=Decimal('0.2'))
        True
        >>> almost('5', '5.3', '4.85', '5.08', tolerance=Decimal('0.2'))
        False
    
    Using ``fail`` or ``test``::
        
        >>> # By passing ``fail=True``, a descriptive AssertionError is raised when the tolerance check fails.
        >>> almost('5', '5.01', fail=True)
        True
        >>> almost('5', '5.02', fail=True)
        Traceback (most recent call last):
          File "<stdin>", line 1, in <module>
          File "privex/helpers/common.py", line 1044, in almost
            raise AssertionError(
        AssertionError: Number at position 0 (val: 5.02) failed tolerance (0.01) check against 5
        >>> # By passing ``test=True``, a standard ``assert`` will be used to compare the numbers.
        >>> almost('5', '5.01', test=True)
        True
        >>> almost('5', '5.02', test=True)
        Traceback (most recent call last):
          File "<stdin>", line 1, in <module>
          File "privex/helpers/common.py", line 1041, in almost
            assert (x - tolerance) <= compare <= (x + tolerance)
        AssertionError

    
    :param Decimal|int|float compare: The base number which all ``numbers`` will be compared against.
    :param Decimal|int|float numbers: One or more numbers to compare against ``compare``
    :param Decimal|int|float tolerance: (kwarg only) Amount that each ``numbers`` can be greater/smaller than ``compare`` before
                                        returning ``False``.
    :keyword bool fail: (default: ``False``) If true, will raise :class:`.AssertionError` on failed tolerance check, instead of
                        returning ``False``. (mutually exclusive with ``assert``)
    :keyword bool test: (default: ``False``) If true, will use ``assert`` instead of testing with ``if``. Useful in unit tests.
                        (mutually exclusive with ``raise``)
    :raises AttributeError: When less than 1 number is present in ``numbers``
    :raises AssertionError: When kwarg ``raise`` is ``True`` and one or more numbers failed the tolerance check.
    :return bool is_almost: ``True`` if all ``numbers`` are within ``tolerance`` of ``compare``, ``False`` if one or more ``numbers``
                            is outside of the tolerance.
    """
    
    if len(numbers) < 1:
        raise AttributeError(
            f'privex.helpers.common.almost expects at least ONE number to compare.'
        )
    
    numbers = [Decimal(n) for n in numbers]
    compare, tolerance = Decimal(compare), Decimal(tolerance)
    
    should_raise, should_assert = kwargs.get('fail', False), kwargs.get('test', False)
    
    for i, x in enumerate(numbers):
        if should_assert:
            assert (x - tolerance) <= compare <= (x + tolerance)
        elif not ((x - tolerance) <= compare <= (x + tolerance)):
            if should_raise:
                raise AssertionError(
                    f"Number at position {i} (val: {x}) failed tolerance ({tolerance}) check against {compare}"
                )
            return False
    
    return True


IS_XARGS = re.compile('^\*([a-zA-Z0-9_])+$')
"""Pre-compiled regex for matching catch-all positional argument parameter names like ``*args``"""
IS_XKWARGS = re.compile('^\*\*([a-zA-Z0-9_])+$')
"""Pre-compiled regex for matching catch-all keyword argument parameter names like ``**args``"""
T_PARAM = inspect.Parameter
"""Type alias for :class:`inspect.Parameter`"""
T_PARAM_LIST = Union[Dict[str, T_PARAM], List[T_PARAM], Iterable[T_PARAM]]
"""
Type alias for dict's containing strings mapped to :class:`inspect.Parameter`'s, lists of just
:class:`inspect.Parameter`'s, and any iterable of :class:`inspect.Parameter`
"""

# noinspection PyProtectedMember
INS_EMPTY = inspect._empty
"""
Type alias for :class:`inspect.empty`
"""


def _filter_params(params: T_PARAM_LIST, ignore_xargs=False, ignore_xkwargs=False, **kwargs) -> Dict[str, T_PARAM]:
    """
    Filter an iterable containing :class:`inspect.Parameter`'s, returning a :class:`.DictObject` containing
    parameter names mapped to their :class:`inspect.Parameter` object.
    
    **Examples**
    
    Function ``some_func`` is used as an example.
    
        >>> import inspect
        >>> def some_func(x, y, z=123, *args, **kwargs):
        ...     pass
        >>> params = inspect.signature(some_func).parameters
    
    With just parameters, no filtering is done. Only scanning the parameters and returning them as a dict::
    
        >>> _filter_params(params)
        {'x': <Parameter "x">, 'y': <Parameter "y">, 'z': <Parameter "z=123">,
         '*args': <Parameter "*args">, '**kwargs': <Parameter "**kwargs">}
    
    With the arguments ``ignore_xargs=True`` and ``ignore_xkwargs=True``, this strips away any catch-all parameters
    e.g. ``*args`` / ``**kwargs``. Example::
    
        >>> _filter_params(params, ignore_xargs=True, ignore_xkwargs=True)
        {'x': <Parameter "x">, 'y': <Parameter "y">, 'z': <Parameter "z=123">}
    
    With the arguments ``ignore_defaults=True`` and ``ignore_positional=True``, this strips away all normal positional
    and keyword parameters - leaving only catch-all parameters for positional/keyword arguments. Example::
    
        >>> _filter_params(params, ignore_defaults=True, ignore_positional=True)
        {'*args': <Parameter "*args">, '**kwargs': <Parameter "**kwargs">}
    
    
    :param params: An iterable of :class:`inspect.Parameter`'s, e.g. from ``inspect.signature(func).parameters``
    :param bool ignore_xargs: Filter out any catch-all positional arguments (e.g. ``*args``)
    :param bool ignore_xkwargs: Filter out any catch-all keyword arguments (e.g. ``**kwargs``)
    
    :key bool ignore_defaults: Filter out any parameter which has a default value (e.g. args usable as kwargs)
    :key bool ignore_positional: Filter out any parameter which doesn't have a default value (mandatory args)
    
    :return DictObject filtered: A dictionary of filtered params, mapping param names to Parameter objects.
    """
    ignore_defaults = kwargs.pop('ignore_defaults', False)
    ignore_positional = kwargs.pop('ignore_positional', False)
    

    
    _params = params
    if isinstance(params, (dict, OrderedDict)) or hasattr(params, 'values'):
        _params = params.values()
    
    _is_xargs = lambda param: IS_XARGS.search(str(param)) is not None
    _is_xkwargs = lambda param: IS_XKWARGS.search(str(param)) is not None
    _is_x_arg = lambda param: _is_xargs(param) or _is_xkwargs(param)
    _def_empty = lambda param: empty(param.default) or param.default is INS_EMPTY
    
    filtered = DictObject()
    for p in _params:   # type: inspect.Parameter
        if ignore_xargs and _is_xargs(p): continue
        if ignore_xkwargs and _is_xkwargs(p): continue
        # x-args (*args / **kwargs) cannot count as defaults / positionals and shouldn't be counted in this IGNORE.
        if ignore_defaults and not _def_empty(p) and not _is_x_arg(p): continue
        if ignore_positional and _def_empty(p) and not _is_x_arg(p): continue
        param_name = str(p) if '=' not in str(p) else p.name
        filtered[param_name] = p
    
    return filtered


T_PARAM_DICT = Union[
    Dict[str, T_PARAM],
    DictObject,
    Dict[type, Dict[str, T_PARAM]]
]
"""
Type alias for dict's mapping parameter names to :class:`inspect.Parameter`'s, :class:`.DictObject`'s,
and dict's mapping classes to dict's mapping parameter names to :class:`inspect.Parameter`'s.
"""


def get_function_params(obj: Union[type, callable], check_parents=False, **kwargs) -> T_PARAM_DICT:
    """
    Extracts a function/method's signature (or class constructor signature if a class is passed), and returns
    it as a dictionary.
    
    Primarily used by :func:`.construct_dict` - but may be useful for other purposes.
    
    If you've passed a class, you can set ``check_parents`` to ``True`` to obtain the signatures of the passed
    class's constructor AND all of it's parent classes, returned as a dictionary mapping classes to dictionaries
    of parameters.
    
    If you've set ``check_parents`` to ``True``, but you want the parameters to be a flat dictionary (just like when
    passing a function or class without check_parents), you can also pass ``merge=True``, which merges each class's
    constructor parameters into a dictionary mapping names to :class:`inspect.Parameter` objects.
    
    If any parameters conflict, children's constructor parameters always take precedence over their parent's version,
    much in the same way that Python's inheritance works.
    
    **Basic (with functions)**::

        
        >>> def some_func(x, y, z=123, *args, **kwargs):
        ...    pass
    
    Get all normal parameters (positional and kwargs - excluding catch-all ``*args`` / ``**kwargs`` parameter types)::
    
        >>> params = get_function_params(some_func)
        >>> params
        {'x': <Parameter "x">, 'y': <Parameter "y">, 'z': <Parameter "z=123">}
    
    Get raw parameter name and value (as written in signature) / access default values::
        
        >>> str(params.z.name)     # You can also access it via params['z']
        'z=123'
        >>> params.z.default  # You can also access it via params['z']
        123

    Get only **required** parameters::
        
        >>> get_function_params(some_func, ignore_defaults=True)
        {'x': <Parameter "x">, 'y': <Parameter "y">}
    
    Get only parameters with defaults::
    
        >>> get_function_params(some_func, ignore_positional=True)
        {'z': <Parameter "z=123">}
    
    
    **Example Usage (with classes and sub-classes)**::
    
        >>> class BaseClass:
        ...     def __init__(self, a, b, c=1234, **kwargs):
        ...         pass
        
        >>> class Example(BaseClass):
        ...     def __init__(self, d, e='hello', f=None, a='overridden', **kwargs):
        ...         super().__init__(a=a, d=d, e=e, f=f, **kwargs)
    
    If we pass the class ``Example`` on it's own, we get a dictionary of just it's own parameters::
    
        >>> get_function_params(Example)
        {'d': <Parameter "d">, 'e': <Parameter "e='hello'">, 'f': <Parameter "f=None">}
    
    However, if we set ``check_parents=True``, we now get a dictionary containing ``Example``'s constructor parameters,
    AND ``BaseClass``'s (it's parent class) constructor parameters, organised by class::
        
        >>> get_function_params(Example, True)
        {
            <class '__main__.Example'>: {
                'd': <Parameter "d">, 'e': <Parameter "e='hello'">, 'f': <Parameter "f=None">,
                'a': <Parameter "a='overridden'">
            },
            <class '__main__.BaseClass'>: {'a': <Parameter "a">, 'b': <Parameter "b">, 'c': <Parameter "c=1234">}
        }
    
    We can also add the optional kwarg ``merge=True``, which merges the parameters of the originally passed class,
    and it's parents.
    
    This is done in reverse order, so that children's conflicting constructor parameters take priority over their
    parents, as can be seen below with ``a`` which is shown as ``a='overridden'`` - the overridden parameter
    of the class ``Example`` with a default value, instead of the parent's ``a`` which makes ``a`` mandatory::
     
        >>> get_function_params(Example, True, merge=True)
        {
            'a': <Parameter "a='overridden'">, 'b': <Parameter "b">, 'c': <Parameter "c=1234">,
            'd': <Parameter "d">, 'e': <Parameter "e='hello'">, 'f': <Parameter "f=None">
        }
    
    
    :param type|callable obj: A class (not an instance) or callable (function / lambda) to extract and filter the
                              parameter's from. If a class is passed, the parameters of the constructor will be
                              returned (``__init__``), excluding the initial ``self`` parameter.
    
    :param bool check_parents: (Default: ``False``) If ``obj`` is a class and this is True, will recursively grab
        the constructor parameters for all parent classes, and return the parameters as a dictionary of
        ``{<class X>: {'a': <Parameter 'a'>}, <class Y>: {'b': <Parameter 'b'>}``, unless ``merge`` is also set
        to ``True``.
    
    :key bool ignore_xargs: (Default: ``True``) Filter out any catch-all positional arguments (e.g. ``*args``)
    :key bool ignore_xkwargs: (Default: ``True``) Filter out any catch-all keyword arguments (e.g. ``**kwargs``)
    
    :key bool ignore_defaults: (Default: ``False``) Filter out any parameter which has a default
                               value (e.g. args usable as kwargs)
    
    :key bool ignore_positional: (Default: ``False``) Filter out any parameter which doesn't have a default
                                 value (mandatory args)
    
    :key bool merge: (Default: ``False``) If this is True, when ``check_parents`` is enabled, all parameters will
                     be flatted into a singular dictionary, e.g. ``{'a': <Parameter 'a'>, 'b': <Parameter "b">}``
    
    :return:
    """
    merge = kwargs.pop('merge', False)
    filter_opts = dict(**kwargs)
    filter_opts['ignore_xargs'] = filter_opts.get('ignore_xargs', True)
    filter_opts['ignore_xkwargs'] = filter_opts.get('ignore_xkwargs', True)
    
    _cls_keys = inspect.signature(obj).parameters
    cls_keys = _filter_params(inspect.signature(obj).parameters, **filter_opts)
    if check_parents and hasattr(obj, '__base__') and inspect.isclass(obj):
        ret = OrderedDictObject({obj: cls_keys})
        last_parent = obj.__base__
        while last_parent not in [None, type, object]:
            try:
                ret[last_parent] = _filter_params(
                    inspect.signature(last_parent).parameters, **filter_opts
                )
                if not hasattr(last_parent, '__base__'):
                    last_parent = None
                    continue
                last_parent = last_parent.__base__
            except (Exception, BaseException) as e:
                log.warning("Finishing check_parents loop due to exception: %s - %s", type(e), str(e))
                last_parent = None
                continue
        
        if merge:
            merged = OrderedDictObject()
            for cls in reversed(ret):
                for k, p in ret[cls].items():
                    merged[k] = p
            return merged
            
        return ret
    
    return OrderedDictObject(cls_keys)


def construct_dict(cls: Union[Type[T], C], kwargs: dict, args: Iterable = None, check_parents=True) -> Union[T, Any]:
    """
    Removes keys from the passed dict ``data`` which don't exist on ``cls`` (thus would get rejected as kwargs)
    using :func:`.get_function_params`. Then create and return an instance of ``cls``, passing the filtered
    ``kwargs`` dictionary as keyword args.

    Ensures that any keys in your dictionary which don't exist on ``cls`` are automatically filtered out, instead
    of causing an error due to unexpected keyword arguments.

    **Example - User class which only takes specific arguments**
    
    First let's define a class which only takes three arguments in it's constructor - username, first_name, last_name.

        >>> class User:
        ...    def __init__(self, username, first_name=None, last_name=None):
        ...        self.username = username
        ...        self.first_name, self.last_name = first_name, last_name
        ...
    
    Now we'll create a dictionary which has those three arguments, but also the excess ``address`` and ``phone``.
    
        >>> data = dict(username='johndoe123', first_name='John', last_name='Doe',
        ...             address='123 Example St', phone='+1-123-000-1234')
    
    If we tried to directly pass data as keyword args, we'd get an error::
     
        >>> john = User(**data)
        TypeError: __init__() got an unexpected keyword argument 'address'
    
    But by using :func:`.construct_dict`, we're able to construct a ``User``, as this helper function detects that
    the excess ``address`` and ``phone`` are not valid parameters for ``User``'s constructor.
     
        >>> from privex.helpers import construct_dict
        >>> john = construct_dict(User, data)
        >>> print(john.username, john.first_name, john.last_name)
        johndoe123 John Doe
    
    **Example - A function/method which only takes specific arguments**
    
    Not only can :func:`.construct_dict` be used for classes, but it can also be used for any function/method.
    
    Here's an example using a simple "factory function" which creates user objects::
    
        >>> def create_user(username, first_name=None, last_name=None):
        ...     return User(username, first_name, last_name)
        >>>
        >>> data = dict(
        ...     username='johndoe123', first_name='John', last_name='Doe',
        ...     address='123 Example St', phone='+1-123-000-1234'
        ... )
        >>> # We can't just pass data as kwargs due to the extra keys.
        >>> create_user(**data)
        TypeError: create_user() got an unexpected keyword argument 'address'
        >>> # But we can call the function using construct_dict, which filters out the excess dict keys :)
        >>> john = construct_dict(create_user, data)
        >>> print(john.username, john.first_name, john.last_name)
        johndoe123 John Doe
    
    
    :param Type[T]|callable cls: A class (not an instance) or callable (function / lambda) to extract and filter the
                                 parameter's from, then call using filtered ``kwargs`` and ``args``.
    
    :param dict kwargs: A dictionary containing keyword arguments to filter and use to call / construct ``cls``.
    
    :param list|set args: A list of positional arguments (NOT FILTERED!) to pass when calling/constructing ``cls``.
    
    :param bool check_parents: (Default: ``True``) If ``obj`` is a class and this is True, will recursively grab
                               the constructor parameters for all parent classes of ``cls`` and merge them into the
                               returned dict.
    :return Any func_result:   If ``cls`` was a function/method, the return result will be the returned data/object
                               from the function passed.
    
    :return T cls_instance:    If ``cls`` was a class, then the return result will be an instance of the class.
    
    """
    args = empty_if(args, [])
    if hasattr(cls, '__attrs_attrs__'):
        # If the passed object has the attribute __attrs_attrs__, then this means that it's an ``attr.s`` class, so
        # we should just extract the attributes from __attrs_attrs__.
        cls_keys = [atr.name for atr in cls.__attrs_attrs__]
    else:
        # Otherwise, extract the function / class's expected parameter names using our helper get_function_params().
        cls_keys = get_function_params(cls, check_parents=check_parents, merge=True)
        cls_keys = cls_keys.keys()

    clean_data = {x: y for x, y in kwargs.items() if x in cls_keys}
    return cls(*args, **clean_data)



