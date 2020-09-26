import asyncio
import socket
import ssl

from privex.helpers import settings
from privex.helpers.common import byteify, empty

from privex.helpers.net.util import generate_http_request, get_ssl_context, ip_is_v6, sock_ver

from privex.helpers.types import AnyNum, IP_OR_STR
from privex.helpers.net.dns import resolve_ip, resolve_ip_async
import logging

log = logging.getLogger(__name__)


def _ssl_context(kwargs, ssl_params=None):
    if not ssl_params:
        ssl_params = kwargs.pop(
            'ssl_params', dict(verify_cert=settings.SSL_VERIFY_CERT, check_hostname=settings.SSL_VERIFY_HOSTNAME)
        )
    return get_ssl_context(**ssl_params)


def _wrap_socket(s: socket.socket, kwargs: dict, host=None, wrap_params=None, ssl_params=None, ) -> ssl.SSLSocket:
    if not wrap_params:
        wrap_params = kwargs.pop('wrap_params', dict(
            server_hostname=kwargs.get('server_hostname', host),
            session=kwargs.get('session'),
            do_handshake_on_connect=kwargs.get('do_handshake_on_connect', True)
        ))
    ctx = _ssl_context(kwargs, ssl_params)
    return ctx.wrap_socket(s, **wrap_params)


def check_host(host: IP_OR_STR, port: AnyNum, version='any', throw=False, **kwargs) -> bool:
    """
    Test if the service on port ``port`` for host ``host`` is working. AsyncIO version: :func:`.check_host_async`

    Basic usage (services which send the client data immediately after connecting)::

        >>> check_host('hiveseed-se.privex.io', 2001)
        True
        >>> check_host('hiveseed-se.privex.io', 9991)
        False

    For some services, such as HTTP - it's necessary to transmit some data to the host before it will
    send a response. Using the ``send`` kwarg, you can transmit an arbitrary string/bytes upon connection.

    Sending data to ``host`` after connecting::

        >>> check_host('files.privex.io', 80, send=b"GET / HTTP/1.1\\n\\n")
        True


    :param str|IPv4Address|IPv6Address host: Hostname or IP to test
    :param int|str port: Port number on ``host`` to connect to
    :param str|int version: When connecting to a hostname, this can be set to ``'v4'``, ``'v6'`` or similar
                            to ensure the connection is via that IP version

    :param bool throw: (default: ``False``) When ``True``, will raise exceptions instead of returning ``False``
    :param kwargs: Additional configuration options (see below)

    :keyword int receive: (default: ``100``) Amount of bytes to attempt to receive from the server (``0`` to disable)
    :keyword bytes|str send: If ``send`` is specified, the data in ``send`` will be transmitted to the server before receiving.
    :keyword int stype: Socket type, e.g. :attr:`socket.SOCK_STREAM`

    :keyword float|int timeout: Socket timeout. If not passed, uses the default from :func:`socket.getdefaulttimeout`.
                                If the global default timeout is ``None``, then falls back to ``5.0``

    :raises socket.timeout: When ``throw=True`` and a timeout occurs.
    :raises socket.gaierror: When ``throw=True`` and various errors occur
    :raises ConnectionRefusedError: When ``throw=True`` and the connection was refused
    :raises ConnectionResetError: When ``throw=True`` and the connection was reset

    :return bool success: ``True`` if successfully connected + sent/received data. Otherwise ``False``.
    """
    kwargs = dict(kwargs)
    receive, stype = int(kwargs.get('receive', 100)), kwargs.get('stype', socket.SOCK_STREAM)
    timeout, send, use_ssl = kwargs.get('timeout', 'n/a'), kwargs.get('send'), kwargs.get('ssl', kwargs.get('use_ssl'))
    http_test, hostname = kwargs.get('http_test', False), kwargs.get('hostname', host)

    # ssl_params = kwargs.get('ssl_params', dict(verify_cert=False, check_hostname=False))
    if timeout == 'n/a':
        t = socket.getdefaulttimeout()
        timeout = settings.DEFAULT_SOCKET_TIMEOUT if not t else t
    if http_test:
        send = generate_http_request(url=kwargs.get('url', '/'), host=hostname)
    try:
        s_ver = socket.AF_INET
        ip = resolve_ip(host, version)
        
        if ip_is_v6(ip): s_ver = socket.AF_INET6
        
        if port == 443 and use_ssl is None:
            log.warning("check_host: automatically setting use_ssl=True as port is 443 and use_ssl was not specified.")
            use_ssl = True
        with socket.socket(s_ver, stype) as s:
            if use_ssl: s = _wrap_socket(s, kwargs, host)
            if timeout: s.settimeout(float(timeout))
            
            s.connect((ip, int(port)))
            if not empty(send):
                s.sendall(byteify(send))
            if receive > 0:
                s.recv(int(receive))
            if use_ssl:
                s.close()
        return True
    except (socket.timeout, TimeoutError, ConnectionRefusedError, ConnectionResetError, socket.gaierror) as e:
        if throw:
            raise e
    return False


