#!/usr/bin/env python3

# Copyright (c) 2022-2026 José Manuel Barroso Galindo <theypsilon@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# You can download the latest version of this tool from:
# https://github.com/theypsilon/Update_All_MiSTer

import json
import unittest

from test.fake_filesystem import FileSystemFactory
from test.file_system_tester_state import FileSystemState
from test.logger_tester import NoLogger
from update_all.config import Config
from update_all.constants import FILE_patreon_key, FILE_patreon_key_md5, FILE_retroaccount_device_id, FILE_retroaccount_user_json
from update_all.other import GenericProvider
from update_all.retroaccount import RetroAccountService
from update_all.retroaccount_gateway import SessionResult


_CORRUPTED_CREDENTIALS_MESSAGE = 'Your credentials are corrupted!\nDo you have any problems with your storage (SD)?'
_REVOKED_CREDENTIALS_MESSAGE = 'Your credentials were revoked!\nYour account must be active, and you have to log in on each device you use.'


class TestRetroAccountService(unittest.TestCase):
    def test_mister_sync___when_no_user_json___removes_stale_patreon_key(self):
        sut, file_system, _gateway, _encryption = tester(files={
            FILE_patreon_key: {'hash': 'stale-md5', 'content': 'old-key'},
            FILE_patreon_key_md5: {'content': 'stale-md5'},
        })
        activate_prev_patreon_key_url(sut)

        sut.mister_sync()

        self.assertFalse(file_system.is_file(FILE_patreon_key))
        self.assertFalse(file_system.is_file(FILE_patreon_key_md5))
        self.assertIsNone(sut.has_forced_logout())
        self.assertFalse(sut.has_installed_update_all_patreon_key())
        self.assertFalse(sut.has_prev_patreon_key_url())

    def test_mister_sync___when_user_json_is_corrupted___forces_logout_and_clears_entitlement(self):
        sut, file_system, _gateway, _encryption = tester(files={
            FILE_retroaccount_user_json: {'content': '{'},
            FILE_patreon_key: {'hash': 'stale-md5', 'content': 'old-key'},
            FILE_patreon_key_md5: {'content': 'stale-md5'},
        })
        activate_prev_patreon_key_url(sut)

        sut.mister_sync()

        self.assertFalse(file_system.is_file(FILE_retroaccount_user_json))
        self.assertFalse(file_system.is_file(FILE_patreon_key))
        self.assertFalse(file_system.is_file(FILE_patreon_key_md5))
        self.assertEqual(_CORRUPTED_CREDENTIALS_MESSAGE, sut.has_forced_logout())
        self.assertFalse(sut.has_installed_update_all_patreon_key())
        self.assertFalse(sut.has_prev_patreon_key_url())

    def test_mister_sync___when_session_is_revoked___persists_device_id_and_clears_credentials_and_entitlement(self):
        sut, file_system, _gateway, _encryption = tester(
            files=default_sync_files(),
            gateway_result=SessionResult.REVOKED,
            gateway_response=401,
        )
        activate_prev_patreon_key_url(sut)

        sut.mister_sync()

        self.assertEqual('device-1', file_system.read_file_contents(FILE_retroaccount_device_id))
        self.assertFalse(file_system.is_file(FILE_retroaccount_user_json))
        self.assertFalse(file_system.is_file(FILE_patreon_key))
        self.assertFalse(file_system.is_file(FILE_patreon_key_md5))
        self.assertEqual(_REVOKED_CREDENTIALS_MESSAGE, sut.has_forced_logout())
        self.assertFalse(sut.has_installed_update_all_patreon_key())
        self.assertFalse(sut.has_prev_patreon_key_url())

    def test_mister_sync___when_session_is_valid___applies_one_explicit_transition_for_refresh_and_entitlement_replacement(self):
        gateway_response = {
            'tokens': {'refresh_token': 'refresh-2'},
            'benefits': {
                'update_all_patreon_key_remove': True,
                'update_all_patreon_key_url': 'https://example.com/update_all.patreonkey',
            },
        }
        sut, file_system, gateway, _encryption = tester(
            files=default_sync_files(),
            gateway_result=SessionResult.VALID,
            gateway_response=gateway_response,
        )

        sut.mister_sync()

        saved_user = file_system.load_dict_from_file(FILE_retroaccount_user_json)
        self.assertEqual('refresh-2', saved_user['refresh_token'])
        self.assertEqual(('device-1', 'refresh-1', 'old-md5'), gateway.mister_sync_calls[0])
        self.assertEqual([(FILE_patreon_key, 'https://example.com/update_all.patreonkey')], gateway.install_calls)
        self.assertTrue(file_system.is_file(FILE_patreon_key))
        self.assertEqual('installed-md5', file_system.read_file_contents(FILE_patreon_key_md5))
        self.assertTrue(sut.has_installed_update_all_patreon_key())
        self.assertIsNone(sut.has_forced_logout())

    def test_mister_sync___when_previous_sync_enabled_extras_and_next_sync_has_no_user_json___disables_extras(self):
        sut, file_system, gateway, _encryption = tester(
            files=default_sync_files(),
            gateway_result=SessionResult.VALID,
            gateway_response={'benefits': {'update_all_extras': True}},
        )
        activate_prev_patreon_key_url(sut)

        sut.mister_sync()
        self.assertTrue(sut.is_update_all_extras_active())

        file_system.unlink(FILE_retroaccount_user_json, verbose=False)
        sut.mister_sync()

        self.assertFalse(sut.is_update_all_extras_active())
        self.assertFalse(file_system.is_file(FILE_patreon_key))
        self.assertEqual(1, len(gateway.mister_sync_calls))
        self.assertFalse(sut.has_prev_patreon_key_url())

    def test_device_logout___when_previous_sync_enabled_extras___disables_extras_in_current_process(self):
        sut, file_system, gateway, _encryption = tester(
            files=default_sync_files(),
            gateway_result=SessionResult.VALID,
            gateway_response={'benefits': {'update_all_extras': True}},
        )
        activate_prev_patreon_key_url(sut)

        sut.mister_sync()
        self.assertTrue(sut.is_update_all_extras_active())

        self.assertTrue(sut.device_logout())

        self.assertFalse(sut.is_update_all_extras_active())
        self.assertFalse(file_system.is_file(FILE_retroaccount_user_json))
        self.assertEqual([('refresh-1', 'device-1')], gateway.logout_calls)
        self.assertFalse(sut.has_prev_patreon_key_url())


