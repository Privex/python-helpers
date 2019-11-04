"""
Test cases related to :py:mod:`privex.helpers.net` or generally network related functions such as :py:func:`.ping`
"""
import warnings
from tests import PrivexBaseCase
from privex import helpers

try:
    import pytest
    
    HAS_PYTEST = True
except ImportError:
    warnings.warn('WARNING: Could not import pytest. You should run "pip3 install pytest" to ensure tests work best')
    pytest = helpers.Mocker.make_mock_class('module')
    pytest.skip = lambda msg, allow_module_level=True: warnings.warn(msg)
    pytest.add_mock_module('mark')
    pytest.mark.skip, pytest.mark.skipif = helpers.mock_decorator, helpers.mock_decorator
    HAS_PYTEST = False

HAS_DNSPYTHON = helpers.plugin.HAS_DNSPYTHON


class TestNet(PrivexBaseCase):
    """Test cases related to :py:mod:`privex.helpers.net` or generally network related functions"""

    def test_ping(self):
        """Test success & failure cases for ping function with IPv4, as well as input validation"""
        try:
            with self.assertRaises(ValueError):
                helpers.ping('127.0.0.1', -1)
            with self.assertRaises(ValueError):
                helpers.ping('127.0.0.1', 0)
            with self.assertRaises(ValueError):
                helpers.ping('notavalidip', 1)
            self.assertTrue(helpers.ping('127.0.0.1', 3))
            self.assertFalse(helpers.ping('192.0.2.0', 3))
        except NotImplementedError as e:
            return pytest.skip(f"Skipping test TestGeneral.test_ping as platform is not supported: \"{str(e)}\"")
        except helpers.NetworkUnreachable as e:
            return pytest.skip(f"Skipping test TestGeneral.test_ping as network is unavailable: \"{str(e)}\"")

    def test_ping_v6(self):
        """Test success & failure cases for ping function with IPv6, as well as input validation"""
        try:
            with self.assertRaises(ValueError):
                helpers.ping('::1', -1)
            with self.assertRaises(ValueError):
                helpers.ping('::1', 0)
            with self.assertRaises(ValueError):
                helpers.ping('notavalidip', 1)
            self.assertTrue(helpers.ping('::1', 3))
            self.assertFalse(helpers.ping('fd06:dead::beef:ab12', 3))
        except NotImplementedError as e:
            return pytest.skip(f"Skipping test TestGeneral.test_ping_v6 as platform is not supported: \"{str(e)}\"")
        except helpers.NetworkUnreachable as e:
            return pytest.skip(f"Skipping test TestGeneral.test_ping_v6 as network is unavailable: \"{str(e)}\"")

    def _check_asn(self, asn, expected_name):
        if not HAS_DNSPYTHON:
            return pytest.skip(f"Skipping asn_to_name tests as dnspython is not installed...")
        name = helpers.asn_to_name(asn)
        self.assertEqual(name, expected_name, msg=f"asn_to_name({asn}) '{name}' == '{expected_name}'")
    
    @pytest.mark.skipif(not HAS_DNSPYTHON, reason="test_asn_to_name_int requires package 'dnspython'")
    def test_asn_to_name_int(self):
        """Test Privex's ASN (as an int) 210083 resolves to 'PRIVEX, SE'"""
        self._check_asn(210083, 'PRIVEX, SE')

    @pytest.mark.skipif(not HAS_DNSPYTHON, reason="test_asn_to_name_str requires package 'dnspython'")
    def test_asn_to_name_str(self):
        """Test Cloudflare's ASN (as a str) '13335' resolves to 'CLOUDFLARENET - Cloudflare, Inc., US'"""
        self._check_asn('13335', 'CLOUDFLARENET - Cloudflare, Inc., US')

    @pytest.mark.skipif(not HAS_DNSPYTHON, reason="test_asn_to_name_erroneous requires package 'dnspython'")
    def test_asn_to_name_erroneous(self):
        """Test asn_to_name returns 'Unknown ASN' when quiet, otherwise throws a KeyError for ASN 'nonexistent'"""
        self.assertEqual(helpers.asn_to_name('nonexistent'), 'Unknown ASN')
        with self.assertRaises(KeyError):
            helpers.asn_to_name('nonexistent', quiet=False)

    @pytest.mark.skipif(not HAS_DNSPYTHON, reason="test_asn_to_name_erroneous_2 requires package 'dnspython'")
    def test_asn_to_name_erroneous_2(self):
        """Test asn_to_name returns 'Unknown ASN' when quiet, otherwise throws KeyError for the ASN 999999999"""
        self.assertEqual(helpers.asn_to_name(999999999), 'Unknown ASN')
        with self.assertRaises(KeyError):
            helpers.asn_to_name(999999999, quiet=False)
