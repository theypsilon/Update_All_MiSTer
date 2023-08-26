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
import configparser
import io
import json
import re
from typing import Optional, Dict, List, Tuple, Any

from update_all.config import Config
from update_all.constants import DOWNLOADER_INI_STANDARD_PATH, ARCADE_ORGANIZER_INI, FILE_downloader_temp_ini
from update_all.databases import AllDBs, Database, db_distribution_mister_by_encc_forks, \
    db_jtcores_by_download_beta_cores, db_names_txt_by_locale, dbs_to_model_variables_pairs, db_arcade_names_txt_by_locale
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
            raise IniRepositoryInitializationError("DownloaderIniRepository needs to be initialized.")

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

    @staticmethod
    def _add_new_downloader_ini_changes(ini, config: Config) -> None:
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

            ini[db_id.lower()]['filter'] = filter_addition

        for db_id, beta_cores_active in [(AllDBs.JTCORES.db_id, config.download_beta_cores)]:
            if db_id not in config.databases or not beta_cores_active:
                continue

            lower_id = db_id.lower()
            filter_value = ini[lower_id].get('filter', '').strip().lower()
            if filter_value == '':
                ini[lower_id]['filter'] = '[MiSTer]'
            elif '!jtbeta' in filter_value:
                ini[lower_id]['filter'] = filter_value.replace('!jtbeta', '').strip()

    def _build_new_downloader_ini_contents(self, config: Config) -> Optional[str]:
        ini: Dict[str, Dict[str, str]] = self.get_downloader_ini(cached=False)
        before = json.dumps(ini)
        self._add_new_downloader_ini_changes(ini, config)
        after = json.dumps(ini)

        if before == after:
            return None

        db_ids = {db.db_id.lower(): db.db_id for _, db in candidate_databases(config)}

        ini_ast = IniAst(ini, db_ids)

        if self._file_system.is_file(self.downloader_ini_standard_path()):
            ini_contents = io.StringIO(self._file_system.read_file_contents(self.downloader_ini_standard_path()))
            ini_ast.process(ini_contents.readlines())

        parser = configparser.ConfigParser(inline_comment_prefixes=(';', '#'))
        for header, section_id in ini.items():
            if header in db_ids:
                header = db_ids[header]
            parser[header] = section_id

        with io.StringIO() as ss:
            if ini_ast.pre_section != '':
                ss.write(ini_ast.pre_section.strip() + '\n\n')
            if ini_ast.mister_section != '':
                ss.write(ini_ast.mister_section.strip() + '\n\n')
            parser.write(ss)
            if ini_ast.nomister_section != '':
                ss.write(ini_ast.nomister_section.strip() + '\n\n')
            ss.seek(0)
            return ss.read()


class IniAst:
    no_section = 0
    other_section = 1
    common_section = 2

    def __init__(self, ini: Dict[str, Any], db_ids: Dict[str, str]):
        self._ini = ini
        self._db_ids = db_ids
        self._state = self.no_section
        self.mister_section = ''
        self.nomister_section = ''
        self.pre_section = ''
        self._current_section = ']['
        self._section_order = ['][']
        self._section_lines = {'][': []}

    def _start_section(self, section: str):
        if section.lower() in self._db_ids:
            self._state = self.common_section
            section = self._db_ids[section.lower()]
        else:
            self._state = self.other_section

        self._current_section = section.lower()
        self._section_order.append(section.lower())
        self._section_lines[self._current_section] = self._section_lines.get(self._current_section, [])
        self._section_lines[self._current_section].append(f'[{section}]')
        self._add_line(f'[{section}]\n')

    def process(self, lines: List[str]) -> None:
        header_regex = re.compile('\s*\[([-_/a-zA-Z0-9]+)\].*', re.I)

        for line in lines:
            match = header_regex.match(line)
            if match is not None:
                self._start_section(match.group(1))
            else:
                self._add_line(line)
                line = line.strip('" \n\'')
                if line == '':
                    continue
                self._section_lines[self._current_section] = self._section_lines.get(self._current_section, [])
                self._section_lines[self._current_section].append(line)

    def print(self):
        file_content = ''
        for section in self._section_order:
            for line in self._section_lines[section]:
                file_content += line + '\n'
            if len(self._section_lines[section]) > 0:
                file_content += '\n'

        return file_content

    def _add_line(self, line: str):
        if self._state == self.no_section:
            self.pre_section += line
        elif self._state == self.common_section:
            pass
        elif self._state == self.other_section:
            if self._current_section in self._ini:
                self._ini.pop(self._current_section)

            if self._current_section.lower() == 'mister':
                self.mister_section += line
            else:
                self.nomister_section += line
        else:
            raise Exception("Wrong state: " + str(self._state))


def candidate_databases(config: Config) -> List[Tuple[str, Database]]:
    configurable_dbs = {
        'main_updater': db_distribution_mister_by_encc_forks(config.encc_forks),
        'jotego_updater': db_jtcores_by_download_beta_cores(config.download_beta_cores),
        'names_txt_updater': db_names_txt_by_locale(config.names_region, config.names_char_code, config.names_sort_code),
        'arcade_names_txt': db_arcade_names_txt_by_locale(config.names_region)
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


class IniRepositoryInitializationError(Exception):
    pass
