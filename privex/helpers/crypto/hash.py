"""
Functions, classes, and variables for working with hashes (MD5, SHA1, SHA256, RIPEMD160 etc.)

 * A variety of small wrapper functions that use :class:`.XHash` for hashing, including
   :func:`.md5` , :func:`.sha1` , :func:`.sha256` , :func:`.whirlpool` , :func:`.ripemd160` and others.

 * :func:`.hashwrap` is used to generate wrapper functions like :func:`.md5` which use :class:`.XHash` for hashing.
 
 * :attr:`.HASH_MAP` is a dictionary mapping known hash algorithms, to wrapper functions that accept a single
   positional argument (the data to be hashed), and kwargs to forward to XHash.

 * :class:`.XHash` is a class based off of hashlib's :class:`._Hash` class, designed to act as an object
   representing a hash, and allowing for easy conversion between string hexdumps, the raw underlying bytes
   that the hash is made of, base64/32 representation, and integer encoding.
   
   It includes various classmethods that can be used to create a :class:`.XHash` instance from a string
   or bytestring, and hashing it.

 * :func:`.calc_hash` is an AsyncIO function for hashing a simple :class:`.str` / :class:`.bytes` string
 
 * :func:`.calc_hash_sync` is a synchronous wrapper function for using :func:`.calc_hash` in non-async contexts
 
 * :func:`.calc_hash_blocks` is an AsyncIO function for efficiently hashing a large amount of data, using a file
   handle, and reading + hashing small blocks at a time to avoid guzzling RAM.
   
 * :func:`.calc_hash_file` is an AsyncIO function for efficiently hashing a file on your disk, it's effectively
   a wrapper for :func:`.calc_hash_blocks` for use with files on your filesystem.
   
 * :func:`.calc_hashes_thread` is an AsyncIO + threaded function for quickly hashing multiple
   class:`.str` / :class:`.bytes` strings at the same time.
   
 * :func:`.hash_files_threads` is an AsyncIO + threaded function for quickly hashing multiple files at the
   same time, using the efficient block hashing via :func:`.calc_hash_blocks`
   
 
 
"""
import asyncio
import base64
import hashlib
import inspect
import warnings
from copy import deepcopy
from math import ceil
from pathlib import Path
from typing import Any, BinaryIO, Callable, Dict, Optional, Protocol, Tuple, Union

from privex.helpers.collections import DictObject
from privex.helpers.common import STRBYTES, byteify, empty, empty_if, is_true, stringify
from privex.helpers.asyncx import await_if_needed, run_coro_thread, run_coro_thread_async
from privex.helpers.types import EXSTRBYTES, T
from io import BytesIO, BufferedReader, BufferedRWPair

try:
    import _hashlib
    HLHash = _hashlib.HASH
except (ImportError, AttributeError, IndexError) as e:
    warnings.warn(f"Failed to import _hashlib.HASH - reason: {type(e)} - {str(e)}")
    HLHash = type("HLHash", (object,), {})

import logging

log = logging.getLogger(__name__)

__all__ = [
    'HLHash', 'KB', 'MB', 'GB', 'TB', 'int_bytes', 'Hash', 'wrap_int_hash', 'crc32', 'adler32', 'hashwrap',
    'ripemd160', 'whirlpool', 'shake_128', 'shake_256', 'HASH_MAP', 'SUPPORTS_UPDATE', 'supports_update',
    'init_hash', 'XHash', 'calc_hash', 'calc_hash_sync', 'FILE_BLOCK_SIZE', 'MIN_BLOCK_SIZE',
    'BYTES_IO', 'calc_hash_blocks', 'calc_hash_file', 'calc_hashes_thread', 'hash_files_threads'
]

KB = 1024
MB = 1024 ** 2
GB = 1024 ** 3
TB = 1024 ** 4


def int_bytes(data: int, endian='big') -> bytes:
    """
    Converts data represented as an integer :class:`.int` (e.g. a hash returned from :func:`zlib.crc32`)
    into :class:`.bytes`
    
    :param int data: The integer to be converted
    :param str endian: Either ``big`` or ``little`` - controls which byte order to use, either big or little endian.
    :return bytes hash: The data as :class:`.bytes`
    """
    num_bytes = int(ceil(data.bit_length() / 8))
    return data.to_bytes(num_bytes, endian)


class Hash(Protocol):
    """
    As :mod:`hashlib` does not make it's ``_Hash`` type accessible, we created this :class:`.Hash` class
    using :class:`.Protocol` as a stand-in replacement for :class:`hashlib._Hash`.
    
    This means that this class represents the objects returned by hashlib functions/methods, e.g.
    
        >>> h: Hash = hashlib.new("sha256", b"hello world")
    
    A protocol class works effectively like an "interface" in other programming languages.
    
    This class does not have any behaviour at all, it's purely a skeleton, holding expected attributes,
    the expected types of each attribute, expected methods, the parameters each method takes (and the types
    the parameters should be, if known), and the expected return type of methods (if known).
    """
    digest_size: int
    block_size: int
    name: str
    
    def copy(self) -> "Hash": ...
    
    def digest(self) -> bytes: ...
    
    def hexdigest(self) -> str: ...
    
    def update(self, data: Union[bytes, bytearray, memoryview]) -> Optional[Any]: ...


