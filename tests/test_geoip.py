"""
Test cases for the :py:mod:`privex.helpers.geoip` module

**Copyright**::

        +===================================================+
        |                 © 2020 Privex Inc.                |
        |               https://www.privex.io               |
        +===================================================+
        |                                                   |
        |        Originally Developed by Privex Inc.        |
        |                                                   |
        |        Core Developer(s):                         |
        |                                                   |
        |          (+)  Chris (@someguy123) [Privex]        |
        |          (+)  Kale (@kryogenic) [Privex]          |
        |                                                   |
        +===================================================+

    Copyright 2020     Privex Inc.   ( https://www.privex.io )

    Permission is hereby granted, free of charge, to any person obtaining a copy of
    this software and associated documentation files (the "Software"), to deal in
    the Software without restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
    Software, and to permit persons to whom the Software is furnished to do so,
    subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
    INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
    PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
    OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
    SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


"""
import base64
import warnings

from privex.helpers.collections import DictObject

from tests.base import PrivexBaseCase

from privex.helpers import Mocker, stringify, plugin, GeoIPDatabaseNotFound, GeoIPAddressNotFound

MOD_LOAD_ERR = f"WARNING: `geoip2` package not installed (or other error loading privex.helpers.geoip). " \
               f"Skipping test case {__name__}."
GEOIP_DB_ERR = f"WARNING: One or more essential GeoIP2 databases are missing (need city + asn). Skipping test case {__name__}."

try:
    import pytest
    
    HAS_PYTEST = True
except ImportError:
    warnings.warn('WARNING: Could not import pytest. You should run "pip3 install pytest" to ensure tests work best')
    pytest = Mocker.make_mock_class('module')
    pytest.skip = lambda msg, allow_module_level=True: warnings.warn(msg)
    HAS_PYTEST = False

if plugin.HAS_GEOIP:
    try:
        # noinspection PyUnresolvedReferences
        from privex.helpers import geoip

        plugin.get_geoip_db('city')
        plugin.get_geoip_db('asn')
    
    except GeoIPDatabaseNotFound as e:
        pytest.skip(GEOIP_DB_ERR + f" Exception was: {type(e)} {str(e)}", allow_module_level=True)
        if not HAS_PYTEST: raise ImportError(f"(GeoIPDatabaseNotFound in {__file__}) {GEOIP_DB_ERR} Exception was: {type(e)} {str(e)}")
    except ImportError:
        pytest.skip(MOD_LOAD_ERR, allow_module_level=True)
        if not HAS_PYTEST: raise ImportError(f"(ImportError in {__file__}) {MOD_LOAD_ERR}")
else:
    pytest.skip(MOD_LOAD_ERR, allow_module_level=True)
    if not HAS_PYTEST: raise ImportError("(plugin.HAS_GEOIP = False) " + MOD_LOAD_ERR)


