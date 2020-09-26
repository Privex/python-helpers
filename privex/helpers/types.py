from decimal import Decimal
from ipaddress import IPv4Address, IPv6Address, IPv4Network, IPv6Network
from typing import Union, Coroutine, Awaitable, Any, TypeVar, Callable

Number = Union[Decimal, int, float]
"""Shorter alias for ``Union[Decimal, int, float]``"""

AnyNum = NumberStr = Union[Decimal, int, float, str]
"""Shorter alias for ``Union[Decimal, int, float, str]``"""

VAL_FUNC_CORO = Union[Any, callable, Coroutine, Awaitable]
"""Type alias for callable's, coroutine's and awaitable's"""

IP_OR_STR = Union[str, IPv4Address, IPv6Address]
"""Shorthand union which accepts :class:`.IPv4Address`, :class:`.IPv6Address` or :class:`str`"""
NET_OR_STR = Union[str, IPv4Network, IPv6Network]
"""Shorthand union which accepts :class:`.IPv4Network`, :class:`.IPv6Network` or :class:`str`"""
IP_NET_OR_STR = Union[str, IPv4Address, IPv6Address, IPv4Network, IPv6Network]
"""Combined :attr:`.IP_OR_STR` + :attr:`.NET_OR_STR`"""

T = TypeVar('T')
"""Plain generic type variable for use in helper functions"""
K = TypeVar('K')
"""Plain generic type variable for use in helper functions"""
V = TypeVar('V')
"""Plain generic type variable for use in helper functions"""
C = TypeVar('C', type, Callable)
"""Generic type variable constrained to :class:`type` / :class:`typing.Callable` for use in helper functions"""
CL = TypeVar('CL', type, Callable)
"""Generic type variable constrained to :class:`type` / :class:`typing.Callable` for use in helper functions"""


USE_ORIG_VAR = type('UseOrigVar', (), {})
"""
A simple functionless type, used purely as a default parameter value meaning "fallback to the value from a certain
other parameter".

Primarily used in :func:`.empty_if` but can be used by any function/method, including use outside of privex-helpers.
"""

NO_RESULT = type('NoResult', (), {})
"""
Simple functionless type which means "no results were found or nothing matched this function's query".

Useful for returning a unique "nothing to return" value from functions where ``None`` / ``False`` might be considered as successful,
and exceptions aren't suitable::

    >>> from privex.helpers.types import NO_RESULT
    >>> def some_func(x: int):
    ...     if (x + 1) > 2: return True
    ...     elif (x + 1) < 2: return False
    ...     if x == 0 or (x + 1) == 0: return None
    ...     return NO_RESULT
    >>> res = some_func(-2)
    >>> res == NO_RESULT
    True

"""

STRBYTES = Union[bytes, str]
"""Shorter alias for ``Union[bytes, str]``"""

AUTO = AUTOMATIC = AUTO_DETECTED = type('AutoDetected', (), {})
"""
Another functionless type, intended to stand-in as the default value for a parameter, with the
meaning "automatically populate this parameter from another source" e.g. instance state attributes
"""

