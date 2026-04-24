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
from unittest.mock import patch
from typing import Tuple

from test.fake_filesystem import FileSystemFactory
from test.ui_model_test_utils import gather_used_effects
from test.update_all_service_tester import SettingsScreenTester, UiContextStub, default_databases, local_store
from update_all.config import Config
from update_all.databases import DB_ID_NAMES_TXT, AllDBs, all_dbs
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
        ui.set_value('log_viewer', 'false')

        sut.prepare_exit_dont_save_and_run(ui)

        self.assertEqual(config.arcade_organizer, False)
        self.assertEqual(config.databases, {DB_ID_NAMES_TXT, all_dbs('').UPDATE_ALL_MISTER.db_id})
        self.assertTrue(config.temporary_downloader_ini)
        self.assertFalse(config.log_viewer)

    def test_prepare_exit_dont_save_and_run___restores_pending_unsaved_video_mode(self):
        service = _MisterVideoModeServiceStub()
        sut, ui = tester(mister_video_mode_service=service)

        sut.prepare_exit_dont_save_and_run(ui)

        self.assertEqual(1, service.restore_calls)

    def test_prepare_exit_without_save___restores_pending_unsaved_video_mode(self):
        service = _MisterVideoModeServiceStub()
        sut, _ui = tester(mister_video_mode_service=service)

        sut.prepare_exit_without_save()

        self.assertEqual(1, service.restore_calls)

    def test_calculate_needs_save___includes_mister_video_mode_label_for_unsaved_kept_mode(self):
        sut, ui = tester(mister_video_mode_service=_MisterVideoModeServiceStub(has_unsaved_kept_mode=True, ini_filename='MiSTer_alt.ini'))

        sut.calculate_needs_save(ui)

        self.assertEqual('true', ui.get_value('needs_save'))
        self.assertIn('MiSTer video mode (MiSTer_alt.ini)', ui.get_value('needs_save_file_list'))

    def test_initialize_ui___enables_direct_video_warning_only_when_vga_scaler_is_not_enabled(self):
        _sut, ui = tester(mister_video_mode_service=_MisterVideoModeServiceStub(direct_video=True, vga_scaler=False))

        self.assertEqual('true', ui.get_value('mister_video_direct_video_warning'))

    def test_initialize_ui___disables_direct_video_warning_when_vga_scaler_is_enabled(self):
        _sut, ui = tester(mister_video_mode_service=_MisterVideoModeServiceStub(direct_video=True, vga_scaler=True))

        self.assertEqual('false', ui.get_value('mister_video_direct_video_warning'))

    def test_initialize_ui___keeps_ajgowans_manuals_general_selector_from_store_even_when_all_manuals_dbs_are_enabled(self):
        manuals_db_ids = set(gather_variable_declarations(settings_screen_model(), "manuals"))
        config = Config(databases={*manuals_db_ids, all_dbs('').UPDATE_ALL_MISTER.db_id})
        store = local_store()
        store.set_ajgowans_manuals_dbs_general_selector(False)

        _sut, ui = tester(config=config, store=store)

        self.assertEqual('false', ui.get_value('ajgowans_manuals_dbs_general_selector'))

    def test_initialize_ui___stores_media_fat_available_space_as_raw_bytes(self):
        file_system = FileSystemFactory.from_state(available_space={'/media/fat': 20 * 1024 * 1024 * 1024}).create_for_system_scope()
        sut, ui = tester(file_system=file_system)

        self.assertEqual(str(20 * 1024 * 1024 * 1024), ui.get_value('media_fat_available_space'))

    def test_select_all_ajgowans_manuals_dbs___toggle_all_enables_every_manual_db_and_selector(self):
        sut, ui = tester()

        result = sut.select_all_ajgowans_manuals_dbs(ui, {'action': 'toggle'})

        self.assertEqual('clear_window', result)
        self.assertEqual('true', ui.get_value('ajgowans_manuals_dbs_general_selector'))
        for variable in gather_variable_declarations(settings_screen_model(), "manuals"):
            self.assertEqual('true', ui.get_value(variable))

    def test_select_all_ajgowans_manuals_dbs___toggle_with_selector_true_and_all_active_disables_every_manual_db_and_selector(self):
        manuals_db_ids = set(gather_variable_declarations(settings_screen_model(), "manuals"))
        config = Config(databases={*manuals_db_ids, all_dbs('').UPDATE_ALL_MISTER.db_id})
        store = local_store()
        store.set_ajgowans_manuals_dbs_general_selector(True)
        sut, ui = tester(config=config, store=store)

        result = sut.select_all_ajgowans_manuals_dbs(ui, {'action': 'toggle'})

        self.assertEqual('clear_window', result)
        self.assertEqual('false', ui.get_value('ajgowans_manuals_dbs_general_selector'))
        for variable in gather_variable_declarations(settings_screen_model(), "manuals"):
            self.assertEqual('false', ui.get_value(variable))

    def test_select_all_ajgowans_manuals_dbs___toggle_with_selector_true_and_any_inactive_only_unapplies_selector(self):
        manuals_db_ids = set(gather_variable_declarations(settings_screen_model(), "manuals"))
        config = Config(databases={*manuals_db_ids, all_dbs('').UPDATE_ALL_MISTER.db_id})
        store = local_store()
        store.set_ajgowans_manuals_dbs_general_selector(True)
        sut, ui = tester(config=config, store=store)
        ui.set_value('ajgowans/manualsdb-3do', 'false')

        result = sut.select_all_ajgowans_manuals_dbs(ui, {'action': 'toggle'})

        self.assertEqual('clear_window', result)
        self.assertEqual('false', ui.get_value('ajgowans_manuals_dbs_general_selector'))
        self.assertEqual('false', ui.get_value('ajgowans/manualsdb-3do'))
        for variable in gather_variable_declarations(settings_screen_model(), "manuals"):
            if variable == 'ajgowans/manualsdb-3do':
                continue
            self.assertEqual('true', ui.get_value(variable))

    def test_select_all_ajgowans_manuals_dbs___unapply_only_unapplies_selector(self):
        store = local_store()
        store.set_ajgowans_manuals_dbs_general_selector(True)
        sut, ui = tester(store=store)
        ui.set_value('ajgowans/manualsdb-3do', 'true')

        result = sut.select_all_ajgowans_manuals_dbs(ui, {'action': 'unapply'})

        self.assertEqual('clear_window', result)
        self.assertEqual('false', ui.get_value('ajgowans_manuals_dbs_general_selector'))
        self.assertEqual('true', ui.get_value('ajgowans/manualsdb-3do'))

    def test_load_menu_entry___restores_pending_unsaved_video_mode_when_ui_engine_raises(self):
        service = _MisterVideoModeServiceStub()
        sut, _ui = tester(mister_video_mode_service=service, initialize_ui=False, ui_runtime=_ImmediateUiRuntimeStub())

        with self.assertRaisesRegex(RuntimeError, 'boom'):
            with patch('update_all.settings_screen.execute_ui_engine', side_effect=RuntimeError('boom')):
                sut._load_menu_entry('main_menu_login')

        self.assertEqual(1, service.restore_calls)


