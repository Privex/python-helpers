from typing import Any, Callable, Coroutine, Optional, Tuple, Union

class _AsyncGit:
    repo: Optional[str]
    default_version: str
    def __init__(self, repo: str=..., default_version: str=..., **kwargs: Any) -> None: ...
    async def git(self, *args: Any, repo: str=..., strip: Any=..., stderr: Any=...) -> Union[str, Tuple[str, str]]: ...
    async def init(self, *args: Any, repo: str=...) -> str: ...
    async def add(self, *args: Any, repo: str=...) -> str: ...
    async def branch(self, *args: Any, repo: str=...) -> str: ...
    async def commit(self, message: Optional[Union[str, bool]], *args: Any, repo: Optional[str]=...) -> str: ...
    async def checkout(self, branch: str, *args: Any, repo: str=..., new: bool=...) -> str: ...
    async def status(self, *args: Any, repo: str=..., concise: Any=...) -> str: ...
    async def tag(self, *args: Any, repo: str=...) -> str: ...
    async def get_current_commit(self, version: str=..., repo: str=...) -> str: ...
    async def get_current_branch(self, repo: str=...) -> str: ...
    async def get_current_tag(self, version: str=..., repo: str=...) -> str: ...
    async def log(self, *args: Any, repo: str=..., concise: Any=...) -> Any: ...
    def __getattr__(self, item: str) -> Union[Callable[[Any, Any, Any, Any, Any], Coroutine], callable, Any]: ...

AsyncGit: Any
Git = AsyncGit
get_current_commit: Any
get_current_branch: Any
get_current_tag: Any

# Names in __all__ with no definition:
#   _repo