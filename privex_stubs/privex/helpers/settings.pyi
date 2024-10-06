from datetime import datetime as datetime
from os.path import basename as basename
from typing import Any, Optional

BASE_DIR: Any
VERSION_FILE: Any
EXTRAS_FOLDER: str

def _is_true(v: Any): ...
def _env_bool(v: Any, d: Any) -> bool: ...
def _env_int(v: Any, d: Any) -> int: ...

DEFAULT_CACHE_TIMEOUT: Any
DEFAULT_CACHE_ADAPTER: Any
DEFAULT_ASYNC_CACHE_ADAPTER: Any
REDIS_HOST: Any
REDIS_PORT: Any
REDIS_DB: Any
MEMCACHED_HOST: Any
MEMCACHED_PORT: Any
search_geoip: Any
GEOIP_DIR: Any
GEOASN_NAME: Any
GEOCITY_NAME: Any
GEOCOUNTRY_NAME: Any
GEOASN_DETECTED: Any
GEOCITY_DETECTED: Any
GEOCOUNTRY_DETECTED: Any
GEOCITY: Any
GEOASN: Any
GEOCOUNTRY: Any
TERMBIN_HOST: Any
TERMBIN_PORT: Any
THREAD_DEBUG: bool
CHECK_CONNECTIVITY: bool
HAS_WORKING_V4: Optional[bool]
HAS_WORKING_V6: Optional[bool]
SSL_VERIFY_CERT: bool
SSL_VERIFY_HOSTNAME: bool
DEFAULT_USER_AGENT: Any
NET_CHECK_TIMEOUT: int
NET_CHECK_HOST_COUNT: int
NET_CHECK_HOST_COUNT_TRY: int
V4_TEST_HOSTS: Any
V6_TEST_HOSTS: Any
DEFAULT_SOCKET_TIMEOUT: int
DEFAULT_READ_TIMEOUT: Any
DEFAULT_WRITE_TIMEOUT: Any

def _bdir_plus_fname(f: Any, sep: str = ..., rem_ext: bool = ...): ...

SQLITE_APP_DB_NAME: Any
SQLITE_APP_DB_FOLDER: Any
