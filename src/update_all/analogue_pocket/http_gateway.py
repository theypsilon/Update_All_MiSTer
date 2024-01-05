# Copyright (c) 2021-2024 José Manuel Barroso Galindo <theypsilon@gmail.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# You can download the latest version of this tool from:
# https://github.com/MiSTer-devel/Downloader_MiSTer
import ssl
import time
import abc
import os
from contextlib import contextmanager
from typing import Tuple, Any, Optional, Generator, List, Dict, Callable, Union
from urllib.parse import urlparse, ParseResult
from http.client import HTTPConnection, HTTPSConnection, HTTPResponse, HTTPException


class HttpGatewayException(Exception):
    pass


class _Connection(abc.ABC):
    @abc.abstractmethod
    def do_request(self, method: str, url: str, body: Any, headers: Any) -> None: pass
    @abc.abstractmethod
    def kill(self) -> None: pass
    @abc.abstractmethod
    def set_timeout(self, timeout: float) -> None: pass
    @abc.abstractmethod
    def is_expired(self, now_time: float) -> bool: pass
    @abc.abstractmethod
    def set_last_use_time(self, t: float) -> None: pass
    @property
    @abc.abstractmethod
    def response(self) -> HTTPResponse: pass
    @abc.abstractmethod
    def finish_response(self) -> None: pass
    @abc.abstractmethod
    def response_connection_header(self) -> str: pass
    @abc.abstractmethod
    def response_keep_alive(self) -> str: pass
    @abc.abstractmethod
    def response_location_header(self) -> Optional[str]: pass
    @abc.abstractmethod
    def response_version_text(self) -> str: pass


