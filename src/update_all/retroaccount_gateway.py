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
from enum import unique, Enum
from typing import Optional, Tuple, Any, TypedDict, Union

from update_all.config import Config
from update_all.constants import API_retroaccount_mister_sync, API_retroaccount_device_logout, API_retroaccount_device_login_code, API_retroaccount_token_poll
from update_all.fetcher import Fetcher
from update_all.file_system import FileSystem
from update_all.logger import Logger
from update_all.other import GenericProvider


class _MisterSyncTokens(TypedDict, total=False):
    refresh_token: str
    access_token: str


class MisterSyncResponse(TypedDict, total=False):
    tokens: _MisterSyncTokens
    update_all_patreon_key_url: str
    update_all_patreon_key_remove: bool


@unique
class SessionResult(Enum):
    VALID = 'valid'
    REVOKED = 'revoked'
    ERROR = 'error'


class RetroAccountGateway:
    def __init__(self, config_provider: GenericProvider[Config], logger: Logger, file_system: FileSystem, fetcher: Fetcher):
        self._config_provider = config_provider
        self._logger = logger
        self._file_system = file_system
        self._fetcher = fetcher

    def _server_url(self) -> str:
        return self._config_provider.get().retroaccount_domain

    def mister_sync(self, device_id: str, refresh_token: str, update_all_patreon_key_fingerprint: Optional[str]) -> Tuple[SessionResult, Union[MisterSyncResponse, int]]:
        body = {}
        if update_all_patreon_key_fingerprint:
            body['update_all_patreon_key_fingerprint'] = update_all_patreon_key_fingerprint
        headers = {
            'x-refresh-token': refresh_token,
            'x-device-id': device_id,
        }
        try:
            status_code, raw_body_response = self._fetcher.fetch(f'{self._server_url()}{API_retroaccount_mister_sync}', method='POST', body=body, headers=headers, timeout=10)
        except Exception as e:
            self._logger.debug('RetroAccountGateway: mister_sync fetch failed')
            self._logger.debug(e)
            return SessionResult.ERROR, 0
        body_response = raw_body_response.decode()

        if status_code == 200:
            response_data = json.loads(body_response)
            return SessionResult.VALID, response_data
        elif status_code in (401, 403):
            return SessionResult.REVOKED, status_code
        else:
            return SessionResult.ERROR, status_code

    def post_device_logout(self, refresh_token: str, device_id: str) -> int:
        headers = {
            'x-refresh-token': refresh_token,
            'x-device-id': device_id,
        }
        try:
            status_code, _ = self._fetcher.fetch(f'{self._server_url()}{API_retroaccount_device_logout}', method='POST', headers=headers, timeout=10)
        except Exception as e:
            self._logger.debug('RetroAccountGateway: post_device_logout fetch failed')
            self._logger.debug(e)
            return 0
        self._logger.debug(f'RetroAccountGateway: Device logout status: {status_code}')
        return status_code

    def request_device_code(self, client_id: str, device_id: Optional[str] = None) -> Optional[dict]:
        payload: dict[str, Any] = {'client_id': client_id}
        if device_id:
            payload['device_id'] = device_id
        try:
            status, raw = self._fetcher.fetch(f'{self._server_url()}{API_retroaccount_device_login_code}', method='POST', body=payload, timeout=10)
        except Exception as e:
            self._logger.debug('RetroAccountGateway: request_device_code fetch failed')
            self._logger.debug(e)
            return None
        if status != 200:
            self._logger.debug(f'RetroAccountGateway: request_device_code failed with status {status}')
            return None
        return json.loads(raw.decode('utf-8')) if raw else {}

    def poll_for_token(self, device_code: str, client_id: str, device_id: Optional[str] = None) -> Optional[dict]:
        payload: dict[str, Any] = {'device_code': device_code, 'client_id': client_id}
        if device_id:
            payload['device_id'] = device_id
        try:
            status, raw = self._fetcher.fetch(f'{self._server_url()}{API_retroaccount_token_poll}', method='POST', body=payload, timeout=10)
        except Exception as e:
            self._logger.debug('RetroAccountGateway: poll_for_token fetch failed')
            self._logger.debug(e)
            return None
        if status == 200:
            return json.loads(raw.decode('utf-8')) if raw else {}
        if status == 428:
            return None
        if status in (401, 403):
            return {'status': 'unauthorized'}
        self._logger.debug(f'RetroAccountGateway: poll_for_token failed with status {status}')
        return None

    def install_file(self, file_path: str, file_url: str) -> None:
        status, data = self._fetcher.fetch(file_url, timeout=30)
        if status != 200:
            raise RuntimeError(f'install_file failed: HTTP {status} for {file_url}')
        self._file_system.make_dirs_parent(file_path)
        self._file_system.write_file_bytes(file_path, data)
