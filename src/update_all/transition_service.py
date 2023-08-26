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
from typing import Dict
from update_all.config import Config
from update_all.constants import FILE_update_all_ini, FILE_update_jtcores_ini, \
    FILE_update_names_txt_ini, ARCADE_ORGANIZER_INI, FILE_update_names_txt_sh
from update_all.databases import db_ids_by_model_variables, DB_ID_DISTRIBUTION_MISTER, AllDBs, DB_ID_NAMES_TXT, DB_ID_ARCADE_NAMES_TXT
from update_all.ini_repository import IniRepository
from update_all.file_system import FileSystem
from update_all.local_store import LocalStore
from update_all.logger import Logger
from update_all.os_utils import OsUtils
from update_all.other import GenericProvider
from update_all.settings_screen_model import settings_screen_model
from update_all.ui_model_utilities import gather_variable_declarations, dynamic_convert_string


default_arcade_organizer_enabled = Config().arcade_organizer


class TransitionService:

    def __init__(self, logger: Logger, file_system: FileSystem, os_utils: OsUtils, ini_repository: IniRepository):
        self._logger = logger
        self._file_system = file_system
        self._os_utils = os_utils
        self._ini_repository = ini_repository
        self._file_checks: Dict[str, bool] = {}
        self._created_downloader_ini = False

    def _file_exists(self, file: str) -> bool:
        if file not in self._file_checks:
            self._file_checks[file] = self._file_system.is_file(file)
        return self._file_checks[file]

    def from_jtpremium_to_jtcores(self, config: Config):
        if not self._file_exists(self._ini_repository.downloader_ini_standard_path()):
            return

        if not config.has_jtpremium:
            return

        self._logger.print('Transitioning from jtpremium to jtcores with premium filter:')
        self._ini_repository.write_downloader_ini(config)
        self._logger.print('Done.')
        self._logger.print()

    def from_mistersam_main_to_db_branch(self, config: Config):
        if not self._file_exists(self._ini_repository.downloader_ini_standard_path()):
            return

        if not config.has_mistersam_main_branch:
            return

        self._logger.print('Transitioning MiSTer SAM old DB URL to new one:')
        self._logger.print(AllDBs.MISTERSAM_FILES.db_url)
        self._ini_repository.write_downloader_ini(config)
        self._logger.print('Done.')
        self._logger.print()

    def from_not_existing_downloader_ini(self, config: Config):
        if self._file_exists(self._ini_repository.downloader_ini_standard_path()):
            return

        if self._file_exists(FILE_update_all_ini):
            return

        self._logger.print(f'File "{self._ini_repository.downloader_ini_standard_path()}" not found.')
        self._logger.print()

        config.databases.add(DB_ID_DISTRIBUTION_MISTER)
        config.databases.add(AllDBs.COIN_OP_COLLECTION.db_id)
        config.databases.add(AllDBs.JTCORES.db_id)
        self._ini_repository.write_downloader_ini(config)

        self._logger.print('A new file "downloader.ini" has been created with default DBs:')
        self._logger.print(f'  - Added DB with id [{DB_ID_DISTRIBUTION_MISTER}]')
        self._logger.print(f'  - Added DB with id [{AllDBs.JTCORES.db_id}]')
        self._logger.print(f'  - Added DB with id [{AllDBs.COIN_OP_COLLECTION.db_id}]')
        self._logger.print()
        self._logger.print('Waiting 10 seconds...')
        self._os_utils.sleep(10.0)
        self._created_downloader_ini = True

    def from_update_all_1(self, config: Config, store: LocalStore):
        changes = []

        if self._file_exists(self._ini_repository.downloader_ini_standard_path()):
            if self._file_exists(FILE_update_all_ini):
                self._fill_arcade_organizer_enabled_model_variable_from_update_all_ini(config)
        else:
            if self._file_exists(FILE_update_all_ini):
                self._fill_config_with_update_all_ini(config, store)
                changes.append('Adding "update_all.ini" values to "downloader.ini".')

            if self._file_exists(FILE_update_jtcores_ini):
                self._fill_config_with_ini_file(config, FILE_update_jtcores_ini, "jt_ini")
                changes.append('Adding "update_jtcores.ini" values to "downloader.ini".')

            if self._file_exists(FILE_update_names_txt_ini):
                self._fill_config_with_ini_file(config, FILE_update_names_txt_ini, "names_ini")
                changes.append('Adding "update_names-txt.ini" values to "downloader.ini".')

            if len(changes) >= 1:
                self._ini_repository.write_downloader_ini(config)

        if config.arcade_organizer != default_arcade_organizer_enabled:
            self._ini_repository.write_arcade_organizer_active_at_arcade_organizer_ini(config)
            changes.append(f'File "{ARCADE_ORGANIZER_INI}" now includes variable "ARCADE_ORGANIZER" previously found in "{FILE_update_all_ini}". It indicates whether the Arcade Organizer is enabled in Update All.')

        for file in [FILE_update_all_ini, FILE_update_jtcores_ini, FILE_update_names_txt_ini, FILE_update_names_txt_sh]:
            if self._file_exists(file):
                self._file_system.unlink(file, verbose=False)
                changes.append(f'Obsolete file "{file}" removed.')

        if len(changes) == 0:
            return

        if self._created_downloader_ini:
            self._logger.print()

        self._logger.print('Transitioning from Update All 1:')
        for change in changes:
            self._logger.print(f'  - {change}')
        self._logger.print()
        self._logger.print('Waiting 10 seconds...')
        self._os_utils.sleep(10.0)

    def from_just_names_txt_enabled_to_arcade_names_txt_enabled(self, config: Config, store: LocalStore):
        if store.get_introduced_arcade_names_txt():
            return

        store.set_introduced_arcade_names_txt(True)

        if DB_ID_NAMES_TXT not in config.databases:
            return

        if DB_ID_ARCADE_NAMES_TXT in config.databases:
            return

        config.databases.add(DB_ID_ARCADE_NAMES_TXT)

        self._ini_repository.write_downloader_ini(config)
        self._logger.print('Transitioning arcade names from "names.txt" to separated "..CONFIG../arcade_names.txt":')
        self._logger.print('Adding Arcade Names TXT db to downloader.ini.')
        self._logger.print()
        self._logger.print('Waiting 10 seconds...')
        self._os_utils.sleep(10.0)

    def _fill_arcade_organizer_enabled_model_variable_from_update_all_ini(self, config):
        ini_content = self._ini_repository.read_old_ini_file(FILE_update_all_ini)
        config.arcade_organizer = ini_content.get_bool('arcade_organizer', default_arcade_organizer_enabled)

    def _fill_config_with_update_all_ini(self, config: Config, store: LocalStore):
        update_all_ini = self._fill_config_with_ini_file(config, FILE_update_all_ini, "ua_ini")

        mame_getter = update_all_ini.get_bool('mame_getter', False)
        hbmame_getter = update_all_ini.get_bool('hbmame_getter', False)
        config.arcade_roms_db_downloader = config.arcade_roms_db_downloader or mame_getter or hbmame_getter
        if mame_getter and not hbmame_getter:
            config.hbmame_filter = True
            self._logger.debug('hbmame_filter=true')

        for variable in gather_variable_declarations(settings_screen_model(), 'store'):
            if hasattr(config, variable):
                value = getattr(config, variable)
                store.generic_set(variable, value)
                self._logger.debug(f'{variable}={str(value)}')

    def _fill_config_with_ini_file(self, config: Config, ini_file, ini_group):
        self._logger.debug(f'\nOpening {ini_file}')

        ini_content = self._ini_repository.read_old_ini_file(ini_file)
        db_ids = db_ids_by_model_variables()

        for variable, description in gather_variable_declarations(settings_screen_model(), ini_group).items():
            string_value = ini_content.get_string(variable, None)
            if string_value is None:
                string_value = description['default']
            else:
                string_value = self._ensure_string_value_is_possible(string_value, description['values'])
                self._logger.debug(f'{variable}={string_value}')

            value = dynamic_convert_string(string_value)

            setattr(config, variable, value)
            if variable in db_ids and value:
                config.databases.add(db_ids[variable])
                self._logger.debug(f'Added database: {db_ids[variable]}')

        return ini_content

    @staticmethod
    def _ensure_string_value_is_possible(string_value, possible_values):
        if string_value in possible_values:
            return string_value

        for pb in possible_values:
            if pb.lower() == string_value.lower():
                return pb

        raise ValueError(f'Value {string_value} is not among the possible values: {", ".join(possible_values)}')

