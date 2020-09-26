import warnings
import pytest
from datetime import datetime, date
from decimal import Decimal

from dateutil.tz import tzutc

from privex import helpers
from tests.base import PrivexBaseCase

JAN_2019_1_MID = datetime(2019, 1, 1, 0, 0, 0, 0, tzinfo=tzutc())
JAN_2019_1_MID_DATE = date(2019, 1, 1)


class TestConvertDate(PrivexBaseCase):
    """Test cases for date/time converter functions/classes"""
    
    ######
    # Test convert_datetime with strings containing full dates + times in ISO format + common formats
    ######
    def test_convert_date_str(self):
        """Test converting ISO date string into datetime"""
        self.assertEqual(helpers.convert_datetime("2019-01-01T00:00:00Z"), JAN_2019_1_MID)

    def test_convert_date_str_2(self):
        """Test converting no-timezone ISO date string into datetime"""
        self.assertEqual(helpers.convert_datetime("2019-01-01 00:00:00.0000"), JAN_2019_1_MID)

    def test_convert_date_str_3(self):
        """Test converting no-timezone human date string (spaces) into datetime"""
        self.assertEqual(helpers.convert_datetime("Jan 1 2019 00:00:00.0000"), JAN_2019_1_MID)

    def test_convert_date_str_4(self):
        """Test converting no-timezone human date string (slashes) into datetime"""
        self.assertEqual(helpers.convert_datetime("01/JAN/2019 00:00:00.0000"), JAN_2019_1_MID)

    def test_convert_date_bytes(self):
        """Test converting ISO date byte-string into datetime"""
        self.assertEqual(helpers.convert_datetime(b"2019-01-01T00:00:00Z"), JAN_2019_1_MID)

    ######
    # Test convert_datetime / convert_unixtime_datetime with epoch times in various formats (string, int, millisecond-epoch)
    ######
    def test_convert_date_int(self):
        """Test :func:`.convert_datetime` - converting integer unix time into datetime"""
        self.assertEqual(helpers.convert_datetime(1546300800), JAN_2019_1_MID)

    def test_convert_date_int_str(self):
        """Test :func:`.convert_datetime` - converting string unix time into datetime"""
        self.assertEqual(helpers.convert_datetime('1546300800'), JAN_2019_1_MID)
    
    def test_convert_date_int_ms(self):
        """Test :func:`.convert_datetime` - converting integer unix time (milliseconds) into datetime"""
        self.assertEqual(helpers.convert_datetime(1546300800 * 1000), JAN_2019_1_MID)

    def test_convert_unixtime_int(self):
        """Test :func:`.convert_unixtime_datetime` - converting integer unix time into datetime"""
        self.assertEqual(helpers.convert_unixtime_datetime(1546300800), JAN_2019_1_MID)

    def test_convert_unixtime_int_str(self):
        """Test :func:`.convert_unixtime_datetime` - converting string unix time into datetime"""
        self.assertEqual(helpers.convert_unixtime_datetime('1546300800'), JAN_2019_1_MID)

    def test_convert_unixtime_int_ms(self):
        """Test :func:`.convert_datetime` - converting integer unix time (milliseconds) into datetime"""
        self.assertEqual(helpers.convert_unixtime_datetime(1546300800 * 1000), JAN_2019_1_MID)

    ######
    # Test convert_datetime with :class:`.date` objects and string/bytes dates (no times)
    ######
    def test_convert_date_datetime(self):
        """Test converting :class:`.datetime` object into datetime"""
        self.assertEqual(helpers.convert_datetime(JAN_2019_1_MID), JAN_2019_1_MID)

    def test_convert_date_date(self):
        """Test converting :class:`.date` object into datetime"""
        self.assertEqual(helpers.convert_datetime(JAN_2019_1_MID_DATE), JAN_2019_1_MID)

    def test_convert_date_date_str(self):
        """Test converting :class:`.date` object's string value into datetime"""
        self.assertEqual(helpers.convert_datetime(str(JAN_2019_1_MID_DATE)), JAN_2019_1_MID)

    def test_convert_date_date_str_2(self):
        """Test converting a flat date string into datetime"""
        self.assertEqual(helpers.convert_datetime("2019-01-01"), JAN_2019_1_MID)

    def test_convert_date_date_str_3(self):
        """Test converting a human date string into datetime"""
        self.assertEqual(helpers.convert_datetime("Jan 1 2019"), JAN_2019_1_MID)

    def test_convert_date_date_str_4(self):
        """Test converting a human date string (slashes) into datetime"""
        self.assertEqual(helpers.convert_datetime("01/JAN/2019"), JAN_2019_1_MID)

    def test_convert_date_date_bytes(self):
        """Test converting :class:`.date` object's byte-string value into datetime"""
        self.assertEqual(helpers.convert_datetime(str(JAN_2019_1_MID_DATE).encode('utf-8')), JAN_2019_1_MID)


