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

from test.zaparoo_service_tester import ZaparooServiceTester
from update_all.constants import FILE_lastcore_dat


ENABLED_MISTER_INI = '[mister]\nmain=zaparoo/MiSTer_Zaparoo\n'
DISABLED_MISTER_INI = '[mister]\nfoo=bar\n'


class TestZaparooService(unittest.TestCase):
    def test_frontend_activation_applied___by_default___is_false(self):
        sut = ZaparooServiceTester()

        self.assertFalse(sut.frontend_activation_applied())

    def test_on_frontend_added___when_changed___marks_frontend_activation_applied(self):
        sut = ZaparooServiceTester()

        sut.on_frontend_added(changed=True, contents=ENABLED_MISTER_INI)

        self.assertTrue(sut.frontend_activation_applied())

    def test_on_frontend_added___when_unchanged___does_not_mark_frontend_activation_applied(self):
        sut = ZaparooServiceTester()

        sut.on_frontend_added(changed=False, contents='')

        self.assertFalse(sut.frontend_activation_applied())

    def test_on_frontend_deleted___when_changed___clears_frontend_activation_applied(self):
        sut = ZaparooServiceTester()
        sut.on_frontend_added(changed=True, contents=ENABLED_MISTER_INI)

        sut.on_frontend_deleted(changed=True, contents=DISABLED_MISTER_INI)

        self.assertFalse(sut.frontend_activation_applied())

    def test_on_frontend_deleted___when_bootcore_is_lastcore___removes_lastcore_dat(self):
        sut = ZaparooServiceTester(files={
            FILE_lastcore_dat: {'content': 'zaparoo/MiSTer_Zaparoo'},
        })

        sut.on_frontend_deleted(
            changed=True,
            contents='[mister]\nfoo=bar\n  BOOTCORE  =  LastCore  \n',
        )

        self.assertFalse(sut.file_system.is_file(FILE_lastcore_dat))

    def test_on_frontend_deleted___when_bootcore_is_not_lastcore___keeps_lastcore_dat(self):
        sut = ZaparooServiceTester(files={
            FILE_lastcore_dat: {'content': 'zaparoo/MiSTer_Zaparoo'},
        })

        sut.on_frontend_deleted(
            changed=True,
            contents='[mister]\nfoo=bar\nbootcore=menu\n',
        )

        self.assertTrue(sut.file_system.is_file(FILE_lastcore_dat))

    def test_on_frontend_deleted___when_unchanged___never_touches_lastcore_dat(self):
        sut = ZaparooServiceTester(files={
            FILE_lastcore_dat: {'content': 'zaparoo/MiSTer_Zaparoo'},
        })

        sut.on_frontend_deleted(changed=False, contents='')

        self.assertTrue(sut.file_system.is_file(FILE_lastcore_dat))