class HttpGateway:
    def __init__(self, ssl_ctx: ssl.SSLContext, timeout: int, logger = None):
        self._ssl_ctx = ssl_ctx
        self._timeout = timeout
        self._logger = logger
        self._connections: Dict[str, _ConnectionQueue] = {}
        self._clean_connections_timer = time.time()

    def __enter__(self): return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and self._logger is not None:
            self._logger.print(f"An exception of type {exc_type} occurred with value {exc_val}. Traceback: {exc_tb}")

        self.cleanup()
        return False

    def cleanup(self) -> None:
        total_cleared = 0
        for queue in self._connections.values():
            total_cleared += queue.size()
            queue.clear_all()
        self._connections = {}
        if self._logger is not None: self._logger.debug(f'Cleaning up {total_cleared} connections.')

    def _take_connection(self, parsed_url) -> _Connection:
        queue_id = parsed_url.scheme + parsed_url.netloc
        if queue_id not in self._connections:
            self._connections[queue_id] = _ConnectionQueue(
                lambda: _HttpConnectionAdapter(
                    http=_create_http_connection(parsed_url, timeout=self._timeout, context=self._ssl_ctx)
                )
            )
        return self._connections[queue_id].pull()

    def _clean_timeout_connections(self, now: float) -> None:
        if now - self._clean_connections_timer < 30.0:
            return
        self._clean_connections_timer = now

        if self._logger is not None: self._logger.debug('Checking keep-alive timeouts...')

        for queue_id, queue in self._connections.items():
            cleaned_up_connections = queue.clear_timed_outs(now)
            if cleaned_up_connections > 0 and self._logger is not None:
                self._logger.debug(f'Cleaning up {cleaned_up_connections} connections "{queue_id}".')

    @contextmanager
    def open(self, url: str, method: str = None, body: Any = None, headers: Any = None) -> Generator[Tuple[str, HTTPResponse], None, None]:
        if self._logger is not None: self._logger.debug('^^^^')
        final_url, conn = self._open_impl(
            url,
            'GET' if method is None else method.upper(),
            body,
            headers or _default_headers,
            0
        )
        if self._logger is not None: self._logger.debug(f'HTTP {conn.response.status}: {final_url}\nvvvv\n')
        try:
            yield final_url, conn.response
        finally:
            conn.finish_response()

    def _open_impl(self, url: str, method: str, body: Any, headers: Any, retry: int) -> Tuple[str, _Connection]:
        self._clean_timeout_connections(time.time())
        retry, conn = self._request(url, method, body, headers, retry)

        if self._logger is not None: self._logger.debug(conn.response_version_text())
        if 300 <= conn.response.status < 400 and retry < 10:
            location = conn.response_location_header()
            if location is not None:
                if self._logger is not None: self._logger.debug(f'HTTP 3XX! Resource moved ({retry}): {url}')
                conn.finish_response()
                return self._open_impl(location, method, body, headers, retry + 1)

        return url, conn

    def _request(self, url: str, method: str, body: Any, headers: Any, retry: int) -> Tuple[int, _Connection]:
        parsed_url = urlparse(url)
        conn = self._take_connection(parsed_url)
        try:
            conn.do_request(method, self._request_url(parsed_url), body, headers)
        except (HTTPException, OSError) as e:
            if self._logger is not None: self._logger.debug(f'Closing "{parsed_url.netloc}".')
            conn.kill()
            if retry < 10:
                if self._logger is not None: self._logger.debug(f'HTTP Exception! {type(e).__name__} ({retry}): {url} {str(e)}')
                return self._request(url, method, body, headers, retry + 1)
            else:
                raise e

        if self._is_a_keep_alive_connection(conn):
            self._handle_keep_alive(conn)

        return retry, conn

    @staticmethod
    def _request_url(parsed_url: ParseResult) -> str:
        url_path = parsed_url.path
        while len(url_path) > 0 and url_path[0] == '/':
            url_path = url_path.lstrip('/')
        return f'/{url_path}?{parsed_url.query}'.rstrip('?')

    def _handle_keep_alive(self, connection: _Connection) -> None:
        connection_header = connection.response_connection_header()
        connection.set_last_use_time(time.time())
        keep_alive_timeout = self._get_keep_alive_timeout(connection_header, connection.response_keep_alive())
        if keep_alive_timeout is not None:
            connection.set_timeout(keep_alive_timeout)

    def _is_a_keep_alive_connection(self, conn: _Connection) -> bool:
        version = conn.response.version
        connection_header = conn.response_connection_header()
        is_keep_alive = (version == 10 and connection_header == 'keep-alive') or (version >= 11 and connection_header != 'close')
        if not is_keep_alive and self._logger is not None: self._logger.debug(f'Version: {version}, Connection: {connection_header}')
        return is_keep_alive

    def _get_keep_alive_timeout(self, connection_header: str, keep_alive_header: str) -> Optional[float]:
        if connection_header == '' or keep_alive_header == '':
            return None

        for p in keep_alive_header.split(','):
            kv = p.split('=')
            if len(kv) == 2 and kv[0].strip().lower() == 'timeout':
                try:
                    return float(kv[1].strip())
                except Exception as e:
                    if self._logger is not None: self._logger.debug(f"Could not parse keep-alive timeout on: {p}", e)
                    return None

        return None


def _create_http_connection(parsed_url: ParseResult, timeout: int, context: ssl.SSLContext) -> HTTPConnection:
    if parsed_url.scheme == 'http':
        return HTTPConnection(parsed_url.netloc, timeout=timeout)
    elif parsed_url.scheme == 'https':
        return HTTPSConnection(parsed_url.netloc, timeout=timeout, context=context)
    else:
        raise ValueError(f'Unsupported scheme "{parsed_url.scheme}" for url: {parsed_url.geturl()}')


_default_headers = {'Connection': 'Keep-Alive', 'Keep-Alive': 'timeout=120'}


class _FinishedResponse:
    pass


