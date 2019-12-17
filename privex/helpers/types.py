from typing import Union, Coroutine, Awaitable, Any, TypeVar, Callable

VAL_FUNC_CORO = Union[Any, callable, Coroutine, Awaitable]
T = TypeVar('T')
"""Plain generic type variable for use in helper functions"""
K = TypeVar('K')
"""Plain generic type variable for use in helper functions"""
V = TypeVar('V')
"""Plain generic type variable for use in helper functions"""
C = TypeVar('C', type, callable, Callable)
"""Generic type variable constrained to :class:`type` / :class:`typing.Callable` for use in helper functions"""
CL = TypeVar('CL', type, callable, Callable)
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