class TestGeoIP(PrivexBaseCase):
    AS_NAMES = DictObject(
        privex=['Privex', 'Privex Inc.', 'Privex Inc', 'Privex SE', 'Privex Sweden', 'PRIVEX', 'PRIVEX INC', 'PRIVEX INC.'],
        hetzner=['Hetzner', 'Hetzner Online GmbH.', 'Hetzner Online GmbH', 'Hetzner Online']
    )
    
    GEO_ATTRS = [
        'country', 'country_code', 'city', 'postcode', 'as_number', 'as_name',
        'ip_address', 'network', 'long', 'lat', 'geoasn_data','geocity_data'
    ]
    
    @classmethod
    def tearDownClass(cls) -> None:
        super(PrivexBaseCase, cls).tearDownClass()
        geoip.cleanup()
    
    def test_geoip_init_cleanup(self):
        """
        Test that :func:`.close_geoip` and :func:`.geoip.cleanup` correctly remove GeoIP instances from the thread store, plus
        test that :func:`.get_geoip` correctly re-creates the thread store object after cleanup.
        """
        n, a = 'geoip_city', 'geoip_asn'
        # Initialise and get a GeoIP2 city read instance, and verify it exists in the thread store
        plugin.get_geoip('city')
        self.assertIsNotNone(plugin._get_threadstore(n))
        # Close and remove the GeoIP2 city instance using close_geoip and confirm it's not in the thread store.
        plugin.close_geoip('city')
        self.assertIsNone(plugin._get_threadstore(n))

        # Initialise and get both a GeoIP2 city + asn read instance, and verify they both exist in the thread store
        plugin.get_geoip('city')
        plugin.get_geoip('asn')
        self.assertIsNotNone(plugin._get_threadstore(n))
        self.assertIsNotNone(plugin._get_threadstore(a))
        
        # Close+remove all GeoIP2 instances using geoip.cleanup, and confirm both City + ASN are not present in the thread store.
        geoip.cleanup()
        self.assertIsNone(plugin._get_threadstore(n))
        self.assertIsNone(plugin._get_threadstore(a))

    def test_geoip_v4_privex1(self):
        """Test ``185.130.44.5`` resolves correctly using :meth:`.geoip.geolocate_ip`"""
        data = geoip.geolocate_ip('185.130.44.5')
        self.assertIn(data.as_name, self.AS_NAMES.privex)
        self.assertEqual(data.as_number, 210083)
        self.assertEqual(data.country, 'Sweden')
        self.assertEqual(data.country_code, 'SE')
        self.assertEqual(data.city, 'Stockholm')
        self.assertIn(str(data.network), ['185.130.44.0/24', '185.130.44.0/23', '185.130.44.0/22'])

    def test_geoip_v6_privex1(self):
        """Test ``2a07:e00::333`` resolves correctly using :meth:`.geoip.geolocate_ip`"""
        data = geoip.geolocate_ip('2a07:e00::333')
        self.assertIn(data.as_name, self.AS_NAMES.privex)
        self.assertEqual(data.as_number, 210083)
        self.assertEqual(data.country, 'Sweden')
        self.assertEqual(data.country_code, 'SE')
        self.assertEqual(data.city, 'Stockholm')
        # GeoIP's network value isn't reliable, so we simple check it starts with 2a07:e00::/
        self.assertIn('2a07:e00::/', str(data.network))
    
    def test_geoip_v4_hetzner1(self):
        """Test ``95.216.3.171`` resolves correctly using :meth:`.geoip.geolocate_ip`"""
        data = geoip.geolocate_ip('95.216.3.171')
        self.assertIn(data.as_name, self.AS_NAMES.hetzner)
        self.assertEqual(data.as_number, 24940)
        self.assertEqual(data.country, 'Finland')
        self.assertEqual(data.country_code, 'FI')
        self.assertIn(data.city, [None, 'Helsinki'])
        # GeoIP's network value isn't reliable, so we simply check the first 5 characters, and confirm there's a / present
        self.assertTrue(str(data.network).startswith('95.21'))
        self.assertIn('/', str(data.network))

    def test_geoip_v6_hetzner1(self):
        """Test ``2a01:4f9:2a:3d4::2`` resolves correctly using :meth:`.geoip.geolocate_ip`"""
        data = geoip.geolocate_ip('2a01:4f9:2a:3d4::2')
        self.assertIn(data.as_name, self.AS_NAMES.hetzner)
        self.assertEqual(data.as_number, 24940)
        self.assertIn(data.geoasn_data.autonomous_system_organization, self.AS_NAMES.hetzner)
        self.assertEqual(data.geoasn_data.autonomous_system_number, 24940)
        # Hetzner's IPv6 range is quirky with GeoIP2. As of 2020-05-17, it's incorrectly reporting Germany for a Finnish IPv6 address.
        # To avoid the test breaking in the future, we'll allow either Finland or Germany.
        self.assertIn(data.country, ['Finland', 'Germany'])
        self.assertIn(data.country_code, ['FI', 'DE'])
        # Again, the IPv6 network that this address belongs to can fluctuate - so we just make sure it starts with 2a01:4f
        self.assertTrue(str(data.network).startswith('2a01:4f'))
        self.assertIn('/', str(data.network))

    def test_geoip_v4_local(self):
        with self.assertRaises(GeoIPAddressNotFound):
            geoip.geolocate_ip('192.168.5.1')

    def test_geoip_v6_local(self):
        with self.assertRaises(GeoIPAddressNotFound):
            geoip.geolocate_ip('fe80::1')

    def test_geoip_v4_local_no_throw(self):
        data = geoip.geolocate_ip('192.168.5.1', throw=False)
        self.assertIsNone(data)

    def test_geoip_v6_local_no_throw(self):
        data = geoip.geolocate_ip('fe80::1', throw=False)
        self.assertIsNone(data)

    def test_geoip_multi(self):
        data = dict(geoip.geolocate_ips('185.130.44.5', '95.216.3.171', '2a01:4f9:2a:3d4::2', '2a07:e00::333'))
        
        self.assertIn(data['185.130.44.5'].as_name, self.AS_NAMES.privex)
        self.assertIn(data['95.216.3.171'].as_name, self.AS_NAMES.hetzner)
        self.assertIn(data['2a07:e00::333'].as_name, self.AS_NAMES.privex)
        self.assertIn(data['2a01:4f9:2a:3d4::2'].as_name, self.AS_NAMES.hetzner)

        self.assertEqual(data['185.130.44.5'].country, 'Sweden')
        self.assertEqual(data['95.216.3.171'].country, 'Finland')
        self.assertEqual(data['2a07:e00::333'].country, 'Sweden')
        self.assertIn(data['2a01:4f9:2a:3d4::2'].country, ['Finland', 'Germany'])
