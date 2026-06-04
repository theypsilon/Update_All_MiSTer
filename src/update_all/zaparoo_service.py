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

import re

from update_all.constants import FILE_MiSTer_ini
from update_all.file_system import FileSystem
from update_all.logger import Logger


FILE_zaparoo_frontend = 'zaparoo/MiSTer_Zaparoo'
FILE_zaparoo_mister_ini_pending = f'.{FILE_MiSTer_ini}.new'
ZAPAROO_FRONTEND_MAIN_LINE = f'main={FILE_zaparoo_frontend}\n'


class ZaparooService:
    def __init__(self, file_system: FileSystem, logger: Logger):
        self._file_system = file_system
        self._logger = logger
        self._zaparoo_frontend_enabled = False

    def zaparoo_frontend_enabled(self) -> bool:
        return self._zaparoo_frontend_enabled

    def keep_frontend_active(self) -> None:
        if not self._file_system.is_file(FILE_zaparoo_frontend):
            return

        try:
            self._keep_frontend_active()
        except Exception as e:
            self._logger.print(
                f'ERROR! Could not keep Zaparoo frontend active in {FILE_MiSTer_ini}'
            )
            self._logger.debug(e)
            self._safe_unlink_pending()

    def _keep_frontend_active(self) -> None:
        current_contents = (
            self._file_system.read_file_contents(FILE_MiSTer_ini)
            if self._file_system.is_file(FILE_MiSTer_ini)
            else ''
        )
        updated_contents = keep_zaparoo_frontend_active_in_mister_ini(current_contents)

        if mister_ini_contents_equivalent(updated_contents, current_contents):
            return

        # Stage to MiSTer.ini.new, fsync it, sanity-check the staged contents as seen
        # through the filesystem, then atomically replace MiSTer.ini and fsync the
        # parent directory so the rename is durable.
        #
        # The read-back may be satisfied from the Linux page cache; it is not a raw
        # physical-media verification. On exFAT / sudden power loss, this is best-effort
        # crash hardening, not an absolute guarantee against filesystem-level corruption.
        self._file_system.write_file_contents(FILE_zaparoo_mister_ini_pending, updated_contents)
        self._file_system.fsync(FILE_zaparoo_mister_ini_pending)

        on_disk = self._file_system.read_file_contents(FILE_zaparoo_mister_ini_pending)
        if on_disk != updated_contents:
            self._logger.print(
                f'ERROR! Refusing to update {FILE_MiSTer_ini}: '
                f'verification of {FILE_zaparoo_mister_ini_pending} did not match expected contents'
            )
            self._safe_unlink_pending()
            return

        self._file_system.move(FILE_zaparoo_mister_ini_pending, FILE_MiSTer_ini)
        self._file_system.fsync_parent_dir(FILE_MiSTer_ini)
        self._zaparoo_frontend_enabled = True

    def _safe_unlink_pending(self) -> None:
        try:
            self._file_system.unlink(FILE_zaparoo_mister_ini_pending, verbose=False)
        except Exception as e:
            self._logger.debug(f'Could not remove stale {FILE_zaparoo_mister_ini_pending}')
            self._logger.debug(e)


def mister_ini_contents_equivalent(a: str, b: str) -> bool:
    return _normalize_mister_ini_for_compare(a) == _normalize_mister_ini_for_compare(b)


def _normalize_mister_ini_for_compare(contents: str) -> str:
    return '\n'.join(re.sub(r'\s+', '', line).lower() for line in contents.splitlines())


def keep_zaparoo_frontend_active_in_mister_ini(contents: str) -> str:
    if contents == '':
        return f'[mister]\n{ZAPAROO_FRONTEND_MAIN_LINE}'

    lines = contents.splitlines(keepends=True)
    section_range = _find_mister_section_range(lines)

    if section_range is None:
        return _append_mister_section(contents)

    section_start, section_end = section_range
    main_line_indexes = []
    for index in range(section_start + 1, section_end):
        value = _main_value(lines[index])
        if value is None:
            continue

        if value.lower() == FILE_zaparoo_frontend.lower():
            return contents

        main_line_indexes.append(index)

    if len(main_line_indexes) > 0:
        lines[main_line_indexes[0]] = ZAPAROO_FRONTEND_MAIN_LINE
        return ''.join(lines)

    _ensure_previous_line_has_newline(lines, section_end - 1)
    lines.insert(section_end, ZAPAROO_FRONTEND_MAIN_LINE)
    return ''.join(lines)


def _append_mister_section(contents: str) -> str:
    separator = '' if contents.endswith(('\n', '\r')) else '\n'
    return f'{contents}{separator}[mister]\n{ZAPAROO_FRONTEND_MAIN_LINE}'


def _find_mister_section_range(lines):
    section_start = None
    for index, line in enumerate(lines):
        section_name = _section_name(line)
        if section_name is None:
            continue

        if section_start is not None:
            return section_start, index

        if section_name.lower() == 'mister':
            section_start = index

    if section_start is None:
        return None

    return section_start, len(lines)


def _section_name(line):
    match = re.match(r'^\s*\[\s*([^\]]+?)\s*]\s*(?:[;#].*)?$', _line_body(line))
    return match.group(1).strip() if match is not None else None


def _main_value(line):
    match = re.match(r'^\s*main\s*=\s*(.*?)\s*(?:[;#].*)?$', _line_body(line), re.IGNORECASE)
    return match.group(1).strip() if match is not None else None


def _line_body(line):
    return line.rstrip('\r\n')


def _ensure_previous_line_has_newline(lines, index):
    if index >= 0 and not lines[index].endswith(('\n', '\r')):
        lines[index] += '\n'
