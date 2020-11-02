import functools
import threading
import logging
import inspect
from contextlib import contextmanager
from time import sleep
from typing import Any, Callable, ContextManager, Set, Type, Union, Optional

import attr
from privex.helpers.common import DictObject, auto_list, empty, empty_if
from privex.helpers.cache import CacheNotFound, cached
from privex.helpers.decorators import r_cache, FO
from privex.helpers.types import AnyNum, AUTO
from privex.helpers.thread import lock_acquire_timeout
from privex.helpers.black_magic import caller_name

log = logging.getLogger(__name__)

__all__ = [
    'CACHE_MGR', 'NO_LOCK', 'ANY_LCK', 'fake_lock_manager', 'CacheSettings', 'z_cache', 'CacheManagerMixin'
]

CACHE_MGR = Union["CacheManagerMixin", Type["CacheManagerMixin"]]
NO_LOCK = type('NoLock', (), {})
ANY_LCK = Optional[Union[threading.Lock, Type[NO_LOCK]]]


@contextmanager
def fake_lock_manager(lock: threading.Lock = None, *args, **kwargs):
    yield True


@attr.s
class CacheSettings:
    cache_prefix: str = attr.ib('pvx_cmgr')
    """The prefix used for all cache keys generated for your class"""
    cache_key_log_name: str = attr.ib('all_cache_keys')
    """The cache key name component for the key used to store a list of all known cache keys for your class"""
    cache_sep: str = attr.ib(':')
    """Separator character(s) used between identifying components within a cache key"""
    default_cache_key_time: Union[float, int] = attr.ib(300)
    """Default number of seconds to cache the log of known cache keys"""
    default_cache_time: Union[float, int] = attr.ib(300)
    """Default number of seconds to cache any objects"""
    _gen_cache_key: Callable[[Any], str] = attr.ib(None)
    _key_add_prefix: Callable[[Any], str] = attr.ib(None)
    
    def gen_cache_key(self, *args, _auto_cache=True, _comps_start: list = None, _comps_end: list = None, **query) -> str:
        # noinspection PyArgumentList
        return self._gen_cache_key(*args, _auto_cache=_auto_cache, _comps_start=_comps_start, _comps_end=_comps_end, **query)
    
    def key_add_prefix(
            self, key: Union[str, Callable[[Any], str]], auto_prefix: bool = True, _auto_cache=True,
            call_args: list = None, call_kwargs: dict = None, _lock: ANY_LCK = None
    ) -> str:
        # noinspection PyArgumentList
        return self._key_add_prefix(
            key, auto_prefix, _auto_cache=_auto_cache, call_args=call_args, call_kwargs=call_kwargs, _lock=_lock
        )
    
    @classmethod
    def from_class(cls, obj: Union["CacheManagerMixin", Type["CacheManagerMixin"]]) -> "CacheSettings":
        _keys = [
            'cache_prefix', 'cache_key_log_name', 'cache_sep', 'default_cache_time',
            'default_cache_key_time', 'gen_cache_key', 'key_add_prefix'
        ]
        # _priv_keys = ['gen_cache_key', 'key_add_prefix']
        constx = {}
        for k in _keys:
            if hasattr(obj, k):
                constx[k] = getattr(obj, k)
        # for k in _priv_keys:
        #     if hasattr(obj, k):
        #         constx[f"_{k}"] = getattr(obj, k)
        return cls(**constx)


