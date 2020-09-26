"""
Functions/classes related to hostnames/domains/reverse DNS etc. - network related helper code

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

import asyncio
import socket
from ipaddress import IPv4Address, IPv6Address, ip_address

from typing import AsyncGenerator, Generator, List, Optional, Tuple, Union

from privex.helpers import plugin
from privex.helpers.common import empty
from privex.helpers.exceptions import BoundaryException, InvalidHost, ReverseDNSNotFound
import logging

from privex.helpers.net.util import is_ip, sock_ver
from privex.helpers.types import IP_OR_STR

log = logging.getLogger(__name__)

__all__ = [
    'ip_to_rdns', 'ip4_to_rdns', 'ip6_to_rdns', 'resolve_ips_async', 'resolve_ip_async', 'resolve_ips_multi_async',
    'resolve_ips', 'resolve_ip', 'resolve_ips_multi', 'get_rdns_async', 'get_rdns', 'get_rdns_multi'
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


async def resolve_ips_async(addr: IP_OR_STR, version: Union[str, int] = 'any', v4_convert=False) -> List[str]:
    """
    AsyncIO version of :func:`.resolve_ips_async` - resolves the IPv4/v6 addresses for a given host (``addr``)
    
    
    :param str|IPv4Address|IPv6Address addr: The hostname to resolve. If an IPv4 / IPv6 address is passed instead of a hostname,
                                             it will be validated against ``version``, then returned in a single item list.

    :param str|int version: Default: ``'any'`` - Return both IPv4 and IPv6 addresses (if both are found). If an IP address is passed,
                            then both IPv4 and IPv6 addresses will be accepted. If set to one of the IPv4/IPv6 version choices, then a
                            passed IP of the wrong version will raise :class:`.AttributeError`

                            Choices:

                              * **IPv4 Options**: ``4`` (int), ``'v4'``, ``'4'`` (str), ``'ipv4'``, ``'inet'``, ``'inet4'``
                              * **IPv6 Options**: ``6`` (int), ``'v6'``, ``'6'`` (str), ``'ipv6'``, ``'inet6'``

    :param bool v4_convert: (Default: ``False``) If set to ``True``, will allow IPv6-wrapped IPv4 addresses starting with ``::ffff:`` to
                            be returned when requesting version ``v6`` from an IPv4-only hostname.

    :raises AttributeError: Raised when an IPv4 address is passed and ``version`` is set to IPv6 - as well as vice versa (IPv6 passed
                            while version is set to IPv4)

    :return List[str] ips: Zero or more IP addresses in a list of :class:`str`'s
    """
    loop = asyncio.get_event_loop()
    addr, version = str(addr), sock_ver(version)
    ips = []
    ip = is_ip(addr, version)
    if ip: return [str(ip)]
    try:
        if version in [socket.AF_INET, socket.AF_INET6]:
            _ips = await loop.getaddrinfo(addr, 2001, family=version, proto=socket.IPPROTO_TCP)
        else:
            _ips = await loop.getaddrinfo(addr, 2001, proto=socket.IPPROTO_TCP)
        
        for ip in _ips:
            ips += [ip[-1][0]]
        # If a hostname has no AAAA records, and we request AF_INET6, getaddrinfo often converts the A records
        # into IPv6-wrapped IPv4 addresses like so: ``::ffff:13.77.161.179``
        # Most people who specifically request IPv6 want only real IPv6 addresses, not IPv4 addresses wrapped in IPv6 format.
        if not v4_convert:
            ips = [ip for ip in ips if not ip.startswith('::ffff')]
        return ips
    except Exception as e:
        log.warning("Exception occurred while resolving host %s - reason: %s %s", addr, type(e), str(e))
        return ips


async def resolve_ip_async(addr: IP_OR_STR, version: Union[str, int] = 'any', v4_convert=False) -> Optional[str]:
    """
    AsyncIO version of :func:`.resolve_ip` - resolves the IPv4/v6 address for a given host (``addr``)
    """
    ips = await resolve_ips_async(addr, version=version, v4_convert=v4_convert)
    if len(ips) == 0:
        return None
    return ips[0]


async def resolve_ips_multi_async(*addr: IP_OR_STR, version: Union[str, int] = 'any', v4_convert=False) \
        -> AsyncGenerator[Tuple[str, Optional[List[str]]], None]:
    """
    Async version of :func:`.resolve_ips_multi`. Resolve IPv4/v6 addresses for multiple hosts specified as positional arguments.
    
    Returns results as an AsyncIO generator, to allow for efficient handling of a large amount of hostnames to resolve.

    Using the AsyncIO generator in a loop efficiently::

        >>> async for host, ips in resolve_ips_multi_async('privex.io', 'cloudflare.com', 'google.com'):
        ...     print(f"{host:<20} ->   {', '.join(ips)}")
        ...
        privex.io            ->   2a07:e00::abc, 185.130.44.10
        cloudflare.com       ->   2606:4700::6811:af55, 2606:4700::6811:b055, 104.17.176.85, 104.17.175.85
        google.com           ->   2a00:1450:4009:807::200e, 216.58.204.238

    If you're only resolving a small number of hosts ( less than 100 or so ), you can simply comprehend the generator into
    a :class:`list` and then turn the result into a :class:`dict` using ``dict()``, which will get you a dictionary of hosts mapped to
    lists of IP addresses.

    Dictionary Cast Examples::

        >>> ips = [x async for x in resolve_ips_multi_async('privex.io', 'microsoft.com', 'google.com')]
        >>> dict(ips)
        {'privex.io': ['2a07:e00::abc', '185.130.44.10'],
         'microsoft.com': ['104.215.148.63', '40.76.4.15', '40.112.72.205', '40.113.200.201', '13.77.161.179'],
         'google.com': ['2a00:1450:4009:807::200e', '216.58.204.238']}
        >>> dict([x async for x in resolve_ips_multi_async('privex.io', 'microsoft.com', 'google.com', version='v6')])
        {'privex.io': ['2a07:e00::abc'], 'microsoft.com': [], 'google.com': ['2a00:1450:4009:81c::200e']}
        >>> dict([x async for x in resolve_ips_multi_async('privex.io', 'this-does-not-exist', 'google.com', version='v6')])
        {'privex.io': ['2a07:e00::abc'], 'this-does-not-exist': [], 'google.com': ['2a00:1450:4009:81c::200e']}
         >>> dict([x async for x in resolve_ips_multi_async('privex.io', 'example.com', '127.0.0.1', version='v6')])
        [resolve_ips_multi AttributeError] Invalid IP: 127.0.0.1 - Ex: <class 'AttributeError'> Passed address '127.0.0.1' was
                                           an IPv4 address, but 'version' requested an IPv6 address.
        {'privex.io': ['2a07:e00::abc'], 'example.com': ['2606:2800:220:1:248:1893:25c8:1946'], '127.0.0.1': None}


    :param str|IPv4Address|IPv6Address addr: Hostname's to resolve / IP addresses to validate or pass-thru
    :param str|int version: (Default: ``any``) - ``4`` (int), ``'v4'``, ``6`` (int), ``'v6'`` (see :func:`.resolve_ips` for more options)
    :param bool v4_convert: (Default: ``False``) If set to ``True``, will allow IPv6-wrapped IPv4 addresses starting with ``::ffff:`` to
                            be returned when requesting version ``v6`` from an IPv4-only hostname.

    :return Tuple[str,Optional[List[str]] gen:  An async generator which returns tuples containing a hostname/IP, and a list of it's
        resolved IPs. If the IP was rejected (e.g. IPv4 IP passed with ``v6`` ``version`` param), then the list may instead be ``None``.
    
    """
    for a in addr:
        try:
            res = await resolve_ips_async(a, version=version, v4_convert=v4_convert)
            yield (a, res)
        except socket.gaierror as e:
            log.warning("[resolve_ips_multi socket.gaierror] Failed to resolve host: %s - Ex: %s %s", addr, type(e), str(e))
            yield (a, None)
        except AttributeError as e:
            log.warning("[resolve_ips_multi AttributeError] Invalid IP: %s - Ex: %s %s", a, type(e), str(e))
            yield (a, None)


def resolve_ips(addr: IP_OR_STR, version: Union[str, int] = 'any', v4_convert=False) -> List[str]:
    """
    With just a single hostname argument, both IPv4 and IPv6 addresses will be returned as strings::
    
        >>> resolve_ips('www.privex.io')
        ['2a07:e00::abc', '185.130.44.10']
    
    You can provide the ``version`` argument as either positional or kwarg, e.g. ``v4`` or ``v6`` to restrict the results
    to only that IP version::
    
        >>> resolve_ips('privex.io', version='v4')
        ['185.130.44.10']
    
    The ``v4_convert`` option is ``False`` by default, which prevents ``::ffff:`` style IPv6 wrapped IPv4 addresses being
    returned when you request version ``v6``::
    
        >>> resolve_ips('microsoft.com')
        ['40.76.4.15', '40.112.72.205', '13.77.161.179', '40.113.200.201', '104.215.148.63']
        >>> resolve_ips('microsoft.com', 'v6')
        []
    
    If for whatever reason, you need ``::ffff:`` IPv6 wrapped IPv4 addresses to be returned, you can set ``v4_convert=True``,
    which will disable filtering out ``::ffff:`` fake IPv6 addresses::
    
        >>> resolve_ips('microsoft.com', 'v6', v4_convert=True)
        ['::ffff:40.76.4.15', '::ffff:40.112.72.205', '::ffff:13.77.161.179',
         '::ffff:40.113.200.201', '::ffff:104.215.148.63']
    
    For convenience, if an IPv4 / IPv6 address is specified, then it will simply be validated against ``version`` and then returned
    within a list. This is useful when handling user specified data, which may be either a hostname or an IP address, and you
    need to resolve hostnames while leaving IP addresses alone::
    
        >>> resolve_ips('8.8.4.4')
        ['8.8.4.4']
        >>> resolve_ips('2a07:e00::333')
        ['2a07:e00::333']
        
        >>> resolve_ips('8.8.4.4', 'v6')
        Traceback (most recent call last):
          File "<ipython-input-10-6ca9e766006f>", line 1, in <module>
            resolve_ips('8.8.4.4', 'v6')
        AttributeError: Passed address '8.8.4.4' was an IPv4 address, but 'version' requested an IPv6 address.
        
        >>> resolve_ips('2a07:e00::333', 'v4')
        Traceback (most recent call last):
          File "<ipython-input-11-543bfa71c57a>", line 1, in <module>
            resolve_ips('2a07:e00::333', 'v4')
        AttributeError: Passed address '2a07:e00::333' was an IPv6 address, but 'version' requested an IPv4 address.
        

    :param str|IPv4Address|IPv6Address addr: The hostname to resolve. If an IPv4 / IPv6 address is passed instead of a hostname,
                                             it will be validated against ``version``, then returned in a single item list.
    
    :param str|int version: Default: ``'any'`` - Return both IPv4 and IPv6 addresses (if both are found). If an IP address is passed,
                            then both IPv4 and IPv6 addresses will be accepted. If set to one of the IPv4/IPv6 version choices, then a
                            passed IP of the wrong version will raise :class:`.AttributeError`
                            
                            Choices:
                            
                              * **IPv4 Options**: ``4`` (int), ``'v4'``, ``'4'`` (str), ``'ipv4'``, ``'inet'``, ``'inet4'``
                              * **IPv6 Options**: ``6`` (int), ``'v6'``, ``'6'`` (str), ``'ipv6'``, ``'inet6'``
    
    :param bool v4_convert: (Default: ``False``) If set to ``True``, will allow IPv6-wrapped IPv4 addresses starting with ``::ffff:`` to
                            be returned when requesting version ``v6`` from an IPv4-only hostname.
    
    :raises AttributeError: Raised when an IPv4 address is passed and ``version`` is set to IPv6 - as well as vice versa (IPv6 passed
                            while version is set to IPv4)
    
    :return List[str] ips: Zero or more IP addresses in a list of :class:`str`'s
    """
    addr, version, ips = str(addr), sock_ver(version), []
    ip = is_ip(addr, version)
    if ip: return [str(ip)]
    try:
        if version in [socket.AF_INET, socket.AF_INET6]:
            _ips = socket.getaddrinfo(addr, 2001, family=version, proto=socket.IPPROTO_TCP)
        else:
            _ips = socket.getaddrinfo(addr, 2001, proto=socket.IPPROTO_TCP)
        for ip in _ips:
            ips += [ip[-1][0]]
        # If a hostname has no AAAA records, and we request AF_INET6, getaddrinfo often converts the A records
        # into IPv6-wrapped IPv4 addresses like so: ``::ffff:13.77.161.179``
        # Most people who specifically request IPv6 want only real IPv6 addresses, not IPv4 addresses wrapped in IPv6 format.
        if not v4_convert:
            ips = [ip for ip in ips if not ip.startswith('::ffff')]
        return ips
    except Exception as e:
        log.warning("Exception occurred while resolving host %s - reason: %s %s", addr, type(e), str(e))
        return ips


def resolve_ip(addr: IP_OR_STR, version: Union[str, int] = 'any', v4_convert=False) -> Optional[str]:
    """
    Wrapper for :func:`.resolve_ips` - passes args to :func:`.resolve_ips` and returns the first item from the results.
    
    If the results are empty, ``None`` will be returned.
    
    Examples::
    
        >>> resolve_ip('privex.io')
        '2a07:e00::abc'
        >>> resolve_ip('privex.io', 'v4')
        '185.130.44.10'
        >>> resolve_ip('microsoft.com')
        '104.215.148.63'
        >>> repr(resolve_ip('microsoft.com' ,'v6'))
        'None'
        >>> resolve_ip('microsoft.com' ,'v6', v4_convert=True)
        '::ffff:104.215.148.63'

    :param str|IPv4Address|IPv6Address addr: Hostname to resolve / IP address to validate or pass-thru
    
    :param str|int version: (Default: ``any``) - ``4`` (int), ``'v4'``, ``6`` (int), ``'v6'`` (see :func:`.resolve_ips` for more options)
    
    :param bool v4_convert: (Default: ``False``) If set to ``True``, will allow IPv6-wrapped IPv4 addresses starting with ``::ffff:`` to
                            be returned when requesting version ``v6`` from an IPv4-only hostname.
    
    :raises AttributeError: Raised when an IPv4 address is passed and ``version`` is set to IPv6 - as well as vice versa (IPv6 passed
                            while version is set to IPv4)
    
    :return Optional[str] ips: An IPv4/v6 address as a string if there was at least 1 result - otherwise ``None``.
    """
    ips = resolve_ips(addr, version=version, v4_convert=v4_convert)
    if len(ips) == 0:
        return None
    return ips[0]


def resolve_ips_multi(*addr: IP_OR_STR, version: Union[str, int] = 'any', v4_convert=False) \
        -> Generator[Tuple[str, Optional[List[str]]], None, None]:
    """
    Resolve IPv4/v6 addresses for multiple hosts specified as positional arguments.
    
    Returns results as a generator, to allow for efficient handling of a large amount of hostnames to resolve.
    
    Using the generator in a loop efficiently::
    
        >>> for host, ips in resolve_ips_multi('privex.io', 'cloudflare.com', 'google.com'):
        ...     print(f"{host:<20} ->   {', '.join(ips)}")
        ...
        privex.io            ->   2a07:e00::abc, 185.130.44.10
        cloudflare.com       ->   2606:4700::6811:af55, 2606:4700::6811:b055, 104.17.176.85, 104.17.175.85
        google.com           ->   2a00:1450:4009:807::200e, 216.58.204.238
    
    If you're only resolving a small number of hosts ( less than 100 or so ), you can simply cast the generator into
    a :class:`dict` using ``dict()``, which will get you a dictionary of hosts mapped to lists of IP addresses.

    Dictionary Cast Examples::
        
        >>> dict(resolve_ips_multi('privex.io', 'microsoft.com', 'google.com'))
        {'privex.io': ['2a07:e00::abc', '185.130.44.10'],
         'microsoft.com': ['104.215.148.63', '40.76.4.15', '40.112.72.205', '40.113.200.201', '13.77.161.179'],
         'google.com': ['2a00:1450:4009:807::200e', '216.58.204.238']}
        >>> dict(resolve_ips_multi('privex.io', 'microsoft.com', 'google.com', version='v6'))
        {'privex.io': ['2a07:e00::abc'], 'microsoft.com': [], 'google.com': ['2a00:1450:4009:81c::200e']}
        >>> dict(resolve_ips_multi('privex.io', 'this-does-not-exist', 'google.com', version='v6'))
        {'privex.io': ['2a07:e00::abc'], 'this-does-not-exist': [], 'google.com': ['2a00:1450:4009:81c::200e']}
         >>> dict(resolve_ips_multi('privex.io', 'example.com', '127.0.0.1', version='v6'))
        [resolve_ips_multi AttributeError] Invalid IP: 127.0.0.1 - Ex: <class 'AttributeError'> Passed address '127.0.0.1' was
                                           an IPv4 address, but 'version' requested an IPv6 address.
        {'privex.io': ['2a07:e00::abc'], 'example.com': ['2606:2800:220:1:248:1893:25c8:1946'], '127.0.0.1': None}
    
    
    :param str|IPv4Address|IPv6Address addr: Hostname to resolve / IP address to validate or pass-thru
    :param str|int version: (Default: ``any``) - ``4`` (int), ``'v4'``, ``6`` (int), ``'v6'`` (see :func:`.resolve_ips` for more options)
    :param bool v4_convert: (Default: ``False``) If set to ``True``, will allow IPv6-wrapped IPv4 addresses starting with ``::ffff:`` to
                            be returned when requesting version ``v6`` from an IPv4-only hostname.
                            
    :return Tuple[str,Optional[List[str]] gen:  A generator which returns tuples containing a hostname/IP, and a list of it's resolved
        IPs. If the IP was rejected (e.g. IPv4 IP passed with ``v6`` ``version`` param), then the list may instead be ``None``.
    """
    for a in addr:
        try:
            res = resolve_ips(a, version=version, v4_convert=v4_convert)
            yield (a, res)
        except socket.gaierror as e:
            log.warning("[resolve_ips_multi socket.gaierror] Failed to resolve host: %s - Ex: %s %s", addr, type(e), str(e))
            yield (a, None)
        except AttributeError as e:
            log.warning("[resolve_ips_multi AttributeError] Invalid IP: %s - Ex: %s %s", a, type(e), str(e))
            yield (a, None)


async def get_rdns_async(host: IP_OR_STR, throw=True, version='any', name_port=80) -> Optional[str]:
    """
    AsyncIO version of :func:`.get_rdns` - get the reverse DNS for a given host (IP address or domain)
    
        >>> from privex.helpers import get_rdns_async
        >>> await get_rdns_async('185.130.44.10')
        'web-se1.privex.io'
        >>> await get_rdns_async('2a07:e00::333')
        'se.dns.privex.io'
        >>> await get_rdns_async('privex.io')
        'web-se1.privex.io'
    
    :param str|IPv4Address|IPv6Address host: An IPv4/v6 address, or domain to lookup reverse DNS for.
    :param bool throw: (Default: ``True``) When ``True``, will raise :class:`.ReverseDNSNotFound` or :class:`.InvalidHost` when no
                       rDNS records can be found for ``host``, or when ``host`` is an invalid IP / non-existent domain.
                       When ``False``, will simply return ``None`` when ``host`` is invalid, or no rDNS records are found.
    
    :param str|int version: IP version to use when looking up a domain/hostname (default: ``'any'``)
    
    :param int name_port: This generally isn't important. This port is passed to :func:`loop.getnameinfo` when looking
                          up the reverse DNS for ``host``. Usually there's no reason to change this from the default.
    
    :raises ReverseDNSNotFound: When ``throw`` is True and no rDNS records were found for ``host``
    :raises InvalidHost: When ``throw`` is True and ``host`` is an invalid IP address or non-existent domain/hostname
    :return Optional[str] rDNS: The reverse DNS hostname for ``host`` (value of PTR record)
    """
    loop = asyncio.get_event_loop()
    host = str(host)
    try:
        if not is_ip(host):
            orig_host = host
            host = await resolve_ip_async(host, version=version)
            if empty(host):
                if throw:
                    raise InvalidHost(f"Host '{orig_host}' is not a valid IP address, nor an existent domain")
                return None
        
        res = await loop.getnameinfo((host, name_port))
        rdns = res[0]
        if is_ip(rdns):
            if throw: raise ReverseDNSNotFound(f"No reverse DNS records found for host '{host}' - result was: {rdns}")
            return None
        return rdns
    except socket.gaierror as e:
        if throw: raise InvalidHost(f"Host '{host}' is not a valid IP address, nor an existent domain: {type(e)} {str(e)}")
    return None


def get_rdns(host: IP_OR_STR, throw=True) -> Optional[str]:
    """
    Look up the reverse DNS hostname for ``host`` and return it as a string. The ``host`` can be an IP address as a :class:`str`,
    :class:`.IPv4Address`, :class:`.IPv6Address` - or a domain.
    
    If a domain is passed, e.g. ``privex.io`` - then the reverse DNS will be looked up for the IP address contained in the domain's
    AAAA or A records.
    
    Toggle ``throw`` to control whether to raise exceptions on error (``True``), or to simply return None (``False``).
    
    Basic usage::
    
        >>> from privex.helpers import get_rdns
        >>> get_rdns('185.130.44.10')
        'web-se1.privex.io'
        >>> get_rdns('2a07:e00::333')
        'se.dns.privex.io'
        >>> get_rdns('privex.io')
        'web-se1.privex.io'
    
    Error handling::
    
        >>> get_rdns('192.168.4.5')
        Traceback (most recent call last):
          File "<ipython-input-14-e1ed65295031>", line 1, in <module>
            get_rdns('192.168.4.5')
        privex.helpers.exceptions.ReverseDNSNotFound: No reverse DNS records found for host '192.168.4.5':
            <class 'socket.herror'> [Errno 1] Unknown host
        >>> get_rdns('non-existent-domain.example')
        Traceback (most recent call last):
          File "<ipython-input-16-0d75d37a930f>", line 1, in <module>
            get_rdns('non-existent-domain.example')
        privex.helpers.exceptions.InvalidHost: Host 'non-existent-domain.example' is not a valid IP address,
        nor an existent domain: <class 'socket.gaierror'> [Errno 8] nodename nor servname provided, or not known
        >>> repr(get_rdns('192.168.4.5', throw=False))
        'None'
        >>> repr(get_rdns('non-existent-domain.example', False))
        'None'
    
    
    :param str|IPv4Address|IPv6Address host: An IPv4/v6 address, or domain to lookup reverse DNS for.
    :param bool throw: (Default: ``True``) When ``True``, will raise :class:`.ReverseDNSNotFound` or :class:`.InvalidHost` when no
                       rDNS records can be found for ``host``, or when ``host`` is an invalid IP / non-existent domain.
                       When ``False``, will simply return ``None`` when ``host`` is invalid, or no rDNS records are found.
    :raises ReverseDNSNotFound: When ``throw`` is True and no rDNS records were found for ``host``
    :raises InvalidHost: When ``throw`` is True and ``host`` is an invalid IP address or non-existent domain/hostname
    :return Optional[str] rDNS: The reverse DNS hostname for ``host`` (value of PTR record)
    """
    try:
        rdns = socket.gethostbyaddr(str(host))
        return rdns[0]
    except socket.herror as e:
        if throw: raise ReverseDNSNotFound(f"No reverse DNS records found for host '{host}': {type(e)} {str(e)}")
    except socket.gaierror as e:
        if throw: raise InvalidHost(f"Host '{host}' is not a valid IP address, nor an existent domain: {type(e)} {str(e)}")
    return None


def get_rdns_multi(*hosts: IP_OR_STR, throw=False) -> Generator[Tuple[str, Optional[str]], None, None]:
    """
    Resolve reverse DNS hostnames for multiple IPs / domains specified as positional arguments.
    
    Each host in ``hosts`` can be an IP address as a :class:`str`, :class:`.IPv4Address`, :class:`.IPv6Address` - or a domain.
    
    Returns results as a generator, to allow for efficient handling of a large amount of hosts to resolve.
    
    Basic usage::
    
        >>> for host, rdns in get_rdns_multi('185.130.44.10', '8.8.4.4', '1.1.1.1', '2a07:e00::333'):
        >>>     print(f"{host:<20} -> {rdns:>5}")
        185.130.44.10        -> web-se1.privex.io
        8.8.4.4              -> dns.google
        1.1.1.1              -> one.one.one.one
        2a07:e00::333        -> se.dns.privex.io
    
    If you're only resolving a small number of hosts ( less than 100 or so ), you can simply cast the generator into
    a :class:`dict` using ``dict()``, which will get you a dictionary of hosts mapped to their rDNS::
    
        >>> data = dict(get_rdns_multi('185.130.44.10', '8.8.4.4', '1.1.1.1', '2a07:e00::333'))
        >>> data['8.8.4.4']
        'dns.google'
        >>> data.get('2a07:e00::333', 'error')
        'se.dns.privex.io'
    
    :param str|IPv4Address|IPv6Address hosts: One or more IPv4/v6 addresses, or domains to lookup reverse DNS for - as positional args.
    
    :param bool throw: (Default: ``False``) When ``True``, will raise :class:`.ReverseDNSNotFound` or :class:`.InvalidHost` when no
                       rDNS records can be found for a host, or when the host is an invalid IP / non-existent domain.
                       When ``False``, will simply return ``None`` when a host is invalid, or no rDNS records are found.
    
    :raises ReverseDNSNotFound: When ``throw`` is True and no rDNS records were found for ``host``
    :raises InvalidHost: When ``throw`` is True and ``host`` is an invalid IP address or non-existent domain/hostname
    
    :return Tuple[str,Optional[str]] rDNS: A generator returning :class:`tuple`'s containing the original passed host, and it's
                                           reverse DNS hostname (value of PTR record)
    """
    for h in hosts:
        yield (str(h), get_rdns(str(h), throw=throw))
