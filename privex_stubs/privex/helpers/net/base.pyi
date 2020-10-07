from privex.helpers import settings as settings
from privex.helpers.common import byteify as byteify, empty as empty
from privex.helpers.net.dns import resolve_ip as resolve_ip, resolve_ip_async as resolve_ip_async
from privex.helpers.net.util import generate_http_request as generate_http_request, get_ssl_context as get_ssl_context, ip_is_v6 as ip_is_v6, sock_ver as sock_ver
from privex.helpers.types import AnyNum as AnyNum, IP_OR_STR as IP_OR_STR
from typing import Any

log: Any

def check_host(host: IP_OR_STR, port: AnyNum, version: Any=..., throw: Any=..., **kwargs: Any) -> bool: ...
async def check_host_async(host: IP_OR_STR, port: AnyNum, version: Any=..., throw: Any=..., **kwargs: Any) -> bool: ...