def wrap_int_hash(f) -> Callable[[Any], bytes]:
    """
    A decorator which wraps functions/methods which return :class:`.int` encoded bytes, and transparently
    converts the integer they return, into :class:`.bytes`

    It additionally enables strings to be passed, as any object that isn't :class:`.bytes` will be converted
    to a string, and then encoded into bytes before being passed to the wrapped function.

    Examples::

        >>> def example(data: bytes):
        >>>     return int(data.hex(), 16)
        >>> example(b"hello")
        448378203247
        >>> @wrap_int_hash
        >>> def example2(data: bytes):
        >>>     return int(data.hex(), 16)
        >>> example2(b"hello")
        b"hello"
        >>> example3 = wrap_int_hash(example)
        >>> example3("testing")
        b"testing"

    """
    
    def _wrapper(*args, **kwargs) -> bytes:
        args, kwargs = list(args), dict(kwargs)
        data = args[0]
        if 'value' in kwargs:
            data = kwargs.pop('value')
        elif 'data' in kwargs:
            data = kwargs.pop('data')
        elif inspect.ismethod(f) and len(args) > 1:
            data = args.pop(1)
        else:
            args.pop(0)
        
        if not isinstance(data, (str, bytes)):
            data = str(data)
        data = byteify(data)
        convd = f(data, *args, **kwargs)
        return int_bytes(convd)
    
    _wrapper.__name__ = f"{f.__name__}_wrap_int_hash"
    _wrapper.__qualname__ = f"{_wrapper.__module__}.wrap_int_hash.{f.__name__}"
    return _wrapper


def crc32(string: Union[str, bytes] = b'') -> "XHash":
    import zlib
    return XHash.from_int_func(byteify(string), zlib.crc32, digest_size=32, name='crc32')


def adler32(string: Union[str, bytes] = b'') -> "XHash":
    import zlib
    return XHash.from_int_func(byteify(string), zlib.adler32, digest_size=32, name='adler32')


def hashwrap(algo: str):
    """
    This is a wrapper/decorator which creates a function that takes one argument (the data to be hashed),
    and forwards it to :class:`.XHash` to hash it.
    
    Example::
    
        >>> my_md5 = hashwrap('md5')
        >>> x = my_md5('hello world')
        >>> x
        <XHash name='md5' hexdigest='5eb63bbbe01eeed093cb22bb8f5acdc3' orig_data=b'hello world' />
        >>> str(x)
        '5eb63bbbe01eeed093cb22bb8f5acdc3'
    
    """
    # noinspection PyTypeChecker
    def _hashwrap(orig_data: Union[str, bytes] = b'', **kwargs) -> "XHash":
        h = XHash.from_hashlib(algo, orig_data, **kwargs)
        return h
    
    return _hashwrap


md4, md5 = hashwrap('md4'), hashwrap('md5')
sha1, sha224, sha256, sha384, sha512 = hashwrap('sha1'), hashwrap('sha224'), hashwrap('sha256'), hashwrap('sha384'), hashwrap('sha512')
ripemd160 = hashwrap('ripemd160')
whirlpool = hashwrap('whirlpool')
shake_128 = hashwrap('shake_128')
shake_256 = hashwrap('shake_256')

# noinspection PyTypeChecker
HASH_MAP: Dict[str, Callable[[STRBYTES], "XHash"]] = dict(
    crc32=crc32,
    adler32=adler32,
    md4=md4, md5=md5,
    sha1=sha1, sha224=sha224, sha256=sha256, sha384=sha384, sha512=sha512,
    blake2b=hashwrap('blake2b'),
    blake2s=hashwrap('blake2s'),
    ripemd160=hashwrap('ripemd160'),
    whirlpool=hashwrap('whirlpool'),
    shake_128=hashwrap('shake_128'),
    shake_256=hashwrap('shake_256'),
    sm3=hashwrap('sm3'),
)
SUPPORTS_UPDATE: Dict[str, bool] = dict(
    crc32=False,
    adler32=False,
    md4=True, md5=True,
    sha1=True, sha224=True, sha256=True, sha384=True, sha512=True,
    blake2b=True, blake2s=True, ripemd160=True, whirlpool=True,
    shake_128=True, shake_256=True, sm3=True,
)


def supports_update(algo: str, fallback: T = False) -> Union[bool, T]:
    if algo in SUPPORTS_UPDATE: return SUPPORTS_UPDATE[algo]
    if algo.lower() in SUPPORTS_UPDATE: return SUPPORTS_UPDATE[algo.lower()]
    return fallback


async def init_hash(algo: str, data: STRBYTES, store_data=True, force_disable_store=False, **kwargs) -> Tuple["XHash", str]:
    algo = algo.lower()
    if algo not in HASH_MAP:
        raise ValueError(f"The algorithm '{algo}' is not supported. Supported algorithms: {', '.join(HASH_MAP)}")
    data = byteify(data)
    # noinspection PyArgumentList
    res = HASH_MAP[algo](data, store_data=store_data, force_disable_store=force_disable_store)
    return res, algo


