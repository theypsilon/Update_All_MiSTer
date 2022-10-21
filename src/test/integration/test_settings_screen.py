# Copyright (c) 2022 José Manuel Barroso Galindo <theypsilon@gmail.com>

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
from typing import Tuple
from unittest.mock import MagicMock

from test.file_system_tester_state import FileSystemState
from test.testing_objects import downloader_ini, update_arcade_organizer_ini, default_downloader_ini_content, \
    store_json_zip
from test.ui_model_test_utils import gather_used_effects
from test.update_all_service_tester import SettingsScreenTester, UiStub, default_databases, local_store
from update_all.config import Config
from update_all.ini_repository import read_ini_contents
from update_all.local_store import LocalStore
from update_all.other import GenericProvider
from test.fake_filesystem import FileSystemFactory
from update_all.databases import AllDBs, DB_ID_NAMES_TXT, db_ids_to_model_variable_pairs
from update_all.settings_screen import SettingsScreen
from update_all.settings_screen_model import settings_screen_model
from update_all.ui_model_utilities import gather_variable_declarations


class TestSettingsScreen(unittest.TestCase):

    def test_calculate_needs_save___on_no_files_setup___returns_downloader_ini_changes(self) -> None:
        sut, ui, _ = tester()
        sut.calculate_needs_save(ui)
        self.assertEqual('  - downloader.ini', ui.get_value('needs_save_file_list'))
        self.assertEqual('true', ui.get_value('needs_save'))

    def test_save___on_no_files_setup___creates_default_downloader_ini(self) -> None:
        sut, ui, fs = tester()
        sut.calculate_needs_save(ui)
        sut.save(ui)
        self.assertEqual(default_downloader_ini_content(), fs.files[downloader_ini]['content'])

    def test_calculate_needs_save___with_default_downloader_ini_and_disabled_names_txt_updater___returns_downloader_ini_changes(self) -> None:
        sut, ui, _ = tester(files={downloader_ini: {'content': default_downloader_ini_content()}})
        ui.set_value('names_txt_updater', 'true')
        sut.calculate_needs_save(ui)
        self.assertEqual('  - downloader.ini', ui.get_value('needs_save_file_list'))
        self.assertEqual('true', ui.get_value('needs_save'))

    def test_calculate_needs_save___with_default_downloader_ini___returns_no_changes(self) -> None:
        sut, ui, _ = tester(files={downloader_ini: {'content': default_downloader_ini_content()}})
        sut.calculate_needs_save(ui)
        self.assertEqual('', ui.get_value('needs_save_file_list'))
        self.assertEqual('false', ui.get_value('needs_save'))

    def test_calculate_needs_save___with_bug_names_txt_updater_disabled_downloader_and_matching_options___returns_no_changes(self):
        config = Config(download_beta_cores=True, databases=default_databases(sub=[DB_ID_NAMES_TXT], add=[AllDBs.BIOS.db_id, AllDBs.THEYPSILON_UNOFFICIAL_DISTRIBUTION.db_id, AllDBs.LLAPI_FOLDER.db_id, AllDBs.ARCADE_ROMS.db_id, AllDBs.ARCADE_OFFSET_FOLDER.db_id, AllDBs.TTY2OLED_FILES.db_id, AllDBs.I2C2OLED_FILES.db_id, AllDBs.MISTERSAM_FILES.db_id]))
        sut, ui, _ = tester(files={
            downloader_ini: {'content': Path('test/fixtures/downloader_ini/bug_names_txt_updater_disabled_downloader.ini').read_text()}
        }, config=config)
        sut.calculate_needs_save(ui)
        self.assertEqual('', ui.get_value('needs_save_file_list'))
        self.assertEqual('false', ui.get_value('needs_save'))

    def test_calculate_needs_save___with_arcade_organized_toggled___returns_arcade_organizer_ini_changes(self):
        sut, ui, _ = tester(files={downloader_ini: {'content': default_downloader_ini_content()}})
        ui.set_value('arcade_organizer', str(not Config().arcade_organizer).lower())
        sut.calculate_needs_save(ui)
        self.assertEqual('  - update_arcade-organizer.ini', ui.get_value('needs_save_file_list'))
        self.assertEqual('true', ui.get_value('needs_save'))

    def test_calculate_needs_save___with_ao_region_disabled_and_names_txt_disabled___returns_downloader_and_arcade_organizer_ini_changes(self):
        sut, ui, _ = tester(files={downloader_ini: {'content': default_downloader_ini_content()}})
        ui.set_value('arcade_organizer_region_dir', 'false')
        ui.set_value('names_txt_updater', 'true')
        sut.calculate_needs_save(ui)
        self.assertEqual('  - downloader.ini\n  - update_arcade-organizer.ini', ui.get_value('needs_save_file_list'))
        self.assertEqual('true', ui.get_value('needs_save'))

    def test_initialize_ui___fills_variables_that_are_declared_in_the_model(self):
        _, ui, _ = tester()

        declared_variables = set(gather_variable_declarations(settings_screen_model()))
        initialized_variables = set(ui.variables.keys())

        intersection = declared_variables & initialized_variables

        self.assertGreaterEqual(len(intersection), 5)
        self.assertSetEqual(intersection, initialized_variables)

    def test_initialize_ui___fills_effects_that_are_used_in_the_model(self):
        _, ui, _ = tester()

        used_effects = set(gather_used_effects(settings_screen_model()))
        initialized_effects = set(ui.effects.keys())

        self.assertGreaterEqual(len(initialized_effects), 5)
        self.assertEqual(used_effects, initialized_effects)

    def test_calculate_needs_save___on_complete_ao_with_arcade_organizer_changes___returns_arcade_organizer_changes(self):
        sut, ui, fs = tester(files={
            update_arcade_organizer_ini: {'content': Path('test/fixtures/update_arcade-organizer_ini/complete_ao.ini').read_text()}
        })

        ui.set_value('arcade_organizer', 'true')
        ui.set_value('arcade_organizer_topdir', 'core')

        sut.calculate_needs_save(ui)

        self.assertIn(Path(update_arcade_organizer_ini).name, ui.get_value('needs_save_file_list'))
        self.assertEqual('true', ui.get_value('needs_save'))

    def test_save___on_complete_ao_with_arcade_organizer_changes_but_deactivated___writes_expected_arcade_organizer_ini(self):
        sut, ui, fs = tester(files={
            update_arcade_organizer_ini: {'content': Path('test/fixtures/update_arcade-organizer_ini/complete_ao.ini').read_text()}
        }, config=Config(arcade_organizer=False))

        ui.set_value('arcade_organizer_topdir', 'core')

        sut.calculate_needs_save(ui)
        sut.save(ui)

        self.assertEqual(Path('test/fixtures/update_arcade-organizer_ini/disabled_topdir_core_ao.ini').read_text(), fs.files[update_arcade_organizer_ini.lower()]['content'])

    def test_save___on_complete_ao_with_arcade_organizer_changes___writes_expected_arcade_organizer_ini(self):
        sut, ui, fs = tester(files={
            update_arcade_organizer_ini: {'content': Path('test/fixtures/update_arcade-organizer_ini/complete_ao.ini').read_text()}
        })

        ui.set_value('arcade_organizer_topdir', 'core')

        sut.calculate_needs_save(ui)
        sut.save(ui)

        self.assertEqual(Path('test/fixtures/update_arcade-organizer_ini/enabled_topdir_core_ao.ini').read_text(), fs.files[update_arcade_organizer_ini.lower()]['content'])

    def test_calculate_needs_save__when_selecting_wizzo_mrext___returns_changes_on_downloader_ini(self):
        sut, ui, _ = tester(files={downloader_ini: {'content': default_downloader_ini_content()}})

        ui.set_value('mrext/all', 'true')

        sut.calculate_needs_save(ui)

        self.assertEqual('  - downloader.ini', ui.get_value('needs_save_file_list'))
        self.assertEqual('true', ui.get_value('needs_save'))

    def test_save___on_default_downloader_ini_with_all_dbs_selected___writes_big_downloader_ini_matching_amount_of_dbs(self):
        sut, ui, fs = tester(files={downloader_ini: {'content': default_downloader_ini_content()}})

        for variable, _ in db_ids_to_model_variable_pairs():
            ui.set_value(variable, 'true')

        sut.calculate_needs_save(ui)
        sut.save(ui)

        ini_sections = len(read_ini_contents(fs.files[downloader_ini.lower()]['content']).sections())
        self.assertEqual(len(db_ids_to_model_variable_pairs()), ini_sections)
        self.assertGreaterEqual(ini_sections, 10)


    def test_save__when_selecting_theme___writes_changes_on_local_store(self):
        sut, ui, fs = tester(files={downloader_ini: {'content': default_downloader_ini_content()}})

        ui.set_value('wait_time_for_reading', '69')
        ui.set_value('ui_theme', 'Cyan Night')

        sut.calculate_needs_save(ui)
        sut.save(ui)

        self.assertEqual(69, fs.files[store_json_zip.lower()]['unzipped_json']['wait_time_for_reading'])
        self.assertEqual('Cyan Night', fs.files[store_json_zip.lower()]['unzipped_json']['theme'])


def tester(files=None, config=None, store=None) -> Tuple[SettingsScreen, UiStub, FileSystemState]:
    ui = UiStub()
    state = FileSystemState(files=files)
    config_provider = GenericProvider[Config]()
    config_provider.initialize(config or Config())
    store_provider = GenericProvider[LocalStore]()
    store_provider.initialize(store or local_store())
    settings_screen = SettingsScreenTester(config_provider=config_provider, store_provider=store_provider, file_system=FileSystemFactory(state=state).create_for_system_scope())
    settings_screen.initialize_ui(ui, screen=MagicMock())

    return settings_screen, ui, state

