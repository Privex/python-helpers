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
import inspect
import sys
from collections import namedtuple, OrderedDict
from typing import Dict, Optional, NamedTuple, Union, Type
import logging

log = logging.getLogger(__name__)


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
        return super().__getitem__(item)

    def __setattr__(self, key, value):
        """When an attribute is set, e.g. ``x.something = 'abcd'``, forward it to ``dict['something'] = 'abcd'``"""
        if hasattr(super(), key):
            return super().__setattr__(key, value)
        return super().__setitem__(key, value)
    

class OrderedDictObject(OrderedDict):
    """
    Ordered version of :class:`.DictObject` - dictionary with attribute access.
    See :class:`.DictObject`
    """
    def __getattr__(self, item):
        """When an attribute is requested, e.g. ``x.something``, forward it to ``dict['something']``"""
        if hasattr(super(), item):
            return super().__getattribute__(item)
        return super().__getitem__(item)
    
    def __setattr__(self, key, value):
        """When an attribute is set, e.g. ``x.something = 'abcd'``, forward it to ``dict['something'] = 'abcd'``"""
        if hasattr(super(), key):
            return super().__setattr__(key, value)
        return super().__setitem__(key, value)


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

    @classmethod
    def from_dict(cls, env):
        # noinspection PyArgumentList
        return cls(**{
            k: v for k, v in env.items()
            if k in inspect.signature(cls).parameters
        })


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



