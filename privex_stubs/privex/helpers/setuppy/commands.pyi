from distutils.cmd import Command
from privex.helpers import settings as settings
from privex.helpers.setuppy import EXTRAS_FOLDER as EXTRAS_FOLDER, extras as extras
from typing import Any, Optional

class BumpCommand(Command):
    description: str = ...
    user_options: Any = ...
    patch: Optional[int]
    minor: Optional[int]
    major: Optional[int]
    build: Optional[int]
    pre: Optional[int]
    token: Optional[str]
    dry: Optional[int]
    version_part: Optional[str]
    def initialize_options(self) -> None: ...
    def finalize_options(self) -> None: ...
    def run(self) -> None: ...

class ExtrasCommand(Command):
    user_options: Any = ...
    description: str = ...
    save: Any = ...
    extra: Any = ...
    list: Any = ...
    install: Any = ...
    def initialize_options(self) -> None: ...
    def finalize_options(self) -> None: ...
    def install_extras(self) -> None: ...
    def run(self): ...
    def save_list(self, extra_list: Any, out_file: Optional[Any] = ...) -> None: ...