class XHash(Hash):
    """
    This is a wrapper class, which is designed to wrap very simple hashing functions that accept
    a :class:`.bytes` first positional argument containing the data to be hashed, and returns the
    hash result as :class:`.bytes`
    
    It attempts to emulate the functionality normally provided by the :class:`hashlib._Hash` object
    returned when calling :func:`hashlib.new` - as well as providing many user friendly features,
    such as easy conversion into a string hex digest, raw bytes, or even integer encoded using
    the standard ``str()`` / ``bytes()`` / ``int()`` casting types.
    
    **Examples**
    
    Create an :class:`.XHash` object by hashing a string or bytes with hashlib::
        
        >>> xh = XHash.from_hashlib('md5', 'hello world')
        >>> xh
        <XHash name='md5' hexdigest='5eb63bbbe01eeed093cb22bb8f5acdc3' orig_data=b'hello world' />
    
    Using :class:`.XHash` with hash functions that return an integer instead of bytes::
    
        >>> import zlib
        >>> # zlib.crc32 returns an int instead of bytes, so we have to use from_int_func to wrap it
        >>> h = XHash.from_int_func(b"hello", zlib.crc32)
        >>> print(repr(h))
        <XHash name='' hexdigest='3610a686' orig_data='b'hello'' />
        >>> h.update(b" world")
        >>> print(repr(h))
        <XHash name='' hexdigest='0d4a1185' orig_data='b'hello world'' />
    
    Seamless conversion between :class:`.bytes` (raw digest), :class:`.str` (hex digest),
    and :class:`.int` (integer encoded digest), using standard python casting::
    
        >>> print(int(h))
        222957957
        >>> print(str(h))
        0d4a1185
        >>> print(bytes(h))
        b'\rJ\x11\x85'
    
    Instead of calling :meth:`.update` - you can use the ``+`` operator between an XHash instance, and
    a :class:`.str`, :class:`.bytes`, :class:`.int` or another :class:`.XHash` instance.
    
        >>> a = h + " lorem"
        >>> b = a + b" ipsum"
        >>> c = int(b" dolor".hex(), 16)
        >>> print(repr(h))
        <XHash name='' hexdigest='0d4a1185' orig_data='b'hello world'' />
        
    """
    digest_size: int
    block_size: int
    name: str
    
    HASHCLS = Optional[Union[Hash, "XHash", HLHash]]
    BYTEFUNC = Callable[[bytes], bytes]
    BYTEFUNCCLS = Union[BYTEFUNC, HASHCLS]
    hash_class: HASHCLS
    item_act: str
    _cache: Union[Dict[str, Any], DictObject]
    
    def __init__(self, orig_data: STRBYTES = b'', data: Union[bytes, int] = b'', wrapper: BYTEFUNCCLS = lambda x: x, *args, **kwargs):
        """
        Construct an instance of :class:`.XHash`
        
        :param str|bytes orig_data: If known, the original data before it was hashed using ``wrapper``
        :param callable|Hash|HLHash wrapper: A function which hashes :class:`.bytes` data into :class:`.bytes` encoded hashes
        :param bytes|int data: If the data has already been hashed, you may pass the :class:`.bytes` or :class:`.int` hash data
        :param kwargs: Any additional keyword args to be passed to the constructor.
        :keyword int digest_size: The hash digest size in BITS, as an integer.
        :keyword int block_size: The block size of the hash algorithm (optional)
        :keyword str name: The name of the hash algorithm, e.g. ``md5``, ``sha256`` etc.
        """
        # If the hash is represented as an integer, we convert it into bytes
        if isinstance(data, int):
            data = int_bytes(data)
        self.digest_size = kwargs.get('digest_size', 0)
        self.block_size = kwargs.get('block_size', 0)
        self.name = kwargs.get('name', '')
        self.hash_class = kwargs.get('hash_class', None)
        if isinstance(wrapper, HLHash):
            if self.hash_class is None:
                self.hash_class = wrapper
            hc = self.hash_class
            self.name = empty_if(self.name, hc.name)
            self.block_size = empty_if(self.block_size, hc.block_size)
            self.digest_size = empty_if(self.digest_size, hc.digest_size, zero=True)
            wrapper = lambda value: hashlib.new(self.name, value).digest()
            hc_digest = hc.digest()
            if len(hc_digest) > 0:
                data = hc_digest
        
        orig_data = byteify(orig_data)
        # If the hash (data) is empty, we hash orig_data using wrapper
        if len(data) == 0:
            data = wrapper(orig_data)
        self.wrapper = wrapper
        
        self.item_act = kwargs.get('item_act', 'str')
        """
        The ``item_act`` attribute/kwarg controls what happens when you access the instance like a list with
        integer indexes / slices, e.g. ``xh[2]`` or ``xh[3:-1]``.
        
        This can be changed on-the-fly, e.g. ``xh.item_act = 'base64'``
         
          * ``str``    - When XHash is accessed like a list (``xh[1]``), the indices will be used against the STRING HASH
                         value, i.e. the hex version.
          * ``bytes``  - When accessed like a list, the indices will be used against the RAW BYTES hash value
          * ``base64`` - When accessed like a list, the indices will be used against the BASE64 hash value
          * ``base32`` - When accessed like a list, the indices will be used against the BASE32 hash value
        """
        
        self._cache = DictObject()
        self.use_cache = kwargs.get('use_cache', True)
        
        # If a certain algorithm supports efficient updates (appending data to be hashed, without needing the entirety
        # of the source data in memory to re-generate the hash), then a user may ask XHash to not store any of the
        # original or updated data into self.orig_data to avoid wasting RAM
        store_data = is_true(kwargs.get('store_data', True))
        # When store_data=False, we only disable data storing if supports_update confirms the algorithm seems
        # to support efficient updates.
        # If a user is absolutely certain that the algorithm they're using - supports efficient updates, they
        # can pass 'force_disable_store=True' to force data storage to be disabled, regardless of what supports_update reports.
        force_disable_store = is_true(kwargs.get('force_disable_store', False))
        if force_disable_store or (not store_data and supports_update(self.name)):
            self.orig_data = b''
            self.store_data = False
        else:
            self.store_data = True
            self.orig_data = orig_data
        self.data = data
        
        self.digest_size = empty_if(self.digest_size, len(self.data), zero=True)
        self.block_size = empty_if(self.block_size, 1, zero=True)

    @property
    def cache(self) -> DictObject:
        if empty(self._cache):
            self._cache = DictObject()
        return self._cache

    @cache.setter
    def cache(self, value):
        self._cache = value

    @cache.deleter
    def cache(self):
        self._cache = DictObject()
    
    def copy(self) -> Union["Hash", "XHash"]:
        """Create a new :class:`.XHash` instance with the same hash data and configuration as the current instance"""
        return XHash(
            self.orig_data, self.data, wrapper=self.wrapper,
            digest_size=self.digest_size, block_size=self.block_size, name=self.name,
            hash_class=self.hash_class
        )
    
    def digest(self) -> bytes:
        """Return the hash as a raw :class:`.bytes` digest"""
        return self.data
    
    def hexdigest(self) -> str:
        """Return the hash as a string :class:`.str` hex digest"""
        return self.data.hex()
    
    def update(self, data: Union[bytes, bytearray, memoryview, str]) -> Optional[Any]:
        """
        Append ``data`` to the original data and update the hash digest.
        
        :param str|bytes|bytearray|memoryview data: A data string/bytes to append - as either :class:`.bytes`, :class:`.str` or others.
        """
        data = byteify(data) if not isinstance(data, (bytes, bytearray, memoryview)) else data
        if self.store_data:
            self.orig_data += data

        if self.hash_class:
            log.debug(f"XHash instance has a hash_class. Using more efficient update method of hash class: {self.hash_class!r}")
            self.hash_class.update(data)
            self.data = self.hash_class.digest()
        else:
            log.debug("XHash instance doesn't have a hash_class. Handling update call by regenerating hash with updated data.")
            if self.store_data:
                self.data = self.wrapper(self.orig_data)
            else:
                self.data = self.wrapper(data)
        return self
    
    @classmethod
    def from_hashlib(cls, algorithm: str = "sha256", orig_data: STRBYTES = b'', **kwargs) -> "XHash":
        """
        Create an :class:`.XHash` object by hashing a string or bytes with hashlib.
        
        Example::
            
            >>> xh = XHash.from_hashlib('md5', 'hello world')
            >>> xh
            <XHash name='md5' hexdigest='5eb63bbbe01eeed093cb22bb8f5acdc3' orig_data=b'hello world' />
            
        :param str algorithm: A supported hashlib hash algorith, e.g. md5, sha1, sha256, sha512, ripemd160
        :param bytes|str orig_data: The data to hash, as either :class:`.bytes` or :class:`.str`
        :param kwargs: Additional arguments to forward to the :class:`.XHash` constructor
        :return XHash obj: An instance of :class:`.XHash` initialised with the hash data
        """
        orig_data = byteify(orig_data)
        kwargs = dict(kwargs)
        kwargs['wrapper'] = hashlib.new(algorithm, orig_data)
        kwargs['name'] = algorithm
        if 'data' in kwargs: kwargs.pop('data')
        return cls(orig_data, **kwargs)
    
    @classmethod
    def from_int_func(
            cls, orig_data: STRBYTES = b'', wrapper: Callable[[bytes], int] = lambda x: x, data: Union[bytes, int] = b'', **kwargs
    ) -> "XHash":
        """
        This classmethod constructs the class just like :meth:`.__init__`, but also wraps ``wrapper``
        using the decorator function :func:`.wrap_int_hash`, which will transparently convert integer results returned
        from ``wrapper`` automatically.
        
        This is important when wrapping functions/methods such as :func:`zlib.crc32` or :func:`zlib.adler32` which
        return integer hashes, instead of :class:`.bytes` or string hex digests.
        
        Example::
        
            >>> import zlib
            >>> zlib.crc32(b"hello world")
            222957957
            >>> h = XHash.from_int_func(b'hello world', zlib.crc32)
            >>> h.hexdigest()
            '0d4a1185'
            >>> print(repr(h))
            <XHash name='' hexdigest='0d4a1185' orig_data='b'hello world'' />
        
            
        :param str|bytes orig_data: If known, the original data before it was hashed using ``wrapper``
        :param callable wrapper: A function which hashes :class:`.bytes` into :class:`.int` numeric objects.
        :param bytes|int data: If the data has already been hashed, you may pass the :class:`.bytes` or :class:`.int` hash data
        :param kwargs: Any additional keyword args to be passed to the constructor.
        :return XHash inst: A new instance of the class :class:`.XHash`
        """
        # Wrap the 'wrapper' function with the wrap_int_hash method, which will automatically intercept the 'int'
        # result returned from the function, and convert it into 'bytes'
        # noinspection PyTypeChecker
        wrapped = wrap_int_hash(wrapper)
        orig_data, data = empty_if(orig_data, b''), empty_if(data, b'')
        if isinstance(data, int): data = int_bytes(data)
        return cls(orig_data=orig_data, data=data, wrapper=wrapped, **kwargs)
    
    def to_dict(self) -> dict:
        """
        Returns a :class:`.dict` containing all the data attributes of this instance.
        
        :return dict data: The class data as a dictionary.
        """
        return dict(
            wrapper=self.wrapper, digest_size=self.digest_size, block_size=self.block_size,
            name=self.name, orig_data=self.orig_data, data=self.data
        )
        # if init_names: data.update(dict(orig=self.orig_data, hashed=self.data))
        # if attr_names: data.update(dict(orig_data=self.orig_data, data=self.data))
        # return data
    
    def to_base64(self, string=True, urlsafe=False, altchars: Optional[bytes] = None, encoding: str = 'utf-8') -> STRBYTES:
        """
        Encode the :class:`.bytes` hash data of this instance using Base64.
        
        :param bool string: (Default: ``True``) If ``True``, decodes the base64 bytestring into a normal string using ``encoding``
        
        :param bool urlsafe: (Default: ``False``) If ``True``, uses :func:`base64.urlsafe_b64encode` instead of :func:`base64.b64encode`
        
        :param None|bytes altchars: A bytes-like object or ASCII string of at least length 2 (additional characters are ignored) which
                                    specifies the alternative alphabet used instead of the + and / characters.
        
        :param str encoding: (Default: ``utf-8``) The encoding to use when decoding the base64 bytes into a string
        
        :return str|bytes b64: The base64 encoded hash bytes, as either a :class:`.str` or :class:`.bytes` depending on ``string``
        """
        cstr = f"{self!s}:{string}:{urlsafe}:{altchars}:{encoding}"
        if 'base64' in self.cache and cstr in self.cache['base64']: return self.cache['base64'][cstr]
        s = bytes(self)
        b = base64.urlsafe_b64encode(s) if urlsafe else base64.b64encode(s, altchars=altchars)
        res = stringify(b, encoding=encoding) if string else b
        if self.use_cache:
            if 'base64' not in self.cache: self.cache['base64'] = DictObject()
            self.cache['base64'][cstr] = res
        return res

    def to_base32(self, string=True, encoding: str = 'utf-8') -> STRBYTES:
        """
        Encode  the :class:`.bytes` hash data of this instance using Base32 - similar to :meth:`.to_base64`
        
        :param bool string: (Default: ``True``) If ``True``, decodes the base64 bytestring into a normal string using ``encoding``
        :param str encoding: (Default: ``utf-8``) The encoding to use when decoding the base64 bytes into a string
        :return str|bytes b32: The base32 encoded hash bytes, as either a :class:`.str` or :class:`.bytes` depending on ``string``
        """
        cstr = f"{self!s}:{string}:{encoding}"

        if 'base32' in self.cache and cstr in self.cache['base32']: return self.cache['base32'][cstr]

        b = base64.b32encode(bytes(self))
        res = stringify(b, encoding=encoding) if string else b

        if self.use_cache:
            if 'base32' not in self.cache: self.cache['base32'] = DictObject()
            self.cache['base32'][cstr] = res
        return res

    def __add__(self, other):
        if isinstance(other, (str, bytes)):
            return self.copy().update(other)
        if isinstance(other, int):
            return self.copy().update(int_bytes(other))
        if isinstance(other, XHash):
            ow, sw = other.wrapper, self.wrapper
            ow: callable
            sw: callable
            if not all([
                ((ow.__name__ == sw.__name__) or (ow.__qualname__ == sw.__qualname__)),
                ow.__module__ == sw.__module__
            ]):
                raise ValueError(f"The XHash object '{other!r}' has a different hash wrapper function than {self!r}")
            return self.copy().update(other.orig_data)
        
    def __iter__(self):
        # x = dict(
        #     orig_data=self.orig_data, data=self.data, wrapper=self.wrapper,
        #     digest_size=self.digest_size, block_size=self.block_size, name=self.name
        # )
        yield from self.to_dict().items()
    
    def __index__(self):
        return int(self)
    
    def __str__(self) -> str:
        return self.hexdigest()
    
    def __len__(self):
        return len(self.hexdigest())
    
    def __eq__(self, other):
        if isinstance(other, str):
            return other == self.hexdigest()
        if isinstance(other, bytes):
            return other == self.data
        if isinstance(other, int):
            return other == int(self)
        if isinstance(other, XHash):
            return all([
                other.name == self.name,
                other.data == self.data,
                other.orig_data == self.orig_data,
                other.digest_size == self.digest_size,
                other.block_size == self.block_size,
            ])
        try:
            otherstr = str(other)
            if other == self.hexdigest():
                return True
            if otherstr.encode('utf-8') == self.digest():
                return True
        except Exception as e:
            log.warning(f"Error while casting comparator object '{repr(other)}' to string/bytes: {type(e)} - {str(e)}")
        return False
    
    def __copy__(self):
        return self.copy()
    
    def __deepcopy__(self, memodict=None):
        memodict = {} if memodict is None else memodict
        # noinspection PyArgumentList
        data = deepcopy(self.to_dict(), memodict)
        return XHash(
            **data, hash_class=deepcopy(self.hash_class),
            # deepcopy(self.orig_data), deepcopy(self.data), wrapper=deepcopy(self.wrapper),
            # digest_size=deepcopy(self.digest_size), block_size=deepcopy(self.block_size), name=deepcopy(self.name)
        )
    
    def __bytes__(self) -> bytes:
        return self.digest()
    
    def __repr__(self) -> str:
        return f"<XHash name='{self.name}' hexdigest='{self.hexdigest()}' orig_data={self.orig_data} />"
    
    def __int__(self) -> int:
        return int(self.digest().hex(), 16)
    
    def __getitem__(self, item):
        """
        Example customisation of what item indexes/slices refer to::
        
            >>> xh = XHash.from_hashlib('md5', "hello world\\n")
            >>> xh
            <XHash name='md5' hexdigest='6f5902ac237024bdd0c176cb93063dc4' orig_data=b'hello world\n' />
            >>> xh[0]
            '6'
            >>> xh[0:5]
            '6f590'
            >>> xh.item_act = 'bytes'
            >>> xh[0:5]
            b'oY\x02\xac#'
            >>> xh.item_act = 'b64'
            >>> xh[0:5]
            'b1kCr'
        
        """
        if isinstance(item, (int, slice)):
            if self.item_act in ['byte', 'bytes']: return bytes(self)[item]
            if self.item_act in ['b64', 'base64']: return self.to_base64()[item]
            if self.item_act in ['b32', 'base32']: return self.to_base32()[item]
            return str(self)[item]
        d = dict(self)
        if item in d: return d[item]
        return self.__getattribute__(item)
    
    def __setitem__(self, key, value):
        return self.__setattr__(key, value)
        

