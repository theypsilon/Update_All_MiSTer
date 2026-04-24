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

from unittest.mock import MagicMock
import unittest

from test.fake_filesystem import FileSystemFactory
from update_all.config import Config
from update_all.constants import FILE_patreon_key_prev, UPDATE_ALL_VERSION
from update_all.encryption import EncryptionResult
from update_all.other import GenericProvider
from update_all.other import TerminalSize, OverscanDim
from update_all.timeline import Timeline
from update_all.update_all_service import calculate_supporter_shoutout, calculate_outro_summary, calculate_success_summary, calculate_reading_sections_summary, format_run_time


class TestUpdateAllService(unittest.TestCase):
    def test_format_run_time___omits_hours_below_one_hour_and_keeps_them_after(self):
        self.assertEqual('59:59.30', format_run_time(3599.3))
        self.assertEqual('1:00:00.30', format_run_time(3600.3))
        self.assertEqual('2:02:05.30', format_run_time(7325.3))

    def test_calculate_supporter_shoutout___selects_tier_from_usable_width(self):
        supporter_name = 'Patron TesterXX'

        cases = [
            (
                Config(term_size=TerminalSize(columns=120, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                "Today's shoutout is for Patron TesterXX! - Join us at patreon.com/theypsilon",
            ),
            (
                Config(term_size=TerminalSize(columns=70, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                'Shoutout to Patron TesterXX! patreon.com/theypsilon',
            ),
            (
                Config(term_size=TerminalSize(columns=45, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                'Thanks Patron TesterXX! patreon.com/theypsilon',
            ),
        ]

        for config, expected in cases:
            with self.subTest(config=config, expected=expected):
                self.assertEqual(expected, calculate_supporter_shoutout(config, supporter_name))

    def test_calculate_outro_summary___selects_tier_from_usable_width(self):
        timestamp = '2026-03-10 19:34:04'
        run_time = '00:01.17'
        cases = [
            (
                Config(commit='unknown', term_size=TerminalSize(columns=120, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                f'Update All {UPDATE_ALL_VERSION} (unk) by theypsilon. Run time: 00:01.17s at 2026-03-10 19:34:04',
            ),
            (
                Config(commit='unknown', term_size=TerminalSize(columns=80, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                f'Update All {UPDATE_ALL_VERSION} by theypsilon 00:01.17s 2026-03-10 19:34:04',
            ),
            (
                Config(commit='unknown', term_size=TerminalSize(columns=56, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                f'Update All {UPDATE_ALL_VERSION}: 00:01.17s 2026-03-10 19:34:04',
            ),
            (
                Config(commit='unknown', term_size=TerminalSize(columns=28, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                f'Update All {UPDATE_ALL_VERSION}: 00:01.17s',
            ),
        ]

        for config, expected in cases:
            with self.subTest(config=config, expected=expected):
                self.assertEqual(expected, calculate_outro_summary(config, run_time, timestamp))

    def test_calculate_success_summary___selects_tier_from_usable_width(self):
        log_path = 'Scripts/.config/update_all/update_all.log'
        cases = [
            (
                Config(term_size=TerminalSize(columns=120, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                'Success! More details at: Scripts/.config/update_all/update_all.log',
            ),
            (
                Config(term_size=TerminalSize(columns=64, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                'Success! Log: Scripts/.config/update_all/update_all.log',
            ),
            (
                Config(term_size=TerminalSize(columns=28, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                'Success! Log saved.',
            ),
        ]

        for config, expected in cases:
            with self.subTest(config=config, expected=expected):
                self.assertEqual(expected, calculate_success_summary(config, log_path))

    def test_calculate_reading_sections_summary___omits_message_when_it_does_not_fit(self):
        downloader_ini_path = '/home/jose/workspace/Update_All_MiSTer/.local_drv/downloader.ini'
        cases = [
            (
                Config(term_size=TerminalSize(columns=120, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                f'Reading sections from {downloader_ini_path}',
            ),
            (
                Config(term_size=TerminalSize(columns=56, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                None,
            ),
        ]

        for config, expected in cases:
            with self.subTest(config=config, expected=expected):
                self.assertEqual(expected, calculate_reading_sections_summary(config, downloader_ini_path))


class TestTimelineFallbacks(unittest.TestCase):
    def test_extract_plus_model___when_local_previous_key_fallback_raises___continues(self):
        file_system = FileSystemFactory.from_state(files={
            FILE_patreon_key_prev: {'content': 'old-key', 'hash': 'old-key'},
        }).create_for_system_scope()
        config_provider = GenericProvider[Config]()
        config_provider.initialize(Config())
        sut = Timeline(MagicMock(), config_provider, file_system, _EncryptionStub(
            EncryptionResult.InvalidKey,
            RuntimeError('boom'),
        ), _RetroAccountStub(False))

        timeline_plus_model, not_yet_updated = sut._extract_plus_model('timeline_plus.enc', 'timeline_plus_output.json')

        self.assertIsNone(timeline_plus_model)
        self.assertFalse(not_yet_updated)

    def test_extract_plus_model___when_remote_previous_key_fallback_raises___continues(self):
        file_system = FileSystemFactory.from_state().create_for_system_scope()
        config_provider = GenericProvider[Config]()
        config_provider.initialize(Config())
        sut = Timeline(MagicMock(), config_provider, file_system, _EncryptionStub(
            EncryptionResult.InvalidKey,
        ), _RetroAccountStub(True, RuntimeError('boom')))

        timeline_plus_model, not_yet_updated = sut._extract_plus_model('timeline_plus.enc', 'timeline_plus_output.json')

        self.assertIsNone(timeline_plus_model)
        self.assertFalse(not_yet_updated)


class _EncryptionStub:
    def __init__(self, *results):
        self._results = list(results)

    def decrypt_file(self, _timeline_plus_model_path: str, _output: str, _key_file_path: str):
        result = self._results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class _RetroAccountStub:
    def __init__(self, has_prev_patreon_key_url: bool, install_exception: Exception = None):
        self._has_prev_patreon_key_url = has_prev_patreon_key_url
        self._install_exception = install_exception

    def has_prev_patreon_key_url(self) -> bool:
        return self._has_prev_patreon_key_url

    def install_update_all_prev_patreon_key(self, _target_path: str) -> None:
        if self._install_exception is not None:
            raise self._install_exception

    def is_update_all_extras_active(self) -> bool:
        return False
