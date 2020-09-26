"""
Various functions/classes which convert/parse objects from one type into another.

**Copyright**::

        +===================================================+
        |                 © 2019 Privex Inc.                |
        |               https://www.privex.io               |
        +===================================================+
        |                                                   |
        |        Originally Developed by Privex Inc.        |
        |        License: X11 / MIT                         |
        |                                                   |
        |        Core Developer(s):                         |
        |                                                   |
        |          (+)  Chris (@someguy123) [Privex]        |
        |          (+)  Kale (@kryogenic) [Privex]          |
        |                                                   |
        +===================================================+

    Copyright 2019     Privex Inc.   ( https://www.privex.io )


"""
import warnings
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Optional, Union, AnyStr

from privex.helpers.exceptions import ValidatorNotMatched
from privex.helpers.types import T
from privex.helpers.collections import Mocker

try:
    from privex.helpers.extras.attrs import AttribDictable
except ImportError as e:
    warnings.warn(f"Failed to import privex.helpers.extras.attrs.AttribDictable - falling back to placeholder type")
    AttribDictable = Mocker.make_mock_class('AttribDictable', instance=False)

try:
    from privex.helpers.collections import Dictable
except ImportError as e:
    warnings.warn(f"Failed to import privex.helpers.collections.Dictable - falling back to placeholder type")
    Dictable = Mocker.make_mock_class('Dictable', instance=False)

try:
    from privex.helpers.collections import DictDataClass
except ImportError as e:
    warnings.warn(f"Failed to import privex.helpers.collections.DictDataClass - falling back to placeholder type")
    DictDataClass = Mocker.make_mock_class('DictDataClass', instance=False)


try:
    import dataclasses
except ImportError as e:
    warnings.warn(f"Failed to import dataclasses - falling back to placeholder type")
    from privex.helpers.mockers import dataclasses

try:
    import attr
    from attr.exceptions import NotAnAttrsClassError
except ImportError as e:
    warnings.warn(f"Failed to import attr - falling back to placeholder type")
    from privex.helpers.mockers import attr


    class NotAnAttrsClassError(Exception):
        pass
    #
    # attr = Mocker(
    #     attributes=dict(
    #         s=mock_decorator,
    #         asdict=lambda obj, dict_factory=dict: dict_factory(obj),
    #         astuple=lambda obj, tuple_factory=tuple: tuple_factory(obj),
    #         validate=lambda obj: False
    #     )
    # )

from privex.helpers.common import empty, is_true, stringify
import logging

log = logging.getLogger(__name__)

MINUTE = 60
HOUR = MINUTE * 60
DAY = HOUR * 24
MONTH = DAY * 30
YEAR = DAY * 365
DECADE = YEAR * 10

SUPPORTED_DT_TYPES = Union[str, bytes, int, datetime, date, AnyStr]


