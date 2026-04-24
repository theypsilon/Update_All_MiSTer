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
import hashlib
from pathlib import Path
from functools import cached_property
from typing import Optional, Final

from update_all.analogue_pocket.firmware_update import pocket_firmware_update
from update_all.analogue_pocket.pocket_backup import pocket_backup
from update_all.arcade_organizer.arcade_organizer import ArcadeOrganizerService
from update_all.config import Config
from update_all.constants import ARCADE_ORGANIZER_INI, FILE_MiSTer, TEST_UNSTABLE_SPINNER_FIRMWARE_MD5, FILE_MiSTer_ini, \
    ARCADE_ORGANIZER_INSTALLED_NAMES_TXT, DEFAULT_SETTINGS_SCREEN_THEME, FILE_downloader_temp_ini, FILE_MiSTer_delme, MEDIA_FAT
from update_all.databases import db_ids_by_model_variables, DB_ID_NAMES_TXT, ALL_DB_IDS
from update_all.ini_repository import SEPARATE_DB_INI_FILES
from update_all.encryption import Encryption
from update_all.ini_repository import IniRepository
from update_all.file_system import FileSystem
from update_all.local_repository import LocalRepository
from update_all.local_store import LocalStore
from update_all.other import GenericProvider, calculate_overscan
from update_all.logger import Logger, CollectorLoggerDecorator
from update_all.mister_video_mode_ui import MisterVideoModeService, MisterVideoModeMenu, MisterVideoAdjustMenu
from update_all.os_utils import OsUtils
from update_all.retroaccount import RetroAccountService, BenefitState
from update_all.settings_screen_model import settings_screen_model
from update_all.settings_screen_printer import SettingsScreenPrinter
from update_all.ui_engine import UiContext, UiApplication, UiSectionFactory, execute_ui_engine, UiRuntime
from update_all.ui_engine_dialog_application import DialogSectionFactory
from update_all.ui_model_utilities import gather_variable_declarations, dynamic_convert_string