async def calc_hash(data: STRBYTES, algo: str = 'sha256', b64=False, hexdigest=True, **kwargs) -> STRBYTES:
    """
    Hash a :class:`.bytes` or :class:`.str` object using the ``algo`` algorithm.

    .. Warning:: This is an AsyncIO function! - If you need to hash something from a synchronous context, use the
                 synchronous wrapper :func:`.calc_hash_sync`

    **Examples**::

        >>> await calc_hash(b"hello world")
        'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9'
        >>> await calc_hash("lorem ipsum", algo="sha512")
        'f80eebd9aabb1a15fb869ed568d858a5c0dca3d5da07a410e1bd988763918d973e344814625f7c844695b2de36ffd27af290d0e34362c51dee5947d58d40527a'
        >>> await calc_hash(b"lorem ipsum", algo="sha256", b64=True)
        'NWUyYmY1N2QzZjQwYzRiNmRmNjlkYWYxOTM2Y2I3NjZmODMyMzc0YjRmYzAyNTlhN2NiZmYwNmUyZjcwZjI2OQ=='
        >>> await calc_hash(b"lorem ipsum", algo="sha256", hexdigest=False)
        b'^+\xf5}?@\xc4\xb6\xdfi\xda\xf1\x93l\xb7f\xf827KO\xc0%\x9a|\xbf\xf0n/p\xf2i'

    **Popular Supported Algorithms**

    For a full list of supported algorithms, see :attr:`.HASH_MAP`

      * ``crc32``
      * ``adler32``
      * ``md4`` + ``md5``
      * ``sha1``
      * ``sha224`` + ``sha256`` + ``sha384`` + ``sha512``
      * ``ripemd160``
      * ``whirlpool``

    :param bytes|str data: A :class:`.bytes` or :class:`.str` object to hash
    :param str algo: The hashing algorithm to use, e.g. ``sha256`` / ``sha384`` - must be in :attr:`.HASH_MAP`
    :param bool b64: When ``True``, encodes the hash with Base64 before outputting it
    :param bool hexdigest: When ``True``, encodes the raw hash as a hex digest, instead of as a bytes digest.
                           If ``b64=True``, hex digestion is done BEFORE base64 encoding.

    :keyword bool decode_b64: (Default: ``True``) Boolean var which controls whether or not a BASE64 encoded result should
                              be automatically decoded from :class:`.bytes` into a :class:`.str`
    :keyword bool decode_raw: (Default: ``False``) Boolean var which controls whether or not a raw binary hash result should
                              be automatically decoded from :class:`.bytes` into a :class:`.str`

    :return str|bytes hash: The resulting hash, either as :class:`.bytes` if ``b64`` and ``hexdigest`` are False, otherwise as a string.
    """
    decode_b64 = kwargs.get('decode_b64', True)
    decode_raw = kwargs.get('decode_raw', False)
    
    res, algo = await init_hash(algo, data, store_data=False)
    res = res.hexdigest() if hexdigest else res.digest()
    
    if not b64:
        return stringify(res) if decode_raw else res
    res = base64.b64encode(byteify(res))
    return stringify(res) if decode_b64 else res


