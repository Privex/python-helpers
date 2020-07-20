"""
Test cases related to :py:mod:`privex.helpers.net` or generally network related functions such as :py:func:`.ping`
"""
import socket
import warnings

from privex.helpers import loop_run
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

    def _check_asn(self, asn, *expected_names):
        if not HAS_DNSPYTHON:
            return pytest.skip(f"Skipping asn_to_name tests as dnspython is not installed...")
        name = helpers.asn_to_name(asn)
        expected_names = list(expected_names)
        self.assertIn(name, expected_names, msg=f"asn_to_name({asn}) '{name}' in: {expected_names}")
    
    @pytest.mark.skipif(not HAS_DNSPYTHON, reason="test_asn_to_name_int requires package 'dnspython'")
    def test_asn_to_name_int(self):
        """Test Privex's ASN (as an int) 210083 resolves to 'PRIVEX, SE'"""
        self._check_asn(210083, 'PRIVEX, SE', 'PRIVEX INC, SE', 'Privex Inc, SE')

    @pytest.mark.skipif(not HAS_DNSPYTHON, reason="test_asn_to_name_str requires package 'dnspython'")
    def test_asn_to_name_str(self):
        """Test Cloudflare's ASN (as a str) '13335' resolves to 'CLOUDFLARENET - Cloudflare, Inc., US'"""
        self._check_asn('13335', 'CLOUDFLARENET - Cloudflare, Inc., US', 'CLOUDFLARENET, US')

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
    
    def test_get_rdns_privex_ns1_ip(self):
        """Test resolving IPv4 and IPv6 addresses into ns1.privex.io"""
        self.assertEqual(helpers.get_rdns('2a07:e00::100'), 'ns1.privex.io')
        self.assertEqual(helpers.get_rdns('185.130.44.3'), 'ns1.privex.io')

    def test_get_rdns_privex_ns1_host(self):
        """Test resolving rDNS for the domains ``steemseed-fin.privex.io`` and ``ns1.privex.io``"""
        self.assertEqual(helpers.get_rdns('ns1.privex.io'), 'ns1.privex.io')
        self.assertEqual(helpers.get_rdns('steemseed-fin.privex.io'), 'hiveseed-fin.privex.io')

    def test_get_rdns_invalid_domain(self):
        """Test :func:`.get_rdns` raises :class:`.InvalidHost` when given a non-existent domain"""
        with self.assertRaises(helpers.InvalidHost):
            helpers.get_rdns('non-existent.domain.example')

    def test_get_rdns_no_rdns_records(self):
        """Test :func:`.get_rdns` raises :class:`.ReverseDNSNotFound` when given a valid IP that has no rDNS records"""
        with self.assertRaises(helpers.ReverseDNSNotFound):
            helpers.get_rdns('192.168.5.1')
    
    def test_get_rdns_multi(self):
        """Test :func:`.get_rdns_multi` with 3x IPv4 addresses and 1x IPv6 address"""
        hosts = dict(helpers.get_rdns_multi('185.130.44.10', '8.8.4.4', '1.1.1.1', '2a07:e00::333'))
        self.assertEqual(len(hosts.keys()), 4)
        self.assertEqual(hosts['185.130.44.10'], 'web-se1.privex.io')
        self.assertEqual(hosts['8.8.4.4'], 'dns.google')
        self.assertEqual(hosts['1.1.1.1'], 'one.one.one.one')
        self.assertEqual(hosts['2a07:e00::333'], 'se.dns.privex.io')

    def test_get_rdns_multi_invalid(self):
        """Test :func:`.get_rdns_multi` with 2x IPv4 addresses + 2x IPv6 addresses with one of each having no records"""
        hosts = dict(helpers.get_rdns_multi('185.130.44.10', '192.168.5.1', 'fe80::5123', '2a07:e00::333'))
        self.assertEqual(len(hosts.keys()), 4)
        self.assertEqual(hosts['185.130.44.10'], 'web-se1.privex.io')
        self.assertIsNone(hosts['192.168.5.1'])
        self.assertIsNone(hosts['fe80::5123'])
        self.assertEqual(hosts['2a07:e00::333'], 'se.dns.privex.io')

    @pytest.mark.xfail()
    def test_check_host(self):
        self.assertTrue(helpers.check_host('hiveseed-se.privex.io', 2001))
        self.assertFalse(helpers.check_host('hiveseed-se.privex.io', 9991))

    @pytest.mark.xfail()
    def test_check_host_send(self):
        http_req = b"GET / HTTP/1.1\n\n"
        self.assertTrue(helpers.check_host('files.privex.io', 80, send=http_req))
        self.assertFalse(helpers.check_host('files.privex.io', 9991))

    @pytest.mark.xfail()
    def test_check_host_throw(self):
        with self.assertRaises(ConnectionRefusedError):
            helpers.check_host('files.privex.io', 9991, throw=True)


