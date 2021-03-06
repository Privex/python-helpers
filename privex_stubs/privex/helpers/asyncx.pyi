import queue
import threading
from privex.helpers.types import STRBYTES, T
from typing import Any, Awaitable, Callable, Coroutine, List, Optional, Tuple, Type, Union

def coro_thread_func(func: callable, *t_args: Any, _output_queue: Optional[Union[queue.Queue, str]]=..., **t_kwargs: Any) -> Any: ...
def run_coro_thread_base(func: callable, *args: Any, _daemon_thread: Any=..., **kwargs: Any) -> threading.Thread: ...
def run_coro_thread(func: callable, *args: Any, **kwargs: Any) -> Any: ...
async def run_coro_thread_async(func: callable, *args: Any, _queue_timeout: Any=..., _queue_sleep: Any=..., **kwargs: Any) -> Any: ...
def run_sync(func: Any, *args: Any, **kwargs: Any): ...
def loop_run(coro: Union[Coroutine, Type[Coroutine], Callable], *args: Any, _loop: Any=..., **kwargs: Any) -> Any: ...
def async_sync(f: Any): ...
async def call_sys_async(proc: Any, *args: Any, write: STRBYTES=..., **kwargs: Any) -> Tuple[bytes, bytes]: ...
async def await_if_needed(func: Union[callable, Coroutine, Awaitable, Any], *args: Any, **kwargs: Any) -> Any: ...
def get_async_type(obj: Any) -> str: ...

AWAITABLE_BLACKLIST_FUNCS: List[str]
AWAITABLE_BLACKLIST_MODS: List[str]
AWAITABLE_BLACKLIST: List[str]

def is_async_context() -> bool: ...

class AwaitableMixin:
    def __getattribute__(self, item: Any): ...

def awaitable_class(cls: Type[T]) -> Type[T]: ...
def awaitable(func: Callable) -> Callable: ...

class aobject:
    __new__: Any = ...
    __init__: Any = ...