def calc_hash_sync(data: STRBYTES, algo: str = 'sha256', b64=False, hexdigest=True, **kwargs) -> STRBYTES:
    """
    Hash a :class:`.bytes` or :class:`.str` object using the ``algo`` algorithm.
    
    This is simply a wrapper function for the AsyncIO function :func:`.calc_hash` - please see the PyDoc
    comment for :func:`.calc_hash` for more information on how to use this function.
    
    **Examples**::

        >>> calc_hash_sync(b"hello world")
        'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9'
        >>> calc_hash_sync("lorem ipsum", algo="sha512")
        'f80eebd9aabb1a15fb869ed568d858a5c0dca3d5da07a410e1bd988763918d973e344814625f7c844695b2de36ffd27af290d0e34362c51dee5947d58d40527a'
    
    :param bytes|str data: A :class:`.bytes` or :class:`.str` object to hash
    :param str algo: The hashing algorithm to use, e.g. ``sha256`` / ``sha384`` - must be in :attr:`.HASH_MAP`
    :param bool b64: When ``True``, encodes the hash with Base64 before outputting it
    :param bool hexdigest: When ``True``, encodes the raw hash as a hex digest, instead of as a bytes digest.
                           If ``b64=True``, hex digestion is done BEFORE base64 encoding.
    
    :return str|bytes hash: The resulting hash, either as :class:`.bytes` if ``b64`` and ``hexdigest`` are False, otherwise as a string.
    """
    return run_coro_thread(calc_hash, data, algo, b64=b64, hexdigest=hexdigest, **kwargs)