class _HttpConnectionAdapter(_Connection):
    _http: HTTPConnection
    _last_use_time: float = 0.0
    _timeout: float = 120.0
    _response: Optional[Union[HTTPResponse, _FinishedResponse]] = None
    _connection_header: Optional[str] = None

    def __init__(self, http: HTTPConnection):
        self._http = http
        if http.timeout is not None:
            self._timeout = http.timeout

    def is_expired(self, now_time: float) -> bool:
        expire_time = self._last_use_time + self._timeout
        return now_time > expire_time

    def do_request(self, method: str, url: str, body: Any, headers: Any) -> None:
        try:
            self._http.request(method, url, headers=headers, body=body)
        except BrokenPipeError:
            pass
        self._response = self._http.getresponse()
        self._connection_header = self.response.headers.get('Connection', '').lower()

    def kill(self) -> None:
        self.finish_response()
        self._http.close()
        self._last_use_time = 0
        self._timeout = 0

    def set_last_use_time(self, t: float) -> None:
        self._last_use_time = t

    def response_connection_header(self):
        return self._connection_header

    def response_keep_alive(self) -> str:
        return self.response.headers.get('Keep-Alive', '')

    @property
    def response(self) -> HTTPResponse:
        if self._response is None: raise HttpGatewayException('No response available.')
        elif isinstance(self._response, _FinishedResponse): raise HttpGatewayException('Response is already finished.')
        return self._response

    def response_location_header(self) -> Optional[str]:
        return self.response.headers.get('location', None)

    def finish_response(self):
        if isinstance(self._response, _FinishedResponse): return
        if self._response is not None:
            self._response.close()
        self._response = _FinishedResponse()

    def set_timeout(self, timeout: float) -> None:
        self._timeout = timeout

    def response_version_text(self) -> str:
        return f'Version: {self.response.version}\n{self.response.headers}'


class _ConnectionQueue:
    def __init__(self, factory: Callable[[], _Connection]):
        self._factory = factory
        self._queue: List[_Connection] = []

    def pull(self) -> _Connection:
        if len(self._queue) == 0:
            return _ConnectionHandler(self._factory(), self)
        return _ConnectionHandler(self._queue.pop(), self)

    def push(self, connection: _Connection) -> None:
        self._queue.append(connection)

    def size(self) -> int:
        return len(self._queue)

    def clear_all(self) -> None:
        for connection in self._queue:
            connection.kill()
        self._queue = []

    def clear_timed_outs(self, now: float) -> int:
        expired_connections = [c for c in self._queue if c.is_expired(now)]
        for connection in expired_connections:
            connection.kill()
            self._queue.remove(connection)
        return len(expired_connections)


class _ConnectionHandler(_Connection):

    def __init__(self, connection, connection_queue):
        self._connection: _Connection = connection
        self._connection_queue: _ConnectionQueue = connection_queue

    def is_expired(self, now_time: float) -> bool:
        return self._connection.is_expired(now_time)

    def finish_response(self) -> None:
        self._connection.finish_response()
        self._connection_queue.push(self._connection)

    def kill(self) -> None:
        self._connection.kill()

    def do_request(self, method: str, url: str, body: Any, headers: Any) -> None:
        self._connection.do_request(method, url, body, headers)

    def set_timeout(self, timeout: float) -> None:
        self._connection.set_timeout(timeout)

    def set_last_use_time(self, t: float) -> None:
        self._connection.set_last_use_time(t)

    @property
    def response(self) -> HTTPResponse:
        return self._connection.response

    def response_version_text(self) -> str:
        return self._connection.response_version_text()

    def response_location_header(self) -> Optional[str]:
        return self._connection.response_location_header()

    def response_connection_header(self):
        return self._connection.response_connection_header()

    def response_keep_alive(self) -> str:
        return self._connection.response_keep_alive()


is_windows = os.name == 'nt'
COPY_BUFSIZE = 1024 * 1024 if is_windows else 64 * 1024


def write_incoming_stream(in_stream: Any, target_path: str, timeout: int):
    start_time = time.time()
    with open(target_path, 'wb') as out_file:
        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                raise TimeoutError(f"Copy operation timed out after {timeout} seconds")

            buf = in_stream.read(COPY_BUFSIZE)
            if not buf:
                break
            out_file.write(buf)