def tester(files=None, gateway_result=SessionResult.VALID, gateway_response=None):
    config = Config()
    config_provider = GenericProvider[Config]()
    config_provider.initialize(config)
    state = FileSystemState(files=files or {}, config=config)
    file_system = FileSystemFactory(state=state).create_for_system_scope()
    gateway = _RetroAccountGatewayStub(file_system, gateway_result, gateway_response)
    encryption = _EncryptionSpy()
    return RetroAccountService(NoLogger(), file_system, config_provider, gateway, encryption), file_system, gateway, encryption


def default_sync_files():
    return {
        FILE_retroaccount_user_json: {'content': json.dumps({'device_id': 'device-1', 'refresh_token': 'refresh-1'})},
        FILE_patreon_key: {'hash': 'old-md5', 'content': 'old-key'},
        FILE_patreon_key_md5: {'content': 'old-md5'},
    }


def activate_prev_patreon_key_url(sut: RetroAccountService):
    sut._update_all_patreon_key_prev_url = 'https://example.com/update_all_prev.patreonkey'


class _EncryptionSpy:
    def __init__(self):
        self.clear_cache_calls = 0

    def clear_cache(self):
        self.clear_cache_calls += 1


class _RetroAccountGatewayStub:
    def __init__(self, file_system, result, response):
        self._file_system = file_system
        self._result = result
        self._response = {} if response is None else response
        self.mister_sync_calls = []
        self.install_calls = []
        self.logout_calls = []

    def mister_sync(self, device_id, refresh_token, update_all_patreon_key_fingerprint):
        self.mister_sync_calls.append((device_id, refresh_token, update_all_patreon_key_fingerprint))
        return self._result, self._response

    def install_file(self, file_path, file_url):
        self.install_calls.append((file_path, file_url))
        self._file_system.write_file_bytes(file_path, b'new-key')
        return 'installed-md5'

    def post_device_logout(self, refresh_token, device_id):
        self.logout_calls.append((refresh_token, device_id))
