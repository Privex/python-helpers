"""
Network related helper code

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
import logging
from ipaddress import ip_address, IPv4Address, IPv6Address
from typing import Union

log = logging.getLogger(__name__)

try:
    from dns.resolver import Resolver
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

        res = Resolver().query('AS{}.asn.cymru.com'.format(as_number), "TXT")
        if len(res) > 0:
            # res[0] is formatted like such: "15169 | US | arin | 2000-03-30 | GOOGLE - Google LLC, US"
            # with literal quotes. we need to strip them, split by pipe, extract the last element, then strip spaces.
            asname = str(res[0]).strip('"').split('|')[-1:][0].strip()
            return str(asname)
        if quiet:
            return 'Unknown ASN'
        raise KeyError('ASN {} was not found, or server did not respond.'.format(as_number))
    
except ImportError:
    log.debug('privex.helpers.net failed to import "dns.resolver" (pypi package "dnspython"), skipping some helpers')
    pass


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
