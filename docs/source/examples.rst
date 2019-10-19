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

