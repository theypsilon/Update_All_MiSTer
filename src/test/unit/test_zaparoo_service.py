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
from update_all.constants import FILE_MiSTer_ini, FILE_MiSTer_ini_update_all_backup, FILE_lastcore_dat
from update_all.zaparoo_service import (
    FILE_zaparoo_frontend,
    FILE_zaparoo_mister_ini_backup_pending,
    FILE_zaparoo_mister_ini_pending,
    mister_ini_contents_equivalent,
)

class TestZaparooService(unittest.TestCase):
    def test_set_frontend_active_true___when_frontend_is_missing___returns_without_applying(self):
        sut = ZaparooServiceTester()

        sut.set_frontend_active(True)

        self.assertEqual(0, sut.frontend_activation_calls)

    def test_set_frontend_active_true___when_frontend_exists___applies_frontend_activation(self):
        sut = ZaparooServiceTester(files={
            FILE_zaparoo_frontend: {'content': 'frontend'},
        })

        sut.set_frontend_active(True)

        self.assertEqual(1, sut.frontend_activation_calls)

    def test_set_frontend_active_true___when_mister_ini_is_missing___creates_mister_ini_with_zaparoo_frontend(self):
        sut = ZaparooServiceTester(files={
            FILE_zaparoo_frontend: {'content': 'frontend'},
        })

        sut.set_frontend_active(True)

        self.assertEqual('[mister]\nmain=zaparoo/MiSTer_Zaparoo\n', sut.file_system.read_file_contents(FILE_MiSTer_ini))
        self.assertFalse(sut.file_system.is_file(FILE_MiSTer_ini_update_all_backup))

    def test_set_frontend_active_true___when_mister_section_is_missing___appends_mister_section_with_zaparoo_frontend(self):
        sut = ZaparooServiceTester(files={
            FILE_zaparoo_frontend: {'content': 'frontend'},
            FILE_MiSTer_ini: {'content': '[menu]\nvideo_mode=8\n'},
        })

        sut.set_frontend_active(True)

        self.assertEqual(
            '[menu]\nvideo_mode=8\n[mister]\nmain=zaparoo/MiSTer_Zaparoo\n',
            sut.file_system.read_file_contents(FILE_MiSTer_ini),
        )

    def test_set_frontend_active_true___when_mister_section_has_no_main___adds_zaparoo_frontend_under_mister_section(self):
        sut = ZaparooServiceTester(files={
            FILE_zaparoo_frontend: {'content': 'frontend'},
            FILE_MiSTer_ini: {'content': '[MiSTer]\nfoo=bar\n[menu]\nvideo_mode=8\n'},
        })

        sut.set_frontend_active(True)

        self.assertEqual(
            '[MiSTer]\nfoo=bar\nmain=zaparoo/MiSTer_Zaparoo\n[menu]\nvideo_mode=8\n',
            sut.file_system.read_file_contents(FILE_MiSTer_ini),
        )

    def test_set_frontend_active_true___when_mister_section_has_different_main___replaces_it_with_zaparoo_frontend(self):
        sut = ZaparooServiceTester(files={
            FILE_zaparoo_frontend: {'content': 'frontend'},
            FILE_MiSTer_ini: {'content': '[mister]\nmain=menu.rbf\nfoo=bar\n'},
        })

        sut.set_frontend_active(True)

        self.assertEqual(
            '[mister]\nmain=zaparoo/MiSTer_Zaparoo\nfoo=bar\n',
            sut.file_system.read_file_contents(FILE_MiSTer_ini),
        )

    def test_set_frontend_active_true___when_zaparoo_frontend_is_already_main_case_insensitive___does_not_rewrite_mister_ini(self):
        contents = '[MISTER]\nMAIN = Zaparoo/mister_zaparoo\n'
        sut = ZaparooServiceTester(files={
            FILE_zaparoo_frontend: {'content': 'frontend'},
            FILE_MiSTer_ini: {'content': contents},
        })

        sut.set_frontend_active(True)

        self.assertEqual(contents, sut.file_system.read_file_contents(FILE_MiSTer_ini))
        self.assertEqual([], [record for record in sut.file_system.write_records if record['scope'] == 'write_file_contents'])

    def test_set_frontend_active___when_disabled_and_zaparoo_frontend_is_main___removes_zaparoo_frontend_main(self):
        original = '[mister]\nmain=zaparoo/MiSTer_Zaparoo\nfoo=bar\n[menu]\nvideo_mode=8\n'
        sut = ZaparooServiceTester(files={
            FILE_MiSTer_ini: {'content': original},
        })

        sut.set_frontend_active(False)

        self.assertEqual(original, sut.file_system.read_file_contents(FILE_MiSTer_ini_update_all_backup))
        self.assertEqual(
            '[mister]\nfoo=bar\n[menu]\nvideo_mode=8\n',
            sut.file_system.read_file_contents(FILE_MiSTer_ini),
        )

    def test_set_frontend_active___when_disabled_and_bootcore_is_lastcore___removes_lastcore_dat(self):
        sut = ZaparooServiceTester(files={
            FILE_MiSTer_ini: {'content': '[mister]\nmain=zaparoo/MiSTer_Zaparoo\n  BOOTCORE  =  LastCore  \n'},
            FILE_lastcore_dat: {'content': 'zaparoo/MiSTer_Zaparoo'},
        })

        sut.set_frontend_active(False)

        self.assertFalse(sut.file_system.is_file(FILE_lastcore_dat))

    def test_set_frontend_active___when_disabled_and_bootcore_is_not_lastcore___keeps_lastcore_dat(self):
        sut = ZaparooServiceTester(files={
            FILE_MiSTer_ini: {'content': '[mister]\nmain=zaparoo/MiSTer_Zaparoo\nbootcore=menu\n'},
            FILE_lastcore_dat: {'content': 'zaparoo/MiSTer_Zaparoo'},
        })

        sut.set_frontend_active(False)

        self.assertTrue(sut.file_system.is_file(FILE_lastcore_dat))

    def test_zaparoo_frontend_path___points_to_installed_zaparoo_frontend(self):
        self.assertEqual('zaparoo/MiSTer_Zaparoo', FILE_zaparoo_frontend)

    def test_zaparoo_mister_ini_pending_path___is_hidden_new_file_alongside_mister_ini(self):
        self.assertEqual('.MiSTer.ini.new', FILE_zaparoo_mister_ini_pending)

    def test_zaparoo_mister_ini_backup_path___is_update_all_backup_file(self):
        self.assertEqual('.MiSTer.ini.update_all.bak', FILE_MiSTer_ini_update_all_backup)

    def test_zaparoo_mister_ini_backup_pending_path___is_hidden_new_file_alongside_backup(self):
        self.assertEqual('.MiSTer.ini.update_all.bak.new', FILE_zaparoo_mister_ini_backup_pending)

    def test_mister_ini_contents_equivalent___ignores_case_within_lines(self):
        self.assertTrue(mister_ini_contents_equivalent(
            '[MiSTer]\nMAIN=Zaparoo/MiSTer_Zaparoo\n',
            '[mister]\nmain=zaparoo/mister_zaparoo\n',
        ))

    def test_mister_ini_contents_equivalent___ignores_intra_line_whitespace(self):
        self.assertTrue(mister_ini_contents_equivalent(
            '[mister]\n  main  =  zaparoo/MiSTer_Zaparoo\t\n',
            '[mister]\nmain=zaparoo/MiSTer_Zaparoo\n',
        ))

    def test_mister_ini_contents_equivalent___treats_extra_blank_lines_as_different(self):
        self.assertFalse(mister_ini_contents_equivalent(
            '[mister]\nmain=zaparoo/MiSTer_Zaparoo\n',
            '[mister]\n\nmain=zaparoo/MiSTer_Zaparoo\n',
        ))

    def test_mister_ini_contents_equivalent___treats_different_values_as_different(self):
        self.assertFalse(mister_ini_contents_equivalent(
            '[mister]\nmain=menu.rbf\n',
            '[mister]\nmain=zaparoo/MiSTer_Zaparoo\n',
        ))

    def test_set_frontend_active_true___when_internal_step_raises___swallows_and_cleans_up_pending(self):
        original = '[mister]\nmain=menu.rbf\n'
        sut = ZaparooServiceTester(files={
            FILE_zaparoo_frontend: {'content': 'frontend'},
            FILE_MiSTer_ini: {'content': original},
            FILE_zaparoo_mister_ini_pending: {'content': 'leftover from a crashed prior run'},
        })

        def boom():
            raise RuntimeError('boom')
        sut._apply_frontend_activation = boom

        sut.set_frontend_active(True)

        self.assertEqual(original, sut.file_system.read_file_contents(FILE_MiSTer_ini))
        self.assertFalse(sut.file_system.is_file(FILE_zaparoo_mister_ini_pending))

    def test_set_frontend_active_true___when_backup_raises___keeps_original_and_cleans_up_pending(self):
        original = '[mister]\nmain=menu.rbf\n'
        sut = ZaparooServiceTester(files={
            FILE_zaparoo_frontend: {'content': 'frontend'},
            FILE_MiSTer_ini: {'content': original},
        })

        def boom():
            raise RuntimeError('boom')
        sut._write_mister_ini_backup = boom

        sut.set_frontend_active(True)

        self.assertEqual(original, sut.file_system.read_file_contents(FILE_MiSTer_ini))
        self.assertFalse(sut.file_system.is_file(FILE_zaparoo_mister_ini_pending))

    def test_set_frontend_active_true___when_writing_mister_ini___stages_backs_up_then_moves(self):
        original = '[mister]\nmain=menu.rbf\n'
        sut = ZaparooServiceTester(files={
            FILE_zaparoo_frontend: {'content': 'frontend'},
            FILE_MiSTer_ini: {'content': original},
        })

        sut.set_frontend_active(True)

        observed = [
            (record['scope'], record['data'])
            for record in sut.file_system.write_records
            if record['scope'] in ('write_file_contents', 'copy', 'fsync', 'move', 'fsync_parent_dir', 'unlink')
        ]
        self.assertEqual(
            [
                ('write_file_contents', ['/media/fat/.mister.ini.new', '[mister]\nmain=zaparoo/MiSTer_Zaparoo\n']),
                ('fsync', '/media/fat/.mister.ini.new'),
                ('copy', ['/media/fat/mister.ini', '/media/fat/.mister.ini.update_all.bak.new']),
                ('fsync', '/media/fat/.mister.ini.update_all.bak.new'),
                ('move', ['/media/fat/.mister.ini.update_all.bak.new', '/media/fat/.mister.ini.update_all.bak']),
                ('fsync_parent_dir', '/media/fat/.mister.ini.update_all.bak'),
                ('move', ['/media/fat/.mister.ini.new', '/media/fat/mister.ini']),
                ('fsync_parent_dir', '/media/fat/mister.ini'),
            ],
            observed,
        )
        self.assertFalse(sut.file_system.is_file(FILE_zaparoo_mister_ini_pending))
        self.assertFalse(sut.file_system.is_file(FILE_zaparoo_mister_ini_backup_pending))
        self.assertEqual(original, sut.file_system.read_file_contents(FILE_MiSTer_ini_update_all_backup))
        self.assertEqual(
            '[mister]\nmain=zaparoo/MiSTer_Zaparoo\n',
            sut.file_system.read_file_contents(FILE_MiSTer_ini),
        )
