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

EXSTRBYTES = Union[STRBYTES, Exception]
"""Alias for ``Union[STRBYTES, Exception]`` (string, bytes, or exception)"""

AUTO = AUTOMATIC = AUTO_DETECTED = type('AutoDetected', (), {})
"""
Another functionless type, intended to stand-in as the default value for a parameter, with the
meaning "automatically populate this parameter from another source" e.g. instance state attributes
"""

CONTINUE = type("Continue", (), {})
"""
A functionless type intended to represent the meaning "Continue with whatever loop or routine, no change needed".

You may also be interested in the polar opposite of this type: :class:`.STOP` ( aka :class:`.ABORT` ), which
represents the meaning "stop whatever loop/routine/function/etc. ASAP" instead of continuing.

As with a lot of the other types in this file, this type is intended to be a generic, user usable type. While it might
be used in some parts of :mod:`privex.helpers` - it does not have a "specific use/purpose", and can be used in
any of your Python applications in any function/method/class to represent whatever intention that you feel is
appropriate for this generic type, given it's name ``CONTINUE`` .

The main area where this would be useful, is in "middleware" functions, which may be ran in a chain, with each function
having the ability to impact the loop in some way:

 * Change the content/metadata being passed to each function in the chain, but don't stop the chain - pass it down to the next one.
 * Change the content/metadata, AND stop the chain to return that content/metadata immediately (e.g. inject a notice about
        a critical error to the content/metadata, and request the chain runner stops the chain and returns the content immediately).
 * Raise an exception, which may either stop the chain, be interpreted at the end of the chain, or simply be passed down to
   the next middleware function in the chain.
 * Analyze the content/metadata passed to itself, and decide that no changes are necessary to the data, nor have any errors occurred,
   thus simply requesting the chain runner CONTINUEs to the next middleware function without any alterations to the data.

This is intended for the last example in the above list, for cases where a function returning ``None``, might be interpreted
as "change the data to ``None``", or "something went wrong". Thus this type allows unambiguously representing the
desire for something to "continue", whether passed into a function using an argument, or returned from a function.
"""

STOP = ABORT = type("Stop", (), {})
"""
Similar to :class:`.CONTINUE` - a functionless type which represents the meaning "stop/abort this function/routine/loop/etc.".

This can be used as either an argument to a function (e.g. to ask that function to stop something), or can be
returned from a function (e.g. to ask the outer function running that function to stop something).

As with a lot of the other types in this file, this type is intended to be a generic, user usable type. While it might
be used in some parts of :mod:`privex.helpers` - it does not have a "specific use/purpose", and can be used in
any of your Python applications in any function/method/class to represent whatever intention that you feel is
appropriate for this generic type, given it's name ``STOP`` / ``ABORT`` .
"""