def convert_datetime(d, if_empty=None, fail_empty=False, **kwargs) -> Optional[datetime]:
    """
    Convert the object ``d`` into a :class:`datetime.datetime` object.
    
    If ``d`` is a string or bytes, then it will be parsed using :func:`dateutil.parser.parse`
    
    If ``d`` is an int/float/Decimal, then it will be assumed to be a unix epoch timestamp.
    
    **Examples**::
        
        >>> convert_datetime("2019-01-01T00:00:00Z")          # ISO date/time
        datetime.datetime(2019, 1, 1, 0, 0, tzinfo=tzutc())
        
        >>> convert_datetime("01/JAN/2019 00:00:00.0000")     # Human date/time with month name
        datetime.datetime(2019, 1, 1, 0, 0, tzinfo=tzutc())
        
        >>> convert_datetime(1546300800)                      # Unix timestamp as integer
        datetime.datetime(2019, 1, 1, 0, 0, tzinfo=tzutc())
        
        >>> convert_datetime(1546300800000)                   # Unix timestamp (milliseconds) as integer
        datetime.datetime(2019, 1, 1, 0, 0, tzinfo=tzutc())
    
    :param d: Object to convert into a datetime
    :param if_empty: If ``d`` is empty / None, return this value
    :param bool fail_empty: (Def: ``False``) If this is True, then if ``d`` is empty, raises :class:`AttributeError`
    
    :key datetime.tzinfo tzinfo: (Default: :class:`dateutil.tz.tzutc`) If no timezone was detected by the parser,
                                 use this timezone. Set this to ``None`` to disable forcing timezone-aware dates.
    
    :raises AttributeError: When ``d`` is empty and ``fail_empty`` is set to True.
    :raises dateutil.parser.ParserError: When ``d`` could not be parsed into a date.
    :return datetime converted: The converted :class:`datetime.datetime` object.
    """
    from dateutil.tz import tzutc
    _tzinfo = kwargs.pop('tzinfo', tzutc())
    if isinstance(d, datetime):
        if d.tzinfo is None and _tzinfo is not None:
            d = d.replace(tzinfo=_tzinfo)
        return d
    
    # For datetime.date objects, we first convert them into a string, then we can parse them into a datetime + set tzinfo
    if isinstance(d, date):
        d = str(d)

    d = stringify(d) if isinstance(d, bytes) else d
    
    if isinstance(d, (int, float)):
        return convert_unixtime_datetime(d)
    
    if isinstance(d, str):
        from dateutil.parser import parse, ParserError
        try:
            t = parse(d)
            if t.tzinfo is None and _tzinfo is not None:
                t = t.replace(tzinfo=_tzinfo)
            return t
        except (ParserError, ValueError) as e:
            log.info("Failed to parse string. Attempting to parse as unix time")
            try:
                t = convert_unixtime_datetime(d)
                return t
            except (BaseException, Exception, ParserError) as _err:
                log.warning("Failed to parse unix time. Re-raising original parser error. Unixtime error was: %s %s",
                            type(_err), str(_err))
                raise e
        except ImportError as e:
            msg = "ERROR: Could not import 'parse' from 'dateutil.parser'. Please " \
                  f"make sure 'python-dateutil' is installed. Exception: {type(e)} - {str(e)}"
            
            log.exception(msg)
            raise ImportError(msg)
    if empty(d):
        if fail_empty: raise AttributeError("Error converting datetime. Parameter 'd' was empty!")
        return if_empty
    
    try:
        log.debug("Passed object is not a supported type. Object type: %s || object repr: %s", type(d), repr(d))
        log.debug("Calling convert_datetime with object casted to string: %s", str(d))
        _d = convert_datetime(str(d), fail_empty=True)
        d = _d
    except Exception as e:
        log.info("Converted passed object with str() to try and parse string version, but failed.")
        log.info("Exception thrown from convert_datetime(str(d)) was: %s %s", type(e), str(e))
        d = None   # By setting d to None, it will trigger the ValueError code below.
    
    if not isinstance(d, datetime):
        raise ValueError('Timestamp must be either a datetime object, or an ISO8601 string...')
    return d


parse_datetime = parse_date = convert_datetime


