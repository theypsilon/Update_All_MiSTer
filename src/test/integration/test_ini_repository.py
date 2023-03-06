# Copyright (c) 2022-2023 José Manuel Barroso Galindo <theypsilon@gmail.com>

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

from test.testing_objects import downloader_ini
from update_all.config import Config
from update_all.databases import AllDBs, DB_ID_DISTRIBUTION_MISTER, DB_ID_NAMES_TXT
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
            databases=default_databases(add=[AllDBs.LLAPI_FOLDER.db_id, DB_ID_NAMES_TXT], sub=[DB_ID_DISTRIBUTION_MISTER]),
            names_region='EU',
            names_char_code='CHAR28',
            names_sort_code='Manufacturer',
            download_beta_cores=True
        )
        fs = test_write_downloader_ini(files={
            downloader_ini: {'content': Path('test/fixtures/downloader_ini/dirty_downloader.ini').read_text()}
        }, config=config)
        self.assertEqual(Path('test/fixtures/downloader_ini/changed_downloader.ini').read_text(), fs.files[downloader_ini]['content'])

    def test_write_downloader_ini___over_bug_duplications_downloader_ini_after_changing_some_options___writes_changed_downloader(self):
        config = Config(download_beta_cores=True, names_region='EU', databases=default_databases(add=[
            DB_ID_NAMES_TXT,
            AllDBs.THEYPSILON_UNOFFICIAL_DISTRIBUTION.db_id,
            AllDBs.LLAPI_FOLDER.db_id,
            AllDBs.ARCADE_ROMS.db_id,
            AllDBs.ARCADE_OFFSET_FOLDER.db_id,
            AllDBs.TTY2OLED_FILES.db_id,
            AllDBs.I2C2OLED_FILES.db_id,
            AllDBs.MISTERSAM_FILES.db_id
        ]))
        fs = test_write_downloader_ini(files={
            downloader_ini: {'content': Path('test/fixtures/downloader_ini/bug_duplications_downloader.ini').read_text()}
        }, config=config)
        self.assertEqual(Path('test/fixtures/downloader_ini/bug_duplications_downloader.ini').read_text(), fs.files[downloader_ini]['content'])

    def test_write_downloader_ini___over_bug_names_txt_updater_disabled_downloader_ini_after_changing_some_options___writes_changed_downloader(self):
        config = Config(download_beta_cores=True, databases=default_databases(sub=[DB_ID_NAMES_TXT], add=[
            AllDBs.BIOS.db_id,
            AllDBs.THEYPSILON_UNOFFICIAL_DISTRIBUTION.db_id,
            AllDBs.LLAPI_FOLDER.db_id,
            AllDBs.ARCADE_ROMS.db_id,
            AllDBs.ARCADE_OFFSET_FOLDER.db_id,
            AllDBs.TTY2OLED_FILES.db_id,
            AllDBs.I2C2OLED_FILES.db_id,
            AllDBs.MISTERSAM_FILES.db_id
        ]))
        fs = test_write_downloader_ini(files={
            downloader_ini: {'content': Path('test/fixtures/downloader_ini/bug_names_txt_updater_disabled_downloader.ini').read_text()}
        }, config=config)
        self.assertEqual(Path('test/fixtures/downloader_ini/bug_names_txt_updater_disabled_downloader.ini').read_text(), fs.files[downloader_ini]['content'])

    def test_write_downloader_ini___lower_case_coin_ops_after_adding_names_txt___becomes_uppercase_after_writing_downloader(self):
        config = Config(databases=default_databases(add=[DB_ID_NAMES_TXT]))
        fs = test_write_downloader_ini(files={
            downloader_ini: {'content': Path('test/fixtures/downloader_ini/coin_op_lowercase_downloader.ini').read_text()}
        }, config=config)
        self.assertEqual(Path('test/fixtures/downloader_ini/coin_op_uppercase_plus_names_downloader.ini').read_text(), fs.files[downloader_ini]['content'])

    def test_write_downloader_ini___with_roms_db_and_filtered_hbmame___adds_expected_db_with_expected_filter_field(self):
        config = Config(databases=default_databases(add=[AllDBs.ARCADE_ROMS.db_id]), hbmame_filter=True)
        fs = test_write_downloader_ini(files={
            downloader_ini: {'content': Path('test/fixtures/downloader_ini/default_downloader.ini').read_text()}
        }, config=config)
        self.assertEqual(Path('test/fixtures/downloader_ini/filtered_hbmame_downloader.ini').read_text(), fs.files[downloader_ini]['content'])

    def test_write_downloader_ini___with_already_existing_roms_db_and_filtered_hbmame___keeps_it_the_same(self):
        config = Config(databases=default_databases(add=[AllDBs.ARCADE_ROMS.db_id]), hbmame_filter=True)
        fs = test_write_downloader_ini(files={
            downloader_ini: {'content': Path('test/fixtures/downloader_ini/filtered_hbmame_downloader.ini').read_text()}
        }, config=config)
        self.assertEqual(Path('test/fixtures/downloader_ini/filtered_hbmame_downloader.ini').read_text(), fs.files[downloader_ini]['content'])

    def test_write_downloader_ini___when_removing_filtered_hbmame___removes_expected_filter_field(self):
        config = Config(databases=default_databases(add=[AllDBs.ARCADE_ROMS.db_id]), hbmame_filter=False)
        fs = test_write_downloader_ini(files={
            downloader_ini: {'content': Path('test/fixtures/downloader_ini/filtered_hbmame_downloader.ini').read_text()}
        }, config=config)
        self.assertEqual(Path('test/fixtures/downloader_ini/arcade_roms_downloader.ini').read_text(), fs.files[downloader_ini]['content'])

    def test_write_downloader_ini___when_removing_arcade_roms_db_altogether___removes_the_db_from_downloader_ini(self):
        config = Config(databases=default_databases())
        fs = test_write_downloader_ini(files={
            downloader_ini: {'content': Path('test/fixtures/downloader_ini/filtered_hbmame_downloader.ini').read_text()}
        }, config=config)
        self.assertEqual(Path('test/fixtures/downloader_ini/default_downloader.ini').read_text(), fs.files[downloader_ini]['content'])

    def test_write_downloader_ini___with_roms_db_and_mister_filtered_hbmame___adds_expected_composed_filter_field(self):
        config = Config(databases=default_databases(add=[AllDBs.ARCADE_ROMS.db_id]), hbmame_filter=True)
        fs = test_write_downloader_ini(files={
            downloader_ini: {'content': Path('test/fixtures/downloader_ini/mister_filtered_downloader.ini').read_text()}
        }, config=config)
        self.assertEqual(Path('test/fixtures/downloader_ini/mister_filtered_plus_hbmame_downloader.ini').read_text(), fs.files[downloader_ini]['content'])

    def test_write_downloader_ini__removes_hbmame_from_mister_filtered_roms_db___restores_previous_filters(self):
        config = Config(databases=default_databases(add=[AllDBs.ARCADE_ROMS.db_id]), hbmame_filter=False)
        fs = test_write_downloader_ini(files={
            downloader_ini: {'content': Path('test/fixtures/downloader_ini/mister_filtered_plus_hbmame_downloader.ini').read_text()}
        }, config=config)
        self.assertEqual(Path('test/fixtures/downloader_ini/mister_filtered_downloader.ini').read_text(), fs.files[downloader_ini]['content'])

    def test_write_downloader_ini___with_roms_db_and_heavily_filtered_hbmame___adds_expected_composed_filter_field(self):
        config = Config(databases=default_databases(add=[AllDBs.ARCADE_ROMS.db_id]), hbmame_filter=True)
        fs = test_write_downloader_ini(files={
            downloader_ini: {'content': Path('test/fixtures/downloader_ini/heavily_filtered_downloader.ini').read_text()}
        }, config=config)
        self.assertEqual(Path('test/fixtures/downloader_ini/heavily_filtered_plus_hbmame_downloader.ini').read_text(), fs.files[downloader_ini]['content'])

    def test_write_downloader_ini__removes_hbmame_from_heavily_filtered_roms_db___restores_previous_filters(self):
        config = Config(databases=default_databases(add=[AllDBs.ARCADE_ROMS.db_id]), hbmame_filter=False)
        fs = test_write_downloader_ini(files={
            downloader_ini: {'content': Path('test/fixtures/downloader_ini/heavily_filtered_plus_hbmame_downloader.ini').read_text()}
        }, config=config)
        self.assertEqual(Path('test/fixtures/downloader_ini/heavily_filtered_downloader.ini').read_text(), fs.files[downloader_ini]['content'])
