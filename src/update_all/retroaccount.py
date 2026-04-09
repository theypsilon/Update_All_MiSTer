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

from dataclasses import dataclass, field
from enum import IntEnum
import os
from typing import Optional, Any, Literal, TypedDict

from update_all.logger import Logger
from update_all.file_system import FileSystem
from update_all.config import Config
from update_all.other import GenericProvider, any_to_bool, any_to_nonfalsy_str
from update_all.constants import MEDIA_FAT, OTHER_MEDIA, FILE_jtbeta, FILE_jtbeta_alt, FILE_retroaccount_user_json, \
    FILE_retroaccount_device_id, FILE_patreon_key_md5, \
    FILE_patreon_key_prev, FILE_JOTEGO_mra_pack_json, FILE_JOTEGO_mra_pack_ini
from update_all.encryption import Encryption, EncryptionResult
from update_all.retroaccount_gateway import RetroAccountGateway, SessionResult
from update_all.retroaccount_ui import DeviceLogin, DeviceLoginRenderer, RetroAccountClient
from update_all.ui_engine import UiSection
from update_all.ui_engine_dialog_application import UiDialogDrawer

_DEFAULT_CLIENT_ID = "update-all-mister"


class BenefitState(IntEnum):
    CHECKING = 0
    ACTIVE = 1
    INACTIVE = 2
    NEED_LOGIN = 3
    CONNECTION_FAILED = 4

ImportantMessageKind = Literal['print', 'debug']
ImportantMessage = tuple[ImportantMessageKind, str]


class _RetroAccountFileDescriptionRequired(TypedDict):
    url: str
    md5: str
    size: int  # Python int covers Rust i64


class _RetroAccountFileDescription(_RetroAccountFileDescriptionRequired, total=False):
    prev: '_RetroAccountFileDescription'
    meta: Any


@dataclass(frozen=True)
class _SyncTransition:
    update_all_extras_active: Optional[bool] = None
    jtbeta_access_active: Optional[bool] = None
    save_device_id: Optional[str] = None
    save_user_json: Optional[dict[str, Any]] = field(default=None, repr=False)
    remove_user_json: bool = False
    remove_update_all_patreon_key: bool = False
    install_update_all_patreon_key_file: Optional[_RetroAccountFileDescription] = None
    install_jtbeta_file: Optional[_RetroAccountFileDescription] = None
    install_jt_mra_pack: Optional[_RetroAccountFileDescription] = None
    credentials_were_corrupted: bool = False
    credentials_were_revoked: bool = False
    connection_failed: bool = False
    need_login: bool = False


def any_to_retroaccount_file_description(val: Any, discard_prev: bool = False) -> Optional[_RetroAccountFileDescription]:
    if not isinstance(val, dict):
        return None

    url = any_to_nonfalsy_str(val.get('url'))
    md5 = any_to_nonfalsy_str(val.get('md5'))
    size = val.get('size')

    if url is None or md5 is None or not isinstance(size, int) or isinstance(size, bool):
        return None

    result: _RetroAccountFileDescription = {
        'url': url,
        'md5': md5,
        'size': size,
        'meta': val.get('meta', None)
    }

    if discard_prev or 'prev' not in val or val['prev'] is None:
        return result

    prev = any_to_retroaccount_file_description(val['prev'])
    if prev is None:
        return None

    result['prev'] = prev
    return result

