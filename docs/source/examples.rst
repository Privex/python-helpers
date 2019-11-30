##############
Example Usages
##############

Boolean testing
===============

The ``empty`` function
-----------------------

The :func:`empty` function in our opinion, is one of most useful functions in this library. It allows for a clean,
readable method of checking if a variable is "empty", e.g. when checking keyword arguments to a function.

With a single argument, it simply tests if a variable is ``""`` (empty string) or ``None``.

The argument ``itr`` can be set to ``True`` if you consider an empty iterable such as ``[]`` or ``{}`` as "empty". This
functionality also supports objects which implement ``__len__``, and also checks to ensure ``__len__`` is available,
avoiding an exception if an object doesn't support it.

The argument ``zero`` can be set to ``True`` if you want to consider ``0`` (integer) and ``'0'`` (string) as "empty".

.. code-block:: python

    from privex.helpers import empty

    x, y = "", None
    z, a = [], 0

    empty(x) # True
    empty(y) # True
    empty(z) # False
    empty(z, itr=True) # True
    empty(a) # False
    empty(a, zero=True) # True


The ``is_true`` and ``is_false`` functions
------------------------------------------

When handling user input, whether from an environment file (``.env``), or from data passed to a web API, it can be
a pain attempting to check for booleans.

A boolean ``True`` could be represented as the string ``'true'``, ``'1'``, ``'YES'``, as an integer ``1``, or even
an actual boolean ``True``. Trying to test for all of those cases requires a rather long ``if`` statement...

Thus :func:`.is_true` and :func:`.is_false` were created.

.. code-block:: python

    from privex.helpers import is_true, is_false

    is_true(0)          # False
    is_true(1)          # True
    is_true('1')        # True
    is_true('true')     # True
    is_true('false')    # False
    is_true('orange')   # False
    is_true('YeS')      # True

    is_false(0)         # True
    is_false('false')   # True
    is_false('true')    # False
    is_false(False)     # True


Handling environmental variables in different formats
=====================================================

Using ``env_csv`` to support lists contained within an env var
---------------------------------------------------------------

The function :func:`.env_csv` parses a CSV-like environment variable into a list

.. code-block:: python

    from privex.helpers import env_csv
    import os
    os.environ['EXAMPLE'] = "this,   is, an,example   "

    env_csv('EXAMPLE', ['error'])
    # returns: ['this', 'is', 'an', 'example']
    env_csv('NOEXIST', ['non-existent'])
    # returns: ['non-existent']

Using ``env_keyval`` to support dictionaries contained within an env var
------------------------------------------------------------------------

The function :func:`.env_keyval` parses an environment variable into a ordered list of tuple pairs, which can be
easily converted into a dictionary using ``dict()``.

.. code-block:: python

    from privex.helpers import env_keyval
    import os
    os.environ['EXAMPLE'] = "John:  Doe , Jane   : Doe, Aaron:Smith"

    env_keyval('EXAMPLE')
    # returns: [('John', 'Doe'), ('Jane', 'Doe'), ('Aaron', 'Smith')]
    env_keyval('NOEXIST', {})
    # returns: {}


Improved collections, including dict's and namedtuple's
=======================================================

In our :py:mod:`privex.helpers.collections` module (plus maybe a few things in :py:mod:`privex.helpers.common`),
we have various functions and classes designed to make working with Python's storage types more painless, while
trying to keep compatibility with code that expects the native types.


Dictionaries with dot notation attribute read/write
---------------------------------------------------

Dictionaries (``dict``) are powerful, and easy to deal with. But why can't you read or write dictionary items with 
attribute dot notation!?

This is where :class:`.DictObject` comes in to save the day. It's a child class of python's native :class:`dict` type, which
means it's still compatible with functions/methods such as :func:`json.dumps`, and in most cases will be plug-n-play with
existing dict-using code.

**Basic usage**

