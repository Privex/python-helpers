class PrivexException(Exception): ...
class NotFound(Exception): ...
class NestedContextException(PrivexException): ...
class BaseDNSException(PrivexException): ...
class BoundaryException(BaseDNSException): ...
class DomainNotFound(BaseDNSException, NotFound): ...
class InvalidDNSRecord(BaseDNSException): ...
class CacheNotFound(PrivexException, NotFound): ...
class NotConfigured(PrivexException): ...
class NetworkUnreachable(PrivexException): ...
class EncryptionError(PrivexException): ...
class EncryptKeyMissing(EncryptionError, NotFound): ...
class InvalidFormat(EncryptionError): ...
class SysCallError(PrivexException): ...
class GeoIPException(PrivexException): ...
class GeoIPDatabaseNotFound(GeoIPException, NotFound): ...
class GeoIPAddressNotFound(GeoIPException, NotFound): ...
class ReverseDNSNotFound(PrivexException, NotFound): ...
class InvalidHost(PrivexException, ValueError): ...
class LockConflict(PrivexException): ...
class LockWaitTimeout(LockConflict): ...
class EventWaitTimeout(PrivexException): ...
class ValidatorNotMatched(PrivexException): ...
