"""
Various wrapper functions/classes which use :mod:`socket` or are strongly tied to functions in this file
which use :mod:`socket`. Part of :mod:`privex.helpers.net` - network related helper code.

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
import functools
import socket
import ssl
import time
from ipaddress import ip_network
from typing import Any, Callable, Generator, IO, Iterable, List, Optional, Tuple, Union

import attr

from privex.helpers import settings
from privex.helpers.common import LayeredContext, byteify, empty, empty_if, is_true, stringify, strip_null
from privex.helpers.thread import SafeLoopThread
from privex.helpers.asyncx import await_if_needed, run_coro_thread
from privex.helpers.net.util import generate_http_request, get_ssl_context, ip_is_v6, ip_sock_ver, is_ip
from privex.helpers.net.dns import resolve_ip, resolve_ip_async
from privex.helpers.types import AUTO, AUTO_DETECTED, AnyNum, STRBYTES, T

import logging

log = logging.getLogger(__name__)

__all__ = [
    'AnySocket', 'OpAnySocket', 'SocketContextManager',
    'StopLoopOnMatch', 'SocketWrapper', 'AsyncSocketWrapper', 'send_data_async', 'send_data', 'upload_termbin',
    'upload_termbin_file', 'upload_termbin_async', 'upload_termbin_file_async'
]

AnySocket = Union[ssl.SSLSocket, "socket.socket"]
OpAnySocket = Optional[Union[ssl.SSLSocket, "socket.socket"]]


class SocketContextManager:
    parent_class: Union["SocketWrapper", "AsyncSocketWrapper"]
    
    def __init__(self, parent_class: Union["SocketWrapper", "AsyncSocketWrapper"]):
        self.parent_class = parent_class
    
    def __enter__(self) -> "SocketWrapper":
        log.debug("Entering SocketContextManager")
        self.parent_class.reconnect()
        return self.parent_class
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        log.debug("Exiting SocketContextManager")
        self.parent_class.close()

    async def __aenter__(self) -> "AsyncSocketWrapper":
        log.debug("[async] Entering SocketContextManager")
        await self.parent_class.reconnect()
        return self.parent_class

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        log.debug("[async] Exiting SocketContextManager")
        self.parent_class.close()


class StopLoopOnMatch(Exception):
    def __init__(self, message: str, match: Any = None, compare: str = None, compare_lower: bool = True, **extra):
        self.message = message
        self.match = match
        self.compare = compare
        self.compare_lower = compare_lower
        self.extra = extra
        super().__init__(message)


def _sockwrapper_auto_connect(new_sock: bool = False):
    def _decorator(f):
        @functools.wraps(f)
        def wrapper(self: Union["SocketWrapper"], *args, _sock_tries=0, **kwargs):
            kwargs = dict(kwargs)
            gensock = None
            if kwargs.pop('new_sock', new_sock):
                log.debug("new_sock is true for call to function %s - generating socket to kwarg 'sock'...", f.__name__)
                # kwargs['sock'] = self._select_socket(new_sock=True)
                gensock = SocketTracker.duplicate(self.tracker)
            elif 'sock' in kwargs and kwargs['sock'] not in [None, False, '']:
                gensock = kwargs.pop('sock')
                
            if gensock not in [None, False, '']:
                
                log.debug("'sock' is present for call to function %s...", f.__name__)
                with gensock as sck:
                    log.debug('ensuring socket is open (inside with). now connecting socket.')
                    try:
                        # self.connect(host=kwargs.get('host'), port=kwargs.get('port'), sock=sck)
                        kwargs['sock'] = sck
                    except OSError as e:
                        if 'already connected' in str(e):
                            log.debug('socket already connected. continuing.')
                    log.debug('socket should now be connected. calling function %s', f.__name__)
                    return f(self, *args, **kwargs)
            
            if not self.connected:
                log.debug('instance socket is not connected ( calling function %s )', f.__name__)
    
                if not self.auto_connect:
                    raise ConnectionError(
                        "Would've auto-connected SocketWrapper, but self.auto_connect is False. Please call connect before "
                        "interacting with the socket."
                    )
                if any([empty(self.host, zero=True), empty(self.port, zero=True)]):
                    raise ConnectionError("Tried to auto-connect SocketWrapper, but self.host and/or self.port are empty!")
                log.debug('connecting instance socket ( calling function %s )', f.__name__)
                # self.connect(self.host, self.port)
                self.tracker.connect()
            try:
                _sock_tries += 1
                return f(self, *args, **kwargs)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError) as e:
                if self.error_reconnect and _sock_tries < 3:
                    log.error("The socket appears to have broken. Resetting and trying again. Error was: %s - %s", type(e), str(e))
                    self.tracker.reconnect()
                    return wrapper(self, *args, _sock_tries=_sock_tries, **kwargs)
                raise e
        return wrapper
    return _decorator


def _async_sockwrapper_auto_connect():
    def _decorator(f):
        @functools.wraps(f)
        async def wrapper(self: Union["AsyncSocketWrapper"], *args, _sock_tries=0, **kwargs):
            if not self.tracker.connected:
                if not self.auto_connect:
                    raise ConnectionError(
                        "Would've auto-connected AsyncSocketWrapper, but self.auto_connect is False. Please call connect before "
                        "interacting with the socket."
                    )

                if any([empty(self.host, zero=True), empty(self.port, zero=True)]):
                    raise ConnectionError("Tried to auto-connect AsyncSocketWrapper, but self.host and/or self.port are empty!")
                # await self.connect(self.host, self.port)
                await self.tracker.connect_async()
            try:
                _sock_tries += 1
                return await f(self, *args, **kwargs)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError) as e:
                log.error("The socket appears to have broken. Error was: %s - %s", type(e), str(e))
                if self.error_reconnect and _sock_tries < 3:
                    log.error("Resetting the connection and trying again...")
                    await self.tracker.reconnect_async()
                    return await wrapper(self, *args, _sock_tries=_sock_tries, **kwargs)
                raise e
        return wrapper
    return _decorator


class MockContext:
    def __enter__(self):
        # return self.auto_socket
        return "yes"
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def __aenter__(self):
        return "yes"
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@attr.s
class SocketTracker:
    """
    Data class used by :class:`.SocketWrapper` / :class:`.AsyncSocketWrapper` for managing sockets
    """
    host: str = attr.ib()
    port: int = attr.ib(converter=int)
    timeout: Union[int, float] = attr.ib(factory=lambda: settings.DEFAULT_SOCKET_TIMEOUT)
    server: bool = attr.ib(default=False, converter=is_true)
    connected: bool = attr.ib(default=False, converter=is_true)
    binded: bool = attr.ib(default=False, converter=is_true)
    listening: bool = attr.ib(default=False, converter=is_true)
    use_ssl: bool = attr.ib(default=False, converter=is_true)
    socket_conf: dict = attr.ib(factory=dict)
    ssl_conf: dict = attr.ib(factory=dict)
    ssl_wrap_conf: dict = attr.ib(factory=dict)
    hostname: str = attr.ib(default=None)
    _ssl_context: ssl.SSLContext = attr.ib(default=None)
    _ssl_socket: ssl.SSLSocket = attr.ib(default=None)
    _loop: asyncio.AbstractEventLoop = attr.ib(default=None)
    _socket: AnySocket = attr.ib(default=None)
    _socket_layer_ctx = attr.ib(default=None)
    
    _host_v4: Optional[str] = attr.ib(default=None)
    _host_v6: Optional[str] = attr.ib(default=None)
    
    _host_v4_resolved: bool = attr.ib(default=False)
    _host_v6_resolved: bool = attr.ib(default=False)
    
    def __attrs_post_init__(self):
        self.hostname = empty_if(self.hostname, self.host, zero=True)
    
    @property
    def family(self) -> int:
        return self.socket_conf.get('family', -1)
    
    @family.setter
    def family(self, value: int):
        self.socket_conf['family'] = value
    
    @property
    def host_v4(self) -> Optional[str]:
        if not self._host_v4_resolved:
            self._host_v4 = resolve_ip(self.host, 'v4')
            self._host_v4_resolved = True
        return self._host_v4

    @property
    def host_v6(self) -> Optional[str]:
        if not self._host_v6_resolved:
            self._host_v6 = resolve_ip(self.host, 'v6')
            self._host_v6_resolved = True
        return self._host_v6
    
    @property
    def socket(self):
        if not self._socket:
            self._socket = socket.socket(**self.socket_conf)
        return self._socket
    
    @socket.setter
    def socket(self, value):
        pass

    @property
    def socket_layer_ctx(self):
        if not self._socket_layer_ctx:
            self._socket_layer_ctx = LayeredContext(MockContext())
        return self._socket_layer_ctx
    
    @socket_layer_ctx.setter
    def socket_layer_ctx(self, value):
        self._socket_layer_ctx = value

    def _make_context(self, **kwargs) -> ssl.SSLContext:
        cnf = {**self.ssl_conf, **kwargs}
        return get_ssl_context(**cnf)
    
    @property
    def ssl_context(self):
        if not self._ssl_context:
            self._ssl_context = self._make_context()
        return self._ssl_context
    
    @ssl_context.setter
    def ssl_context(self, value):
        self._ssl_context = value
    
    @property
    def ssl_socket(self):
        if not self._ssl_socket:
            self._ssl_socket = self.ssl_context.wrap_socket(self.socket, **self.ssl_wrap_conf)
        return self._ssl_socket
    
    @ssl_socket.setter
    def ssl_socket(self, value):
        self._ssl_socket = value

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        if not self._loop:
            self._loop = asyncio.get_event_loop()
        return self._loop
    
    @property
    def _auto_socket(self):
        return self.ssl_socket if self.use_ssl else self.socket
    
    @property
    def auto_socket(self) -> AnySocket:
        if not self.connected: self.connect()
        return self._auto_socket

    @property
    def ip_address(self):
        try:
            if empty(self._auto_socket) or empty(self._auto_socket.getpeername()):
                return None
        except Exception as e:
            log.warning("Error while getting peername: %s %s", type(e), str(e))
            return None
        return self._auto_socket.getpeername()[0]
    connected_ip = ip_address
    
    @property
    def connected_port(self):
        try:
            if empty(self._auto_socket) or empty(self._auto_socket.getpeername()):
                return None
        except Exception as e:
            log.warning("Error while getting peername: %s %s", type(e), str(e))
            return None
        return self._auto_socket.getpeername()[1]

    def bind(self, address: Tuple[str, AnyNum] = None, force=False, **kwargs):
        if self.binded and not force:
            return self.auto_socket
        self.auto_socket.bind(address)
        self.binded = True
        return self.auto_socket

    def listen(self, backlog: int = 10, force=False, **kwargs):
        s = self.auto_socket
        if self.listening and not force:
            return s
        self.auto_socket.listen(backlog)
        self.listening = True
        return self.auto_socket
    
    def post_connect(self, sock: AnySocket):
        log.debug("[%s.%s] Connected to host: %s", __name__, self.__class__.__name__, sock.getpeername())
        sock.settimeout(self.timeout)
        return sock
    
    def v6_fallback(self, ex: Exception = None) -> bool:
        ip = self.ip_address
        if self.family == socket.AF_INET6 or (self.family != socket.AF_INET and not empty(ip) and ip_is_v6(ip)):
            if self.host_v4:
                if ex:
                    log.warning(
                        "[%s.%s] Error while using IPv6. Falling back to v4. %s %s",
                        __name__, self.__class__.__name__, type(ex), str(ex)
                    )
                self.family = socket.AF_INET
                return True
        return False
    
    def connect(self, force=False, override_ssl=None, _conn_tries=0) -> AnySocket:
        if not self.connected or force:
            sock = self.socket
            if self.use_ssl and override_ssl in [None, True]:
                sock = self.ssl_socket
            log.debug("[%s.%s] Connecting to host %s on port %s", __name__, self.__class__.__name__, self.host, self.port)

            # log.debug("Connecting to host %s on port %s", self.host, self.port)
            try:
                _conn_tries += 1
                sock.settimeout(self.timeout)
                sock.connect((self.host, self.port))
            except OSError as e:
                if 'already connected' in str(e):
                    log.debug("[%s.%s] Got OSError. Already connected. %s - %s", __name__, self.__class__.__name__, type(e), str(e))
                    self.connected = True
                    return self.post_connect(self.auto_socket)
                if _conn_tries >= 3:
                    raise e
                if not self.v6_fallback(e):
                    log.warning("[%s.%s] Got OSError. Resetting. %s - %s", __name__, self.__class__.__name__, type(e), str(e))
                # self._socket = None
                return self.reconnect(force=True, override_ssl=override_ssl, _conn_tries=_conn_tries)
            # sock.settimeout(self.timeout)
            self.connected = True
            if self.use_ssl:
                self.ssl_socket = sock
            else:
                self.socket = sock
            return self.post_connect(sock)
        sock = self.ssl_socket if self.use_ssl and override_ssl in [None, True] else self.socket
        return self.post_connect(sock)

    def reconnect(self, force=True, override_ssl=None, _conn_tries=0) -> AnySocket:
        if self.connected or force:
            self.disconnect()
        return self.connect(force=True, override_ssl=override_ssl, _conn_tries=_conn_tries)

    async def reconnect_async(self, force=True, override_ssl=None, _conn_tries=0) -> AnySocket:
        if self.connected or force:
            self.disconnect()
        return await self.connect_async(force=True, override_ssl=override_ssl, _conn_tries=_conn_tries)

    async def connect_async(self, force=False, override_ssl=None, _conn_tries=0) -> AnySocket:
        if not self.connected or force:
            sock = self.socket
            if self.use_ssl and override_ssl in [None, True]:
                sock = self.ssl_socket
            log.debug("[async] [%s.%s] Connecting to host %s on port %s (timeout: %s)", __name__, self.__class__.__name__,
                      self.host, self.port, self.timeout)
            try:
                _conn_tries += 1
                sock.settimeout(self.timeout)
                await asyncio.wait_for(self.loop.sock_connect(sock, (self.host, self.port)), self.timeout + 0.1)
            except (OSError, asyncio.TimeoutError) as e:
                if 'already connected' in str(e):
                    log.debug("[%s.%s] Got OSError. Already connected. %s - %s", __name__, self.__class__.__name__, type(e), str(e))
                    self.connected = True
                    return self.post_connect(self.auto_socket)
                if _conn_tries >= 3:
                    raise e
                if not self.v6_fallback(e):
                    log.warning("[%s.%s] Got OSError. Resetting. %s - %s", __name__, self.__class__.__name__, type(e), str(e))
                # self._socket = None
                return await self.reconnect_async(force=True, override_ssl=override_ssl, _conn_tries=_conn_tries)
            # sock.settimeout(self.timeout)
            self.connected = True
        sock = self.ssl_socket if self.use_ssl and override_ssl in [None, True] else self.socket
        return self.post_connect(sock)

    def _shutdown(self, sck):
        try:
            sck.shutdown(socket.SHUT_RDWR)
        except OSError as e:
            if 'not connected' in str(e): return
            log.warning("OSError while shutting down socket: %s %s", type(e), str(e))
        except Exception as e:
            log.warning("Exception while shutting down socket: %s %s", type(e), str(e))

    def _close(self, sck):
        try:
            sck.close()
        except OSError as e:
            log.warning("OSError while closing socket: %s %s", type(e), str(e))
        except Exception as e:
            log.warning("Exception while closing socket: %s %s", type(e), str(e))
    
    def disconnect(self):
        self.connected, self.binded, self.listening = False, False, False
        try:
            log.debug("[%s.%s] Disconnecting socket for host %s on port %s", __name__, self.__class__.__name__, self.host, self.port)
    
            # log.debug()
            if self._socket:
                self._shutdown(self._socket)
                self._close(self._socket)
                # try:
                #     self._socket.shutdown(socket.SHUT_RDWR)
                # except OSError as e:
                #     log.warning("OSError while shutting down socket: %s %s", type(e), str(e))
                # except Exception as e:
                #     log.warning("Exception while shutting down socket: %s %s", type(e), str(e))
                # self._socket.close()
                self._socket = None
            if self._ssl_socket:
                self._shutdown(self._ssl_socket)
                self._close(self._ssl_socket)
                # self._ssl_socket.shutdown(socket.SHUT_RDWR)
                # self._ssl_socket.close()
                self._ssl_socket = None
            return True
        except Exception:
            log.exception("error while closing socket")
            return False
    
    @classmethod
    def duplicate(cls, inst: "SocketTracker", **kwargs) -> "SocketTracker":
        cfg = dict(
            host=inst.host, port=inst.port, timeout=inst.timeout, server=inst.server, use_ssl=inst.use_ssl,
            socket_conf=inst.socket_conf, ssl_conf=inst.ssl_conf, ssl_wrap_conf=inst.ssl_wrap_conf
        )
        cfg = {**cfg, **kwargs}
        return cls(**cfg)
    
    def __enter__(self):
        if self.socket_layer_ctx.virtual_layer == 0:
            self._socket_layer_ctx = None
            if self.connected:
                self.reconnect()
        elif not self.connected: self.connect()
        # return self.auto_socket
        self.socket_layer_ctx.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.socket_layer_ctx.virtual_layer <= 1:
            self.disconnect()
        self.socket_layer_ctx.__exit__(exc_type, exc_val, exc_tb)
        # return self.auto_socket

    async def __aenter__(self):
        if self.socket_layer_ctx.virtual_layer == 0:
            self._socket_layer_ctx = None
            if self.connected:
                await self.reconnect_async()
        elif not self.connected: await self.connect_async()
        # return self.auto_socket
        await self.socket_layer_ctx.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # self.disconnect()
        if self.socket_layer_ctx.virtual_layer <= 1:
            self.disconnect()
        await self.socket_layer_ctx.__aexit__(exc_type, exc_val, exc_tb)

    def __getattr__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError:
            pass
        sock: AnySocket = super().__getattribute__('auto_socket')
        return getattr(sock, item)
    

class SocketWrapper(object):
    """
    A wrapper class to make working with :class:`socket.socket` much simpler.
    
    .. NOTE:: For AsyncIO, use :class:`.AsyncSocketWrapper` instead.
    
    **Features**
    
     * Automatic address family detection - detects whether you have working IPv4 / IPv6, and decides the best way
       to connect to a host, depending on what IP versions that host supports
     * ``Happy Eyeballs`` for IPv6. If something goes wrong with an IPv6 connection, it will fallback to IPv4 if the
       host has it available (i.e. a domain with both ``A`` and ``AAAA`` records)
     * Easy to use SSL, which works with HTTPS and other SSL-secured protocols. Just pass ``use_ssl=True`` in the constructor.
     * Many wrapper methods such as :meth:`.recv_eof`, :meth:`.query`, and :meth:`.http_request` to make working
       with sockets much easier.
      
    
    **Examples**
    
    Send a string of bytes / text to a server, and then read until EOF::
    
        >>> sw = SocketWrapper('icanhazip.org', 80)
        >>> res = sw.query("GET / HTTP/1.1\\nHost: icanhazip.com\\n\\n")
        >>> print(res)
        HTTP/1.1 200 OK
        Server: nginx
        Content-Type: text/plain; charset=UTF-8
        Content-Length: 17
        x-rtfm: Learn about this site at http://bit.ly/icanhazip-faq and do not abuse the service.
        
        2a07:e00::abc
    
    For basic HTTP requests, you can use :meth:`.http_request`, which will automatically send ``Host`` (based on the host you passed),
    and ``User-Agent``. SSL works too, just set ``use_ssl=True``::
    
        >>> sw = SocketWrapper('myip.privex.io', 443, use_ssl=True)
        >>> res = sw.http_request('/?format=json')
        >>> print(res)
        HTTP/1.1 200 OK
        Server: nginx
        Date: Tue, 22 Sep 2020 03:40:48 GMT
        Content-Type: application/json
        Content-Length: 301
        Connection: close
        Access-Control-Allow-Origin: *
        {"error":false,"geo":{"as_name":"Privex Inc.","as_number":210083,"city":"Stockholm","country":"Sweden",
         "country_code":"SE","error":false,"zip":"173 11"},"ip":"2a07:e00::abc","ip_type":"ipv6","ip_valid":true,
         "messages":[], "ua":"Python Privex Helpers ( https://github.com/Privex/python-helpers )"}
    
    Standard low-level sending and receiving data::
        
        >>> sw = SocketWrapper('127.0.0.1', 8888)
        >>> sw.sendall(b"hello world")    # Send the text 'hello world'
        >>> sw.recv(64)                   # read up to 64 bytes of data from the socket
        b"lorem ipsum\n"
        
    """
    DEFAULT_TIMEOUT = empty_if(socket.getdefaulttimeout(), settings.DEFAULT_SOCKET_TIMEOUT, zero=True)

    _context: Optional[ssl.SSLContext]
    _socket: OpAnySocket
    _base_socket: Optional[socket.socket]
    _ssl_socket: Optional[ssl.SSLSocket]
    _layer_context: Optional[LayeredContext]
    _socket_ctx_mgr: SocketContextManager
    # connected: bool
    auto_connect: bool
    auto_listen: bool
    listen_backlog: int
    tracker: SocketTracker
    
    def __init__(
            self, host: str, port: int, server=False, family=-1, type=socket.SOCK_STREAM, proto=-1, fileno=None,
            timeout=DEFAULT_TIMEOUT, use_ssl=False, verify_cert=False, **kwargs
    ):
        self.host, self.port = host, int(port)
        self.server = is_true(server)
        # if self.server and (empty(type) or type == -1):
        #     type = socket.SOCK_STREAM
        # self._socket = kwargs.get('socket', None)
        # self._base_socket = kwargs.get('base_socket', None)
        # self._ssl_socket = kwargs.get('ssl_socket', None)
        _context = kwargs.get('ssl_context', None)
        # self.connected = not (self._socket is None)
        binded, listening = kwargs.get('binded', False), kwargs.get('listening', False)
        check_connectivity = kwargs.get('check_connectivity', settings.CHECK_CONNECTIVITY)
        self.auto_connect = kwargs.get('auto_connect', True)
        self.error_reconnect = kwargs.get('error_reconnect', True)
        self.auto_listen = kwargs.get('auto_listen', True)
        self.listen_backlog = kwargs.get('listen_backlog', 10)
        self.read_timeout = kwargs.get('read_timeout', settings.DEFAULT_READ_TIMEOUT)
        self.send_timeout = kwargs.get('send_timeout', settings.DEFAULT_WRITE_TIMEOUT)
        
        from privex.helpers.net.common import check_v4_async, check_v6_async

        if family == -1 and is_ip(host):
            log.debug("Host '%s' appears to be an IP. Automatically setting address family based on IP.", host)
            family = ip_sock_ver(host)
        
        if family == -1 and check_connectivity:
            host_v4 = resolve_ip(host, 'v4')
            host_v6 = resolve_ip(host, 'v6')
            
            if host_v6 is not None and run_coro_thread(check_v6_async):
                log.debug("Domain %s has one or more IPv6 addresses, and current system appears to have IPv6 connectivity. "
                          "Using domain's IPv6 address: %s", host, host_v6)
                family = socket.AF_INET6
            elif host_v4 is not None and run_coro_thread(check_v4_async):
                log.debug("Domain %s has one or more IPv4 addresses, and current system appears to have IPv4 connectivity. "
                          "Using domain's IPv4 address: %s", host, host_v4)
                family = socket.AF_INET

        # self.use_ssl = use_ssl
        # self.socket_conf = dict(family=family, type=type, proto=proto, fileno=fileno)
        # self.ssl_wrap_conf = dict(
        #     server_hostname=kwargs.get('server_hostname'),
        #     session=kwargs.get('session'),
        #     do_handshake_on_connect=kwargs.get('do_handshake_on_connect', True)
        # )
        # self.ssl_conf = dict(
        #     verify_cert=verify_cert,
        #     check_hostname=kwargs.get('check_hostname'),
        #     verify_mode=kwargs.get('verify_mode')
        # )
        # sck = self._socket if self._socket is not None else socket.socket(**self.socket_conf)
        self.tracker = SocketTracker(
            self.host, self.port,
            timeout=timeout, server=server, binded=binded, connected=kwargs.get('connected', False),
            listening=listening, use_ssl=use_ssl,
            socket_conf=dict(family=family, type=type, proto=proto, fileno=fileno),
            ssl_conf=dict(
                verify_cert=verify_cert,
                check_hostname=kwargs.get('check_hostname'),
                verify_mode=kwargs.get('verify_mode')
            ),
            ssl_wrap_conf=dict(
                server_hostname=kwargs.get('server_hostname'),
                session=kwargs.get('session'),
                do_handshake_on_connect=kwargs.get('do_handshake_on_connect', True)
            ), hostname=kwargs.get('hostname', None)
        )

        _socket = kwargs.get('socket', None)
        _base_socket = kwargs.get('base_socket', None)
        _ssl_socket = kwargs.get('ssl_socket', None)
        
        if _context is not None: self.tracker.ssl_context = _context
        if _socket is not None: self.tracker.socket = _socket
        if _base_socket is not None: self.tracker.socket = _base_socket
        if _ssl_socket is not None: self.tracker.ssl_socket = _ssl_socket
        
        # self._timeout = float(timeout)
        self._layer_context = None
        self._socket_ctx_mgr = SocketContextManager(self)
        # if use_ssl:
        #     ctx = get_ssl_context(**ssl_params)
        #     s = ctx.wrap_socket(
        #         server_hostname=kwargs.get('server_hostname'),
        #         session=kwargs.get('session'),
        #         do_handshake_on_connect=kwargs.get('do_handshake_on_connect', True),
        #     )
    
    @property
    def ssl_conf(self) -> dict:
        return self.tracker.ssl_conf
    
    @ssl_conf.setter
    def ssl_conf(self, value):
        self.tracker.ssl_conf = value

    @property
    def ssl_wrap_conf(self) -> dict:
        return self.tracker.ssl_wrap_conf

    @ssl_wrap_conf.setter
    def ssl_wrap_conf(self, value):
        self.tracker.ssl_wrap_conf = value

    @property
    def socket_conf(self) -> dict:
        return self.tracker.socket_conf

    @socket_conf.setter
    def socket_conf(self, value):
        self.tracker.socket_conf = value
    
    @property
    def timeout(self):
        return self.tracker.timeout
    
    @property
    def _auto_socket(self):
        return self.tracker._auto_socket
    
    @timeout.setter
    def timeout(self, value):
        self.socket.settimeout(value)
        self.tracker.timeout = value
        # self.base_socket.settimeout(value)
        # if self._socket:
        #     self._socket.settimeout(value)
        # self._timeout = value
    
    def _make_context(self, **kwargs) -> ssl.SSLContext:
        cnf = {**self.ssl_conf, **kwargs}
        return get_ssl_context(**cnf)
    
    def _make_socket(self, **kwargs) -> socket.socket:
        cnf = {**self.socket_conf, **kwargs}
        # if self.server:
        #     if 'family' in cnf: del cnf['family']
        #     if 'type' in cnf: del cnf['type']
        #     if 'proto' in cnf: del cnf['proto']
        #     if 'fileno' in cnf: del cnf['fileno']
        #     log.info("socket host: %s || port: %s", self.host, self.port)
        #     log.info("socket extra config: %s", cnf)
        #     return socket.create_server((self.host, self.port), **cnf)
        return socket.socket(**cnf)

    def _ssl_wrap_socket(self, sock: socket.socket = None, ctx: ssl.SSLContext = None, **kwargs) -> ssl.SSLSocket:
        cnf = {**self.ssl_wrap_conf, **kwargs}
        ctx = empty_if(ctx, self.context, itr=True, zero=True)
        sock = empty_if(sock, self.base_socket, itr=True, zero=True)
        return ctx.wrap_socket(sock, **cnf)
    
    def _select_socket(self, new_sock=False, **kwargs) -> Union[ssl.SSLSocket, "socket.socket"]:
        if new_sock:
            sock = self._make_socket()
            if kwargs.get('use_ssl', self.use_ssl):
                sock = self._ssl_wrap_socket(sock, **kwargs)
            return sock
        if self.use_ssl:
            return self._ssl_wrap_socket(**kwargs)
        return self.base_socket
    
    @property
    def hostname(self):
        return self.tracker.hostname
    
    @hostname.setter
    def hostname(self, value):
        self.tracker.hostname = value
    
    @property
    def context(self) -> ssl.SSLContext:
        # if not self._context:
        #     self._context = self._make_context()
        # return self._context
        if not self.tracker.ssl_context:
            self.tracker.ssl_context = self._make_context()
        return self.tracker.ssl_context
    
    ssl_context = context

    @property
    def base_socket(self) -> socket.socket:
        if not self.tracker.socket:
            self.tracker.socket = self._make_socket()
        return self.tracker.socket

    @base_socket.setter
    def base_socket(self, value: socket.socket):
        self.tracker.socket = value

    @property
    def socket(self) -> AnySocket:
        # if not self._socket:
        #     self._socket = self._select_socket()
        # if not self.server: self._socket.settimeout(self.timeout)
        return self.tracker.auto_socket
    
    @socket.setter
    def socket(self, value: AnySocket):
        if self.tracker.use_ssl:
            self.tracker.ssl_socket = value
        else:
            self.tracker.socket = value
        # self._socket = value
    
    @property
    def connected(self):
        return self.tracker.connected
    
    # @connected.setter
    # def connected(self, value):
    #     self.tracker.connected = value
    
    def _connect_sanity(self, host, port, sock: OpAnySocket = None, **kwargs):
        port = int(port)
        sck = self.socket if sock is None else sock

        if sock is None and self.connected and self.socket is not None:
            if host != self.host or port != int(self.port):
                log.debug(f"Already connected, but {self.__class__.__name__}.connect called with different host/port than stored. "
                          f"Trigerring a reconnect.")
                return self.reconnect(host, port, sock=sck)
            log.debug(f"Already connected, {self.__class__.__name__}.connect called with same details as previously. "
                      f"Returning existing socket.")
            return sck
        if empty(port, True, True):
            raise ValueError(f"{self.__class__.__name__}.connect requires a port. Either connect(host, port) or connect( (host,port) )")
        return True
        
    def _connect(self, host: str, port: AnyNum, sock: OpAnySocket = None, **kwargs) -> AnySocket:
        port = int(port)
        sck = self.tracker if sock is None else sock
        if self.server:
            log.debug("Binding to host '%s' on port %s", host, port)
            self.bind(host, port, sock=sock)
            log.debug("Successfully binded to host '%s' on port %s", host, port)
            if self.auto_listen:
                log.debug("Auto-listen is enabled. Calling %s.listen(%s)", self.__class__.__name__, self.listen_backlog)
                self.listen(self.listen_backlog, sock=sock)
                log.debug("%s is now listening on host(s) '%s' on port %s", self.__class__.__name__, host, port)
            # if sock is None: self.host, self.port, self.connected = host, port, True
            return sck

        log.debug("[%s.%s] Connecting to host %s on port %s", self.__class__.__name__, __name__, host, port)
        sck.connect((host, port))
        
        # if sock is None: self.host, self.port, self.connected = host, port, True
        return sck
    
    def _get_addr(self, host: Union[str, Tuple[str, AnyNum]] = None, port: AnyNum = None) -> Tuple[str, int]:
        csn = self.__class__.__name__
    
        if host is None:
            if self.host is None: raise ValueError(f"No host specified to {csn}.reconnect(host, port) - and no host in {csn}.host")
            host = self.host
        if port is None:
            if self.port is None: raise ValueError(f"No port specified to {csn}.connect(host, port) - and no port in {csn}.port")
            port = self.port
        if isinstance(host, (list, set)): host = tuple(host)
        if isinstance(host, tuple): host, port = host
        
        return host, int(port)
    
    def bind(self, host: Union[str, Tuple[str, AnyNum]] = None, port: AnyNum = None, sock: OpAnySocket = None, **kwargs):
        sck = self.socket if sock is None else sock
        if sock is None and self.binded:
            return
        sck.bind(self._get_addr(host, port))
        if sock is None: self.binded = True
        return True
    
    def connect(self, host: Union[str, Tuple[str, AnyNum]] = None, port: AnyNum = None, sock: OpAnySocket = None, **kwargs) -> AnySocket:
        # csn = self.__class__.__name__
        #
        # if host is None:
        #     if self.host is None: raise ValueError(f"No host specified to {csn}.reconnect(host, port) - and no host in {csn}.host")
        #     host = self.host
        # if port is None:
        #     if self.port is None: raise ValueError(f"No port specified to {csn}.connect(host, port) - and no port in {csn}.port")
        #     port = self.port
        # if isinstance(host, (list, set)): host = tuple(host)
        # if isinstance(host, tuple): host, port = host

        host, port = self._get_addr(host, port)
        sanity = self._connect_sanity(host, port, sock=sock)
        if sanity is not True: return sanity
        return self._connect(host, port, sock=sock)
    
    def reconnect(self, host: Union[str, Tuple[str, AnyNum]] = None, port: AnyNum = None, sock: OpAnySocket = None, **kwargs):
        csn = self.__class__.__name__

        # self.close(sock=sock)
        if host is None:
            if port is not None:
                if self.host is None:
                    raise ValueError(f"No host specified to {csn}.reconnect(host, port) - and no host in {csn}.host")
                # return self.connect(self.host, port, sock=sock, **kwargs)
                host = self.host
                # self.tracker.host, self.tracker.port = self.host, port
                # self.tracker.reconnect()
                # return self.tracker
            # if all([self.host is not None, self.port is not None]):
                # return self.connect(self.host, self.port, sock=sock, **kwargs)
                # self.tracker.host, self.tracker.port = self.host,

                # self.tracker.connect()
                # return self.tracker
        elif port is None:
            port = self.port
            # self.tracker.host, self.tracker.port = host, port
        # else:
        self.tracker.host, self.tracker.port = host, port
    
        # return self.connect(host, port, sock=sock, **kwargs)
        self.tracker.reconnect()
        return self.tracker
        # return self.connect(host, self.port, sock=sock, **kwargs)
    
    def listen(self, backlog=10, sock: OpAnySocket = None, **kwargs):
        if self.listening:
            return True
        (self.socket if sock is None else sock).listen(backlog)
        if sock is None: self.listening = True
        return True
    
    @_sockwrapper_auto_connect()
    def accept(self, sock: OpAnySocket = None, **kwargs) -> Tuple[AnySocket, Tuple[str, int]]:
        return (self.socket if sock is None else sock).accept()
    
    @_sockwrapper_auto_connect()
    def settimeout(self, value, sock: OpAnySocket = None, **kwargs):
        return (self.socket if sock is None else sock).settimeout(value)
    
    def close(self, sock: OpAnySocket = None):
        log.debug("Closing socket connection to host: %s || port: %s", self.host, self.port)
        if sock is not None:
            log.debug(" !! sock was specified. only closing sock.")
            try:
                sock.close()
                log.debug("Closed sock.")
            except Exception:
                log.exception("error while closing sock")
            return
        self.tracker.disconnect()
        # try:
        #     if self._socket is not None:
        #         log.debug("closing self.socket")
        #         self.socket.close()
        # except Exception:
        #     log.exception("error while closing self.socket")
        # try:
        #     if self._base_socket is not None:
        #         log.debug("closing self.base_socket")
        #         self.base_socket.close()
        # except Exception:
        #     log.exception("error while closing self.base_socket")
        #
        # try:
        #     if self._ssl_socket is not None:
        #         self._ssl_socket.close()
        #         log.debug("closing self._ssl_socket")
        # except Exception:
        #     log.exception("error while closing self._ssl_socket")
        # self.connected = False
        # log.debug("setting socket instance attributes to None")
        # self._socket, self._ssl_socket, self._base_socket = None, None, None
    
    @_sockwrapper_auto_connect()
    def recv(self, bufsize: int, flags: int = None, sock: OpAnySocket = None, **kwargs) -> bytes:
        if flags is None: return (self.socket if sock is None else sock).recv(bufsize)
        return (self.socket if sock is None else sock).recv(bufsize, flags)

    @_sockwrapper_auto_connect()
    def recvfrom(self, bufsize: int, flags: int = None, sock: OpAnySocket = None, **kwargs) -> Tuple[bytes, Any]:
        if flags is None: return (self.socket if sock is None else sock).recvfrom(bufsize)
        return (self.socket if sock is None else sock).recvfrom(bufsize, flags)

    @_sockwrapper_auto_connect()
    def recvmsg(
            self, bufsize: int, ancbufsize:int = None, flags: int = None, sock: OpAnySocket = None, **kwargs
    ) -> Tuple[bytes, List[Tuple[int, int, bytes]], int, Any]:
        args = [bufsize]
        if ancbufsize is not None: args.append(ancbufsize)
        if flags is not None: args.append(flags)
        return (self.socket if sock is None else sock).recvmsg(*args)

    @_sockwrapper_auto_connect()
    def read_eof(
                self, bufsize: int = 256, eof_timeout: AnyNum = 120, flags: int = None, timeout_fail=False, strip=True,
                conv: Optional[Callable[[Union[bytes, str]], T]] = stringify, sock: OpAnySocket = None, **kwargs
            ) -> Union[bytes, str, T]:
        strip_func = kwargs.get('strip_func', lambda d: strip_null(d, conv=conv))
        data = b''
        total_time = 0.0
        
        while True:
            st_time = time.time()
            chunk = self.recv(bufsize, flags, sock=sock)
            if not chunk:
                log.debug("Finished reading until EOF")
                break
            e_time = time.time()
            total_time += (e_time - st_time)
            data += chunk
            if total_time > eof_timeout:
                log.error("Giving up, spent over %f seconds (%f) reading until EOF for host %s", eof_timeout, total_time, self.host)
                if timeout_fail:
                    raise TimeoutError(f"Giving up, spent over {eof_timeout} seconds ({total_time}) reading until EOF for host {self.host}")
                break
        
        return strip_func(data) if strip else data

    @_sockwrapper_auto_connect()
    def shutdown(self, how: int = None, sock: OpAnySocket = None, **kwargs):
        how = empty_if(how, socket.SHUT_RDWR, itr=True)
        return (self.socket if sock is None else sock).shutdown(how)

    @_sockwrapper_auto_connect()
    def send(self, data: Union[str, bytes], flags: int = None, sock: OpAnySocket = None, **kwargs):
        a = [byteify(data)]
        if not empty(flags): a.append(flags)
        return (self.socket if sock is None else sock).send(*a)

    @_sockwrapper_auto_connect()
    def sendall(self, data: Union[str, bytes], flags: int = None, sock: OpAnySocket = None, **kwargs):
        a = [byteify(data)]
        if not empty(flags): a.append(flags)
        return (self.socket if sock is None else sock).sendall(*a)

    @_sockwrapper_auto_connect()
    def sendto(self, data: Union[str, bytes], *args, sock: OpAnySocket = None, **kwargs):
        return (self.socket if sock is None else sock).sendto(byteify(data), *args, **kwargs)

    @_sockwrapper_auto_connect()
    def send_chunks(self, gen: Union[Iterable, Generator], flags: int = None, sock: OpAnySocket = None, **kwargs):
        results = []
        for c in gen:
            results.append(self.send(c, flags, sock=sock, **kwargs))
        return results

    # @_sockwrapper_auto_connect()
    # def query(self, data: Union[str, bytes], bufsize: int = 32, eof_timeout=30, **kwargs):
    #     timeout_fail, send_flags = kwargs.get('timeout_fail'), kwargs.get('send_flags', kwargs.get('flags', None))
    #     recv_flags = kwargs.get('recv_flags', kwargs.get('flags', None))
    #     log.debug(" >> Sending %s bytes to %s:%s", len(data), self.host, self.port)
    #     self.sendall(byteify(data), flags=send_flags)
    #     log.debug(" >> Reading %s bytes per chunk from %s:%s", bufsize, self.host, self.port)
    #     return self.read_eof(bufsize, eof_timeout=eof_timeout, flags=recv_flags, timeout_fail=timeout_fail)

    # @_sockwrapper_auto_connect()
    # def http_request(
    #         self, url="/", host=AUTO_DETECTED, method="GET", user_agent=DEFAULT_USER_AGENT, extra_data: Union[STRBYTES, List[str]] = None,
    #         body: STRBYTES = None, eof_timeout=30, **kwargs
    # ) -> Union[bytes, Awaitable[bytes]]:
    #     bufsize, flags, timeout_fail = kwargs.pop('bufsize', 256), kwargs.pop('flags', None), kwargs.pop('timeout_fail', False)
    #     data = self._http_request(url, host=host, method=method, user_agent=user_agent, extra=extra_data, body=body, **kwargs)
    #     self.sendall(data, flags=flags)
    #     return self.read_eof(bufsize, eof_timeout=eof_timeout, flags=flags, timeout_fail=timeout_fail)

    def _http_request(self, url, host: str, method: str, user_agent: str = settings.DEFAULT_USER_AGENT, extra=None, **kwargs) -> bytes:
        host = self.hostname if host == AUTO_DETECTED else host
        return generate_http_request(url, host, method=method, user_agent=user_agent, extra_data=extra, **kwargs)

    @_sockwrapper_auto_connect()
    def query(self, data: Union[str, bytes], bufsize: int = 32, eof_timeout=30, sock: OpAnySocket = None, **kwargs):
        timeout_fail, send_flags = kwargs.pop('timeout_fail', False), kwargs.pop('send_flags', kwargs.get('flags', None))
        recv_flags = kwargs.pop('recv_flags', kwargs.pop('flags', None))
        log.debug(" >> Sending %s bytes to %s:%s", len(data), self.host, self.port)
        self.sendall(byteify(data), flags=send_flags, sock=sock)
        log.debug(" >> Reading %s bytes per chunk from %s:%s", bufsize, self.host, self.port)
        return self.read_eof(bufsize, eof_timeout=eof_timeout, flags=recv_flags, timeout_fail=timeout_fail, sock=sock, **kwargs)

    @_sockwrapper_auto_connect()
    def http_request(
                self, url="/", host=AUTO_DETECTED, method="GET", user_agent=settings.DEFAULT_USER_AGENT,
                extra_data: Union[STRBYTES, List[str]] = None, body: STRBYTES = None, eof_timeout=30, bufsize: int = 256,
                conv: Optional[Callable[[Union[bytes, str]], T]] = stringify, sock: OpAnySocket = None, **kwargs
            ) -> Union[str, bytes, T]:
        
        data = self._http_request(url, host=host, method=method, user_agent=user_agent, extra=extra_data, body=body, **kwargs)
        kargs = dict(data=data, bufsize=bufsize, eof_timeout=eof_timeout, timeout_fail=kwargs.get('timeout_fail', False), conv=conv,
                     sock=sock, **kwargs)
        if sock is not None: return self.query(**kargs)
        # with self:
        with self.tracker:
            return self.query(**kargs)

    @_sockwrapper_auto_connect()
    def setblocking(self, flag: bool, sock: OpAnySocket = None, **kwargs):
        return (self.socket if sock is None else sock).setblocking(flag)
    
    def handle_connection(
            self, sock: AnySocket, addr: Tuple[str, int], callback: Callable[["SocketWrapper", Tuple[str, int]], Any],
            stop_return: Union[str, bytes] = None,
            **kwargs
    ):
        stop_compare, stop_compare_lower = kwargs.get('stop_compare', 'equal'), kwargs.get('stop_compare_lower', True)
        if stop_return is not None: stop_return = stringify(stop_return)
        log.info("NEW CONNECTION: %s || %s", sock, addr)
        log.info("Running callback: %s(%s, %s)\n", callback.__name__, sock, addr)
        orig_cres = callback(self.from_socket(sock), addr)
        cres = stringify(orig_cres)
        log.info("Callback return data: %s\n\n", cres)
        if stop_return is not None:
            if stop_compare_lower: stop_return, cres = stop_return.lower(), cres.lower()
            
            if stop_compare.lower() in ['in', 'contain', 'contains', 'contained', 'within', 'inside']:
                if stop_return in cres or strip_null(stop_return) in strip_null(cres):
                    raise StopLoopOnMatch("Matched stop_return. Parent should stop loop.", cres, stop_compare, stop_compare_lower)
            
            if cres == stop_return or strip_null(cres) == strip_null(stop_return):
                raise StopLoopOnMatch("Matched stop_return. Parent should stop loop.", cres, stop_compare, stop_compare_lower)
        return orig_cres

    @_sockwrapper_auto_connect()
    def on_connect(
            self, callback: Callable[["SocketWrapper", Tuple[str, int]], Any], timeout: AnyNum = None,
            stop_return: Union[str, bytes] = None, **kwargs
    ):
        if not self.server:
            raise ValueError("This SocketWrapper has 'server' set to False. Can't handle incoming connections.")
        if not self.binded: self.bind()
        if not self.listening: self.listen(self.listen_backlog)
        stop_return_match = None
        
        while self.connected and stop_return_match is None:
            log.info("Waiting for incoming connection ( %s:%s || %s ) ...", self.host, self.port, self.socket.getsockname())
            sock, addr = self.accept()
            try:
                self.handle_connection(sock, addr, callback, stop_return, **kwargs)
            except StopLoopOnMatch as e:
                log.info(" !!! Stopping on_connect as 'stop_return' has been matched: %s", stop_return)
                log.info(" !!! The matching message was: %s", e.match)
                break
            
        # if stop_return_match is not None:
        #     log.info(" !!! Stopping on_connect as 'stop_return' has been matched: %s", stop_return)
        #     log.info(" !!! The matching message was: %s", stop_return_match)

        log.info(" !!! Disconnected. Stopping on_connect.")

    class SocketWrapperThread(SafeLoopThread):
        def __init__(self, *args, parent_instance: "SocketWrapper", callback, stop_return, conn_kwargs: dict = None, **kwargs):
            kwargs = dict(kwargs)
            self.parent_instance = parent_instance
            self.callback = callback
            self.conn_kwargs = empty_if(conn_kwargs, {}, itr=True)
            self.stop_return = stop_return
            self.stop_compare = kwargs.pop('stop_compare', 'equal')
            self.stop_compare_lower = kwargs.pop('stop_compare_lower', True)
            super().__init__(*args, **kwargs)
    
        def loop(self):
            pi = self.parent_instance
            log.info("Waiting for incoming connection ( %s:%s || %s ) ...", pi.host, pi.port, pi.socket.getsockname())
            sock, addr = pi.accept()
            try:
                pi.handle_connection(
                    sock, addr, self.callback, self.stop_return,
                    stop_compare=self.stop_compare, stop_compare_lower=self.stop_compare_lower, **self.conn_kwargs
                )
            except StopLoopOnMatch as e:
                log.info(" !!! Stopping on_connect as 'stop_return' has been matched: %s", self.stop_return)
                log.info(" !!! The matching message was: %s", e.match)
                self.emit_stop()
        
        def run(self):
            self.parent_instance.reconnect()
            return super().run()
        
    def on_connect_thread(
            self, callback: Callable[["SocketWrapper", Tuple[str, int]], Any], timeout: AnyNum = None,
            stop_return: Union[str, bytes] = None, daemon=True, auto_start=True, **kwargs
    ) -> SocketWrapperThread:
        t = self.SocketWrapperThread(parent_instance=self, callback=callback, stop_return=stop_return, **kwargs)
        t.setDaemon(daemon)
        if auto_start:
            t.start()
        return t

    @classmethod
    def from_socket(cls, sock: AnySocket, server=False, **kwargs) -> Union["SocketWrapper", "AsyncSocketWrapper"]:
        sock_host, sock_port = sock.getsockname()
        cfg = dict(
            family=sock.family, proto=sock.proto, type=sock.type, fileno=sock.fileno(),
            host=sock_host, port=sock_port, server=server, socket=sock, base_socket=sock
        )
        cfg = {**cfg, **kwargs}
        return cls(**cfg)
    
    def __getattribute__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError:
            pass
        sock: AnySocket = super().__getattribute__('socket')
        return getattr(sock, item)
    
    def __enter__(self):
        # if not self._socket_ctx_mgr:
        #     self._socket_ctx_mgr = SocketContextManager(self)
        # if not self._layer_context:
        #     self._layer_context = LayeredContext(self._socket_ctx_mgr, max_layers=1)
        # return self._layer_context.__enter__()
        self.tracker.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # return self.tracker.__aexit__()
    
        # return self._layer_context.__exit__(exc_type, exc_val, exc_tb)
        return self.tracker.__exit__(exc_type, exc_val, exc_tb)


class AsyncSocketWrapper(SocketWrapper):
    """
    
        >>> from privex.helpers import AsyncSocketWrapper
        >>> sw = AsyncSocketWrapper('termbin.com', 9999)
        >>> url = await sw.query("HELLO world\\n\\nThis is a test\\nusing async sockets\\n\\nwith Python")
        'https://termbin.com/lsd93'
        >>> url = await sw.read_eof()
    """
    _loop: Optional[asyncio.AbstractEventLoop]
    DEFAULT_TIMEOUT = empty_if(socket.getdefaulttimeout(), settings.DEFAULT_SOCKET_TIMEOUT, zero=True)

    def __init__(
            self, host: str, port: int, server=False, family=-1, type=socket.SOCK_STREAM, proto=-1, fileno=None,
            timeout=DEFAULT_TIMEOUT, use_ssl=False, verify_cert=False, loop=None, **kwargs
    ):
        self._loop = loop
        super().__init__(
            host=host, port=port, server=server, family=family, type=type, proto=proto, fileno=fileno, timeout=timeout,
            use_ssl=use_ssl, verify_cert=verify_cert, **kwargs
        )
    
    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        if not self._loop:
            self._loop = asyncio.get_event_loop()
        return self._loop
    
    async def _connect(self, host: str, port: AnyNum, sock: OpAnySocket = None, **kwargs) -> AnySocket:
        port = int(port)
        # sck = self.socket if sock is None else sock

        if self.server:
            log.debug("Binding to host '%s' on port %s", host, port)
            self.bind(host, port, sock=sock)
            log.debug("Successfully binded to host '%s' on port %s", host, port)
            if self.auto_listen:
                log.debug("Auto-listen is enabled. Calling %s.listen(%s)", self.__class__.__name__, self.listen_backlog)
                self.listen(self.listen_backlog, sock=sock)
                log.debug("%s is now listening on host(s) '%s' on port %s", self.__class__.__name__, host, port)
            # if sock is None: self.host, self.port, self.connected = host, port, True
            return self.socket
        log.debug("Connecting to host %s on port %s", host, port)
        if sock:
            await self.loop.sock_connect(sock, (host, port))
            return sock
        await self.tracker.connect_async()
        return self.tracker.auto_socket
        # self.loop.soc
        # if sock is None: self.host, self.port, self.connected = host, port, True
    
    async def connect(
            self, host: Union[str, Tuple[str, AnyNum]] = None, port: AnyNum = None, sock: OpAnySocket = None, **kwargs) -> AnySocket:
        
        host, port = self._get_addr(host, port)
        sanity = await self._connect_sanity(host, port)
        if sanity is not True: return sanity
        return await self._connect(host, port, sock=sock)

    async def _connect_sanity(self, host, port, sock: OpAnySocket = None, **kwargs):
        port = int(port)
        # sock = self._auto_socket if sock is None else sock

        if sock is not None or (self.connected and self._auto_socket is not None):
            if host != self.host or port != int(self.port):
                log.debug(f"Already connected, but {self.__class__.__name__}.connect called with different host/port than stored. "
                          f"Trigerring a reconnect.")
                return await self.reconnect(host, port, sock=sock)
            log.debug(f"Already connected, {self.__class__.__name__}.connect called with same details as previously. "
                      f"Returning existing socket.")
            return sock
        if empty(port, True, True):
            raise ValueError(f"{self.__class__.__name__}.connect requires a port. Either connect(host, port) or connect( (host,port) )")
        return True

    async def reconnect(self, host: Union[str, Tuple[str, AnyNum]] = None, port: AnyNum = None, sock: OpAnySocket = None, **kwargs):
        csn = self.__class__.__name__
        self.close()
        if host is None:
            if port is not None:
                if self.host is None:
                    raise ValueError(f"No host specified to {csn}.reconnect(host, port) - and no host in {csn}.host")
                return await self.connect(self.host, port, sock=sock)
            if all([self.host is not None, self.port is not None]):
                return await self.connect(self.host, self.port, sock=sock)
        if port is not None:
            return await self.connect(host, port, sock=sock)
        return await self.connect(host, self.port, sock=sock)

    @_async_sockwrapper_auto_connect()
    async def read_eof(
            self, bufsize: int = 256, eof_timeout: AnyNum = 120, flags: int = None, timeout_fail=False, strip=True,
            conv: Optional[Callable[[Union[bytes, str]], T]] = stringify, sock: OpAnySocket = None, **kwargs
    ) -> Union[str, bytes, T]:
        strip_func = kwargs.get('strip_func', lambda d: strip_null(d, conv=conv))
        data, total_time = b'', 0.0
    
        while True:
            st_time = time.time()
            chunk = await self.recv(bufsize, flags, timeout=kwargs.get('read_timeout', AUTO), sock=sock)
            if not chunk:
                log.debug("Finished reading until EOF")
                break
            e_time = time.time()
            total_time += (e_time - st_time)
            data += chunk
            if not empty(eof_timeout, True) and total_time > eof_timeout:
                log.error("Giving up, spent over %f seconds (%f) reading until EOF for host %s", eof_timeout, total_time, self.host)
                if timeout_fail:
                    raise TimeoutError(f"Giving up, spent over {eof_timeout} seconds ({total_time}) reading until EOF for host {self.host}")
                break
    
        return strip_func(data) if strip else data

    @_async_sockwrapper_auto_connect()
    async def recv(self, bufsize: int, flags: int = None, sock: OpAnySocket = None, timeout: Union[float, int] = AUTO, **kwargs) -> bytes:
        timeout, sck = self.read_timeout if timeout is AUTO else timeout, self.socket if sock is None else sock
        if timeout not in [None, False]:
            return await asyncio.wait_for(self.loop.sock_recv(sck, bufsize), timeout)
        return await self.loop.sock_recv(sck, bufsize)

    @_async_sockwrapper_auto_connect()
    async def recv_into(self, buf: bytearray, sock: OpAnySocket = None, **kwargs) -> int:
        return await self.loop.sock_recv_into(self.socket if sock is None else sock, buf)

    @_async_sockwrapper_auto_connect()
    async def send(self, data: Union[str, bytes], flags: int = None, sock: OpAnySocket = None, timeout: Union[float, int] = AUTO, **kwargs):
        return await self.send_timeout(data, flags, sock, timeout, **kwargs)

    @_async_sockwrapper_auto_connect()
    async def sendall(
                self, data: Union[str, bytes], flags: int = None, sock: OpAnySocket = None, timeout: Union[float, int] = AUTO, **kwargs
            ):
        timeout, sck = self.send_timeout if timeout is AUTO else timeout, self.socket if sock is None else sock
        if timeout not in [None, False]:
            return await asyncio.wait_for(self.loop.sock_sendall(sck, byteify(data)), timeout)
        return await self.loop.sock_sendall(sck, byteify(data))

    @_async_sockwrapper_auto_connect()
    async def sendfile(
            self, file: IO[bytes], offset: int = None, count: int = None, fallback: bool = True, sock: OpAnySocket = None,
            timeout: Union[float, int] = AUTO, **kwargs
    ):
        timeout, sck = self.send_timeout if timeout is AUTO else timeout, self.socket if sock is None else sock
        if timeout not in [None, False]:
            return await asyncio.wait_for(self.loop.sock_sendfile(sck, file, offset=offset, count=count, fallback=fallback), timeout)
        return await self.loop.sock_sendfile(sck, file, offset=offset, count=count, fallback=fallback)

    @_async_sockwrapper_auto_connect()
    async def query(self, data: Union[str, bytes], bufsize: int = 32, eof_timeout=30, sock: OpAnySocket = None, **kwargs):
        timeout_fail, send_flags = kwargs.pop('timeout_fail', False), kwargs.pop('send_flags', kwargs.get('flags', None))
        recv_flags = kwargs.pop('recv_flags', kwargs.pop('flags', None))
        shared_timeout = kwargs.pop('timeout', AUTO)
        log.debug(" >> Sending %s bytes to %s:%s", len(data), self.host, self.port)
        snd_tmout, rcv_tmout = kwargs.pop('send_timeout', shared_timeout), kwargs.pop('read_timeout', shared_timeout)
        await self.sendall(byteify(data), flags=send_flags, sock=self.socket if sock is None else sock, timeout=snd_tmout)
        log.debug(" >> Reading %s bytes per chunk from %s:%s", bufsize, self.host, self.port)
        return await self.read_eof(
            bufsize, eof_timeout=eof_timeout, flags=recv_flags, timeout_fail=timeout_fail,
            sock=self.socket if sock is None else sock, read_timeout=rcv_tmout, **kwargs
        )

    @_async_sockwrapper_auto_connect()
    async def http_request(
            self, url="/", host=AUTO_DETECTED, method="GET", user_agent=settings.DEFAULT_USER_AGENT,
            extra_data: Union[STRBYTES, List[str]] = None, body: STRBYTES = None, eof_timeout=30, bufsize: int = 256,
            conv: Optional[Callable[[Union[bytes, str]], T]] = stringify, sock: OpAnySocket = None, **kwargs
    ) -> Union[str, bytes, T]:
        async with self:
            data = self._http_request(
                url, host=host, method=method, user_agent=user_agent, extra=extra_data, body=body, sock=sock, **kwargs
            )
            
            # await self.sendall(data)
            return await self.query(
                data, bufsize, eof_timeout=eof_timeout, timeout_fail=kwargs.get('timeout_fail', False), conv=conv, sock=sock, **kwargs
            )
            # return await super().http_request(
            #     url, host=host, method=method, user_agent=user_agent, extra=extra_data, body=body, eof_timeout=eof_timeout, **kwargs
            # )
    
    async def accept(self, sock: OpAnySocket = None, **kwargs) -> Tuple[AnySocket, Tuple[str, int]]:
        return await self.loop.sock_accept(self.socket if sock is None else sock)

    async def handle_connection(
            self, sock: AnySocket, addr: Tuple[str, int], callback: Callable[["AsyncSocketWrapper", Tuple[str, int]], Any],
            stop_return: Union[str, bytes] = None,
            **kwargs
    ):
        stop_compare, stop_compare_lower = kwargs.get('stop_compare', 'equal'), kwargs.get('stop_compare_lower', True)
        if stop_return is not None: stop_return = stringify(stop_return)
        log.info("[async] NEW CONNECTION: %s || %s", sock, addr)
        log.info("[async] Running callback: %s(%s, %s)\n", callback.__name__, sock, addr)
        orig_cres = await await_if_needed(callback(self.from_socket(sock), addr))
        cres = stringify(orig_cres)
        log.info("[async] Callback return data: %s\n\n", cres)
        if stop_return is not None:
            if stop_compare_lower: stop_return, cres = stop_return.lower(), cres.lower()
        
            if stop_compare.lower() in ['in', 'contain', 'contains', 'contained', 'within', 'inside']:
                if stop_return in cres or strip_null(stop_return) in strip_null(cres):
                    raise StopLoopOnMatch("[async] Matched stop_return. Parent should stop loop.", cres, stop_compare, stop_compare_lower)
        
            if cres == stop_return or strip_null(cres) == strip_null(stop_return):
                raise StopLoopOnMatch("[async] Matched stop_return. Parent should stop loop.", cres, stop_compare, stop_compare_lower)
        return orig_cres
    
    @_sockwrapper_auto_connect()
    async def on_connect(
            self, callback: Callable[["AsyncSocketWrapper", Tuple[str, int]], Any], timeout: AnyNum = None,
            stop_return: Union[str, bytes] = None, sock: OpAnySocket = None, **kwargs
    ):
        if not self.server:
            raise ValueError("This AsyncSocketWrapper has 'server' set to False. Can't handle incoming connections.")
        if not self.binded: self.bind(sock=self.socket if sock is None else sock)
        if not self.listening: self.listen(self.listen_backlog, sock=self.socket if sock is None else sock)
        # if stop_return is not None: stop_return = stringify(stop_return)
        # stop_compare, stop_compare_lower = kwargs.get('stop_compare', 'equal'), kwargs.get('stop_compare_lower', True)
        stop_return_match = None
        
        while self.connected and stop_return_match is None:
            log.info("[async] Waiting for incoming connection ( %s:%s || %s ) ...", self.host, self.port, self.socket.getsockname())
            sock, addr = await self.accept()
            try:
                with sock:
                    await self.handle_connection(sock, addr, callback, stop_return, **kwargs)
            except StopLoopOnMatch as e:
                log.info(" !!! Stopping on_connect as 'stop_return' has been matched: %s", stop_return)
                log.info(" !!! The matching message was: %s", e.match)
                break
            # log.info("[async] NEW CONNECTION: %s || %s", sock, addr)
            # log.info("[async] Running callback: %s(%s, %s)\n", callback.__name__, sock, addr)
            # cres = await await_if_needed(callback(self.from_socket(sock), addr))
            # cres = stringify(cres)
            # log.info("[async] Callback return data: %s\n\n", cres)
            # if stop_return is not None:
            #     if stop_compare_lower:
            #         stop_return, cres = stop_return.lower(), cres.lower()
            #     if stop_compare.lower() in ['in', 'contain', 'contains', 'contained', 'within', 'inside']:
            #         if stop_return in cres or strip_null(stop_return) in strip_null(cres):
            #             stop_return_match = cres
            #             break
            #     if cres == stop_return or strip_null(cres) == strip_null(stop_return):
            #         stop_return_match = cres
            #         break
        # if stop_return_match is not None:
        #     log.info(" !!! Stopping on_connect as 'stop_return' has been matched: %s", stop_return)
        #     log.info(" !!! The matching message was: %s", stop_return_match)
        
        log.info(" !!! Disconnected. Stopping on_connect.")

    async def __aenter__(self):
        # if not self._socket_ctx_mgr:
        #     self._socket_ctx_mgr = SocketContextManager(self)
        # if not self._layer_context:
        #     self._layer_context = LayeredContext(self._socket_ctx_mgr, max_layers=1)
        # return await self._layer_context.__aenter__()
        return await self.tracker.__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # return await self._layer_context.__aexit__(exc_type, exc_val, exc_tb)
        return await self.tracker.__aexit__(exc_type, exc_val, exc_tb)


async def send_data_async(
        host: str, port: int, data: Union[bytes, str, Iterable], timeout: AnyNum = None, **kwargs
) -> Optional[Union[str, bytes]]:
    """
    
        >>> await send_data_async('termbin.com', 9999, "hello world\\nthis is a test\\n\\nlorem ipsum dolor\\n")
        'https://termbin.com/oi07'
    
    :param host:
    :param port:
    :param data:
    :param timeout:
    :param kwargs:
    :return:
    """
    fhost = f"({host}):{port}"
    chunk_size = int(kwargs.get('chunk', kwargs.get('chunk_size', 64)))
    string_result = is_true(kwargs.get('string_result', True))
    strip_result = is_true(kwargs.get('strip_result', True))
    fail = is_true(kwargs.get('fail', True))
    ip_version = kwargs.get('ip_version', 'any')
    timeout = empty_if(timeout, empty_if(socket.getdefaulttimeout(), 15, zero=True), zero=True)
    
    is_iter, data_iter = False, None
    
    if data is not None:
        if isinstance(data, (str, bytes, int, float)):
            data = byteify(data)
        else:
            try:
                data_iter = iter(data)
                is_iter = True
            except TypeError:
                # noinspection PyTypeChecker
                data = byteify(data)
        
    loop = asyncio.get_event_loop()
    try:
        s_ver = socket.AF_INET
        ip = await resolve_ip_async(host, ip_version)
        
        if ip_is_v6(ip): s_ver = socket.AF_INET6
        
        fhost += f" (IP: {ip})"
        
        with socket.socket(s_ver, socket.SOCK_STREAM) as s:
            s.settimeout(float(timeout))
            log.debug(" [...] Connecting to host: %s", fhost)
            await loop.sock_connect(s, (ip, port))
            log.debug(" [+++] Connected to %s\n", fhost)

            if data is None:
                log.debug(" [!!!] 'data' is None. Not transmitting any data to the host.")
            elif is_iter:
                i = 1
                for c in data_iter:
                    log.debug(" [...] Sending %s byte chunk (%s)\n", len(c), i)
                    await loop.sock_sendall(s, c)
            else:
                # We use 'sendall' to reliably send the entire contents of 'data' to the service we're connected to.
                log.debug(" [...] Sending %s bytes to %s ...\n", len(data), fhost)
                await loop.sock_sendall(s, data)
            # s.sendall(data)
            log.debug(" >> Reading response ...")
            res = b''
            i = 1
            while True:
                chunk = await loop.sock_recv(s, chunk_size)
                if not chunk: break
                res += chunk
                log.debug(" [...] Read %s byte chunk (%s)\n", len(chunk), i)
                i += 1
            if string_result:
                res = stringify(res)
                if strip_result: res = res.strip("\x00").strip().strip("\x00").strip()
            log.debug(" [+++] Got result ( %s bytes ) \n", len(res))
    except (socket.timeout, ConnectionRefusedError, ConnectionResetError, socket.gaierror) as e:
        if fail:
            raise e
        log.warning("Exception while connecting + sending data to: %s - reason: %s %s", fhost, type(e), str(e))
        return None
    return res


def send_data(
        host: str, port: int, data: Optional[Union[bytes, str, Iterable]] = None, timeout: Union[int, float] = None, **kwargs
) -> Optional[Union[str, bytes]]:
    """
        >>> from privex.helpers import send_data
        >>> send_data('termbin.com', 9999, "hello world\\nthis is a test\\n\\nlorem ipsum dolor\\n")
        'https://termbin.com/oi07'
    
    :param str host: The hostname or IPv4/v6 address to connect to
    :param port:     The port number to connect to on ``host``
    :param bytes|str|iter data:      The data to send to ``host:port`` via a TCP socket. Generally :class:`bytes` / :class:`str`.
                                     Can be an iterator/generator to send data in chunks. Can be ``None`` to disable sending data, instead
                                     only receiving and returning data.
    :param float|int timeout: Socket timeout. If not passed, uses the default from :func:`socket.getdefaulttimeout`.
                              If the global default timeout is ``None``, then falls back to ``15``
    :param kwargs:
    :keyword int chunk: (Default: ``64``) Maximum number of bytes to read into buffer per socket receive call.
    :keyword bool string_result: (Default: ``True``) If ``True``, the response sent by the server will be casted into a :class:`str`
                                 before returning it.
    :keyword bool strip_result: (Default: ``True``) This argument only works if ``string_result`` is also True.
                                If both ``string_result`` and ``strip_result`` are ``True``, the response sent by the server will
                                have whitespace, newlines, and null bytes trimmed from the start and end after it's casted into a string.
    :keyword bool fail: (Default: ``True``) If ``True``, will raise exceptions when connection errors occur. When ``False``, will simply
                        ``None`` if there are connection exceptions raised during this function's execution.
    :keyword str|int ip_version: (Default: ``any``)
    :return:
    """
    fhost = f"({host}):{port}"
    chunk_size = int(kwargs.get('chunk', kwargs.get('chunk_size', 64)))
    string_result = is_true(kwargs.get('string_result', True))
    strip_result = is_true(kwargs.get('strip_result', True))
    fail = is_true(kwargs.get('fail', True))
    ip_version = kwargs.get('ip_version', 'any')
    timeout = empty_if(timeout, empty_if(socket.getdefaulttimeout(), 15, zero=True), zero=True)

    is_iter, data_iter, is_v6, v4_address, host_is_ip = False, None, False, None, False

    if data is not None:
        if isinstance(data, (str, bytes, int, float)):
            data = byteify(data)
        else:
            try:
                data_iter = iter(data)
                is_iter = True
            except TypeError:
                # noinspection PyTypeChecker
                data = byteify(data)
    
    try:
        ip_network(host)
        host_is_ip = True
    except (TypeError, ValueError) as e:
        host_is_ip = False
    
    try:
        # First we resolve the IP address of 'host', so we can detect whether we're connecting to an IPv4 or IPv6 host,
        # letting us adjust the AF_INET variable accordingly.
        s_ver = socket.AF_INET
        ip = resolve_ip(host, ip_version)
    
        if ip_is_v6(ip):
            s_ver, is_v6 = socket.AF_INET6, True
            if not host_is_ip:
                try:
                    v4_address = resolve_ip(host, 'v4')
                except (socket.timeout, ConnectionRefusedError, ConnectionResetError, socket.gaierror, AttributeError) as e:
                    log.warning(
                        "Warning: failed to resolve IPv4 address for %s (to be used as a backup if IPv6 is broken). Reason: %s %s ",
                        type(e), str(e)
                    )
        
        fhost += f" (IP: {ip})"

    except (socket.timeout, ConnectionRefusedError, ConnectionResetError, socket.gaierror) as e:
        if fail:
            raise e
        log.warning("Exception while connecting + sending data to: %s - reason: %s %s", fhost, type(e), str(e))
        return None
    
    try:
        with socket.socket(s_ver, socket.SOCK_STREAM) as s:
            # Once we have our socket object, we set the timeout (by default it could hang forever), and open the connection.
            s.settimeout(timeout)
            log.debug(" [...] Connecting to host: %s", fhost)
            s.connect((ip, port))
            log.debug(" [+++] Connected to %s\n", fhost)
            
            if data is None:
                log.debug(" [!!!] 'data' is None. Not transmitting any data to the host.")
            elif is_iter:
                i = 1
                for c in data_iter:
                    log.debug(" [...] Sending %s byte chunk (%s)\n", len(c), i)
                    s.sock_sendall(c)
            else:
                # We use 'sendall' to reliably send the entire contents of 'data' to the service we're connected to.
                log.debug(" [...] Sending %s bytes to %s ...\n", len(data), fhost)
                s.sendall(data)
            # Once we've sent 'data',
            log.debug(" >> Reading response ...")
            res = b''
            i = 1
            while True:
                chunk = s.recv(chunk_size)
                if not chunk: break
                res += chunk
                log.debug(" [...] Read %s byte chunk (%s)\n", len(chunk), i)
                i += 1
            if string_result:
                res = stringify(res)
                if strip_result: res = res.strip("\x00").strip().strip("\x00").strip()
            log.debug(" [+++] Got result ( %s bytes ) \n", len(res))
    except (socket.timeout, ConnectionRefusedError, ConnectionResetError, socket.gaierror) as e:
        log.warning("Exception while connecting + sending data to: %s - reason: %s %s", fhost, type(e), str(e))
        if is_v6 and not empty(v4_address):
            log.warning(
                "Retrying connection to %s over IPv4 instead of IPv6. || IPv6 address: %s || IPv4 address: %s ",
                fhost, ip, v4_address
            )
            return send_data(host, port, data, timeout=timeout, **kwargs)

        if fail:
            raise e
        return None
    return res


def upload_termbin(data: Union[bytes, str], timeout: Union[int, float] = None, **kwargs) -> str:
    """
    Upload the :class:`bytes` / :class:`string` ``data`` to the pastebin service `TermBin`_ ,
    using the hostname and port defined in :attr:`privex.helpers.settings.TERMBIN_HOST`
    and :attr:`privex.helpers.settings.TERMBIN_PORT`
    
    NOTE - An AsyncIO version of this function is available: :func:`.upload_termbin_async`
    
    Returns the `TermBin`_ URL as a string - which is a raw download / viewing link for the paste.
    
    .. _TermBin:   https://termbin.com
    
        >>> my_data = "hello world\\nthis is a test\\n\\nlorem ipsum dolor\\n"
        >>> upload_termbin(my_data)
        'https://termbin.com/kerjk'
    
    :param bytes|str data:    The data to upload to `TermBin`_ - as either :class:`str` or :class:`bytes`
    :param float|int timeout: Socket timeout. If not passed, uses the default from :func:`socket.getdefaulttimeout`.
                              If the global default timeout is ``None``, then falls back to ``15``
    :return str url:   The `TermBin`_ URL to your paste as a string - which is a raw download / viewing link for the paste.
    """
    data = byteify(data)
    log.info(" [...] Uploading %s bytes to termbin ...\n", len(data))
    res = send_data(settings.TERMBIN_HOST, settings.TERMBIN_PORT, data, timeout=timeout, **kwargs)
    log.info(" [+++] Got termbin link: %s \n", res)
    
    return res


def upload_termbin_file(filename: str, timeout: int = 15, **kwargs) -> str:
    """
    Uploads the file ``filename`` to `TermBin`_ and returns the paste URL as a string.

    .. NOTE:: An AsyncIO version of this function is available: :func:`.upload_termbin_file_async`

    .. NOTE:: If the data you want to upload is already loaded into a variable - you can use :func:`.upload_termbin` instead,
              which accepts your data directly - through a :class:`str` or :class:`bytes` parameter

    .. _TermBin:   https://termbin.com

    :param str filename:      The path (absolute or relative) to the file you want to upload to `TermBin`_ - as a :class:`str`
    :param float|int timeout: Socket timeout. If not passed, uses the default from :func:`socket.getdefaulttimeout`.
                              If the global default timeout is ``None``, then falls back to ``15``
    :return str url:   The `TermBin`_ URL to your paste as a string - which is a raw download / viewing link for the paste.
    """
    log.info(" >> Uploading file '%s' to termbin", filename)
    
    with open(filename, 'rb') as fh:
        log.debug(" [...] Opened file %s - reading contents into RAM...", filename)
        data = fh.read()
        log.debug(" [+++] Loaded file into RAM. Total size: %s bytes", len(data))
    
    res = upload_termbin(data, timeout=timeout, **kwargs)
    log.info(" [+++] Uploaded file %s to termbin. Got termbin link: %s \n", filename, res)
    return res


async def upload_termbin_async(data: Union[bytes, str], timeout: Union[int, float] = None) -> str:
    """
    Upload the :class:`bytes` / :class:`string` ``data`` to the pastebin service `TermBin`_ ,
    using the hostname and port defined in :attr:`privex.helpers.settings.TERMBIN_HOST`
    and :attr:`privex.helpers.settings.TERMBIN_PORT`

    NOTE - A synchronous (non-async) version of this function is available: :func:`.upload_termbin`

    Returns the `TermBin`_ URL as a string - which is a raw download / viewing link for the paste.

    .. _TermBin:   https://termbin.com

        >>> my_data = "hello world\\nthis is a test\\n\\nlorem ipsum dolor\\n"
        >>> await upload_termbin_async(my_data)
        'https://termbin.com/kerjk'

    :param bytes|str data:    The data to upload to `TermBin`_ - as either :class:`str` or :class:`bytes`
    :param float|int timeout: Socket timeout. If not passed, uses the default from :func:`socket.getdefaulttimeout`.
                              If the global default timeout is ``None``, then falls back to ``15``
    :return str url:   The `TermBin`_ URL to your paste as a string - which is a raw download / viewing link for the paste.
    """
    data = byteify(data)
    log.info(" [...] Uploading %s bytes to termbin ...\n", len(data))
    res = await send_data_async(settings.TERMBIN_HOST, settings.TERMBIN_PORT, data, timeout=timeout)
    log.info(" [+++] Got termbin link: %s \n", res)
    
    return res


async def upload_termbin_file_async(filename: str, timeout: int = 15) -> str:
    """
    Uploads the file ``filename`` to `TermBin`_ and returns the paste URL as a string.
    
    .. NOTE:: A synchronous (non-async) version of this function is available: :func:`.upload_termbin_file`
    
    .. NOTE:: If the data you want to upload is already loaded into a variable - you can use :func:`.upload_termbin_async` instead,
              which accepts your data directly - through a :class:`str` or :class:`bytes` parameter

    
    .. _TermBin:   https://termbin.com

    :param str filename:      The path (absolute or relative) to the file you want to upload to `TermBin`_ - as a :class:`str`
    :param float|int timeout: Socket timeout. If not passed, uses the default from :func:`socket.getdefaulttimeout`.
                              If the global default timeout is ``None``, then falls back to ``15``
    :return str url:   The `TermBin`_ URL to your paste as a string - which is a raw download / viewing link for the paste.
    """
    log.info(" >> Uploading file '%s' to termbin", filename)
    
    with open(filename, 'rb') as fh:
        log.debug(" [...] Opened file %s - reading contents into RAM...", filename)
        data = fh.read()
        log.debug(" [+++] Loaded file into RAM. Total size: %s bytes", len(data))
    
    res = await upload_termbin_async(data, timeout=timeout)
    log.info(" [+++] Uploaded file %s to termbin. Got termbin link: %s \n", filename, res)
    return res
