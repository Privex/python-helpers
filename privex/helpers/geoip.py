"""
Various helper functions for use with Maxmind's GeoIP2 Library

Getting started with our GeoIP2 wrapper
---------------------------------------

Basic Usage::

    >>> from privex.helpers import geoip
    >>> res = geoip.geolocate_ip('185.130.44.5')
    >>> print(f"Country: {res.country} || Code: {res.country_code} || City: {res.city}")
    Country: Sweden || Code: SE || City: Stockholm
    >>> print(f"ISP: {res.as_name} || AS Num: {res.as_number}")
    ISP: Privex Inc. || AS Num: 210083 || Network: 185.130.44.0/24

If your application won't need to touch the GeoIP database for a while, you should call :func:`.cleanup` to
close the GeoIP2 databases to save memory::

    >>> geoip.cleanup


Using the GeoIP2 :func:`.geoip_manager` context manager
-------------------------------------------------------

Alternatively, you can use the context manager :func:`.geoip_manager` which will automatically call :func:`.cleanup`
at the end of a ``with`` block::

    >>> with geoip.geoip_manager():
    ...     res = geoip.geolocate_ip('2a07:e00::333')
    ...     print(f"Postcode: {res['postcode']} || Lat: {res.get('lat', 'unknown')} || Long: {res.long}")
    ...
    Postcode: 173 11 || Lat: 59.3333 || Long: 18.05


Accessing the underlying :mod:`geoip2` library instances
--------------------------------------------------------

If our wrappers don't provide certain features you need, you can easily access the raw GeoIP2 reader instances.


With our context manager
^^^^^^^^^^^^^^^^^^^^^^^^

Accessing :class:`geoip2.database.Reader` via the context manager::

    >>> import geoip2.models
    >>> with geoip.geoip_manager('city') as geo:
    ...     data: geoip2.models.City = geo.city('95.216.3.171')
    ...     print('Continent:', data.continent.names.get('en'), 'Time Zone:', data.location.time_zone)
    Continent: Europe Time Zone: Europe/Helsinki


Directly, via the :mod:`privex.helpers.plugin` module
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Accessing :class:`geoip2.database.Reader` via the plugin module::
    
    >>> from privex.helpers import plugin
    >>> geo = plugin.get_geoip('asn')
    >>> as_data: geoip2.models.ASN = geo.asn('95.216.3.171')
    >>> print(f"{as_data.autonomous_system_organization} (ASN: {as_data.autonomous_system_number})")
    'Hetzner Online GmbH (ASN: 24940)'
    >>> # To close the ASN database properly when you're done, call 'plugin.close_geoip' with 'asn'
    >>> plugin.close_geoip('asn')
    True



**Copyright**::

        +===================================================+
        |                 © 2020 Privex Inc.                |
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

    Copyright 2020     Privex Inc.   ( https://www.privex.io )


"""
import logging
import attr
import geoip2.database
import geoip2.models
import geoip2.errors
from contextlib import contextmanager
from typing import Optional, Tuple, Generator
from privex.helpers import plugin
from privex.helpers.extras.attrs import AttribDictable
from privex.helpers.exceptions import GeoIPAddressNotFound
from privex.helpers.common import empty
from privex.helpers.types import IP_OR_STR

log = logging.getLogger(__name__)

__all__ = [
    'GeoIPResult', 'geolocate_ip', 'geolocate_ips', 'cleanup_geoip', 'geoip_manager'
]


@attr.s
class GeoIPResult(AttribDictable):
    country = attr.ib(type=str, default=None)
    """Full English country name where this IP is based, e.g. ``Sweden``"""
    country_code = attr.ib(type=str, default=None)
    """Two letter ISO country code representing the country where this IP is based, e.g. ``SE``"""
    
    city = attr.ib(type=str, default=None)
    """Full English city name where this IP is based, e.g. ``Stockholm``"""
    postcode = attr.ib(type=str, default=None)
    """Estimated Postcode / ZIP code where the IP is located e.g. ``173 11``"""
    
    as_number = attr.ib(type=int, default=None)
    """The string name of the ISP / Organisation the IP belongs to, e.g. ``Privex Inc.``"""
    as_name = attr.ib(type=str, default=None)
    """The numeric AS number identifying the ISP / Organisation the IP belongs to, e.g. ``210083``"""
    
    ip_address = attr.ib(type=str, default=None)
    """The IP address the result is for"""
    network = attr.ib(type=str, default=None)
    """The network the IP belongs to, e.g. ``185.130.44.0/22``"""
    
    long = attr.ib(type=int, default=None)
    """An estimated longitude (part of co-ordinates) where the IP is based"""
    lat = attr.ib(type=int, default=None)
    """An estimated latitude (part of co-ordinates) where the IP is based"""
    
    geoasn_data = attr.ib(type=geoip2.models.ASN, default=None)
    """The raw object returned by :meth:`geoip2.database.Reader.asn` """
    geocity_data = attr.ib(type=geoip2.models.City, default=None)
    """The raw object returned by :meth:`geoip2.database.Reader.city` """