def z_cache(cls: CACHE_MGR = None, cache_key: Union[str, callable] = None, cache_time=AUTO, format_args: list = None,
            format_opt: FO = FO.POS_AUTO, extract_class=True, **opts):
    """
    A special method caching decorator which is designed to integrate with classes that extend :class:`.CacheManagerMixin`
    
    This is simply a wrapper for :func:`.r_cache` - it transparently caches the output of a wrapped method/function, but
    unlike :func:`.r_cache`, it's designed to automatically integrate with classes which extend :class:`.CacheManagerMixin` ,
    allowing it to automatically retrieve cache settings such as the cache prefix, default cache time, along with directly calling
    various classmethods which enable logging of newly created ``cache_key`` 's for painless cleanup of cache keys when needed,
    without having to manually track them, or doing the nuclear option of erasing the entire cache system's database.
    
    It integrates with your class by intercepting the first argument of any method calls that are wrapped with :func:`.z_cache`.
    Both standard instance methods and :class:`.classmethod` 's are supported transparently - while static methods will only
    integrate properly with your own class if you set ``cls`` (first argument) on the decorator to point to the class or instance
    containing your cache manager settings and inherited methods from :class:`.CacheManagerMixin`
    
    After you've extended :class:`.CacheManagerMixin`, you can enable argument-based caching for any method, simply by adding
    the decorator line ``@z_cache()`` above it. :func:`.z_cache` will automatically handle the cache key name, including extracting
    your method's passed arguments and inserting them into the cache key, ensuring method calls with certain arguments, are cached
    separately from other method calls with a different set of arguments.
    
    Example::
        
        >>> from privex.helpers.cache.extras import CacheManagerMixin, z_cache
        >>> from time import sleep
        >>>
        >>> class MyClass(CacheManagerMixin):
        ...     # It's recommended, but not necessary - to re-create cache_key_lock with None, as it will ensure your
        ...     # class has a separate threading.Lock() instance from other CacheManagerMixin based classes
        ...     cache_key_lock: Optional[threading.Lock] = None
        ...     # You should override cache_prefix to ensure cache keys auto-created for your class won't
        ...     # conflict with cache keys created by other classes
        ...     cache_prefix: str = 'my_class'
        ...     # While it's possible to set the cache timeout per method with z_cache / per call to cache_set,
        ...     # it's helpful to adjust default_cache_time to a number of seconds which is suitable for most
        ...     # methods in your class, avoiding the need to specify it each time..
        ...     default_cache_time: Union[float, int] = 300
        ...     # default_cache_key_time should generally be set to the same number of seconds as default_cache_time.
        ...     # It controls how long the "cache key log" is held for, which is simply a list of known cache keys for
        ...     # your class, enabling the use of the method .clear_all_cache_keys
        ...     default_cache_key_time: Union[float, int] = 300
        ...
        ...     @z_cache()
        ...     def hello(self, world=10):
        ...         sleep(5)
        ...         return f"Hello world: {world}"
        ...
        >>> c = MyClass()
        >>> # The first call to hello() will take 5 seconds due to the sleep
        >>> c.hello()
        Hello world: 10
        >>> c.hello()   # But when we call it again - it returns instantly
        Hello world: 10
        >>> # If we call .hello() with a different set of arguments, it will result in a new cache key being auto-generated,
        >>> # requiring a new, non-cached call to hello() to get the result for '5'
        >>> c.hello(5)
        Hello world: 5
    
    
    :param CACHE_MGR cls: For functions or methods which don't have a :class:`.CacheManagerMixin` based class or instance being passed
                          as their first argument, you'll need to set ``cls`` to point to a :class:`.CacheManagerMixin` based class
                          or instance, so that :func:`.z_cache` is able to both retrieve your overridden cache settings, and call
                          the various helper classmethod's for handling prefixed cache keys etc.
     
    :param str|callable cache_key: If you don't like automatic determination and argument-based generation of the cache_key, you
                                   may manually set the cache key to store the output of the method into.
                                   
                                   For dynamic generation of the cache key, this may be set to a ``callable``, such as a lambda, function,
                                   or method which returns the cache key to be used as a :class:`.str`.
                                   However, whatever callable is passed, must accept the exact same positional and keyword arguments as
                                   the method being wrapped - as those will be the args/kwargs passed to your ``cache_key``
                                   callable object.
    
    :param float|int cache_time:   The number of seconds to cache the output of the wrapped method/function for. By default, this is
                                   automatically extracted from the class of the wrapped function, by retrieving ``default_cache_time``
     
    :param format_args:            See the docs for :func:`.r_cache`
    :param format_opt:             See the docs for :func:`.r_cache`
    
    :param bool extract_class:     (Default: ``True``) This argument controls whether or not we attempt to auto-extract the
                                   related class/instance of the wrapped method by analyzing the first positional argument, along
                                   with the keyword arguments ``self`` and ``cls`` if they're present.
                                   
                                   If ``extract_class`` is set to ``False``, no attempt will be made to retrieve the related
                                   class/instance using the first argument - instead, if ``cls`` isn't passed, it will immediately
                                   fall back to using the original parent class for settings - :class:`.CacheManagerMixin`
    
    :param opts:                   See the docs for :func:`.r_cache`
    :return:
    """
    f_gen_cache_key = opts.get('gen_cache_key', cls.gen_cache_key if cls is not None else None)
    f_key_add_prefix = opts.get('key_add_prefix', cls.key_add_prefix if cls is not None else None)
    
    def _mk_key(_func: callable, _ck: Union[str, callable] = None, g_cachekey: callable = None, *zargs, **zkwargs):
        zargs = list(zargs)
        if _ck in [None, '', b'', False, True, 0, [], ()]:
            log.debug(" [_mk_key] No cache key specified, generating cache key based on function name + arguments")
            if len(zargs) > 0 and (inspect.isclass(zargs[0]) or inspect.ismethod(zargs[0])):
                log.debug(" [_mk_key] First argument appears to be cls/self - popping argument 0 to prevent wasteful cache repr() caching.")
                zargs.pop(0)
            gk = g_cachekey(*zargs, _comps_start=_func.__name__, **zkwargs)
            log.debug(" [_mk_key] Generated cache key: %s", gk)
            return gk
        return _ck
    
    # Sharing normal variables between the outer z_cache, and the intter wrapper function causes a lot of problems,
    # however, we're able to share an actual object instance easily - so we use a DictObject to make various variables
    # available from within the inner wrapper functions.
    z_opts = DictObject(
        {
            'cache_key':     cache_key, 'cache_time': cache_time, 'format_args': format_args, 'format_opt': format_opt,
            'extract_class': extract_class, 'gen_cache_key': f_gen_cache_key, 'key_add_prefix': f_key_add_prefix,
            'opts':          dict(opts)
        }
    )
    
    # _cls = cls
    
    def _decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            kwargs = dict(kwargs)
            z_kwargs = dict(kwargs)
            zo = DictObject(z_opts)
            ex_class = zo.pop('extract_class', None)
            cset: Optional[CacheSettings] = None
            # gen_cache_key = zo.pop('gen_cache_key', None)
            # key_add_prefix = zo.pop('key_add_prefix', None)
            
            if ex_class:
                # First check if the first positional argument is a class, or an instance of CacheManagerMixin
                # If it is, and we don't already have a valid gen_cache_key set, then try to use gen_cache_key from that.
                if len(args) > 0:
                    if args[0] and (inspect.isclass(args[0]) or isinstance(args[0], CacheManagerMixin)):
                        log.debug(" [z_cache] Setting gen_cache_key to 'args[0].gen_cache_key'")
                        _cls: CacheManagerMixin = args[0]
                        if cset is None:
                            try:
                                cset = CacheSettings.from_class(_cls)
                            except Exception as e:
                                log.warning(f"Failed to generate CacheSettings object from class object: {_cls} "
                                            f"- reason: {type(e)} {str(e)}")
                            
                        # key_add_prefix = getattr(args[0], 'key_add_prefix', None) if key_add_prefix is None else key_add_prefix
                        # gen_cache_key = getattr(args[0], 'gen_cache_key', None) if gen_cache_key is None else gen_cache_key
                        #
                # If gen_cache_key is still None, see if 'self' or 'cls' are present in the keyword arguments
                # Just like with the positional args, we try to extract 'gen_cache_key' from the class/instance if it's possibly.
                if len(kwargs) > 0:
                    c_self, c_cls = kwargs.get('self'), kwargs.get('cls')
                    if c_self and (inspect.isclass(c_self) or isinstance(c_self, CacheManagerMixin)):
                        log.debug(" [z_cache] Setting gen_cache_key to 'c_self.gen_cache_key' (kwargs['self'])")
                        if cset is None:
                            try:
                                cset = CacheSettings.from_class(c_self)
                            except Exception as e:
                                log.warning(f"Failed to generate CacheSettings object from class object: {c_self} "
                                            f"- reason: {type(e)} {str(e)}")
                        # key_add_prefix = getattr(c_self, 'key_add_prefix', None) if key_add_prefix is None else key_add_prefix
                        # gen_cache_key = getattr(c_self, 'gen_cache_key', None) if gen_cache_key is None else gen_cache_key
                    if c_cls and (inspect.isclass(c_cls) or isinstance(c_cls, CacheManagerMixin)):
                        log.debug(" [z_cache] Setting gen_cache_key to 'c_cls.gen_cache_key' (kwargs['cls'])")
                        try:
                            cset = CacheSettings.from_class(c_cls)
                        except Exception as e:
                            log.warning(f"Failed to generate CacheSettings object from class object: {c_cls} "
                                        f"- reason: {type(e)} {str(e)}")
                        # key_add_prefix = getattr(c_cls, 'key_add_prefix', None) if key_add_prefix is None else key_add_prefix
                        # gen_cache_key = getattr(c_cls, 'gen_cache_key', None) if gen_cache_key is None else gen_cache_key
            
            cset: CacheSettings = CacheSettings.from_class(CacheManagerMixin) if cset is None else cset
            # zo = DictObject(z_opts)
            # If gen_cache_key is STILL None, then we fallback to CacheManagerMixin.gen_cache_key
            # gen_cache_key = CacheManagerMixin.gen_cache_key if gen_cache_key is None else gen_cache_key
            # If key_add_prefix is STILL None, then we fallback to CacheManagerMixin.key_add_prefix
            # key_add_prefix = CacheManagerMixin.key_add_prefix if key_add_prefix is None else key_add_prefix
            
            # If the decorator was passed a custom cache_key, then we need to pass it to key_add_prefix to ensure that the
            # key is both prefixed, and added to the known cache key list for easy removal later on.
            if zo.get('cache_key') is not None:
                log.debug(f" [z_cache] Calling key_add_prefix with cache key '{zo.cache_key}' + args ({args}) + kwargs ({kwargs})")
                # noinspection PyTypeChecker
                zo.cache_key = cset.key_add_prefix(zo.cache_key, call_args=list(args), call_kwargs=dict(kwargs))
                log.debug(f" [z_cache] New prefixed cache key is: '{zo.cache_key}'")
            # We use _mk_key - a wrapper for gen_cache_key, to auto-generate a cache key, depending on if the
            # passed cache_key was empty.
            zo.cache_key = _mk_key(f, zo.get('cache_key'), cset.gen_cache_key, *args, **z_kwargs)
            
            x_ck, x_ct = zo.pop('cache_key'), zo.pop('cache_time', None)
            x_ct = cset.default_cache_time if x_ct in [None, AUTO] else x_ct
            x_fmtargs, x_fmtopts = zo.pop('format_args', None), zo.pop('format_opt', None)
            z_kwargs.pop('_func', None), z_kwargs.pop('_ck', None), z_kwargs.pop('g_cachekey', None)
            log.debug(f" [z_cache] Calling r_cache: {x_ck}, {x_ct}, {x_fmtargs}, {x_fmtopts}, {z_opts.opts}")
            log.debug(f" [z_cache] func args: {args} || kwargs: {kwargs}")
            return r_cache(x_ck, x_ct, x_fmtargs, x_fmtopts, **zo.opts)(f)(*args, **kwargs)
        
        return wrapper
    
    return _decorator


