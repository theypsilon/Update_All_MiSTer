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
import os
import subprocess
import tempfile
import unittest
import zipfile
from unittest.mock import MagicMock, patch
from typing import Tuple

from test.fake_filesystem import FileSystemFactory
from test.spy_os_utils import SpyOsUtils
from test.ui_model_test_utils import gather_used_effects
from test.update_all_service_tester import SettingsScreenTester, UiContextStub, default_databases, local_store
from update_all.config import Config
from update_all.constants import FILE_MiSTer_ini
from update_all.databases import DB_ID_NAMES_TXT, AllDBs, all_dbs
from update_all.local_store import LocalStore
from update_all.other import GenericProvider
from update_all.retroaccount import BenefitState, ChipIdAttachResult
from update_all.settings_screen import CHIP_ID_DEBUG_LOG_PATH, SettingsScreen
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

    def test_initialize_ui___with_missing_zaparoo_frontend_store_field___defaults_it_to_false(self):
        store = local_store()
        store.unwrap_props().pop('zaparoo_frontend_active', None)

        _, ui = tester(store=store)

        self.assertEqual('false', ui.get_value('zaparoo_frontend_active'))

    def test_initialize_ui___with_zaparoo_frontend_main_in_mister_ini___sets_frontend_active_true(self):
        file_system = FileSystemFactory.from_state(files={
            FILE_MiSTer_ini: {'content': '[mister]\nmain=zaparoo/MiSTer_Zaparoo\n'},
        }).create_for_system_scope()

        _, ui = tester(file_system=file_system)

        self.assertEqual('true', ui.get_value('zaparoo_frontend_active'))

    def test_initialize_ui___with_legacy_pending_zaparoo_store_true___ignores_store_field(self):
        store = local_store()
        store.unwrap_props()['zaparoo_frontend_active'] = True
        store.mark_as_cleaned()

        _, ui = tester(store=store)

        self.assertEqual('false', ui.get_value('zaparoo_frontend_active'))

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

    def test_retroachievements_db_toggle___when_disabled___enables_db_and_sets_service_status(self):
        config = Config(databases=default_databases())
        service = _RetroAchievementsServiceStub(enable_status='missing_credentials')
        sut, ui = tester(config=config, retroachievements_service=service)

        sut.retroachievements_db_toggle(ui)

        self.assertEqual('true', ui.get_value(all_dbs('').RETROACHIEVEMENTS_DB.db_id))
        self.assertEqual('missing_credentials', ui.get_value('retroachievements_cfg_status'))
        self.assertEqual(1, service.prepare_enable_calls)
        self.assertEqual(0, service.disable_calls)
        self.assertEqual([], service.set_mister_ini_active_calls)

    def test_retroachievements_db_toggle___when_enabled___disables_db(self):
        retroachievements_db_id = all_dbs('').RETROACHIEVEMENTS_DB.db_id
        config = Config(databases=default_databases(add=[retroachievements_db_id]))
        service = _RetroAchievementsServiceStub(enable_status='ok')
        sut, ui = tester(config=config, retroachievements_service=service)

        sut.retroachievements_db_toggle(ui)

        self.assertEqual('false', ui.get_value(retroachievements_db_id))
        self.assertEqual('ok', ui.get_value('retroachievements_cfg_status'))
        self.assertEqual(0, service.prepare_enable_calls)
        self.assertEqual(0, service.disable_calls)
        self.assertEqual([], service.set_mister_ini_active_calls)

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

    def test_extract_chip_id___when_not_mister___stores_failure_and_does_not_start_extraction(self):
        sut, ui = tester(config=Config(databases=default_databases(), not_mister=True))
        sut._queue_detached_chip_id_extraction = MagicMock()
        sut._run_chip_id_extraction_without_update_all_relaunch = MagicMock()

        result = sut.extract_chip_id(ui)

        self.assertEqual('clear_window', result)
        self.assertEqual('FAILURE_NOT_MISTER', ui.get_value('retroaccount_extract_chip_id_result'))
        sut._queue_detached_chip_id_extraction.assert_not_called()
        sut._run_chip_id_extraction_without_update_all_relaunch.assert_not_called()

    def test_extract_chip_id___when_linker_pyz_is_missing___asks_for_full_update_and_does_not_start_extraction(self):
        config = Config(databases=default_databases())
        file_system = chip_id_linker_file_system(config, pyz=False)
        sut, ui = tester(config=config, file_system=file_system)
        sut._run_chip_id_extraction_without_update_all_relaunch = MagicMock()

        with patch('update_all.settings_screen.is_mister_scripts_menu_fb_launch') as is_menu_launch:
            result = sut.extract_chip_id(ui)

        self.assertEqual('clear_window', result)
        self.assertEqual('FAILURE_LINKER_PYZ_MISSING', ui.get_value('retroaccount_extract_chip_id_result'))
        self.assertEqual('Full update required', ui.get_value('retroaccount_device_verification_description'))
        self.assertEqual(
            'Run a full Update All before linking FPGA ID.',
            ui.get_value('retroaccount_device_verification_message')
        )
        self.assertEqual('', ui.get_value('retroaccount_verified_chip_id_message'))
        is_menu_launch.assert_not_called()
        sut._run_chip_id_extraction_without_update_all_relaunch.assert_not_called()

    def test_extract_chip_id___when_rbf_is_missing___asks_for_full_update_and_does_not_start_extraction(self):
        config = Config(databases=default_databases())
        file_system = chip_id_linker_file_system(config, rbf=False)
        sut, ui = tester(config=config, file_system=file_system)
        sut._run_chip_id_extraction_without_update_all_relaunch = MagicMock()

        with patch('update_all.settings_screen.is_mister_scripts_menu_fb_launch') as is_menu_launch:
            result = sut.extract_chip_id(ui)

        self.assertEqual('clear_window', result)
        self.assertEqual('FAILURE_RBF_MISSING', ui.get_value('retroaccount_extract_chip_id_result'))
        self.assertEqual('Full update required', ui.get_value('retroaccount_device_verification_description'))
        self.assertEqual(
            'Run a full Update All before linking FPGA ID.',
            ui.get_value('retroaccount_device_verification_message')
        )
        self.assertEqual('', ui.get_value('retroaccount_verified_chip_id_message'))
        is_menu_launch.assert_not_called()
        sut._run_chip_id_extraction_without_update_all_relaunch.assert_not_called()

    def test_extract_chip_id___when_not_scripts_menu_framebuffer_launch___runs_extraction_without_relaunch_and_attaches(self):
        retroaccount = _RetroAccountStub()
        config = Config(databases=default_databases())
        sut, ui = tester(config=config, file_system=chip_id_linker_file_system(config), retroaccount=retroaccount)
        sut._run_chip_id_extraction_without_update_all_relaunch = MagicMock(return_value='0123456789abcdef')

        with patch('update_all.settings_screen.is_mister_scripts_menu_fb_launch', return_value=False):
            result = sut.extract_chip_id(ui)

        self.assertEqual('clear_window', result)
        self.assertEqual('0123456789abcdef', ui.get_value('retroaccount_extract_chip_id_result'))
        self.assertEqual('0123456789abcdef', config.chip_id_result)
        self.assertEqual(['0123456789abcdef'], retroaccount.attach_calls)
        self.assertEqual(1, retroaccount.mister_sync_calls)
        self.assertEqual('true', ui.get_value('retroaccount_device_verified'))
        self.assertEqual('Linking successful!', ui.get_value('retroaccount_device_verification_message'))
        self.assertEqual('FPGA ID: 0123456789abcdef', ui.get_value('retroaccount_verified_chip_id_message'))

    def test_extract_chip_id___when_not_scripts_menu_framebuffer_launch_and_extraction_fails___does_not_attach(self):
        retroaccount = _RetroAccountStub()
        config = Config(databases=default_databases())
        sut, ui = tester(config=config, file_system=chip_id_linker_file_system(config), retroaccount=retroaccount)
        sut._run_chip_id_extraction_without_update_all_relaunch = MagicMock(return_value='FAILURE_LOAD_CORE_FIFO')

        with patch('update_all.settings_screen.is_mister_scripts_menu_fb_launch', return_value=False):
            result = sut.extract_chip_id(ui)

        self.assertEqual('clear_window', result)
        self.assertEqual('FAILURE_LOAD_CORE_FIFO', ui.get_value('retroaccount_extract_chip_id_result'))
        self.assertEqual([], retroaccount.attach_calls)
        self.assertEqual(0, retroaccount.mister_sync_calls)

    def test_extract_chip_id___when_mister___queues_detached_worker_and_exits_immediately(self):
        config = Config(databases=default_databases())
        sut, ui = tester(config=config, file_system=chip_id_linker_file_system(config))
        sut._queue_detached_chip_id_extraction = MagicMock(return_value='EXTRACTION_STARTED')

        with patch('update_all.settings_screen.is_mister_scripts_menu_fb_launch', return_value=True):
            with self.assertRaises(SystemExit) as e:
                sut.extract_chip_id(ui)

        self.assertEqual(0, e.exception.code)
        self.assertEqual('EXTRACTION_STARTED', ui.get_value('retroaccount_extract_chip_id_result'))
        sut._queue_detached_chip_id_extraction.assert_called_once_with()

    def test_initialize_ui___loads_chip_id_result_from_config_for_retroaccount_menu(self):
        _sut, ui = tester(config=Config(databases=default_databases(), chip_id_result='0123456789abcdef'))

        self.assertEqual('FPGA ID link pending', ui.get_value('retroaccount_device_verification_description'))

    def test_initialize_ui___loads_verified_device_state_for_retroaccount_menu(self):
        retroaccount = _RetroAccountStub(device_verified=True)

        _sut, ui = tester(retroaccount=retroaccount)

        self.assertEqual('true', ui.get_value('retroaccount_device_verified'))
        self.assertEqual('FPGA ID linked: 0123456789abcdef', ui.get_value('retroaccount_device_verification_description'))
        self.assertEqual('FPGA ID: 0123456789abcdef', ui.get_value('retroaccount_verified_chip_id_message'))

    def test_initialize_ui___loads_device_label_and_account_description_formatters(self):
        retroaccount = _RetroAccountStub(device_label='MiSTer Living Room Cabinet')

        _sut, ui = tester(retroaccount=retroaccount)

        self.assertEqual('MiSTer Living Room Cabinet', ui.get_value('device_label'))
        self.assertEqual(
            'Device label: MiSTer Living Room Cabinet',
            ui.formatters['device_label_message']('MiSTer Living Room Cabinet')
        )
        self.assertEqual('Device label: Not available', ui.formatters['device_label_message'](''))

    def test_retroaccount_check_state___refreshes_device_verification_state(self):
        retroaccount = _RetroAccountStub(device_verified=True)
        sut, ui = tester(config=Config(databases=default_databases(), chip_id_result='0123456789abcdef'), retroaccount=retroaccount)
        retroaccount._device_verified = False
        ui.set_value('retroaccount_update_all_extras', 'Checking...')
        ui.set_value('retroaccount_jtbeta_access', 'Checking...')
        ui.set_value('retroaccount_checking', '')

        result = sut.retroaccount_check_state(ui)

        self.assertEqual('clear_window', result)
        self.assertEqual('false', ui.get_value('retroaccount_device_verified'))
        self.assertEqual('FPGA ID link pending', ui.get_value('retroaccount_device_verification_description'))

    def test_retroaccount_check_state___refreshes_device_label(self):
        retroaccount = _RetroAccountStub()
        sut, ui = tester(retroaccount=retroaccount)
        retroaccount._device_label = 'MiSTer Living Room'
        ui.set_value('retroaccount_update_all_extras', 'Checking...')
        ui.set_value('retroaccount_jtbeta_access', 'Checking...')
        ui.set_value('retroaccount_checking', '')

        result = sut.retroaccount_check_state(ui)

        self.assertEqual('clear_window', result)
        self.assertEqual('MiSTer Living Room', ui.get_value('device_label'))

    def test_start_detached_chip_id_extraction___starts_linker_command_with_resolved_paths(self):
        with tempfile.TemporaryDirectory() as base_path:
            config = Config(base_path=base_path, base_system_path=base_path, databases=default_databases())
            file_system = FileSystemFactory.from_state(config=config, files={
                'Scripts/.config/update_all/update_all.pyz': {'content': 'pyz'},
                'Scripts/.config/update_all/Linker.rbf': {'content': 'rbf'},
            }).create_for_system_scope()
            sut, _ui = tester(config=config, file_system=file_system)
            process = MagicMock()
            process.pid = 456
            pyz_path = f'{base_path}/scripts/.config/update_all/update_all.pyz'
            rbf_path = f'{base_path}/scripts/.config/update_all/linker.rbf'
            update_all_dir = f'{base_path}/scripts'

            with patch('update_all.settings_screen.sys.executable', '/usr/bin/python3'), \
                    patch('update_all.settings_screen.subprocess.Popen', return_value=process) as popen:
                result = _start_detached_chip_id_extraction(sut)

            self.assertEqual('EXTRACTION_STARTED', result)
            popen.assert_called_once_with(
                [
                    '/usr/bin/python3',
                    pyz_path,
                    '--chip-id-linker',
                    '--rbf',
                    rbf_path,
                    '--update-all-dir',
                    update_all_dir,
                    '--log',
                    CHIP_ID_DEBUG_LOG_PATH,
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
            )

    def test_start_detached_chip_id_extraction___uses_current_update_all_archive_even_without_pyz_extension(self):
        with tempfile.TemporaryDirectory() as base_path:
            config = Config(base_path=base_path, base_system_path=base_path, databases=default_databases())
            file_system = FileSystemFactory.from_state(config=config, files={
                'Scripts/.config/update_all/update_all.pyz': {'content': 'stale cached pyz'},
                'Scripts/.config/update_all/Linker.rbf': {'content': 'rbf'},
            }).create_for_system_scope()
            sut, _ui = tester(config=config, file_system=file_system)
            process = MagicMock()
            process.pid = 456
            current_archive_path = _temp_zipapp_with_suffix('.sh')
            rbf_path = f'{base_path}/scripts/.config/update_all/linker.rbf'
            update_all_dir = f'{base_path}/scripts'

            with patch('update_all.settings_screen.sys.argv', [current_archive_path]), \
                    patch('update_all.settings_screen.sys.executable', '/usr/bin/python3'), \
                    patch('update_all.settings_screen.subprocess.Popen', return_value=process) as popen:
                result = _start_detached_chip_id_extraction(sut)

            self.assertEqual('EXTRACTION_STARTED', result)
            popen.assert_called_once_with(
                [
                    '/usr/bin/python3',
                    current_archive_path,
                    '--chip-id-linker',
                    '--rbf',
                    rbf_path,
                    '--update-all-dir',
                    update_all_dir,
                    '--log',
                    CHIP_ID_DEBUG_LOG_PATH,
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
            )
            _remove(current_archive_path)

    def test_start_detached_chip_id_extraction___when_linker_pyz_is_missing___stores_failure(self):
        with tempfile.TemporaryDirectory() as base_path:
            config = Config(base_path=base_path, base_system_path=base_path, databases=default_databases())
            file_system = FileSystemFactory.from_state(config=config, files={
                'Scripts/.config/update_all/Linker.rbf': {'content': 'rbf'},
            }).create_for_system_scope()
            sut, _ui = tester(config=config, file_system=file_system)

            with patch('update_all.settings_screen.subprocess.Popen') as popen:
                result = _start_detached_chip_id_extraction(sut)

            self.assertEqual('FAILURE_LINKER_PYZ_MISSING', result)
            popen.assert_not_called()

    def test_start_detached_chip_id_extraction___when_rbf_is_missing___stores_failure(self):
        with tempfile.TemporaryDirectory() as base_path:
            config = Config(base_path=base_path, base_system_path=base_path, databases=default_databases())
            file_system = FileSystemFactory.from_state(config=config, files={
                'Scripts/.config/update_all/update_all.pyz': {'content': 'pyz'},
            }).create_for_system_scope()
            sut, _ui = tester(config=config, file_system=file_system)

            with patch('update_all.settings_screen.subprocess.Popen') as popen:
                result = _start_detached_chip_id_extraction(sut)

            self.assertEqual('FAILURE_RBF_MISSING', result)
            popen.assert_not_called()

    def test_run_chip_id_extraction_without_update_all_relaunch___calls_linker_extract_only_and_returns_stdout(self):
        with tempfile.TemporaryDirectory() as base_path:
            config = Config(base_path=base_path, base_system_path=base_path, databases=default_databases())
            file_system = FileSystemFactory.from_state(config=config, files={
                'Scripts/.config/update_all/update_all.pyz': {'content': 'pyz'},
                'Scripts/.config/update_all/Linker.rbf': {'content': 'rbf'},
            }).create_for_system_scope()
            sut, _ui = tester(config=config, file_system=file_system)
            process = subprocess.CompletedProcess([], 0, stdout='0123456789abcdef\n', stderr='')
            pyz_path = f'{base_path}/scripts/.config/update_all/update_all.pyz'
            rbf_path = f'{base_path}/scripts/.config/update_all/linker.rbf'

            with patch('update_all.settings_screen.sys.executable', '/usr/bin/python3'), \
                    patch('update_all.settings_screen.subprocess.run', return_value=process) as run:
                result = sut._run_chip_id_extraction_without_update_all_relaunch()

            self.assertEqual('0123456789abcdef', result)
            run.assert_called_once_with(
                [
                    '/usr/bin/python3',
                    pyz_path,
                    '--chip-id-linker',
                    '--extract-only',
                    '--rbf',
                    rbf_path,
                    '--log',
                    CHIP_ID_DEBUG_LOG_PATH,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

    def test_load_menu_entry___restores_pending_unsaved_video_mode_when_ui_engine_raises(self):
        service = _MisterVideoModeServiceStub()
        sut, _ui = tester(mister_video_mode_service=service, initialize_ui=False, ui_runtime=_ImmediateUiRuntimeStub())

        with self.assertRaisesRegex(RuntimeError, 'boom'):
            with patch('update_all.settings_screen.execute_ui_engine', side_effect=RuntimeError('boom')):
                sut._load_menu_entry('main_menu_login')

        self.assertEqual(1, service.restore_calls)

    def test_load_chip_id_result_menu___starts_link_result_with_retroaccount_menu_history(self):
        sut, _ui = tester(initialize_ui=False, ui_runtime=_ImmediateUiRuntimeStub())

        with patch('update_all.settings_screen.execute_ui_engine') as execute:
            sut.load_chip_id_result_menu()

        execute.assert_called_once()
        self.assertEqual('retroaccount_device_verification_result', execute.call_args[0][0])
        self.assertEqual(['main_menu_account', 'retroaccount_account_menu'], execute.call_args.kwargs['initial_history'])

    def test_retroaccount_attach_chip_id_to_device___when_attach_succeeds___shows_completion(self):
        config = Config(databases=default_databases(), chip_id_result='0123456789abcdef')
        retroaccount = _RetroAccountStub(attach_result=True)
        sut, ui = tester(config=config, retroaccount=retroaccount, initialize_ui=False)

        result = sut.retroaccount_attach_chip_id_to_device(ui)

        self.assertEqual('clear_window', result)
        self.assertEqual(['0123456789abcdef'], retroaccount.attach_calls)
        self.assertEqual(1, retroaccount.mister_sync_calls)
        self.assertEqual('true', ui.get_value('retroaccount_device_verified'))
        self.assertEqual('FPGA ID linked: 0123456789abcdef', ui.get_value('retroaccount_device_verification_description'))
        self.assertEqual('Linking successful!', ui.get_value('retroaccount_device_verification_message'))
        self.assertEqual('FPGA ID: 0123456789abcdef', ui.get_value('retroaccount_verified_chip_id_message'))

    def test_retroaccount_attach_chip_id_to_device___when_attach_fails___shows_failure(self):
        config = Config(databases=default_databases(), chip_id_result='0123456789abcdef')
        retroaccount = _RetroAccountStub(attach_result=False, attach_status_code=409)
        sut, ui = tester(config=config, retroaccount=retroaccount, initialize_ui=False)

        result = sut.retroaccount_attach_chip_id_to_device(ui)

        self.assertEqual('clear_window', result)
        self.assertEqual(['0123456789abcdef'], retroaccount.attach_calls)
        self.assertEqual(1, retroaccount.mister_sync_calls)
        self.assertEqual('false', ui.get_value('retroaccount_device_verified'))
        self.assertEqual('FPGA ID linking failed', ui.get_value('retroaccount_device_verification_description'))
        self.assertEqual('Could not link FPGA ID. Try again later.', ui.get_value('retroaccount_device_verification_message'))

    def test_retroaccount_attach_chip_id_to_device___when_result_is_not_chip_id___does_not_call_endpoint(self):
        config = Config(databases=default_databases(), chip_id_result='FAILURE_MEM_SIGBUS')
        retroaccount = _RetroAccountStub(attach_result=True)
        sut, ui = tester(config=config, retroaccount=retroaccount, initialize_ui=False)

        result = sut.retroaccount_attach_chip_id_to_device(ui)

        self.assertEqual('clear_window', result)
        self.assertEqual([], retroaccount.attach_calls)
        self.assertEqual(0, retroaccount.mister_sync_calls)
        self.assertEqual('Could not link FPGA ID. Try again later.', ui.get_value('retroaccount_device_verification_message'))

    def test_retroaccount_device_logout___clears_live_device_verification_state(self):
        config = Config(databases=default_databases(), chip_id_result='0123456789abcdef')
        retroaccount = _RetroAccountStub(device_verified=True)
        sut, ui = tester(config=config, retroaccount=retroaccount)

        result = sut.retroaccount_device_logout(ui)

        self.assertEqual('clear_window', result)
        self.assertEqual(1, retroaccount.logout_calls)
        self.assertEqual('', config.chip_id_result)
        self.assertEqual('false', ui.get_value('retroaccount_device_verified'))
        self.assertEqual('FPGA ID not linked', ui.get_value('retroaccount_device_verification_description'))
        self.assertEqual('', ui.get_value('retroaccount_verified_chip_id_message'))
        self.assertEqual('', ui.get_value('device_label'))

    def test_load_menu_entry___starts_pending_chip_id_extraction_after_curses_exits(self):
        sut, _ui = tester(initialize_ui=False, ui_runtime=_ImmediateUiRuntimeStub())
        sut._pending_chip_id_extraction = ['/usr/bin/python3', '/tmp/update_all_chipid.pyz']

        with patch('update_all.settings_screen.execute_ui_engine', side_effect=SystemExit(0)), \
                patch('update_all.settings_screen.subprocess.Popen') as popen:
            with self.assertRaises(SystemExit):
                sut._load_menu_entry('main_menu_login')

        popen.assert_called_once_with(
            ['/usr/bin/python3', '/tmp/update_all_chipid.pyz'],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )
        self.assertIsNone(sut._pending_chip_id_extraction)


def tester(config: Config = None, store: LocalStore = None, mister_video_mode_service=None, initialize_ui=True, ui_runtime=None, file_system=None, retroaccount=None, os_utils=None, retroachievements_service=None) -> Tuple[SettingsScreen, UiContextStub]:
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
        retroaccount=retroaccount,
        os_utils=os_utils,
        retroachievements_service=retroachievements_service,
    )
    if initialize_ui:
        settings_screen.initialize_ui(ui)
    return settings_screen, ui


class _RetroAchievementsServiceStub:
    def __init__(self, enable_status):
        self._enable_status = enable_status
        self.prepare_enable_calls = 0
        self.disable_calls = 0
        self.set_mister_ini_active_calls = []

    def prepare_enable(self):
        self.prepare_enable_calls += 1
        return self._enable_status

    def disable(self):
        self.disable_calls += 1

    def set_mister_ini_active(self, active):
        self.set_mister_ini_active_calls.append(active)

    def would_change_mister_ini_active(self, active):
        return False


def chip_id_linker_file_system(config: Config, pyz: bool = True, rbf: bool = True):
    files = {}
    if pyz:
        files['Scripts/.config/update_all/update_all.pyz'] = {'content': 'pyz'}
    if rbf:
        files['Scripts/.config/update_all/Linker.rbf'] = {'content': 'rbf'}
    return FileSystemFactory.from_state(config=config, files=files).create_for_system_scope()


def _temp_zipapp_with_suffix(suffix: str) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as file:
        path = file.name
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('__main__.py', '')
    return path


def _remove(*paths: str) -> None:
    for path in paths:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


def _start_detached_chip_id_extraction(sut: SettingsScreen) -> str:
    result = sut._queue_detached_chip_id_extraction()
    if result == 'EXTRACTION_STARTED':
        sut._start_pending_chip_id_extraction_after_ui_shutdown()
    return result


class _MisterVideoModeServiceStub:
    def __init__(self, has_unsaved_kept_mode=False, ini_filename=None, direct_video=False, vga_scaler=False):
        self.restore_calls = 0
        self._has_unsaved_kept_mode = has_unsaved_kept_mode
        self._ini_filename = ini_filename
        self._direct_video = direct_video
        self._vga_scaler = vga_scaler

    def restore_mode_before_unsaved_keeps(self):
        self.restore_calls += 1

    def has_unsaved_kept_mode(self):
        return self._has_unsaved_kept_mode

    def unsaved_kept_mode_filename(self):
        return self._ini_filename

    def current_direct_video(self):
        return self._direct_video

    def current_vga_scaler(self):
        return self._vga_scaler


class _RetroAccountStub:
    def __init__(self, device_verified=False, attach_result=True, device_label=None, attach_status_code=200):
        self._device_verified = device_verified
        self._verified_chip_id = '0123456789abcdef' if device_verified else None
        self._device_label = device_label
        self._attach_result = attach_result
        self._attach_status_code = attach_status_code
        self.attach_calls = []
        self.mister_sync_calls = 0
        self.logout_calls = 0

    def get_login_state(self):
        return True

    def is_update_all_extras_active(self):
        return False

    def is_device_verified(self):
        return self._device_verified

    def get_verified_chip_id(self):
        return self._verified_chip_id

    def get_device_label(self):
        return self._device_label

    def update_all_extras_sync_state(self):
        return BenefitState.CHECKING

    def jtbeta_access_sync_state(self):
        return BenefitState.CHECKING

    def attach_chip_id_to_current_device(self, chip_id):
        self.attach_calls.append(chip_id)
        if self._attach_result:
            self._device_verified = True
            self._verified_chip_id = chip_id.lower()
        return ChipIdAttachResult(self._attach_result, self._attach_status_code)

    def mister_sync(self, output):
        self.mister_sync_calls += 1

    def device_logout(self):
        self.logout_calls += 1
        self._device_verified = False
        self._verified_chip_id = None
        self._device_label = None
        return True


class _ImmediateUiRuntimeStub:
    def initialize_runtime(self, cb):
        cb()

    def update(self) -> None:
        pass

    def interrupt(self) -> None:
        pass

    def resume(self) -> None:
        pass
