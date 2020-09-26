import warnings

from privex.helpers.decorators import mock_decorator
from privex.helpers.collections import Mocker, dataclasses_mock

module = Mocker.make_mock_class('module')


def mkclass(name: str = 'module', instance: bool = True, **kwargs):
    return Mocker.make_mock_class(name, instance=instance, **kwargs)


def mkmodule(mod_name: str, attributes: dict = None, modules: dict = None, **kwargs):
    return Mocker.make_mock_module(mod_name, attributes, modules, **kwargs)


dataclasses = dataclasses_mock
dataclass, field = dataclasses.dataclass, dataclasses.field

pytest = mkmodule(
    'pytest',
    dict(
        skip=lambda msg, allow_module_level=True: warnings.warn(msg),
        mark=Mocker.make_mock_class(
            '_pytest.mark.structures.MarkGenerator',
            attributes=dict(skip=mock_decorator, skipif=mock_decorator())
        )
    )
)

attr = Mocker(
    attributes=dict(
        s=mock_decorator,
        asdict=lambda obj, dict_factory=dict: dict_factory(obj),
        astuple=lambda obj, tuple_factory=tuple: tuple_factory(obj),
        validate=lambda obj: False
    )
)