class TestConvertGeneral(PrivexBaseCase):
    """Test cases for general converter functions/classes"""
    def test_convert_bool_int_true(self):
        self.assertEqual(helpers.convert_bool_int(True), 1)

    def test_convert_bool_int_false(self):
        self.assertEqual(helpers.convert_bool_int(False), 0)

    def test_convert_bool_int_empty(self):
        self.assertEqual(helpers.convert_bool_int(None), 0)

    def test_convert_bool_int_empty_cust(self):
        self.assertEqual(helpers.convert_bool_int(None, if_empty="error"), "error")

    def test_convert_bool_int_empty_fail(self):
        with self.assertRaises(AttributeError):
            helpers.convert_bool_int(None, fail_empty=True)

    def test_convert_int_bool_true(self):
        self.assertTrue(helpers.convert_int_bool(1))

    def test_convert_int_bool_false(self):
        self.assertFalse(helpers.convert_int_bool(0))

    def test_convert_int_bool_empty(self):
        self.assertFalse(helpers.convert_int_bool(None))

    def test_convert_int_bool_empty_cust(self):
        self.assertEqual(helpers.convert_int_bool(None, if_empty="error"), "error")
    
    def test_convert_int_bool_empty_fail(self):
        with self.assertRaises(AttributeError):
            helpers.convert_int_bool(None, fail_empty=True)


try:
    from dataclasses import dataclass, field
    
    HAS_DATACLASSES = True
except ImportError:
    HAS_DATACLASSES = False
    warnings.warn(
        'WARNING: Could not import dataclasses module (Python older than 3.7?). '
        'For older python versions such as 3.6, you can run "pip3 install dataclasses" to install the dataclasses '
        'backport library, which emulates Py3.7+ dataclasses using older syntax.', category=ImportWarning
    )
    # To avoid a severe syntax error caused by the missing dataclass types, we generate a dummy dataclass and field class
    # so that type annotations such as Type[dataclass] don't break the test before it can be skipped.
    from privex.helpers.mockers import dataclass, field

try:
    import attr
    
    HAS_ATTRS = True
except ImportError:
    HAS_ATTRS = False
    warnings.warn(
        'WARNING: Could not import "attr" module. Please run "pip3 install attrs" to install the attrs module.', category=ImportWarning
    )
    # To avoid a severe syntax error caused by the missing dataclass types, we generate a dummy dataclass and field class
    # so that type annotations such as Type[dataclass] don't break the test before it can be skipped.
    from privex.helpers.mockers import attr

EXAMP_DEC = Decimal('1.2345')
EXAMP_DEC_STR = '1.2345'
EXAMP_DEC_FLOAT = 1.2345

EXAMP_INT, EXAMP_INT_STR = 123123, '123123'
EXAMP_FLOAT, EXAMP_FLOAT_STR = 543.12342, '543.12342'
EXAMP_STR = 'hello world'

EXAMP_LIST = [1, 2, Decimal('3.123'), ('a', 'b', b'c')]
EXAMP_LIST_CLEAN_NUM = [1, 2, 3.123, ['a', 'b', 'c']]
EXAMP_LIST_CLEAN_STR = ['1', '2', '3.123', ['a', 'b', 'c']]

EXAMP_DICT = dict(lorem='ipsum', dolor=3, world=list(EXAMP_LIST), example=Decimal(EXAMP_DEC))
EXAMP_DICT_CLEAN_STR = dict(lorem='ipsum', dolor='3', world=list(EXAMP_LIST_CLEAN_STR), example=EXAMP_DEC_STR)
EXAMP_DICT_CLEAN_NUM = dict(lorem='ipsum', dolor=3, world=list(EXAMP_LIST_CLEAN_NUM), example=EXAMP_DEC_FLOAT)