class TestNetResolveIP(PrivexBaseCase):
    """
    Test cases related to :func:`.resolve_ips`, :func:`.resolve_ip` and :func:`.resolve_ips_multi`
    """
    
    # --- privex.helpers.net.resolve_ips ---
    def test_resolve_ips_ipv4_addr(self):
        """Test :func:`.resolve_ips` returns the same IPv4 address passed to it"""
        ips = helpers.resolve_ips('185.130.44.5')
        self.assertEqual(len(ips), 1)
        self.assertEqual(ips[0], '185.130.44.5')

    def test_resolve_ips_ipv6_addr(self):
        """Test :func:`.resolve_ips` returns the same IPv6 address passed to it"""
        ips = helpers.resolve_ips('2a07:e00::333')
        self.assertEqual(len(ips), 1)
        self.assertEqual(ips[0], '2a07:e00::333')

    def test_resolve_ips_ipv4_addr_invalid(self):
        """Test :func:`.resolve_ips` raises :class:`.AttributeError` when ``version`` is v4 but an IPv6 address was passed"""
        with self.assertRaises(AttributeError):
            helpers.resolve_ips('2a07:e00::333', 'v4')

    def test_resolve_ips_ipv6_addr_invalid(self):
        """Test :func:`.resolve_ips` raises :class:`.AttributeError` when ``version`` is v6 but an IPv4 address was passed"""
        with self.assertRaises(AttributeError):
            helpers.resolve_ips('185.130.44.5', 'v6')

    def test_resolve_ips_hiveseed(self):
        """Test :func:`.resolve_ips` returns expected v4 + v6 for ``hiveseed-fin.privex.io``"""
        ips = helpers.resolve_ips('hiveseed-fin.privex.io')
        self.assertEqual(len(ips), 2)
        self.assertIn('2a01:4f9:2a:3d4::2', ips)
        self.assertIn('95.216.3.171', ips)

    def test_resolve_ips_hiveseed_v4(self):
        """Test :func:`.resolve_ips` returns only v4 for ``hiveseed-fin.privex.io`` when version is set to v4"""
        ips = helpers.resolve_ips('hiveseed-fin.privex.io', 'v4')
        self.assertEqual(len(ips), 1)
        self.assertEqual(ips[0], '95.216.3.171')

    def test_resolve_ips_hiveseed_v6(self):
        """Test :func:`.resolve_ips` returns only v6 for ``hiveseed-fin.privex.io`` when version is set to v6"""
        ips = helpers.resolve_ips('hiveseed-fin.privex.io', 'v6')
        self.assertEqual(len(ips), 1)
        self.assertEqual(ips[0], '2a01:4f9:2a:3d4::2')

    def test_resolve_ips_v4_convert_false(self):
        """Test :func:`.resolve_ips` returns an empty list for ``microsoft.com`` when v6 requested without v4_convert"""
        ips = helpers.resolve_ips('microsoft.com', 'v6', v4_convert=False)
        self.assertEqual(len(ips), 0)

    def test_resolve_ips_v4_convert(self):
        """Test :func:`.resolve_ips` returns IPv6-wrapped IPv4 addresses for ``microsoft.com`` when v4_convert is enabled + v6 version"""
        ips = helpers.resolve_ips('microsoft.com', 'v6', v4_convert=True)
        if ips is None or len(ips) == 0:
            return pytest.skip(
                f"Skipping test TestNetResolveIP.test_resolve_ips_v4_convert as v6-wrapped IPv4 addresses "
                f"aren't supported on this platform."
            )
        self.assertTrue(ips[0].startswith('::ffff:'))

    # --- privex.helpers.net.resolve_ip ---

    def test_resolve_ip_v4_convert(self):
        """Test :func:`.resolve_ip` returns an IPv6-wrapped IPv4 address for ``microsoft.com`` when v4_convert is enabled + v6 version"""
        ip = helpers.resolve_ip('microsoft.com', 'v6', v4_convert=True)
        if ip is None:
            return pytest.skip(
                f"Skipping test TestNetResolveIP.test_resolve_ip_v4_convert as v6-wrapped IPv4 addresses "
                f"aren't supported on this platform."
            )
        self.assertTrue(ip.startswith('::ffff:'))

    def test_resolve_ip_hiveseed(self):
        """Test :func:`.resolve_ip` returns expected either correct v4 or v6 for ``hiveseed-fin.privex.io``"""
        self.assertIn(helpers.resolve_ip('hiveseed-fin.privex.io'), ['95.216.3.171', '2a01:4f9:2a:3d4::2'])
        
    def test_resolve_ip_hiveseed_v4(self):
        """Test :func:`.resolve_ip` returns only v4 for ``hiveseed-fin.privex.io`` when version is v4"""
        self.assertEqual(helpers.resolve_ip('hiveseed-fin.privex.io', 'v4'), '95.216.3.171')

    def test_resolve_ip_hiveseed_v6(self):
        """Test :func:`.resolve_ip` returns only v6 for ``hiveseed-fin.privex.io`` when version is v6"""
        self.assertEqual(helpers.resolve_ip('hiveseed-fin.privex.io', 'v6'), '2a01:4f9:2a:3d4::2')

    # --- privex.helpers.net.resolve_ips_multi ---
    def test_resolve_ips_multi_any(self):
        """Test :func:`.resolve_ips_multi` with 2 domains and an IPv4 address"""
        ips = dict(helpers.resolve_ips_multi('hiveseed-fin.privex.io', 'privex.io', '8.8.4.4'))
        self.assertIn('2a01:4f9:2a:3d4::2', ips['hiveseed-fin.privex.io'])
        self.assertIn('95.216.3.171', ips['hiveseed-fin.privex.io'])
        
        self.assertIn('2a07:e00::abc', ips['privex.io'])
        self.assertIn('185.130.44.10', ips['privex.io'])
        
        self.assertIn('8.8.4.4', ips['8.8.4.4'])

    def test_resolve_ips_multi_v4(self):
        """Test :func:`.resolve_ips_multi` with 2 domains, an IPv4 address, and an IPv6 address with version ``v4``"""
        ips = dict(helpers.resolve_ips_multi('hiveseed-fin.privex.io', 'privex.io', '8.8.4.4', '2a07:e00::333', version='v4'))
        self.assertNotIn('2a01:4f9:2a:3d4::2', ips['hiveseed-fin.privex.io'])
        self.assertIn('95.216.3.171', ips['hiveseed-fin.privex.io'])
    
        self.assertNotIn('2a07:e00::abc', ips['privex.io'])
        self.assertIn('185.130.44.10', ips['privex.io'])
    
        self.assertIn('8.8.4.4', ips['8.8.4.4'])
        self.assertIsNone(ips['2a07:e00::333'])

    def test_resolve_ips_multi_v6(self):
        """Test :func:`.resolve_ips_multi` with 2 domains, an IPv4 address, and an IPv6 address with version ``v6``"""
        ips = dict(helpers.resolve_ips_multi('hiveseed-fin.privex.io', 'privex.io', '8.8.4.4', '2a07:e00::333', version='v6'))
        self.assertIn('2a01:4f9:2a:3d4::2', ips['hiveseed-fin.privex.io'])
        self.assertNotIn('95.216.3.171', ips['hiveseed-fin.privex.io'])
    
        self.assertIn('2a07:e00::abc', ips['privex.io'])
        self.assertNotIn('185.130.44.10', ips['privex.io'])

        self.assertIn('2a07:e00::333', ips['2a07:e00::333'])
        self.assertIsNone(ips['8.8.4.4'])


