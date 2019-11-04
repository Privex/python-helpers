"""
Common functions and classes that don't fit into a specific category

**Copyright**::

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
import inspect
import math
import random
import string
import argparse
import logging
import sys
from decimal import Decimal, getcontext
from os import getenv as env
from typing import Sequence, List, Union, Tuple, Type, Dict

log = logging.getLogger(__name__)

SAFE_CHARS = 'abcdefhkmnprstwxyz23456789ACDEFGHJKLMNPRSTWXYZ'
"""Characters that shouldn't be mistaken, avoiding users confusing an o with a 0 or an l with a 1 or I"""

ALPHANUM = string.ascii_uppercase + string.digits + string.ascii_lowercase
"""All characters from a-z, A-Z, and 0-9 - for random strings where there's no risk of user font confusion"""


def random_str(size:int = 50, chars: Sequence = SAFE_CHARS) -> str:
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


class Mocker(object):
    """
    This mock class is designed to be used either to act as a stand-in "noop" (no operation) object, which
    could be used either as a drop-in replacement for a failed module / class import, or for certain unit tests.
    
    If you need additional functionality such as methods having actual behaviour, you can set attributes on a
    Mocker instance to either a lambda, or point them at a real function/method::
    
        >>> m = Mocker()
        >>> m.some_func = lambda a: a+1
        >>> m.some_func(5)
        6
    
    
    **Example use case - fallback for unimportant module imports**
    
    Below is a real world example of using :class:`.Mocker` and :py:func:`privex.helpers.decorators.mock_decorator`
    to simulate :py:mod:`pytest` - allowing your tests to run under the standard :py:mod:`unittest` framework if
    a user doesn't have pytest (as long as your tests aren't critically dependent on PyTest).
    
    Try importing ``pytest`` then fallback to a mock pytest::
    
        >>> try:
        ...     import pytest
        ... except ImportError:
        ...     from privex.helpers import Mocker, mock_decorator
        ...     print('Failed to import pytest. Using privex.helpers.Mocker to fake pytest.')
        ...     # Make pytest pretend to be the class 'module' (the class actually used for modules)
        ...     pytest = Mocker.make_mock_class('module')
        ...     # To make pytest.mark.skip work, we add the fake module 'mark', then set skip to `mock_decorator`
        ...     pytest.add_mock_module('mark')
        ...     pytest.mark.skip = mock_decorator
        ...
    
    Since we added the mock module ``mark``, and set the attribute ``skip`` to point at ``mock_decorator``, the
    test function ``test_something`` won't cause a syntax error. ``mock_decorator`` will just call test_something()
    which doesn't do anything anyway::
     
        >>> @pytest.mark.skip(reason="this test doesn't actually do anything...")
        ... def test_something():
        ...     pass
        >>>
        >>> def test_other_thing():
        ...     if True:
        ...         return pytest.skip('cannot test test_other_thing because of an error')
        ...
        >>>
    
    **Generating "disguised" mock classes**
    
    If you need the mock class to appear to have a certain class name and/or module path, you can generate
    "disguised" mock classes using :py:meth:`.make_mock_class` like so:
    
        >>> redis = Mocker.make_mock_class('Redis', module='redis')
        >>> redis
        <redis.Redis object at 0x7fd7402ea4a8>
    
    **A :class:`.Mocker` instance has the following behaviour**
    
    * Attributes that don't exist result in a function being returned, which accepts any arguments / keyword args,
      and simply returns ``None``
    
    Example::
    
        >>> m = Mocker()
        >>> repr(m.randomattr('hello', world=123))
        'None'
    
    
    * Arbitrary attributes ``x.something`` and items ``x['something']`` can be set on an instance, and they will
      be similarly returned when they're accessed. Attributes and items share the same key/value's, so the
      following examples are all accessing the same data::
    
    Example::
    
        >>> m = Mocker()
        >>> m.example = 'hello'
        >>> m['example'] = 'world'
        >>> print(m.example)
        world
        >>> print(m['example'])
        world
    
    * You can add arbitrary "modules" to a Mocker instance. With only the ``name`` argument, :py:meth:`.add_mock_module`
      will add a "module" under the instance, which is really just another :class:`.Mocker` instance.
    
    Example::
    
        >>> m = Mocker()
        >>> m.add_mock_module('my_module')
        >>> m.my_module.example = 'hello'
        >>> print(m.my_module['example'], m.my_module.example)
        hello hello
    
    
    """
    mock_modules: dict
    mock_attrs: dict
    
    def __init__(self, modules: dict = None, attributes: dict = None):
        self.mock_attrs = {} if attributes is None else attributes
        self.mock_modules = {} if modules is None else modules
    
    @classmethod
    def make_mock_class(cls, name='Mocker', instance=True, **kwargs):
        """
        Return a customized mock class or create an instance which appears to be named ``name``
        
        Allows code which might check ``x.__class__.__name__`` to believe it's the correct object.
        
        Using the kwarg ``module`` you can change the module that the class / instance appears to have been imported
        from, allowing for quite deceiving fake classes and instances.
        
        **Example usage**::
        
            >>> redis = Mocker.make_mock_class('Redis', module='redis')
            >>> # As seen below, the class appears to be called Redis, and even claims to be from the module `redis`
            >>> redis
            <redis.Redis object at 0x7fd7402ea4a8>
            >>> print(f'Module: {redis.__module__} - Class Name: {redis.__class__.__name__}')
            Module: redis - Class Name: Redis
        
        **Creating methods/attributes dynamically**
        
        You can set arbitrary attributes to point at a function, or just set them to a lambda::
        
            >>> redis.exists = lambda key: 1
            >>> redis.exists('hello')
            1
            >>> redis.hello()  # Non-existent attributes just act as a function that eats any args and returns None
            None
            
        
        :param name: The name to write onto the mock class's ``__name__`` (and ``__qualname__`` if not specified)
        :param bool instance: If ``True`` then the disguised mock class will be returned as an instance. Otherwise
                              the raw class itself will be returned for you to instantiate yourself.
        :param kwargs: All kwargs (other than ``qualname``) are forwarded to ``__init__`` of the disguised class
                       if ``instance`` is True.
        :key str qualname: Optionally specify the "qualified name" to insert into ``__qualname__``. If this isn't
                           specified, then ``name`` is used for qualname, which is fine for most cases anyway.
        :key str module: Optionally override the module namespace that the class is supposedly from. If not specified,
                         then the class will just inherit this module (``privex.helpers.common``)
        :return:
        """
        qualname = kwargs.pop('qualname', name)
        
        class OuterMocker(cls):
            pass
        
        OuterMocker.__name__ = name
        OuterMocker.__qualname__ = qualname
        
        if 'module' in kwargs:
            OuterMocker.__module__ = kwargs['module']
        
        return OuterMocker() if instance else OuterMocker
        
    def add_mock_module(self, name: str, value=None, mock_attrs: dict = None, mock_modules: dict = None):
        """
        Add a fake sub-module to this Mocker instance.
        
        Example::
        
            >>> m = Mocker()
            >>> m.add_mock_module('my_module')
            >>> m.my_module.example = 'hello'
            >>> print(m.my_module['example'], m.my_module.example)
            hello hello
        
        
        :param str name: The name of the module to add.
        :param value: Set the "module" to this object, instead of an instance of :class:`.Mocker`
        :param dict mock_attrs: If ``value`` is ``None``, then this can optionally contain a dictionary of
                                attributes/items to pre-set on the Mocker instance.
        :param dict mock_modules: If ``value`` is ``None``, then this can optionally contain a dictionary of
                                 "modules" to pre-set on the Mocker instance.
        """
        mock_attrs = {} if mock_attrs is None else mock_attrs
        mock_modules = {} if mock_modules is None else mock_modules
        
        self.mock_modules[name] = Mocker(modules=mock_modules, attributes=mock_attrs) if value is None else value

    def __getattribute__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError:
            pass
        try:
            if item in super().__getattribute__('mock_modules'):
                return self.mock_modules[item]
        except AttributeError:
            pass
        try:
            if item in super().__getattribute__('mock_attrs'):
                return self.mock_attrs[item]
        except AttributeError:
            pass
        
        return lambda *args, **kwargs: None
    
    def __setattr__(self, key, value):
        if key in ['mock_attrs', 'mock_modules']:
            return super().__setattr__(key, value)
        m = super().__getattribute__('mock_attrs')
        m[key] = value
    
    def __getitem__(self, item):
        return self.__getattribute__(item)
    
    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    @property
    def __name__(self):
        return self.__class__.__name__
    