class RetroAccountService(RetroAccountClient):
    def __init__(self, logger: Logger, file_system: FileSystem, config_provider: GenericProvider[Config], retroaccount_gateway: RetroAccountGateway, encryption: Encryption):
        self._logger = logger
        self._file_system = file_system
        self._config_provider = config_provider
        self._retroaccount_gateway = retroaccount_gateway
        self._encryption = encryption
        self._has_installed_update_all_patreon_key = False
        self._has_installed_jtbeta = False
        self._update_all_extras: Optional[bool] = None
        self._update_all_extras_sync_state: BenefitState = BenefitState.CHECKING
        self._jtbeta_access_sync_state: BenefitState = BenefitState.CHECKING
        self._update_all_patreon_key_prev_file: Optional[_RetroAccountFileDescription] = None
        self._important_messages: list[ImportantMessage] = []
        self._sync_done = False

    def update_all_extras_sync_state(self) -> BenefitState:
        return self._update_all_extras_sync_state

    def jtbeta_access_sync_state(self) -> BenefitState:
        return self._jtbeta_access_sync_state

    def has_synced(self) -> bool:
        return self._sync_done

    def has_installed_update_all_patreon_key(self) -> bool: return self._has_installed_update_all_patreon_key
    def has_installed_jtbeta(self) -> bool: return self._has_installed_jtbeta

    def consume_important_messages(self) -> list[ImportantMessage]:
        messages = self._important_messages.copy()
        self._important_messages.clear()
        return messages

    @property
    def server_url(self) -> str:
        return self._config_provider.get().retroaccount_domain

    def is_update_all_extras_active(self) -> bool:
        if self._update_all_extras is None:
            self._update_all_extras = self._encryption.validate_key() == EncryptionResult.Success
        return self._update_all_extras

    def has_prev_patreon_key_url(self) -> bool:
        return self._update_all_patreon_key_prev_file is not None

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
                need_login=True,
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
                need_login=True,
            )

        device_id = any_to_nonfalsy_str(user_data.get('device_id'))
        refresh_token = any_to_nonfalsy_str(user_data.get('refresh_token'))
        if not device_id or not refresh_token:
            self._logger.print(f'RetroAccount Warning: Corrupted {FILE_retroaccount_user_json}')
            return _SyncTransition(
                remove_update_all_patreon_key=True,
                update_all_extras_active=False,
                credentials_were_corrupted=True,
                need_login=True,
            )

        patreon_key_fingerprint = None
        patreon_key_path = self._config_provider.get().patreon_key_path
        if self._file_system.is_file(patreon_key_path):
            try:
                patreon_key_fingerprint = self._file_system.hash(patreon_key_path)
            except Exception as e:
                self._logger.debug(f"RetroAccountService: Update All Patreon Key could not be hashed")
                self._logger.debug(e)

        jtbeta_fingerprint = None
        if self._file_system.is_file(FILE_jtbeta):
            try:
                jtbeta_fingerprint = self._file_system.hash(FILE_jtbeta)
            except Exception as e:
                self._logger.debug(f"RetroAccountService: jtbeta.zip could not be hashed")
                self._logger.debug(e)

        self._logger.bench('RetroAccountService Gateway mister_sync start')
        result, response = self._retroaccount_gateway.mister_sync(device_id, refresh_token, patreon_key_fingerprint, jtbeta_fingerprint)
        self._logger.bench('RetroAccountService Gateway mister_sync end')

        if result == SessionResult.VALID and isinstance(response, dict):
            new_tokens = response.get('tokens', None)
            if isinstance(new_tokens, dict) and len(new_tokens) > 1:
                self._logger.debug(f'RetroAccountService: New token!')

            benefits = response.get('benefits', {})
            self._logger.debug(f'RetroAccountService: Benefits after mister_sync ', benefits)
            return _SyncTransition(
                save_user_json=new_tokens,
                install_update_all_patreon_key_file=any_to_retroaccount_file_description(benefits.get('update_all_patreon_key_file', None)),
                install_jtbeta_file=any_to_retroaccount_file_description(benefits.get('jtbeta_file', None), discard_prev=True),
                install_jt_mra_pack=any_to_retroaccount_file_description(benefits.get('jt_mra_pack', None), discard_prev=True),
                remove_update_all_patreon_key=any_to_bool(benefits.get('update_all_patreon_key_remove', None)),
                update_all_extras_active=any_to_bool(benefits.get('update_all_extras', None)),
                jtbeta_access_active=any_to_bool(benefits.get('jtbeta_access', None)),
            )

        if result == SessionResult.REVOKED:
            self._logger.debug(f'RetroAccountService: User session revoked', response)
            return _SyncTransition(
                save_device_id=device_id,
                remove_user_json=True,
                remove_update_all_patreon_key=True,
                update_all_extras_active=False,
                credentials_were_revoked=True,
                need_login=True,
            )

        self._logger.debug(f'RetroAccountService: MiSTer sync API returned status {response}.')
        return _SyncTransition(
            connection_failed=True
        )

    def _reset_sync_effects(self) -> None:
        self._has_installed_update_all_patreon_key = False
        self._has_installed_jtbeta = False
        self.consume_important_messages()

    def _apply_sync_transition(self, transition: _SyncTransition) -> None:
        self._logger.debug(transition)

        if transition.update_all_extras_active is not None:
            self._update_all_extras = transition.update_all_extras_active
            if transition.update_all_extras_active:
                self._update_all_extras_sync_state = BenefitState.ACTIVE
            else:
                self._update_all_extras_sync_state = BenefitState.INACTIVE

        if transition.jtbeta_access_active is not None:
            if transition.jtbeta_access_active:
                self._jtbeta_access_sync_state = BenefitState.ACTIVE
            else:
                self._jtbeta_access_sync_state = BenefitState.INACTIVE

        if transition.connection_failed:
            self._jtbeta_access_sync_state = BenefitState.CONNECTION_FAILED
            self._update_all_extras_sync_state = BenefitState.CONNECTION_FAILED

        if transition.need_login:
            self._jtbeta_access_sync_state = BenefitState.NEED_LOGIN
            self._update_all_extras_sync_state = BenefitState.NEED_LOGIN

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

        if transition.install_update_all_patreon_key_file:
            self._logger.bench('RetroAccountService: Installing Update All Patreon Key START')
            self._install_update_all_patreon_key(transition.install_update_all_patreon_key_file)
            self._logger.bench('RetroAccountService: Installing Update All Patreon Key END')

        if transition.install_jtbeta_file:
            self._logger.bench('RetroAccountService: Installing JTBeta START')
            self._install_jtbeta(transition.install_jtbeta_file)
            self._logger.bench('RetroAccountService: Installing JTBeta END')

        if transition.install_jt_mra_pack:
            self._logger.bench('RetroAccountService: Installing JT MRA PACK START')
            self._install_jt_mra_pack(transition.install_jt_mra_pack)
            self._logger.bench('RetroAccountService: Installing JT MRA PACK END')

        if transition.credentials_were_corrupted:
            self._report_forced_logout('Your credentials are corrupted!\nDo you have any problems with your storage (SD)?')

        if transition.credentials_were_revoked:
            self._report_forced_logout('Your credentials were revoked!')

        self._sync_done = True

    def _report_forced_logout(self, message: str) -> None:
        self._important_messages.append(('print', '\nYou\'ve been logged out from RetroAccount.'))
        self._important_messages.append(('print', message))
        self._important_messages.append(('print', 'Please log in again from the Settings Screen.'))

    def _unlink_update_all_patreon_key(self):
        try:
            update_all_patreon_key_path = self._config_provider.get().patreon_key_path
            self._file_system.unlink(update_all_patreon_key_path, verbose=False)
            self._file_system.unlink(FILE_patreon_key_md5, verbose=False)
            self._file_system.unlink(FILE_patreon_key_prev, verbose=False)
        except Exception as e:
            self._logger.debug('RetroAccountService: Error during removal of update all patreon key.')
            self._logger.debug(e)

    def _install_update_all_patreon_key(self, update_all_patreon_key_file: _RetroAccountFileDescription) -> None:
        try:
            update_all_patreon_key_path = self._config_provider.get().patreon_key_path
            if self._file_system.is_file(update_all_patreon_key_path):
                self._file_system.copy(update_all_patreon_key_path, FILE_patreon_key_prev)
            update_all_patreon_key_md5 = self._retroaccount_gateway.install_file(update_all_patreon_key_path, update_all_patreon_key_file['url'])
            self._file_system.write_file_contents(FILE_patreon_key_md5, update_all_patreon_key_md5)
            self._has_installed_update_all_patreon_key = True
            self._logger.debug(f'RetroAccountService: New update_all.patreonkey installed at {update_all_patreon_key_path} with MD5: {update_all_patreon_key_md5}')
            self._important_messages.append(('print', 'Update All Patreon Key installed!'))
            self._important_messages.append(('debug', f'update_all.patreonkey MD5: {update_all_patreon_key_md5}'))
        except Exception as e:
            self._logger.debug('RetroAccountService: Could not install update all patreon key.')
            self._logger.debug(e)

        if 'prev' in update_all_patreon_key_file:
            self._update_all_patreon_key_prev_file = update_all_patreon_key_file['prev']
            self._logger.debug(f'RetroAccountService: Previous update all patreon key URL available: {self._update_all_patreon_key_prev_file["url"]}')

    def install_update_all_prev_patreon_key(self, target_path: str) -> None:
        if not self._update_all_patreon_key_prev_file:
            self._logger.debug('RetroAccountService: No previous update all patreon key url available!')
            return

        try:
            self._retroaccount_gateway.install_file(target_path, self._update_all_patreon_key_prev_file["url"])
        except Exception as e:
            self._logger.debug(f'RetroAccountService: Could not install previous update all patreon key from {self._update_all_patreon_key_prev_file["url"]} to {target_path}')
            self._logger.debug(e)

    def _install_jtbeta(self, jtbeta_file: _RetroAccountFileDescription) -> None:
        try:
            jtbeta_md5 = self._retroaccount_gateway.install_file(FILE_jtbeta, jtbeta_file['url'])
            self._has_installed_jtbeta = True
            self._logger.debug(f'RetroAccountService: New jtbeta.zip installed at {FILE_jtbeta} with MD5: {jtbeta_md5}')
            self._important_messages.append(('print', 'New jtbeta.zip from JOTEGO installed!'))
            self._important_messages.append(('debug', f'jtbeta.zip MD5: {jtbeta_md5}'))
        except Exception as e:
            self._logger.debug('RetroAccountService: Could not install jtbeta.zip.')
            self._logger.debug(e)
        try:
            other_paths = [os.path.join(MEDIA_FAT, FILE_jtbeta_alt)] + [os.path.join(p, FILE_jtbeta) for p in OTHER_MEDIA]
            for o_path in other_paths:
                if self._file_system.is_file(o_path):
                    self._file_system.copy(FILE_jtbeta, o_path)
                    self._logger.debug(f'RetroAccountService: Copied jtbeta.zip to {o_path}')
                    self._important_messages.append(('debug', f'jtbeta.zip also copied to {o_path}'))
        except Exception as e:
            self._logger.debug('RetroAccountService: Could not copy jtbeta.zip to other media.')
            self._logger.debug(e)

    def _install_jt_mra_pack(self, jt_mra_pack: _RetroAccountFileDescription) -> None:
        meta = jt_mra_pack.get('meta', None)
        if isinstance(meta, dict):
            db = meta.get('db', None)
            if isinstance(db, str) and db:
                try:
                    self._file_system.write_file_contents(FILE_JOTEGO_mra_pack_json, db)
                    self._file_system.write_file_contents(FILE_JOTEGO_mra_pack_ini,f"[jt_mra_kai]\ndb_url = {FILE_JOTEGO_mra_pack_json}\n")
                    self._logger.debug(f'RetroAccountService: Installed {FILE_JOTEGO_mra_pack_ini}')
                    return
                except Exception as e:
                    self._logger.debug('RetroAccountService: Error during JOTEGO MRA PACK install.')
                    self._logger.debug(e)
                    return

        self._logger.debug('RetroAccountService: Could not install JOTEGO MRA PACK. Wrong meta?', meta)

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
        self._file_system.unlink(FILE_JOTEGO_mra_pack_ini, verbose=False)
        self._update_all_extras = False
        self._has_installed_update_all_patreon_key = False
        self._has_installed_jtbeta = False
        self._update_all_patreon_key_prev_file = None
        self.consume_important_messages()

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
