"""
A thorough test case for :py:func:`.ip_to_rdns` - which converts IPv4/v6 addresses into ARPA reverse DNS domains.

**Copyright**::

        +===================================================+
        |                 © 2019 Privex Inc.                |
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

    Copyright 2019     Privex Inc.   ( https://www.privex.io )

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
from privex.helpers import ip_to_rdns, BoundaryException
from tests.base import PrivexBaseCase

VALID_V4_1 = '172.131.22.17'
VALID_V4_1_16BOUND = '131.172.in-addr.arpa'
VALID_V4_1_24BOUND = '22.131.172.in-addr.arpa'
VALID_V4_2 = '127.0.0.1'
VALID_V4_2_RDNS = '1.0.0.127.in-addr.arpa'
VALID_V6_1 = '2001:dead:beef::1'
VALID_V6_1_RDNS = '1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.f.e.e.b.d.a.e.d.1.0.0.2.ip6.arpa'
VALID_V6_1_16BOUND = '1.0.0.2.ip6.arpa'
VALID_V6_1_32BOUND = 'd.a.e.d.1.0.0.2.ip6.arpa'


class TestIPReverseDNS(PrivexBaseCase):
    """
    Unit testing for the reverse DNS functions in :py:mod:`privex.helpers.net`

    Covers:
     - positive resolution tests (generate standard rDNS domain from clean input)
     - positive boundary tests (confirm valid results with range of boundaries)
     - negative address tests (ensure errors thrown for invalid v4/v6 addresses)
     - negative boundary tests (ensure errors thrown for invalid v4/v6 rDNS boundaries)
    
    """

    ####
    # Positive tests (normal resolution)
    ####

    def test_v4_to_arpa(self):
        """Test generating rDNS for standard v4"""
        rdns = ip_to_rdns(VALID_V4_2)
        self.assertEqual(rdns, VALID_V4_2_RDNS)

    def test_v6_to_arpa(self):
        """Test generating rDNS for standard v6"""
        rdns = ip_to_rdns(VALID_V6_1)
        self.assertEqual(rdns, VALID_V6_1_RDNS)

    ####
    # Positive tests (boundaries)
    ####

    def test_v4_arpa_boundary_24bit(self):
        """Test generating 24-bit v4 boundary"""
        rdns = ip_to_rdns(VALID_V4_1, boundary=True, v4_boundary=24)
        self.assertEqual(rdns, VALID_V4_1_24BOUND)

    def test_v4_arpa_boundary_16bit(self):
        """Test generating 16-bit v4 boundary"""
        rdns = ip_to_rdns(VALID_V4_1, boundary=True, v4_boundary=16)
        self.assertEqual(rdns, VALID_V4_1_16BOUND)

    def test_v6_arpa_boundary_16bit(self):
        """Test generating 16-bit v6 boundary"""
        rdns = ip_to_rdns(VALID_V6_1, boundary=True, v6_boundary=16)
        self.assertEqual(rdns, VALID_V6_1_16BOUND)

    def test_v6_arpa_boundary_32bit(self):
        """Test generating 32-bit v6 boundary"""
        rdns = ip_to_rdns(VALID_V6_1, boundary=True, v6_boundary=32)
        self.assertEqual(rdns, VALID_V6_1_32BOUND)

    ####
    # Negative tests (invalid addresses)
    ####
    def test_v4_invalid(self):
        """Raise if IPv4 address has < 4 octets"""
        with self.assertRaises(ValueError):
            ip_to_rdns('127.0.0')

    def test_v4_invalid_2(self):
        """Raise if IPv4 address has octet out of range"""
        with self.assertRaises(ValueError):
            ip_to_rdns('127.0.0.373')

    def test_v6_invalid(self):
        """Raise if IPv6 address has invalid block formatting"""
        with self.assertRaises(ValueError):
            ip_to_rdns('2001::ff::a')

    def test_v6_invalid_2(self):
        """Raise if v6 address has invalid chars"""
        with self.assertRaises(ValueError):
            ip_to_rdns('2001::fh')

    ####
    # Negative tests (invalid boundaries)
    ####

    def test_v4_inv_boundary(self):
        """Raise if IPv4 boundary isn't divisable by 8"""
        with self.assertRaises(BoundaryException):
            ip_to_rdns(VALID_V4_2, boundary=True, v4_boundary=7)

    def test_v4_inv_boundary_2(self):
        """Raise if IPv4 boundary is too short"""
        with self.assertRaises(BoundaryException):
            ip_to_rdns(VALID_V4_2, boundary=True, v4_boundary=0)

    def test_v6_inv_boundary(self):
        """Raise if IPv6 boundary isn't dividable by 4"""
        with self.assertRaises(BoundaryException):
            ip_to_rdns(VALID_V6_1, boundary=True, v6_boundary=9)

    def test_v6_inv_boundary_2(self):
        """Raise if IPv6 boundary is too short"""
        with self.assertRaises(BoundaryException):
            ip_to_rdns(VALID_V6_1, boundary=True, v6_boundary=0)
