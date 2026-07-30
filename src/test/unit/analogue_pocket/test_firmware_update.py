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

import os
import tempfile
import unittest
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from test.fake_filesystem import FileSystemFactory
from test.file_system_tester_state import FileSystemState
from test.logger_tester import LoggerSpy
from test.testing_objects import pocket_firmware_details_json
from test.update_all_service_tester import LocalRepositoryTester
from update_all.analogue_pocket.firmware_update import remove_old_firmware_files


def tester(files: dict[str, Any]):
    return LocalRepositoryTester(file_system=FileSystemFactory(state=FileSystemState(files=files)).create_for_system_scope())

class TestFirmwareUpdate(unittest.TestCase):

        def test_firmware_firmware_info_has_expected_types(self) -> None:
            repo = tester(files={
                pocket_firmware_details_json: {
                    'content': Path('test/fixtures/pocket_firmware_details_json/standard.json').read_text()}
                }
            )

            info = repo.pocket_firmware_info()
            self.assertTrue(isinstance(info['size'], float))
            self.assertTrue(isinstance(info['file'], str))
            self.assertTrue(isinstance(info['md5'], str))
            self.assertTrue(isinstance(info['version'], str))
            self.assertTrue(isinstance(info['url'], str))
            self.assertEqual(5, len(info.keys()))

        def test_firmware_firmware_info_follows_expected_invariants(self) -> None:
            repo = tester(files={
                pocket_firmware_details_json: {
                    'content': Path('test/fixtures/pocket_firmware_details_json/standard.json').read_text()}
                }
            )

            info = repo.pocket_firmware_info()
            self.assertGreaterEqual(float(info['version']), 2.0)
            self.assertTrue('analogue.co', urlparse(info['url']).netloc)

        def test_remove_old_firmware_files___removes_every_stale_file_around_the_latest_one(self) -> None:
            with tempfile.TemporaryDirectory() as mount:
                _touch(mount, 'pocket_firmware_1.9.bin', 'pocket_firmware_2.0.bin', 'pocket_firmware_2.1.bin', 'pocket_firmware_2.2.bin', 'other_file.bin')

                already_on_latest = remove_old_firmware_files(mount, 'pocket_firmware_2.1.bin', LoggerSpy())

                self.assertTrue(already_on_latest)
                self.assertEqual(['other_file.bin', 'pocket_firmware_2.1.bin'], sorted(os.listdir(mount)))

        def test_remove_old_firmware_files___when_latest_is_missing___removes_all_of_them(self) -> None:
            with tempfile.TemporaryDirectory() as mount:
                _touch(mount, 'pocket_firmware_1.9.bin', 'pocket_firmware_2.0.bin')

                already_on_latest = remove_old_firmware_files(mount, 'pocket_firmware_2.1.bin', LoggerSpy())

                self.assertFalse(already_on_latest)
                self.assertEqual([], os.listdir(mount))

        def test_remove_old_firmware_files___matches_the_latest_file_ignoring_case(self) -> None:
            with tempfile.TemporaryDirectory() as mount:
                _touch(mount, 'POCKET_FIRMWARE_2.1.BIN'.lower(), 'pocket_firmware_2.0.bin')

                already_on_latest = remove_old_firmware_files(mount, 'Pocket_Firmware_2.1.bin', LoggerSpy())

                self.assertTrue(already_on_latest)
                self.assertEqual(['pocket_firmware_2.1.bin'], os.listdir(mount))

        def test_remove_old_firmware_files___when_mount_has_no_firmware_files___does_nothing(self) -> None:
            with tempfile.TemporaryDirectory() as mount:
                already_on_latest = remove_old_firmware_files(mount, 'pocket_firmware_2.1.bin', LoggerSpy())

                self.assertFalse(already_on_latest)
                self.assertEqual([], os.listdir(mount))


def _touch(mount: str, *names: str) -> None:
    for name in names:
        Path(mount, name).touch()
