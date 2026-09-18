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
from typing import Dict, Iterable, List, Tuple

from update_all.downloader_ini_document import DownloaderIniDocument, IniSections, parser_sections
from update_all.file_system import FileSystem

DROP_IN_INI_FOLDER: str = 'downloader'

class IniFile:
    def __init__(self, document: DownloaderIniDocument):
        self.parser = document.parser()
        self.repeated_sections = document.repeated_sections
        self.section_lines = {section.name: section.line for section in document.sections.values()}

    def sections(self, literal_percent: bool = False) -> IniSections:
        """Use raw values on interpolation errors only when literal_percent is enabled."""
        return parser_sections(self.parser, literal_percent)


class DownloaderIniReader:
    """Report duplicate sections and propagate read/parse errors for callers to handle."""

    def __init__(self, file_system: FileSystem):
        self._file_system = file_system

    def read_ini_file(self, path: str) -> IniFile:
        return read_ini(self._file_system.read_file_contents(path))

    def drop_in_ini_paths(self, base_path: str) -> List[str]:
        """Relative paths of the ini files that Downloader picks up besides downloader.ini, in its loading order:
        the non-hidden '{base_path}/downloader/*.ini' sorted, and then '{base_path}/downloader_*.ini' sorted."""
        result: List[str] = []
        drop_in_folder = f'{base_path}/{DROP_IN_INI_FOLDER}'
        if self._file_system.is_folder(drop_in_folder):
            for name in self._file_system.list_file_names_in_folder(drop_in_folder):
                if name.startswith('.'):
                    continue
                if name.lower().endswith('.ini'):
                    result.append(f'{DROP_IN_INI_FOLDER}/{name}')

        for name in self._file_system.list_file_names_in_folder(base_path):
            lower = name.lower()
            if lower.startswith('downloader_') and lower.endswith('.ini'):
                result.append(name)

        return sort_drop_in_ini_paths(result)


def sort_drop_in_ini_paths(paths: Iterable[str]) -> List[str]:
    return sorted(paths, key=lambda path: (not path.startswith(DROP_IN_INI_FOLDER + '/'), path))


def read_ini(contents: str) -> IniFile:
    """When a section is repeated, in any casing, only its first definition is read and the rest get reported.
    Malformed contents raise the configparser error."""
    return IniFile(DownloaderIniDocument(contents))


def read_ini_contents(contents: str) -> configparser.ConfigParser:
    return read_ini(contents).parser


def first_definitions(files: Iterable[Tuple[str, IniSections]]) -> Tuple[IniSections, Dict[str, List[str]]]:
    """Return first definitions and all source paths in the supplied loading order."""
    sections: IniSections = {}
    sources: Dict[str, List[str]] = {}
    for path, file_sections in files:
        for section_id, section in file_sections.items():
            if section_id not in sections:
                sections[section_id] = section
            sources.setdefault(section_id, []).append(path)

    return sections, sources
