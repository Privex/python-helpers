"""
General uncategorised functions/classes for network related helper code

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
import logging
import random
import socket
from datetime import datetime
from math import ceil
from typing import List, Tuple

from privex.helpers.decorators import r_cache, r_cache_async

from privex.helpers import settings
from privex.helpers.common import byteify, empty, empty_if, is_true
from privex.helpers.asyncx import run_coro_thread_async
from privex.helpers.net import base as netbase
from privex.helpers.net.dns import resolve_ip, resolve_ip_async
from privex.helpers.net.socket import AsyncSocketWrapper
from privex.helpers.net.util import get_ssl_context, ip_is_v6
from privex.helpers.types import AUTO, AnyNum, IP_OR_STR

log = logging.getLogger(__name__)

__all__ = [
    'check_host', 'check_host_async', 'check_host_http', 'check_host_http_async', 'test_hosts_async',
    'test_hosts', 'check_v4', 'check_v6', 'check_v4_async', 'check_v6_async'
]


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
    receive, stype = int(kwargs.get('receive', 100)), kwargs.get('stype', socket.SOCK_STREAM)
    timeout, send, use_ssl = kwargs.get('timeout', 'n/a'), kwargs.get('send'), kwargs.get('ssl', kwargs.get('use_ssl'))
    ssl_params = kwargs.get('ssl_params', dict(verify_cert=False, check_hostname=False))
    if timeout == 'n/a':
        t = socket.getdefaulttimeout()
        timeout = 10.0 if not t else t
    
    try:
        s_ver = socket.AF_INET
        ip = resolve_ip(host, version)
    
        if ip_is_v6(ip): s_ver = socket.AF_INET6
    
        if port == 443 and use_ssl is None:
            log.warning("check_host: automatically setting use_ssl=True as port is 443 and use_ssl was not specified.")
            use_ssl = True
        with socket.socket(s_ver, stype) as s:
            orig_sock = s
            if timeout: s.settimeout(float(timeout))
            if use_ssl:
                ctx = get_ssl_context(**ssl_params)
                s = ctx.wrap_socket(
                    s,
                    server_hostname=kwargs.get('server_hostname'),
                    session=kwargs.get('session'),
                    do_handshake_on_connect=kwargs.get('do_handshake_on_connect', True),
                )
                
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
    receive, stype = int(kwargs.get('receive', 16)), kwargs.get('stype', socket.SOCK_STREAM)
    timeout, send = kwargs.get('timeout', 'n/a'), kwargs.get('send')
    http_test, use_ssl = kwargs.get('http_test', False), kwargs.get('use_ssl', False)
    if timeout == 'n/a':
        t = socket.getdefaulttimeout()
        timeout = settings.DEFAULT_SOCKET_TIMEOUT if not t else t
    
    # loop = asyncio.get_event_loop()
    s_ver = socket.AF_INET
    ip = await resolve_ip_async(host, version)
    
    if ip_is_v6(ip): s_ver = socket.AF_INET6
    
    try:
        aw = AsyncSocketWrapper(host, int(port), family=s_ver, use_ssl=use_ssl, timeout=timeout)
        await aw.connect()
        if http_test:
            log.info("Sending HTTP request to %s", host)
            log.info("Response from %s : %s", host, await aw.http_request())
        
        elif not empty(send) and receive > 0:
            log.info("Sending query data '%s' and trying to receive data from %s", send, host)
            log.info("Response from %s : %s", host, await aw.query(send, receive, read_timeout=kwargs.get('read_timeout', AUTO)))
        
        elif not empty(send):
            log.info("Sending query data '%s' to %s", send, host)
            await aw.sendall(send)
        else:
            log.info("Receiving data from %s", host)
            
            log.info("Response from %s : %s", host, await aw.read_eof(
                receive, strip=False, read_timeout=kwargs.get('read_timeout', AUTO),
            ))
        
        # with socket.socket(s_ver, stype) as s:
        #     if timeout: s.settimeout(float(timeout))
        #     await loop.sock_connect(s, (ip, int(port)))
        #     if not empty(send):
        #         await loop.sock_sendall(s, byteify(send))
        #     if receive > 0:
        #         await loop.sock_recv(s, int(receive))
        return True
    except (socket.timeout, TimeoutError, ConnectionRefusedError, ConnectionResetError, socket.gaierror) as e:
        if throw:
            raise e
    return False


def check_host_http(host: IP_OR_STR, port: AnyNum = 80, version='any', throw=False, **kwargs) -> bool:
    return netbase.check_host(host, port, version, throw=throw, http_test=True, **kwargs)


async def check_host_http_async(
            host: IP_OR_STR, port: AnyNum = 80, version='any', throw=False, send=b"GET / HTTP/1.1\\n\\n", **kwargs
        ) -> bool:
    # return await check_host_async(host, port, version, throw=throw, send=send, **kwargs)
    return await netbase.check_host_async(host, port, version, throw=throw, http_test=True, **kwargs)


async def test_hosts_async(hosts: List[str] = None, ipver: str = 'any', timeout: AnyNum = None, **kwargs) -> bool:
    randomise = is_true(kwargs.get('randomise', True))
    max_hosts = kwargs.get('max_hosts', settings.NET_CHECK_HOST_COUNT_TRY)
    if max_hosts is not None: max_hosts = int(max_hosts)
    timeout = empty_if(timeout, empty_if(socket.getdefaulttimeout(), 4, zero=True), zero=True)
    
    v4h, v6h = list(settings.V4_TEST_HOSTS), list(settings.V6_TEST_HOSTS)
    if randomise: random.shuffle(v4h)
    if randomise: random.shuffle(v6h)
    
    if empty(hosts, True, True):
        # if empty(ipver, True, True) or ipver in ['any', 'all', 'both', 10, '10', '46', 46]:
        #     settings.V4_CHECKED_AT
        if isinstance(ipver, str): ipver = ipver.lower()
        if ipver in [4, '4', 'v4', 'ipv4']:
            hosts = v4h
            ipver = 4
        elif ipver in [6, '6', 'v6', 'ipv6']:
            hosts = v6h
            ipver = 6
        else:
            ipver = 'any'
            if max_hosts:
                hosts = v4h[:int(ceil(max_hosts / 2))] + v6h[:int(ceil(max_hosts / 2))]
            else:
                hosts = v4h + v6h
    
    if max_hosts: hosts = hosts[:max_hosts]
    
    # st4_empty = any([empty(settings.HAS_WORKING_V4, True, True), empty(settings.V4_CHECKED_AT, True, True)])
    # st6_empty = any([empty(settings.HAS_WORKING_V6, True, True), empty(settings.V6_CHECKED_AT, True, True)])
    
    # if ipver == 6 and not st6_empty and settings.V6_CHECKED_AT > datetime.utcnow():
    #     # if settings.V6_CHECKED_AT > datetime.utcnow()
    #     log.debug("Returning cached IPv6 status: working = %s", settings.HAS_WORKING_V6)
    #     return settings.HAS_WORKING_V6
    # if ipver == 4 and not st4_empty and settings.V4_CHECKED_AT > datetime.utcnow():
    #     # if settings.V6_CHECKED_AT > datetime.utcnow()
    #     log.debug("Returning cached IPv4 status: working = %s", settings.HAS_WORKING_V4)
    #     return settings.HAS_WORKING_V4
    #
    # if ipver == 'any' and any([not st4_empty, not st6_empty]) and settings.V4_CHECKED_AT > datetime.utcnow():
    #     # if settings.V6_CHECKED_AT > datetime.utcnow()
    #     if st4_empty:
    #         log.debug("test_hosts being requested for 'any' ip ver. IPv6 status cached, but not IPv4 status. Checking IPv4 status...")
    #         await check_v4_async()
    #     if st6_empty:
    #         log.debug("test_hosts being requested for 'any' ip ver. IPv4 status cached, but not IPv6 status. Checking IPv6 status...")
    #         await check_v6_async(hosts)
    #     # if not st4_empty and not st6_empty:
    #     log.debug(
    #         "Returning status %s based on: Working IPv4 = %s || Working IPv6 = %s",
    #         settings.HAS_WORKING_V4 or settings.HAS_WORKING_V6, settings.HAS_WORKING_V4, settings.HAS_WORKING_V6
    #     )
    #     return settings.HAS_WORKING_V4 or settings.HAS_WORKING_V6
    
    # max_hosts = int(kwargs.get('max_hosts', settings.NET_CHECK_HOST_COUNT_TRY))
    min_hosts_pos = int(kwargs.get('required_positive', settings.NET_CHECK_HOST_COUNT))
    
    # hosts = empty_if(hosts, settings.V4_TEST_HOSTS, itr=True)
    hosts = [x for x in hosts]
    
    if randomise: random.shuffle(hosts)
    
    if len(hosts) > max_hosts: hosts = hosts[:max_hosts]
    
    # port = empty_if(port, 80, zero=True)
    
    total_hosts = len(hosts)
    total_working, total_broken = 0, 0
    working_list, broken_list = [], []
    log.debug("Testing %s hosts with IP version '%s' - timeout: %s", total_hosts, ipver, timeout)

    host_checks = []
    host_checks_hosts = []
    for h in hosts:
        # host_checks.append(
        #     asyncio.create_task(_test_host_async(h, ipver=ipver, timeout=timeout))
        # )
        host_checks.append(
            asyncio.create_task(
                run_coro_thread_async(_test_host_async, h, ipver=ipver, timeout=timeout)
            )
        )
        host_checks_hosts.append(h)

    host_checks_res = await asyncio.gather(*host_checks, return_exceptions=True)
    for i, _res in enumerate(host_checks_res):
        h = host_checks_hosts[i]
        if isinstance(_res, Exception):
            log.warning("Exception while checking host %s", h)
            total_broken += 1
            continue

        res, h, port = _res
    
        if res:
            total_working += 1
            working_list.append(f"{h}:{port}")
            log.debug("check_host for %s (port %s) came back True (WORKING). incremented working hosts: %s", h, port, total_working)
        else:
            total_broken += 1
            broken_list.append(f"{h}:{port}")
            log.debug("check_host for %s (port %s) came back False (! BROKEN !). incremented broken hosts: %s", h, port, total_broken)

    # port = 80
    # for h in hosts:
    #     try:
    #         h, port, res = await _test_host_async(h, ipver, timeout)
    #         if res:
    #             total_working += 1
    #             log.debug("check_host for %s came back true. incremented working hosts: %s", h, total_working)
    #         else:
    #             total_broken += 1
    #             log.debug("check_host for %s came back false. incremented broken hosts: %s", h, total_broken)
    #
    #     except Exception as e:
    #         log.warning("Exception while checking host %s port %s", h, port)
    
    working = total_working >= min_hosts_pos
    
    log.info("test_hosts - proto: %s - protocol working? %s || total hosts: %s || working hosts: %s || broken hosts: %s",
             ipver, working, total_hosts, total_working, total_broken)
    log.debug("working hosts: %s", working_list)
    log.debug("broken hosts: %s", broken_list)
    
    return working


async def _test_host_async(host, ipver: str = 'any', timeout: AnyNum = None) -> Tuple[bool, str, int]:
    nh = host.split(':')
    if len(nh) > 1:
        port = int(nh[-1])
        host = ':'.join(nh[:-1])
    else:
        host = ':'.join(nh)
        log.warning("Host is missing port: %s - falling back to port 80")
        port = 80
    log.debug("Checking host %s via port %s + IP version '%s'", host, port, ipver)
    if port == 80:
        res = await check_host_http_async(host, port, ipver, throw=False, timeout=timeout)
    elif port == 53:
        res = await netbase.check_host_async(host, port, ipver, throw=False, timeout=timeout, send="hello\nworld\n")
    else:
        res = await netbase.check_host_async(host, port, ipver, throw=False, timeout=timeout)
    return res, host, port


def test_hosts(hosts: List[str] = None, ipver: str = 'any', timeout: AnyNum = None, **kwargs) -> bool:
    randomise = is_true(kwargs.get('randomise', True))
    max_hosts = kwargs.get('max_hosts', settings.NET_CHECK_HOST_COUNT_TRY)
    if max_hosts is not None: max_hosts = int(max_hosts)
    timeout = empty_if(timeout, empty_if(socket.getdefaulttimeout(), 4, zero=True), zero=True)

    v4h, v6h = list(settings.V4_TEST_HOSTS), list(settings.V6_TEST_HOSTS)
    if randomise: random.shuffle(v4h)
    if randomise: random.shuffle(v6h)

    if empty(hosts, True, True):
        # if empty(ipver, True, True) or ipver in ['any', 'all', 'both', 10, '10', '46', 46]:
        #     settings.V4_CHECKED_AT
        if isinstance(ipver, str): ipver = ipver.lower()
        if ipver in [4, '4', 'v4', 'ipv4']:
            hosts = v4h
            ipver = 4
        elif ipver in [6, '6', 'v6', 'ipv6']:
            hosts = v6h
            ipver = 6
        else:
            ipver = 'any'
            if max_hosts:
                hosts = v4h[:int(ceil(max_hosts / 2))] + v6h[:int(ceil(max_hosts / 2))]
            else:
                hosts = v4h + v6h

    if max_hosts: hosts = hosts[:max_hosts]
    
    # st4_empty = any([empty(settings.HAS_WORKING_V4, True, True), empty(settings.V4_CHECKED_AT, True, True)])
    # st6_empty = any([empty(settings.HAS_WORKING_V6, True, True), empty(settings.V6_CHECKED_AT, True, True)])

    # if ipver == 6 and not st6_empty and settings.V6_CHECKED_AT > datetime.utcnow():
    #     # if settings.V6_CHECKED_AT > datetime.utcnow()
    #     log.debug("Returning cached IPv6 status: working = %s", settings.HAS_WORKING_V6)
    #     return settings.HAS_WORKING_V6
    # if ipver == 4 and not st4_empty and settings.V4_CHECKED_AT > datetime.utcnow():
    #     # if settings.V6_CHECKED_AT > datetime.utcnow()
    #     log.debug("Returning cached IPv4 status: working = %s", settings.HAS_WORKING_V4)
    #     return settings.HAS_WORKING_V4

    # if ipver == 'any' and any([not st4_empty, not st6_empty]) and settings.V4_CHECKED_AT > datetime.utcnow():
    #     # if settings.V6_CHECKED_AT > datetime.utcnow()
    #     if st4_empty:
    #         log.debug("test_hosts being requested for 'any' ip ver. IPv6 status cached, but not IPv4 status. Checking IPv4 status...")
    #         check_v4()
    #     if st6_empty:
    #         log.debug("test_hosts being requested for 'any' ip ver. IPv4 status cached, but not IPv6 status. Checking IPv6 status...")
    #         check_v6()
    #     # if not st4_empty and not st6_empty:
    #     log.debug(
    #         "Returning status %s based on: Working IPv4 = %s || Working IPv6 = %s",
    #         settings.HAS_WORKING_V4 or settings.HAS_WORKING_V6, settings.HAS_WORKING_V4, settings.HAS_WORKING_V6
    #     )
    #     return settings.HAS_WORKING_V4 or settings.HAS_WORKING_V6

    # max_hosts = int(kwargs.get('max_hosts', settings.NET_CHECK_HOST_COUNT_TRY))
    min_hosts_pos = int(kwargs.get('required_positive', settings.NET_CHECK_HOST_COUNT))
    
    # hosts = empty_if(hosts, settings.V4_TEST_HOSTS, itr=True)
    hosts = [x for x in hosts]
    
    if randomise: random.shuffle(hosts)
    
    if len(hosts) > max_hosts: hosts = hosts[:max_hosts]
    
    
    total_hosts = len(hosts)
    total_working, total_broken = 0, 0

    log.debug("Testing %s hosts with IP version '%s' - timeout: %s", total_hosts, ipver, timeout)
    port = 80
    
    for h in hosts:
        try:
            nh = h.split(':')
            if len(nh) > 1:
                port = int(nh[-1])
                h = ':'.join(nh[:-1])
            else:
                h = ':'.join(nh)
                log.warning("Host is missing port: %s - falling back to port 80")
                port = 80
    
            log.debug("Checking host %s via port %s + IP version '%s'", h, port, ipver)

            if port == 80:
                res = check_host_http(h, port, ipver, throw=False, timeout=timeout)
            else:
                res = check_host(h, port, ipver, throw=False, timeout=timeout)
            if res:
                total_working += 1
                log.debug("check_host for %s came back true. incremented working hosts: %s", h, total_working)
            else:
                total_broken += 1
                log.debug("check_host for %s came back false. incremented broken hosts: %s", h, total_broken)

        except Exception as e:
            log.warning("Exception while checking host %s port %s", h, port)
    
    working = total_working >= min_hosts_pos
    
    log.info("test_hosts - proto: %s - protocol working? %s || total hosts: %s || working hosts: %s || broken hosts: %s",
             ipver, working, total_hosts, total_working, total_broken)
    
    return working


@r_cache("pvxhelpers:check_v4", settings.NET_CHECK_TIMEOUT)
def check_v4(hosts: List[str] = None, *args, **kwargs) -> bool:
    """Check and cache whether IPv4 is functional by testing a handful of IPv4 hosts"""
    return test_hosts(hosts, ipver='v4', *args, **kwargs)


@r_cache("pvxhelpers:check_v6", settings.NET_CHECK_TIMEOUT)
def check_v6(hosts: List[str] = None, *args, **kwargs) -> bool:
    """Check and cache whether IPv6 is functional by testing a handful of IPv6 hosts"""
    return test_hosts(hosts, ipver='v6', *args, **kwargs)


@r_cache_async("pvxhelpers:check_v4", settings.NET_CHECK_TIMEOUT)
async def check_v4_async(hosts: List[str] = None, *args, **kwargs) -> bool:
    """(Async ver of :func:`.check_v4`) Check and cache whether IPv4 is functional by testing a handful of IPv4 hosts"""
    return await test_hosts_async(hosts, ipver='v4', *args, **kwargs)


@r_cache_async("pvxhelpers:check_v6", settings.NET_CHECK_TIMEOUT)
async def check_v6_async(hosts: List[str] = None, *args, **kwargs) -> bool:
    """(Async ver of :func:`.check_v6`) Check and cache whether IPv6 is functional by testing a handful of IPv6 hosts"""
    return await test_hosts_async(hosts, ipver='v6', *args, **kwargs)
