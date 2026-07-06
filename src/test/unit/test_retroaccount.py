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

import io
import json
import unittest

from test.fake_filesystem import FileSystemFactory
from test.file_system_tester_state import FileSystemState
from test.logger_tester import LoggerSpy, NoLogger
from update_all.config import Config
from update_all.constants import MEDIA_FAT, OTHER_MEDIA, FILE_jtbeta, FILE_jtbeta_alt, FILE_patreon_key, FILE_patreon_key_md5, \
    FILE_retroaccount_device_id, FILE_retroaccount_user_json, FILE_retroaccount_verified_chip_id
from update_all.other import GenericProvider
from update_all.retroaccount import BenefitState, ChipIdAttachResult, RetroAccountService, any_to_retroaccount_file_description
from update_all.retroaccount_gateway import SessionResult
from update_all.update_output import LtsvUpdateOutput, NoopUpdateOutput


_CORRUPTED_CREDENTIALS_MESSAGE = 'Your credentials are corrupted!\nDo you have any problems with your storage (SD)?'
_REVOKED_CREDENTIALS_MESSAGE = 'Your credentials were revoked!'


class TestRetroAccountService(unittest.TestCase):
    def test_consume_important_messages___returns_tuples_and_clears_the_buffer(self):
        sut, _file_system, _gateway, _encryption = tester()

        sut._report_forced_logout('custom message')

        messages = sut.consume_important_messages()

        self.assertEqual([
            ('print', '\nYou\'ve been logged out from RetroAccount.'),
            ('print', 'custom message'),
            ('print', 'Please log in again from the Settings Screen.'),
        ], messages)
        self.assertTrue(all(isinstance(message, tuple) for message in messages))
        self.assertEqual([], sut.consume_important_messages())

    def test_mister_sync___when_no_user_json___removes_stale_patreon_key(self):
        sut, file_system, _gateway, _encryption = tester(files={
            FILE_patreon_key: {'hash': 'stale-md5', 'content': 'old-key'},
            FILE_patreon_key_md5: {'content': 'stale-md5'},
        })
        activate_prev_patreon_key_url(sut)

        mister_sync(sut)

        self.assertFalse(file_system.is_file(FILE_patreon_key))
        self.assertFalse(file_system.is_file(FILE_patreon_key_md5))
        self.assertEqual([], sut.consume_important_messages())
        self.assertFalse(sut.has_installed_update_all_patreon_key())
        self.assertFalse(sut.has_prev_patreon_key_url())

    def test_mister_sync___when_user_json_is_corrupted___forces_logout_and_clears_entitlement(self):
        sut, file_system, _gateway, _encryption = tester(files={
            FILE_retroaccount_user_json: {'content': '{'},
            FILE_patreon_key: {'hash': 'stale-md5', 'content': 'old-key'},
            FILE_patreon_key_md5: {'content': 'stale-md5'},
        })
        activate_prev_patreon_key_url(sut)

        mister_sync(sut)

        self.assertFalse(file_system.is_file(FILE_retroaccount_user_json))
        self.assertFalse(file_system.is_file(FILE_patreon_key))
        self.assertFalse(file_system.is_file(FILE_patreon_key_md5))
        self.assertEqual(_forced_logout_messages(_CORRUPTED_CREDENTIALS_MESSAGE), sut.consume_important_messages())
        self.assertFalse(sut.has_installed_update_all_patreon_key())
        self.assertFalse(sut.has_prev_patreon_key_url())

    def test_mister_sync___when_session_is_revoked___persists_device_id_and_clears_credentials_and_entitlement(self):
        sut, file_system, _gateway, _encryption = tester(
            files=default_sync_files(),
            gateway_result=SessionResult.REVOKED,
            gateway_response=401,
        )
        activate_prev_patreon_key_url(sut)

        mister_sync(sut)

        self.assertEqual('device-1', file_system.read_file_contents(FILE_retroaccount_device_id))
        self.assertFalse(file_system.is_file(FILE_retroaccount_user_json))
        self.assertFalse(file_system.is_file(FILE_patreon_key))
        self.assertFalse(file_system.is_file(FILE_patreon_key_md5))
        self.assertEqual(_forced_logout_messages(_REVOKED_CREDENTIALS_MESSAGE), sut.consume_important_messages())
        self.assertFalse(sut.has_installed_update_all_patreon_key())
        self.assertFalse(sut.has_prev_patreon_key_url())

    def test_mister_sync___when_connection_fails___keeps_credentials_and_entitlement_files(self):
        sut, file_system, gateway, _encryption = tester(
            files=default_sync_files(),
            gateway_result=SessionResult.ERROR,
            gateway_response=403,
        )

        mister_sync(sut)

        self.assertEqual([('device-1', 'refresh-1', 'old-md5', None)], gateway.mister_sync_calls)
        self.assertTrue(file_system.is_file(FILE_retroaccount_user_json))
        self.assertTrue(file_system.is_file(FILE_patreon_key))
        self.assertTrue(file_system.is_file(FILE_patreon_key_md5))
        self.assertEqual([], sut.consume_important_messages())
        self.assertEqual(BenefitState.CONNECTION_FAILED, sut.update_all_extras_sync_state())
        self.assertEqual(BenefitState.CONNECTION_FAILED, sut.jtbeta_access_sync_state())

    def test_mister_sync___when_session_is_valid___applies_one_explicit_transition_for_refresh_and_entitlement_replacement(self):
        gateway_response = {
            'tokens': {'refresh_token': 'refresh-2'},
            'device': {'label': '  MiSTer Living Room  '},
            'benefits': {
                'update_all_patreon_key_remove': True,
                'update_all_patreon_key_file': {'url': 'https://example.com/update_all.patreonkey', 'md5': 'expected-md5', 'size': 32},
            },
        }
        sut, file_system, gateway, _encryption = tester(
            files=default_sync_files(),
            gateway_result=SessionResult.VALID,
            gateway_response=gateway_response,
        )

        mister_sync(sut)

        saved_user = file_system.load_dict_from_file(FILE_retroaccount_user_json)
        self.assertEqual('refresh-2', saved_user['refresh_token'])
        self.assertEqual(('device-1', 'refresh-1', 'old-md5', None), gateway.mister_sync_calls[0])
        self.assertEqual('MiSTer Living Room', sut.get_device_label())
        self.assertEqual([(FILE_patreon_key, 'https://example.com/update_all.patreonkey')], gateway.install_calls)
        self.assertTrue(file_system.is_file(FILE_patreon_key))
        self.assertEqual('installed-md5', file_system.read_file_contents(FILE_patreon_key_md5))
        self.assertTrue(sut.has_installed_update_all_patreon_key())
        self.assertEqual([
            ('print', 'Update All Patreon Key installed!'),
            ('debug', 'update_all.patreonkey MD5: installed-md5'),
        ], sut.consume_important_messages())

    def test_mister_sync___when_session_returns_jtbeta_url___installs_jtbeta_and_copies_it_to_existing_media(self):
        alt_jtbeta_path = f'{MEDIA_FAT}/{FILE_jtbeta_alt}'
        usb_jtbeta_path = f'{OTHER_MEDIA[0]}/{FILE_jtbeta}'
        sut, file_system, gateway, _encryption = tester(
            files={
                **default_sync_files(),
                alt_jtbeta_path: {'hash': 'old-alt-md5', 'content': 'old-alt'},
                usb_jtbeta_path: {'hash': 'old-usb-md5', 'content': 'old-usb'},
            },
            gateway_result=SessionResult.VALID,
            gateway_response={'benefits': {'jtbeta_file': {'url': 'https://example.com/jtbeta.zip', 'md5': 'expected-md5', 'size': 1024}}},
        )

        mister_sync(sut)

        self.assertEqual(('device-1', 'refresh-1', 'old-md5', None), gateway.mister_sync_calls[0])
        self.assertEqual([(FILE_jtbeta, 'https://example.com/jtbeta.zip')], gateway.install_calls)
        self.assertTrue(sut.has_installed_jtbeta())
        self.assertTrue(file_system.is_file(FILE_jtbeta))
        self.assertTrue(file_system.compare_files(FILE_jtbeta, alt_jtbeta_path))
        self.assertTrue(file_system.compare_files(FILE_jtbeta, usb_jtbeta_path))
        self.assertEqual([
            ('print', 'New jtbeta.zip from JOTEGO installed!'),
            ('debug', 'jtbeta.zip MD5: installed-md5'),
            ('debug', f'jtbeta.zip also copied to {alt_jtbeta_path}'),
            ('debug', f'jtbeta.zip also copied to {usb_jtbeta_path}'),
        ], sut.consume_important_messages())

    def test_mister_sync___when_session_returns_jtbeta_url___emits_ltsv_membership_extra_event(self):
        stream = io.StringIO()
        sut, _file_system, _gateway, _encryption = tester(
            files=default_sync_files(),
            gateway_result=SessionResult.VALID,
            gateway_response={'benefits': {'jtbeta_file': {'url': 'https://example.com/jtbeta.zip', 'md5': 'expected-md5', 'size': 1024}}},
        )

        sut.mister_sync(LtsvUpdateOutput(stream))

        self.assertEqual(
            'DLP1\tevent:retroaccount_sync_start\n'
            'DLP1\tevent:retroaccount_membership_extra'
            '\ttopic:jtbeta'
            '\tmsg:New jtbeta.zip from JOTEGO installed!'
            '\tinfo:You are receiving the new jtbeta.zip because you are a member of JOTEGO. This will allow you to run private and beta games made by the JOTEGO Team on your MiSTer.\n'
            'DLP1\tevent:retroaccount_sync_end\n',
            stream.getvalue()
        )

    def test_mister_sync___when_session_returns_active_jtbeta_access___tries_to_auto_enable_jt_private_releases(self):
        jtcores_service = _JtcoresServiceStub()
        sut, _file_system, _gateway, _encryption = tester(
            files=default_sync_files(),
            gateway_result=SessionResult.VALID,
            gateway_response={'benefits': {'jtbeta_access': True}},
            jtcores_service=jtcores_service,
        )

        mister_sync(sut)

        self.assertEqual(1, jtcores_service.enable_private_beta_cores_from_retroaccount_if_allowed_calls)

    def test_mister_sync___when_session_returns_inactive_jtbeta_access___does_not_auto_enable_jt_private_releases(self):
        jtcores_service = _JtcoresServiceStub()
        sut, _file_system, _gateway, _encryption = tester(
            files=default_sync_files(),
            gateway_result=SessionResult.VALID,
            gateway_response={'benefits': {'jtbeta_access': False}},
            jtcores_service=jtcores_service,
        )

        mister_sync(sut)

        self.assertEqual(0, jtcores_service.enable_private_beta_cores_from_retroaccount_if_allowed_calls)

    def test_mister_sync___when_session_does_not_return_jtbeta_access___does_not_auto_enable_jt_private_releases(self):
        jtcores_service = _JtcoresServiceStub()
        sut, _file_system, _gateway, _encryption = tester(
            files=default_sync_files(),
            gateway_result=SessionResult.VALID,
            gateway_response={'benefits': {}},
            jtcores_service=jtcores_service,
        )

        mister_sync(sut)

        self.assertEqual(0, jtcores_service.enable_private_beta_cores_from_retroaccount_if_allowed_calls)

    def test_mister_sync___when_session_is_revoked___emits_ltsv_credentials_removed_event(self):
        stream = io.StringIO()
        sut, _file_system, _gateway, _encryption = tester(
            files=default_sync_files(),
            gateway_result=SessionResult.REVOKED,
            gateway_response=401,
        )

        sut.mister_sync(LtsvUpdateOutput(stream))

        self.assertEqual(
            'DLP1\tevent:retroaccount_sync_start\n'
            'DLP1\tevent:retroaccount_credentials_removed\treason:revoked\n'
            'DLP1\tevent:retroaccount_sync_end\n',
            stream.getvalue()
        )

    def test_noop_update_output___accepts_events(self):
        output = NoopUpdateOutput()

        output.sync_started()
        output.jtbeta_updated()
        output.credentials_removed('revoked')
        output.sync_finished()

    def test_mister_sync___when_previous_sync_enabled_extras_and_next_sync_has_no_user_json___disables_extras(self):
        sut, file_system, gateway, _encryption = tester(
            files=default_sync_files(),
            gateway_result=SessionResult.VALID,
            gateway_response={'benefits': {'update_all_extras': True}},
        )
        activate_prev_patreon_key_url(sut)

        mister_sync(sut)
        self.assertTrue(sut.is_update_all_extras_active())

        file_system.unlink(FILE_retroaccount_user_json, verbose=False)
        mister_sync(sut)

        self.assertFalse(sut.is_update_all_extras_active())
        self.assertFalse(file_system.is_file(FILE_patreon_key))
        self.assertEqual(1, len(gateway.mister_sync_calls))
        self.assertFalse(sut.has_prev_patreon_key_url())

    def test_device_logout___when_previous_sync_enabled_extras___disables_extras_in_current_process(self):
        files = default_sync_files()
        files[FILE_retroaccount_verified_chip_id] = {'content': '0123456789abcdef'}
        sut, file_system, gateway, _encryption = tester(
            files=files,
            gateway_result=SessionResult.VALID,
            gateway_response={'device': {'label': 'MiSTer Living Room'}, 'benefits': {'update_all_extras': True}},
        )
        activate_prev_patreon_key_url(sut)

        mister_sync(sut)
        self.assertTrue(sut.is_update_all_extras_active())
        self.assertEqual('MiSTer Living Room', sut.get_device_label())

        self.assertTrue(sut.device_logout())

        self.assertFalse(sut.is_update_all_extras_active())
        self.assertIsNone(sut.get_device_label())
        self.assertFalse(file_system.is_file(FILE_retroaccount_user_json))
        self.assertFalse(file_system.is_file(FILE_retroaccount_verified_chip_id))
        self.assertEqual([('refresh-1', 'device-1')], gateway.logout_calls)
        self.assertFalse(sut.has_prev_patreon_key_url())

    def test_attach_chip_id_to_current_device___with_valid_session___stores_verified_chip_id(self):
        logger = LoggerSpy()
        sut, file_system, gateway, _encryption = tester(files=default_sync_files(), logger=logger)

        result = sut.attach_chip_id_to_current_device('0123456789ABCDEF')

        self.assertEqual(ChipIdAttachResult(True, 200), result)
        self.assertTrue(result)
        self.assertEqual([('device-1', 'refresh-1', '0123456789abcdef')], gateway.attach_chip_id_calls)
        self.assertEqual('0123456789abcdef', file_system.read_file_contents(FILE_retroaccount_verified_chip_id))
        self.assertTrue(sut.is_device_verified())
        self.assertIn('RetroAccountService: FPGA ID attach succeeded with status 200', logger.debug_messages)

    def test_attach_chip_id_to_current_device___when_endpoint_fails___does_not_store_verified_chip_id(self):
        logger = LoggerSpy()
        sut, file_system, gateway, _encryption = tester(files=default_sync_files(), logger=logger)
        gateway.attach_chip_id_status = 500

        result = sut.attach_chip_id_to_current_device('0123456789abcdef')

        self.assertEqual(ChipIdAttachResult(False, 500), result)
        self.assertFalse(result)
        self.assertEqual([('device-1', 'refresh-1', '0123456789abcdef')], gateway.attach_chip_id_calls)
        self.assertFalse(file_system.is_file(FILE_retroaccount_verified_chip_id))
        self.assertIn('RetroAccountService: FPGA ID attach failed with status 500', logger.debug_messages)

    def test_attach_chip_id_to_current_device___with_invalid_chip_id___does_not_call_endpoint(self):
        sut, file_system, gateway, _encryption = tester(files=default_sync_files())

        result = sut.attach_chip_id_to_current_device('FAILURE_MEM_SIGBUS')

        self.assertEqual(ChipIdAttachResult(False), result)
        self.assertFalse(result)
        self.assertEqual([], gateway.attach_chip_id_calls)
        self.assertFalse(file_system.is_file(FILE_retroaccount_verified_chip_id))

    def test_mister_sync___when_login_is_lost___removes_verified_chip_id(self):
        sut, file_system, _gateway, _encryption = tester(files={
            FILE_retroaccount_verified_chip_id: {'content': '0123456789abcdef'},
        })

        mister_sync(sut)

        self.assertFalse(file_system.is_file(FILE_retroaccount_verified_chip_id))