.. code-block:: python

    from privex.helpers import DictObject

    x = dict(hello='world', lorem='ipsum')
    x['hello']  # This works with a normal dict
    x.hello     # But this raises: AttributeError: 'dict' object has no attribute 'hello'

    # We can cast the dict 'x' into a DictObject
    y = DictObject(x)
    y['hello']         # Returns: 'world'
    y.hello            # Returns: 'world'

    # Not only can you access dict keys via attributes, you can also set keys via attributes
    y.example = 'testing'
    y                  # We can see below that setting 'example' worked as expected.
    # Output: {'hello': 'world', 'lorem': 'ipsum', 'example': 'testing'}


**Type checking / Equality comparison**

As :class:`.DictObject` is a subclass of :class:`dict`, you can use :func:`isinstance` to check against :class:`dict` 
(e.g.  ``isinstance(DictObject(), dict)``) and it should return True.

You can also compare dictionary equality between a :class:`.DictObject` and a :class:`dict` using ``==`` as normal.

.. code-block:: python

    y = DictObject(hello='world')

    isinstance(y, dict)   # You should always use isinstance instead of `type(x) == dict`
    # Returns: True

    # You can also use typing.Dict with isinstance when checking a DictObject
    from typing import Dict
    isinstance(y, Dict)   # Returns: True

    # You can compare equality between a DictObject and a dict with no problems
    DictObject(hello='world') == dict(hello='world')
    # Returns: True
    DictObject(hello='world') == dict(hello='example')
    # Returns: False

**Type Masquerading**

Also included is the class :class:`.MockDictObj`, which is a subclass of :class:`.DictObject` with it's name, qualified name,
and module adjusted so that it appears to be the builtin :class:`dict` type.

This may help in some cases, but sadly can't fool a ``type(x) == dict`` check.

.. code-block:: python

    from privex.helpers import MockDictObj
    z = MockDictObj(y)
    type(z)                  # Returns: <class 'dict'>
    z.__class__.__module__   # Returns: 'builtins'



Named Tuple's (namedtuple) with dict-like key access, dict casting, and writable fields
---------------------------------------------------------------------------------------

A somewhat simpler version of :class:`dict`'s are :func:`collections.namedtuple`'s

Unfortunately they have a few quirks that can make them annoying to deal with.

.. code-block:: python

    Person = namedtuple('Person', 'first_name last_name')  # This is an existing namedtuple "type" or "class"
    john = Person('John', 'Doe')  # This is an existing namedtuple instance
    john.first_name               # This works on a standard namedtuple. Returns: John
    john[1]                       # This works on a standard namedtuple. Returns: Doe
    john['first_name']            # However, this would throw a TypeError.
    dict(john)                    # This would throw a ValueError.
    john.address = '123 Fake St'  # This raises an AttributeError.

Thus, we created :func:`.dictable_namedtuple` (and more), which creates namedtuples with additional functionality,
including item/key access of fields, easy casting into dictionaries, and ability to add new fields.

.. code-block:: python

    from privex.helpers import dictable_namedtuple
    Person = dictable_namedtuple('Person', 'first_name last_name')
    john = Person('John', 'Doe')
    dave = Person(first_name='Dave', last_name='Smith')
    print(dave['first_name'])       # Prints:  Dave
    print(dave.first_name)          # Prints:  Dave
    print(john[1])                  # Prints:  Doe
    print(dict(john))               # Prints:  {'first_name': 'John', 'last_name': 'Doe'}
    john.address = '123 Fake St'    # Unlike normal namedtuple, we can add new fields
    print(john)                     # Prints: Person(first_name='John', last_name='Doe', address='123 Fake St')


You can use :func:`.convert_dictable_namedtuple` to convert existing ``namedtuple`` instancess
into ``dictable_namedtuple`` instances:

.. code-block:: python

    Person = namedtuple('Person', 'first_name last_name')  # This is an existing namedtuple "type" or "class"
    john = Person('John', 'Doe')  # This is an existing namedtuple instance

    d_john = convert_dictable_namedtuple(john)
    d_john.first_name               # Returns: John
    d_john[1]                       # Returns: Doe
    d_john['first_name']            # Returns: 'John'
    dict(d_john)                    # Returns: {'first_name': 'John', 'last_name': 'Doe'}

For more information, check out the module docs at :mod:`privex.helpers.collections`

