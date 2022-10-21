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
from update_all.config import Config
from update_all.constants import FILE_update_all_ini, FILE_update_jtcores_ini, \
    FILE_update_names_txt_ini, ARCADE_ORGANIZER_INI, FILE_update_names_txt_sh, FILE_update_jtcores_sh
from update_all.databases import db_ids_by_model_variables
from update_all.ini_repository import IniRepository
from update_all.file_system import FileSystem
from update_all.local_store import LocalStore
from update_all.logger import Logger
from update_all.os_utils import OsUtils
from update_all.settings_screen_model import settings_screen_model
from update_all.ui_model_utilities import gather_variable_declarations, dynamic_convert_string


default_arcade_organizer_enabled = Config().arcade_organizer


class TransitionService:

    def __init__(self, logger: Logger, file_system: FileSystem, os_utils: OsUtils, ini_repository: IniRepository):
        self._logger = logger
        self._file_system = file_system
        self._os_utils = os_utils
        self._ini_repository = ini_repository

    def transition_from_update_all_1(self, config: Config, store: LocalStore):
        update_all_ini_exists = self._file_system.is_file(FILE_update_all_ini)
        changes = []

        if self._file_system.is_file(self._ini_repository.downloader_ini_standard_path()):
            if update_all_ini_exists:
                self._fill_arcade_organizer_enabled_model_variable_from_update_all_ini(config)
        else:
            if update_all_ini_exists:
                self._fill_config_with_update_all_ini(config, store)

            for ini_file, ini_group in [(FILE_update_jtcores_ini, "jt_ini"), (FILE_update_names_txt_ini, "names_ini")]:
                if self._file_system.is_file(ini_file):
                    self._fill_config_with_ini_file(config, ini_file, ini_group)

            self._ini_repository.write_downloader_ini(config)
            changes.append('A new file "downloader.ini" has been created.')

        if config.arcade_organizer != default_arcade_organizer_enabled:
            self._ini_repository.write_arcade_organizer_active_at_arcade_organizer_ini(config)
            changes.append(f'File "{ARCADE_ORGANIZER_INI}" now includes variable "ARCADE_ORGANIZER" previously found in "{FILE_update_all_ini}". It indicates whether the Arcade Organizer is enabled in Update All.')

        for file in [FILE_update_all_ini, FILE_update_jtcores_ini, FILE_update_names_txt_ini, FILE_update_names_txt_sh]:
            if self._file_system.is_file(file):
                self._file_system.unlink(file, verbose=False)
                changes.append(f'Obsolete file "{file}" removed.')

        if len(changes) >= 1:
            coming_from_update_all_1 = len(changes) >= 2 or 'downloader.ini' not in changes[0]
            if coming_from_update_all_1:
                self._logger.print('Transitioning from Update All 1:')
            else:
                self._logger.print('Setting default options:')

            for change in changes:
                self._logger.print(f'  - {change}')
            self._logger.print()
            if coming_from_update_all_1:
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
