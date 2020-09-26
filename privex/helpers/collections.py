"""
Functions, classes and/or types which either **are**, or are related to Python
variable storage types (``dict``, ``tuple``, ``list``, ``set`` etc.)

Object-like Dictionaries (dict's)
---------------------------------

Have you ever wanted a dictionary that works like an object, where you can get/set dictionary keys using 
attributes (``x.something``) as easily as you can with items (``x['something']``)?

We did. So we invented :class:`.DictObject`, a sub-class of the built-in :class:`dict`, making it compatible
with most functions/methods which expect a :class:`dict` (e.g. :meth:`json.dumps`).

You can create a new :class:`.DictObject` and use it just like a ``dict``, or you can convert an existing
``dict`` into a ``DictObject`` much like you'd cast any other builtin type.

It can also easily be cast back into a standard ``dict`` when needed, without losing any data.

Creating a new DictObject and using it
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Since :class:`.DictObject` is a subclass of the builtin :class:`dict`, you can instantiate a new
:class:`.DictObject` in the same way you would use the standard :class:`dict` class::

        >>> d = DictObject(hello='world')
        >>> d
        {'hello': 'world'}
        >>> d['hello']
        'world'
        >>> d.hello
        'world'
        >>> d.lorem = 'ipsum'
        >>> d['orange'] = 'banana'
        >>> d
        {'hello': 'world', 'lorem': 'ipsum', 'orange': 'banana'}


Converting an existing dictionary (dict) into a DictObject
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can convert an existing ``dict`` into a :class:`.DictObject` in the same way you'd convert
any other object into a ``dict``::

    >>> y = {"hello": "world", "example": 123}
    >>> x = DictObject(y)
    >>> x.example
    123
    >>> x['hello']
    'world'
    >>> x.hello = 'replaced'
    >>> x
    {'hello': 'replaced', 'example': 123}

It also works vice versa, you can convert a :class:`.DictObject` instance back into a :class:`dict` just as
easily as you converted the `dict` into a `DictObject`.

    >>> z = dict(x)
    >>> z
    {'hello': 'replaced', 'example': 123}



Dict-able NamedTuple's
----------------------

While :func:`collections.namedtuple`'s can be useful, they have some quirks, such as not being able to access
fields by item/key (``x['something']``). They also expose a method ``._asdict()``, but cannot be directly casted
into a :class:`dict` using ``dict(x)``.

Our :func:`.dictable_namedtuple` collection is designed to fix these quirks.

What is a dictable_namedtuple and why use it?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Unlike the normal :func:`.namedtuple` types, ``dictable_namedtuple``s add extra convenience functionality:

    * Can access fields via item/key: ``john['first_name']``

    * Can convert instance into a dict simply by casting: ``dict(john)``

    * Can set new items/attributes on an instance, even if they weren't previously defined.
    
    * NOTE: You cannot edit an original namedtuple field defined on the type, those remain read only

There are three functions available for working with ``dictable_namedtuple`` classes/instances,
each for different purposes.

  * :py:func:`.dictable_namedtuple` - Create a new ``dictable_namedtuple`` type for instantiation.

  * :py:func:`.convert_dictable_namedtuple` - Convert an existing **namedtuple instance** (not a type/class) into
    a ``dictable_namedtuple`` instance.
  
  * :py:func:`.subclass_dictable_namedtuple` - Convert an existing **namedtuple type/class** (not an instance) into
    a ``dictable_namedtuple`` type for instantiation.


Importing dictable_namedtuple functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from collections import namedtuple
    from privex.helpers import dictable_namedtuple, convert_dictable_namedtuple, subclass_dictable_namedtuple

Creating a NEW dictable_namedtuple type and instance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you're **creating a new Named Tuple**, and you want it to support dictionary-like access, and
have it able to be converted into a dict simply through ``dict(my_namedtuple)``, then you want
:py:func:`.dictable_namedtuple`

.. code-block:: python

    Person = dictable_namedtuple('Person', 'first_name last_name')
    john = Person('John', 'Doe')
    dave = Person(first_name='Dave', last_name='Smith')
    print(dave['first_name'])       # Prints:  Dave
    print(dave.first_name)          # Prints:  Dave
    print(john[1])                  # Prints:  Doe
    print(dict(john))               # Prints:  {'first_name': 'John', 'last_name': 'Doe'}

Converting an existing namedtuple instance into a dictable_namedtuple instance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


If you have **existing Named Tuple instances**, e.g. returned from a python library, then you can use
:py:func:`.convert_dictable_namedtuple` to convert them into ``dictable_namedtuple``'s and gain all the
functionality mentioned at the start of this section. 

.. code-block:: python

    Person = namedtuple('Person', 'first_name last_name')  # This is an existing namedtuple "type" or "class"
    john = Person('John', 'Doe')  # This is an existing namedtuple instance
    john.first_name               # This works on a standard namedtuple. Returns: John
    john[1]                       # This works on a standard namedtuple. Returns: Doe
    john['first_name']            # However, this would throw a TypeError.
    dict(john)                    # And this would throw a ValueError.

    # We can now convert 'john' into a dictable_namedtuple, which will retain the functionality of a
    # namedtuple, but add to the functionality by allowing dict-like key access, updating/creating new
    # fields, as well as painlessly casting to a dictionary.

    d_john = convert_dictable_namedtuple(john)
    d_john.first_name               # Returns: John
    d_john[1]                       # Returns: Doe
    d_john['first_name']            # Returns: 'John'
    dict(d_john)                    # Returns: {'first_name': 'John', 'last_name': 'Doe'}

Converting an existing namedtuple type/class into a dictable_namedtuple type/class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have **existing Named Tuple type/class** then you can use :py:func:`.subclass_dictable_namedtuple`
to convert the type/class into a ``dictable_namedtuple`` type/class and gain all the functionality mentioned 
at the start of this section. (**NOTE:** it's usually easier to just replace your ``namedtuple`` calls 
with ``dictable_namedtuple``)

.. code-block:: python

    Person = namedtuple('Person', 'first_name last_name')  # This is an existing namedtuple "type" or "class"
    # We can now convert the 'Person' type into a dictable_namedtuple type.
    d_Person = subclass_dictable_namedtuple(Person)
    # Then we can use this converted type to create instances of Person with dictable_namedtuple functionality.
    john = d_Person('John', 'Doe')
    john.first_name               # Returns: John
    john[1]                       # Returns: Doe
    john['first_name']            # Returns: 'John'
    dict(john)                    # Returns: {'first_name': 'John', 'last_name': 'Doe'}



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
import copy
import functools
import inspect
import os
import sys
import types
from os.path import dirname, abspath
from collections import namedtuple, OrderedDict
from json import JSONDecodeError
from types import MemberDescriptorType
from typing import Any, Callable, Dict, Optional, NamedTuple, Union, Type, List, Generator, Iterable, TypeVar

# from privex.helpers.decorators import mock_decorator

from privex.helpers.types import AUTO, T, K
import logging
import warnings

log = logging.getLogger(__name__)


def _mock_decorator(*dec_args, **dec_kwargs):
    def _decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper
    return _decorator


def generate_class(
        name: str, qualname: str = None, module: str = None, bases: Union[tuple, list] = None,
        attributes: Dict[str, Any] = None, **kwargs
) -> Any:
    """
    A small helper function for dynamically generating classes / types.

    **Basic usage**

    Generating a simple class, with an instance constructor, a basic instance method, and an instance factory classmethod::

        >>> import random
        >>> from privex.helpers.collections import generate_class
        >>> def hello_init(self, example: int):
        ...     self.example = example
        ...
        >>> Hello = generate_class(
        ...     'Hello', module='hello',
        ...     attributes=dict(
        ...         __init__=hello_init, lorem=lambda self: self.example * 10,
        ...         make_hello=classmethod(lambda cls: cls(random.randint(1, 100)))
        ...     )
        ... )
        ...
        >>> h = Hello(123)
        >>> h.lorem()
        1230
        >>> j = Hello.make_hello()
        >>> j.example
        77
        >>> j.lorem()
        770

    Generating a child class which inherits from an existing class (the parent(s) can also be a generated classes)::

        >>> World = generate_class(
        ...     'World', module='hello', bases=(Hello,), attributes=dict(ipsum=lambda self: float(self.example) / 3)
        ... )
        >>> w = World(130)
        >>> w.lorem()
        1300
        >>> w.ipsum()
        43.333333333333336

    :param str name:         The name of the class, e.g. ``Hello``
    :param str qualname:     (Optional) The qualified name of the class, e.g. for nested classes ``A -> B -> C``, class ``C``
                             would have the ``__name__``: ``C`` and ``__qualname__``: ``A.B.C``
    :param str module:       (Optional) The module the class should appear to belong to (sets ``__module__``)
    :param tuple|list bases: (Optional) A tuple or list of "base" / "parent" classes for inheritance.
    :param dict attributes:  (Optional) A dictionary of attributes to add to the class. (can include constructor + methods)
    :param kwargs:
    :return:
    """
    qualname = name if qualname is None else qualname
    bases = (object,) if bases is None else (tuple(bases) if not isinstance(bases, tuple) else bases)
    attributes = {} if attributes is None else attributes
    attributes['__module__'] = attributes.get('__module__', module)
    # kwargs = dict(kwargs)
    
    x = type(name, bases, attributes)
    x.__name__ = name
    x.__qualname__ = qualname
    x.__module__ = module
    
    return x


def generate_class_kw(name: str, qualname: str = None, module: str = None, bases: Union[tuple, list] = None, **kwargs) -> Type:
    """
    Same as :func:`.generate_class`, but instead of a :class:`dict` ``attributes`` parameter - all additional keyword arguments
    will be used for ``attributes``

    **Example**::

        >>> def lorem_init(self, ipsum=None):
        ...     self._ipsum = ipsum
        ...
        >>> Lorem = generate_class_kw('Lorem',
        ...     __init__=lorem_init, hello=staticmethod(lambda: 'world'),
        ...     ipsum=property(lambda self: 0 if self._ipsum is None else self._ipsum)
        ... )
        >>> l = Lorem()
        >>> l.ipsum()
        0
        >>> l.hello()
        'world'

    """
    return generate_class(name, qualname, module, bases, attributes=dict(kwargs))


def copy_func(f: Callable, rewrap_classmethod=True, name=None, qualname=None, module=AUTO, **kwargs) -> Union[Callable, classmethod]:
    """Based on http://stackoverflow.com/a/6528148/190597 (Glenn Maynard)"""
    if isinstance(f, classmethod):
        fn = copy_func(f.__func__)
        return classmethod(fn) if rewrap_classmethod else fn
    g = types.FunctionType(f.__code__, f.__globals__, name=name if name is not None else f.__name__,
                           argdefs=f.__defaults__,
                           closure=f.__closure__)
    g = functools.update_wrapper(g, f)
    g.__kwdefaults__ = f.__kwdefaults__
    g.__qualname__ = g.__name__ if qualname is None else qualname
    g.__module__ = getattr(f, '__module__') if module is AUTO else module
    return g