class TestAnyToRetroAccountFileDescription(unittest.TestCase):
    def test_any_to_retroaccount_file_description___returns_normalized_recursive_description(self):
        self.assertEqual({
            'url': 'https://example.com/file.zip',
            'md5': 'abc123',
            'size': 10,
            'meta': None,
            'prev': {
                'url': 'https://example.com/prev.zip',
                'md5': 'def456',
                'size': 9,
                'meta': None,
            },
        }, any_to_retroaccount_file_description({
            'url': '  https://example.com/file.zip  ',
            'md5': '  abc123  ',
            'size': 10,
            'prev': {
                'url': 'https://example.com/prev.zip',
                'md5': 'def456',
                'size': 9,
            },
            'ignored': True,
        }))

    def test_any_to_retroaccount_file_description___accepts_missing_or_null_prev(self):
        self.assertEqual({
            'url': 'https://example.com/file.zip',
            'md5': 'abc123',
            'size': 10,
            'meta': None,
        }, any_to_retroaccount_file_description({
            'url': 'https://example.com/file.zip',
            'md5': 'abc123',
            'size': 10,
        }))
        self.assertEqual({
            'url': 'https://example.com/file.zip',
            'md5': 'abc123',
            'size': 10,
            'meta': None,
        }, any_to_retroaccount_file_description({
            'url': 'https://example.com/file.zip',
            'md5': 'abc123',
            'size': 10,
            'prev': None,
        }))

    def test_any_to_retroaccount_file_description___returns_none_for_invalid_values(self):
        cases = [
            None,
            'abc',
            {},
            {'url': 'https://example.com/file.zip', 'md5': 'abc123'},
            {'url': 'https://example.com/file.zip', 'md5': 'abc123', 'size': '10'},
            {'url': 'https://example.com/file.zip', 'md5': 'abc123', 'size': True},
            {'url': 'https://example.com/file.zip', 'md5': 'abc123', 'size': 10, 'prev': 'bad'},
            {'url': 'https://example.com/file.zip', 'md5': 'abc123', 'size': 10, 'prev': {'url': 'https://example.com/prev.zip', 'size': 9}},
        ]
        for value in cases:
            with self.subTest(value=value):
                self.assertIsNone(any_to_retroaccount_file_description(value))



