# Copyright (c) 2022-2024 José Manuel Barroso Galindo <theypsilon@gmail.com>

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

import unittest
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from test.fake_filesystem import FileSystemFactory
from test.file_system_tester_state import FileSystemState
from test.testing_objects import pocket_firmware_details_json
from test.update_all_service_tester import LocalRepositoryTester


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