def convert_unixtime_datetime(d: Union[str, int, float, Decimal], if_empty=None, fail_empty=False) -> datetime:
    """Convert a unix timestamp into a :class:`datetime.datetime` object"""
    from dateutil.tz import tzutc
    if empty(d):
        if fail_empty: raise AttributeError("Error converting datetime. Parameter 'd' was empty!")
        return if_empty
    if isinstance(d, datetime):
        return d
    d = int(d)
    # If the timestamp is larger than NOW + 50 years in seconds, then it's probably milliseconds.
    if d > datetime.utcnow().timestamp() + (DECADE * 5):
        t = datetime.utcfromtimestamp(d // 1000)
    else:
        t = datetime.utcfromtimestamp(d)
    
    t = t.replace(tzinfo=tzutc())
    return t


parse_unixtime = parse_epoch = convert_epoch_datetime = convert_unixtime_datetime


def convert_bool_int(d, if_empty=0, fail_empty=False) -> int:
    """Convert a boolean ``d`` into an integer (``0`` for ``False``, ``1`` for ``True``)"""
    if type(d) is int: return 1 if d >= 1 else 0
    if empty(d):
        if fail_empty: raise AttributeError(f"Error converting '{d}' into a boolean. Parameter 'd' was empty!")
        return if_empty
    return 1 if is_true(d) else 0


def convert_int_bool(d, if_empty=False, fail_empty=False) -> bool:
    """Convert an integer ``d`` into a boolean (``0`` for ``False``, ``1`` for ``True``)"""
    if empty(d):
        if fail_empty: raise AttributeError(f"Error converting '{d}' into a boolean. Parameter 'd' was empty!")
        return if_empty
    return is_true(d)


DICT_TYPES = (dict, AttribDictable, Dictable, DictDataClass)

FLOAT_TYPES = (float, Decimal)
INTEGER_TYPES = (int,)
NUMBER_TYPES = FLOAT_TYPES + INTEGER_TYPES

LIST_TYPES = (list, set, tuple)

SIMPLE_TYPES = Union[list, dict, str, float, int]
SIMPLE_TYPES_TUPLE = (list, dict, str, float, int)


def _clean_attrs_matcher(ob):
    try:
        attr.validate(ob)
        return True
        # return clean_dict(attr.asdict(ob))
    except NotAnAttrsClassError:
        return False


_clean_floats = lambda ob, number_str=False, **kwargs: str(ob) if number_str else float(ob)
_clean_ints = lambda ob, number_str=False, **kwargs: str(ob) if number_str else int(ob)


def _clean_strs(ob, **kwargs):
    try:
        return stringify(ob)
    except Exception:
        return str(repr(ob))


def clean_obj(ob: Any, number_str: bool = False, fail=False, fallback: T = None) -> Union[SIMPLE_TYPES, T]:
    """
    Cleans an object by converting it / it's contents into basic, simple, JSON-compatible types.
    
    For example, :class:`.Decimal`'s will become :class:`.float`'s (or :class:`str`'s if ``number_str=True``),
    :class:`bytes` will be decoded into a :class:`str` if possible,
    :param Any ob:              An object to clean - making it safe for use with JSON/YAML etc.
    :param bool number_str:     (Default: ``False``) When set to ``True``, numbers will be converted to strings instead of int/float.
    :param bool fail:           (Default: ``False``) When set to ``True``, will raise the exception thrown by the fallback converter
                                if an error occurs, instead of returning ``fallback``
    :param Any fallback:        (Default: ``None``) The value to return if all matchers/converters fail to handle the object,
                                only used when ``fail=False`` (the default)
    
    :return SIMPLE_TYPES|T res: A clean version of the object for serialisation - or ``fallback`` if something went wrong.
    """
    # if isinstance(ob, FLOAT_TYPES): return str(ob) if number_str else float(ob)
    # if isinstance(ob, INTEGER_TYPES): return str(ob) if number_str else int(ob)
    # if isinstance(ob, NUMBER_TYPES): return str(ob) if number_str else float(ob)
    #
    # if isinstance(ob, (str, bytes)):
    #     try:
    #         return stringify(ob)
    #     except Exception:
    #         return str(repr(ob))
    #
    # if isinstance(ob, DICT_TYPES): return clean_dict(dict(ob))
    # if isinstance(ob, LIST_TYPES): return clean_list(list(ob))
    # if dataclasses.is_dataclass(ob): return dataclasses.asdict(ob)
    
    matched = False
    for matcher, convt in CLEAN_OBJ_VALIDATORS.items():
        try:
            log.debug("Checking matcher: %s - against object: %s", matcher, ob)
            if isinstance(matcher, (list, set)): matcher = tuple(matcher)
            if isinstance(matcher, tuple):
                if not isinstance(ob, matcher): continue
                matched = True
            if not matched and callable(matcher):
                if not matcher(ob): continue
                matched = True
            if not matched:
                if type(ob) is not type(matcher): continue
                matched = True
            log.debug("Matched %s has matched against object. Running converter. Object is: %s", matcher, ob)

            res = convt(ob, number_str=number_str)
            return res
        except ValidatorNotMatched:
            log.info("Matcher %s raised ValidatorNotMatched for object '%s' - continuing.", matcher, ob)
            continue
        except Exception as e:
            log.error("Matcher %s raised %s for object '%s' - continuing. Message was: %s", matcher, type(e), ob, str(e))
            continue
    
    log.warning(
        "All %s matchers failed to match against object '%s' - using fallback converter: %s",
        len(CLEAN_OBJ_VALIDATORS), ob, CLEAN_OBJ_FALLBACK
    )
    try:
        res = CLEAN_OBJ_FALLBACK(ob, number_str=number_str)
        return res
    except Exception as e:
        log.exception("Fallback matcher failed to convert object '%s' ...", ob)
        if fail:
            raise e
        return fallback


def clean_list(ld: list, **kwargs) -> list:
    ld = list(ld)
    nl = []
    for d in ld:
        try:
            x = clean_obj(d, **kwargs)
            nl.append(x)
            # if isinstance(d, (int, float, str)):
            #     nl.append(d)
            #     continue
            # if isinstance(d, LIST_TYPES):
            #     nl.append(clean_list(list(d)))
            #     continue
            # if isinstance(d, LIST_TYPES):
            #     nl.append(clean_list(list(d)))
            #     continue
            # if isinstance(d, DICT_TYPES):
            #     nl.append(clean_dict(dict(d)))
            #     continue
            # nl.append(str(d))
        except Exception:
            log.exception("Error while cleaning list item: %s", d)
    return nl


def clean_dict(data: dict, **kwargs) -> dict:
    data = dict(data)
    cleaned = {}
    for k, v in data.items():
        try:
            n = clean_obj(v, **kwargs)
            cleaned[k] = n
            # if isinstance(v, (dict, AttribDictable)):
            #     n = clean_dict(dict(v))
            #     cleaned[k] = n
            #     continue
            # if isinstance(v, list):
            #     n = clean_list(list(v))
            #     cleaned[k] = n
            #     continue
            # if isinstance(v, (int, float, str)):
            #     cleaned[k] = v
            #     continue
            # cleaned[k] = str(v)
        except Exception:
            log.exception("Error while cleaning dict item: %s = %s", k, v)
    
    return cleaned


CLEAN_OBJ_VALIDATORS = {
    FLOAT_TYPES:          _clean_floats,
    INTEGER_TYPES:        _clean_ints,
    NUMBER_TYPES:         _clean_floats,
    (str, bytes):         _clean_strs,
    DICT_TYPES:           clean_dict,
    LIST_TYPES:           clean_list,
    _clean_attrs_matcher:     lambda ob, **kwargs: clean_obj(attr.asdict(ob), **kwargs),
    dataclasses.is_dataclass: lambda ob, **kwargs: clean_obj(dataclasses.asdict(ob), **kwargs),
}

CLEAN_OBJ_FALLBACK = lambda ob, **kwargs: str(ob)

__all__ = [
    'convert_datetime', 'convert_unixtime_datetime', 'convert_bool_int', 'convert_int_bool',
    'parse_date', 'parse_datetime', 'parse_epoch', 'parse_unixtime', 'convert_epoch_datetime',
    'DICT_TYPES', 'FLOAT_TYPES', 'INTEGER_TYPES', 'NUMBER_TYPES', 'LIST_TYPES',
    'clean_obj', 'clean_list', 'clean_dict', 'CLEAN_OBJ_FALLBACK', 'CLEAN_OBJ_VALIDATORS',
    'MINUTE', 'HOUR', 'DAY', 'MONTH', 'YEAR', 'DECADE',
    
]

