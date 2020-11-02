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
from typing import Callable, Sequence, List, Union, Tuple, Type, Dict, Any, Iterable, Optional, BinaryIO, Generator, Mapping
from privex.helpers import settings
from privex.helpers.collections import DictObject, OrderedDictObject
from privex.helpers.types import T, K, V, C, USE_ORIG_VAR, STRBYTES, NumberStr
from privex.helpers.exceptions import NestedContextException


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


def env_csv(env_key: str, env_default=None, csvsplit=',') -> List[str]:
    """
    Quick n' dirty parsing of simple CSV formatted environment variables, with fallback
    to user specified ``env_default`` (defaults to None)

    Example:

        >>> import os
        >>> os.environ['EXAMPLE'] = '  hello ,  world, test')
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


    **Example uses**

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

    Below, you'll see extract_settings extracted all keys starting with ``DB_``, removed the ``DB_`` prefix, converted the
    remaining portion of the key to lowercase, and also merged in the default setting 'host' since ``DB_HOST`` didn't exist.

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


def get_return_type(f: callable) -> Optional[Union[type, object, callable]]:
    """
    Extract the return type for a function/method. Note that this only works with functions/methods which have their
    return type annotated, e.g. ``def somefunc(x: int) -> float: return x * 2.1``
    
    .. Attention:: If you want to extract a function/method return type and have any Generic :mod:`typing` types simplified
                   down to their native Python base types (important to be able to compare with :func:`.isinstance` etc.),
                   then you should use :func:`.extract_type` instead (handles raw types, objects, and function pointers)
    
    
    **Example 1** - Extracting a generic return type from a function::
    
        >>> def list_wrap(v: T) -> List[T]:
        ...     return [v]
        ...
        >>> rt = get_return_type(list_wrap)
        typing.List[~T]
        >>> rt._name            # We can get the string type name via _name
        'List'
        >>> l = rt.__args__[0]  # We can access the types inside of the [] via .__args__
        ~T
        >>> l.__name__          # Get the name of 'l' - the type inside of the []
        'T'
    
    **Example 2** - What happens if you use this on a function/method with no return type annotation?
    
    The answer is: **nothing** - it will simply return ``None`` if the function/method has no return type annotation::
    
        >>> def hello(x):
        ...     return x * 5
        >>> repr(get_return_type(hello))
        'None'
        
        
    :param callable f: A function/method to extract the return type from
    :return return_type: The return type, usually either a :class:`.type` or a :class:`.object`
    """
    if f is None: return None
    if not inspect.isclass(f) and any([inspect.isfunction(f), inspect.ismethod(f), inspect.iscoroutinefunction(f)]):
        sig = inspect.signature(f)
        ret = sig.return_annotation
        # noinspection PyUnresolvedReferences,PyProtectedMember
        if ret is inspect._empty or empty(ret, True):
            return None
        return ret
    return f


def typing_to_base(tp, fail=False, return_orig=True, clean_union=True) -> Optional[Union[type, object, callable, tuple, Tuple[type]]]:
    """
    Attempt to extract one or more native Python base types from a :mod:`typing` type, including generics such as ``List[str]``,
    and combined types such as ``Union[list, str]``
    
        >>> typing_to_base(List[str])
        list
        >>> typing_to_base(Union[str, Dict[str, list], int])
        (str, dict, int)
        >>> typing_to_base(Union[str, Dict[str, list], int], clean_union=False)
        (str, typing.Dict[str, list], int)
        >>> typing_to_base(str)
        str
        >>> typing_to_base(str, fail=True)
        TypeError: Failed to extract base type for type object: <class 'str'>
        >>> repr(typing_to_base(str, return_orig=False))
        'None'
        
    :param tp: The :mod:`typing` type object to extract base/native type(s) from.
    :param bool fail: (Default: ``False``) If True, then raises :class:`.TypeError` if ``tp`` doesn't appear to be a :mod:`typing` type.
    :param bool return_orig: (Default: ``True``) If True, returns ``tp`` as-is if it's not a typing type. When ``False``,
                             non- :mod:`typing` types will cause ``None`` to be returned.
    :param bool clean_union: (Default: ``True``) If True, :class:`typing.Union`'s will have each type
                             converted/validated into a normal type using :func:`.extract_type`
    :return type_res: Either a :class:`.type` base type, a :class:`.tuple` of types, a :mod:`typing` type object, or something else
                      depending on what type ``tp`` was.
    """
    # We can't use isinstance() with Union generic objects, so we have to identify them by checking their repr string.
    if repr(tp).startswith('typing.Union['):
        # For Union's (including Optional[]), we iterate over the object's ``__args__`` which contains the Union's types,
        # and pass each type through extract_type to cleanup any ``typing`` generics such as ``List[str]`` back into
        # their native type (e.g. ``str`` for ``List[str]``)
        ntypes = []
        # noinspection PyUnresolvedReferences
        targs = tp.__args__
        for t in targs:
            try:
                ntypes.append(extract_type(t) if clean_union else t)
            except Exception as e:
                log.warning("Error while extracting type for %s (part of %s). Reason: %s - %s", t, repr(tp), type(e), str(e))
                ntypes.append(t)
        return tuple(ntypes)
    # For Python 3.6, __origin__ contains the typing type without the generic part, while __orig_bases__ is a tuple containing the
    # native/base type, and some typing type.
    # On 3.7+, __origin__ contains the native/base type, while __orig_bases__ doesn't exist
    if hasattr(tp, '__orig_bases__'): return tp.__orig_bases__[0]

    # __origin__ / __extra__ are exposed by :mod:`typing` types, including generics such as Dict[str,str]
    # original SO answer: https://stackoverflow.com/a/54241536/2648583
    if hasattr(tp, '__origin__'): return tp.__origin__
    if hasattr(tp, '__extra__'): return tp.__extra__
    if fail:
        raise TypeError(f"Failed to extract base type for type object: {repr(tp)}")
    if return_orig:
        return tp
    return None


def extract_type(tp: Union[type, callable, object], **kwargs) -> Optional[Union[type, object, callable, tuple, Tuple[type]]]:
    """
    Attempt to identify the :class:`.type` of a given value, or for functions/methods - identify their RETURN value type.
    
    This function can usually detect :mod:`typing` types, including generics such as ``List[str]``, and will attempt to extract
    their native Python base type, e.g. :class:`.list`.
    
    For :class:`typing.Union` based types (including :class:`typing.Optional`), it can extract a tuple of base types, including
    from nested :class:`typing.Union`'s - e.g. ``Union[str, list, Union[dict, set], int`` would be simplified down
    to ``(str, list, dict, set, int)``

    .. Attention:: If you want to extract the original return type from a function/method, including generic types such as ``List[str]``,
                   then you should use :func:`.get_return_type` instead.

    **Example 1** - convert a generic type e.g. ``Dict[str, str]`` into it's native type (e.g. ``dict``)::

        >>> dtype = Dict[str, str]
        >>> # noinspection PyTypeHints,PyTypeChecker
        >>> isinstance({}, dtype)
        TypeError: Subscripted generics cannot be used with class and instance checks
        >>> extract_type(dtype)
        dict
        >>> isinstance({}, extract_type(dtype))
        True

    **Example 2** - extract the return type of a function/method, and if the return type is a generic (e.g. ``List[str]``), automatically
    convert it into the native type (e.g. ``list``) for use in comparisons such as :func:`.isinstance`::

        >>> def list_wrap(v: T) -> List[T]:
        ...     return [v]
        >>>
        >>> extract_type(list_wrap)
        list
        >>> isinstance([1, 2, 3], extract_type(list_wrap))
        True

    **Example 3** - extract the type from an instantiated object, allowing for :func:`.isinstance` comparisons::

        >>> from privex.helpers import DictObject
        >>> db = DictObject(hello='world', lorem='ipsum')
        {'hello': 'world', 'lorem': 'ipsum'}
        >>> type_db = extract_type(db)
        privex.helpers.collections.DictObject
        >>> isinstance(db, type_db)
        True
        >>> isinstance(DictObject(test=123), type_db)
        True
    
    **Example 4** - extract a tuple of types from a :class:`typing.Union` or :class:`typing.Optional` (inc. return types) ::
        
        >>> def hello(x) -> Optional[str]:
        ...     return x * 5
        ...
        >>> extract_type(hello)
        (str, NoneType)
        >>> # Even with a Union[] containing a List[], another Union[] (containing a Tuple and set), and a Dict[],
        >>> # extract_type is still able to recursively flatten and simplify it down to a tuple of base Python types
        >>> extract_type(Union[
        ...     List[str],
        ...     Union[Tuple[str, int, str], set],
        ...     Dict[int, str]
        ... ])
        (list, tuple, set, dict)
    
    
    **Return Types**
    
    A :class:`.type` will be returned for most calls where ``tp`` is either:
    
        * Already a native :class:`.type` e.g. :class:`.list`
        * A generic type such as ``List[str]`` (which are technically instances of :class:`.object`)
        * A function/method with a valid return type annotation, including generic return types
        * An instance of a class (an object), where the original type can be easily extracted via ``tp.__class__``
    
    If ``tp`` was an :class:`.object` and the type/class couldn't be extracted, then it would be returned in it's original object form.
    
    If ``tp`` was an unusual function/method which couldn't be detected as one, or issues occurred while extracting the return type,
    then ``tp`` may be returned in it's original :class:`.callable` form.
    
    
    :param tp: The type/object/function etc. to extract the most accurate type from
    :return type|object|callable ret: A :class:`.type` will be returned for most calls, but may be an :class:`.object`
                                      or :class:`.callable` if there were issues detecting the type.
    """
    # If tp is None, there's nothing we can do with it, so return None.
    if tp is None: return None
    # If 'tp' is a known native type, we don't need to extract anything, just return tp.
    if tp in [list, set, tuple, dict, str, bytes, int, float, Decimal]: return tp
    is_func = any([inspect.isfunction(tp), inspect.ismethod(tp), inspect.iscoroutinefunction(tp)])
    # Functions count as class instances (instances of object), therefore to narrow down a real class/type instance,
    # we have to confirm it's NOT a function/method/coro, NOT a raw class/type, but IS an instance of object.
    # if not is_func and not inspect.isclass(tp) and isinstance(tp, object):
    if not is_func and isinstance(tp, object):
        # Handle extracting base types from generic :mod:`typing` objects, including tuples of types from Union's
        tbase = typing_to_base(tp, return_orig=False)
        if tbase is not None:    # If the result wasn't None, then we know it was a typing type and base type(s) were extracted properly
            return tbase
        # Before checking __class__, we make sure that tp is an instance by checking isclass(tp) is False
        if not inspect.isclass(tp) and hasattr(tp, '__class__'):
            return tp.__class__  # If tp isn't a typing type, __class__ (if it exists) should be the "type" of tp
        return tp  # If all else fails, return tp as-is
    
    # If is_func matches at this point, we're dealing with a function/method/coroutine and need to extract the return type.
    # To prevent an infinite loop, we set _sec_layer when passing the return type to extract_type(), ensuring that we don't
    # call extract_type(rt) AGAIN if the return type just so happened to be a function
    if is_func and not kwargs.get('_sec_layer'):
        # Extract the original return type, then pass it through extract_type again, since if it's a generic type,
        # we'll want to extract the native type from it, since generics like ``List[str]`` can't be used with ``isinstance()``
        rt = get_return_type(tp)
        return extract_type(rt, _sec_layer=True)
    # If all else fails, return tp as-is
    return tp


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


def call_sys(proc, *args, write: STRBYTES = None, **kwargs) -> Union[Tuple[bytes, bytes], Tuple[str, str]]:
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

    
    :param Decimal|int|float|str compare: The base number which all ``numbers`` will be compared against.
    :param Decimal|int|float|str numbers: One or more numbers to compare against ``compare``
    :param Decimal|int|float|str tolerance: (kwarg only) Amount that each ``numbers`` can be greater/smaller than ``compare`` before
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
T_PARAM_LIST = Union[Dict[str, T_PARAM], Mapping[str, T_PARAM], List[T_PARAM], Iterable[T_PARAM]]
"""
Type alias for dict's containing strings mapped to :class:`inspect.Parameter`'s, lists of just
:class:`inspect.Parameter`'s, and any iterable of :class:`inspect.Parameter`
"""

# noinspection PyProtectedMember,PyUnresolvedReferences
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


class LayeredContext:
    """
    A wrapper class for context manager classes / functions which allows you to control how many ``with`` layers that a context manager
    can have - and allow for the previous layer's context manager ``__enter__`` / ``yield`` result to be passed down
    when :attr:`.max_layers` is hit.

    (context managers are classes/functions with the methods ``__enter__`` / ``__exit__`` / ``__aenter__`` / ``__aexit__`` etc.)

    Works with context manager classes, asyncio context manager classes, and :func:`contextlib.contextmanager` functions.

    By default, :class:`.LayeredContext` sets :attr:`.max_layers` to ``1``, meaning after 1 layer of ``with`` or ``async with``
    statements, all additional layers will simply get given the same context result as the 1st layer, plus both ``__enter__``
    and ``__exit__`` will only be called once (at the start and end of the first layer).

    **Using with class-based context managers**::

        >>> class Hello:
        ...     def __enter__(self):
        ...         print('entering Hello')
        ...         return self
        ...     def __exit__(self, exc_type, exc_val, exc_tb):
        ...         print('exiting Hello')
        >>> ctx_a = LayeredContext(Hello())
        >>> with ctx_a as a:
        ...     print('class manager layer 1')
        ...     with ctx_a as b:
        ...         print('class manager layer 2')
        ...     print('back to class layer 1')
        entering Hello
        class manager layer 1
        class manager layer 2
        back to class layer 1
        exiting Hello

    We can see that ``entering Hello`` and ``exiting Hello`` were only outputted at the end of the first context block ``with ctx_a as a``,
    showing that ``Hello`` was only entered/exited as a context manager for the first ``with`` block.

    **Using with function-based :func:`contextlib.contextmanager` context managers**::

        >>> from contextlib import contextmanager
        >>> @contextmanager
        >>> def lorem():
        ...     print('entering lorem contextmanager')
        ...     yield 'hello world'
        ...     print('exiting lorem contextmanager')
        >>> ctx_b = LayeredContext(lorem())
        >>> with ctx_b as c:
        ...     print('function manager layer 1 - context is:', c)
        ...     with ctx_b as d:
        ...         print('function manager layer 2 - context is:', d)
        ...     print('back to function layer 1')
        entering lorem contextmanager
        function manager layer 1 - context is: hello world
        function manager layer 2 - context is: hello world
        back to function layer 1
        exiting lorem contextmanager

    We can see the default :attr:`.max_layers` of ``1`` was respected, as the 2nd layer ``with ctx_b as d`` only
    printed ``function manager layer 2`` (thus ``lorem``'s enter/exit methods were not called), and it shows the
    context is still ``hello world`` (the context yielded by ``lorem`` in layer 1).

    **Example usage**

    First we need an example class which can be used as a context manager, so we create ``Example`` with a very simple
    ``__enter__`` and ``__exit__`` method, which simply adds and subtracts from ``self.ctx_layer`` respectively::

        >>> class Example:
        ...     def __init__(self):
        ...         self.ctx_layer = 0
        ...     def __enter__(self):
        ...         self.ctx_layer += 1
        ...         return self
        ...     def __exit__(self, exc_type, exc_val, exc_tb):
        ...         if self.ctx_layer <= 0: raise ValueError('ctx_layer <= 0 !!!')
        ...         self.ctx_layer -= 1
        ...         return None

    If we then create an instance of ``Example``, and use it as a context manager in a 2 layer nested ``with exp``, we can see
    ``ctx_layer`` gets increased each time we use it as a context manager, and decreases after the context manager block::

        >>> exp = Example()
        >>> with exp as x:
        ...     print(x.ctx_layer)       # prints: 1
        ...     with exp as y:
        ...         print(y.ctx_layer)   # prints: 2
        ...     print(x.ctx_layer)       # prints: 1
        >>> exp.ctx_layer
        0

    Now, lets wrap it with :class:`.LayeredContext`, and set the maximum amount of layers to ``1``. If we start using ``ctx`` as a
    context manager, it works as if we used the example instance ``exp`` as a context manager. But, unlike the real instance, ``__enter__``
    is only really called for the first ``with`` block, and ``__exit__`` is only really called once we finish the first
    layer ``with ctx as x`` ::

        >>> ctx = LayeredContext(exp, max_layers=1)
        >>> with ctx as x:
        ...     print(x.ctx_layer)             # prints: 1
        ...     with ctx as y:
        ...         print(y.ctx_layer)         # prints: 1
        ...         print(ctx.virtual_layer)   # prints: 2
        ...     print(x.ctx_layer)         # prints: 1
        ...     print(ctx.virtual_layer)   # prints: 1
        >>> exp.ctx_layer
        0
        >>> print(ctx.layer, ctx.virtual_layer)
        0 0

    """
    wrapped_class: K
    layer_contexts: List[Any]
    current_context: Optional[Union[K, Any]]
    layer: int
    virtual_layer: int
    max_layers: Optional[int]
    fail: bool
    
    def __init__(self, wrapped_class: K, max_layers: Optional[int] = 1, fail: bool = False):
        """
        Construct a :class:`.LayeredContext` instance, wrapping the context manager class instance or func:`contextlib.contextmanager`
        manager function ``wrapped_class``.


        :param K|object wrapped_class: A context manager class or :func:`contextlib.contextmanager` manager function to wrap

        :param int max_layers: Maximum layers of ``(async) with`` blocks before silently consuming further attempts to enter/exit
                               the context manager for :attr:`.wrapped_class`

        :param bool fail: (default: ``False``) When ``True``, will raise :class:`.NestedContextException` when an :meth:`.enter` call is
                          going to cause more than ``max_layers`` context manager layers to be active.
        """
        self.fail = fail
        self.max_layers = max_layers
        self.wrapped_class = wrapped_class
        self.layer_contexts = []
        self.current_context = None
        self.layer = 0
        self.virtual_layer = 0
    
    @property
    def class_name(self):
        if hasattr(self.wrapped_class, '__name__'):
            return self.wrapped_class.__name__
        return self.wrapped_class.__class__.__name__
    
    def enter(self) -> Union[K, Any]:
        self._virt_enter()
        if not self.max_layers or self.layer < self.max_layers:
            return self._enter(self.wrapped_class.__enter__())
        if self.fail:
            raise NestedContextException(f"Too many context manager layers for {self.class_name} ({self.__class__.__name__})")
        return self.current_context
    
    def exit(self, exc_type=None, exc_val=None, exc_tb=None) -> Any:
        if self._virt_exit():
            return self._exit(self.wrapped_class.__exit__(exc_type, exc_val, exc_tb))
        return None
    
    async def aenter(self) -> Union[K, Any]:
        self._virt_enter()
        if not self.max_layers or self.layer < self.max_layers:
            return self._enter(await self.wrapped_class.__aenter__())
        if self.fail:
            raise NestedContextException(f"Too many context manager layers for {self.class_name} ({self.__class__.__name__})")
        return self.current_context
    
    async def aexit(self, exc_type=None, exc_val=None, exc_tb=None) -> Any:
        if self._virt_exit():
            return self._exit(await self.wrapped_class.__aexit__(exc_type, exc_val, exc_tb))
        return None
    
    def _enter(self, context: Optional[Union[K, Any]]):
        self.layer += 1
        log.debug(
            "Entering context layer %d (virt: %d) of class %s (max: %d)", self.layer, self.virtual_layer, self.class_name, self.max_layers
        )
        self.current_context = context
        self.layer_contexts.append(self.current_context)
        return self.current_context
    
    def _exit(self, result):
        log.debug("Exiting context layer %d of class %s (max layers: %d)", self.layer, self.class_name, self.max_layers)
        self.layer -= 1
        self.layer_contexts.pop(self.layer)
        
        self.current_context = None if self.layer < 1 else self.layer_contexts[self.layer - 1]
        return result
    
    def _virt_enter(self):
        self.virtual_layer += 1
        log.debug("ENTER virtual layer %d of class %s (max layers: %d)", self.virtual_layer, self.wrapped_class, self.max_layers)
    
    def _virt_exit(self):
        if self.virtual_layer < 1:
            log.debug("Not calling real _exit as virtual_layer (%d) is 0 or less", self.virtual_layer)
            return False
        log.debug("EXIT virtual layer %d of class %s (max layers: %d)", self.virtual_layer, self.wrapped_class, self.max_layers)
        self.virtual_layer -= 1
        if self.virtual_layer >= self.layer:
            log.debug("Not calling real _exit as virtual_layer (%d) >= layer (%d)", self.virtual_layer, self.layer)
            return False
        return True
    
    def __enter__(self) -> Union[K, Any]:
        return self.enter()
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> Any:
        return self.exit(exc_type, exc_val, exc_tb)
    
    async def __aenter__(self) -> Union[K, Any]:
        return await self.aenter()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> Any:
        return await self.aexit(exc_type, exc_val, exc_tb)


def strip_null(value: Union[str, bytes], conv: Callable[[str], Union[str, bytes, T]] = stringify, nullc="\00") -> Union[str, bytes, T]:
    """
    Small convenience function which :func:`.stringify`'s ``value`` then strips it of whitespace and null bytes, with
    two passes for good measure.
    
    :param str|bytes value: The value to clean whitespace/null bytes out of
    :param callable conv:   (Default :func:`.stringify`) Optionally, you can override the casting function used after
                            the stripping is completed
    :param str nullc:       (Default: ``\00``) Null characters to remove
    :return str|bytes|T cleaned: The cleaned up ``value``
    """
    value = stringify(value).strip().strip(nullc).strip().strip(nullc)
    return conv(value)


def auto_list(obj: V, conv: Union[Type[T], Callable[[V], T]] = list, force_wrap=False, force_iter=False, **kw) -> T:
    """
    Used for painless conversion of various data types into list-like objects (:class:`.list` / :class:`.tuple` / :class:`.set` etc.)
    
    Ensure object ``obj`` is a list-like object of type ``conv``, if it isn't, then attempt to convert it into
    an instance of ``conv`` via either **list wrapping**, or **list iterating**, depending on the type that ``obj`` is detected to be.

    Examples::

        >>> auto_list('hello world')
        ['hello world']
        >>> auto_list('lorem ipsum', conv=set)
        {'lorem ipsum'}
        >>> auto_list('hello world', force_iter=True)
        ['h', 'e', 'l', 'l', 'o', ' ', 'w', 'o', 'r', 'l', 'd']

        >>> auto_list(('this', 'is', 'a', 'test',))
        ['this', 'is', 'a', 'test']
        >>> auto_list(('this', 'is', 'a', 'test',), force_wrap=True)
        [('this', 'is', 'a', 'test')]

    **List Wrapping**
    
    The **list wrapping** conversion method is when we wrap an object with list brackets, i.e. ``[obj]``. which makes
    the ``obj`` a single item inside of a new list.
    
    This is important for simple single-value data types such as :class:`.str`, :class:`.bytes`, integers, floats etc. - since
    using ``list()`` might simply iterate over their contents, e.g. turnining ``"hello"`` into ``['h', 'e', 'l', 'l', 'o']``,
    which is rarely what you intend when you want to convert an object into a list.
    
    This method is used by default for the types::
        
        str, bytes, int, float, Decimal, bool, dict
    
    To force conversion via **List Wrapping**, set the argument ``force_wrap=True``


    **List Iteration / Iterating**
    
    The **list iteration** method is when we call ``list(obj)`` to convert ``obj`` 's **contents** into a list,
    rather than making ``obj`` an item inside of the list.
    
    This is important for other list-like data types such as :class:`.list` / :class:`.set` / :class:`.tuple` etc.,
    since with the **List Wrapping** method, it would result in for example, a set ``{'hello', 'world'}`` simply
    being wrapped by a list ``[{'hello', 'world'}]``, instead of converting it into a list.
    
    To force conversion via **List Iteration**, set the argument ``force_iter=True``
    
    This method is used bt default for the types::
    
        list, set, tuple, range
        
        any object which didn't match the list wrapping type checks and has the method: __iter__
    
    
    
    :param V|any obj: An object of practically any type, to convert into an instance type of ``conv``
    
    :param T|type|callable conv:  A :class:`.type` which is also callable with ``obj`` as the first positional argument, to convert
                                ``obj`` into a ``conv`` instance.
    
    :param bool force_wrap: When set to ``True``, ``obj`` will always be converted into ``conv`` using the list
                            wrapping method ``conv([obj])``, regardless of whether it's a type that should or shouldn't be wrapped.
    
    :param bool force_iter: When set to ``True``, ``obj`` will always be converted into ``conv`` using the list iterator
                            method, i.e. ``conv(list(obj))``, regardless of whether it's a type that should or shouldn't be iterated.
    
    :keyword bool zero: Passthru argument to :func:`.empty` (treat the number ``0`` as empty)
    :keyword bool itr:  Passthru argument to :func:`.empty` (treat zero-length iterables as empty)
    
    :return T|list|set|tuple data: The object ``obj`` after converting it into a ``conv`` instance
    """
    obj = empty_if(obj, [], zero=kw.get('zero', True), itr=kw.get('itr', True))
    # If ``obj`` is already the correct type, then return it.
    if obj is not None and isinstance(obj, conv): return obj
    
    # For basic object types which simply contain a singular piece of data, such as strings, bytes, int, float etc.
    # it's important that we wrap them in [] to make them into just one item inside of a list, before converting the list
    # into whatever it's final form is.
    if not force_iter and (force_wrap or isinstance(obj, (str, bytes, int, float, Decimal, bool, dict))):
        return conv([obj])
    
    # If an object is a list/set/tuple/similar iterable object, then it's probably better if we use ``list()`` + ``conv()`` to convert
    # the CONTENTS of the object into ``conv``, rather than just wrapping the object itself as a single item
    if force_iter or isinstance(obj, (list, set, tuple, range)) or hasattr(obj, '__iter__'): return conv(list(obj))
    return conv(obj)
