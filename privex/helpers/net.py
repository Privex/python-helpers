"""
Network related helper code

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
import logging
import platform
import subprocess
from privex.helpers.exceptions import BoundaryException, NetworkUnreachable
from privex.helpers import plugin
from ipaddress import ip_address, IPv4Address, IPv6Address
from typing import Union

log = logging.getLogger(__name__)

__all__ = [
    'ip_to_rdns', '_check_boundaries', 'ip4_to_rdns', 'ip6_to_rdns', 'ip_is_v4', 'ip_is_v6',
    'ping', 'BoundaryException', 'NetworkUnreachable'
]

try:
    from dns.resolver import Resolver, NoAnswer, NXDOMAIN
    
    def asn_to_name(as_number: Union[int, str], quiet: bool = True) -> str:
        """
        Look up an integer Autonomous System Number and return the human readable
        name of the organization.

        Usage:

        >>> asn_to_name(210083)
        'PRIVEX, SE'
        >>> asn_to_name('13335')
        'CLOUDFLARENET - Cloudflare, Inc., US'

        This helper function requires ``dnspython>=1.16.0``, it will not be visible unless
        you install the dnspython package in your virtualenv, or systemwide::
        
            pip3 install dnspython
        

        :param int/str as_number: The AS number as a string or integer, e.g. 210083 or '210083'
        :param bool quiet:        (default True) If True, returns 'Unknown ASN' if a lookup fails. 
                                  If False, raises a KeyError if no results are found.
        :raises KeyError:         Raised when a lookup returns no results, and ``quiet`` is set to False.
        :return str as_name:      The name and country code of the ASN, e.g. 'PRIVEX, SE'
        """
        
        try:
            res = Resolver().query('AS{}.asn.cymru.com'.format(as_number), "TXT")
            if len(res) > 0:
                # res[0] is formatted like such: "15169 | US | arin | 2000-03-30 | GOOGLE - Google LLC, US" with
                # literal quotes. we need to strip them, split by pipe, extract the last element, then strip spaces.
                asname = str(res[0]).strip('"').split('|')[-1:][0].strip()
                return str(asname)
            raise NoAnswer('privex.helpers.net.asn_to_name returned no results.')
        except (NoAnswer, NXDOMAIN):
            if quiet:
                return 'Unknown ASN'
            raise KeyError('ASN {} was not found, or server did not respond.'.format(as_number))
    
    __all__ += ['asn_to_name']
    plugin.HAS_DNSPYTHON = True
    
except ImportError:
    log.debug('privex.helpers.net failed to import "dns.resolver" (pypi package "dnspython"), skipping some helpers')
    pass


def ip_to_rdns(ip: str, boundary: bool = False, v6_boundary: int = 32, v4_boundary: int = 24) -> str:
    """
    Converts an IPv4 or IPv6 address into an in-addr domain

    Default boundaries: IPv4 - 24 bits, IPv6 - 32 bits

    **Examples:**

        >>> ip_to_rdns('127.0.0.1') # IPv4 to arpa format
            '1.0.0.127.in-addr.arpa'

        >>> ip_to_rdns('2001:dead:beef::1') # IPv6 to arpa format
            '1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.f.e.e.b.d.a.e.d.1.0.0.2.ip6.arpa'

        >>> ip_to_rdns('2001:dead:beef::1', boundary=True) # IPv6 32-bit boundary to arpa
            'd.a.e.d.1.0.0.2.ip6.arpa'

    :param str ip: IPv4 or IPv6 address
    :param bool boundary: If True, return the base (boundary) domain to place NS/SOA
    :param int v6_boundary: Bits for IPv6 boundary. Must be dividable by 4 bits (nibble)
    :param int v4_boundary: Bits for IPv4 boundary. Must be dividable by 8 bits (octet)

    :raises ValueError: When IP address is invalid
    :raises BoundaryException: When boundary for IPv4/v6 is invalid

    :return str rdns_domain: in-addr.arpa format, e.g. ``0.0.127.in-addr.arpa``
    :return str rdns_domain: ip6.arpa format, e.g. ``0.8.e.f.ip6.arpa``
    """
    v6_boundary = int(v6_boundary)
    v4_boundary = int(v4_boundary)
    # sanity check
    if boundary:
        # will raise a BoundaryException if v4/v6 is invalid
        _check_boundaries(v4_boundary, v6_boundary)
    # ip_address helps us detect the type, and uncompress v6 addresses
    ip_obj = ip_address(ip)

    # IPv6 Addresses use nibbles and ip6.arpa
    ip_type = type(ip_obj)
    if ip_type == IPv6Address:
        return ip6_to_rdns(ip_obj, v6_boundary, boundary)
    elif ip_type == IPv4Address:
        return ip4_to_rdns(ip_obj, v4_boundary, boundary)
    else:
        raise ValueError("Not a v4 nor v6 address...? Type was: {}".format(ip_type))


def _check_boundaries(v4_boundary: int, v6_boundary: int):
    """
    Boundary validator for :py:func:`.ip_to_rdns`

    :raises BoundaryException: When either the v4 or v6 boundary is invalid
    """
    if v6_boundary > 128 or v6_boundary < 4:
        raise BoundaryException('v6_boundary must be at least 4 bits, and less than 128 (was: {})'.format(v6_boundary))
    if v4_boundary > 32 or v4_boundary < 8:
        raise BoundaryException('v4_boundary must be at least 8 bits, and less than 32 (was: {})'.format(v4_boundary))
    if v6_boundary % 4 != 0:
        raise BoundaryException('v6_boundary not dividable by 4 bits (was: {})'.format(v6_boundary))
    if v4_boundary % 8 != 0:
        raise BoundaryException('v4_boundary not dividable by 8 bits (was: {})'.format(v4_boundary))


def ip4_to_rdns(ip_obj: IPv4Address, v4_boundary: int = 24, boundary: bool = False) -> str:
    """
    Internal function for getting the rDNS domain for a given v4 address. Use :py:func:`.ip_to_rdns` unless 
    you have a specific need for this one.

    :param IPv4Address ip_obj: An IPv4 ip_address() object to get the rDNS domain for
    :param int v4_boundary: 8-32 bits. If ``boundary`` is True, return the base rDNS domain at this boundary.
    :param bool boundary: If True, cut off the rDNS domain to the given ``v4_boundary``
    :return str rdns_domain: in-addr.arpa format, e.g. ``0.0.127.in-addr.arpa``
    """
    addr = ip_obj.reverse_pointer
    if boundary:
        exploded = ip_obj.exploded
        # each octet of ipv4 is 8 bits. only take the first x octets for boundary
        octets = int(v4_boundary / 8)
        addr_bounded = exploded.split('.')[:octets][::-1]  # array of octets, trim octets, and reverse the array
        addr_joined = '.'.join(addr_bounded)  # glue the array back together
        addr = addr_joined + '.in-addr.arpa'  # and finally add the arpa subdomain
    return addr


def ip6_to_rdns(ip_obj: IPv6Address, v6_boundary: int = 32, boundary: bool = False) -> str:
    """
    Internal function for getting the rDNS domain for a given v6 address. Use :py:func:`.ip_to_rdns` unless 
    you have a specific need for this one.

    :param IPv6Address ip_obj: An IPv4 ip_address() object to get the rDNS domain for
    :param int v6_boundary: 8-128 bits. If ``boundary`` is True, return the base rDNS domain at this boundary.
    :param bool boundary: If True, cut off the rDNS domain to the given ``v6_boundary``
    :return str rdns_domain: ip6.arpa format, e.g. ``0.8.e.f.ip6.arpa``
    """
    # first uncompress the IP
    expanded = ip_obj.exploded
    # Remove the colons
    # if we're not doing boundary, this will be used later, otherwise it'll just be replaced anyway
    addr = expanded.replace(':', '')
    if boundary:
        # if we need a boundary address, use v6_boundary to strip off the excess characters
        del_chars = int(v6_boundary / 4)        # 4 bits = 1 character (nibble)
        addr = addr[:del_chars]                 # now we have the boundary portion, e.g. 200100fa
    addr_reverse = addr[::-1]                   # reverse the address, e.g. af001002
    addr_joined = '.'.join(list(addr_reverse))  # join together with dots, e.g. a.f.0.0.1.0.0.2
    return addr_joined + '.ip6.arpa'            # and finally, return the completed string, a.f.0.0.1.0.0.2.ip6.arpa


def ip_is_v4(ip: str) -> bool:
    """
    Determines whether an IP address is IPv4 or not

    :param str ip: An IP address as a string, e.g. 192.168.1.1
    :raises ValueError: When the given IP address ``ip`` is invalid
    :return bool: True if IPv6, False if not (i.e. probably IPv4)
    """
    return type(ip_address(ip)) == IPv4Address


def ip_is_v6(ip: str) -> bool:
    """
    Determines whether an IP address is IPv6 or not

    :param str ip: An IP address as a string, e.g. 192.168.1.1
    :raises ValueError: When the given IP address ``ip`` is invalid
    :return bool: True if IPv6, False if not (i.e. probably IPv4)
    """
    return type(ip_address(ip)) == IPv6Address


def ping(ip: str, timeout: int = 30) -> bool:
    """
    Sends a ping to a given IPv4 / IPv6 address. Tested with IPv4+IPv6 using ``iputils-ping`` on Linux, as well as the
    default IPv4 ``ping`` utility on Mac OSX (Mojave, 10.14.6).
    
    Fully supported when using Linux with the ``iputils-ping`` package. Only IPv4 support on Mac OSX.
    
    **Example Usage**::
    
        >>> from privex.helpers import ping
        >>> if ping('127.0.0.1', 5) and ping('::1', 10):
        ...     print('Both 127.0.0.1 and ::1 are up')
        ... else:
        ...     print('127.0.0.1 or ::1 failed to respond to a ping within the given timeout.')
    
    **Known Incompatibilities**:
    
     * NOT compatible with IPv6 addresses on OSX due to the lack of a timeout argument with ``ping6``
     * NOT compatible with IPv6 addresses when using ``inetutils-ping`` on Linux due to separate ``ping6`` command

    :param str ip: An IP address as a string, e.g. ``192.168.1.1`` or ``2a07:e00::1``
    :param int timeout: (Default: 30) Number of seconds to wait for a response from the ping before timing out
    :raises ValueError: When the given IP address ``ip`` is invalid or ``timeout`` < 1
    :return bool: ``True`` if ping got a response from the given IP, ``False`` if not
    """
    ip_obj = ip_address(ip)   # verify IP is valid (this will throw if it isn't)
    if timeout < 1:
        raise ValueError('timeout value cannot be less than 1 second')
    opts4 = {
        'Linux': ["/bin/ping", "-c1", f"-w{timeout}"],
        'Darwin': ["/sbin/ping", "-c1", f"-t{timeout}"]
    }
    opts6 = {'Linux':  ["/bin/ping", "-c1", f"-w{timeout}"]}
    opts = opts4 if ip_is_v4(ip_obj) else opts6
    if platform.system() not in opts:
        raise NotImplementedError(f"{__name__}.ping is not fully supported on platform '{platform.system()}'...")
    
    with subprocess.Popen(opts[platform.system()] + [ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
        out, err = proc.communicate()
        err = err.decode('utf-8')
        if 'network is unreachable' in err.lower():
            raise NetworkUnreachable(f'Got error from ping: "{err}"')
        
        return 'bytes from {}'.format(ip) in out.decode('utf-8')
