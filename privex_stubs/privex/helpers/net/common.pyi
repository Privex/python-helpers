from privex.helpers.types import AnyNum, IP_OR_STR
from typing import Any, List

def check_host(host: IP_OR_STR, port: AnyNum, version: Any=..., throw: Any=..., **kwargs: Any) -> bool: ...
async def check_host_async(host: IP_OR_STR, port: AnyNum, version: Any=..., throw: Any=..., **kwargs: Any) -> bool: ...
def check_host_http(host: IP_OR_STR, port: AnyNum=..., version: Any=..., throw: Any=..., **kwargs: Any) -> bool: ...
async def check_host_http_async(host: IP_OR_STR, port: AnyNum=..., version: Any=..., throw: Any=..., send: Any=..., **kwargs: Any) -> bool: ...
async def test_hosts_async(hosts: List[str]=..., ipver: str=..., timeout: AnyNum=..., **kwargs: Any) -> bool: ...
def test_hosts(hosts: List[str]=..., ipver: str=..., timeout: AnyNum=..., **kwargs: Any) -> bool: ...
def check_v4(hosts: List[str]=..., *args: Any, **kwargs: Any) -> bool: ...
def check_v6(hosts: List[str]=..., *args: Any, **kwargs: Any) -> bool: ...
async def check_v4_async(hosts: List[str]=..., *args: Any, **kwargs: Any) -> bool: ...
async def check_v6_async(hosts: List[str]=..., *args: Any, **kwargs: Any) -> bool: ...
