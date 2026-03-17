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
from update_all.constants import FILE_patreon_key, FILE_patreon_key_md5, FILE_retroaccount_user_json, MD5_old_patreon_key
from update_all.other import GenericProvider
from update_all.retroaccount import RetroAccountService
from update_all.retroaccount_gateway import SessionResult


class TestRetroAccountSyncFingerprint(unittest.TestCase):
    def test_mister_sync_withholds_fingerprint_when_key_metadata_is_missing(self):
        gateway_response = {'update_all_patreon_key_url': 'https://example.com/update_all.patreonkey'}
        sut, file_system, gateway = _tester(
            files={
                FILE_retroaccount_user_json: {'content': json.dumps({'device_id': 'device-1', 'refresh_token': 'refresh-1'})},
                FILE_patreon_key: {'hash': 'new-md5', 'content': 'existing-key'},
            },
            gateway_response=gateway_response,
        )

        sut.mister_sync()

        self.assertEqual(('device-1', 'refresh-1', None), gateway.mister_sync_calls[0])
        self.assertEqual([(FILE_patreon_key, 'https://example.com/update_all.patreonkey')], gateway.install_calls)
        self.assertEqual('installed-md5', file_system.read_file_contents(FILE_patreon_key_md5))

    def test_mister_sync_withholds_fingerprint_when_key_metadata_mismatches(self):
        sut, _file_system, gateway = _tester(
            files={
                FILE_retroaccount_user_json: {'content': json.dumps({'device_id': 'device-1', 'refresh_token': 'refresh-1'})},
                FILE_patreon_key: {'hash': 'new-md5', 'content': 'existing-key'},
                FILE_patreon_key_md5: {'content': 'different-md5'},
            },
        )

        sut.mister_sync()

        self.assertEqual(('device-1', 'refresh-1', None), gateway.mister_sync_calls[0])

    def test_mister_sync_keeps_legacy_fingerprint_when_metadata_is_missing(self):
        sut, _file_system, gateway = _tester(
            files={
                FILE_retroaccount_user_json: {'content': json.dumps({'device_id': 'device-1', 'refresh_token': 'refresh-1'})},
                FILE_patreon_key: {'hash': MD5_old_patreon_key, 'content': 'legacy-key'},
            },
        )

        sut.mister_sync()

        self.assertEqual(('device-1', 'refresh-1', MD5_old_patreon_key), gateway.mister_sync_calls[0])


def _tester(files=None, gateway_result=SessionResult.VALID, gateway_response=None):
    config = Config()
    config_provider = GenericProvider[Config]()
    config_provider.initialize(config)
    state = FileSystemState(files=files or {}, config=config)
    file_system = FileSystemFactory(state=state).create_for_system_scope()
    gateway = _RetroAccountGatewayStub(file_system, gateway_result, gateway_response)
    encryption = _EncryptionSpy()
    return RetroAccountService(NoLogger(), file_system, config_provider, gateway, encryption), file_system, gateway


class _EncryptionSpy:
    def clear_cache(self):
        pass


class _RetroAccountGatewayStub:
    def __init__(self, file_system, result, response):
        self._file_system = file_system
        self._result = result
        self._response = {} if response is None else response
        self.mister_sync_calls = []
        self.install_calls = []

    def mister_sync(self, device_id, refresh_token, update_all_patreon_key_fingerprint):
        self.mister_sync_calls.append((device_id, refresh_token, update_all_patreon_key_fingerprint))
        return self._result, self._response

    def install_file(self, file_path, file_url):
        self.install_calls.append((file_path, file_url))
        self._file_system.write_file_bytes(file_path, b'new-key')
        return 'installed-md5'
