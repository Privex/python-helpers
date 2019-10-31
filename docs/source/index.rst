.. _Privex Python Helpers documentation:



Privex Python Helpers's documentation
=================================================

.. image:: https://www.privex.io/static/assets/svg/brand_text_nofont.svg
   :target: https://www.privex.io/
   :width: 400px
   :height: 400px
   :alt: Privex Logo
   :align: center

Welcome to the documentation for `Privex's Python Helpers`_ - a small, open source Python 3 package
containing a variety of functions, classes, exceptions, decorators and more - each of which would otherwise
be too small to maintain in an individual package.

This documentation is automatically kept up to date by ReadTheDocs, as it is automatically re-built each time
a new commit is pushed to the `Github Project`_ 

.. _Privex's Python Helpers: https://github.com/Privex/python-helpers
.. _Github Project: https://github.com/Privex/python-helpers

.. contents::


Quick install
-------------

**Installing with** `Pipenv`_ **(recommended)**

.. code-block:: bash

    pipenv install privex-helpers


**Installing with standard** ``pip3``

.. code-block:: bash

    pip3 install privex-helpers



.. _Pipenv: https://pipenv.kennethreitz.org/en/latest/




Python Module Overview
----------------------

Privex's Python Helpers is organised into various sub-modules to make it easier to find the
functions/classes you want to use, and to avoid having to load the entire module (though it's lightweight).

With the exception of :mod:`privex.helpers.django` (Django gets upset if certain django modules are imported before
it's initialised), **all functions/classes are imported within the** ``__init__`` **file,** allowing you to simply type:

.. code-block:: python

    from privex.helpers import empty, run_sync, asn_to_name

Instead of having to import the functions from each individual module:

.. code-block:: python

    from privex.helpers.common import empty
    from privex.helpers.asyncx import run_sync
    from privex.helpers.net import asn_to_name

Below is a listing of the sub-modules available in ``privex-helpers`` with a short description of what each module
contains.

.. include:: helpers/index.rst


All Documentation
=================

.. toctree::
   :maxdepth: 8
   :caption: Main:

   self
   install
   examples


.. toctree::
   :maxdepth: 3
   :caption: Code Documentation:

   helpers/index

.. toctree::
   :caption: Unit Testing

   helpers/tests


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