class SettingsScreen(UiApplication):
    def __init__(self, logger: Logger, config_provider: GenericProvider[Config], file_system: FileSystem,
                 ini_repository: IniRepository, os_utils: OsUtils, mister_video_mode_service: MisterVideoModeService,
                 settings_screen_printer: SettingsScreenPrinter,
                 local_repository: LocalRepository, store_provider: GenericProvider[LocalStore],
                 ui_runtime: UiRuntime, ao_service: ArcadeOrganizerService, encryption: Encryption,
                 retroaccount: RetroAccountService):
        self._logger = logger
        self._config_provider = config_provider
        self._file_system = file_system
        self._ini_repository = ini_repository
        self._os_utils = os_utils
        self._settings_screen_printer = settings_screen_printer
        self._local_repository = local_repository
        self._store_provider = store_provider
        self._ui_runtime = ui_runtime
        self._ao_service = ao_service
        self._encryption = encryption
        self._retroaccount = retroaccount
        self._mister_video_mode_service = mister_video_mode_service
        self._original_firmware = None
        self._theme_manager = None

    def load_main_menu(self) -> None:
        if self._retroaccount.get_login_state():
            menu = 'main_menu_account'
        else:
            menu = 'main_menu_login'
        self._load_menu_entry(menu)

    def load_test_menu(self) -> None:
        self._load_menu_entry('test_menu')

    def _load_menu_entry(self, menu_entry) -> None:
        def loader():
            model = settings_screen_model()
            try:
                execute_ui_engine(menu_entry, model, self, self._ui_runtime)
            except Exception:
                self._mister_video_mode_service.restore_mode_before_unsaved_keeps()
                raise

        self._ui_runtime.initialize_runtime(loader)

    def initialize_ui(self, ui: UiContext) -> UiSectionFactory:
        ui.set_value('needs_save', 'false')

        arcade_organizer_ini = self._ini_repository.get_arcade_organizer_ini()

        for variable, description in gather_variable_declarations(settings_screen_model(), "ao_ini").items():
            value = arcade_organizer_ini.get_string(description['name'], description['default'])
            for possible_value in description['values']:
                if possible_value.lower() == value.lower():
                    value = possible_value
                    break
            ui.set_value(variable, value)

        db_ids = db_ids_by_model_variables()
        config = self._config_provider.get()
        for variable in self._all_config_variables:
            if hasattr(config, variable):
                value = getattr(config, variable)
                if not isinstance(value, str):
                    value = str(value).lower()
                ui.set_value(variable, value)

        for variable in gather_variable_declarations(settings_screen_model(), "db"):
            ui.set_value(variable, 'true' if db_ids[variable] in config.databases else 'false')

        for variable in gather_variable_declarations(settings_screen_model(), "separate_db"):
            ui.set_value(variable, 'true' if db_ids[variable] in config.databases else 'false')

        local_store = self._store_provider.get()
        ui.set_value('ui_theme', local_store.get_theme())
        mirror = local_store.get_mirror()
        # @TODO (mirror) ui.set_value('mirror', mirror if mirror else config.mirror)
        ui.set_value('countdown_time', str(local_store.get_countdown_time()))
        ui.set_value('log_viewer', str(local_store.get_log_viewer()).lower())
        ui.set_value('use_settings_screen_theme_in_log_viewer', str(local_store.get_use_settings_screen_theme_in_log_viewer()).lower())
        ui.set_value('timeline_after_logs', str(local_store.get_timeline_after_logs()).lower())
        ui.set_value('autoreboot', str(local_store.get_autoreboot()).lower())
        ui.set_value('pocket_firmware_update', str(local_store.get_pocket_firmware_update()).lower())
        ui.set_value('pocket_backup', str(local_store.get_pocket_backup()).lower())
        ui.set_value('retroaccount_domain', config.retroaccount_domain)
        ui.set_value('overscan', local_store.get_overscan())
        ui.set_value('monochrome_ui', str(local_store.get_monochrome_ui()).lower())
        ui.set_value(
            'ajgowans_manuals_dbs_general_selector',
            str(local_store.get_ajgowans_manuals_dbs_general_selector()).lower()
            if local_store.has_field('ajgowans_manuals_dbs_general_selector')
            else 'false'
        )

        if ALL_DB_IDS['JTCORES'] not in config.databases:
            ui.set_value('download_beta_cores', str(local_store.get_download_beta_cores()).lower())

        if DB_ID_NAMES_TXT not in config.databases:
            ui.set_value('names_region', local_store.get_names_region())
            ui.set_value('names_char_code', local_store.get_names_char_code())
            ui.set_value('names_sort_code', local_store.get_names_sort_code())

        ui.set_value(
            'mister_video_direct_video_warning',
            str(self._mister_video_mode_service.current_direct_video() and not self._mister_video_mode_service.current_vga_scaler()).lower()
        )
        ui.set_value('media_fat_available_space', self._read_media_fat_available_space())

        ui.add_custom_formatters({
            'bytes_to_gb': self._format_available_space,
        })

        drawer_factory, theme_manager, device_login_renderer = self._settings_screen_printer.initialize_screen(config)
        if local_store.get_monochrome_ui():
            ui_theme = 'Mono'
        else:
            ui_theme = local_store.get_theme() if self._retroaccount.is_update_all_extras_active() else DEFAULT_SETTINGS_SCREEN_THEME
        theme_manager.set_theme(ui_theme)

        pocket_firmware = self._local_repository.pocket_firmware_info()
        if isinstance(pocket_firmware, dict):
            ui.set_value('pocket_firmware_version', pocket_firmware['version'])

        ui.add_custom_effects({
            'calculate_needs_save': lambda effect: self.calculate_needs_save(ui),
            'calculate_has_right_available_code': lambda effect: self.calculate_has_right_available_code(ui),
            'calculate_is_test_spinner_firmware_applied': lambda effect: self.calculate_is_test_spinner_firmware_applied(ui),
            'test_unstable_spinner_firmware': lambda effect: self.test_unstable_spinner_firmware(ui),
            'save': lambda effect: self.save(ui),
            'prepare_exit_dont_save_and_run': lambda effect: self.prepare_exit_dont_save_and_run(ui),
            'calculate_file_exists': lambda effect: self.calculate_file_exists(ui, effect),
            'remove_file': lambda effect: self.remove_file(ui, effect),
            'calculate_arcade_organizer_folders': lambda effect: self.calculate_arcade_organizer_folders(ui),
            'clean_arcade_organizer_folders': lambda effect: self.clean_arcade_organizer_folders(ui),
            'calculate_names_char_code_warning': lambda effect: self.calculate_names_char_code_warning(ui),
            'calculate_names_txt_file_warning': lambda effect: self.calculate_names_txt_file_warning(ui),
            'disable_monochrome_ui': lambda effect: self.disable_monochrome_ui(ui),
            'apply_theme': lambda effect: self.apply_theme(ui),
            'prepare_exit_without_save': lambda effect: self.prepare_exit_without_save(),
            'pocket_firmware_update': lambda effect: self.pocket_firmware_update(ui),
            'pocket_backup': lambda effect: self.pocket_backup(ui),
            'apply_overscan': lambda effect: self.apply_overscan(ui),
            'select_all_ajgowans_manuals_dbs': lambda effect: self.select_all_ajgowans_manuals_dbs(ui, effect),
            'retroaccount_check_state': lambda effect: self.retroaccount_check_state(ui),
            'retroaccount_device_logout': lambda effect: self.retroaccount_device_logout(ui),
        })

        self._theme_manager = theme_manager

        return DialogSectionFactory(drawer_factory, {
            'device_login': lambda drawer, _interpolator, data: self._retroaccount.create_device_login_ui(drawer, device_login_renderer, data),
            'mister_video_mode': lambda drawer, _interpolator, data: MisterVideoModeMenu(drawer, self._mister_video_mode_service, data),
            'mister_video_adjust': lambda drawer, _interpolator, data: MisterVideoAdjustMenu(drawer, self._mister_video_mode_service, data),
        })

    def calculate_file_exists(self, ui, effect) -> None:
        ui.set_value('file_exists', 'true' if self._file_system.is_file(effect['target']) else 'false')

    def remove_file(self, ui, effect) -> None:
        ui.set_value('file_exists', self._file_system.unlink(effect['target']))

    def calculate_has_right_available_code(self, ui: UiContext) -> None:
        is_test_firmware, firmware_md5 = self._is_test_firmware()
        if firmware_md5 is not None:
            self._original_firmware = firmware_md5

        ui.set_value('has_right_available_code', 'true' if self._retroaccount.is_update_all_extras_active() else 'false')

        self._set_spinner_options(ui)

    def _is_test_firmware(self):
        is_test_firmware, firmware_md5 = False, None
        if self._file_system.is_file(FILE_MiSTer):
            firmware_md5 = hashlib.md5(self._file_system.read_file_binary(FILE_MiSTer)).hexdigest()
            is_test_firmware = firmware_md5 == TEST_UNSTABLE_SPINNER_FIRMWARE_MD5

        return is_test_firmware, firmware_md5

    def calculate_is_test_spinner_firmware_applied(self, ui: UiContext) -> None:
        is_test_firmware, _ = self._is_test_firmware()
        ui.set_value('is_test_spinner_firmware_applied', 'true' if is_test_firmware else 'false')

    def test_unstable_spinner_firmware(self, ui: UiContext) -> None:
        is_test_firmware, firmware_md5 = self._is_test_firmware()
        if is_test_firmware:
            url = "https://raw.githubusercontent.com/MiSTer-devel/Distribution_MiSTer/main/MiSTer"
        else:
            url = "https://raw.githubusercontent.com/theypsilon/Main_MiSTer/test-unstable-taito-spinner-firmware/bin"

        content = self._os_utils.download(url)
        if content is None:
            return None

        self._file_system.write_file_bytes(FILE_MiSTer_delme, content)
        self._file_system.move(FILE_MiSTer_delme, FILE_MiSTer)
        self._set_spinner_options(ui)

    def _set_spinner_options(self, ui: UiContext):
        is_test_firmware, firmware_md5 = self._is_test_firmware()

        ui.set_value('is_test_spinner_firmware_applied', 'true' if is_test_firmware else 'false')
        ui.set_value('firmware_needs_reboot', 'true' if self._original_firmware != firmware_md5 else 'false')

    def calculate_needs_save(self, ui: UiContext) -> None:
        needs_save_file_set = set()

        temp_config = Config()
        self._copy_temp_save_to_config(ui, temp_config)
        if self._ini_repository.does_downloader_ini_need_save(temp_config):
            needs_save_file_set.add("downloader.ini")

        db_ids = db_ids_by_model_variables()
        current_config = self._config_provider.get()
        for variable in gather_variable_declarations(settings_screen_model(), "separate_db"):
            db_id = db_ids[variable]
            was_active = db_id in current_config.databases
            is_active = ui.get_value(variable) == 'true'
            if was_active != is_active:
                ini_filename = SEPARATE_DB_INI_FILES.get(db_id.lower())
                if ini_filename is not None:
                    needs_save_file_set.add(ini_filename)

        arcade_roms_db_id = ALL_DB_IDS['ARCADE_ROMS']
        if arcade_roms_db_id in current_config.databases and ui.get_value('arcade_roms_db_downloader') == 'true':
            if current_config.hbmame_filter != (ui.get_value('hbmame_filter') == 'true'):
                needs_save_file_set.add(SEPARATE_DB_INI_FILES[arcade_roms_db_id.lower()])

        if self._does_arcade_oganizer_need_save(ui):
            needs_save_file_set.add("update_arcade-organizer.ini")

        temp_store = self._store_provider.get().clone()
        self._fill_store(temp_store, ui, temp_config)

        if temp_store.needs_save():
            needs_save_file_set.add(f"Internals ({', '.join(temp_store.changed_fields())})")

        if self._mister_video_mode_service.has_unsaved_kept_mode():
            ini_filename = self._mister_video_mode_service.unsaved_kept_mode_filename() or FILE_MiSTer_ini
            needs_save_file_set.add(f"MiSTer video mode ({ini_filename})")

        if len(needs_save_file_set) > 0:
            needs_save_file_list = "  - " + "\n  - ".join(sorted(needs_save_file_set))
        else:
            needs_save_file_list = ''

        ui.set_value('needs_save', str(len(needs_save_file_set) > 0).lower())
        ui.set_value('needs_save_file_list', needs_save_file_list)

    def save(self, ui: UiContext) -> None:
        self._copy_ui_options_to_current_config(ui)

        config = self._config_provider.get()

        if self._does_arcade_oganizer_need_save(ui):
            new_ao_ini = {}
            for variable, description in gather_variable_declarations(settings_screen_model(), "ao_ini").items():
                value = ui.get_value(variable)

                if value != description['default']:
                    new_ao_ini[description['name']] = value

            self._ini_repository.write_arcade_organizer(new_ao_ini)
        elif config.arcade_organizer != Config().arcade_organizer:
            self._ini_repository.write_arcade_organizer_active_at_arcade_organizer_ini(config)

        self._ini_repository.write_downloader_ini(config)
        self._ini_repository.write_separate_db_ini_files(config)
        self._mister_video_mode_service.save_unsaved_kept_mode_to_active_ini()

        local_store = self._store_provider.get()
        self._fill_store(local_store, ui, config)
        if ALL_DB_IDS['JTCORES'] in config.databases:
            local_store.set_download_beta_cores(config.download_beta_cores)

        if DB_ID_NAMES_TXT in config.databases:
            local_store.set_names_region(config.names_region)
            local_store.set_names_char_code(config.names_char_code)
            local_store.set_names_sort_code(config.names_sort_code)

        if local_store.needs_save():
            self._local_repository.save_store(local_store)
            self._logger.configure(config)

    def _fill_store(self, store: LocalStore, ui: UiContext, config: Config):
        store.set_theme(ui.get_value('ui_theme'))
        store.set_countdown_time(config.countdown_time)
        store.set_log_viewer(config.log_viewer)
        store.set_use_settings_screen_theme_in_log_viewer(config.use_settings_screen_theme_in_log_viewer)
        store.set_timeline_after_logs(config.timeline_after_logs)
        store.set_autoreboot(config.autoreboot)
        store.set_pocket_firmware_update(config.pocket_firmware_update)
        store.set_pocket_backup(config.pocket_backup)
        store.set_overscan(config.overscan)
        store.set_monochrome_ui(config.monochrome_ui)
        store.set_ajgowans_manuals_dbs_general_selector(ui.get_value('ajgowans_manuals_dbs_general_selector') != 'false')
        # @TODO (mirror) store.set_mirror(ui.get_value('mirror'))

    def _does_arcade_oganizer_need_save(self, ui: UiContext):
        arcade_organizer_ini = self._ini_repository.get_arcade_organizer_ini()

        for variable, description in gather_variable_declarations(settings_screen_model(), "ao_ini").items():
            old_value = arcade_organizer_ini.get_string(description['name'], description['default']).lower()
            new_value = ui.get_value(variable).lower()
            if old_value != new_value:
                return True

        return False

    def _copy_ui_options_to_current_config(self, ui: UiContext) -> None:
        self._copy_temp_save_to_config(ui, self._config_provider.get())

    def _copy_temp_save_to_config(self, ui: UiContext, config: Config) -> None:
        db_ids = db_ids_by_model_variables()
        config.databases.clear()
        for variable in self._all_config_variables:
            value = dynamic_convert_string(ui.get_value(variable))
            if variable in db_ids:
                continue
            else:
                if not isinstance(value, type(getattr(config, variable, None))):
                    continue
                setattr(config, variable, value)

        for variable in gather_variable_declarations(settings_screen_model(), "db"):
            if ui.get_value(variable) == 'false':
                continue

            config.databases.add(db_ids[variable])

        for variable in gather_variable_declarations(settings_screen_model(), "separate_db"):
            if ui.get_value(variable) == 'false':
                continue

            config.databases.add(db_ids[variable])

        config.databases.add(ALL_DB_IDS['UPDATE_ALL_MISTER'])

    @cached_property
    def _all_config_variables(self):
        return [
            *gather_variable_declarations(settings_screen_model(), "ua_ini"),
            *gather_variable_declarations(settings_screen_model(), "store"),
            *gather_variable_declarations(settings_screen_model(), "summary"),
            *gather_variable_declarations(settings_screen_model(), "jt_ini"),
            *gather_variable_declarations(settings_screen_model(), "names_ini"),
            *gather_variable_declarations(settings_screen_model(), "arcade_roms"),
            *gather_variable_declarations(settings_screen_model(), "rannysnice_wallpapers"),
            *gather_variable_declarations(settings_screen_model(), "pocket"),
        ]

    @cached_property
    def _ajgowans_manuals_db_variables(self):
        return list(gather_variable_declarations(settings_screen_model(), "manuals"))

    def calculate_names_char_code_warning(self, ui: UiContext) -> None:

        names_char_code = ui.get_value('names_char_code').lower()

        mister_ini = self._read_mister_ini()

        has_date_code_1 = False
        if 'rbf_hide_datecode=1' in mister_ini:
            has_date_code_1 = True

        ui.set_value('names_char_code_warning', 'true' if names_char_code == 'char28' and not has_date_code_1 else 'false')

    def calculate_names_txt_file_warning(self, ui: UiContext):
        if not self._file_system.is_file('names.txt'):
            ui.set_value('names_txt_file_warning', 'false')
            return

        installed_present = self._file_system.is_file(ARCADE_ORGANIZER_INSTALLED_NAMES_TXT)
        ui.set_value('names_txt_file_warning', 'false' if installed_present else 'true')

    def _read_mister_ini(self):
        if self._file_system.is_file(FILE_MiSTer_ini):
            return self._file_system.read_file_contents(FILE_MiSTer_ini).replace(" ", "")
        else:
            return ''

    def calculate_arcade_organizer_folders(self, ui: UiContext) -> None:
        config = self._config_provider.get()
        ao_config = self._ao_service.make_arcade_organizer_config(f'{config.base_path}/{ARCADE_ORGANIZER_INI}', config.base_path, config.http_proxy)
        folders, success = self._ao_service.run_arcade_organizer_print_orgdir_folders(ao_config)

        ui.set_value('has_arcade_organizer_folders', 'true' if success and len(folders) > 0 else 'false')
        ui.set_value('arcade_organizer_folders_list', '\n'.join(folders) if success else '')

    def clean_arcade_organizer_folders(self, ui: UiContext) -> None:
        for line in ui.get_value('arcade_organizer_folders_list').splitlines():
            self._file_system.remove_non_empty_folder(line.strip())

        ui.set_value('has_arcade_organizer_folders', 'false')
        ui.set_value('arcade_organizer_folders_list', '')

    def disable_monochrome_ui(self, ui: UiContext):
        if ui.get_value('monochrome_ui') == 'true':
            ui.set_value('monochrome_ui', 'false')



    def apply_theme(self, ui: UiContext):
        if ui.get_value('monochrome_ui') == 'true':
            self._theme_manager.set_theme('Mono')
        else:
            ui_theme = ui.get_value('ui_theme') if self._retroaccount.is_update_all_extras_active() else DEFAULT_SETTINGS_SCREEN_THEME
            self._theme_manager.set_theme(ui_theme)

    def apply_overscan(self, ui: UiContext):
        config = self._config_provider.get()
        config.overscan = ui.get_value('overscan')
        config.overscan_dim = calculate_overscan(config.overscan, config.term_size)

    def _read_media_fat_available_space(self) -> str:
        try:
            available_space = self._file_system.available_space(MEDIA_FAT)
            return str(available_space)
        except Exception as e:
            self._logger.debug('Could not calculate available space for /media/fat')
            self._logger.debug(e)
            return str(10**15)

    def select_all_ajgowans_manuals_dbs(self, ui: UiContext, effect) -> Optional[str]:
        changed = False
        action = effect['action']
        current_selector = ui.get_value('ajgowans_manuals_dbs_general_selector')
        all_active = all(
            ui.get_value(variable) == 'true'
            for variable in self._ajgowans_manuals_db_variables
        )

        if action == 'toggle':
            if current_selector == 'false':
                changed = self._set_all_ajgowans_manuals_dbs(ui, 'true') or changed
                changed = self._set_ajgowans_manuals_dbs_general_selector(ui, 'true') or changed
            else:
                if all_active:
                    changed = self._set_all_ajgowans_manuals_dbs(ui, 'false') or changed
                changed = self._set_ajgowans_manuals_dbs_general_selector(ui, 'false') or changed
        elif action == 'unapply':
            changed = self._set_ajgowans_manuals_dbs_general_selector(ui, 'false') or changed
        else:
            raise ValueError(f'Unknown ajgowans manuals selector action value: {action}')

        return 'clear_window' if changed else None

    def _set_ajgowans_manuals_dbs_general_selector(self, ui: UiContext, value: str) -> bool:
        if ui.get_value('ajgowans_manuals_dbs_general_selector') == value:
            return False

        ui.set_value('ajgowans_manuals_dbs_general_selector', value)
        return True

    def _set_all_ajgowans_manuals_dbs(self, ui: UiContext, value: str) -> bool:
        changed = False
        for variable in self._ajgowans_manuals_db_variables:
            if ui.get_value(variable) != value:
                ui.set_value(variable, value)
                changed = True
        return changed

    @staticmethod
    def _format_available_space(available_space: str) -> str:
        try:
            available_space_value = int(available_space)
        except ValueError:
            return 'unknown'

        if available_space_value < 0:
            return 'unknown'

        units = ['B', 'KB', 'MB', 'GB', 'TB']
        value = float(available_space_value)

        for unit in units:
            if value < 1024 or unit == units[-1]:
                if unit == 'B':
                    return f'{int(value)} {unit}'
                return f'{value:.1f} {unit}'
            value /= 1024

    def prepare_exit_without_save(self) -> None:
        self._mister_video_mode_service.restore_mode_before_unsaved_keeps()

    def prepare_exit_dont_save_and_run(self, ui):
        self._mister_video_mode_service.restore_mode_before_unsaved_keeps()
        self._copy_ui_options_to_current_config(ui)
        config = self._config_provider.get()
        config.temporary_downloader_ini = True
        self._logger.configure(config)
        self._ini_repository.write_downloader_ini(config, FILE_downloader_temp_ini)
        self._ini_repository.write_separate_db_ini_files(config, str(Path(FILE_downloader_temp_ini).parent))
        self._logger.debug(f'Written temporary {FILE_downloader_temp_ini} file.')

    def pocket_firmware_update(self, ui):
        self._ui_runtime.interrupt()

        self._logger.print()
        logger = CollectorLoggerDecorator(self._logger)
        installed = pocket_firmware_update(self._config_provider.get().curl_ssl, self._local_repository, logger, self._config_provider.get().http_config)

        logs = list(logger.prints)
        logs.append('')

        header = 'Your Pocket is updated' if installed else 'Update failed!'
        if installed:
            logs.append("\n\nReboot your Analogue Pocket to apply the new firmware if you haven't done it yet.")
        else:
            logs.append('\n\nUpdate failed.')

        ui.set_value('pocket_firmware_update_result_txt', '\n'.join(logs))
        ui.set_value('pocket_firmware_update_result_header', header)

        self._ui_runtime.resume()

    def pocket_backup(self, ui):
        self._ui_runtime.interrupt()

        self._logger.print()
        logger = CollectorLoggerDecorator(self._logger)
        backup_done = pocket_backup(logger)

        logs = list(logger.prints)
        logs.append('')

        header = 'Your Pocket Backup has been created!' if backup_done else 'Pocket Backup failed!'
        if backup_done:
            logs.append("\n\nPocket Backup process ended successfully.")
        else:
            logs.append('\n\nPocket Backup process failed.')

        ui.set_value('pocket_backup_result_txt', '\n'.join([log for log in logs if log.strip() != '.' and 'Done' not in log]))
        ui.set_value('pocket_backup_result_header', header)

        self._ui_runtime.resume()

    def retroaccount_check_state(self, ui: UiContext) -> Optional[str]:
        state_changed = False

        update_all_extras = benefit_state_to_message(self._retroaccount.update_all_extras_sync_state())
        update_all_extras_ui_key = 'retroaccount_update_all_extras'
        if ui.get_value(update_all_extras_ui_key) != update_all_extras:
            ui.set_value(update_all_extras_ui_key, update_all_extras)
            ui.set_value('retroaccount_update_all_extras_support', 'This benefit is active!' if update_all_extras == ACTIVE_BENEFIT_MSG else 'Support theypsilon on Patreon to unlock this benefit.')
            state_changed = True

        jtbeta_access = benefit_state_to_message(self._retroaccount.jtbeta_access_sync_state())
        jtbeta_access_ui_key = 'retroaccount_jtbeta_access'
        if ui.get_value(jtbeta_access_ui_key) != jtbeta_access:
            ui.set_value(jtbeta_access_ui_key, jtbeta_access)
            ui.set_value('retroaccount_jtbeta_access_support', 'This benefit is active!' if jtbeta_access == ACTIVE_BENEFIT_MSG else 'Support JOTEGO and theypsilon on Patreon to unlock this benefit.')
            state_changed = True

        checking_ui_key = 'retroaccount_checking'
        checking_ui_value = ui.get_value(checking_ui_key)
        if checking_ui_value != RETROACCOUNT_STATE_ONLINE:
            dots = checking_ui_value.count(".")
            if state_changed:
                ui.set_value(checking_ui_key, RETROACCOUNT_STATE_ONLINE)
            elif dots >= len(RETROACCOUNT_STATE_ONLINE):
                ui.set_value(checking_ui_key, dots * ' ')
            else:
                ui.set_value(checking_ui_key, (dots + 1) * '.')

        if state_changed:
            return 'clear_window'

    def retroaccount_device_logout(self, _ui: UiContext) -> None:
        self._retroaccount.device_logout()

RETROACCOUNT_STATE_ONLINE: Final[str] = 'Online.'
ACTIVE_BENEFIT_MSG: Final[str] = 'Active'

def benefit_state_to_message(benefit_state: BenefitState) -> str:
    if benefit_state == BenefitState.CHECKING:
        return 'Checking...'
    elif benefit_state == BenefitState.ACTIVE:
        return 'Active'
    elif benefit_state == BenefitState.INACTIVE:
        return 'Inactive'
    elif benefit_state == BenefitState.CONNECTION_FAILED:
        return 'Could not connect to the server. Try again later'
    elif benefit_state == BenefitState.NEED_LOGIN:
        return 'Login again please.'
    else:
        return ''