@attr.s
class ExampleAttrs:
    hello = attr.ib(default='world')
    lorem = attr.ib(factory=lambda: Decimal(EXAMP_DEC))
    ipsum = attr.ib(factory=lambda: list(EXAMP_LIST))
    dolor = attr.ib(factory=lambda: dict(EXAMP_DICT))


@dataclass
class ExampleDataClass:
    hello: str = 'world'
    lorem: Decimal = field(default_factory=lambda: Decimal(EXAMP_DEC))
    ipsum: list = field(default_factory=lambda: list(EXAMP_LIST))
    dolor: dict = field(default_factory=lambda: dict(EXAMP_DICT))


class TestCleanData(PrivexBaseCase):
    def test_clean_obj_decimal(self):
        self.assertEqual(helpers.clean_obj(EXAMP_DEC), EXAMP_DEC_FLOAT)
        self.assertEqual(helpers.clean_obj(EXAMP_DEC, number_str=True), EXAMP_DEC_STR)

    def test_clean_obj_float(self):
        self.assertEqual(helpers.clean_obj(EXAMP_FLOAT), EXAMP_FLOAT)
        self.assertEqual(helpers.clean_obj(EXAMP_FLOAT, number_str=True), EXAMP_FLOAT_STR)

    def test_clean_obj_int(self):
        self.assertEqual(helpers.clean_obj(EXAMP_INT), EXAMP_INT)
        self.assertEqual(helpers.clean_obj(EXAMP_INT, number_str=True), EXAMP_INT_STR)

    def test_clean_obj_list(self):
        self.assertEqual(helpers.clean_obj(EXAMP_LIST), EXAMP_LIST_CLEAN_NUM)
        self.assertEqual(helpers.clean_obj(EXAMP_LIST, number_str=True), EXAMP_LIST_CLEAN_STR)

    def test_clean_obj_dict(self):
        self.assertEqual(helpers.clean_obj(EXAMP_DICT), EXAMP_DICT_CLEAN_NUM)
        self.assertEqual(helpers.clean_obj(EXAMP_DICT, number_str=True), EXAMP_DICT_CLEAN_STR)

    @pytest.mark.skipif(HAS_ATTRS is False, reason='HAS_ATTRS is False (must install attrs: pip3 install attrs)')
    def test_clean_obj_attrs(self):
        o = ExampleAttrs()
        c = helpers.clean_obj(o)
        self.assertIsInstance(c, dict)
        self.assertEqual(c['hello'], 'world')
        self.assertEqual(c['lorem'], EXAMP_DEC_FLOAT)
        self.assertListEqual(c['ipsum'], EXAMP_LIST_CLEAN_NUM)
        self.assertDictEqual(c['dolor'], EXAMP_DICT_CLEAN_NUM)
        
        cs = helpers.clean_obj(o, True)
        self.assertIsInstance(cs, dict)
        self.assertEqual(cs['hello'], 'world')
        self.assertEqual(cs['lorem'], EXAMP_DEC_STR)
        self.assertListEqual(cs['ipsum'], EXAMP_LIST_CLEAN_STR)
        self.assertDictEqual(cs['dolor'], EXAMP_DICT_CLEAN_STR)

    @pytest.mark.skipif(HAS_DATACLASSES is False, reason='HAS_DATACLASSES is False (Python older than 3.7?)')
    def test_clean_obj_dataclass(self):
        o = ExampleDataClass()
        c = helpers.clean_obj(o)
        self.assertIsInstance(c, dict)
        self.assertEqual(c['hello'], 'world')
        self.assertEqual(c['lorem'], EXAMP_DEC_FLOAT)
        self.assertListEqual(c['ipsum'], EXAMP_LIST_CLEAN_NUM)
        self.assertDictEqual(c['dolor'], EXAMP_DICT_CLEAN_NUM)
        
        cs = helpers.clean_obj(o, True)
        self.assertIsInstance(cs, dict)
        self.assertEqual(cs['hello'], 'world')
        self.assertEqual(cs['lorem'], EXAMP_DEC_STR)
        self.assertListEqual(cs['ipsum'], EXAMP_LIST_CLEAN_STR)
        self.assertDictEqual(cs['dolor'], EXAMP_DICT_CLEAN_STR)
