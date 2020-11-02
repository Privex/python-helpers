from privex.helpers.collections import Mocker as Mocker, dataclasses_mock as dataclasses_mock
from privex.helpers.decorators import mock_decorator as mock_decorator
from typing import Any

module: Any

def mkclass(name: str=..., instance: bool=..., **kwargs: Any) -> Any: ...
def mkmodule(mod_name: str, attributes: dict=..., modules: dict=..., **kwargs: Any) -> Any: ...
dataclasses = dataclasses_mock
dataclass: Any
field: Any
pytest: Any
attr: Any
