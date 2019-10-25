"""
Exception classes used either by our helpers, or just generic exception names which are missing from
the standard base exceptions in Python, and are commonly used across our projects.

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


class PrivexException(Exception):
    """Base exception for all custom Privex exceptions"""
    pass


#####
# Exceptions related to DNS (domain, or individual record errors)
#####

class BaseDNSException(PrivexException):
    """Base exception for DNS-related exceptions"""
    pass


class BoundaryException(BaseDNSException):
    """
    Thrown when the v4/v6 address boundary for a reverse DNS record is invalid.
    
    An "address boundary" is the minimum amount of bits that defines a character in a reverse DNS domain 
    (i.e. those ending in in-addr/ip6.arpa):

         - IPv6 uses "nibbles" of 4 bits for each individual character in a standard 128-bit address
         - IPv4 uses "octets" of 8 bits, which represent 0-255 in each of the 4 "blocks" within an IPv4 address
    
    This means the minimum and maximum boundaries for IPv4 and IPv6 are as such:

        IPv6 - Minimum boundary: 4 bits (``*.f.ip6.arpa``), Maximum boundary: 128 bits (rDNS for a single address, i.e. a /128)
        IPv4 - Minimum boundary: 8 bits (``x.x.x.127.in-addr.arpa``), Maximum boundary: 32 bits (``1.0.0.127.in-addr.arpa``)
    
    """
    pass


class DomainNotFound(BaseDNSException):
    """Thrown when a (sub)domain or it's parent(s) could not be found"""
    pass


class InvalidDNSRecord(BaseDNSException):
    """Thrown when a passed DNS record is not valid"""
    pass


class CacheNotFound(PrivexException):
    """
    Thrown when a cache key is requested, but it doesn't exist / is expired.
    
    Most likely only used when some form of "strict mode" is enabled for the cache adapter.
    """
    pass


class NotConfigured(PrivexException):
    """
    Thrown when code attempts to access something that wasn't fully configured / instantiated by the user.
    
    Example: Attempting to use a database dependant function/method without having configured any database details.
    """


class NetworkUnreachable(PrivexException):
    """
    Thrown when a network interface or IP version (e.g. IPv4/v6) is unavailable.
    
    Example: when running ``ping`` with an IPv6 address on a system which has no IPv6.
    """


class EncryptionError(PrivexException):
    """Raised when something went wrong attempting to encrypt or decrypt a piece of data"""
    pass


class EncryptKeyMissing(EncryptionError):
    """Raised when ENCRYPT_KEY is not set, or invalid"""
    pass


class InvalidFormat(EncryptionError):
    """
    Raised when an invalid public/private format, or encoding is specified when serializing an asymmetric key pair
    """