FILE_BLOCK_SIZE = 64 * MB
MIN_BLOCK_SIZE = 100 * MB

BYTES_IO = Union[BytesIO, BinaryIO, BufferedReader, BufferedRWPair]


async def calc_hash_blocks(fh: BYTES_IO, fsize: int, algo: str = 'sha256', b64=False, hexdigest=True, **kwargs) -> STRBYTES:
    """
    Generates a hash efficiently, by reading and hashing iteratively read data blocks from a file-like object.
    
    With algorithms that support efficient ``.update()`` calls, such as ``sha1`` - ``sha512`` and ``md5``,
    this can allow for hashing a large amount of data (i.e. multiple GB worth), without having to load the
    entire data into memory.
    
    Additionally, by specifying a function to ``block_callback`` - your calling code can be notified each time
    a block is read, with ``(current_block: int, total_blocks: int)`` - allowing you to display progress information
    as the file is hashed.
    
    **Example**::
        
        >>> from pathlib import Path
        >>> p = Path('~/big-example-file.iso').expanduser()
        >>> fsz = p.stat().st_size
        >>> with open(str(p), 'rb') as fp:
        ...     h = await calc_hash_blocks(fp, fsz, 'md5')
        >>> print(h)
        5eb63bbbe01eeed093cb22bb8f5acdc3
    
    
    :param BYTES_IO fh: A file-like object which returns bytes when ``.read()`` is called
    :param int fsize: The total amount of data in ``fh`` as an integer number of bytes
    :param str algo:  The hashing algorithm to use, e.g. ``sha256`` / ``sha384`` - must be in :attr:`.HASH_MAP`
    :param bool b64: When ``True``, encodes the hash with Base64 before outputting it
    :param bool hexdigest: When ``True``, encodes the raw hash as a hex digest, instead of as a bytes digest.
                           If ``b64=True``, hex digestion is done BEFORE base64 encoding.
    :param kwargs:
    :keyword int blocksize: The number of bytes to read during each block iteration. Default :attr:`.FILE_BLOCK_SIZE`
    :keyword str filename:  Only used in DEBUG logs, for displaying the filename of the file that's being read.
    :keyword callable block_callback: An optional callback function, which will be called with the
                                      parameters ``(current_block: int, total_blocks: int)`` - allowing the caller
                                      to potentially track progress of the hashing operation.
    :return str|bytes digest: The hash digest of the file, as either a hex string, base64 string, or raw bytes
    """
    blocksize = int(kwargs.get('blocksize', FILE_BLOCK_SIZE))
    filename = kwargs.get('filename', '')
    block_callback = kwargs.get('block_callback', lambda current, end: None)

    total_blocks = ceil(float(fsize) / float(blocksize))
    curblock = 1
    res, algo = await init_hash(algo, b'', store_data=False)

    # 1 < 5
    # 2 < 5
    # 3 < 5
    # 4 < 5
    # 5 !!!
    log.debug(f"[{curblock} / {total_blocks}] Reading first block of {blocksize} bytes from file: {filename}")
    data = fh.read(blocksize)
    res.update(data)
    await await_if_needed(block_callback(1, total_blocks))
    curblock += 1
    
    while len(data) > 0:
        log.debug(f"[{curblock} / {total_blocks}] Reading block of {blocksize} bytes")
        data = fh.read(blocksize)
        res.update(data)
        await await_if_needed(block_callback(curblock, total_blocks))
        curblock += 1

    log.debug(f"Digesting hash. Hex digest? {hexdigest}")
    res = res.hexdigest() if hexdigest else res.digest()

    if b64:
        log.debug(f"Base64 encoding data...")
        res = base64.b64encode(byteify(res)).decode('utf-8')
    return res