class TestAsyncResolveIP(PrivexBaseCase):
    # --- privex.helpers.net.resolve_ips ---
    def test_resolve_ips_ipv4_addr(self):
        """Test :func:`.resolve_ips` returns the same IPv4 address passed to it"""
        ips = loop_run(helpers.resolve_ips_async('185.130.44.5'))
        self.assertEqual(len(ips), 1)
        self.assertEqual(ips[0], '185.130.44.5')
    
    def test_resolve_ips_ipv6_addr(self):
        """Test :func:`.resolve_ips` returns the same IPv6 address passed to it"""
        ips = loop_run(helpers.resolve_ips_async('2a07:e00::333'))
        self.assertEqual(len(ips), 1)
        self.assertEqual(ips[0], '2a07:e00::333')
    
    def test_resolve_ips_ipv4_addr_invalid(self):
        """Test :func:`.resolve_ips` raises :class:`.AttributeError` when ``version`` is v4 but an IPv6 address was passed"""
        with self.assertRaises(AttributeError):
            loop_run(helpers.resolve_ips_async('2a07:e00::333', 'v4'))
    
    def test_resolve_ips_ipv6_addr_invalid(self):
        """Test :func:`.resolve_ips` raises :class:`.AttributeError` when ``version`` is v6 but an IPv4 address was passed"""
        with self.assertRaises(AttributeError):
            loop_run(helpers.resolve_ips_async('185.130.44.5', 'v6'))
    
    def test_resolve_ips_hiveseed(self):
        """Test :func:`.resolve_ips` returns expected v4 + v6 for ``hiveseed-fin.privex.io``"""
        ips = helpers.resolve_ips('hiveseed-fin.privex.io')
        self.assertEqual(len(ips), 2)
        self.assertIn('2a01:4f9:2a:3d4::2', ips)
        self.assertIn('95.216.3.171', ips)
    
    def test_resolve_ips_hiveseed_v4(self):
        """Test :func:`.resolve_ips` returns only v4 for ``hiveseed-fin.privex.io`` when version is set to v4"""
        ips = loop_run(helpers.resolve_ips_async('hiveseed-fin.privex.io', 'v4'))
        self.assertEqual(len(ips), 1)
        self.assertEqual(ips[0], '95.216.3.171')
    
    def test_resolve_ips_hiveseed_v6(self):
        """Test :func:`.resolve_ips` returns only v6 for ``hiveseed-fin.privex.io`` when version is set to v6"""
        ips = helpers.resolve_ips('hiveseed-fin.privex.io', 'v6')
        self.assertEqual(len(ips), 1)
        self.assertEqual(ips[0], '2a01:4f9:2a:3d4::2')
    
    def test_resolve_ips_v4_convert_false(self):
        """Test :func:`.resolve_ips` returns an empty list for ``microsoft.com`` when v6 requested without v4_convert"""
        ips = loop_run(helpers.resolve_ips_async('microsoft.com', 'v6', v4_convert=False))
        self.assertEqual(len(ips), 0)
    
    def test_resolve_ips_v4_convert(self):
        """Test :func:`.resolve_ips` returns IPv6-wrapped IPv4 addresses for ``microsoft.com`` when v4_convert is enabled + v6 version"""
        ips = loop_run(helpers.resolve_ips_async('microsoft.com', 'v6', v4_convert=True))
        if ips is None or len(ips) == 0:
            return pytest.skip(
                f"Skipping test TestNetResolveIP.test_resolve_ips_v4_convert as v6-wrapped IPv4 addresses "
                f"aren't supported on this platform."
            )
        self.assertTrue(ips[0].startswith('::ffff:'))
    
    # --- privex.helpers.net.resolve_ip ---
    
    def test_resolve_ip_v4_convert(self):
        """Test :func:`.resolve_ip` returns an IPv6-wrapped IPv4 address for ``microsoft.com`` when v4_convert is enabled + v6 version"""
        ip = loop_run(helpers.resolve_ip_async('microsoft.com', 'v6', v4_convert=True))
        if ip is None:
            return pytest.skip(
                f"Skipping test TestNetResolveIP.test_resolve_ip_v4_convert as v6-wrapped IPv4 addresses "
                f"aren't supported on this platform."
            )
        self.assertTrue(ip.startswith('::ffff:'))
    
    def test_resolve_ip_hiveseed(self):
        """Test :func:`.resolve_ip` returns expected either correct v4 or v6 for ``hiveseed-fin.privex.io``"""
        self.assertIn(loop_run(helpers.resolve_ip_async('hiveseed-fin.privex.io')), ['95.216.3.171', '2a01:4f9:2a:3d4::2'])
    
    def test_resolve_ip_hiveseed_v4(self):
        """Test :func:`.resolve_ip` returns only v4 for ``hiveseed-fin.privex.io`` when version is v4"""
        self.assertEqual(loop_run(helpers.resolve_ip_async('hiveseed-fin.privex.io', 'v4')), '95.216.3.171')
    
    def test_resolve_ip_hiveseed_v6(self):
        """Test :func:`.resolve_ip` returns only v6 for ``hiveseed-fin.privex.io`` when version is v6"""
        self.assertEqual(loop_run(helpers.resolve_ip_async('hiveseed-fin.privex.io', 'v6')), '2a01:4f9:2a:3d4::2')
    
    @staticmethod
    async def _resolve_multi_async(*addr, version='any', v4_convert=False):
        res = []
        async for x in helpers.resolve_ips_multi_async(*addr, version=version, v4_convert=v4_convert):
            res.append(x)
        return res

    def _resolve_multi(self, *addr, version='any', v4_convert=False):
        return loop_run(self._resolve_multi_async(*addr, version=version, v4_convert=v4_convert))

    # --- privex.helpers.net.resolve_ips_multi ---
    def test_resolve_ips_multi_any(self):
        """Test :func:`.resolve_ips_multi` with 2 domains and an IPv4 address"""
        ips = dict(self._resolve_multi('hiveseed-fin.privex.io', 'privex.io', '8.8.4.4'))
        self.assertIn('2a01:4f9:2a:3d4::2', ips['hiveseed-fin.privex.io'])
        self.assertIn('95.216.3.171', ips['hiveseed-fin.privex.io'])
        
        self.assertIn('2a07:e00::abc', ips['privex.io'])
        self.assertIn('185.130.44.10', ips['privex.io'])
        
        self.assertIn('8.8.4.4', ips['8.8.4.4'])
    
    def test_resolve_ips_multi_v4(self):
        """Test :func:`.resolve_ips_multi` with 2 domains, an IPv4 address, and an IPv6 address with version ``v4``"""
        ips = dict(self._resolve_multi('hiveseed-fin.privex.io', 'privex.io', '8.8.4.4', '2a07:e00::333', version='v4'))
        self.assertNotIn('2a01:4f9:2a:3d4::2', ips['hiveseed-fin.privex.io'])
        self.assertIn('95.216.3.171', ips['hiveseed-fin.privex.io'])
        
        self.assertNotIn('2a07:e00::abc', ips['privex.io'])
        self.assertIn('185.130.44.10', ips['privex.io'])
        
        self.assertIn('8.8.4.4', ips['8.8.4.4'])
        self.assertIsNone(ips['2a07:e00::333'])
    
    def test_resolve_ips_multi_v6(self):
        """Test :func:`.resolve_ips_multi` with 2 domains, an IPv4 address, and an IPv6 address with version ``v6``"""
        ips = dict(self._resolve_multi('hiveseed-fin.privex.io', 'privex.io', '8.8.4.4', '2a07:e00::333', version='v6'))
        self.assertIn('2a01:4f9:2a:3d4::2', ips['hiveseed-fin.privex.io'])
        self.assertNotIn('95.216.3.171', ips['hiveseed-fin.privex.io'])
        
        self.assertIn('2a07:e00::abc', ips['privex.io'])
        self.assertNotIn('185.130.44.10', ips['privex.io'])
        
        self.assertIn('2a07:e00::333', ips['2a07:e00::333'])
        self.assertIsNone(ips['8.8.4.4'])


