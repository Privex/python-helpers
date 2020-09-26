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


class PrivexException(Exception):
    """Base exception for all custom Privex exceptions"""
    pass


class NotFound(Exception):
    """Generic exception mixin for all exceptions related to something not being found"""
    pass


class NestedContextException(PrivexException):
    """
    Raised by a context manager when there's a conflict while nesting multiple ``with xxx as y`` blocks - for example
    if there's too many nested ``with`` layers.
    """


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


class DomainNotFound(BaseDNSException, NotFound):
    """Thrown when a (sub)domain or it's parent(s) could not be found"""
    pass


class InvalidDNSRecord(BaseDNSException):
    """Thrown when a passed DNS record is not valid"""
    pass


class CacheNotFound(PrivexException, NotFound):
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


class EncryptKeyMissing(EncryptionError, NotFound):
    """Raised when ENCRYPT_KEY is not set, or invalid"""
    pass


class InvalidFormat(EncryptionError):
    """
    Raised when an invalid public/private format, or encoding is specified when serializing an asymmetric key pair
    """


class SysCallError(PrivexException):
    """
    Raised when an error appears to have been returned after calling an external command
    (e.g. via :class:`subprocess.Popen`)
    """


class GeoIPException(PrivexException):
    pass


class GeoIPDatabaseNotFound(GeoIPException, NotFound):
    pass


class GeoIPAddressNotFound(GeoIPException, NotFound):
    pass


class ReverseDNSNotFound(PrivexException, NotFound):
    """Raised when a given IP address does not have a reverse DNS set"""
    pass


class InvalidHost(PrivexException, ValueError):
    """Raised when a passed IP address or hostname/domain is invalid."""
    pass


class LockConflict(PrivexException):
    """
    Raised when attempting to acquire a lock with a :class:`threading.Lock` or :class:`asyncio.Lock`, and the lock object
    is already locked.

    This would only be raised either when non-blocking acquisition was requested, or the blocking wait timed out.
    """


class LockWaitTimeout(LockConflict):
    """
    Sub-class of :class:`.LockConflict` - only to be raised when a timeout has been reached while waiting
    to acquire a :class:`threading.Lock`
    """


class EventWaitTimeout(PrivexException):
    """
    Raised when a timeout has been reached while waiting for an event (:class:`threading.Event`) to be signalled.
    """


class ValidatorNotMatched(PrivexException):
    pass

