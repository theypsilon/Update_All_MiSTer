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

from typing import Optional, Dict, Any

from update_all.logger import Logger
from update_all.file_system import FileSystem
from update_all.config import Config
from update_all.other import GenericProvider
from update_all.constants import FILE_retroaccount_user_json, FILE_retroaccount_device_id
from update_all.encryption import Encryption
from update_all.retroaccount_gateway import RetroAccountGateway, SessionResult, MisterSyncResponse
from update_all.retroaccount_ui import DeviceLogin, DeviceLoginRenderer, RetroAccountClient
from update_all.ui_engine import UiSection
from update_all.ui_engine_dialog_application import UiDialogDrawer

_DEFAULT_CLIENT_ID = "update-all-mister"


class RetroAccountService(RetroAccountClient):
    def __init__(self, logger: Logger, file_system: FileSystem, config_provider: GenericProvider[Config], retroaccount_gateway: RetroAccountGateway, encryption: Encryption):
        self._logger = logger
        self._file_system = file_system
        self._config_provider = config_provider
        self._retroaccount_gateway = retroaccount_gateway
        self._encryption = encryption

    @property
    def server_url(self) -> str:
        return self._config_provider.get().retroaccount_domain

    def is_feature_enabled(self) -> bool:
        return self._config_provider.get().retroaccount_feature_flag

    def get_login_state(self) -> bool:
        return self._file_system.is_file(FILE_retroaccount_user_json)

    def get_existing_device_id(self) -> Optional[str]:
        if self._file_system.is_file(FILE_retroaccount_device_id):
            return self._file_system.read_file_contents(FILE_retroaccount_device_id).strip() or None
        return None

    def create_device_login_ui(self, drawer: UiDialogDrawer, renderer: DeviceLoginRenderer, data: Dict[str, Any]) -> UiSection:
        return DeviceLogin(drawer, renderer, self, data)

    def request_device_code(self) -> Optional[dict]:
        return self._retroaccount_gateway.request_device_code(_DEFAULT_CLIENT_ID, device_id=self.get_existing_device_id())

    def poll_for_token(self, device_code: str, device_id: Optional[str] = None) -> Optional[dict]:
        result = self._retroaccount_gateway.poll_for_token(device_code, _DEFAULT_CLIENT_ID, device_id=device_id)
        if result is None:
            self._logger.debug('@', end='')
        else:
            if 'status' in result and result['status'] == 'unauthorized':
                self._logger.print('WARNING: Device code ', device_code, ' unauthorized for device id ', device_id)
            else:
                self._logger.print('Device code ', device_code, ' authorized for device id ', device_id)
        return result

    def mister_sync(self) -> None:
        if not self._config_provider.get().retroaccount_feature_flag:
            return

        self._logger.bench('RetroAccountService.mister_sync start')
        try:
            self._mister_sync_impl()
        except Exception as e:
            self._logger.debug('RetroAccountService.mister_sync failed:')
            self._logger.debug(e)

        self._logger.bench('RetroAccountService.mister_sync end')

    def _mister_sync_impl(self) -> None:
        if not self._file_system.is_file(FILE_retroaccount_user_json):
            self._logger.print('RetroAccount: Nothing to sync.')
            return

        try:
            user_data = self._file_system.load_dict_from_file(FILE_retroaccount_user_json)
        except Exception as e:
            self._logger.debug('RetroAccountService: Could not read user data for sync')
            self._logger.debug(e)
            self._file_system.unlink(FILE_retroaccount_user_json, verbose=False)
            return

        device_id = user_data.get('device_id', '')
        refresh_token = user_data.get('refresh_token', '')

        if not device_id or not refresh_token:
            self._logger.print(f'RetroAccount Warning: Corrupted {FILE_retroaccount_user_json}')
            return

        patreon_key_fingerprint = None
        patreon_key_path = self._config_provider.get().patreon_key_path
        if self._file_system.is_file(patreon_key_path):
            try:
                patreon_key_fingerprint = self._file_system.hash(patreon_key_path)
            except Exception as e:
                self._logger.debug(f"RetroAccountService: Update All Patreon Key could not be hashed")
                self._logger.debug(e)

        self._logger.bench('RetroAccountService Gateway mister_sync start')
        result, response = self._retroaccount_gateway.mister_sync(device_id, refresh_token, patreon_key_fingerprint)
        self._logger.bench('RetroAccountService Gateway mister_sync end')

        if result == SessionResult.VALID and isinstance(response, dict):
            new_refresh_token = response.get('tokens', {}).get('refresh_token')
            if new_refresh_token:
                self._logger.debug(f'RetroAccountService: New refresh token!')
                user_data['refresh_token'] = new_refresh_token
                self._file_system.make_dirs_parent(FILE_retroaccount_user_json)
                self._file_system.save_json(user_data, FILE_retroaccount_user_json)

            self._process_mister_response(response)

        elif result == SessionResult.REVOKED:
            self._logger.debug(f'RetroAccountService: User session revoked', response)
            self._file_system.make_dirs_parent(FILE_retroaccount_device_id)
            self._file_system.write_file_contents(FILE_retroaccount_device_id, device_id)
            self._file_system.unlink(FILE_retroaccount_user_json, verbose=False)

        else:
            self._logger.debug(f'RetroAccountService: MiSTer sync API returned status {response}.')

    def _process_mister_response(self, response_dict: MisterSyncResponse) -> None:
        update_all_patreon_key_path = self._config_provider.get().patreon_key_path
        if response_dict.get('update_all_patreon_key_remove', False):
            try:
                self._file_system.unlink(update_all_patreon_key_path, verbose=False)
                self._encryption.clear_cache()
            except Exception as e:
                self._logger.debug('RetroAccountService: Error during removal of update all patreon key.')
                self._logger.debug(e)

        update_all_patreon_key_url = response_dict.get('update_all_patreon_key_url', None)
        if isinstance(update_all_patreon_key_url, str):
            try:
                self._retroaccount_gateway.install_file(update_all_patreon_key_path, update_all_patreon_key_url)
                self._encryption.clear_cache()
                self._logger.debug(f'RetroAccountService: New update_all.patreonkey installed at {update_all_patreon_key_path}!')
            except Exception as e:
                self._logger.debug('RetroAccountService: Could not install update all patreon key.')
                self._logger.debug(e)

    def save_login_credentials(self, credentials: dict) -> bool:
        device_id = credentials.get("device_id", "")
        if not device_id:
            self._logger.debug("RetroAccountService: Login succeeded but missing device_id in credentials")
            return False

        try:
            self._file_system.make_dirs_parent(FILE_retroaccount_device_id)
            self._file_system.write_file_contents(FILE_retroaccount_device_id, device_id)
        except Exception as e:
            self._logger.debug("RetroAccountService: Could not create device.id")
            self._logger.debug(e)

        try:
            self._file_system.make_dirs_parent(FILE_retroaccount_user_json)
            self._file_system.save_json(credentials, FILE_retroaccount_user_json)
        except Exception as e:
            self._logger.debug("RetroAccountService: Could not create user.json")
            self._logger.debug(e)
            return False

        self.mister_sync()
        return True

    def device_logout(self) -> bool:
        if not self._file_system.is_file(FILE_retroaccount_user_json):
            return False

        try:
            user_data = self._file_system.load_dict_from_file(FILE_retroaccount_user_json)
        except Exception as e:
            self._logger.debug('RetroAccountService: Device logout could not read user data')
            self._logger.debug(e)
            self._file_system.unlink(FILE_retroaccount_user_json, verbose=False)
            return True

        device_id = user_data.get('device_id', '')
        refresh_token = user_data.get('refresh_token', '')

        if device_id and refresh_token:
            self._retroaccount_gateway.post_device_logout(refresh_token, device_id)

        self._file_system.unlink(FILE_retroaccount_user_json, verbose=False)
        return True