def _q_copy(obj: K, key: str = None, deep_private: bool = False, quiet: bool = False, fail: bool = False, **kwargs) -> K:
    should_copy = kwargs.pop('should_copy', True)
    if not should_copy:
        log.debug("Not copying object '%s' (key '%s') as should_copy is False", repr(obj), key)
        return obj
    # By default, deep_private is false, which means we avoid deep copying any attributes which have keys starting with __
    # This is because they're usually objects/types we simply can't deepcopy without issues.
    if not deep_private and key is not None and key.startswith('__'):
        log.debug("Not deep copying key '%s' as deep_private is true and key begins with __", key)
        return obj
    use_copy_func = kwargs.get('use_copy_func', True)
    try:
        if use_copy_func and any([inspect.isfunction(obj), inspect.ismethod(obj), isinstance(obj, classmethod)]):
            copied = copy_func(obj)
        else:
            copied = copy.deepcopy(obj)
        return copied
    except Exception as ex:
        if fail:
            raise ex
        log_args = "Exception while deep copying object %s ( %s ) - using normal ref. Ex: %s %s", key, obj, type(ex), str(ex)
        if quiet:
            log.debug(*log_args)
        else:
            log.warning(*log_args)
    return obj


COPY_CLASS_BLACKLIST = [
    '__dict__', '__slots__', '__weakref__'
]


def _copy_class_dict(obj: Type[T], name, deep_copy=True, deep_private=False, **kwargs) -> Union[Type[T], type]:
    """
    Internal function used by :func:`.copy_class`

    Make a deep copy of the :class:`.type` / class ``obj`` (for standard classes, which use ``__dict__``)
    """
    orig_dict, filt_dict = dict(obj.__dict__), {}
    attr_blacklist = kwargs.get('blacklist', COPY_CLASS_BLACKLIST)
    # Try to deep copy each attribute's value from the original __dict__ in 'orig_dict' into 'filt_dict'.
    # Attributes that are private (start with '__') will use standard references by default (if deep_private is False),
    # along with any attributes that fail to be deep copied.
    for k, v in orig_dict.items():
        # if not deep_copy: break
        if k in attr_blacklist: continue
        filt_dict[k] = v if not deep_copy else _q_copy(v, key=k, deep_private=deep_private, **kwargs)
    
    bases = kwargs.get('bases', obj.__bases__ if kwargs.get('use_bases', True) else (object,))
    return type(name, bases, filt_dict if deep_copy else orig_dict)


def _copy_class_slotted(obj: Type[T], name, deep_copy=True, deep_private=False, **kwargs) -> Union[Type[T], type]:
    """
    Internal function used by :func:`.copy_class`

    Make a deep copy of the :class:`.type` / class ``obj`` (for slotted classes, i.e. those which use ``__slots__``)

    Based on a StackOverflow answer by user ``nkpro``: https://stackoverflow.com/a/61823543/2648583
    """
    slots = obj.__slots__ if type(obj.__slots__) != str else (obj.__slots__,)
    orig_dict, slotted_members = {}, {}
    attr_blacklist = kwargs.get('blacklist', COPY_CLASS_BLACKLIST)

    for k, v in obj.__dict__.items():
        if k in attr_blacklist: continue
        dcval = v if not deep_copy else _q_copy(v, k, deep_private=deep_private, **kwargs)
        if k not in slots:
            orig_dict[k] = dcval
        elif type(v) != MemberDescriptorType:
            slotted_members[k] = dcval
    
    bases = kwargs.get('bases', obj.__bases__ if kwargs.get('use_bases', True) else (object,))
    new_obj = type(name, bases, orig_dict)
    for k, v in slotted_members.items():
        setattr(new_obj, k, v)
    
    return new_obj


DEFAULT_ALLOWED_DUPE = [
    '__annotations__', '__doc__', '__init__', '__getattr__', '__setattr__', '__len__', '__sizeof__',
    '__getattribute__', '__getitem__', '__setitem__', '__delitem__', '__str__', '__repr__',
    '__del__', '__delattr__', '__enter__', '__exit__', '__aenter__', '__aexit__',
    '__next__', '__iter__', '__hash__', '__call__', '__dir__', '__get__', '__set__', '__contains__'
    '__add__', '__sub__', '__mul__', '__floordiv__', '__div__', '__mod__', '__pow__',
    '__eq__', '__ne__', '__lt__', '__gt__', '__le__', '__ge__', '__cmp__',
    '__copy__', '__deepcopy__', '__getstate__', '__setstate__', '__new__',
]


#
# class Asdf:
#     def __

