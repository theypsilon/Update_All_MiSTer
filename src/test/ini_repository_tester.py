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

import configparser
import json
from contextlib import contextmanager
from pathlib import PurePosixPath
from textwrap import dedent
from typing import Any, Dict, List, Optional
from unittest.mock import patch

from test.downloader_ini_reader_tester import DownloaderIniReaderTester
from test.fake_filesystem import FileSystemFactory
from test.logger_tester import LoggerSpy
from test.spy_os_utils import SpyOsUtils
from update_all.constants import DOWNLOADER_INI_STANDARD_PATH, DOWNLOADER_STORE_STANDARD_PATH, MEDIA_FAT
from update_all.file_system import FileSystem
from update_all.ini_parser import IniParser
from update_all.ini_repository import IniRepository
from update_all.logger import Logger
from update_all.os_utils import OsUtils


class IniRepositoryTester(IniRepository):
    def __init__(self, file_system: FileSystem = None, os_utils: OsUtils = None,
                 logger: Logger = None, files: Optional[Dict[str, str]] = None,
                 downloader_store: Optional[Dict[str, Any]] = None,
                 base_path: Optional[str] = MEDIA_FAT):
        self.base_path = base_path or MEDIA_FAT
        files = dict(files or {})
        if downloader_store is not None:
            files[DOWNLOADER_STORE_STANDARD_PATH] = json.dumps(downloader_store)
        self._fixture_file_names = {self.file_path(path).lower(): PurePosixPath(path).name for path in files}
        self.file_system = file_system or FileSystemFactory.from_state(
            files={path: {'content': dedent(contents).lstrip('\n')} for path, contents in files.items()},
            folders={str(PurePosixPath(path).parent) for path in files if '/' in path},
            base_path=self.base_path,
        ).create_for_system_scope()
        self.logger = logger or LoggerSpy()
        super().__init__(self.logger, self.file_system, os_utils or SpyOsUtils(), DownloaderIniReaderTester(file_system=self.file_system))
        if base_path is not None:
            self.initialize_downloader_ini_base_path(base_path)

    def file_path(self, filename: str) -> str:
        return str(PurePosixPath(self.base_path) / filename)

    def file_exists(self, filename: str) -> bool:
        return self.file_system.is_file(self.file_path(filename))

    def write_file(self, filename: str, contents: str) -> None:
        self.file_system.write_file_contents(self.file_path(filename), contents)

    def remove_file(self, filename: str) -> None:
        self.file_system.unlink(self.file_path(filename))

    @contextmanager
    def case_preserving_file_names(self):
        """Keep case-insensitive lookups, but list fixture filenames in their original spelling."""
        list_names = self.file_system.list_file_names_in_folder

        def names_in_folder(folder):
            return [self._fixture_file_names.get(str(PurePosixPath(folder) / name).lower(), name)
                    for name in list_names(folder)]

        with patch.object(self.file_system, 'list_file_names_in_folder', side_effect=names_in_folder):
            yield

    @contextmanager
    def unreadable(self, filename: str):
        read_contents = self.file_system.read_file_contents

        def read(path):
            if self.file_path(path).lower() == self.file_path(filename).lower():
                raise PermissionError(f'Cannot read {filename}')
            return read_contents(path)

        with patch.object(self.file_system, 'read_file_contents', side_effect=read):
            yield

    def downloader_sections(self) -> Dict[str, IniParser]:
        return {name: IniParser(values) for name, values in self.get_downloader_ini(cached=False).items()}

    def downloader_store(self) -> Dict[str, Any]:
        return self.file_system.load_dict_from_file(self.downloader_store_standard_path())

    def ini_contents(self, filename: str = DOWNLOADER_INI_STANDARD_PATH) -> str:
        return self.file_system.read_file_contents(self.file_path(filename))

    def parsed_ini(self, filename: str = DOWNLOADER_INI_STANDARD_PATH) -> configparser.ConfigParser:
        # Inspect the actual output independently: the production reader would
        # hide repeated sections and could conceal a broken write.
        parser = configparser.ConfigParser(inline_comment_prefixes=(';', '#'))
        parser.read_string(self.ini_contents(filename))
        return parser

    def section_values(self, section_name: str, filename: str = DOWNLOADER_INI_STANDARD_PATH) -> Dict[str, str]:
        parser = self.parsed_ini(filename)
        matches = [name for name in parser.sections() if name.lower() == section_name.lower()]
        if len(matches) != 1:
            raise AssertionError(f'Expected exactly one [{section_name}] section, found {matches}')
        return dict(parser[matches[0]])


def removed_section_logs(logger: LoggerSpy) -> List[str]:
    return [line for line in logger.debug_lines
            if line.startswith(('Repeated section removed from ', 'Sections removed from '))]


def repeated_section_warnings(logger: LoggerSpy) -> List[str]:
    return [line for line in logger.print_lines
            if line.startswith('WARNING! Section [') and 'was repeated' in line]
