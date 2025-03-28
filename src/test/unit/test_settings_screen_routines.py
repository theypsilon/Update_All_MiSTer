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
from typing import Tuple

from test.ui_model_test_utils import gather_used_effects
from test.update_all_service_tester import SettingsScreenTester, UiContextStub, default_databases, local_store
from update_all.config import Config
from update_all.databases import DB_ID_NAMES_TXT, AllDBs
from update_all.local_store import LocalStore
from update_all.other import GenericProvider
from update_all.settings_screen import SettingsScreen
from update_all.settings_screen_model import settings_screen_model
from update_all.ui_model_utilities import gather_variable_declarations


class TestSettingsScreenRoutines(unittest.TestCase):

    def test_initialize_ui___fills_variables_that_are_declared_in_the_model(self):
        _, ui = tester()

        declared_variables = set(gather_variable_declarations(settings_screen_model()))
        initialized_variables = set(ui.variables.keys())

        intersection = declared_variables & initialized_variables

        self.assertGreaterEqual(len(intersection), 5)
        self.assertSetEqual(intersection, initialized_variables)

    def test_initialize_ui___fills_effects_that_are_used_in_the_model(self):
        _, ui = tester()

        used_effects = set(gather_used_effects(settings_screen_model()))
        initialized_effects = set(ui.effects.keys())

        self.assertGreaterEqual(len(initialized_effects), 5)
        self.assertEqual(used_effects, initialized_effects)

    def test_bad_apple___with_no_mister_ini_changes___does_not_crash(self):
        sut, ui = tester()
        sut.play_bad_apple(ui)

    def test_calculate_names_char_code_warning___with_names_char18___returns_names_char_code_warning_equals_true(self):
        sut, ui = tester()
        ui.set_value('names_char_code', 'char18')
        sut.calculate_names_char_code_warning(ui)
        self.assertEqual(ui.get_value('names_char_code_warning'), 'false')

    def test_calculate_names_char_code_warning___with_names_char28___returns_names_char_code_warning_equals_false(self):
        sut, ui = tester()
        ui.set_value('names_char_code', 'char28')
        sut.calculate_names_char_code_warning(ui)
        self.assertEqual(ui.get_value('names_char_code_warning'), 'true')

    def test_prepare_exit_dont_save_and_run___with_temp_values___writes_temp_values_into_config_and_marks_temporary_downloader_ini(self):
        config = Config()
        sut, ui = tester(config=config)
        ui.set_value('arcade_organizer', 'false')
        ui.set_value('names_txt_updater', 'true')

        sut.prepare_exit_dont_save_and_run(ui)

        self.assertEqual(config.arcade_organizer, False)
        self.assertEqual(config.databases, {DB_ID_NAMES_TXT, AllDBs.UPDATE_ALL_MISTER.db_id})
        self.assertTrue(config.temporary_downloader_ini)


def tester(config: Config = None, store: LocalStore = None) -> Tuple[SettingsScreen, UiContextStub]:
    ui = UiContextStub()
    config_provider = GenericProvider[Config]()
    config_provider.initialize(config or Config(databases=default_databases()))
    store_provider = GenericProvider[LocalStore]()
    store_provider.initialize(store or local_store())
    settings_screen = SettingsScreenTester(config_provider=config_provider, store_provider=store_provider)
    settings_screen.initialize_ui(ui)
    return settings_screen, ui