def copy_class_simple(obj: Type[T], name=None, qualname=None, module=AUTO, allow_attrs: list = None, ban_attrs: list = None, **kwargs):
    """
    This is an alternative to :func:`.copy_class` which simply creates a blank class, then iterates over ``obj.__dict__``,
    using :func:`setattr` to copy each attribute over to the cloned class.
    
    It uses :func:`._q_copy` to safely deep copy any attributes which are object references, and thus need their reference pointers
    severed, to avoid edits to the copy affecting the original (and vice versa).
    
    
    :param obj:          The class to duplicate
    :param str name:     The class name to set on the duplicate. If left as ``None``, the duplicate will retain the original ``obj`` name.
    :param str qualname:           The qualified class name to set on the duplicate.
    :param Optional[str] module:   The module path to set on the duplicate, e.g. ``privex.helpers.common``
    :param list allow_attrs: Optionally, you may specify additional private attributes (ones which start with ``__``) that
                             are allowed to be copied from the original class to the duplicated class.
    :param list ban_attrs:   Optionally, you may blacklist certain attributes from being copied from the original class to the duplicate.
    
                             Blacklisted attributes take priority over whitelisted attributes, so you may use this to cancel out
                             any attributes in the default attribute whitelist :attr:`.DEFAULT_ALLOWED_DUPE` which you don't want
                             to be copied to the duplicated class.
    :param kwargs:
    :keyword tuple|list bases: If specified, overrides the default inherited classes (``obj.__bases__``) which would be
                               set on the duplicated class's ``__bases__``.
    :return:
    """
    kwargs = dict(kwargs)

    name = name if name is not None else obj.__name__
    qualname = qualname if qualname is not None else name
    module = module if module is not AUTO else obj.__module__
    
    mkr = generate_class(
        name, qualname, module, bases=kwargs.pop('bases', getattr(obj, '__bases__')), attributes=kwargs.pop('dict_attrs', None)
    )
    allow_attrs = [] if allow_attrs is None else allow_attrs
    ban_attrs = [] if ban_attrs is None else ban_attrs
    allow_attrs += [d for d in DEFAULT_ALLOWED_DUPE if d not in allow_attrs]
    
    for k, v in obj.__dict__.items():
        if k in ban_attrs or (k.startswith('__') and k not in allow_attrs): continue
        try:
            setattr(mkr, k, _q_copy(v, **kwargs))
        except Exception:
            log.exception(f"Failed to copy attribute {k} (value: {v}) to duplicated {obj.__name__} class.")
    # if kwargs.get('bases') is not None:
    #     bases = kwargs.pop('bases')
    #     mkr.__bases__ = bases if isinstance(bases, tuple) else tuple(bases)
    if kwargs.get('str_func') is not None:
        str_func = kwargs.pop('str_func')
        mkr.__str__ = (lambda self: str_func) if isinstance(str_func, str) else str_func

    # mkr.__name__ = name if name is not None else obj.__name__
    # mkr.__qualname__ = qualname if qualname is not None else mkr.__name__
    # mkr.__module__ = module if module is not None else obj.__module__
    return mkr


def copy_class(obj: Type[T], name=None, deep_copy=True, deep_private=False, **kwargs) -> Union[Type[T], type]:
    """
    Attempts to create a full copy of a :class:`.type` or class, severing most object pointers such as attributes containing a
    :class:`.dict` / :class:`.list`, along with classes or instances of classes.

    Example::

        >>> class SomeClass:
        >>>     example = 'lorem ipsum'
        >>>     data = ['hello', 'world']
        >>>     testing = 123
        >>>
        >>> from privex.helpers import copy_class
        >>> OtherClass = copy_class(SomeClass, name='OtherClass')

    If you then append to the :class:`.list` attribute ``data`` on both SomeClass and OtherClass - with a different item
    appended to each class, you'll see that the added item was only added to ``data`` for that class, and not to the other class,
    proving the original and the copy are independent from each other::

        >>> SomeClass.data.append('lorem')
        >>> OtherClass.data.append('ipsum')
        >>> SomeClass.data
        ['hello', 'world', 'lorem']
        >>> OtherClass.data
        ['hello', 'world', 'ipsum']


    :param Type[T] obj: A :class:`.type` / class to attempt to duplicate, deep copying each individual object in the class, to
                        avoid any object pointers shared between the original and the copy.
    :param str|None name: The class name to use for the copy of ``obj``. If not specified, defaults to the original class name from ``obj``
    :param bool deep_copy: (Default: ``True``) If True, uses :func:`copy.deepcopy` to deep copy each attribute in ``obj`` to the copy.
                            If False, then standard references will be used, which may result in object pointers being copied.
    :param bool deep_private: (Default: ``False``) If True, :func:`copy.deepcopy` will be used on "private" class attributes,
                              i.e. ones that start with ``__``. If False, attributes starting with ``__`` will not be deep copied,
                              only a standard assignment/reference will be used.
    :param kwargs: Additional advanced settings (see ``keyword`` pydoc entries for this function)

    :keyword bool use_bases: (Default: ``True``) If True, copy the inheritance (bases) from ``obj`` into the class copy.
    :keyword bool quiet: (Default ``False``) If True, log deep copy errors as ``debug`` level (usually silent in production apps)
                         instead of the louder ``warning``.
    :keyword tuple bases: A :class:`.tuple` of classes to use as "bases" (inheritance) for the class copy. If not specified,
                          copies ``__bases__`` from the original class.
    :keyword str module: If specified, overrides the module ``__module__`` in the class copy with this string, instead of copying from
                         the original class.
    :return Type[T] obj_copy: A deep copy of the original ``obj``
    """
    # If no class name was passed as an attribute, then we copy the name from the original class.
    if not name:
        name = obj.__name__
    
    # Depending on whether 'obj' is a normal class using __dict__, or a slotted class using __slots__, we need to handle the
    # deep copying of the class differently.
    if hasattr(obj, '__slots__'):
        new_obj = _copy_class_slotted(obj, name=name, deep_copy=deep_copy, deep_private=deep_private, **kwargs)
    else:
        new_obj = _copy_class_dict(obj, name=name, deep_copy=deep_copy, deep_private=deep_private, **kwargs)
    
    # Override the module path string if the user specified 'module' as a kwarg
    module = kwargs.get('module')
    if module is not None:
        new_obj.__module__ = module
    return new_obj


