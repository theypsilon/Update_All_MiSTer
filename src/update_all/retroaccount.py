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

from dataclasses import dataclass
from typing import Optional, Any

from update_all.logger import Logger
from update_all.file_system import FileSystem
from update_all.config import Config
from update_all.other import GenericProvider
from update_all.constants import FILE_retroaccount_user_json, FILE_retroaccount_device_id, FILE_patreon_key_md5, \
    FILE_patreon_key_prev
from update_all.encryption import Encryption, EncryptionResult
from update_all.retroaccount_gateway import RetroAccountGateway, SessionResult, MisterSyncResponse
from update_all.retroaccount_ui import DeviceLogin, DeviceLoginRenderer, RetroAccountClient
from update_all.ui_engine import UiSection
from update_all.ui_engine_dialog_application import UiDialogDrawer

_DEFAULT_CLIENT_ID = "update-all-mister"
_CORRUPTED_CREDENTIALS_MESSAGE = 'Your credentials are corrupted!\nDo you have any problems with your storage (SD)?'
_REVOKED_CREDENTIALS_MESSAGE = 'Your credentials were revoked!\nYour account must be active, and you have to log in on each device you use.'


@dataclass(frozen=True)
class _SyncTransition:
    update_all_extras_active: Optional[bool] = None
    save_device_id: Optional[str] = None
    save_user_json: Optional[dict[str, Any]] = None
    remove_user_json: bool = False
    remove_update_all_patreon_key: bool = False
    install_update_all_patreon_key_url: Optional[str] = None
    credentials_were_corrupted: bool = False
    credentials_were_revoked: bool = False