# CacheSettings = namedtuple(
#     'CacheSettings', 'cache_prefix cache_key_log_name cache_sep default_cache_key_time default_cache_time'
# )


class CacheManagerMixin:
    """
    **CacheManagerMixin** is a class mixin which adds various methods and settings to assist with class-scoped caching, including
    an adjustable class-level cache prefix :attr:`.cache_prefix`, a method to remove all known cache keys managed by
    your class :meth:`.clear_all_cache_keys`, and a special decorator which automatically integrates with your class :func:`.z_cache`
    by intercepting the first argument of a method call.
    
    After you've extended :class:`.CacheManagerMixin`, you can enable argument-based caching for any method, simply by adding
    the decorator line ``@z_cache()`` above it. :func:`.z_cache` will automatically handle the cache key name, including extracting
    your method's passed arguments and inserting them into the cache key, ensuring method calls with certain arguments, are cached
    separately from other method calls with a different set of arguments.
    
    Most methods of this class are generally only used internally, or for certain niche use cases, but there are some methods
    that can be useful in almost any use case:
    
        * :meth:`.get_all_cache_keys` - returns a :class:`.set` of all known cache keys used by your class. Note that
          this method relies on the "cache key log", which will only be aware of keys that were cached within the
          last :attr:`.default_cache_key_time` seconds.
        
        * :meth:`.clear_cach_keys` - manually remove individual cache keys immediately
        
        * :meth:`.clear_all_cache_keys` - as the name implies, this method will remove **all known cache keys** that are found
          inside of the cache key log ( :attr:`.cache_key_log_name` )
        
        * :meth:`.cache_set` - set a cache key directly from the body of a method. The key that you enter, will be automatically
          prefixed with the appropriate :attr:`.cache_prefix`, so you don't need to worry about manually prefixing your cache key names.
        
        * :meth:`.cache_get` - retrieve the contents of a given cache key name - if it exists. Just like with :meth:`.cache_set`, this
          method will automatically prefix the key you enter. Additionally, by default, if the key you're trying to retrieve
          doesn't exist, it will make a second cache call without the prefix, in-case that you were really wanting the literal key
          you entered (not the auto-prefixed key). The automatic no-prefix-fallback can be disabled, see the docs for that method.
        
        * :meth:`.cache_get_or_set` - a combination of :meth:`.get` and :meth:`.set` - if the key you're trying to retrieve doesn't exist,
          then the fallback ``value`` will be set on that cache key and returned. Additionally, you may specify a "callback" for
          ``value``, i.e. a function/method which will be called if ``key`` doesn't exist, which should return the new value which
          should be set on the key and returned.
    
     
    Example::
        
        >>> from privex.helpers.cache.extras import CacheManagerMixin, z_cache
        >>> from time import sleep
        >>>
        >>> class MyClass(CacheManagerMixin):
        ...     # It's recommended, but not necessary - to re-create cache_key_lock with None, as it will ensure your
        ...     # class has a separate threading.Lock() instance from other CacheManagerMixin based classes
        ...     cache_key_lock: Optional[threading.Lock] = None
        ...     # You should override cache_prefix to ensure cache keys auto-created for your class won't
        ...     # conflict with cache keys created by other classes
        ...     cache_prefix: str = 'my_class'
        ...     # While it's possible to set the cache timeout per method with z_cache / per call to cache_set,
        ...     # it's helpful to adjust default_cache_time to a number of seconds which is suitable for most
        ...     # methods in your class, avoiding the need to specify it each time..
        ...     default_cache_time: Union[float, int] = 300
        ...     # default_cache_key_time should generally be set to the same number of seconds as default_cache_time.
        ...     # It controls how long the "cache key log" is held for, which is simply a list of known cache keys for
        ...     # your class, enabling the use of the method .clear_all_cache_keys
        ...     default_cache_key_time: Union[float, int] = 300
        ...
        ...     @z_cache()
        ...     def hello(self, world=10):
        ...         sleep(5)
        ...         return f"Hello world: {world}"
        ...
        >>> c = MyClass()
        >>> # The first call to hello() will take 5 seconds due to the sleep
        >>> c.hello()
        Hello world: 10
        >>> c.hello()   # But when we call it again - it returns instantly
        Hello world: 10
        >>> # If we call .hello() with a different set of arguments, it will result in a new cache key being auto-generated,
        >>> # requiring a new, non-cached call to hello() to get the result for '5'
        >>> c.hello(5)
        Hello world: 5
    
        
        
    """
    cache_key_lock: Optional[threading.Lock] = None
    """
    A :class:`threading.Lock` lock object which is used when adding cache keys to :attr:`.cache_key_log_name` to prevent
    the risk of two simultaneous cache key additions causing one call to overwrite the other's addition attempt.
    """
    cache_prefix: str = 'pvx_cmgr'
    """The prefix used for all cache keys generated for your class"""
    cache_key_log_name: str = 'all_cache_keys'
    """The cache key name component for the key used to store a list of all known cache keys for your class"""
    cache_sep: str = ':'
    """Separator character(s) used between identifying components within a cache key"""
    default_cache_key_time: Union[float, int] = 300
    """Default number of seconds to cache the log of known cache keys"""
    default_cache_time: Union[float, int] = 300
    """Default number of seconds to cache any objects"""
    
    @classmethod
    def _get_lock(cls, lock: ANY_LCK = None, timeout=30, fail=True) -> ContextManager:
        log.debug("Lock requested by caller: %s", caller_name())
        if lock == NO_LOCK:
            log.debug("Returning fake lock to caller: %s", caller_name())
            return fake_lock_manager()
        if lock is None:
            if cls.cache_key_lock is None:
                log.debug("Setting cls.cache_key_lock")
                cls.cache_key_lock = threading.Lock()
            log.debug("Returning cls.cache_key_lock")
            lock = cls.cache_key_lock
        log.debug("Returning lock_acquire_timeout(%s, timeout=%s, fail=%s)", lock, timeout, fail)
        return lock_acquire_timeout(lock, timeout=timeout, fail=fail)
    
    @classmethod
    def gen_cache_key(cls, *args, _auto_cache=True, _comps_start: list = None, _comps_end: list = None, **query) -> str:
        _comps_start, _comps_end = auto_list(_comps_start), auto_list(_comps_end)
        kcomps = [cls.cache_prefix] + _comps_start
        args, query = list(args), dict(query)
        if len(args) > 0:  # If there are positional args, join them up with commas and add to kcomps
            kcomps.append(','.join([str(a) for a in args]))
        if len(query) > 0:  # if there are kwargs, convert them into a list of strings 'key=value' and merge with kcomps
            ql = [f'{k}={v}' for k, v in query.items()]
            ql.sort()
            kcomps += ql
        kcomps += _comps_end
        # convert kcomps into a string by joining all items with the configured cache key separator
        k = cls.cache_sep.join(kcomps)
        if _auto_cache:
            cls.log_cache_key(k)
        return k
    
    @classmethod
    def get_all_cache_keys(cls) -> Set[str]:
        """
        Retrieve the list of cache keys as a :class:`.set` from the cache key ``'query_cache_keys'`` which
        stores the list of ``query_hidden:xxx:xxx:xxx`` keys, allowing for easy clearing of those cache keys when needed.
        :return:
        """
        lk = cls.cache_sep.join([cls.cache_prefix, cls.cache_key_log_name])
        qk = cached.get_or_set(lk, set(), cls.default_cache_key_time)
        qk = set() if empty(qk, True, True) else qk
        if isinstance(qk, (list, tuple)): qk = set(qk)
        return qk
    
    @classmethod
    def log_cache_key(cls, key: str, _lock: ANY_LCK = None) -> Set[str]:
        """
        Add a cache key name to the cache key log :attr:`.cache_key_log_name`. This usually doesn't need to be called from outside
        of this class, since most methods which may add or edit a cache key should also insert/update the key into the cache key log.
        
        :param str key:  The key to add to the cache key log.
        :param ANY_LCK _lock:  You may optionally pass a :class:`.Lock` instance if needed, e.g. to prevent a conflict
                               where the calling function/method has already acquired the class-level lock :attr:`.cache_key_lock`
                               It can also be set to the dummy type :class:`.NO_LOCK` ``NO_LOCK`` to prevent using a lock.
        :return Set[str] cache_key_log: The cache key log after adding ``ckeys``
        """
        lk = cls.cache_sep.join([cls.cache_prefix, cls.cache_key_log_name])
        with cls._get_lock(_lock):
            log.debug(f"Adding cache key '{key}' to list of cached query keys: '{lk}'")
            keys = cls.get_all_cache_keys()
            keys.add(key)
            cached.set(lk, keys, cls.default_cache_key_time)
            log.debug(f"Successfully added '{key}' to '{lk}' and wrote back to cache. Current key list: {keys}")
        return keys
    
    @classmethod
    def log_delete_cache_keys(cls, *ckeys: str, _lock: ANY_LCK = None) -> Set[str]:
        """
        Remove one or more cache key names from the cache key log :attr:`.cache_key_log_name`. This usually doesn't need to be called
        from outside of this class, since :meth:`.clear_cache_keys` automatically removes any logged cache key names after deleting
        the cache key itself from the global cache.
        
        :param str ckeys:      One or more cache keys to remove from the cache key log
        :param ANY_LCK _lock:  You may optionally pass a :class:`.Lock` instance if needed, e.g. to prevent a conflict
                               where the calling function/method has already acquired the class-level lock :attr:`.cache_key_lock`
                               It can also be set to the dummy type :class:`.NO_LOCK` ``NO_LOCK`` to prevent using a lock.
        :return Set[str] cache_key_log: The cache key log after removing ``ckeys``
        """
        lk = cls.cache_sep.join([cls.cache_prefix, cls.cache_key_log_name])
        ckeys = list(ckeys)
        log.debug(f"Removing {len(ckeys)} keys from cache key list. Keys to be removed: {ckeys}")
        log.debug(f" [log_delete_cache_keys] Obtaining hold on lock: {_lock}")
        with cls._get_lock(_lock):
            keys = cls.get_all_cache_keys()
            for key in ckeys:
                log.debug(f"Removing cache key '{key}' from list of cached query keys: '{lk}'")
                if key not in keys:
                    log.debug(f"The key '{key}' isn't in the key list. Skipping.")
                    continue
                keys.remove(key)
                log.debug(f"Successfully removed '{key}' from '{lk}'.")
            cached.set(lk, keys, cls.default_cache_key_time)
            log.debug(
                f"Finished removing {len(ckeys)} keys from cache key list. Wrote new key list back to cache. "
                f"Current key list: {keys}")
        log.debug(f" [log_delete_cache_keys] Releasing hold on lock: {_lock}")
        return keys
    
    log_delete_cache_key = log_delete_cache_keys
    
    @classmethod
    def cache_set(cls, key: str, value: Any, timeout: Optional[AnyNum] = AUTO, auto_prefix: bool = True):
        """
        This is a simple helper method which calls :meth:`.cached.set` - while automatically prepending :attr:`.cache_prefix`
        and :attr:`.cache_sep` before the key, plus when ``timeout=AUTO`` ( :class:`.AUTO` ), the timeout will be
        automatically set to the default timeout: :attr:`.default_cache_time`

        :param str key:   NOTE: Key will be auto-prepended with :attr:`.cache_prefixx - The cache key (as a string) to set the
                          value for, e.g. ``example:test``
        :param Any value: The value to store in the cache key ``key``
        :param int timeout: The amount of seconds to keep the data in cache. Pass ``None`` to disable expiration.
        :param bool auto_prefix: If set to ``True``, will auto-prepend :attr:`.cache_prefix` to ``key`` if it's not present.
        :return:
        """
        timeout = cls.default_cache_time if timeout == AUTO else timeout
        # For safety, if the cache key passed to this method already starts with `.cache_prefix`, then don't prepend
        # the cache_prefix to the key. Otherwise, if it's not present, then prepend the cache prefix.
        key = cls._pfx_key(key, auto_prefix=auto_prefix)
        return cached.set(key, value, timeout=timeout)
    
    @classmethod
    def cache_get(cls, key: str, default: Any = None, fail: bool = False, auto_prefix=True, fallback_prefix: bool = True):
        """
        This is a simple helper method which calls :meth:`.cached.get` - while automatically prepending :attr:`.cache_prefix`
        and :attr:`.cache_sep` before the key.

        :param str key: The cache key (as a string) to get the value for, e.g. ``example:test``
        :param Any default: If the cache key ``key`` isn't found / is expired, return this value (Default: ``None``)
        :param bool fail: If set to ``True``, will raise :class:`.CacheNotFound` instead of returning ``default``
                          when a key is non-existent / expired.
        :param bool auto_prefix: If set to ``True``, will auto-prepend :attr:`.cache_prefix` to ``key`` if it's not present.
        :param bool fallback_prefix: If set to ``True``, if we fail to find ``key`` with the prefix prepended, then we'll retry
                                     a cache lookup WITHOUT the key prefix.
        :raises CacheNotFound: Raised when ``fail=True`` and ``key`` was not found in cache / expired.
        :return Any value: The value of the cache key ``key``, or ``default`` if it wasn't found.
        """
        # timeout = cls.default_cache_time if timeout == AUTO else timeout
        # For safety, if the cache key passed to this method already starts with `.cache_prefix`, then don't prepend
        # the cache_prefix to the key. Otherwise, if it's not present, then prepend the cache prefix.
        key = cls._pfx_key(key, auto_prefix=auto_prefix)
        try:
            return cached.get(key, default, fail=True)
        except CacheNotFound as outer:
            # If fallback_prefix is enabled - try looking up 'key' with the cache prefix removed from the start of it
            if fallback_prefix and key.startswith(cls.cache_prefix):
                try:
                    key = cls._unpfx_key(key)  # Remove the prefix from the cache key
                    return cached.get(key, default, fail=True)
                except CacheNotFound as inner:
                    # If we still can't find the key at this point - give up and return the default value (or raise if fail=True)
                    if fail: raise inner
                    return default
            # If fallback_prefix isn't enabled, or the key wasn't prefixed - give up and raise the exception or return default value.
            if fail: raise outer
            return default
    
    @classmethod
    def cache_get_or_set(cls, key: str, value: Any, timeout: Optional[AnyNum] = AUTO, auto_prefix=True):
        """
        This is a simple helper method which calls :meth:`.cached.get_or_set` - while automatically prepending :attr:`.cache_prefix`
        and :attr:`.cache_sep` before the key.

        :param str key: The cache key (as a string) to get the value for, e.g. ``example:test``
        :param Any value: The value to store in the cache key ``key``
        :param int timeout: The amount of seconds to keep the data in cache. Pass ``None`` to disable expiration.
        :param bool auto_prefix: If set to ``True``, will auto-prepend :attr:`.cache_prefix` to ``key`` if it's not present.
        :raises CacheNotFound: Raised when ``fail=True`` and ``key`` was not found in cache / expired.
        :return Any value: The value of the cache key ``key``, or ``default`` if it wasn't found.
        """
        timeout = cls.default_cache_time if timeout == AUTO else timeout
        # For safety, if the cache key passed to this method already starts with `.cache_prefix`, then don't prepend
        # the cache_prefix to the key. Otherwise, if it's not present, then prepend the cache prefix.
        key = cls._pfx_key(key, auto_prefix=auto_prefix)
        return cached.get_or_set(key, value, timeout=timeout)
    
    @classmethod
    def _pfx_key(
            cls, key: Union[str, Callable[[Any], str]], auto_prefix: bool = True, _auto_cache=True,
            call_args: list = None, call_kwargs: dict = None, _lock: ANY_LCK = None
    ) -> str:
        """
        Add this class's cache key prefix to ``key`` if it isn't already prefixed
        
        
        :param str|callable key:   The key to prepend the cache key prefix onto - if not already prefixed.
                                   This may optionally be a function (e.g. a lambda) which returns a cache key to be auto-prefixed,
                                   and any necessary positional/keyword arguments for the function may be specified using the
                                   arguments ``call_args`` and ``call_kwargs``
        
        :param bool auto_prefix:   This argument is mainly used by internal methods to reduce the need to copy/paste handling code
                                   which allows users to request that a method does not attempt to auto-prefix the key they entered.
                                   
        :param bool _auto_cache:   This is a boolean key, which controls whether or not keys are automatically logged to the cache key log,
                                   which is a list of all known cache keys for a given class. Uses :meth:`.log_cache_key`
        
        :param list call_args:     If ``key`` is a callable (e.g. a lambda), ``call_args`` can be set to a list of positional arguments
                                   to pass to the callable function ``key``
                                   
        :param dict call_kwargs:   If ``key`` is a callable (e.g. a lambda), ``call_kwargs`` can be set to a :class:`.dict` of
                                   keyword arguments to pass to the callable function ``key``
        
        :param ANY_LCK _lock:      This method itself does not use a lock, but it calls upon :meth:`.log_cache_key` which does use
                                   a lock. You may optionally pass a :class:`.Lock` instance if needed, e.g. to prevent a conflict
                                   where the calling function/method has already acquired the class-level lock.
                                   It can also be set to the dummy type :class:`.NO_LOCK` ``NO_LOCK`` to prevent using a lock.
        :return str new_key:       The original ``key`` after it may or may not have had a prefix prepended to it.
        """
        if callable(key):
            call_args, call_kwargs = auto_list(call_args), empty_if(call_kwargs, {}, itr=True, zero=True)
            key = key(*call_args, **call_kwargs)
        key = key if key.startswith(cls.cache_prefix) or not auto_prefix else cls.cache_sep.join([cls.cache_prefix, key])
        if _auto_cache:   # By default, _auto_cache is enabled, which means we log all created keys to the cache key log
            cls.log_cache_key(key, _lock=_lock)
        return key
    
    key_add_prefix = _pfx_key
    
    @classmethod
    def _unpfx_key(cls, key: str, prefix: str = None, sep: str = None):
        """Remove the cache key prefix from a given cache key"""
        prefix, sep = empty_if(prefix, cls.cache_prefix), empty_if(sep, cls.cache_sep)
        j = key.split(f"{prefix}{sep}")
        return j[0] if len(j) == 1 else ''.join(j[1:])
    
    key_remove_prefix = _unpfx_key
    
    @classmethod
    def clear_cache_keys(cls, *keys: str, auto_prefix=True, remove_log=True, _lock: ANY_LCK = None) -> bool:
        log.debug(f" [clear_cache_keys] Obtaining hold on lock: {_lock}")
        with cls._get_lock(_lock):
            pk = [cls._pfx_key(k, auto_prefix=auto_prefix, _auto_cache=False) for k in keys]
            log.debug(f" [clear_cache_keys] Clearing {len(pk)} keys from cache: {pk}")
            res = cached.remove(*pk)
            if remove_log:
                log.debug(f" [clear_cache_keys] remove_log is True. Removing {len(pk)} keys from cache key log: {pk}")
                # nlock = threading.Lock()
                cls.log_delete_cache_keys(*pk, _lock=NO_LOCK)
        log.debug(f" [clear_cache_keys] Released hold on lock: {_lock}")
        
        return res
    
    @classmethod
    def clear_all_cache_keys(cls):
        """
        Remove all known cache keys related to this class which aren't expired.
        
        Uses the ``cache key log`` under the class specific key name :attr:`.cache_key_log_name`, which is a cached list
        that contains all known cache keys that have been created by this class, whether via :meth:`.cache_set`, or
        using the CacheManager decorator :func:`.z_cache`
        """
        keys = list(cls.get_all_cache_keys())
        if len(keys) < 1:
            return "NO_CACHE_KEYS"
        return cls.clear_cache_keys(*list(cls.get_all_cache_keys()))