#
# set_default_options:
#
# ENCC_FORKS="false" # Possible values: "true", "false"
# DOWNLOADER_WHEN_POSSIBLE="false" # Possible values: "true", "false"
#
# MAIN_UPDATER="true"
# MAIN_UPDATER_INI="${EXPORTED_INI_PATH}" # Probably update_all.ini
#
# JOTEGO_UPDATER="true"
# JOTEGO_UPDATER_INI="${EXPORTED_INI_PATH}" # Probably update_all.ini
#
# UNOFFICIAL_UPDATER="false"
# UNOFFICIAL_UPDATER_INI="${EXPORTED_INI_PATH}" # Probably update_all.ini
#
# LLAPI_UPDATER="false"
# LLAPI_UPDATER_INI="${EXPORTED_INI_PATH}" # Probably update_all.ini
#
# ARCADE_OFFSET_DOWNLOADER="false"
# COIN_OP_COLLECTION_DOWNLOADER="true"
# ARCADE_ROMS_DB_DOWNLOADER="false"
# TTY2OLED_FILES_DOWNLOADER="false"
# I2C2OLED_FILES_DOWNLOADER="false"
# MISTERSAM_FILES_DOWNLOADER="false"
#
# BIOS_GETTER="true"
# BIOS_GETTER_INI="update_bios-getter.ini"
#
# MAME_GETTER="true"
# MAME_GETTER_INI="update_mame-getter.ini"
#
# HBMAME_GETTER="true"
# HBMAME_GETTER_INI="update_hbmame-getter.ini"
#
# NAMES_TXT_UPDATER="false"
# NAMES_TXT_UPDATER_INI="update_names-txt.ini"
# NAMES_REGION="US"
# NAMES_CHAR_CODE="CHAR18"
# NAMES_SORT_CODE="Common"
#
# ARCADE_ORGANIZER="true"
# ARCADE_ORGANIZER_INI="update_arcade-organizer.ini"
#
# COUNTDOWN_TIME=15
# WAIT_TIME_FOR_READING=2
# AUTOREBOOT="true"
# KEEP_USBMOUNT_CONF="false"