def mister_sync(sut: RetroAccountService) -> None:
    sut.mister_sync(NoopUpdateOutput())

def tester(files=None, gateway_result=SessionResult.VALID, gateway_response=None, logger=None, jtcores_service=None):
    config = Config()
    config_provider = GenericProvider[Config]()
    config_provider.initialize(config)
    state = FileSystemState(files=files or {}, config=config)
    file_system = FileSystemFactory(state=state).create_for_system_scope()
    gateway = _RetroAccountGatewayStub(file_system, gateway_result, gateway_response)
    encryption = _EncryptionSpy()
    return RetroAccountService(
        logger or NoLogger(),
        file_system,
        config_provider,
        gateway,
        encryption,
        jtcores_service or _JtcoresServiceStub(),
    ), file_system, gateway, encryption


def default_sync_files():
    return {
        FILE_retroaccount_user_json: {'content': json.dumps({'device_id': 'device-1', 'refresh_token': 'refresh-1'})},
        FILE_patreon_key: {'hash': 'old-md5', 'content': 'old-key'},
        FILE_patreon_key_md5: {'content': 'old-md5'},
    }


def activate_prev_patreon_key_url(sut: RetroAccountService):
    sut._update_all_patreon_key_prev_url = 'https://example.com/update_all_prev.patreonkey'