def _create_mocker_copy(name=None, **kwargs) -> Union[type, Type["Mocker"]]:
    kwargs['dict_attrs'] = kwargs.get('dict_attrs', {})
    
    def n(self): return self.__class__.__name__
    def m(self): return self.__class__.__module__
    
    nm = copy_func(n, name='__name__', qualname=f"{name}.__name__", module=kwargs.get('module', AUTO))
    # mm = copy_func(m, name='__module__', qualname=f"{name}.__module__", module=kwargs.get('module', AUTO))
    kwargs['dict_attrs']['__name__'] = property(nm)
    # kwargs['dict_attrs']['__module__'] = property(mm)
    
    return copy_class_simple(Mocker, name=name, **kwargs)


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
    # _ALLOWED_DUPE = [
    #     '__module__', '__annotations__', '__doc__', '__init__', '__getattr__', '__setattr__', '__getitem__',
    #     '__setitem__'
    # ]
    mock_modules: dict
    mock_attrs: dict
    
    def __init__(self, modules: dict = None, attributes: dict = None, *args, **kwargs):
        self.mock_attrs = {} if attributes is None else attributes
        self.mock_modules = {} if modules is None else modules
    
    @classmethod
    def make_mock_module(cls, mod_name: str, attributes: dict = None, modules: dict = None, built_in=False, **kwargs):
        mod_base = kwargs.pop('module_base', _module_dir() if built_in else dirname(dirname(dirname(abspath(__file__)))))
        mod_file = os.path.join(mod_base, kwargs.pop('module_file', os.path.join(*mod_name.split('.'), '__init__.py')))
        fix_funcs = kwargs.get('fix_funcs', True)
        
        attributes = {} if not attributes else attributes
        
        if fix_funcs:
            for k, v in attributes.items():
                if inspect.isfunction(v) or inspect.ismethod(v):
                    v.__module__ = mod_name
        modrep = f"<module '{mod_name}' from '{mod_file}'>"
        def x(self): return modrep
        
        # copy_func(x, name='__str__', qualname='__str__', module=mod_name)
        attributes['__repr__'] = attributes.get('__repr__', copy_func(x, name='__repr__', qualname='__repr__', module=mod_name))
        attributes['__str__'] = attributes.get('__str__', copy_func(x, name='__str__', qualname='__str__', module=mod_name))
        attributes['__file__'] = attributes.get('__file__', mod_file)
        return cls.make_mock_class('module', attributes=attributes, modules=modules, **kwargs)

    @classmethod
    def make_mock_class(
        cls, name='Mocker', instance=True, simple=False, attributes: dict = None, modules: dict = None, **kwargs
    ) -> Union[Any, "Mocker", Type["Mocker"]]:
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
        :param bool simple:   When ``True``, generates a very basic, new class - not based on :class:`.Mocker`, which contains
                              the attributes/methods defined in the param ``attributes``.
        :param kwargs: All kwargs (other than ``qualname``) are forwarded to ``__init__`` of the disguised class
                       if ``instance`` is True.
        :param dict attributes: If ``simple`` is True, then this dictionary of attributes is used to generate the class's
                                attributes, methods, and/or constructor.
                                If ``simple`` is False, and ``instance`` is True, these attributes are passed to the constructor
                                of the :class:`.Mocker` clone that was generated.
        :param dict modules: If ``simple`` is False, and ``instance`` is True, this dict of modules are passed to the constructor
                                of the :class:`.Mocker` clone that was generated.
        
        :key str qualname: Optionally specify the "qualified name" to insert into ``__qualname__``. If this isn't
                           specified, then ``name`` is used for qualname, which is fine for most cases anyway.
        :key str module: Optionally override the module namespace that the class is supposedly from. If not specified,
                         then the class will just inherit this module (``privex.helpers.common``)
        :return:
        """
        qualname = kwargs.pop('qualname', name)
        mod_name = kwargs.pop('module', __name__)
        attributes = {} if attributes is None else attributes
        modules = {} if modules is None else modules
        if simple:
            c = generate_class(
                name, qualname=qualname, module=mod_name, bases=kwargs.pop('bases', None), attributes=attributes
            )
            return c(**kwargs) if instance else c
        c = _create_mocker_copy(name, deep_private=True, module=mod_name, qualname=qualname)

        # OuterMocker.__name__ = name
        
        # if mod_name is not None:
        #     OuterMocker.__module__ = kwargs['module']
        str_func = attributes.pop('__str__', None)
        repr_func = attributes.pop('__repr__', None)
        if str_func is not None: c.__str__ = str_func
        if repr_func is not None: c.__repr__ = repr_func
        return c(modules=modules, attributes=attributes, **kwargs) if instance else c
        
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
    
    def add_mock_modules(self, *module_list, _dict_to_attrs=True, _parse_dict=True, **module_map):
        """
        
            >>> hello = Mocker.make_mock_class('Hello')
            >>> hello.add_mock_modules(
            ...     world={
            ...         'lorem': 'ipsum',
            ...         'dolor': 123,
            ...     }
            ... )
        
        :param module_list:
        :param _parse_dict:
        :param _dict_to_attrs:
        :param module_map:
        :return:
        """
        module_map = dict(module_map)
        for m in module_list:
            log.debug("Adding simple mock module from module_list: %s", m)
            self.add_mock_module(m)
        for k, v in module_map.items():
            m_val, m_attrs, m_modules = v, {}, {}
            if isinstance(v, dict):
                if _parse_dict:
                    _m_val = None
                    if 'value' in v: _m_val = v['value']
                    if 'attrs' in v:
                        log.debug("Popping 'attrs' from kwarg '%s' value as attributes for module: %s", k, v)
                        m_attrs = {**m_attrs, **v.pop('attrs')}
                    if 'modules' in v:
                        log.debug("Popping 'modules' from kwarg '%s' value as attributes for module: %s", k, v)
                        m_modules = {**m_modules, **v.pop('modules')}
                    if not _dict_to_attrs or not all([_m_val is None, m_attrs is None, m_modules is None]):
                        log.debug("Setting module value to value of kwarg '%s': %s", k, v)
                        m_val = _m_val if m_attrs is None and m_modules is None else None
                if _dict_to_attrs:
                    log.debug("Importing kwarg '%s' value as attributes for module: %s", k, v)
                    m_attrs = {**m_attrs, **v}
                    
            self.add_mock_module(k, m_val, mock_attrs=m_attrs, mock_modules=m_modules)
    
    @classmethod
    def _duplicate_cls(cls, name=None, qualname=None, module=None, **kwargs) -> Type["Mocker"]:
        return _create_mocker_copy(name=name, qualname=qualname, module=module, **kwargs)
    
    def _duplicate_ins(self, name=None, qualname=None, module=None, **kwargs) -> "Mocker":
        mkr = _create_mocker_copy(name=name, qualname=qualname, module=module, **kwargs)
        return mkr(modules=self.mock_modules, attributes=self.mock_attrs)
    
    def __getattr__(self, item):
        try:
            return object.__getattribute__(self, item)
        except AttributeError:
            pass
        try:
            if item in object.__getattribute__(self, 'mock_modules'):
                return self.mock_modules[item]
        except AttributeError:
            pass
        try:
            if item in object.__getattribute__(self, 'mock_attrs'):
                return self.mock_attrs[item]
        except AttributeError:
            pass
        
        return lambda *args, **kwargs: None
    
    def __setattr__(self, key, value):
        if key in ['mock_attrs', 'mock_modules']:
            return object.__setattr__(self, key, value)
        m = object.__getattribute__(self, 'mock_attrs')
        m[key] = value
    
    def __getitem__(self, item):
        try:
            return self.__getattr__(item)
        except AttributeError as ex:
            raise KeyError(str(ex))
    
    def __setitem__(self, key, value):
        try:
            self.__setattr__(key, value)
        except AttributeError as ex:
            raise KeyError(str(ex))
    
    @property
    def __name__(self):
        return self.__class__.__name__

    def __dir__(self) -> Iterable[str]:
        base_attrs = list(object.__dir__(self))
        extra_attrs = list(self.mock_attrs.keys()) + list(self.mock_modules.keys())
        return base_attrs + extra_attrs


def _module_dir():
    import collections
    col_dir = dirname(abspath(collections.__file__))
    return dirname(col_dir)
    

dataclasses_mock = Mocker.make_mock_module(
    'dataclasses',
    attributes=dict(
        dataclass=_mock_decorator,
        asdict=lambda obj, dict_factory=dict: dict_factory(obj),
        astuple=lambda obj, tuple_factory=tuple: tuple_factory(obj),
        is_dataclass=lambda obj: False,
        field=lambda *args, **kwargs: kwargs.get('default', kwargs.get('default_factory', lambda: None)()),
    ), built_in=True
)
"""
This is a :class:`.Mocker` instance which somewhat emulates the Python 3.7+ :mod:`dataclasses` module,
including the :func:`dataclasses.dataclass` decorator.
"""

try:
    # noinspection PyCompatibility
    import dataclasses
    # noinspection PyCompatibility
    from dataclasses import dataclass, field
except (ImportError, ImportWarning, AttributeError, KeyError) as e:
    warnings.warn(
        f"Failed to import dataclasses (added in Python 3.7). Setting placeholders for typing. "
        f"If you're running Python older than 3.7 and want to use the dataclass features in privex-helpers, "
        f"please update to Python 3.7+, or run 'pip3 install -U dataclasses' to install the backported dataclass emulation "
        f"library for older Python versions.", category=ImportWarning
    )
    # To avoid a severe syntax error caused by the missing dataclass types, we generate a dummy dataclasses module, along with a
    # dummy dataclass and field class so that type annotations such as Type[dataclass] don't cause the module to throw a syntax error.
    # noinspection PyTypeHints
    dataclasses = dataclasses_mock
    # noinspection PyTypeHints
    dataclass = dataclasses.dataclass
    field = dataclasses.field


class DictObject(dict):
    """
    A very simple :class:`dict` wrapper, which allows you to read and write dictionary keys using attributes
    (dot notation) PLUS standard item (key / square bracket notation) access.

    **Example Usage (creating and using a new DictObject)**::

        >>> d = DictObject(hello='world')
        >>> d
        {'hello': 'world'}
        >>> d['hello']
        'world'
        >>> d.hello
        'world'
        >>> d.lorem = 'ipsum'
        >>> d['orange'] = 'banana'
        >>> d
        {'hello': 'world', 'lorem': 'ipsum', 'orange': 'banana'}

    **Example Usage (converting an existing dict)**::

        >>> y = {"hello": "world", "example": 123}
        >>> x = DictObject(y)
        >>> x.example
        123
        >>> x['hello']
        'world'
        >>> x.hello = 'replaced'
        >>> x
        {'hello': 'replaced', 'example': 123}

    """

    def __getattr__(self, item):
        """When an attribute is requested, e.g. ``x.something``, forward it to ``dict['something']``"""
        if hasattr(super(), item):
            return super().__getattribute__(item)
        try:
            return super().__getitem__(item)
        except KeyError as ex:
            raise AttributeError(str(ex))

    def __setattr__(self, key, value):
        """When an attribute is set, e.g. ``x.something = 'abcd'``, forward it to ``dict['something'] = 'abcd'``"""
        if hasattr(super(), key):
            return super().__setattr__(key, value)
        try:
            return super().__setitem__(key, value)
        except KeyError as ex:
            raise AttributeError(str(ex))
    
    def __dir__(self) -> Iterable[str]:
        return list(dict.__dir__(self)) + list(self.keys())
        

class OrderedDictObject(OrderedDict):
    """
    Ordered version of :class:`.DictObject` - dictionary with attribute access.
    See :class:`.DictObject`
    """
    def __getattr__(self, item):
        """When an attribute is requested, e.g. ``x.something``, forward it to ``dict['something']``"""
        if hasattr(super(), item):
            return super().__getattribute__(item)
        try:
            return super().__getitem__(item)
        except KeyError as ex:
            raise AttributeError(str(ex))
    
    def __setattr__(self, key, value):
        """When an attribute is set, e.g. ``x.something = 'abcd'``, forward it to ``dict['something'] = 'abcd'``"""
        if hasattr(super(), key):
            return super().__setattr__(key, value)
        try:
            return super().__setitem__(key, value)
        except KeyError as ex:
            raise AttributeError(str(ex))

    def __dir__(self) -> Iterable[str]:
        return list(OrderedDict.__dir__(self)) + list(self.keys())


class MockDictObj(DictObject):
    """
    This is a masqueraded :class:`.DictObject` made to look like the builtin :class:`dict` by
    editing the class name, qualname and module.

    It may improve compatibility when passing :class:`.DictObject` to certain third-party 
    functions/methods.

    Note: this isn't enough to fool a ``type(x) is dict`` check.
    """


MockDictObj.__name__ = 'dict'
MockDictObj.__qualname__ = 'dict'
MockDictObj.__module__ = 'builtins'



def is_namedtuple(*objs) -> bool:
    """
    Takes one or more objects as positional arguments, and returns ``True`` if ALL passed objects
    are namedtuple instances

    **Example usage**

    First, create or obtain one or more NamedTuple objects::

        >>> from collections import namedtuple
        
        >>> Point, Person = namedtuple('Point', 'x y'), namedtuple('Person', 'first_name last_name')

        >>> pt1, pt2 = Point(1.0, 5.0), Point(2.5, 1.5)
        >>> john = Person('John', 'Doe')
    
    We'll also create a ``tuple``, ``dict``, and ``str`` to show they're detected as invalid::

        >>> normal_tuple, tst_dict, tst_str = (1, 2, 3,), dict(hello='world'), "hello world"
    
    First we'll call :func:`.is_namedtuple` with our Person NamedTuple object ``john``::

        >>> is_namedtuple(john)
        True
    
    As expected, the function shows ``john`` is in-fact a named tuple.

    Now let's try it with our two Point named tuple's ``pt1`` and ``pt2``, plus our Person named tuple ``john``.

        >>> is_namedtuple(pt1, john, pt2)
        True
    
    Since all three arguments were named tuples (even though pt1/pt2 and john are different types), the function
    returns ``True``.

    Now we'll test with a few objects that clearly aren't named tuple's::

        >>> is_namedtuple(tst_str)   # Strings aren't named tuples.
        False
        >>> is_namedtuple(normal_tuple)    # A plain bracket tuple is not a named tuple.
        False
        >>> is_namedtuple(john, tst_dict)  # ``john`` is a named tuple, but a dict isn't, thus False is returned.
        False


    Original source: https://stackoverflow.com/a/2166841

    :param Any objs: The objects (as positional args) to check whether they are a NamedTuple
    :return bool is_namedtuple: ``True`` if all passed ``objs`` are named tuples.
    """
    if len(objs) == 0: raise AttributeError("is_namedtuple expects at least one argument")

    for x in objs:
        t = type(x)
        b = t.__bases__
        if tuple not in b: return False
        f = getattr(t, '_fields', None)
        if not isinstance(f, tuple): return False
        if not all(type(n) == str for n in f): return False
    return True


def convert_dictable_namedtuple(nt_instance, typename=None, module=None, **kwargs) -> Union[NamedTuple, Dict]:
    """
    Convert an existing :func:`collections.namedtuple` instance into a dictable_namedtuple instance.

    **Example**

    First we create a namedtuple type ``Person``

        >>> from collections import namedtuple
        >>> Person = namedtuple('Person', 'first_name last_name')
    
    Next we create an instance of ``Person`` called John Doe, and we can confirm it's a normal namedtuple, as we
    can't access first_name by item/key.

        >>> john = Person('John', 'Doe')
        >>> john['first_name']
        TypeError: tuple indices must be integers or slices, not str
    
    Using :func:`.convert_dictable_namedtuple`, we can convert ``john`` from a normal ``namedtuple``, into
    a ``dictable_namedtuple``.
    
    This enables many convenience features (see :func:`.dictable_namedtuple` for more info) 
    such as easy casting to a :class:`dict`, and accessing fields by item/key (square brackets)::

        >>> from privex.helpers import convert_dictable_namedtuple
        >>> d_john = convert_dictable_namedtuple(john)
        >>> d_john
        Person(first_name='John', last_name='Doe')
        >>> d_john['first_name']
        'John'
        >>> dict(d_john)
        {'first_name': 'John', 'last_name': 'Doe'}
    

    :param nt_instance: An instantiated namedtuple object (using a type returned from :func:`collections.namedtuple`)
    :param str typename: Optionally, you can change the name of your instance's class, e.g. if you provide a ``Person`` 
                         instance, but you set this to ``Man``, then this will return a ``Man`` instance, like so:
                         ``Man(first_name='John', last_name='Doe')``
    :param str module: Optionally, you can change the module that the type class belongs to. Otherwise it will inherit the module path
                       from the class of your instance.
    :key bool read_only: (Default: ``False``) If set to ``True``, the outputted dictable_namedtuple instance will not
                         allow new fields to be created via attribute / item setting.
    :return dictable_namedtuple: The instance you passed ``nt_instance``, converted into a dictable_namedtuple
    """

    nt_class = nt_instance.__class__
    module = nt_class.__module__ if module is None else module

    dnt_class = subclass_dictable_namedtuple(nt_class, typename=typename, module=module, **kwargs)
    return dnt_class(**nt_instance._asdict())


def subclass_dictable_namedtuple(named_type: type, typename=None, module=None, **kwargs) -> type:
    """
    Convert an existing :func:`collections.namedtuple` **type** into a dictable_namedtuple.

    If you have an INSTANCE of a type (e.g. it has data attached), use :func:`.convert_dictable_namedtuple`

    **Example**::

        >>> from collections import namedtuple
        >>> from privex.helpers import subclass_dictable_namedtuple
        >>> # Create a namedtuple type called 'Person'
        >>> orig_Person = namedtuple('Person', 'first_name last_name')
        >>> # Convert the 'Person' type into a dictable_namedtuple
        >>> Person = subclass_dictable_namedtuple(orig_Person)
        >>> john = Person('John', 'Doe')   # Create an instance of this dictable_namedtuple Person
        >>> john['middle_name'] = 'Davis'
    
    :param type named_type: A NamedTuple type returned from :func:`collections.namedtuple`
    :param str typename: Optionally, you can change the name of your type, e.g. if you provide a ``Person`` 
                         class type, but you set this to ``Man``, then this will return a ``Man`` class type.
    :param str module: Optionally, you can change the module that the type class belongs to. Otherwise it will
                       inherit the module path from ``named_type``.
    :key bool read_only: (Default: ``False``) If set to ``True``, the outputted dictable_namedtuple type will not allow
                         new fields to be created via attribute / item setting.
    :return type dictable_namedtuple: Your ``named_type`` converted into a dictable_namedtuple type class.
    """
    typename = named_type.__name__ if typename is None else typename
    module = named_type.__module__ if module is None else module
    read_only = kwargs.pop('read_only', False)

    _dt = make_dict_tuple(typename, ' '.join(named_type._fields), read_only=read_only)

    if module is None:
        try:
            module = sys._getframe(1).f_globals.get('__name__', '__main__')
        except (AttributeError, ValueError):
            pass

    if module is not None:
        _dt.__module__ = module
    return _dt


def make_dict_tuple(typename, field_names, *args, **kwargs):
    """
    Generates a :func:`collections.namedtuple` type, with added / modified methods injected to make it
    into a ``dictable_namedtuple``.
    
    Note: You probably want to be using :func:`.dictable_namedtuple` instead of calling this directly.
    """
    read_only = kwargs.pop('read_only', False)
    module = kwargs.pop('module', None)
    
    # Create a namedtuple type to use as a base
    BaseNT = namedtuple(typename, field_names, **kwargs)

    def __init__(self, *args, **kwargs):
        self.__dict__['_extra_items'] = dict()
        for i, a in enumerate(list(args)):
            self.__dict__[self._fields[i]] = a
        for k, a in kwargs.items():
            self.__dict__[k] = a
    
    def __iter__(self):
        """This ``__iter__`` method allows for casting a dictable_namedtuple instance using ``dict(my_nt)``"""
        for k in self._fields: yield (k, getattr(self, k),)

    def __getitem__(self, item):
        """Handles when a dictable_namedtuple instance is accessed like ``my_nt['abc']`` or ``my_nt[0]``"""
        if type(item) is int:
            return self.__dict__[self._fields[item]]
        return getattr(self, item)

    def __getattr__(self, item):
        """Handles when a dictable_namedtuple instance is accessed like ``my_nt.abcd``"""
        try:
            _v = object.__getattribute__(self, '_extra_items')
            return _v[item]
        except (KeyError, AttributeError):
            return object.__getattribute__(self, item)

    def __setitem__(self, key, value):
        """Handles when a dictable_namedtuple instance is accessed like ``my_nt['abc'] = 'def'``"""
        if hasattr(self, key):
            return tuple.__setattr__(self, key, value)
        if self._READ_ONLY:
            raise KeyError(f"{self.__class__.__name__} is read only. You cannot set a non-existent field.")
        self._extra_items[key] = value
        if key not in self._fields:
            tuple.__setattr__(self, '_fields', self._fields + (key,))

    def __setattr__(self, key, value):
        """Handles when a dictable_namedtuple instance is accessed like ``my_nt.abcd = 'def'``"""
        if key in ['_extra_items', '_fields'] or key in self._fields:
            return tuple.__setattr__(self, key, value)
        if self._READ_ONLY:
            raise AttributeError(f"{self.__class__.__name__} is read only. You cannot set a non-existent field.")
        self._extra_items[key] = value
        if key not in self._fields:
            tuple.__setattr__(self, '_fields', self._fields + (key,))

    def _asdict(self):
        """
        The original namedtuple ``_asdict`` doesn't work with our :meth:`.__iter__`, so we override it
        for compatibility. Simply calls ``return dict(self)`` to convert the instance to a dict.
        """
        return dict(self)

    def __repr__(self):
        _n = ', '.join(f"{name}='{getattr(self, name)}'" for name in self._fields)
        return f"{self.__class__.__name__}({_n})"

    # Inject our methods defined above into the namedtuple type BaseNT
    BaseNT.__getattr__ = __getattr__
    BaseNT.__getitem__ = __getitem__
    BaseNT.__setitem__ = __setitem__
    BaseNT.__setattr__ = __setattr__
    BaseNT._asdict = _asdict
    BaseNT.__repr__ = __repr__
    BaseNT.__iter__ = __iter__
    BaseNT.__init__ = __init__
    BaseNT._READ_ONLY = read_only
    
    # Create a class for BaseNT with tuple + object mixins, allowing things like __dict__ to function properly
    # and allowing for tuple.__setattr__ / object.__getattribute__ calls.
    class K(BaseNT, tuple, object):
        pass

    # Get the calling module so we can overwrite the module name of the class.
    if module is None:
        try:
            module = sys._getframe(1).f_globals.get('__name__', '__main__')
        except (AttributeError, ValueError):
            pass
    
    # Overwrite the type name + module to match the originally requested typename
    K.__name__ = BaseNT.__name__
    K.__qualname__ = BaseNT.__qualname__
    K.__module__ = module

    return K


def dictable_namedtuple(typename, field_names, *args, **kwargs) -> Union[Type[namedtuple], dict]:
    """
    Creates a dictable_namedtuple type for instantiation (same usage as :func:`collections.namedtuple`) - unlike
    namedtuple, dictable_namedtuple instances allow item (dict-like) field access, support writing and can be
    painlessly converted into dictionaries via ``dict(my_namedtuple)``.

    Named tuple instances created from ``dictable_namedtuple`` types are generally backwards compatible with
    any code that expects a standard :func:`collections.namedtuple` type instance.

    **Quickstart**

        >>> from privex.helpers import dictable_namedtuple
        >>> # Define a dictable_namedtuple type of 'Person', which has two fields - first_name and last_name
        >>> p = dictable_namedtuple('Person', 'first_name last_name')
        >>> john = p('John', 'Doe')    # Alternatively you can do p(first_name='John', last_name='Doe')
        >>> john.first_name            # You can retrieve keys either via attributes (dot notation)
        'John'
        >>> john['last_name']          # Via named keys (square brackets)
        'Doe'
        >>> john[1]                    # Or, via indexed keys (square brackets, with integer keys)
        'Doe'
        >>> john.middle_name = 'Davis' # You can also update / set new keys via attribute/key/index
        >>> dict(john)                 # Newly created keys will show up as normal in dict(your_object)
        {'first_name': 'John', 'last_name': 'Doe', 'middle_name': 'Davis'}
        >>> john                       # As well as in the representation in the REPL or when str() is called.
        Person(first_name='John', last_name='Doe', middle_name='Davis')

    This function adds / overrides the following methods on the generated namedtuple type:

    * _asdict
    * __iter__
    * __getitem__
    * __getattribute__
    * __setitem__
    * __setattr__
    * __repr__

    Extra functionality compared to the standard :func:`.namedtuple` generated classes:

        * Can access fields via item/key: ``john['first_name']``

        * Can convert instance into a dict simply by casting: ``dict(john)``

        * Can set new items/attributes on an instance, even if they weren't previously defined.
          ``john['middle_name'] = 'Davis'`` or ``john.middle_name = 'Davis'``

    **Example Usage**

    First we'll create a named tuple typle called ``Person``, which takes two arguments, first_name and last_name.

        >>> from privex.helpers import dictable_namedtuple
        >>> Person = dictable_namedtuple('Person', 'first_name last_name')
    
    Now we'll create an instance of ``Person`` called ``john``. These instances look like normal ``namedtuple``'s, and
    should be generally compatible with any functions/methods which deal with named tuple's.

        >>> john = Person('John', 'Doe')   # Alternatively you can do Person(first_name='John', last_name='Doe')
        >>> john
        Person(first_name='John', last_name='Doe')
    
    Unlike a normal ``namedtuple`` type instance, we can access fields by attribute (``.first_name``), index (``[0]``), 
    AND by item/key name (``['last_name']``).

        >>> john.first_name
        'John'
        >>> john[0]
        'John'
        >>> john['last_name']
        'Doe'
    
    Another potentially useful feature, is that you can also update / create new fields, via your preferred method
    of field notation (other than numbered indexes, since those don't include a field name)::

        >>> john['middle_name'] = 'Davis'
        >>> john.middle_name = 'Davis'

    We can also convert ``john`` into a standard dictionary, with a simple ``dict(john)`` cast. You can see that
    the new field we added (``middle_name``) is present in the dictionary serialized format.

        >>> dict(john)
        {'first_name': 'John', 'last_name': 'Doe', 'middle_name': 'Davis'}
    

    :param str typename: The name used for the namedtuple type/class
    :param str field_names: One or more field names separated by spaces, e.g. ``'id first_name last_name address'``
    :key bool read_only: (Default: ``False``) If set to ``True``, the outputted dictable_namedtuple instance will not
                         allow new fields to be created via attribute / item setting.
    :return Type[namedtuple] dict_namedtuple: A dict_namedtuple type/class which can be instantiated with the given
                             ``field_names`` via positional or keyword args.
    """
    module = kwargs.get('module', None)
    read_only = kwargs.pop('read_only', False)
    
    # As per namedtuple's comment block, we need to set __module__ to the frame
    # where the named tuple is created, otherwise it can't be pickled properly.
    # This also ensures that __module__ would match that of a normal namedtuple()
    if module is None:
        try:
            module = sys._getframe(1).f_globals.get('__name__', '__main__')
        except (AttributeError, ValueError):
            pass

    return make_dict_tuple(typename, field_names, module=module, read_only=read_only, *args, **kwargs)


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

    def __getitem__(self, key):
        """
        When the instance is accessed like a dict, try returning the matching attribute.
        """
        if hasattr(self, key): return getattr(self, key)
        raise KeyError(key)

    def __setitem__(self, key, value):
        """
        When the instance is modified like a dict, try setting the matching attribute.
        """
        return setattr(self, key, value)

    def get(self: Union[Type["dataclasses.dataclass"], "dataclasses.dataclass"], key, fallback=None):
        names = set([f.name for f in dataclasses.fields(self)])
        return getattr(self, key) if key in names else fallback

    @classmethod
    def from_dict(cls, env):
        # noinspection PyArgumentList
        return cls(**{
            k: v for k, v in env.items()
            if k in inspect.signature(cls).parameters
        })

    @classmethod
    def from_list(cls: Type[T], obj_list: Iterable[dict]) -> Generator[T, None, None]:
        for o in obj_list:
            yield cls.from_dict(o)


class DictDataClass(Dictable):
    """
    This is a base class for use with Python 3.7+ :class:`.dataclass` 's, designed to make dataclasses more interoperable with
    existing dictionaries, and allows them to be used like dictionaries, similar to :class:`.Dictable`, but more powerful /
    flexible.
    
    The most notable difference between this and :class:`.Dictable` - is that DictDataClass uses the attribute :attr:`.raw_data` on your
    dataclass to store any excess attributes when your dataclass is initialised from a dictionary with :meth:`.from_dict`
    or :meth:`.from_list`, allowing you to retrieve any dictionary keys which couldn't be stored on your dataclass instance.
    
    Basic Example::
    
        >>> from dataclasses import dataclass, field
        >>> from privex.helpers import DictDataClass, DictObject
        >>> from typing import Union
        >>>
        >>> @dataclass
        >>> class ExampleDataclass(DictDataClass):
        ...     example: str = 'hello world'
        ...     lorem: int = 999
        ...     raw_data: Union[dict, DictObject] = field(default_factory=DictObject, repr=False)
        ...     ### ^ The raw, unmodified data that was passed as kwargs, as a dictionary
        ...     ### For DictDataClass to work properly, you must include the raw_data dataclass field in your dataclass.
        ...
        >>> edc = ExampleDataclass.from_dict(dict(example='test', hello='this is an example'))
        >>> edc.example
        'test'
        >>> dict(edc)
        {'example': 'test', 'lorem': 999}
    
    Thanks to :attr:`.raw_data` - you can access any extraneous items contained within the dictionary used in :meth:`.from_dict`
    as if they were part of your dataclass. You can also access and set any attribute using standard dictionary item syntax with square
    brackets like so::
    
        >>> edc.hello               # This is not in the original dataclass attributes, but is proxied from raw_data
        'this is an example'
        >>> edc['hello']            # Also works with item / dict syntax
        'this is an example'
        >>> edc['hello'] = 'world'  # You can set attributes using "key" / dict-like syntax
        >>> edc.hello
        'world'
        >>> edc.hello = 'test'      # You can also set raw_data keys using standard attribute dot-notation syntax.
        >>> edc['hello']
        'test'
     
    **Dictionary casting modes / ``__iter__`` configuration modes**
    
    There are a total of four (4) :class:`.dict`` conversion modes that you may use for a given class.
    
    These modes control whether :attr:`.raw_data` is used when an instance is being casted via ``dict(obj)``, the order in which it's
    merged with the instance attributes, along with the option to include **just** the dataclass attributes, or **just** the raw_data.
    
    Available :attr:`.DictConfig.dict_convert_mode` options::
    
        * **Fallback / Dataclass / Instance Attributes Only** - When ``dict_convert_mode`` is empty (``None`` or ``""``), or
          it can't be matched against a pre-defined conversion mode, when an instance is converted into a :class:`.dict` - only the
          attributes of the instance are used - :attr:`.raw_data` keys are ignored.
          
          ``dict_convert_mode`` settings: ``None``, ``""``, ``"none"`` or any other invalid option.
        
        * Raw Data Only ( ``raw`` / ``raw_data`` ) - When this mode is used, converting the instance to a ``dict`` will
          effectively just return ``raw_data``, while still enforcing the ``dict_exclude`` and ``dict_listify`` settings.
          
          ``dict_convert_mode`` settings: ``"raw"``, ``"raw_data"``, ``"rawdata"``, or any other value beginning with ``raw``
        
        
        * Merge with Dataclass Priority - In this mode, both :attr:`.raw_data` and the instance's attributes are used when converting
          into a :class:`.dict` - first the :attr:`.raw_data` dictionary is taken, and we merge the instance attributes on top of it.
          
          This means the instance/dataclass attributes take priority over the ``raw_data`` attributes, which will generally result
          in only ``raw_data`` keys which don't exist on the instance having their values used in the final ``dict``.
        
          ``dict_convert_mode`` settings: ``"merge_dc"`` / ``"merge_ins"`` / ``"merge_dataclass"``
        
        * Merge with :attr:`.raw_data` Priority - In this mode, both :attr:`.raw_data` and the instance's attributes are used when
          converting into a :class:`.dict` - first the instance attributes are converted into a dict, then we merge the
          :attr:`.raw_data` dictionary on top of it.
          
          This means the :attr:`.raw_data` keys take priority over the instance/dataclass attributes, which will generally result in
          only instance attributes which don't exist in ``raw_data`` having their values used in the final ``dict``.
        
          ``dict_convert_mode`` settings: ``"merge_rd"`` / ``"merge_raw"`` / ``"merge_raw_data"``
    
    By default, the conversion mode is set to ``merge_dc``, which means when an instance is converted into a :class:`.dict` - the
    dataclass instance attributes are merged on top of the raw_data dictionary, meaning raw_data is included, but dataclass attributes
    take priority over :attr:`.raw_data` keys.
    
    **Changing the conversion mode**
    
        >>> from dataclasses import dataclass, field
        >>>
        >>> @dataclass
        >>> class MyDataclass(DictDataClass):
        ...     class DictConfig:
        ...         dict_convert_mode = 'merge_dc'
        ...
        ...     hello: str
        ...     lorem: str = 'ipsum'
        ...     raw_data: Union[dict, DictObject] = field(default_factory=DictObject, repr=False)
        >>> dc = MyDataclass.from_dict(dict(hello='test', example=555, test='testing'))
        >>> dc.hello
        'test'
        >>> dc.hello = 'replaced'
        >>> dict(dc)
        {'hello': 'replaced', 'example': 555, 'test': 'testing', 'lorem': 'ipsum'}
        >>> dc.DictConfig.dict_convert_mode = 'merge_raw'
        {'hello': 'test', 'lorem': 'ipsum', 'example': 555, 'test': 'testing'}
        >>> dc.DictConfig.dict_convert_mode = None
        {'hello': 'replaced', 'lorem': 'ipsum'}
    
    """
    raw_data: Union[dict, DictObject]
    
    class _DictConfig:
        dict_convert_mode: Optional[str] = "merge_dc"
        dict_listify: List[str] = []
        """
        Keys which contain iterable's (list/set etc.) of objects such as those based on :class:`.DictDataClass` / :class:`.Dictable`,
        which should be converted into a list of :class:`.dict`'s using ``dict()``.
        
        Example:
        
            >>> @dataclass
            >>> class Order(DictDataClass):
            ...     hello: str = 'world'
            >>>
            >>> class MyDataclass(DictDataClass):
            ...     class DictConfig:
            ...         dict_listify = ['orders']
            ...     lorem = 'ipsum'
            ...     orders: list = [Order(), Order('test')]
            ...
        """
        listify_cast: Union[Type, callable] = DictObject
        dict_exclude_base: List[str] = ['raw_data', 'DictConfig', '_DictConfig']
        dict_exclude: List[str] = []
        """
        A list of attributes / raw_data keys to exclude when your instance is converted into a :class:`.dict`
        """
    
    @property
    def _dc_dict_config(self) -> Union[_DictConfig, DictObject]:
        """Internal property used to merge the base DictDataClass _DictConfig with the current instance's DictConfig"""
        base = {k: v for k, v in self._DictConfig.__dict__.items() if not k.startswith('__')}
        inst = {k: v for k, v in self.DictConfig.__dict__.items() if not k.startswith('__')}
        return DictObject({**base, **inst})
    
    DictConfig = copy_class(_DictConfig, name='DictConfig', quiet=True)

    def __iter__(self):
        cls_name = self.__class__.__name__
        # The raw_data attribute isn't required, and isn't guaranteed to have been set on a dataclass, so
        # we fallback to a blank DictObject if it's not found.
        dict_rd = DictObject()
        if hasattr(self, 'raw_data'):
            dict_rd = dict(self.raw_data)
        
        # dataclasses.asdict can sometimes freak out when a dataclass contains un-serializable objects such as arbitrary
        # class instances (which may even be excluded already in DictConfig. In such a case, we can fallback to __dict__ :)
        try:
            dict_dc = dataclasses.asdict(self, dict_factory=dict)
        except (TypeError, ValueError, JSONDecodeError) as e:
            log.warning("Dictifying %s using dataclasses.asdict failed (%s %s)... falling back to __dict__", cls_name, type(e), str(e))
            dict_dc = dict(self.__dict__)

        from privex.helpers import empty
        dconf = self._dc_dict_config
        mode = "" if empty(dconf.dict_convert_mode, True, True) else str(dconf.dict_convert_mode).lower()
        # By default, if dict_convert_mode is None, or doesn't match any of the pre-defined modes, then it
        # defaults to dict_dc (the instance's dataclass attributes, converted into a dictionary)
        itr = dict_dc
        if mode in ['merge_dc', 'merge_ins', 'merge_dataclass']:
            itr = {**dict_rd, **dict_dc}
        elif mode in ['merge_rd', 'merge_raw', 'merge_raw_data']:
            itr = {**dict_dc, **dict_rd}
        elif mode.startswith('raw'):
            itr = dict_rd
        
        exclude = dconf.dict_exclude_base + dconf.dict_exclude
        
        for k, v in itr.items():
            # Don't include any dict keys which are listed in dict_exclude/dict_exclude_base
            if k in exclude: continue
            # If this key is listed in dict_listify, then we iterate over the current value, casting
            # each element using the type/callable specified in DictConfig.listify_case
            # (defaults to DictObject, which is backwards compatible with code requiring dict's)
            if k in dconf.dict_listify: v = [dconf.listify_cast(o) for o in v]
            yield (k, v,)
    
    def __getitem__(self, key):
        """
        When the instance is accessed like a dict, try returning the matching attribute.
        If the attribute doesn't exist, or the key is an integer, try and pull it from raw_data
        """
        if hasattr(self, 'raw_data') and type(key) is int: return self.raw_data[key]
        if hasattr(self, key): return getattr(self, key)
        if hasattr(self, 'raw_data') and key in self.raw_data: return self.raw_data[key]
        raise KeyError(key)

    def __setitem__(self, key, value):
        """
        When the instance is modified like a dict, try setting the matching attribute.
        If the key is an int, or exists in raw_data, then set it on raw_data instead of as a dataclass attribute.
        """
        if hasattr(self, 'raw_data') and type(key) is int:
            self.raw_data[key] = value
            return
        
        if hasattr(self, 'raw_data') and key in self.raw_data:
            self.raw_data[key] = value
            return
        
        return setattr(self, key, value)
    
    def __getattr__(self, item):
        # object.__getattribute__()
        def ha(key):
            return key in self.__dict__
        
        if ha('raw_data') and type(item) is int:
            return self.__dict__['raw_data'][item]
        if ha(item):
            return self.__dict__[item]
        if ha('raw_data') and item in self.__dict__['raw_data']:
            return self.__dict__['raw_data'][item]
        raise AttributeError(item)
    
    def __setattr__(self, key, value):
        def ha(k): return k in self.__dict__
        
        if ha(key):
            self.__dict__[key] = value
            return
        
        if ha('raw_data'):
            self.__dict__['raw_data'][key] = value
            return
        
        return super().__setattr__(key, value)
    
    @classmethod
    def from_dict(cls: Type[dataclass], obj):
        names = set([f.name for f in dataclasses.fields(cls)])
        clean = {k: v for k, v in obj.items() if k in names}
        if 'raw_data' in names:
            clean['raw_data'] = DictObject(clean.get('raw_data')) if 'raw_data' in clean else DictObject(obj)
        return cls(**clean)
    

DictDataclass = DictDataClass