async def calc_hash_file(filename: str, algo: str = 'sha256', b64=False, hexdigest=True, **kwargs) -> STRBYTES:
    """
    
    **Example**::
    
        >>> await calc_hash_file("~/Downloads/tails-amd64-4.13.iso", 'md5')
        '1121970d5891d89b4a1b05bccc3ac9d4'
    
    **Custom Block Size**
    
    By default, blocks are read in chunks of :attr:`.FILE_BLOCK_SIZE` bytes (at the time of writing, it's set to 64MB),
    but you can override the block size to use by passing the keyword argument ``blocksize`` (number of bytes)
    
    For example, to read blocks of 512 MB at a time::
    
        >>> await calc_hash_file("~/Downloads/tails-amd64-4.13.iso", 'sha256', blocksize=512 * 1024 * 1024)
        '880d926c4aef6ac27bc775f1cd99ccdd719499ced982449a31aa0a660f0546a0'
    
    Or, if you'd rather read the entire file into memory and hash that, instead of dividing the file into blocks and
    hashing each block, simply set ``blocksize=0`` to disable block reading::
        
        >>> await calc_hash_file("~/Downloads/tails-amd64-4.13.iso", 'md5', blocksize=0)
    
    :param str filename: The absolute or relative path to the file you want to hash
    :param str algo:  The hashing algorithm to use, e.g. ``sha256`` / ``md5`` - must be in :attr:`.HASH_MAP`
    :param bool b64: When ``True``, encodes the hash with Base64 before outputting it
    :param bool hexdigest: When ``True``, encodes the raw hash as a hex digest, instead of as a bytes digest.
                           If ``b64=True``, hex digestion is done BEFORE base64 encoding.
    :param kwargs: Keyword arguments - see below for available keyword arguments
    
    :keyword int blocksize: The number of bytes to read during each block iteration. Default :attr:`.FILE_BLOCK_SIZE`
    :keyword int min_blocksize: The minimum size (in bytes) that a file needs to be, before it's read in blocks,
                                instead of reading the entire file into memory. Default :attr:`.MIN_BLOCK_SIZE`
    :keyword callable block_callback: An optional callback function, which will be called with the
                                  parameters ``(current_block: int, total_blocks: int)`` - allowing the caller
                                  to potentially track progress of the hashing operation.
    
    :return str|bytes digest: The hash digest of the file, as either a hex string, base64 string, or raw bytes

    """
    blocksize = kwargs.get('blocksize', FILE_BLOCK_SIZE)
    min_blocksize = kwargs.get('min_blocksize', MIN_BLOCK_SIZE)
    block_callback = kwargs.get('block_callback', lambda current, end: None)
    p = Path(str(filename)).expanduser().resolve()
    filename = str(p)
    # Do not use a block-reading loop to read the file if any of the following conditions are true:
    #   - The file is smaller than the block size we'd read per cycle (blocksize / FILE_BLOCK_SIZE)
    #   - The file is smaller than the minimum block size required before we split the process into blocks (min_blocksize / MIN_BLOCK_SIZE)
    #   - The hash algorithm we're going to use, does not support efficient "update" hashing, thus reading in
    #     blocks wouldn't reduce memory usage nor improve performance.
    #
    fsize = p.stat().st_size
    if empty(blocksize, zero=True) or fsize <= blocksize or algo not in SUPPORTS_UPDATE or (min_blocksize > 0 and fsize <= min_blocksize):
        with open(filename, 'rb') as fh:
            data = fh.read()
        return await calc_hash(data, algo=algo, b64=b64, hexdigest=hexdigest)

    # res, algo = await init_hash(algo, b'')

    with open(filename, 'rb') as fh:
        h = await calc_hash_blocks(
            fh, fsize, algo=algo, b64=b64, hexdigest=hexdigest,
            blocksize=blocksize, block_callback=block_callback, filename=filename
        )
        # total_blocks = ceil(fsize / blocksize)
        # curblock = 1
        # # 1 < 5
        # # 2 < 5
        # # 3 < 5
        # # 4 < 5
        # # 5 !!!
        # log.debug(f"[{curblock} / {total_blocks}] Reading first block of {blocksize} bytes from file: {filename}")
        # data = fh.read(blocksize)
        # res.update(data)
        # await await_if_needed(block_callback(1, total_blocks))
        # curblock += 1
        #
        # while len(data) > 0:
        #     log.debug(f"[{curblock} / {total_blocks}] Reading block of {blocksize} bytes")
        #     data = fh.read(blocksize)
        #     res.update(data)
        #     await await_if_needed(block_callback(curblock, total_blocks))
        #     curblock += 1
    return h
    # log.debug(f"Digesting hash. Hex digest? {hexdigest}")
    # res = res.hexdigest() if hexdigest else res.digest()
    # if not b64:
    #     return res
    # log.debug(f"Base64 encoding data...")
    # res = base64.b64encode(byteify(res))
    # return f"{algo}-{res.decode('utf-8')}" if prep_algo else res.decode('utf-8')


