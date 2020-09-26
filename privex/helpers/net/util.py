import platform
import socket
import ssl
import subprocess
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network, ip_address, ip_network
from typing import List, Optional, Union
from privex.helpers import settings
from privex.helpers.common import empty_if, byteify, is_true, stringify
from privex.helpers.exceptions import NetworkUnreachable
from privex.helpers.types import IP_OR_STR, STRBYTES

__all__ = [
    'ip_is_v4', 'ip_is_v6', 'ping', 'IPV4_ALIASES', 'IPV6_ALIASES', 'ip_ver_to_int', 'ip_ver_to_sock',
    'sock_ver', 'is_ip', 'sock_validate_ip'
]


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


IPV4_ALIASES = [4, 'v4', '4', 'ipv4', 'ip4', 'inet', 'inet4', socket.AF_INET, str(socket.AF_INET)]
IPV6_ALIASES = [6, 'v6', '6', 'ipv6', 'ip6', 'inet6', socket.AF_INET6, str(socket.AF_INET6)]


def ip_ver_to_int(ver: Union[str, int]) -> int:
    ver = str(ver).lower()
    if ver in IPV4_ALIASES: return 4
    if ver in IPV6_ALIASES: return 6
    return 0


def sock_ver(version) -> Optional[int]:
    version = empty_if(version, 'any', zero=True, itr=True)
    version = str(version).lower()
    if ip_ver_to_int(version) == 4: return socket.AF_INET
    if ip_ver_to_int(version) == 6: return socket.AF_INET6
    return None


ip_ver_to_sock = sock_ver


def ip_sock_ver(ip_addr) -> Optional[int]:
    a = ip_network(ip_addr, strict=False)
    if isinstance(a, (IPv4Address, IPv4Network)): return socket.AF_INET
    if isinstance(a, (IPv6Address, IPv6Network)): return socket.AF_INET6
    return None


def is_ip(addr: str, version: int = None):
    try:
        res = sock_validate_ip(addr, version=version)
        return res
    except AttributeError as e:
        raise e
    except ValueError:
        return False


def sock_validate_ip(addr: IP_OR_STR, version: int, throw=True) -> Optional[Union[IPv4Address, IPv4Address]]:
    ip = ip_address(addr)
    ver = "v4" if ip_is_v4(ip) else "v6"
    if version == socket.AF_INET and ver != 'v4':
        if not throw: return None
        raise AttributeError(f"Passed address '{addr}' was an IPv6 address, but 'version' requested an IPv4 address.")
    if version == socket.AF_INET6 and ver != 'v6':
        if not throw: return None
        raise AttributeError(f"Passed address '{addr}' was an IPv4 address, but 'version' requested an IPv6 address.")
    return ip


def get_ssl_context(
            verify_cert: bool = False, check_hostname: Optional[bool] = None, verify_mode: Optional[int] = None, **kwargs
        ) -> ssl.SSLContext:
    check_hostname = empty_if(check_hostname, is_true(verify_cert))
    verify_mode = empty_if(verify_mode, ssl.CERT_REQUIRED if verify_cert else ssl.CERT_NONE)
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = check_hostname
    ctx.verify_mode = verify_mode
    return ctx


def generate_http_request(
    url="/", host=None, method="GET", user_agent=settings.DEFAULT_USER_AGENT, extra_data: Union[STRBYTES, List[str]] = None,
    body: STRBYTES = None, **kwargs
) -> bytes:
    method, url = stringify(method), stringify(url)
    http_ver = stringify(kwargs.get('http_ver', '1.0'))
    data = f"{method.upper()} {url} HTTP/{http_ver}\n"
    if host is not None: data += f"Host: {stringify(host)}\n"
    if user_agent is not None: data += f"User-Agent: {stringify(user_agent)}\n"
    data = byteify(data)
    
    if extra_data is not None:
        if isinstance(extra_data, list):
            extra_data = [byteify(x) for x in extra_data]
            data += b"\n".join(extra_data)
        else:
            data += byteify(extra_data)
        if not data.endswith(b"\n"): data += b"\n"
    
    if body is not None:
        data += byteify(body)
    if not data.endswith(b"\n"): data += b"\n"
    if not data.endswith(b"\n\n"): data += b"\n"
    return data
