from privex.helpers.common import *
from privex.helpers.collections import *
from privex.helpers.decorators import *
from privex.helpers.net import *
from privex.helpers.exceptions import *
from privex.helpers.plugin import *
from privex.helpers.cache.asyncx import *
from privex.helpers.cache.extras import *
from privex.helpers.asyncx import *
from privex.helpers.extras import *
from privex.helpers.converters import *
from privex.helpers.geoip import *
from privex.helpers.thread import *
from privex.helpers import plugin as plugin
from privex.helpers.cache import CacheAdapter as CacheAdapter, CacheNotFound as CacheNotFound, CacheWrapper as CacheWrapper, MemoryCache as MemoryCache, cached as cached
from privex.helpers.cache.MemcachedCache import MemcachedCache as MemcachedCache
from privex.helpers.cache.RedisCache import RedisCache as RedisCache
from privex.helpers.cache.SqliteCache import SqliteCache as SqliteCache
from privex.helpers.crypto import EncryptHelper as EncryptHelper, Format as Format, KeyManager as KeyManager, auto_b64decode as auto_b64decode, is_base64 as is_base64
from privex.helpers.setuppy.bump import bump_version as bump_version, get_current_ver as get_current_ver
from privex.helpers.setuppy.commands import BumpCommand as BumpCommand, ExtrasCommand as ExtrasCommand
from privex.helpers.setuppy.common import extras_require as extras_require, reqs as reqs
from typing import Any

log: Any

class _Dummy:
    dummydata: Any = ...
    def __init__(self) -> None: ...
    def __getattr__(self, item: Any): ...
    def __setattr__(self, key: Any, value: Any): ...
    def __getitem__(self, item: Any): ...
    def __setitem__(self, key: Any, value: Any) -> None: ...

def _setup_logging(level: Any = ...): ...

name: str
VERSION: Any