async def check_host_async(host: IP_OR_STR, port: AnyNum, version='any', throw=False, **kwargs) -> bool:
    """
    AsyncIO version of :func:`.check_host`. Test if the service on port ``port`` for host ``host`` is working.

    Basic usage (services which send the client data immediately after connecting)::

        >>> await check_host_async('hiveseed-se.privex.io', 2001)
        True
        >>> await check_host_async('hiveseed-se.privex.io', 9991)
        False

    For some services, such as HTTP - it's necessary to transmit some data to the host before it will
    send a response. Using the ``send`` kwarg, you can transmit an arbitrary string/bytes upon connection.

    Sending data to ``host`` after connecting::

        >>> await check_host_async('files.privex.io', 80, send=b"GET / HTTP/1.1\\n\\n")
        True


    :param str|IPv4Address|IPv6Address host: Hostname or IP to test
    :param int|str port: Port number on ``host`` to connect to
    :param str|int version: When connecting to a hostname, this can be set to ``'v4'``, ``'v6'`` or similar
                            to ensure the connection is via that IP version

    :param bool throw: (default: ``False``) When ``True``, will raise exceptions instead of returning ``False``
    :param kwargs: Additional configuration options (see below)

    :keyword int receive: (default: ``100``) Amount of bytes to attempt to receive from the server (``0`` to disable)
    :keyword bytes|str send: If ``send`` is specified, the data in ``send`` will be transmitted to the server before receiving.
    :keyword int stype: Socket type, e.g. :attr:`socket.SOCK_STREAM`

    :keyword float|int timeout: Socket timeout. If not passed, uses the default from :func:`socket.getdefaulttimeout`.
                                If the global default timeout is ``None``, then falls back to ``5.0``

    :raises socket.timeout: When ``throw=True`` and a timeout occurs.
    :raises socket.gaierror: When ``throw=True`` and various errors occur
    :raises ConnectionRefusedError: When ``throw=True`` and the connection was refused
    :raises ConnectionResetError: When ``throw=True`` and the connection was reset

    :return bool success: ``True`` if successfully connected + sent/received data. Otherwise ``False``.
    """
    kwargs = dict(kwargs)
    receive, stype = int(kwargs.get('receive', 100)), kwargs.get('stype', socket.SOCK_STREAM)
    timeout, send, use_ssl = kwargs.get('timeout', 'n/a'), kwargs.get('send'), kwargs.get('ssl', kwargs.get('use_ssl'))
    http_test, hostname = kwargs.get('http_test', False), kwargs.get('hostname', host)
    
    if timeout == 'n/a':
        t = socket.getdefaulttimeout()
        timeout = 10.0 if not t else t
    
    loop = asyncio.get_event_loop()
    if http_test:
        send = generate_http_request(url=kwargs.get('url', '/'), host=hostname)
    if port == 443 and use_ssl is None:
        log.warning("check_host_async: automatically setting use_ssl=True as port is 443 and use_ssl was not specified.")
        use_ssl = True
    try:
        if sock_ver(version) is None:
            s_ver = socket.AF_INET
            host = await resolve_ip_async(host, version)
            if ip_is_v6(host): s_ver = socket.AF_INET6
        else:
            s_ver = sock_ver(version)
        
        with socket.socket(s_ver, stype) as s:
            if use_ssl: s = _wrap_socket(s, kwargs, host)
            if timeout:
                s.settimeout(float(timeout))
                await asyncio.wait_for(loop.sock_connect(s, (host, int(port))), timeout)
            else:
                await loop.sock_connect(s, (host, int(port)))
            
            if not empty(send):
                await loop.sock_sendall(s, byteify(send))
            if receive > 0:
                await loop.sock_recv(s, int(receive))
        return True
    except (socket.timeout, TimeoutError, ConnectionRefusedError, ConnectionResetError, socket.gaierror) as e:
        if throw:
            raise e
    return False
