# Copyright (c) 2022-2026 José Manuel Barroso Galindo <theypsilon@gmail.com>

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
# https://github.com/theypsilon/Update_All_MiSTer

import json
import socket
import ssl
import threading
import time
from http.client import HTTPException
from typing import Optional, Any, Tuple

from update_all.analogue_pocket.http_gateway import HttpGateway, HttpLogger, write_stream_to_data
from update_all.config import Config
from update_all.other import GenericProvider


_RETRYABLE_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})


def context_from_curl_ssl(curl_ssl) -> Tuple[ssl.SSLContext, Optional[Exception]]:
    try:
        context = ssl.create_default_context()

        if curl_ssl.startswith('--cacert '):
            cacert_file = curl_ssl[len('--cacert '):]
            context.load_verify_locations(cacert_file)
        elif curl_ssl == '--insecure':
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        return context, None
    except Exception as e:
        return ssl.create_default_context(), e


class Fetcher:
    def __init__(self, config_provider: GenericProvider[Config], logger: Optional[HttpLogger] = None):
        self._config_provider = config_provider
        self._logger = logger
        self._gw: Optional[HttpGateway] = None
        self._lock = threading.Lock()
        self._cleaned_up = False

    def _get_gw(self) -> HttpGateway:
        with self._lock:
            if self._cleaned_up:
                raise RuntimeError('Fetcher: already cleaned up')
            if self._gw is None:
                config = self._config_provider.get()
                ssl_ctx, ssl_err = context_from_curl_ssl(config.curl_ssl)
                if ssl_err is not None:
                    raise RuntimeError(f'Fetcher: SSL context error: {ssl_err}')

                self._gw = HttpGateway(
                    ssl_ctx=ssl_ctx or ssl.create_default_context(),
                    timeout=300,
                    logger=self._logger,
                    config=config.http_config,
                )
            return self._gw

    def cleanup(self) -> None:
        with self._lock:
            self._cleaned_up = True
            if self._gw is not None:
                self._gw.cleanup()
                self._gw = None

    def fetch(self, url: str, method: Optional[str] = None, body: Any = None, headers: Any = None, timeout: Optional[float] = None, retry: int = 3) -> Tuple[int, bytes]:
        if isinstance(body, dict):
            if len(body) == 0:
                body = None
            else:
                body = json.dumps(body)
                if not headers:
                    headers = {}
                headers['Content-Type'] = 'application/json'

        timeout = timeout or 300
        gw = self._get_gw()
        last_exception: Optional[Exception] = None
        last_status = 0
        last_data = b''
        for attempt in range(1 + retry):
            if self._cleaned_up:
                break

            try:
                with gw.open(url, method, body, headers) as (final_url, in_stream):
                    data, _ = write_stream_to_data(in_stream, False, timeout)
                    last_status = in_stream.status
                    last_data = data
                    if last_status not in _RETRYABLE_STATUS_CODES:
                        return last_status, last_data
            except (TimeoutError, socket.timeout, OSError, HTTPException) as e:
                last_exception = e

            if attempt < retry:
                delay = min(1 << attempt, 600)
                if self._logger is not None:
                    self._logger.debug(f'Retry {attempt + 1}/{retry} for {url} in {delay}s')
                deadline = time.monotonic() + delay
                while not self._cleaned_up and time.monotonic() < deadline:
                    time.sleep(0.25)

        if last_status != 0:
            return last_status, last_data

        if last_exception is None:
            raise RuntimeError('Fetcher: fetch aborted')

        raise last_exception
