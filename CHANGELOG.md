-----------------------------------------------------------------------------------------------------------------------

3.2.0 - Added MemcachedCache + privex.helpers.cache.extra, plus various other additions
====================================================================================================================

-----------------------------------------------------------------------------------------------------------------------

Author: Chris (Someguy123)
Date:   Mon Nov 2 03:26 AM 2020 +0000

- **privex.helpers.settings**
    - Added `DEFAULT_CACHE_ADAPTER` which can be adjusted via the env var `PRIVEX_CACHE_ADAPTER`. This setting allows
      overriding the cache adapter which is used automatically by default via `cached` / `async_cached`, along with
      the global adapter when you call `get_adapter`
      
    - Added `DEFAULT_ASYNC_CACHE_ADAPTER` which can be adjusted via the env var `PRIVEX_ASYNC_CACHE_ADAPTER`.
      It defaults to the same value as `DEFAULT_CACHE_ADAPTER`, since thanks to the new `import_adapter` function
      and `ADAPTER_MAP` dictionary in `privex.helpers.cache`, it's now possible to reference cache adapters by simple
      names such as `memcached`, `redis`, `sqlite3`, `memory` etc. - and these aliases point to either the synchronous
      or asyncio version of their related adapter depending on which context they're being passed into. 

- **privex.helpers.cache**
    - Added `MemcachedCache` module, which contains the synchronous cache adapter `MemcachedCache`. This is simply a synchronous
      version of `AsyncMemcachedCache` that uses `pylibmc` instead of `aiomcache`.
      
    - Added `ADAPTER_MAP` dictionary, which maps aliases such as `memcached`, `redis`, `sqlite3`, `memory` etc. to their
      respective synchronous and asyncio adapter module paths, which can be loaded using the 
      newly added `import_adapter` function, or simply using `adapter_set` / `async_adapter_set`.
      
    - Added `import_adapter` function, which looks up an adapter alias name such as `redis` / `memcached`, maps it
      to the fully qualified module path via `ADAPTER_MAP`, and then loads the module + extracts the class from the module.
     
    - Adjusted `adapter_set`, `async_adapter_set`, along with `CacheWrapper` + `AsyncCacheWrapper` so that they now use the
      default string cache adapter defined in `settings`, and can transparently handle string adapter values by passing 
      them off to `import_adapter`.
    
    - Added new `extras` module
    
        - `CacheManagerMixin` is a class mixin which adds various methods and settings to assist with class-scoped caching, 
           including an adjustable class-level cache prefix `.cache_prefix`, a method to remove all known cache keys managed by
           your class `.clear_all_cache_keys`, and a special decorator which automatically integrates with your class `.z_cache`
           by intercepting the first argument of a method call.
           
        - `z_cache` - A special method caching decorator which is designed to integrate with classes that 
           extend `.CacheManagerMixin`
              
          This is simply a wrapper for `.r_cache` - it transparently caches the output of a wrapped method/function, but
          unlike `.r_cache`, it's designed to automatically integrate with classes which extend `.CacheManagerMixin` ,
          allowing it to automatically retrieve cache settings such as the cache prefix, default cache time, along with 
          directly calling various classmethods which enable logging of newly created `cache_key` 's for painless cleanup of
          cache keys when needed, without having to manually track them, or doing the nuclear option of erasing the entire
          cache system's database.

- **privex.helpers.common**
    - Added new small helper function `auto_list`, which is a small but useful function that simplifies the conversion
      of objects into lists, sets, tuples etc. with the option to manually force a certain conversion method,
      either `list wrapping` or `list iteration`

- **privex.helpers.plugin**
    - Added various functions for managing **memcached instances** via the `pylibmc` library
        - `connect_memcached` - create a new memcached `Client` object
        - `get_memcached` - get or create a Memcached `Client` object shared by your thread
        - `close_memcached` - close the Memcached `Client` connection and delete it from the threadstore
        - `reset_memcached` - close the shared `Client` then re-create it again.
        - `configure_memcached` - configure Memcached settings then automatically reset the shared `Client` instance.
    - Added new `HAS_MEMCACHED` boolean value, to track whether synchronous memcached via `pylibmc` is available