def geolocate_ip(addr: IP_OR_STR, throw=True) -> Optional[GeoIPResult]:
    """
    Looks up the IPv4/IPv6 address ``addr`` against GeoIP2 City + ASN, and returns a :class:`.GeoIPResult` containing the GeoIP data.
    
    Usage::
    
        >>> g = geolocate_ip('2a07:e00::333')
        >>> print(g.city, g.country, g.country_code, g.as_number, g.as_name, sep='\t')
        Stockholm	Sweden	SE	210083	Privex Inc.
        >>> g = geolocate_ip('8.8.4.4')
        None	United States	US	15169	Google LLC
    
    
    :param IP_OR_STR addr: An IPv4 or IPv6 address to geo-locate
    :param bool throw: (Default: ``True``) If ``True``, will raise :class:`.GeoIPAddressNotFound` if an IP address isn't found
                       in the GeoIP database. If ``False``, will simply return ``None`` if it's not found.
    :raises GeoIPAddressNotFound: When ``throw`` is ``True`` and ``addr`` can't be found in a GeoIP database.
    :raises ValueError: When ``addr`` is not a valid IP address.
    :return Optional[GeoIPResult] res: A :class:`.GeoIPResult` containing the GeoIP data for the IP - or ``None`` if ``throw`` is
                                       ``False``, and the IP address wasn't found in the database.
                                       
    """
    addr = str(addr)
    res = GeoIPResult()
    try:
        # with geoip2.database.Reader(settings.GEOCITY) as g:
        g = plugin.get_geoip('city')
        try:
            response: geoip2.models.City = g.city(addr)
            res.geocity_data = response
            res.country_code = response.country.iso_code
            res.country = response.country.names.get('en', None)
            res.city = response.city.names.get('en', None)
            res.postcode = response.postal.code
            res.long = response.location.longitude
            res.lat = response.location.latitude
        except geoip2.errors.AddressNotFoundError as e:
            if throw:
                raise GeoIPAddressNotFound(str(e))
            return None
        except ValueError as e:
            # We always raise ValueError regardless of the 'throw' param - since ValueError
            # usually means the address is completely invalid.
            raise e
        except Exception as e:
            log.warning("Failed to resolve Country / City for %s - Reason: %s %s", addr, type(e), str(e))
        g = plugin.get_geoip('asn')
        try:
            response: geoip2.models.ASN = g.asn(addr)
            res.as_name = response.autonomous_system_organization
            res.as_number = response.autonomous_system_number
            res.network = response.network
            res.ip_address = response.ip_address
            res.geoasn_data = response
        except geoip2.errors.AddressNotFoundError as e:
            if throw:
                raise GeoIPAddressNotFound(str(e))
        except ValueError as e:
            # We always raise ValueError regardless of the 'throw' param - since ValueError
            # usually means the address is completely invalid.
            raise e
        except Exception as e:
            log.warning("Failed to resolve ASN for %s - Reason: %s %s", addr, type(e), str(e))
    except Exception as e:
        log.exception("Serious error while resolving GeoIP for %s", addr)
        raise e
    return res


def geolocate_ips(*addrs, throw=False) -> Generator[Tuple[str, Optional[GeoIPResult]], None, None]:
    """
    Same as :func:`.geolocate_ip` but accepts multiple IP addresses, and returns the results as a generator.
    
    Usage::
    
        >>> for ip, g in geolocate_ips('185.130.44.5', '8.8.4.4', '2a07:e00::333'):
        ...     print(f"{ip:<20} -> {str(g.city):<15} {str(g.country):<15} ({g.as_number} {g.as_name})")
        185.130.44.5         -> Stockholm       Sweden          (210083 Privex Inc.)
        8.8.4.4              -> None            United States   (15169 Google LLC)
        2a07:e00::333        -> Stockholm       Sweden          (210083 Privex Inc.)
        >>> data = dict(geolocate_ips('185.130.44.5', '8.8.4.4', '2a07:e00::333'))
        >>> data['8.8.4.4'].country
        'United States'
        >>> data['2a07:e00::333'].as_name
        'Privex Inc.'
    
    
    :param IP_OR_STR addrs: One or more IPv4 or IPv6 addresses to geo-locate
    :param bool throw: (Default: ``True``) If ``True``, will raise :class:`.GeoIPAddressNotFound` if an IP address isn't found
                       in the GeoIP database. If ``False``, will simply return ``None`` if it's not found.
    :raises GeoIPAddressNotFound: When ``throw`` is ``True`` and one of the ``addrs`` can't be found in a GeoIP database.
    :raises ValueError: When ``throw`` is ``True`` and one of the ``addrs`` is not a valid IP address.
    
    :return Tuple[str, Optional[GeoIPResult]] res: A generator which returns tuples containing the matching IP
                        address, and the :class:`.GeoIPResult` object containing the GeoIP data for the IP - or
                        ``None`` if ``throw`` is ``False``, and the IP address wasn't found in the database.
    """
    for addr in addrs:
        try:
            res = geolocate_ip(addr, throw=throw)
        except (Exception, ValueError) as e:
            if throw:
                raise e
            log.warning("Ignoring exception while geo-locating IP '%s': %s %s", addr, type(e), str(e))
            res = None
        if empty(res): yield (addr, None)
        if all([empty(res.country), empty(res.country_code), res.as_name, res.as_number, res.lat, res.long]):
            yield (addr, None)
        yield (addr, res)


def cleanup(geo_type: str = None):
    """
    With no arguments, closes and removes GeoIP city + asn + country from thread store.
    
    With the first argument ``geo_type`` specified (either 'city', 'asn' or 'country'), only that specific GeoIP2 instance
    will be closed and removed from the thread store.
    """
    if geo_type is None:
        return [plugin.close_geoip('city'),
                plugin.close_geoip('asn'),
                plugin.close_geoip('country')]
    return plugin.close_geoip(geo_type)


cleanup_geoip = cleanup


@contextmanager
def geoip_manager(geo_type: str = None) -> Optional[geoip2.database.Reader]:
    if not empty(geo_type):
        yield plugin.get_geoip(geo_type)
        cleanup()
    else:
        yield None
        cleanup()