def tester(config: Config = None, store: LocalStore = None, mister_video_mode_service=None, initialize_ui=True, ui_runtime=None, file_system=None) -> Tuple[SettingsScreen, UiContextStub]:
    ui = UiContextStub()
    config_provider = GenericProvider[Config]()
    config_provider.initialize(config or Config(databases=default_databases()))
    store_provider = GenericProvider[LocalStore]()
    store_provider.initialize(store or local_store())
    settings_screen = SettingsScreenTester(
        config_provider=config_provider,
        store_provider=store_provider,
        mister_video_mode_service=mister_video_mode_service,
        ui_runtime=ui_runtime,
        file_system=file_system,
    )
    if initialize_ui:
        settings_screen.initialize_ui(ui)
    return settings_screen, ui


class _MisterVideoModeServiceStub:
    def __init__(self, has_unsaved_kept_mode=False, ini_filename=None, direct_video=False, vga_scaler=False):
        self.restore_calls = 0
        self._has_unsaved_kept_mode = has_unsaved_kept_mode
        self._ini_filename = ini_filename
        self._direct_video = direct_video
        self._vga_scaler = vga_scaler

    def restore_mode_before_unsaved_keeps(self):
        self.restore_calls += 1
        return True

    def has_unsaved_kept_mode(self):
        return self._has_unsaved_kept_mode

    def unsaved_kept_mode_filename(self):
        return self._ini_filename

    def current_direct_video(self):
        return self._direct_video

    def current_vga_scaler(self):
        return self._vga_scaler


class _ImmediateUiRuntimeStub:
    def initialize_runtime(self, cb):
        cb()

    def update(self) -> None:
        pass

    def interrupt(self) -> None:
        pass

    def resume(self) -> None:
        pass