class RetroAccountService(RetroAccountClient):
    def __init__(self, logger: Logger, file_system: FileSystem, config_provider: GenericProvider[Config], retroaccount_gateway: RetroAccountGateway, encryption: Encryption):
        self._logger = logger
        self._file_system = file_system
        self._config_provider = config_provider
        self._retroaccount_gateway = retroaccount_gateway
        self._encryption = encryption
        self._has_installed_update_all_patreon_key = False
        self._has_forced_logout = None
        self._update_all_extras: Optional[bool] = None

    def has_installed_update_all_patreon_key(self) -> bool: return self._has_installed_update_all_patreon_key
    def has_forced_logout(self) -> Optional[str]: return self._has_forced_logout

    @property
    def server_url(self) -> str:
        return self._config_provider.get().retroaccount_domain

    def is_update_all_extras_active(self) -> bool:
        if self._update_all_extras is None:
            return self._encryption.validate_key() == EncryptionResult.Success
        return self._update_all_extras

    def get_login_state(self) -> bool:
        return self._file_system.is_file(FILE_retroaccount_user_json)

    def get_existing_device_id(self) -> Optional[str]:
        if self._file_system.is_file(FILE_retroaccount_device_id):
            return self._file_system.read_file_contents(FILE_retroaccount_device_id).strip() or None
        return None

    def create_device_login_ui(self, drawer: UiDialogDrawer, renderer: DeviceLoginRenderer, data: dict[str, Any]) -> UiSection:
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
        self._logger.bench('RetroAccountService.mister_sync start')
        self._reset_sync_effects()
        try:
            transition = self._build_mister_sync_transition()
            if transition is not None:
                self._apply_sync_transition(transition)
        except Exception as e:
            self._logger.debug('RetroAccountService.mister_sync failed:')
            self._logger.debug(e)

        self._logger.bench('RetroAccountService.mister_sync end')

    def _build_mister_sync_transition(self) -> Optional[_SyncTransition]:
        if not self._file_system.is_file(FILE_retroaccount_user_json):
            self._logger.print('RetroAccount: Nothing to sync.')
            return _SyncTransition(
                remove_update_all_patreon_key=True,
                update_all_extras_active=False,
            )

        try:
            user_data = self._file_system.load_dict_from_file(FILE_retroaccount_user_json)
        except Exception as e:
            self._logger.debug('RetroAccountService: Could not read user data for sync')
            self._logger.debug(e)
            return _SyncTransition(
                remove_user_json=True,
                remove_update_all_patreon_key=True,
                update_all_extras_active=False,
                credentials_were_corrupted=True,
            )

        credentials = self._read_sync_credentials(user_data)
        if credentials is None:
            self._logger.print(f'RetroAccount Warning: Corrupted {FILE_retroaccount_user_json}')
            return _SyncTransition(
                remove_update_all_patreon_key=True,
                update_all_extras_active=False,
                credentials_were_corrupted=True,
            )

        device_id, refresh_token = credentials

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
            updated_user_data = None
            new_refresh_token = response.get('tokens', {}).get('refresh_token')
            if isinstance(new_refresh_token, str) and new_refresh_token.strip():
                self._logger.debug(f'RetroAccountService: New refresh token!')
                updated_user_data = {'device_id': device_id, 'refresh_token': new_refresh_token.strip()}

            update_all_patreon_key_url = response.get('update_all_patreon_key_url', None)
            update_all_patreon_key_url = update_all_patreon_key_url.strip() if isinstance(update_all_patreon_key_url, str) else None
            return _SyncTransition(
                save_user_json=updated_user_data,
                install_update_all_patreon_key_url=update_all_patreon_key_url,
                remove_update_all_patreon_key=response.get('update_all_patreon_key_remove', False) is True,
                update_all_extras_active=response.get('update_all_extras', False) is True,
            )

        if result == SessionResult.REVOKED:
            self._logger.debug(f'RetroAccountService: User session revoked', response)
            return _SyncTransition(
                save_device_id=device_id,
                remove_user_json=True,
                remove_update_all_patreon_key=True,
                update_all_extras_active=False,
                credentials_were_revoked=True,
            )

        self._logger.debug(f'RetroAccountService: MiSTer sync API returned status {response}.')
        return None

    def _reset_sync_effects(self) -> None:
        self._has_installed_update_all_patreon_key = False
        self._has_forced_logout = None

    @staticmethod
    def _read_sync_credentials(user_data: dict[str, Any]) -> Optional[tuple[str, str]]:
        device_id = user_data.get('device_id')
        refresh_token = user_data.get('refresh_token')
        if not isinstance(device_id, str) or not isinstance(refresh_token, str):
            return None

        device_id = device_id.strip()
        refresh_token = refresh_token.strip()
        if not device_id or not refresh_token:
            return None

        return device_id, refresh_token

    def _apply_sync_transition(self, transition: _SyncTransition) -> None:
        if transition.update_all_extras_active is not None:
            self._update_all_extras = transition.update_all_extras_active

        if transition.save_device_id:
            self._file_system.make_dirs_parent(FILE_retroaccount_device_id)
            self._file_system.write_file_contents(FILE_retroaccount_device_id, transition.save_device_id)

        if transition.save_user_json is not None:
            self._file_system.make_dirs_parent(FILE_retroaccount_user_json)
            self._file_system.save_json(transition.save_user_json, FILE_retroaccount_user_json)

        if transition.remove_user_json:
            self._file_system.unlink(FILE_retroaccount_user_json, verbose=False)

        if transition.remove_update_all_patreon_key:
            self._unlink_update_all_patreon_key()

        if transition.install_update_all_patreon_key_url:
            self._install_update_all_patreon_key(transition.install_update_all_patreon_key_url)

        if transition.credentials_were_corrupted:
            self._has_forced_logout = 'Your credentials are corrupted!\nDo you have any problems with your storage (SD)?'

        if transition.credentials_were_revoked:
            self._has_forced_logout = 'Your credentials were revoked!\nYour account must be active, and you have to log in on each device you use.'

    def _unlink_update_all_patreon_key(self):
        update_all_patreon_key_path = self._config_provider.get().patreon_key_path
        if not self._file_system.is_file(update_all_patreon_key_path):
            return

        try:
            self._file_system.unlink(update_all_patreon_key_path, verbose=False)
            self._file_system.unlink(FILE_patreon_key_md5, verbose=False)
            self._encryption.clear_cache()
        except Exception as e:
            self._logger.debug('RetroAccountService: Error during removal of update all patreon key.')
            self._logger.debug(e)

    def _install_update_all_patreon_key(self, update_all_patreon_key_url: str) -> None:
        try:
            update_all_patreon_key_path = self._config_provider.get().patreon_key_path
            if self._file_system.is_file(update_all_patreon_key_path):
                self._file_system.copy(update_all_patreon_key_path, FILE_patreon_key_prev)
            update_all_patreon_key_md5 = self._retroaccount_gateway.install_file(update_all_patreon_key_path, update_all_patreon_key_url)
            self._file_system.write_file_contents(FILE_patreon_key_md5, update_all_patreon_key_md5)
            self._encryption.clear_cache()
            self._logger.debug(f'RetroAccountService: New update_all.patreonkey installed at {update_all_patreon_key_path}!')
            self._has_installed_update_all_patreon_key = True
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

    def _apply_local_device_logout_effects(self) -> None:
        self._file_system.unlink(FILE_retroaccount_user_json, verbose=False)
        self._update_all_extras = False
        self._has_installed_update_all_patreon_key = False
        self._has_forced_logout = None

    def device_logout(self) -> bool:
        if not self._file_system.is_file(FILE_retroaccount_user_json):
            return False

        try:
            user_data = self._file_system.load_dict_from_file(FILE_retroaccount_user_json)
        except Exception as e:
            self._logger.debug('RetroAccountService: Device logout could not read user data')
            self._logger.debug(e)
            self._apply_local_device_logout_effects()
            return True

        device_id = user_data.get('device_id', '')
        refresh_token = user_data.get('refresh_token', '')

        if device_id and refresh_token:
            self._retroaccount_gateway.post_device_logout(refresh_token, device_id)

        self._apply_local_device_logout_effects()
        return True
