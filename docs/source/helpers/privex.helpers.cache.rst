Framework-independent Cache System
==================================

(part of ``privex.helpers.cache``)


.. automodule:: privex.helpers.cache


   
   
   
Base/Core Caching System
------------------------

Below are functions and classes contained within :mod:`privex.helpers.cache` (inside the module
init file ``__init__.py``) - these functions/classes provide a high-level entry point into the
**Privex Helper's Framework Independent Caching System**


   .. rubric:: Functions

   .. autosummary::
      :toctree: cache
   
      adapter_get
      adapter_set
      get
      get_or_set
      remove
      set
      update_timeout


   .. rubric:: Attributes

   .. autosummary::
      :toctree: cache

      cached
      async_cached

   
   .. rubric:: Classes

   .. autosummary::
      :toctree: cache
   
      CacheWrapper
      AsyncCacheWrapper

Extra Modules
-------------


.. autosummary::
   :toctree: cache/extras

   extras

.. autosummary::
   :toctree: cache/post_deps

   post_deps


Synchronous Cache Adapters
--------------------------


Currently, Privex Helper's caching system includes two synchronous cache adapters for use by the user, along
with the base adapter class :class:`.CacheAdapter`

**In-memory Cache**

:class:`.MemoryCache` is the cache adapter used by default by the cache abstraction system, if you don't change
the adapter in your application using :func:`.adapter_set`. **MemoryCache** requires no additional dependencies
to use, and can handle caching practically anything you throw at it, since it simply stores the cache
in a python :class:`.dict` dictionary within your applications memory.

**Redis Cache**

:class:`.RedisCache` is the second pre-included synchronous cache adapter, unlike :class:`.MemoryCache`, it requires
the package ``redis`` to function. The ``redis`` package is included in the privex-helpers' extra ``cache``.

To use the ``cache`` extra, simply change ``privex-helpers`` in your ``requirements.txt`` to: ``privex-helpers[cache]``

Similarly, if installing the package on the command line, you can run: ``pip3 install "privex-helpers[cache]"`` and
then Pip will install both ``privex-helpers``, along with some additional dependencies to be able to use
all of the available cache adapters.

**Class List**


   .. rubric:: Classes

   .. autosummary::
      :toctree: cache

      ~CacheAdapter.CacheAdapter
      ~MemoryCache.MemoryCache
      ~RedisCache.RedisCache
      ~MemcachedCache.MemcachedCache
      ~SqliteCache.SqliteCache




AsyncIO Cache Adapters
----------------------


.. automodule:: privex.helpers.cache.asyncx


.. autosummary::
   :toctree: cache/asyncx

   AsyncRedisCache
   AsyncMemoryCache
   AsyncMemcachedCache
   AsyncSqliteCache
   base







