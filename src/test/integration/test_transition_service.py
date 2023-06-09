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
import unittest
from pathlib import Path
from typing import Dict

from test.fake_filesystem import FileSystemFactory
from test.file_system_tester_state import FileSystemState
from test.testing_objects import downloader_ini, update_all_ini, update_arcade_organizer_ini, update_names_txt_ini, \
    update_jtcores_ini
from test.update_all_service_tester import TransitionServiceTester, local_store
from update_all.config import Config
from update_all.databases import AllDBs


def test_transitions(files: Dict[str, str] = None, config: Config = None):
    config = config or Config()
    fs = FileSystemState(config=config, files=None if files is None else {filename: {'content': Path(path).read_text()} for filename, path in files.items()})
    sut = TransitionServiceTester(file_system=FileSystemFactory(state=fs).create_for_system_scope())
    sut.from_not_existing_downloader_ini(config)
    sut.from_update_all_1(config, local_store())
    sut.from_jtpremium_to_jtcores(config)
    sut.from_mistersam_main_to_db_branch(config)
    return fs


class TestTransitionService(unittest.TestCase):
    def test_on_empty_state___writes_default_downloader_ini(self):
        fs = test_transitions()
        self.assertEqual(Path('test/fixtures/downloader_ini/default_downloader.ini').read_text(), fs.files[downloader_ini]['content'])

    def test_with_dirty_downloader_ini___writes_nothing(self):
        fs = test_transitions(files={downloader_ini: 'test/fixtures/downloader_ini/dirty_downloader.ini'})
        self.assertEqual(Path('test/fixtures/downloader_ini/dirty_downloader.ini').read_text(), fs.files[downloader_ini]['content'])

    def test_with_downloader_ini_and_other_inis___writes_ao_ini_and_keeps_downloader_ini(self):
        fs = test_transitions(files={
            downloader_ini: 'test/fixtures/downloader_ini/default_downloader.ini',
            update_all_ini: 'test/fixtures/update_all_ini/complete_ua_first.ini',
        })
        self.assertEqualFiles({
            downloader_ini: 'test/fixtures/downloader_ini/default_downloader.ini',
            update_arcade_organizer_ini: 'test/fixtures/update_arcade-organizer_ini/complete_ao.ini',
        }, fs.files)

    def test_with_update_all_ini_with_names_and_encc___writes_corresponding_downloader_ini(self):
        fs = test_transitions(files={
            update_all_ini: 'test/fixtures/update_all_ini/complete_ua_first.ini',
            update_names_txt_ini: 'test/fixtures/update_names-txt_ini/complete_nt.ini',
            update_jtcores_ini: 'test/fixtures/update_jtcores_ini/complete_jt.ini',
        })
        self.assertEqualFiles({
            downloader_ini: 'test/fixtures/downloader_ini/complete_downloader_first.ini',
            update_arcade_organizer_ini: 'test/fixtures/update_arcade-organizer_ini/complete_ao.ini'
        }, fs.files)

    def test_with_just_update_all_ini_with_opposite_to_defaults___writes_corresponding_downloader_ini(self):
        fs = test_transitions(files={
            update_all_ini: 'test/fixtures/update_all_ini/complete_ua_second.ini',
        })
        self.assertEqualFiles({
            downloader_ini: 'test/fixtures/downloader_ini/complete_downloader_second.ini',
        }, fs.files)

    def test_with_just_update_jtcores_ini___writes_corresponding_downloader_ini(self):
        fs = test_transitions(files={
            update_jtcores_ini: 'test/fixtures/update_jtcores_ini/complete_jt.ini',
        })
        self.assertEqualFiles({
            downloader_ini: 'test/fixtures/downloader_ini/default_premium_downloader.ini',
        }, fs.files)

    def test_with_just_jtpremium_in_downloader_ini___writes_downloader_ini_with_jtcores_with_mister_inheritance(self):
        just_jtpremium_config = Config(has_jtpremium=True, download_beta_cores=True, databases={AllDBs.JTCORES.db_id})
        fs = test_transitions(config=just_jtpremium_config, files={
            downloader_ini: 'test/fixtures/downloader_ini/just_jtpremium.ini',
        })
        self.assertEqualFiles({
            downloader_ini: 'test/fixtures/downloader_ini/just_jtcores_with_mister_inheritance.ini',
        }, fs.files)

    def test_with_just_jtpremium_with_filter_wtf_in_downloader_ini___writes_downloader_ini_with_jtcores_with_filter_wtf(self):
        just_jtpremium_config = Config(has_jtpremium=True, download_beta_cores=True, databases={AllDBs.JTCORES.db_id})
        fs = test_transitions(config=just_jtpremium_config, files={
            downloader_ini: 'test/fixtures/downloader_ini/just_jtpremium_with_filter_wtf.ini',
        })
        self.assertEqualFiles({
            downloader_ini: 'test/fixtures/downloader_ini/just_jtcores_with_filter_wtf.ini',
        }, fs.files)

    def test_mistersam_on_main_branch___writes_downloader_ini_with_mistersam_on_db_branch(self):
        just_mistersam_with_main_branch_config = Config(has_mistersam_main_branch=True, databases={AllDBs.MISTERSAM_FILES.db_id})
        fs = test_transitions(config=just_mistersam_with_main_branch_config, files={
            downloader_ini: 'test/fixtures/downloader_ini/mistersam_on_main.ini',
        })
        self.assertEqualFiles({
            downloader_ini: 'test/fixtures/downloader_ini/mistersam_on_db.ini',
        }, fs.files)

    def assertEqualFiles(self, expected, actual):
        actual = {filename.lower(): description['content'].strip() for filename, description in actual.items()}
        expected = {filename.lower(): Path(path).read_text().strip() for filename, path in expected.items()}
        self.assertEqual(expected, actual)