class Dictable:
    """
    A small abstract class for use with Python 3.7 dataclasses.

    Allows dataclasses to be converted into a ``dict`` using the standard ``dict()`` function:

        >>> @dataclass
        >>> class SomeData(Dictable):
        ...     a: str
        ...     b: int
        ...
        >>> mydata = SomeData(a='test', b=2)
        >>> dict(mydata)
        {'a': 'test', 'b': 2}

    Also allows creating dataclasses from arbitrary dictionaries, while ignoring any extraneous dict keys.

    If you create a dataclass using a ``dict`` and you have keys in your ``dict`` that don't exist in the dataclass,
    it'll generally throw an error due to non-existent kwargs:

        >>> mydict = dict(a='test', b=2, c='hello')
        >>> sd = SomeData(**mydict)
        TypeError: __init__() got an unexpected keyword argument 'c'

    Using ``from_dict`` you can simply trim off any extraneous dict keys:

        >>> sd = SomeData.from_dict(**mydict)
        >>> sd.a, sd.b
        ('test', 2)
        >>> sd.c
        AttributeError: 'SomeData' object has no attribute 'c'



    """

    def __iter__(self):
        # Allow casting into dict()
        for k, v in self.__dict__.items(): yield (k, v,)

    @classmethod
    def from_dict(cls, env):
        # noinspection PyArgumentList
        return cls(**{
            k: v for k, v in env.items()
            if k in inspect.signature(cls).parameters
        })

