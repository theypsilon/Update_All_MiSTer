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
import unittest

from test.frontends_service_tester import FrontendsServiceTester
from update_all.constants import FILE_lastcore_dat


class TestFrontendsService(unittest.TestCase):
    def test_on_frontend_deleted___when_bootcore_is_lastcore___removes_lastcore_dat(self):
        sut = FrontendsServiceTester(files={
            FILE_lastcore_dat: {'content': 'zaparoo/MiSTer_Zaparoo'},
        })

        sut.on_frontend_deleted(
            changed=True,
            contents='[mister]\nfoo=bar\n  BOOTCORE  =  LastCore  \n',
        )

        self.assertFalse(sut.file_system.is_file(FILE_lastcore_dat))

    def test_on_frontend_deleted___when_bootcore_is_not_lastcore___keeps_lastcore_dat(self):
        sut = FrontendsServiceTester(files={
            FILE_lastcore_dat: {'content': 'zaparoo/MiSTer_Zaparoo'},
        })

        sut.on_frontend_deleted(
            changed=True,
            contents='[mister]\nfoo=bar\nbootcore=menu\n',
        )

        self.assertTrue(sut.file_system.is_file(FILE_lastcore_dat))

    def test_on_frontend_deleted___when_unchanged___never_touches_lastcore_dat(self):
        sut = FrontendsServiceTester(files={
            FILE_lastcore_dat: {'content': 'zaparoo/MiSTer_Zaparoo'},
        })

        sut.on_frontend_deleted(changed=False, contents='')

        self.assertTrue(sut.file_system.is_file(FILE_lastcore_dat))
