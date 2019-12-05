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
import random
import re
import string
import argparse
import logging
import sys
from collections import namedtuple, OrderedDict
from datetime import datetime
from decimal import Decimal, getcontext
from os import getenv as env
from typing import Sequence, List, Union, Tuple, Type, Dict, TypeVar, Any, Iterable, Callable, NewType, Optional

from privex.helpers.collections import DictObject, OrderedDictObject

log = logging.getLogger(__name__)

SAFE_CHARS = 'abcdefhkmnprstwxyz23456789ACDEFGHJKLMNPRSTWXYZ'
"""Characters that shouldn't be mistaken, avoiding users confusing an o with a 0 or an l with a 1 or I"""

ALPHANUM = string.ascii_uppercase + string.digits + string.ascii_lowercase
"""All characters from a-z, A-Z, and 0-9 - for random strings where there's no risk of user font confusion"""

T = TypeVar('T')
"""Plain generic type variable for use in helper functions"""
K = TypeVar('K')
"""Plain generic type variable for use in helper functions"""
V = TypeVar('V')
"""Plain generic type variable for use in helper functions"""

C = TypeVar('C', type, callable, Callable)
"""Generic type variable constrained to :class:`type` / :class:`typing.Callable` for use in helper functions"""
CL = TypeVar('CL', type, callable, Callable)
"""Generic type variable constrained to :class:`type` / :class:`typing.Callable` for use in helper functions"""


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


USE_ORIG_VAR = type('UseOrigVar', (), {})
"""
A simple functionless type, used purely as a default parameter value meaning "fallback to the value from a certain
other parameter".

Primarily used in :func:`.empty_if` but can be used by any function/method, including use outside of privex-helpers.

"""


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


def byteify(data: Union[str, bytes], encoding='utf-8') -> bytes:
    """
    Convert a piece of data into bytes if it isn't already.
        
        >>> byteify("hello world")
        b"hello world"
    
    """
    return bytes(data, encoding) if type(data) is not bytes else data


def stringify(data: Union[str, bytes], encoding='utf-8') -> str:
    """
    Convert a piece of data into a string (from bytes) if it isn't already.

        >>> stringify(b"hello world")
        "hello world"

    """
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