def _forced_logout_messages(message: str):
    return [
        ('print', '\nYou\'ve been logged out from RetroAccount.'),
        ('print', message),
        ('print', 'Please log in again from the Settings Screen.'),
    ]


class _EncryptionSpy:
    def __init__(self):
        self.clear_cache_calls = 0

    def clear_cache(self):
        self.clear_cache_calls += 1


class _JtcoresServiceStub:
    def __init__(self):
        self.enable_private_beta_cores_from_retroaccount_if_allowed_calls = 0

    def enable_private_beta_cores_from_retroaccount_if_allowed(self):
        self.enable_private_beta_cores_from_retroaccount_if_allowed_calls += 1


class _RetroAccountGatewayStub:
    def __init__(self, file_system, result, response):
        self._file_system = file_system
        self._result = result
        self._response = {} if response is None else response
        self.mister_sync_calls = []
        self.install_calls = []
        self.logout_calls = []
        self.attach_chip_id_calls = []
        self.attach_chip_id_status = 200

    def mister_sync(self, device_id, refresh_token, update_all_patreon_key_fingerprint, jtbeta_fingerprint=None):
        self.mister_sync_calls.append((device_id, refresh_token, update_all_patreon_key_fingerprint, jtbeta_fingerprint))
        return self._result, self._response

    def install_file(self, file_path, file_url):
        self.install_calls.append((file_path, file_url))
        self._file_system.write_file_bytes(file_path, b'new-key')
        return 'installed-md5'

    def post_device_logout(self, refresh_token, device_id):
        self.logout_calls.append((refresh_token, device_id))

    def put_device_hardware_id(self, device_id, refresh_token, chip_id):
        self.attach_chip_id_calls.append((device_id, refresh_token, chip_id))
        return self.attach_chip_id_status