async def calc_hashes_thread(
        *data: STRBYTES, algo: str = 'sha256', b64=False, hexdigest=True, fail=True, **kwargs
) -> Tuple[EXSTRBYTES, ...]:
    """
    Hash one or more strings of :class:`.bytes` or :class:`.str` using AsyncIO threads
    
    **Examples**::
    
        >>> await calc_hashes_thread("hello world", "testing", b"lorem ipsum dolor")
        ('b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9',
         'cf80cd8aed482d5d1527d7dc72fceff84e6326592848447d2dc0b0e87dfc9a90',
         'ed03353266c993ea9afb9900a3ca688ddec1656941b1ca15ee1650a022616dfa')
        
        >>> await calc_hashes_thread("hello world", "testing", b"lorem ipsum dolor", algo='md5')
        ('5eb63bbbe01eeed093cb22bb8f5acdc3', 'ae2b1fca515949e5d54fb22b8ed95575', 'bfab65d69198004a3981e11872ee1b17')

    :param str|bytes data: The strings of data to hash, as :class:`.bytes` or :class:`.str`
    :param str algo:  The hashing algorithm to use, e.g. ``sha256`` / ``md5`` - must be in :attr:`.HASH_MAP`
    :param bool b64: When ``True``, encodes the hash with Base64 before outputting it
    :param bool hexdigest: When ``True``, encodes the raw hash as a hex digest, instead of as a bytes digest.
                           If ``b64=True``, hex digestion is done BEFORE base64 encoding.
    :param bool fail: When ``True``, raises an exception if any hash attempt fails. When ``False``, any failed
                      hash attempt will have it's :class:`.Exception` returned in the tuple as an object.
    :param kwargs: Extra keyword arguments to pass to :func:`.calc_hash`
    
    :return str|bytes digest: The hash digest of the file, as either a hex string, base64 string, or raw bytes

    """
    calls = [run_coro_thread_async(calc_hash, d, algo=algo, b64=b64, hexdigest=hexdigest, **kwargs) for d in data]
    return tuple(await asyncio.gather(*calls, return_exceptions=not fail))


async def hash_files_threads(
        *filenames: Union[str, Path], algo: str = 'sha256', b64=False, hexdigest=True, fail=True, **kwargs
) -> Tuple[EXSTRBYTES, ...]:
    """Hash files using AsyncIO threads"""
    # with open(str(filename), 'rb') as fh:
    #     data = fh.read()
    
    calls = [
        run_coro_thread_async(calc_hash_file, fn, algo=algo, b64=b64, hexdigest=hexdigest, **kwargs)
        for fn in filenames
    ]
    return tuple(await asyncio.gather(*calls, return_exceptions=not fail))
    # return (await calc_hashes_thread(data, algo=algo, b64=b64, hexdigest=hexdigest, **kwargs))[0]
