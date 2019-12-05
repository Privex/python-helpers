from datetime import datetime

from dateutil.tz import tzutc

from privex import helpers
from tests.base import PrivexBaseCase

JAN_2019_1_MID = datetime(2019, 1, 1, 0, 0, 0, 0, tzinfo=tzutc())


class TestConvertDate(PrivexBaseCase):
    """Test cases for date/time converter functions/classes"""
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
