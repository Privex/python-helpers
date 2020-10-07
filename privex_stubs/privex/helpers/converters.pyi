from datetime import date, datetime
from decimal import Decimal
from privex.helpers.types import T
from typing import Any, AnyStr, Optional, Union

class NotAnAttrsClassError(Exception): ...

MINUTE: int
HOUR: Any
DAY: Any
MONTH: Any
YEAR: Any
DECADE: Any
SUPPORTED_DT_TYPES = Union[str, bytes, int, datetime, date, AnyStr]

def convert_datetime(d: Any, if_empty: Any=..., fail_empty: Any=..., **kwargs: Any) -> Optional[datetime]: ...
parse_datetime = convert_datetime
parse_date = convert_datetime

def convert_unixtime_datetime(d: Union[str, int, float, Decimal], if_empty: Any=..., fail_empty: Any=...) -> datetime: ...
parse_unixtime = convert_unixtime_datetime
parse_epoch = convert_unixtime_datetime
convert_epoch_datetime = convert_unixtime_datetime

def convert_bool_int(d: Any, if_empty: Any=..., fail_empty: Any=...) -> int: ...
def convert_int_bool(d: Any, if_empty: Any=..., fail_empty: Any=...) -> bool: ...

DICT_TYPES: Any
FLOAT_TYPES: Any
INTEGER_TYPES: Any
NUMBER_TYPES: Any
LIST_TYPES: Any
SIMPLE_TYPES = Union[list, dict, str, float, int]

def clean_obj(ob: Any, number_str: bool=..., fail: Any=..., fallback: T=...) -> Union[SIMPLE_TYPES, T]: ...
def clean_list(ld: list, **kwargs: Any) -> list: ...
def clean_dict(data: dict, **kwargs: Any) -> dict: ...

CLEAN_OBJ_VALIDATORS: Any
CLEAN_OBJ_FALLBACK: Any
