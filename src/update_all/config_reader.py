# Copyright (c) 2022-2025 José Manuel Barroso Galindo <theypsilon@gmail.com>

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
from pathlib import Path
from typing import Dict

from update_all.analogue_pocket.http_gateway import http_config
from update_all.file_system import FileSystem
from update_all.config import Config, EnvDict
from update_all.constants import MEDIA_FAT, KENV_CURL_SSL, KENV_COMMIT, KENV_LOCATION_STR, MISTER_ENVIRONMENT, KENV_DEBUG, \
    KENV_RETROACCOUNT_FEATURE_FLAG, KENV_RETROACCOUNT_DOMAIN, DOMAIN_default_retroaccount, \
    FILE_retroaccount_feature_flag, K_RETROACCOUNT_DOMAIN
from update_all.databases import DB_ID_NAMES_TXT, model_variables_by_db_id, DB_ID_DISTRIBUTION_MISTER, all_dbs, ALL_DB_IDS
from update_all.ini_repository import IniRepository
from update_all.ini_parser import IniParser
from update_all.local_store import LocalStore
from update_all.logger import Logger
from update_all.other import strtobool


class ConfigReader:
    def __init__(self, logger: Logger, env: EnvDict, ini_repository: IniRepository):
        self._logger = logger
        self._env = env
        self._ini_repository = ini_repository

    def read_downloader_ini(self) -> Dict[str, IniParser]:
        self._ini_repository.initialize_downloader_ini_base_path(str(calculate_base_path(self._env)))
        return {k: IniParser(v) for k, v in self._ini_repository.get_downloader_ini().items()}

    def fill_config_with_mister_section(self, config: Config, downloader_ini: Dict[str, IniParser]):
        if 'mister' in downloader_ini:
            mister_section = downloader_ini['mister']
            config.base_path = mister_section.get_string('base_path', config.base_path)
            config.base_system_path = mister_section.get_string('base_system_path', config.base_path)
            config.paths_from_downloader_ini = mister_section.has('base_path')
            config.verbose = mister_section.get_bool('verbose', config.verbose)
            if http_proxy := mister_section.get_string('http_proxy', ''):
                config.http_proxy = http_proxy
                config.http_config = http_config(http_proxy=http_proxy, https_proxy=None)

    def fill_config_with_environment(self, config: Config):
        if is_debug_enabled(self._env):
            config.verbose = True

        config.base_path = str(calculate_base_path(self._env))
        config.base_system_path = config.base_path
        config.curl_ssl = valid_max_length(KENV_CURL_SSL, self._env['CURL_SSL'], 50).strip()
        config.commit = valid_max_length(KENV_COMMIT, self._env['COMMIT'], 50).strip()
        config.skip_downloader = strtobool(self._env.get('SKIP_DOWNLOADER').strip().lower())
        config.transition_service_only = strtobool(self._env['TRANSITION_SERVICE_ONLY'].strip().lower())
        config.patreon_key_path = self._env['PATREON_KEY_PATH'].strip()
        config.command = self._env.get('COMMAND', config.command).strip().upper()
        config.timeline_short_path = self._env.get('TIMELINE_SHORT_PATH', config.timeline_short_path).strip()
        config.timeline_plus_path = self._env.get('TIMELINE_PLUS_PATH', config.timeline_plus_path).strip()
        config.mirror = self._env.get('MIRROR_ID', config.mirror).strip().lower()
        config.retroaccount_feature_flag = strtobool(self._env.get(KENV_RETROACCOUNT_FEATURE_FLAG, 'false').strip().lower())
        config.retroaccount_domain = self._env.get(KENV_RETROACCOUNT_DOMAIN, DOMAIN_default_retroaccount).strip().rstrip('/')
        if self._env['HTTP_PROXY'] or self._env['HTTPS_PROXY']:
            config.http_config = http_config(http_proxy=self._env['HTTP_PROXY'], https_proxy=self._env['HTTPS_PROXY'])
            config.http_proxy = self._env['HTTP_PROXY'] or self._env['HTTPS_PROXY']  # @TODO: Remove this line when this is not used by the Arcade Organizer or any other part
        elif config.http_proxy != '':
            config.http_config = http_config(http_proxy=config.http_proxy, https_proxy=None)

        if not is_mister_environment(self._env):
            config.not_mister = True

    def fill_config_with_database_sections(self, config: Config, downloader_ini: Dict[str, IniParser]) -> None:
        for db_id, variable in model_variables_by_db_id().items():
            is_present = db_id.lower() in downloader_ini
            config.__setattr__(variable, is_present)
            if is_present:
                config.databases.add(db_id)

        db_defs = all_dbs(config.mirror)
        config.databases.add(ALL_DB_IDS['UPDATE_ALL_MISTER'])

        if DB_ID_DISTRIBUTION_MISTER in downloader_ini:
            parser = downloader_ini[DB_ID_DISTRIBUTION_MISTER]
            config.encc_forks = db_defs.encc_forks_by_distribution_mister_db_url(parser.get_string('db_url', None))

        if ALL_DB_IDS['JTCORES'] in downloader_ini:
            parser = downloader_ini[ALL_DB_IDS['JTCORES']]
            if db_defs.should_download_beta_cores(parser.get_string('db_url', None), parser.get_string('filter', None)):
                config.download_beta_cores = True

        if DB_ID_NAMES_TXT in downloader_ini:
            parser = downloader_ini[DB_ID_NAMES_TXT]
            (config.names_region,
             config.names_char_code,
             config.names_sort_code) = db_defs.names_locale_by_db_url(parser.get_string('db_url', None))

        if ALL_DB_IDS['ARCADE_ROMS'] in downloader_ini:
            parser = downloader_ini[ALL_DB_IDS['ARCADE_ROMS']]
            config.hbmame_filter = '!hbmame' in parser.get_string('filter', '')

        if ALL_DB_IDS['RANNYSNICE_WALLPAPERS'].lower() in downloader_ini:
            parser = downloader_ini[ALL_DB_IDS['RANNYSNICE_WALLPAPERS'].lower()]
            rannysnice_wallpapers_filter = parser.get_string('filter', '').replace('-', '').replace('_', '').lower()
            config.rannysnice_wallpapers_filter = 'ar16-9' if 'ar169' in rannysnice_wallpapers_filter else 'ar4-3' if 'ar43' in rannysnice_wallpapers_filter else 'all'

        config.arcade_organizer = self._ini_repository.get_arcade_organizer_ini().get_bool('arcade_organizer', config.arcade_organizer)

    def fill_config_with_local_store(self, config: Config, store: LocalStore):
        if mirror := store.get_mirror():
            config.mirror = mirror
        config.countdown_time = store.get_countdown_time()
        config.autoreboot = store.get_autoreboot()
        config.pocket_firmware_update = store.get_pocket_firmware_update()
        config.pocket_backup = store.get_pocket_backup()
        config.log_viewer = store.get_log_viewer()
        config.timeline_after_logs = store.get_timeline_after_logs()

    def read_retroaccount_feature_flag_file(self, config: Config, file_system: FileSystem) -> None:
        if not file_system.is_file(FILE_retroaccount_feature_flag):
            return

        config.retroaccount_feature_flag = True
        try:
            content = file_system.read_file_contents(FILE_retroaccount_feature_flag).strip()
            if content:
                data = json.loads(content)
                if K_RETROACCOUNT_DOMAIN in data:
                    config.retroaccount_domain = str(data[K_RETROACCOUNT_DOMAIN]).strip().rstrip('/')
        except (json.JSONDecodeError, Exception) as e:
            self._logger.debug(f'Could not parse retroaccount feature flag file as JSON: {e}')

    def debug_log(self, config: Config, store: LocalStore):
        self._logger.debug('env: ' + json.dumps(self._env, indent=4))
        self._logger.debug('config: ' + json.dumps(config, default=lambda o: str(o) if isinstance(o, Path) or isinstance(o, set) else o.__dict__, indent=4))
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
