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
import hashlib
from functools import cached_property

from update_all.config import Config
from update_all.constants import ARCADE_ORGANIZER_INI, FILE_MiSTer, \
    TEST_UNSTABLE_SPINNER_FIRMWARE_MD5, DOWNLOADER_URL, FILE_MiSTer_ini, ARCADE_ORGANIZER_URL, \
    ARCADE_ORGANIZER_INSTALLED_NAMES_TXT, STANDARD_UI_THEME, FILE_downloader_temp_ini, FILE_MiSTer_delme
from update_all.databases import db_ids_by_model_variables, DB_ID_NAMES_TXT, AllDBs
from update_all.ini_repository import IniRepository
from update_all.file_system import FileSystem
from update_all.local_repository import LocalRepository
from update_all.local_store import LocalStore
from update_all.other import Checker, GenericProvider
from update_all.logger import Logger
from update_all.os_utils import OsUtils
from update_all.settings_screen_model import settings_screen_model
from update_all.settings_screen_printer import SettingsScreenPrinter
from update_all.ui_engine import UiContext, UiApplication, UiSectionFactory, execute_ui_engine, UiRuntime
from update_all.ui_engine_dialog_application import DialogSectionFactory
from update_all.ui_model_utilities import gather_variable_declarations, dynamic_convert_string


