from decimal import Decimal
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network
from typing import Any, Awaitable, Callable, Coroutine, TypeVar, Union

Number = Union[Decimal, int, float]
AnyNum = Union[Decimal, int, float, str]
NumberStr = Union[Decimal, int, float, str]
VAL_FUNC_CORO = Union[Any, callable, Coroutine, Awaitable]
IP_OR_STR = Union[str, IPv4Address, IPv6Address]
NET_OR_STR = Union[str, IPv4Network, IPv6Network]
IP_NET_OR_STR = Union[str, IPv4Address, IPv6Address, IPv4Network, IPv6Network]
T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')
C = TypeVar('C', type, Callable)
CL = TypeVar('CL', type, Callable)
USE_ORIG_VAR: Any
NO_RESULT: Any
STRBYTES = Union[bytes, str]
AUTO: Any
AUTOMATIC: Any
AUTO_DETECTED: Any
