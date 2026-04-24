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
from pathlib import Path

from test.ini_assertions import assertEqualIni
from test.testing_objects import downloader_ini
from update_all.config import Config
from update_all.constants import DOWNLOADER_ARCADE_ROMS_DB_INI, DOWNLOADER_BIOS_DB_INI, DOWNLOADER_AJGOWANS_MANUALSDB_INI, DOWNLOADER_INI_STANDARD_PATH, MEDIA_FAT
from update_all.databases import AllDBs, DB_ID_DISTRIBUTION_MISTER, DB_ID_NAMES_TXT, all_dbs
from update_all.ini_repository import read_ini_contents
from test.fake_filesystem import FileSystemFactory
from test.file_system_tester_state import FileSystemState
from test.update_all_service_tester import default_databases, IniRepositoryTester
import unittest


def test_write_downloader_ini(files=None, folders=None, config: Config = None):
    state = FileSystemState(files=files, folders=folders)
    ini_repository = IniRepositoryTester(file_system=FileSystemFactory(state=state).create_for_system_scope())
    ini_repository.write_downloader_ini(config)
    return state


class TestIniRepository(unittest.TestCase):

    def test_write_downloader_ini___over_dirty_downloader_ini_after_changing_some_options___writes_changed_downloader(self):
        config = Config(
            databases=default_databases(add=[all_dbs('').LLAPI_FOLDER.db_id, DB_ID_NAMES_TXT], sub=[DB_ID_DISTRIBUTION_MISTER]),
            names_region='EU',
            names_char_code='CHAR28',
            names_sort_code='Manufacturer',
            download_beta_cores=True
        )
        fs = test_write_downloader_ini(files={
            downloader_ini: {'content': Path('test/fixtures/downloader_ini/dirty_downloader.ini').read_text()}
        }, config=config)
        assertEqualIni(self, 'test/fixtures/downloader_ini/changed_downloader.ini', fs.files[downloader_ini]['content'])

    def test_write_downloader_ini___over_bug_duplications_downloader_ini_after_changing_some_options___writes_changed_downloader(self):
        config = Config(download_beta_cores=True, names_region='EU', databases=default_databases(add=[
            DB_ID_NAMES_TXT,
            all_dbs('').THEYPSILON_UNOFFICIAL_DISTRIBUTION.db_id,
            all_dbs('').LLAPI_FOLDER.db_id,
            all_dbs('').UBERYOJI_BOOT_ROMS.db_id,
            all_dbs('').ARCADE_OFFSET_FOLDER.db_id,
            all_dbs('').TTY2OLED_FILES.db_id,
            all_dbs('').I2C2OLED_FILES.db_id,
            all_dbs('').MISTERSAM_FILES.db_id
        ]))
        fs = test_write_downloader_ini(files={
            downloader_ini: {'content': Path('test/fixtures/downloader_ini/bug_duplications_downloader.ini').read_text()}
        }, config=config)
        assertEqualIni(self, 'test/fixtures/downloader_ini/bug_duplications_downloader.ini', fs.files[downloader_ini]['content'])

    def test_write_downloader_ini___over_bug_names_txt_updater_disabled_downloader_ini_after_changing_some_options___writes_changed_downloader(self):
        config = Config(download_beta_cores=True, databases=default_databases(sub=[DB_ID_NAMES_TXT], add=[
            all_dbs('').AGG23_DB.db_id,
            all_dbs('').THEYPSILON_UNOFFICIAL_DISTRIBUTION.db_id,
            all_dbs('').LLAPI_FOLDER.db_id,
            all_dbs('').UBERYOJI_BOOT_ROMS.db_id,
            all_dbs('').ARCADE_OFFSET_FOLDER.db_id,
            all_dbs('').TTY2OLED_FILES.db_id,
            all_dbs('').I2C2OLED_FILES.db_id,
            all_dbs('').MISTERSAM_FILES.db_id
        ]))
        fs = test_write_downloader_ini(files={
            downloader_ini: {'content': Path('test/fixtures/downloader_ini/bug_names_txt_updater_disabled_downloader.ini').read_text()}
        }, config=config)
        assertEqualIni(self, 'test/fixtures/downloader_ini/bug_names_txt_updater_disabled_downloader.ini', fs.files[downloader_ini]['content'])

    def test_write_downloader_ini___lower_case_coin_ops_after_adding_names_txt___becomes_uppercase_after_writing_downloader(self):
        config = Config(databases=default_databases(add=[DB_ID_NAMES_TXT]))
        fs = test_write_downloader_ini(files={
            downloader_ini: {'content': Path('test/fixtures/downloader_ini/coin_op_lowercase_downloader.ini').read_text()}
        }, config=config)
        assertEqualIni(self, 'test/fixtures/downloader_ini/coin_op_uppercase_plus_names_downloader.ini', fs.files[downloader_ini]['content'])

    def test_write_downloader_ini___with_separate_db_and_filtered_hbmame___does_not_add_arcade_roms_to_downloader_ini(self):
        config = Config(databases=default_databases(add=[all_dbs('').ARCADE_ROMS.db_id]), hbmame_filter=True)
        fs = test_write_downloader_ini(files={
            downloader_ini: {'content': Path('test/fixtures/downloader_ini/default_downloader.ini').read_text()}
        }, config=config)
        assertEqualIni(self, 'test/fixtures/downloader_ini/default_downloader.ini', fs.files[downloader_ini]['content'])

    def test_write_downloader_ini___with_existing_arcade_roms_in_downloader_ini___removes_it(self):
        config = Config(databases=default_databases(add=[all_dbs('').ARCADE_ROMS.db_id]), hbmame_filter=True)
        fs = test_write_downloader_ini(files={
            downloader_ini: {'content': Path('test/fixtures/downloader_ini/filtered_hbmame_downloader.ini').read_text()}
        }, config=config)
        assertEqualIni(self, 'test/fixtures/downloader_ini/default_downloader.ini', fs.files[downloader_ini]['content'])

    def test_write_downloader_ini___with_existing_arcade_roms_and_mister_filter___removes_arcade_roms_keeps_mister(self):
        config = Config(databases=default_databases(add=[all_dbs('').ARCADE_ROMS.db_id]), hbmame_filter=False)
        fs = test_write_downloader_ini(files={
            downloader_ini: {'content': Path('test/fixtures/downloader_ini/mister_filtered_plus_hbmame_downloader.ini').read_text()}
        }, config=config)
        assertEqualIni(self, 'test/fixtures/downloader_ini/mister_filtered_no_arcade_roms_downloader.ini', fs.files[downloader_ini]['content'])

    def test_write_downloader_ini___with_existing_arcade_roms_and_heavy_filter___removes_arcade_roms_keeps_rest(self):
        config = Config(databases=default_databases(add=[all_dbs('').ARCADE_ROMS.db_id]), hbmame_filter=False)
        fs = test_write_downloader_ini(files={
            downloader_ini: {'content': Path('test/fixtures/downloader_ini/heavily_filtered_plus_hbmame_downloader.ini').read_text()}
        }, config=config)
        assertEqualIni(self, 'test/fixtures/downloader_ini/heavily_filtered_no_arcade_roms_downloader.ini', fs.files[downloader_ini]['content'])

    def test_write_separate_db_ini_files___with_filtered_hbmame___writes_filter_to_arcade_roms_ini(self):
        state = FileSystemState()
        ini_repository = IniRepositoryTester(file_system=FileSystemFactory(state=state).create_for_system_scope())
        ini_repository.initialize_downloader_ini_base_path(MEDIA_FAT)
        config = Config(databases=default_databases(add=[all_dbs('').ARCADE_ROMS.db_id]), hbmame_filter=True)

        ini_repository.write_separate_db_ini_files(config)

        self.assertEqual(
            '[arcade_roms_db]\n'
            'db_url = https://raw.githubusercontent.com/zakk4223/ArcadeROMsDB_MiSTer/db/arcade_roms_db.json.zip\n'
            'filter = !hbmame\n',
            state.files[f'{MEDIA_FAT}/{DOWNLOADER_ARCADE_ROMS_DB_INI}'.lower()]['content']
        )

    def test_write_downloader_ini___with_negated_jtbeta_but_beta_cores_activated___writes_jtcores_without_negated_jtbeta(self):
        config = Config(databases={all_dbs('').JTCORES.db_id, all_dbs('').UPDATE_ALL_MISTER.db_id}, download_beta_cores=True)
        fs = test_write_downloader_ini(files={
            downloader_ini: {'content': Path('test/fixtures/downloader_ini/just_jtcores_with_negated_jtbeta.ini').read_text()}
        }, config=config)
        assertEqualIni(self, 'test/fixtures/downloader_ini/just_jtcores_with_filter_wtf.ini', fs.files[downloader_ini]['content'])

    def test_write_downloader_ini___with_update_all_ini_and_a_bunch_other_things___puts_update_all_ini_at_the_end(self):
        config = Config(databases=default_databases())
        fs = test_write_downloader_ini(files={
            downloader_ini: {'content': Path('test/fixtures/downloader_ini/default_downloader_unsorted.ini').read_text()}
        }, config=config)
        self.assertEqual(Path('test/fixtures/downloader_ini/default_downloader.ini').read_text(), fs.files[downloader_ini]['content'])

    def test_write_separate_db_ini_files___with_multiple_active_manualsdbs___writes_single_file_with_multiple_sections(self):
        state = FileSystemState()
        ini_repository = IniRepositoryTester(file_system=FileSystemFactory(state=state).create_for_system_scope())
        ini_repository.initialize_downloader_ini_base_path(MEDIA_FAT)
        config = Config(databases=default_databases(add=[
            all_dbs('').MANUALSDB_3DO.db_id,
            all_dbs('').MANUALSDB_NES.db_id,
            all_dbs('').MANUALSDB_SNES.db_id,
        ]))

        ini_repository.write_separate_db_ini_files(config)

        path = f'{MEDIA_FAT}/{DOWNLOADER_AJGOWANS_MANUALSDB_INI}'.lower()
        contents = state.files[path]['content']
        parsed = read_ini_contents(contents)
        self.assertEqual(
            {'ajgowans/manualsdb-3do', 'ajgowans/manualsdb-nes', 'ajgowans/manualsdb-snes'},
            {s for s in parsed.sections()}
        )
        self.assertEqual(
            'https://raw.githubusercontent.com/ajgowans/manualsdb-nes/db/db.json.zip',
            parsed['ajgowans/manualsdb-nes']['db_url']
        )

    def test_write_separate_db_ini_files___with_some_manualsdbs_deactivated___shrinks_file_to_remaining_sections(self):
        state = FileSystemState(files={
            f'{MEDIA_FAT}/{DOWNLOADER_AJGOWANS_MANUALSDB_INI}': {'content':
                '[ajgowans/manualsdb-3do]\n'
                'db_url = https://raw.githubusercontent.com/ajgowans/manualsdb-3do/db/db.json.zip\n\n'
                '[ajgowans/manualsdb-nes]\n'
                'db_url = https://raw.githubusercontent.com/ajgowans/manualsdb-nes/db/db.json.zip\n\n'
                '[ajgowans/manualsdb-snes]\n'
                'db_url = https://raw.githubusercontent.com/ajgowans/manualsdb-snes/db/db.json.zip\n'
            }
        })
        ini_repository = IniRepositoryTester(file_system=FileSystemFactory(state=state).create_for_system_scope())
        ini_repository.initialize_downloader_ini_base_path(MEDIA_FAT)
        config = Config(databases=default_databases(add=[all_dbs('').MANUALSDB_NES.db_id]))

        ini_repository.write_separate_db_ini_files(config)

        path = f'{MEDIA_FAT}/{DOWNLOADER_AJGOWANS_MANUALSDB_INI}'.lower()
        parsed = read_ini_contents(state.files[path]['content'])
        self.assertEqual({'ajgowans/manualsdb-nes'}, {s for s in parsed.sections()})

    def test_write_separate_db_ini_files___with_all_manualsdbs_deactivated___deletes_file(self):
        state = FileSystemState(files={
            f'{MEDIA_FAT}/{DOWNLOADER_AJGOWANS_MANUALSDB_INI}': {'content':
                '[ajgowans/manualsdb-nes]\n'
                'db_url = https://raw.githubusercontent.com/ajgowans/manualsdb-nes/db/db.json.zip\n'
            }
        })
        ini_repository = IniRepositoryTester(file_system=FileSystemFactory(state=state).create_for_system_scope())
        ini_repository.initialize_downloader_ini_base_path(MEDIA_FAT)
        config = Config(databases=default_databases())

        ini_repository.write_separate_db_ini_files(config)

        path = f'{MEDIA_FAT}/{DOWNLOADER_AJGOWANS_MANUALSDB_INI}'.lower()
        self.assertNotIn(path, state.files)

    def test_write_separate_db_ini_files___with_bios_and_manualsdbs_active___writes_them_to_different_files(self):
        state = FileSystemState()
        ini_repository = IniRepositoryTester(file_system=FileSystemFactory(state=state).create_for_system_scope())
        ini_repository.initialize_downloader_ini_base_path(MEDIA_FAT)
        config = Config(databases=default_databases(add=[
            all_dbs('').BIOS.db_id,
            all_dbs('').MANUALSDB_NES.db_id,
        ]))

        ini_repository.write_separate_db_ini_files(config)

        bios_path = f'{MEDIA_FAT}/{DOWNLOADER_BIOS_DB_INI}'.lower()
        manuals_path = f'{MEDIA_FAT}/{DOWNLOADER_AJGOWANS_MANUALSDB_INI}'.lower()
        self.assertIn('[bios_db]', state.files[bios_path]['content'])
        self.assertNotIn('manualsdb', state.files[bios_path]['content'])
        self.assertIn('[ajgowans/manualsdb-nes]', state.files[manuals_path]['content'])
        self.assertNotIn('bios_db', state.files[manuals_path]['content'])

    def test_extract_dbs_to_separate_ini___with_multiple_manualsdbs_in_downloader_ini___extracts_all_into_single_file_in_one_pass(self):
        state = FileSystemState(files={
            downloader_ini: {'content':
                '[update_all_mister]\n'
                'db_url = https://update_all\n\n'
                '[ajgowans/manualsdb-3do]\n'
                'db_url = https://raw.githubusercontent.com/ajgowans/manualsdb-3do/db/db.json.zip\n\n'
                '[ajgowans/manualsdb-nes]\n'
                'db_url = https://raw.githubusercontent.com/ajgowans/manualsdb-nes/db/db.json.zip\n\n'
                '[distribution_mister]\n'
                'db_url = https://distribution\n'
            }
        })
        ini_repository = IniRepositoryTester(file_system=FileSystemFactory(state=state).create_for_system_scope())
        ini_repository.initialize_downloader_ini_base_path(MEDIA_FAT)
        downloader_ini_dict = {
            'update_all_mister': None, 'distribution_mister': None,
            'ajgowans/manualsdb-3do': None, 'ajgowans/manualsdb-nes': None,
        }

        moved = ini_repository.extract_dbs_to_separate_ini(
            ['ajgowans/manualsdb-3do', 'ajgowans/manualsdb-nes', 'ajgowans/manualsdb-snes'],
            DOWNLOADER_AJGOWANS_MANUALSDB_INI,
            downloader_ini_dict,
        )

        self.assertEqual({'ajgowans/manualsdb-3do', 'ajgowans/manualsdb-nes'}, set(moved))
        remaining = read_ini_contents(state.files[downloader_ini]['content'])
        self.assertEqual({'update_all_mister', 'distribution_mister'}, set(remaining.sections()))
        manuals_path = f'{MEDIA_FAT}/{DOWNLOADER_AJGOWANS_MANUALSDB_INI}'.lower()
        extracted = read_ini_contents(state.files[manuals_path]['content'])
        self.assertEqual({'ajgowans/manualsdb-3do', 'ajgowans/manualsdb-nes'}, set(extracted.sections()))
        self.assertNotIn('ajgowans/manualsdb-3do', downloader_ini_dict)
        self.assertNotIn('ajgowans/manualsdb-nes', downloader_ini_dict)

    def test_extract_dbs_to_separate_ini___with_existing_target_file___merges_preserving_non_conflicting_sections(self):
        state = FileSystemState(files={
            downloader_ini: {'content':
                '[ajgowans/manualsdb-nes]\n'
                'db_url = https://raw.githubusercontent.com/ajgowans/manualsdb-nes/db/db.json.zip\n'
            },
            f'{MEDIA_FAT}/{DOWNLOADER_AJGOWANS_MANUALSDB_INI}': {'content':
                '[ajgowans/manualsdb-3do]\n'
                'db_url = https://raw.githubusercontent.com/ajgowans/manualsdb-3do/db/db.json.zip\n'
            },
        })
        ini_repository = IniRepositoryTester(file_system=FileSystemFactory(state=state).create_for_system_scope())
        ini_repository.initialize_downloader_ini_base_path(MEDIA_FAT)
        downloader_ini_dict = {'ajgowans/manualsdb-nes': None}

        moved = ini_repository.extract_dbs_to_separate_ini(
            ['ajgowans/manualsdb-3do', 'ajgowans/manualsdb-nes'],
            DOWNLOADER_AJGOWANS_MANUALSDB_INI,
            downloader_ini_dict,
        )

        self.assertEqual(['ajgowans/manualsdb-nes'], moved)
        manuals_path = f'{MEDIA_FAT}/{DOWNLOADER_AJGOWANS_MANUALSDB_INI}'.lower()
        merged = read_ini_contents(state.files[manuals_path]['content'])
        self.assertEqual({'ajgowans/manualsdb-3do', 'ajgowans/manualsdb-nes'}, set(merged.sections()))

    def test_extract_dbs_to_separate_ini___with_colliding_section_in_target_file___downloader_ini_version_wins(self):
        state = FileSystemState(files={
            downloader_ini: {'content':
                '[ajgowans/manualsdb-nes]\n'
                'db_url = https://new-url.example/db.json.zip\n'
            },
            f'{MEDIA_FAT}/{DOWNLOADER_AJGOWANS_MANUALSDB_INI}': {'content':
                '[ajgowans/manualsdb-nes]\n'
                'db_url = https://old-url.example/db.json.zip\n'
            },
        })
        ini_repository = IniRepositoryTester(file_system=FileSystemFactory(state=state).create_for_system_scope())
        ini_repository.initialize_downloader_ini_base_path(MEDIA_FAT)
        downloader_ini_dict = {'ajgowans/manualsdb-nes': None}

        ini_repository.extract_dbs_to_separate_ini(
            ['ajgowans/manualsdb-nes'],
            DOWNLOADER_AJGOWANS_MANUALSDB_INI,
            downloader_ini_dict,
        )

        manuals_path = f'{MEDIA_FAT}/{DOWNLOADER_AJGOWANS_MANUALSDB_INI}'.lower()
        merged = read_ini_contents(state.files[manuals_path]['content'])
        self.assertEqual('https://new-url.example/db.json.zip', merged['ajgowans/manualsdb-nes']['db_url'])
