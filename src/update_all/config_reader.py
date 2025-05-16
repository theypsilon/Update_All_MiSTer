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
import json
import time
from pathlib import Path
from typing import Dict

from update_all.config import Config
from update_all.constants import MEDIA_FAT, KENV_CURL_SSL, KENV_COMMIT, KENV_LOCATION_STR, MISTER_ENVIRONMENT, \
    KENV_DEBUG, KENV_TRANSITION_SERVICE_ONLY, KENV_LOCAL_TEST_RUN
from update_all.databases import DB_ID_NAMES_TXT, names_locale_by_db_url, model_variables_by_db_id, \
    AllDBs, DB_ID_DISTRIBUTION_MISTER, DB_URL_JTPREMIUM_DEPRECATED, DB_URL_MISTERSAM_FILES_DEPRECATED
from update_all.ini_repository import IniRepository
from update_all.ini_parser import IniParser
from update_all.local_store import LocalStore
from update_all.logger import Logger
from update_all.other import strtobool


class ConfigReader:
    def __init__(self, logger: Logger, env: dict[str, str], ini_repository: IniRepository):
        self._logger = logger
        self._env = env
        self._ini_repository = ini_repository

    def read_downloader_ini(self) -> Dict[str, IniParser]:
        self._ini_repository.initialize_downloader_ini_base_path(str(calculate_base_path(self._env)))
        return {k: IniParser(v) for k, v in self._ini_repository.get_downloader_ini().items()}

    def fill_config_with_environment_and_mister_section(self, config: Config, downloader_ini: Dict[str, IniParser]):
        if 'mister' in downloader_ini:
            mister_section = downloader_ini['mister']
            config.base_path = mister_section.get_string('base_path', config.base_path)
            config.base_system_path = mister_section.get_string('base_system_path', config.base_path)
            config.paths_from_downloader_ini = mister_section.has('base_path')
            config.verbose = mister_section.get_bool('verbose', False)
        else:
            config.base_path = str(calculate_base_path(self._env))
            config.base_system_path = config.base_path

        if is_debug_enabled(self._env):
            config.verbose = True

        config.curl_ssl = valid_max_length(KENV_CURL_SSL, self._env[KENV_CURL_SSL], 50).strip()
        config.commit = valid_max_length(KENV_COMMIT, self._env[KENV_COMMIT], 50).strip()
        config.start_time = time.time()
        config.local_test_run = strtobool(self._env.get(KENV_LOCAL_TEST_RUN).strip().lower())
        config.transition_service_only = strtobool(self._env[KENV_TRANSITION_SERVICE_ONLY].strip().lower())

        self._logger.configure(config)

        if not is_mister_environment(self._env):
            config.not_mister = True

        self._logger.debug('env: ' + json.dumps(self._env, indent=4))

    def fill_config_with_ini_files(self, config: Config, downloader_ini: Dict[str, IniParser]) -> None:
        for db_id, variable in model_variables_by_db_id().items():
            is_present = db_id.lower() in downloader_ini
            config.__setattr__(variable, is_present)
            if is_present:
                config.databases.add(db_id)

        config.databases.add(AllDBs.UPDATE_ALL_MISTER.db_id)

        if DB_ID_DISTRIBUTION_MISTER in downloader_ini:
            parser = downloader_ini[DB_ID_DISTRIBUTION_MISTER]
            db_url = parser.get_string('db_url', AllDBs.MISTER_DEVEL_DISTRIBUTION_MISTER.db_url).strip().lower()
        
            if db_url == AllDBs.MISTER_DB9_DISTRIBUTION_MISTER.db_url.lower():
                config.encc_forks = 'db9'
            elif db_url == AllDBs.MISTER_AITORGOMEZ_DISTRIBUTION_MISTER.db_url.lower():
                config.encc_forks = 'aitorgomez'
            else:
                config.encc_forks = 'devel'

        if AllDBs.JTCORES.db_id in downloader_ini:
            parser = downloader_ini[AllDBs.JTCORES.db_id]
            jt_db_url = parser.get_string('db_url', AllDBs.JTCORES.db_url).strip().lower()
            jt_filter = parser.get_string('filter', None)
            if jt_db_url == DB_URL_JTPREMIUM_DEPRECATED.lower():
                config.download_beta_cores = True
            elif jt_filter is not None and '!jtbeta' not in jt_filter.replace(' ', '').lower():
                config.download_beta_cores = True

        if DB_ID_NAMES_TXT in downloader_ini:
            parser = downloader_ini[DB_ID_NAMES_TXT]
            config.names_region, config.names_char_code, config.names_sort_code = names_locale_by_db_url(parser.get_string('db_url', AllDBs.NAMES_CHAR18_COMMON_JP_TXT.db_url).strip())

        if AllDBs.ARCADE_ROMS.db_id in downloader_ini:
            parser = downloader_ini[AllDBs.ARCADE_ROMS.db_id]
            config.hbmame_filter = '!hbmame' in parser.get_string('filter', '')

        if AllDBs.RANNYSNICE_WALLPAPERS.db_id.lower() in downloader_ini:
            parser = downloader_ini[AllDBs.RANNYSNICE_WALLPAPERS.db_id.lower()]
            rannysnice_wallpapers_filter = parser.get_string('filter', '').replace('-', '').replace('_', '').lower()
            config.rannysnice_wallpapers_filter = 'ar16-9' if 'ar169' in rannysnice_wallpapers_filter else 'ar4-3' if 'ar43' in rannysnice_wallpapers_filter else 'all'

        config.arcade_organizer = self._ini_repository.get_arcade_organizer_ini().get_bool('arcade_organizer', config.arcade_organizer)

        self._logger.debug('config: ' + json.dumps(config, default=lambda o: str(o) if isinstance(o, Path) or isinstance(o, set) else o.__dict__, indent=4))

    def fill_config_with_local_store(self, config: Config, store: LocalStore):
        config.wait_time_for_reading = store.get_wait_time_for_reading()
        config.countdown_time = store.get_countdown_time()
        config.autoreboot = store.get_autoreboot()
        config.pocket_firmware_update = store.get_pocket_firmware_update()
        config.pocket_backup = store.get_pocket_backup()
        config.log_viewer = store.get_log_viewer()
        self._logger.debug('store: ' + json.dumps(store.unwrap_props(), indent=4))


def valid_max_length(key: str, value: str, max_limit: int) -> str:
    if len(value) <= max_limit:
        return value

    raise InvalidConfigParameter(f"Invalid {key} with value '{value}'. Too long string (max is {max_limit}).")


def calculate_base_path(env):
    if is_mister_environment(env):
        return Path(MEDIA_FAT)
    else:
        return Path(env[KENV_LOCATION_STR]).resolve()


def is_mister_environment(env):
    return env[KENV_LOCATION_STR].strip().lower() == MISTER_ENVIRONMENT


def is_debug_enabled(env):
    return strtobool(env[KENV_DEBUG].strip().lower())


class InvalidConfigParameter(Exception):
    pass
