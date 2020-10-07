from privex.helpers import settings as settings
from privex.helpers.setuppy.commands import BumpCommand as BumpCommand
from typing import Any

log: Any

def version_replace(data: str, old_version: str, new_version: str) -> str: ...
def get_current_ver(data: str=...) -> Any: ...
default_replace_func = version_replace
default_current_ver = get_current_ver

def bump_version(part: str = ..., dry: bool = ..., **kwargs: Any): ...
