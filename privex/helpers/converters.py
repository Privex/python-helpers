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
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Union, AnyStr


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


__all__ = [
    'convert_datetime', 'convert_unixtime_datetime', 'convert_bool_int', 'convert_int_bool',
    'parse_date', 'parse_datetime', 'parse_epoch', 'parse_unixtime', 'convert_epoch_datetime',
    'MINUTE', 'HOUR', 'DAY', 'MONTH', 'YEAR', 'DECADE',
]

