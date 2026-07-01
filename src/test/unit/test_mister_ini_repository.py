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

from test.mister_ini_repository_tester import MisterIniRepositoryTester
from update_all.constants import FILE_MiSTer_ini, FILE_MiSTer_ini_update_all_backup
from update_all.mister_ini_repository import FILE_mister_ini_backup_pending, FILE_mister_ini_pending


class TestMisterIniRepository(unittest.TestCase):
    def test_ensure_mister_ini_key___when_missing_and_create_enabled___creates_mister_ini_without_backup(self):
        sut = MisterIniRepositoryTester()

        changed, contents = sut.ensure_mister_ini_key('RA_*', 'main', 'MiSTer_RA', create_if_missing=True)

        self.assertTrue(changed)
        self.assertEqual('[RA_*]\nmain=MiSTer_RA\n', contents)
        self.assertEqual('[RA_*]\nmain=MiSTer_RA\n', sut.file_system.read_file_contents(FILE_MiSTer_ini))
        self.assertFalse(sut.file_system.is_file(FILE_MiSTer_ini_update_all_backup))

    def test_ensure_mister_ini_key___when_existing_and_changed___stages_backs_up_and_replaces_mister_ini(self):
        original = '[mister]\nfoo=bar\n'
        updated = '[mister]\nfoo=bar\n\n[RA_*]\nmain=MiSTer_RA\n'
        sut = MisterIniRepositoryTester(files={
            FILE_MiSTer_ini: {'content': original},
        })

        changed, contents = sut.ensure_mister_ini_key('RA_*', 'main', 'MiSTer_RA', create_if_missing=True)

        observed = [
            (record['scope'], record['data'])
            for record in sut.file_system.write_records
            if record['scope'] in ('write_file_contents', 'copy', 'fsync', 'move', 'fsync_parent_dir', 'unlink')
        ]
        self.assertEqual(
            [
                ('write_file_contents', ['/media/fat/.mister.ini.new', updated]),
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
        self.assertTrue(changed)
        self.assertEqual(updated, contents)
        self.assertEqual(original, sut.file_system.read_file_contents(FILE_MiSTer_ini_update_all_backup))
        self.assertEqual(updated, sut.file_system.read_file_contents(FILE_MiSTer_ini))
        self.assertFalse(sut.file_system.is_file(FILE_mister_ini_pending))
        self.assertFalse(sut.file_system.is_file(FILE_mister_ini_backup_pending))

    def test_ensure_mister_ini_key___when_existing_key_is_equivalent___does_not_write(self):
        original = '[MISTER]\nMAIN = Zaparoo/mister_zaparoo\n'
        sut = MisterIniRepositoryTester(files={
            FILE_MiSTer_ini: {'content': original},
        })

        changed, contents = sut.ensure_mister_ini_key(
            'mister',
            'main',
            'zaparoo/MiSTer_Zaparoo',
            create_if_missing=True,
        )

        self.assertFalse(changed)
        self.assertEqual(original, contents)
        self.assertEqual([], sut.file_system.write_records)
        self.assertEqual(original, sut.file_system.read_file_contents(FILE_MiSTer_ini))

    def test_ensure_mister_ini_key___when_missing_and_create_disabled___does_not_write(self):
        sut = MisterIniRepositoryTester()

        changed, contents = sut.ensure_mister_ini_key('RA_*', 'main', 'MiSTer_RA', create_if_missing=False)

        self.assertFalse(changed)
        self.assertEqual('', contents)
        self.assertFalse(sut.file_system.is_file(FILE_MiSTer_ini))

    def test_remove_mister_ini_key___when_section_becomes_empty_and_flag_enabled___removes_section(self):
        sut = MisterIniRepositoryTester(files={
            FILE_MiSTer_ini: {'content': '[mister]\nfoo=bar\n\n[RA_*]\nmain=MiSTer_RA\n'},
        })

        changed, contents = sut.remove_mister_ini_key('RA_*', 'main', 'MiSTer_RA', remove_empty_section=True)

        self.assertTrue(changed)
        self.assertEqual('[mister]\nfoo=bar\n', contents)
        self.assertEqual('[mister]\nfoo=bar\n', sut.file_system.read_file_contents(FILE_MiSTer_ini))