class TestAsyncNet(PrivexBaseCase):
    def test_get_rdns_privex_ns1_ip(self):
        """Test resolving IPv4 and IPv6 addresses into ns1.privex.io"""
        self.assertEqual(loop_run(helpers.get_rdns_async('2a07:e00::100')), 'ns1.privex.io')
        self.assertEqual(loop_run(helpers.get_rdns_async('185.130.44.3')), 'ns1.privex.io')
    
    def test_get_rdns_privex_ns1_host(self):
        """Test resolving rDNS for the domains ``steemseed-fin.privex.io`` and ``ns1.privex.io``"""
        self.assertEqual(loop_run(helpers.get_rdns_async('ns1.privex.io')), 'ns1.privex.io')
        self.assertEqual(loop_run(helpers.get_rdns_async('steemseed-fin.privex.io')), 'hiveseed-fin.privex.io')
    
    def test_get_rdns_invalid_domain(self):
        """Test :func:`.get_rdns` raises :class:`.InvalidHost` when given a non-existent domain"""
        with self.assertRaises(helpers.InvalidHost):
            loop_run(helpers.get_rdns_async('non-existent.domain.example'))
    
    def test_get_rdns_no_rdns_records(self):
        """Test :func:`.get_rdns` raises :class:`.ReverseDNSNotFound` when given a valid IP that has no rDNS records"""
        with self.assertRaises(helpers.ReverseDNSNotFound):
            loop_run(helpers.get_rdns_async('192.168.5.1'))

    @pytest.mark.xfail()
    def test_check_host_async(self):
        self.assertTrue(loop_run(helpers.check_host_async('hiveseed-se.privex.io', 2001)))
        self.assertFalse(loop_run(helpers.check_host_async('hiveseed-se.privex.io', 9991)))

    @pytest.mark.xfail()
    def test_check_host_async_send(self):
        http_req = b"GET / HTTP/1.1\n\n"
        self.assertTrue(loop_run(helpers.check_host_async('files.privex.io', 80, send=http_req)))
        self.assertFalse(loop_run(helpers.check_host_async('files.privex.io', 9991)))

    @pytest.mark.xfail()
    def test_check_host_async_throw(self):
        with self.assertRaises(ConnectionRefusedError):
            loop_run(helpers.check_host_async('files.privex.io', 9991, throw=True))


