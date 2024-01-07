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
from urllib.parse import urlparse

from update_all.analogue_pocket.firmware_update import latest_firmware_info


class TestFirmwareUpdate(unittest.TestCase):

        def test_firmware_firmware_info_has_expected_types(self) -> None:
            info = latest_firmware_info()
            self.assertTrue(isinstance(info['size'], float))
            self.assertTrue(isinstance(info['file'], str))
            self.assertTrue(isinstance(info['md5'], str))
            self.assertTrue(isinstance(info['version'], str))
            self.assertTrue(isinstance(info['url'], str))
            self.assertEqual(5, len(info.keys()))

        def test_firmware_firmware_info_follows_expected_invariants(self) -> None:
            info = latest_firmware_info()
            self.assertGreaterEqual(2.0, float(info['version']))
            self.assertTrue('analogue.co', urlparse(info['url']).netloc)
