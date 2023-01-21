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
import configparser
import io
import json
import re
from typing import Optional, Dict, List, Tuple

from update_all.config import Config
from update_all.constants import DOWNLOADER_INI_STANDARD_PATH, ARCADE_ORGANIZER_INI, FILE_downloader_temp_ini
from update_all.databases import AllDBs, Database, db_distribution_mister_by_encc_forks, \
    db_jtcores_by_download_beta_cores, db_names_txt_by_locale, dbs_to_model_variables_pairs
from update_all.file_system import FileSystem
from update_all.ini_parser import IniParser
from update_all.logger import Logger
from update_all.os_utils import OsUtils

class IniRepository:

    def __init__(self, logger: Logger, file_system: FileSystem, os_utils: OsUtils):
        self._logger = logger
        self._file_system = file_system
        self._os_utils = os_utils
        self._base_path = None
        self._downloader_ini = None
        self._arcade_organizer_ini = None

    def initialize_downloader_ini_base_path(self, base_path: str) -> None:
        self._base_path = base_path

    def get_downloader_ini(self, cached: bool = True) -> Dict[str, Dict[str, str]]:
        if cached and self._downloader_ini is not None:
            return self._downloader_ini

        result = self._read_downloader_ini()
        if cached:
            self._downloader_ini = result
        return result

    def get_arcade_organizer_ini(self, cached: bool = True) -> IniParser:
        if cached and self._arcade_organizer_ini is not None:
            return self._arcade_organizer_ini

        result = self.read_old_ini_file(ARCADE_ORGANIZER_INI)
        if cached:
            self._arcade_organizer_ini = result
        return result

    def _read_downloader_ini(self) -> Dict[str, Dict[str, str]]:
        path = self.downloader_ini_standard_path()
        contents = ''
        try:
            contents = self._file_system.read_file_contents(path)
            parser = read_ini_contents(contents)
        except Exception as e:
            self._logger.debug(f'Could not read Downloader INI file at: {path}')
            self._logger.debug(f'contents: {contents}')
            self._logger.debug(e)
            return {}

        return {header.lower(): {k.lower(): v for k, v in section.items()} for header, section in parser.items() if header.lower() != 'default'}

    def read_old_ini_file(self, path: str) -> IniParser:
        if not self._file_system.is_file(path):
            return IniParser({})

        contents = ''
        try:
            contents = f'[default]\n{self._file_system.read_file_contents(path).lower()}'
            parser = read_ini_contents(contents)
        except Exception as e:
            self._logger.debug(f'Incorrect old INI format at: {path}')
            self._logger.debug(f'contents: {contents}')
            self._logger.debug(e)
            return IniParser({})

        return IniParser(parser['default'])

    def downloader_ini_standard_path(self) -> str:
        if self._base_path is None:
            raise Exception("DownloaderIniRepository needs to be initialized.")

        return f'{self._base_path}/{DOWNLOADER_INI_STANDARD_PATH}'

    def downloader_ini_path_tweaked_by_config(self, config: Config) -> str:
        return FILE_downloader_temp_ini if config.temporary_downloader_ini else self.downloader_ini_standard_path()

    def write_downloader_ini(self, config: Config, target_path: str = None) -> None:
        new_ini_contents = self._build_new_downloader_ini_contents(config)
        if new_ini_contents is None:
            return

        downloader_ini_path = self.downloader_ini_standard_path()
        if target_path is None:
            target_path = downloader_ini_path

        self._file_system.make_dirs_parent(target_path)
        self._file_system.write_file_contents(target_path, new_ini_contents)

        if target_path == downloader_ini_path:
            self._downloader_ini = None

    def write_arcade_organizer_active_at_arcade_organizer_ini(self, config: Config) -> None:
        contents = ''
        if self._file_system.is_file(ARCADE_ORGANIZER_INI):
            contents = self._file_system.read_file_contents(ARCADE_ORGANIZER_INI).strip()
            if 'arcade_organizer' in contents.lower():
                return
            contents += '\n'

        contents += f'ARCADE_ORGANIZER={str(config.arcade_organizer).lower()}\n'
        self._save_arcade_organizer_contents(contents + '\n')

    def write_arcade_organizer(self, props: Dict[str, str]) -> None:
        contents = ''
        for k, v in props.items():
            contents += f'{k.upper()}={v}\n'
        self._save_arcade_organizer_contents(contents + '\n')

    def _save_arcade_organizer_contents(self, contents):
        self._file_system.make_dirs_parent(ARCADE_ORGANIZER_INI)
        self._file_system.write_file_contents(ARCADE_ORGANIZER_INI, contents)
        self._arcade_organizer_ini = None

    def does_downloader_ini_need_save(self, config: Config) -> bool:
        if not self._file_system.is_file(self.downloader_ini_standard_path()):
            ini = {}
            self._add_new_downloader_ini_changes(ini, config)
            return len(ini) > 0

        new_ini_contents = self._build_new_downloader_ini_contents(config)
        if new_ini_contents is None:
            return False
        new_ini_contents = new_ini_contents.strip().lower()

        current_ini_contents = self._file_system.read_file_contents(self.downloader_ini_standard_path()).strip().lower()
        return new_ini_contents != current_ini_contents

    def _add_new_downloader_ini_changes(self, ini, config: Config) -> None:
        for _, db in candidate_databases(config):
            db_id = db.db_id.lower()
            if db in active_databases(config):
                if db_id not in ini:
                    ini[db_id] = {}
                ini[db_id]['db_url'] = db.db_url
            elif db_id in ini:
                del ini[db_id]

        mister_filter = ini['mister']['filter'].strip().lower() if 'mister' in ini and 'filter' in ini['mister'] else ''

        for db_id, filter_addition, filter_active in [(AllDBs.ARCADE_ROMS.db_id, '!hbmame', config.hbmame_filter)]:
            if db_id not in config.databases:
                continue

            lower_id = db_id.lower()

            if filter_active:
                arcade_roms_filter = ini[lower_id]['filter'].strip().lower() if 'filter' in ini[lower_id] else ''

                if len(arcade_roms_filter) == 0:
                    filter_result = f'{mister_filter} {filter_addition}'
                else:
                    filter_result = f'{arcade_roms_filter.replace(filter_addition, "")} {filter_addition}'

                ini[lower_id]['filter'] = ' '.join(filter_result.split()).strip()

            elif 'filter' in ini[lower_id]:
                filter_result = ini[lower_id]['filter'].replace(filter_addition, "").replace(mister_filter, "")

                ini[lower_id]['filter'] = ' '.join(filter_result.split()).strip()

                if len(ini[lower_id]['filter']) == 0:
                    del ini[lower_id]['filter']

        for db_id, filter_addition in [(AllDBs.RANNYSNICE_WALLPAPERS.db_id, config.rannysnice_wallpapers_filter)]:
            if db_id not in config.databases:
                continue

            lower_id = db_id.lower()
            ini[lower_id]['filter'] = filter_addition

    def _build_new_downloader_ini_contents(self, config: Config) -> Optional[str]:
        ini: dict[str, Dict[str, str]] = self.get_downloader_ini(cached=False)
        before = json.dumps(ini)
        self._add_new_downloader_ini_changes(ini, config)
        after = json.dumps(ini)

        if before == after:
            return None

        db_ids = {db.db_id.lower(): db.db_id for _, db in candidate_databases(config)}

        mister_section = ''
        nomister_section = ''
        pre_section = ''

        if self._file_system.is_file(self.downloader_ini_standard_path()):
            header_regex = re.compile('\s*\[([-_/a-zA-Z0-9]+)\].*', re.I)
            ini_contents = io.StringIO(self._file_system.read_file_contents(self.downloader_ini_standard_path()))

            no_section = 0
            other_section = 1
            common_section = 2

            state = no_section

            for line in ini_contents.readlines():
                match = header_regex.match(line)

                section: str
                if match is not None:
                    section = match.group(1).lower()
                    if section in db_ids:
                        state = common_section
                    else:
                        state = other_section

                if state == no_section:
                    pre_section += line
                elif state == common_section:
                    pass
                elif state == other_section:
                    if section in ini:
                        ini.pop(section)

                    if section.lower() == 'mister':
                        mister_section += line
                    else:
                        nomister_section += line
                else:
                    raise Exception("Wrong state: " + str(state))

        parser = configparser.ConfigParser(inline_comment_prefixes=(';', '#'))
        for header, section_id in ini.items():
            if header in db_ids:
                header = db_ids[header]
            parser[header] = section_id

        with io.StringIO() as ss:
            if pre_section != '':
                ss.write(pre_section.strip() + '\n\n')
            if mister_section != '':
                ss.write(mister_section.strip() + '\n\n')
            parser.write(ss)
            if nomister_section != '':
                ss.write(nomister_section.strip() + '\n\n')
            ss.seek(0)
            return ss.read()


def candidate_databases(config: Config) -> List[Tuple[str, Database]]:
    configurable_dbs = {
        'main_updater': db_distribution_mister_by_encc_forks(config.encc_forks),
        'jotego_updater': db_jtcores_by_download_beta_cores(config.download_beta_cores),
        'names_txt_updater': db_names_txt_by_locale(config.names_region, config.names_char_code, config.names_sort_code)
    }
    result = []
    for variable, dbs in dbs_to_model_variables_pairs():
        if variable in configurable_dbs:
            result.append((variable, configurable_dbs[variable]))
            continue

        if len(dbs) != 1:
            raise ValueError(f"Needs to be length 1, but is '{len(dbs)}', or must be contained in configurable_dbs.")

        result.append((variable, dbs[0]))
    return result


def active_databases(config: Config) -> list[Database]:
    return [db for var, db in candidate_databases(config) if db.db_id in config.databases]


def read_ini_contents(contents: str):
    parser = configparser.ConfigParser(inline_comment_prefixes=(';', '#'))
    parser.read_string(contents)
    return parser