- General stuff
    - Added `pylibmc` to extras/cache.txt
    - Added some missing packages to the `Pipfile` - and synchronised `Pipfile.lock`
    - Added `.env` to `.gitignore`
    - Created unit tests for the new `CacheManagerMixin` class and `z_cache` decorator
    - Created unit tests for the new `MemcachedCache` cache adapter
    - Fixed the `live` command in `docs/Makefile` for newer `sphinx-autobuild`
    - Added `SqliteCache` and `MemcachedCache` to the docs
    - Added `privex.helpers.cache.extras` and `privex.helpers.cache.post_dep` to the docs
    - Added some other missing things to the docs
    - Created and updated a lot of stub files in `privex_stubs` (assists IDEs like PyCharm with type hinting 
        and function/method previews)
    - Possibly other various additions / fixes / improvements that I forgot to list.

-----------------------------------------------------------------------------------------------------------------------

3.1.0 - Added SqliteCache + AsyncSqliteCache, plus minor fixes in privex.helpers.plugin
====================================================================================================================

-----------------------------------------------------------------------------------------------------------------------

Author: Chris (Someguy123)
Date:   Wed Oct 7 11:36 2020 +0000

- **privex.helpers.cache**
    - Added `SqliteCache` module, containing the synchronous cache adapter `SqliteCache` which uses an Sqlite3 database for
      persistent cache storage without the need for any extra system service (unlike the memcached / redis adapters)

    - Added `asyncx.AsyncSqliteCache` module, containing the AsyncIO cache adapter `AsyncSqliteCache`, which is simply an 
      AsyncIO version of `SqliteCache` using the `aiosqlite` library.
        - **NOTE:** Due to the file-based nature of SQLite3, combined with the fact write operations generally result in the
          database being locked until the write is completed - use of the AsyncIO SQLite3 cache adapter only *slightly*
          improves performance, due to the blocking single-user nature of SQLite3.

    - Added `post_deps` module, short for **post-init dependencies**. This module contains functions and classes which are
      known to have (or have a high risk of) recursive import conflicts - e.g. the new SQLite caching uses the `privex-db`
      package, and the `privex-db` package imports various things from `privex.helpers` causing a recursive import issue if we
      load `privex.db` within a class that's auto-loaded in an `__init__.py` file.

      The nature of this module means that none of it's contents are auto-loaded / aliased using `__init__.py` module constructor 
      files. This shouldn't be a problem for most people though, as the functions/classes etc. within the module are primarily
      only useful for certain cache adapter classes, rather than intended for use by the users of `privex-helpers` 
      (though there's nothing stopping you from importing things from `post_deps` in your own project).

        - `sqlite_cache_set_dbfolder` and `sqlite_cache_set_dbname` are two module level functions that are intended for use
          by users. These functions allow you to quickly override the `DEFAULT_DB_FOLDER` and/or `DEFAULT_DB_NAME` dynamically
          for both SqliteCacheManager and AsyncSqliteCacheManager.
        - `SqliteCacheResult` is a namedtuple that represents a row returned when querying the `pvcache` table within 
          an SQLite cache database
        - `_SQManagerBase` is a mix-in class used by both `SqliteCacheManager` and `AsyncSqliteCacheManager`, containing code 
          which is used by both classes.
        - `SqliteCacheManager` is a child class of `SqliteWrapper`, designed to provide easier interaction with an SQLite3 
          cache database, including automatic creation of the database file, and the `pvcache` table within it. This class is
          intended for use by `privex.helpers.cache.SqliteCache`
        - `AsyncSqliteCacheManager` is a child class of `SqliteAsyncWrapper`, and is simply an AsyncIO 
          version of `SqliteCacheManager`. This class is intended for use by `privex.helpers.cache.asyncx.AsyncSqliteCache`

- **privex.helpers.plugins**
    - Added `HAS_PRIVEX_DB` attribute, for tracking whether the `privex-db` library is available for use.
    - Added `clean_threadstore` to `__all__` - seems I forgot to add it previously.

- **privex.helpers.settings**
    - Added `SQLITE_APP_DB_NAME` which can also be controlled via an env var of the same name - allowing you to adjust the
      base of the default DB filename for the SQLite3 cache adapters.
    - Added `SQLITE_APP_DB_FOLDER` (can also be controlled via env) - similar to the DB_NAME attribute, controls the 
      default base folder used by the SQLite3 cache adapters.



-----------------------------------------------------------------------------------------------------------------------

3.0.0 - Overhauled net module, new object cleaner for easier serialisation, improved class generation/mocking + more
====================================================================================================================

-----------------------------------------------------------------------------------------------------------------------

Author: Chris (Someguy123)
Date:   Sat Sep 26 04:29 2020 +0000

- `privex.helpers.common`
    - Added `strip_null` - very simple helper function to strip both `\00` and white space
      from a string - with 2 cycles for good measure.

- `privex.helpers.types`
    - Added `AUTO` / `AUTOMATIC` / `AUTO_DETECTED` dummy type, for use as the default value
      of function/method parameters, signalling to users that a parameter is auto-populated
      from another data source (e.g. instance/class attribute) if not specified.

- `privex.helpers.collections`
    - Added `copy_class_simple` (alternative to `copy_class`)
    - Added `copy_func` for copying functions, methods, and classmethods
    - Improved `_q_copy` to handle copying functions, methods and classmethods
    - Added `generate_class` + `generate_class_kw`
    - Added `Mocker.make_mock_module`
    - Added `Mocker.add_mock_modules`
    - Added `Mocker.__dir__` to track the available mock attributes and modules
    - Added `dataclasses_mock` - a `Mocker` instance which emulates `dataclasses` as a drop-in
      partially functional dummy for Python 3.6 when the `dataclasses` backport package isn't installed. 
    - Various changes to `Mocker.make_mock_class` - potentially breaking, see
      the **BREAKING CHANGES** section.
    - Added `DictObject.__dir__` + `OrderedDictObject.__dir__` to enable proper tracking of dictionary keys as attributes

- `privex.helpers.net`
    - This module has now been converted into a folder-based module. Imports in `__init__.py` have been carefully
      setup to ensure that existing import statements should still work as normal
    - Added new `SocketWrapper` and `AsyncSocketWrapper` classes, which are powerful wrapper classes for working with
      Python `socket.socket` objects, including support for SSL/TLS, partial support for running socket servers, and\
      making basic HTTP requests
    - **Many, many new functions and classes!** There's too many to list, and due to the conversion into a module folder
      instead of a singular file, it's difficult to track which functions/classes are new, and which existed before.
      
      If you really want to know what's new, just take a look around the `privex/helpers/net` module.

- `privex.helpers.converters`
    - Added `clean_obj` - which is a function that recursively "cleans" any arbitrary object, as to make it safe to convert
      into JSON and other common serialisation formats. It supports `dict`'s, `list`'s, [attrs](https://attrs.org)
      objects, native Python `dataclass`'s, `Decimal`, and many other types of objects.
    - Added `clean_dict` (used by `clean_obj`, usually no need to call it directly)
    - Added `clean_list` (used by `clean_obj`, usually no need to call it directly)

- Added `privex.helpers.mockers` module, which contains pre-made `Mocker` objects that are designed to stand-in
  for certain libraries / classes as partially functional dummies, if the real module(s) are unavailable for whatever reason.
 
- **And probably some other small additions / changes**


**BREAKING CHANGES**

- Both `_copy_class_dict` and `_copy_class_slotted` now check each attribute name
  against a blacklist (default: `COPY_CLASS_BLACKLIST`), and the default blacklist
  contains `__dict__`, `__slots__` and `__weakref__`, as the first 2 can't be directly
  copied (but we copy their contents by iteration), and weakref simply can't be deep copied
  (and it probably isn't a good idea to copy it anyway).
- `_copy_class_dict` (used by `copy_class`) no longer breaks the attribute copy loop if `deep_copy=False`
 
- `Mocker.make_mock_class` now returns a cloned `Mocker` class or instance by default, instead of
  a barebones class / instance of a barebones class.
  
  This was done simply because a Mocker class/instance is designed to handle being
  instantiated with any combination of constructor arguments, and have arbitrary
  attributes be retrieved / methods called without raising errors.
  
  If you absolutely require a plain, simple, empty class to be generated, you may
  pass the parameter `simple=True` to generate a bare class instead of a clone of Mocker
  (similar to the old behaviour). Unlike the old version of this method, you can now specify attributes
  as a dictionary to make your barebones mock class act similar to the class it's mocking. 

- Many things in `privex.helpers.net` such as `check_host` / `check_host_async` have been improved in various ways, however
  there may be some breaking changes with certain `privex.helpers.net` functions/classes in certain usecases.
    - Due to the high risk of bugs with certain networking functions that have been completely revamped, the
      older, simpler versions of various networking functions are available under `privex.helpers.net.base`
      with their original names.
      
      Because of the naming conflicts, to use the legacy functions/classes from `base`, you must import them
      directly from `privex.helpers.net.base` like so:
      
      ```
      # Option 1: import the base module itself, with an alias to prevent naming conflicts (and make it more
      # clear what you're referencing)
      from privex.helpers.net import base as netbase
      if netbase.check_host('google.com', 80):
          print('google.com is up')
      # Option 2: import the required legacy functions directly (optionally, you can alias them as needed)
      # You could also alias the newer overhauled functions while testing them in small portions
      # of your application.
      from privex.helpers.net.base import check_host
      from privex.helpers.net import check_host as new_check_host
      
      if check_host('www.privex.io', 443, http_test=True, use_ssl=True):
          print('[old check_host] https://www.privex.io is up')
      if new_check_host('files.privex.io', 443, http_test=True, use_ssl=True):
          print('[new check_host] https://files.privex.io is up')
      ```


-----------------------------------------------------------------------------------------------------------------------

2.8.0 - Refactoring, bug fixes + new loop_run function
===============================================================================================

-----------------------------------------------------------------------------------------------------------------------

Author: Chris (Someguy123)
Date:   Tue 17 Dec 2019

**Tl;Dr; important changes**

 - Added asyncx functions: `loop_run`, `is_async_context`, `_awaitable_blacklisted`
 - Added asyncx decorator `awaitable_class`, and mixin class `AwaitableMixin` (mixin version of awaitable_class decorator)
 - Removed class `helpers.extras.git.Git` and replaced it with an alias to `AsyncGit` as `@awaitable_class` rendered the
  wrapper class obsolete
 - Refactored some types from `common` module into `types`
 - Refactored tests and added some new tests for some of the added functions/classes
 - Various refactoring and general cleanup


**New Features / Additions**

 - `asyncx.loop_run` is similar to `asyncx.run_sync`, but more flexible, and doesn't use the deprecated `asyncio.coroutine`
   function. It can be passed either a coroutine directly for execution, or if a function/method is passed, 
   (doesn't have to be async) then it can attempt to extract the coroutine by calling each layer until a coroutine
   or non-callable is found.
   
   While there's no plan to remove `asynx.run_sync` in the near future, it's strongly recommended to switch usages of `run_sync`
   to `loop_run` because it's better at handling different forms of awaitable objects: 
        
    - Unlike `run_sync`, loop_run can handle both async function references AND coroutines
    
    - Unlike `run_sync`, loop_run can unwrap coroutines / async function references that are wrapped in a normal 
      non-async function (e.g. `@awaitable` wrapper functions)
    
    - Unlike `run_sync`, loop_run can accept the optional `_loop` keyword argument, allowing you to specify a custom asyncio
      event loop if you desire.
    
    - Unlike `run_sync`, loop_run will cleanly execute non-async functions if they're encountered, and simply return
      non-callable objects that were passed to it, instead of failing.

 - New function / class decorator `asyncx.awaitable_class` - wraps a class and overrides `__getattribute__` to enable all async
  methods to be called from non-async code. Similar to `asyncx.awaitable`, but affects all async methods in a class, and
  doesn't require non-async wrapper functions to be written.
  
    - If a non-async method or standard attribute is requested, then those are returned as normal without modification.
  
    - If an async method is called on the class, then it checks to see if there's a current AsyncIO context - if there is, it
      simply returns the coroutine for `await`'ing
      
    - If there isn't an async context, it will use `loop_run` to call the method synchronously using the
      current event loop, and return the method's result synchronously. 

 - New class `asyncx.AwaitableMixin` - a mixin class which works the same as `asyncx.awaitable_class`, but as a mixin class
   add to your class's inheritance, instead of a decorator.
 
 - Created the file `CHANGELOG.md` - note that it doesn't contain a full changelog yet, it only goes back as far as version 2.5
 

**Changes / Updates**

 - **The wrapper class `helpers.extras.git.Git` has been removed,** as `AsyncGit` now uses the much simpler `@awaitable_class`
   decorator to enable synchronous usage of all async methods, instead of a sub-class with individually `@awaitable` wrapped
   methods.
  
   To avoid breaking any existing code which relied on `extras.git.Git`, `Git` is now an alias for `AsyncGit`. No changes
   needed to be made to the Git tests in `tests/test_extras.py`, so this change isn't believed to cause code breakage.

 - A large portion of the decorator `asyncx.awaitable` has been refactored into the smaller functions: `_awaitable_blacklisted`
   and `is_async_context`.
   
 - During the refactoring of `asyncx.awaitable`, a bug was discovered in the blacklist scanning for sub-modules - this is now
   fixed (note: blacklist scanning is refactored into `_awaitable_blacklisted`)

 - `asyncx.py` now has an `__all__` module attribute, allowing `__init__` to simply import `*` instead of having to list each
  class/function etc.

 - `cache.asyncx.__init__` 
    - Added a PyDoc comment at the start of the file, explaining the AsyncIO adapters and how to use them.
    
    - Added the attributes `HAS_ASYNC_REDIS`, `HAS_ASYNC_MEMORY`, and `HAS_ASYNC_MEMCACHED` to allow for easy availability
     checking of async cache adapters.
     
    - Lowered the `ImportError` log level for AsyncRedisCache and AsyncMemcachedCache from `log.exception` down to `log.debug`
 
 - Refactored various generic / template types (e.g. `T`, `K`, `CL`) from `helpers.common` into `helpers.types`


**Testing**

 - Refactored `tests/test_general.py` into a folder `tests/general/`
 
 - Refactored AsyncIO related tests from `tests/test_general.py` into `tests/asyncx/test_async_common.py`
 
 - Added several new AsyncIO tests to `tests/asyncx/test_async_common.py`, mainly aimed at the new `asyncx.awaitable_class`, 
   and `asyncx.AwaitableMixin`


-----------------------------------------------------------------------------------------------------------------------

2.7.0 - Async cache adapters + many new functions
===============================================================================================

-----------------------------------------------------------------------------------------------------------------------

Author: Chris (Someguy123)
Date:   Fri Dec 13 09:16:57 2019 +0000

**New Features / Additions**

 - `privex.helpers.common`
     - Added `extract_settings` for extracting prefixed settings from modules, classes or dict's.

 - Created new `helpers.black_magic` module for *somewhat risky* code that uses app introspection
     - `calling_function` - Returns the name of the function which called your function/method.
     - `calling_module` - Returns the name of the module which called your function/method
     - `caller_name` - Get the fully qualified name of a caller in the format `some.module.SomeClass.method`

 - Created new `helpers.types` module for holding type aliases and new type definitions

 - `privex.helpers.decorators`
     - Added `async_retry` decorator, which works similar to `retry_on_error`, but supports wrapping asyncio coroutines

 - `privex.helpers.cache`
     - Created new `asyncx` submodule for AsyncIO cache adapters
     - `asyncx.base.AsyncCacheAdapter` is a new base class for AsyncIO cache adapters, with all methods as coros
     - `asyncx.AsyncRedisCache` is a new AsyncIO cache adapter for Redis
     - `asyncx.AsyncMemoryCache` is a new AsyncIO cache adapter for in-memory caching (async version of `MemoryCache`)
     - `asyncx.AsyncMemcachedCache` is a new AsyncIO cache adapter for Memcached
     - `CacheAdapter` has a new method `get_or_set_async`, which is an async method that supports
       coroutines as a value, as well as standard callable's and plain values

 - `privex.helpers.plugin`
     - New functions for organising __STORE by thread: `_get_threadstore`, `_set_threadstore`, `clean_threadstore`
     - New functions for managing AsyncIO Redis (aioredis) instances `get_redis_async`, `close_redis_async` etc.
     - New functions for managing AsyncIO Memcached (aiomcache) instances `get_memcached_async`, `close_memcached_async` etc.

**Changes / Updates**

 - Added `aioredis`, `hiredis`, and `aiomcache` to `extras/cache.txt`

 - `async-property` is now a core requirement, since it's used by a lot of async classes

 - New settings `MEMCACHED_HOST` and `MEMCACHED_PORT` for AsyncMemcachedCache

 - New plugin status `HAS_ASYNC_REDIS` for detecting if `aioredis` is available

 - `privex.helpers.decorators`
     - `retry_on_err` has been slightly cleaned up
     - `retry_on_err` now supports **ignoring exceptions**, so you can list exceptions that cause a retry, but shouldn't 
       increase the retry count.
     - `retry_on_err` now supports the setting `instance_match`, which changes how exceptions are compared. When enabled, it will
       compare using `isinstance()` instead of an exact type comparison.

 - `privex.helpers.asyncx`
     - `awaitable` decorator now detects when it's received a non-async function, and returns the result correctly
     - `awaitable` now supports "blacklisting" functions/modules, to ensure when those functions/modules call an 
       `@awaitable` function, that they always get a synchronous result, not a coroutine.

 - `privex.helpers.cache`
     - `CacheWrapper` now uses `@awaitable` for most methods, allowing AsyncIO cache adapters to be used without breaking existing
       synchronous code which uses the cache API.
     - `CacheAdapter` now has dummy `__enter__` and `__exit__` methods defined, allowing all synchronous cache adapters to be used
       in a `with` statement, regardless of whether they actually use context management.

 - `privex.helpers.plugin`
     - `get_redis`, `close_redis`, `reset_redis` etc. now use the new thread store system to help ensure thread safety
       by separating instances per thread.
     - Refactored `get_redis`'s connection opening into `connect_redis`, and now uses `extract_settings` for loading 
       default settings

**Testing**

 - Added unit tests for `extract_settings` to `tests/test_general.py`

 - New folders `tests/asyncx` and `tests/cache` for containing flat test case modules using pytest-asyncio

 - `tests/asyncx/test_async_retry.py` tests the new `@async_retry` decorator

 - `tests/cache/test_async_memcached.py` tests the new `AsyncMemcachedCache` class

 - `tests/cache/test_async_redis.py` tests the new `AsyncRedisCache` class

 - `tests/cache/test_async_memory.py` tests the new `AsyncMemoryCache` class

Additional merged commits:

 - enable memcached on travis



-----------------------------------------------------------------------------------------------------------------------

2.6.0 - `extras.git` + `asyncx.awaitable` + aobject
===============================================================================================

-----------------------------------------------------------------------------------------------------------------------

Author: Chris (Someguy123)
Date:   Sat Dec 7 05:57:20 2019 +0000

 - Created `helpers.extras.git` module, which contains a git command wrapper that works with both sync and async functions
    - Primarily intended for the three methods: `get_current_commit`, `get_current_branch`, and `get_current_tag`, which
      allows python applications and libraries to identify what version they are, via git.
    - Includes various basic methods such as `init`, `checkout`, `branch`, `tag`, `status`, `log` and others.
 - Added new async helpers
    - `aobject` allows sub-classes to have `async __init__` constructors
    - `awaitable` helps create wrapper functions that allow async functions to work with sync code seamlessly
 - Improved `byteify` and `stringify` with None handling
 - Added new `SysCallError` exception
 - `sniffio` is now a required dependency - however it's very small and dependency free in itself (only about 30kb).
 - Added unit tests for the git module, including tests for both synchronous and asynchronous execution of the methods
 - Re-generated some of the documentation
 - Possibly other small changes


-----------------------------------------------------------------------------------------------------------------------

2.5.1 - Added call_sys(_async) + tests.sh refactoring
===============================================================================================

-----------------------------------------------------------------------------------------------------------------------

Author: Chris (Someguy123)
Date:   Sat Dec 7 00:06:30 2019 +0000

 - Added `call_sys` function in `helpers.common`, an easier way to run and interact with external programs
 - Added `shell_quote` function - small shim for python 3.8's `shlex.join` for backwards compatibility
 - Added `call_sys_async` function in `helpers.asyncx`, which is a fully async version of `call_sys`
 - Added tests for `call_sys` and `call_sys_async`
 
 - Improvements to `local_tests.sh`
    - Re-factored most of `local_tests.sh` into `lib/lib_test.sh`. lib_test.sh contains only shell functions, so it can be
      sourced into a bash shell for debugging local_tests.sh
    
    - Now has a `QUIET` option, for less verbose output
    - Re-factored virtualenv creation, detection and activation into `pyactivate`, `venv_status`, `is_current_venv` and others
    - Handle script running from within an existing virtualenv cleanly.
    - Main body of the venv creation / test running has been moved into `main_tests()` in lib_test
    - Now shows a summary at the end of the tests, so you can see which python versions caused tests to throw warnings and/or
      were skipped
    - Lots of other small improvements
 
 - Added gitignore lines for `dev_*.py`, sqlite databases, and adjusted `venv` lines to only affect root folder.



-----------------------------------------------------------------------------------------------------------------------

2.5.0 - Converters, construct_dict, get_function_params (Final release - PyPi published)
===============================================================================================

-----------------------------------------------------------------------------------------------------------------------


Author: Chris (Someguy123)
Date:   Thu Dec 5 02:53:08 2019 +0000

 - Includes commit 12da829ff8da8b64549208ac92bb48c62f0af60c which enables 2.5.0 to function fully on 
   Python 3.6 and 3.7 (prior to this commit some tests only worked on 3.8+)

```
commit 12da829ff8da8b64549208ac92bb48c62f0af60c
Date:   Thu Dec 5 02:39:32 2019 +0000
Add local_tests.sh, fix get_function_params on older python

     - Added `local_tests.sh` for running the unit tests on multiple python versions locally
     - Added `OrderedDictObject` to collections module, since python versions before 3.8 cannot reverse a normal dict.
     - Add unit tests for ordered dict object
     - Adjusted `get_function_params` to use the new OrderedDictObject (fixes failing tests on older python versions)
```

**New Features / Additions**

 - `privex.helpers.common`
    - Added `get_function_params` - which extracts and filters a function/method or class constructor's parameters, and
      outputs them in a dictionary
      
    - Added `construct_dict`, which allows you to either construct a class, or call a function using a dictionary of 
      keyword arguments, using `get_function_params` to detect what arguments the class/function/method can take, including any
      parent classes, then filtering out any keyword arguments which would otherwise be rejected and cause a TypeError.
      
    - Added `_filter_params`, a private function used by the aforementioned functions to filter a dictionary or iterable of
      Parameter objects.
    
 - New module `converters`, containing functions/classes designed to convert/parse one type into another
 
    - `convert_datetime` converts both string date/time's as well as unix timestamps into `datetime.datetime` objects 
      using `dateutil.parser`
    
    - `convert_unixtime_datetime` converts specifically UNIX epoch timestamps (can be string, int, float, Decimal etc.) into
      `datetime.datetime` objects, and is used by `convert_datetime` to handle unix timestamps.
      
    - `convert_bool_int` converts booleans `True` / `False` as well as string / int versions into integers 1 (true) and 0 (false)
    
    - `convert_int_bool` is mostly an alias to `is_true`, but exists for convenience and semantics (if there's a
      convert_bool_int, why not a convert_int_bool?)

    **Changes / Updates**
    
     - Shrank the rather large copyright notice in most modules down to the small copyright block, and instead of dumping the
       whole X11 / MIT License text in there, the licence block simply states `License: X11 / MIT`. This should make the docs a
       bit more readable.
     
     - Added `python-dateutil` to the `Pipfile`
     
     - For sanity reasons, `python-dateutil` has been added to the `install_requires` (meaning it's auto-installed when you
       install privex-helpers). The package is relatively small and depends on just `six`, weighing in around 500kb 
       (python-dateutil = 468kb, six = 36kb).
    
       It may be removed and refactored into a setup.py extra at a later point, but for now it's small and commonly 
       required enough that it can be a dependency.

     - Added `dateutil` to the sphinx intersphinx mapping
     - Possibly other small changes I forgot to include
    
    **Testing**
    
     - Added new test case `TestInspectFunctions` to test_general, which tests the new `get_function_params` 
       and `construct_dict` functions.
       
     - Added new test module `test_converters.py` which contains test cases for the new converters module
     
        - `TestConvertDate` covers date/time related converters such as `convert_datetime` and `convert_unixtime_datetime`
        
        - `TestConvertGeneral` covers other converters that don't fit into a specific category 
          (or would otherwise be pointless to categorize)