class SettingsScreen(UiApplication):
    def __init__(self, logger: Logger, config_provider: GenericProvider[Config], file_system: FileSystem,
                 ini_repository: IniRepository, os_utils: OsUtils, settings_screen_printer: SettingsScreenPrinter,
                 checker: Checker, local_repository: LocalRepository, store_provider: GenericProvider[LocalStore],
                 ui_runtime: UiRuntime):
        self._logger = logger
        self._config_provider = config_provider
        self._file_system = file_system
        self._ini_repository = ini_repository
        self._os_utils = os_utils
        self._settings_screen_printer = settings_screen_printer
        self._checker = checker
        self._local_repository = local_repository
        self._store_provider = store_provider
        self._ui_runtime = ui_runtime
        self._original_firmware = None
        self._theme_manager = None

    def load_main_menu(self) -> None:
        self._load_menu_entry('main_menu')

    def load_test_menu(self) -> None:
        self._load_menu_entry('test_menu')

    def _load_menu_entry(self, menu_entry) -> None:
        def loader():
            execute_ui_engine(menu_entry, settings_screen_model(), self, self._ui_runtime)

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

        local_store = self._store_provider.get()
        ui_theme = local_store.get_theme() if self._checker.available_code > 1 else STANDARD_UI_THEME
        ui.set_value('ui_theme', ui_theme)
        ui.set_value('wait_time_for_reading', str(local_store.get_wait_time_for_reading()))
        ui.set_value('countdown_time', str(local_store.get_countdown_time()))
        ui.set_value('autoreboot', str(local_store.get_autoreboot()).lower())

        if AllDBs.JTCORES.db_id not in config.databases:
            ui.set_value('download_beta_cores', str(local_store.get_download_beta_cores()).lower())

        if DB_ID_NAMES_TXT not in config.databases:
            ui.set_value('names_region', local_store.get_names_region())
            ui.set_value('names_char_code', local_store.get_names_char_code())
            ui.set_value('names_sort_code', local_store.get_names_sort_code())

        drawer_factory, theme_manager = self._settings_screen_printer.initialize_screen()
        theme_manager.set_theme(ui_theme)

        ui.add_custom_effects({
            'calculate_needs_save': lambda effect: self.calculate_needs_save(ui),
            'calculate_has_right_available_code': lambda effect: self.calculate_has_right_available_code(ui),
            'calculate_is_test_spinner_firmware_applied': lambda effect: self.calculate_is_test_spinner_firmware_applied(ui),
            'test_unstable_spinner_firmware': lambda effect: self.test_unstable_spinner_firmware(ui),
            'play_bad_apple': lambda effect: self.play_bad_apple(ui), 'save': lambda effect: self.save(ui),
            'prepare_exit_dont_save_and_run': lambda effect: self.prepare_exit_dont_save_and_run(ui),
            'calculate_file_exists': lambda effect: self.calculate_file_exists(ui, effect),
            'remove_file': lambda effect: self.remove_file(ui, effect),
            'calculate_arcade_organizer_folders': lambda effect: self.calculate_arcade_organizer_folders(ui),
            'clean_arcade_organizer_folders': lambda effect: self.clean_arcade_organizer_folders(ui),
            'calculate_names_char_code_warning': lambda effect: self.calculate_names_char_code_warning(ui),
            'calculate_names_txt_file_warning': lambda effect: self.calculate_names_txt_file_warning(ui),
            'apply_theme': lambda effect: self.apply_theme(ui),
        })

        self._theme_manager = theme_manager
        return DialogSectionFactory(drawer_factory)

    def calculate_file_exists(self, ui, effect) -> None:
        ui.set_value('file_exists', 'true' if self._file_system.is_file(effect['target']) else 'false')

    def remove_file(self, ui, effect) -> None:
        ui.set_value('file_exists', self._file_system.unlink(effect['target']))

    def calculate_has_right_available_code(self, ui: UiContext) -> None:
        is_test_firmware, firmware_md5 = self._is_test_firmware()
        if firmware_md5 is not None:
            self._original_firmware = firmware_md5

        ui.set_value('has_right_available_code', 'true' if self._checker.available_code > 1 else 'false')

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

    def play_bad_apple(self, _ui) -> None:
        content = self._os_utils.download(DOWNLOADER_URL)
        if content is None:
            return None

        temp_file = self._file_system.temp_file_by_id('downloader.sh')
        self._file_system.write_file_bytes(temp_file.name, content)

        mister_ini = self._read_mister_ini()

        bad_apple_db_url = "https://github.com/theypsilon/BadAppleDB_MiSTer/releases/download/v1/bad_apple_full_res_db.json.zip"
        if 'fb_size=2' in mister_ini or 'fb_terminal=0' in mister_ini:
            bad_apple_db_url = "https://github.com/theypsilon/BadAppleDB_MiSTer/releases/download/v1/bad_apple_half_res_db.json.zip"

        env = {
            'DOWNLOADER_INI_PATH': "/tmp/downloader_bad_apple.ini",
            'ALLOW_REBOOT': '0',
            'CURL_SSL': self._config_provider.get().curl_ssl,
            'UPDATE_LINUX': 'false',
            'DEFAULT_DB_ID': 'bad_apple_db',
            'DEFAULT_DB_URL': bad_apple_db_url,
            'LOGFILE': "/tmp/downloader_bad_apple.log",
        }

        self._ui_runtime.interrupt()

        self._os_utils.execute_process(temp_file.name, env)

        self._ui_runtime.resume()

    def calculate_needs_save(self, ui: UiContext) -> None:
        needs_save_file_set = set()

        temp_config = Config()
        self._copy_temp_save_to_config(ui, temp_config)
        if self._ini_repository.does_downloader_ini_need_save(temp_config):
            needs_save_file_set.add("downloader.ini")

        if self._does_arcade_oganizer_need_save(ui):
            needs_save_file_set.add("update_arcade-organizer.ini")

        local_store = self._store_provider.get()
        local_store.set_theme(ui.get_value('ui_theme'))
        local_store.set_wait_time_for_reading(temp_config.wait_time_for_reading)
        local_store.set_countdown_time(temp_config.countdown_time)
        local_store.set_autoreboot(temp_config.autoreboot)

        if local_store.needs_save():
            needs_save_file_set.add(f"Internals ({', '.join(local_store.changed_fields())})")

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

        local_store = self._store_provider.get()
        if AllDBs.JTCORES.db_id in config.databases:
            local_store.set_download_beta_cores(config.download_beta_cores)

        if DB_ID_NAMES_TXT in config.databases:
            local_store.set_names_region(config.names_region)
            local_store.set_names_char_code(config.names_char_code)
            local_store.set_names_sort_code(config.names_sort_code)

        if local_store.needs_save():
            self._local_repository.save_store(local_store)

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
                if not isinstance(value, type(getattr(config, variable))):
                    raise TypeError(f'{variable} can not have value {value}! (wrong type)')
                setattr(config, variable, value)

        for variable in gather_variable_declarations(settings_screen_model(), "db"):
            if ui.get_value(variable) == 'false':
                continue

            config.databases.add(db_ids[variable])

    @cached_property
    def _all_config_variables(self):
        return [
            *gather_variable_declarations(settings_screen_model(), "ua_ini"),
            *gather_variable_declarations(settings_screen_model(), "jt_ini"),
            *gather_variable_declarations(settings_screen_model(), "names_ini"),
            *gather_variable_declarations(settings_screen_model(), "arcade_roms"),
            *gather_variable_declarations(settings_screen_model(), "rannysnice_wallpapers"),
        ]

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
        content = self._os_utils.download(ARCADE_ORGANIZER_URL)
        if content is None:
            return None

        temp_file = self._file_system.temp_file_by_id('arcade_organizer.sh')
        self._file_system.write_file_bytes(temp_file.name, content)

        return_code, output = self._os_utils.read_command_output(['python3', temp_file.name, '--print-orgdir-folders'],
                                                                 {
                                                                     'SSL_SECURITY_OPTION': self._config_provider.get().curl_ssl,
                                                                     'INI_FILE': f'{self._config_provider.get().base_path}/{ARCADE_ORGANIZER_INI}'
                                                                 })

        ui.set_value('has_arcade_organizer_folders', 'true' if return_code == 0 and len(output.strip()) > 0 else 'false')
        ui.set_value('arcade_organizer_folders_list', output if return_code == 0 else '')

    def clean_arcade_organizer_folders(self, ui: UiContext) -> None:
        for line in ui.get_value('arcade_organizer_folders_list').splitlines():
            self._file_system.remove_non_empty_folder(line.strip())

        ui.set_value('has_arcade_organizer_folders', 'false')
        ui.set_value('arcade_organizer_folders_list', '')

    def apply_theme(self, ui: UiContext):
        self._theme_manager.set_theme(ui.get_value('ui_theme'))

    def prepare_exit_dont_save_and_run(self, ui):
        self._copy_ui_options_to_current_config(ui)
        config = self._config_provider.get()
        config.temporary_downloader_ini = True
        self._ini_repository.write_downloader_ini(config, FILE_downloader_temp_ini)
        self._logger.debug(f'Written temporary {FILE_downloader_temp_ini} file.')
