# Copyright (c) 2022-2025 José Manuel Barroso Galindo <theypsilon@gmail.com>

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

from update_all.analogue_pocket.http_gateway import fetch
from update_all.logger import Logger
from update_all.file_system import FileSystem
from update_all.config import Config
from update_all.os_utils import context_from_curl_ssl
from update_all.other import GenericProvider
from update_all.constants import FILE_retroaccount_user_json, FILE_retroaccount_device_id, API_retroaccount_access_mister


class RetroAccountService:
    def __init__(self, logger: Logger, file_system: FileSystem, config_provider: GenericProvider[Config]):
        self._logger = logger
        self._file_system = file_system
        self._config_provider = config_provider

    def validate_user_session(self) -> None:
        if not self._config_provider.get().retroaccount_feature_flag:
            return

        self._logger.bench('RetroAccountService.validate_user_session start')
        try:
            self._validate_user_session_impl()
        except Exception as e:
            self._logger.debug(f'Session validation failed: {e}')

        self._logger.bench('RetroAccountService.validate_user_session end')

    def _validate_user_session_impl(self) -> None:
        if not self._file_system.is_file(FILE_retroaccount_user_json):
            return

        user_data = self._file_system.load_dict_from_file(FILE_retroaccount_user_json)
        device_id = user_data.get('device_id', '')
        refresh_token = user_data.get('refresh_token', '')

        if not device_id or not refresh_token:
            return

        config = self._config_provider.get()
        api_url = f'{config.retroaccount_domain}{API_retroaccount_access_mister}'
        ssl_ctx, ssl_err = context_from_curl_ssl(config.curl_ssl)
        if ssl_err is not None:
            self._logger.debug(f'SSL context warning: {ssl_err}')

        headers = {
            'x-refresh-token': refresh_token,
            'x-device-id': device_id,
        }
        status_code, raw_body = fetch(api_url, headers=headers, ssl_ctx=ssl_ctx, timeout=30, retry=0)
        body = raw_body.decode()

        if status_code == 200:
            response_data = json.loads(body)
            new_refresh_token = response_data.get('tokens', {}).get('refresh_token')
            if new_refresh_token:
                self._logger.debug(f'New refresh token!')
                user_data['refresh_token'] = new_refresh_token
                self._file_system.make_dirs_parent(FILE_retroaccount_user_json)
                self._file_system.save_json(user_data, FILE_retroaccount_user_json)
        elif status_code in (401, 403):
            self._logger.debug(f'User session revoked ({status_code}')
            self._file_system.make_dirs_parent(FILE_retroaccount_device_id)
            self._file_system.write_file_contents(FILE_retroaccount_device_id, device_id)
            self._file_system.unlink(FILE_retroaccount_user_json, verbose=False)
        else:
            raise Exception(f'API returned status {status_code}: {body}')
