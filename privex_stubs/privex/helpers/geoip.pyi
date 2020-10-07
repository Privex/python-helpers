import geoip2.errors
from privex.helpers.extras.attrs import AttribDictable
from privex.helpers.types import IP_OR_STR
from typing import Any, Generator, Optional, Tuple

class GeoIPResult(AttribDictable):
    country: Any = ...
    country_code: Any = ...
    city: Any = ...
    postcode: Any = ...
    as_number: Any = ...
    as_name: Any = ...
    ip_address: Any = ...
    network: Any = ...
    long: Any = ...
    lat: Any = ...
    geoasn_data: Any = ...
    geocity_data: Any = ...
    def __init__(self, country: Any, country_code: Any, city: Any, postcode: Any, as_number: Any, as_name: Any, ip_address: Any, network: Any, long: Any, lat: Any, geoasn_data: Any, geocity_data: Any) -> None: ...
    def __lt__(self, other: Any) -> Any: ...
    def __le__(self, other: Any) -> Any: ...
    def __gt__(self, other: Any) -> Any: ...
    def __ge__(self, other: Any) -> Any: ...

def geolocate_ip(addr: IP_OR_STR, throw: Any=...) -> Optional[GeoIPResult]: ...
def geolocate_ips(*addrs: Any, throw: Any=...) -> Generator[Tuple[str, Optional[GeoIPResult]], None, None]: ...
cleanup_geoip = cleanup

def geoip_manager(geo_type: str=...) -> Optional[geoip2.database.Reader]: ...
