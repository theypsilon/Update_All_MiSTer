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
from typing import Callable, Tuple

from update_all.constants import FILE_MiSTer_ini, FILE_MiSTer_ini_update_all_backup
from update_all.file_system import FileSystem
from update_all.logger import Logger


FILE_mister_ini_pending = f'.{FILE_MiSTer_ini}.new'
FILE_mister_ini_backup_pending = f'{FILE_MiSTer_ini_update_all_backup}.new'


class MisterIniRepository:
    def __init__(self, file_system: FileSystem, logger: Logger):
        self._file_system = file_system
        self._logger = logger

    def ensure_mister_ini_key(
            self,
            section: str,
            key: str,
            value: str,
            create_if_missing: bool = False,
            replace_existing: bool = True,
            prepend_section: bool = False,
    ) -> Tuple[bool, str]:
        return self._update_mister_ini(
            lambda contents: _ensure_mister_ini_key(
                contents,
                section,
                key,
                value,
                replace_existing=replace_existing,
                prepend_section=prepend_section,
            ),
            create_if_missing=create_if_missing,
        )

    def remove_mister_ini_key(
            self,
            section: str,
            key: str,
            value: str,
            remove_empty_section: bool = False,
    ) -> Tuple[bool, str]:
        return self._update_mister_ini(
            lambda contents: _remove_mister_ini_key(
                contents,
                section,
                key,
                value,
                remove_empty_section=remove_empty_section,
            ),
        )

    def _update_mister_ini(
            self,
            transform: Callable[[str], str],
            create_if_missing: bool = False,
    ) -> Tuple[bool, str]:
        try:
            if not self._file_system.is_file(FILE_MiSTer_ini):
                if not create_if_missing:
                    return False, ''

                current_contents = ''
                backup_current = False
            else:
                current_contents = self._file_system.read_file_contents(FILE_MiSTer_ini)
                backup_current = True

            updated_contents = transform(current_contents)
            if updated_contents == current_contents:
                return False, current_contents

            # Stage to MiSTer.ini.new, fsync it, sanity-check the staged contents as seen
            # through the filesystem, then atomically replace MiSTer.ini and fsync the
            # parent directory so the rename is durable.
            #
            # The read-back may be satisfied from the Linux page cache; it is not a raw
            # physical-media verification. On exFAT / sudden power loss, this is best-effort
            # crash hardening, not an absolute guarantee against filesystem-level corruption.
            self._file_system.write_file_contents(FILE_mister_ini_pending, updated_contents)
            self._file_system.fsync(FILE_mister_ini_pending)

            on_disk = self._file_system.read_file_contents(FILE_mister_ini_pending)
            if on_disk != updated_contents:
                self._logger.print(
                    f'ERROR! Refusing to update {FILE_MiSTer_ini}: '
                    f'verification of {FILE_mister_ini_pending} did not match expected contents'
                )
                self._safe_unlink_pending()
                return False, current_contents

            if backup_current:
                self._write_mister_ini_backup()

            self._file_system.move(FILE_mister_ini_pending, FILE_MiSTer_ini)
            self._file_system.fsync_parent_dir(FILE_MiSTer_ini)
            return True, updated_contents
        except Exception:
            self._safe_unlink_pending()
            raise

    def _write_mister_ini_backup(self) -> None:
        try:
            self._file_system.copy(FILE_MiSTer_ini, FILE_mister_ini_backup_pending)
            self._file_system.fsync(FILE_mister_ini_backup_pending)
            self._file_system.move(FILE_mister_ini_backup_pending, FILE_MiSTer_ini_update_all_backup)
            self._file_system.fsync_parent_dir(FILE_MiSTer_ini_update_all_backup)
        except Exception:
            self._file_system.unlink(FILE_mister_ini_backup_pending, verbose=False)
            raise

    def _safe_unlink_pending(self) -> None:
        try:
            self._file_system.unlink(FILE_mister_ini_pending, verbose=False)
        except Exception as e:
            self._logger.debug(f'Could not remove stale {FILE_mister_ini_pending}')
            self._logger.debug(e)


def _ensure_mister_ini_key(
        contents: str,
        section: str,
        key: str,
        value: str,
        replace_existing: bool,
        prepend_section: bool,
) -> str:
    key_line = f'{key}={value}\n'
    if contents == '':
        return f'[{section}]\n{key_line}'

    lines = contents.splitlines(keepends=True)
    section_range = _find_section_range(lines, section)
    if section_range is None:
        return _add_mister_ini_section(contents, section, key_line, prepend_section)

    section_start, section_end = section_range
    key_indexes = []
    for index, parsed_key, parsed_value in _iter_mister_ini_key_values(lines, section_start + 1, section_end):
        if not _mister_ini_names_equal(parsed_key, key):
            continue

        if _mister_ini_values_equal(parsed_value, value):
            return contents

        key_indexes.append(index)

    if len(key_indexes) > 0 and replace_existing:
        lines[key_indexes[0]] = key_line
        return ''.join(lines)

    insertion_index = _section_key_insertion_index(lines, section_start, section_end)
    _ensure_previous_line_has_newline(lines, insertion_index - 1)
    lines.insert(insertion_index, key_line)
    return ''.join(lines)


def _remove_mister_ini_key(
        contents: str,
        section: str,
        key: str,
        value: str,
        remove_empty_section: bool,
) -> str:
    if contents == '':
        return contents

    lines = contents.splitlines(keepends=True)
    section_range = _find_section_range(lines, section)
    if section_range is None:
        return contents

    section_start, section_end = section_range
    indexes_to_remove = [
        index
        for index, parsed_key, parsed_value in _iter_mister_ini_key_values(lines, section_start + 1, section_end)
        if _mister_ini_names_equal(parsed_key, key) and _mister_ini_values_equal(parsed_value, value)
    ]
    if len(indexes_to_remove) == 0:
        return contents

    for index in reversed(indexes_to_remove):
        del lines[index]

    section_end -= len(indexes_to_remove)
    if remove_empty_section and not _mister_ini_section_has_meaningful_lines(lines[section_start + 1:section_end]):
        del lines[section_start:section_end]
        _remove_trailing_blank_lines(lines)

    return ''.join(lines)


def _add_mister_ini_section(contents: str, section: str, key_line: str, prepend: bool) -> str:
    block = f'[{section}]\n{key_line}'
    if contents == '':
        return block

    normalized = contents.rstrip('\r\n')
    return f'{block}\n{contents}' if prepend else f'{normalized}\n\n{block}'


def _find_section_range(lines, section: str):
    for section_start, line in enumerate(lines):
        if _is_mister_ini_section(line, section):
            break
    else:
        return None

    section_end = section_start + 1
    while section_end < len(lines) and _mister_ini_section_name(lines[section_end]) is None:
        section_end += 1
    return section_start, section_end


def _section_key_insertion_index(lines, section_start: int, section_end: int) -> int:
    insertion_index = section_end
    while insertion_index > section_start + 1 and _line_body(lines[insertion_index - 1]).strip() == '':
        insertion_index -= 1
    return insertion_index


def _mister_ini_section_has_meaningful_lines(lines) -> bool:
    return any(
        stripped != '' and not stripped.startswith((';', '#'))
        for stripped in (_line_body(line).strip() for line in lines)
    )


def _mister_ini_section_name(line: str):
    parsed_line = _line_body(line).lstrip(' \t').split(';', 1)[0].rstrip(' \t')
    return parsed_line[1:].split(']', 1)[0] if parsed_line.startswith('[') else None


def _is_mister_ini_section(line: str, section: str) -> bool:
    section_name = _mister_ini_section_name(line)
    return section_name is not None and _mister_ini_section_names_equal(section_name, section)


def _mister_ini_key_value(line: str):
    match = re.match(r'^\s*([^=;#]+?)\s*=\s*(.*?)\s*(?:[;#].*)?$', _line_body(line))
    return None if match is None else (match.group(1).strip(), match.group(2).strip())


def _iter_mister_ini_key_values(lines, start: int, end: int):
    for index in range(start, end):
        parsed_key_value = _mister_ini_key_value(lines[index])
        if parsed_key_value is not None:
            yield index, parsed_key_value[0], parsed_key_value[1]


def _mister_ini_names_equal(a: str, b: str) -> bool:
    return a.strip().lower() == b.strip().lower()


def _mister_ini_section_names_equal(a: str, b: str) -> bool:
    return a.lower() == b.lower()


def _mister_ini_values_equal(a: str, b: str) -> bool:
    return re.sub(r'\s+', '', a).lower() == re.sub(r'\s+', '', b).lower()


def _line_body(line: str) -> str:
    return line.rstrip('\r\n')


def _ensure_previous_line_has_newline(lines, index: int) -> None:
    if index >= 0 and not lines[index].endswith(('\n', '\r')):
        lines[index] += '\n'


def _remove_trailing_blank_lines(lines) -> None:
    while len(lines) > 0 and _line_body(lines[-1]).strip() == '':
        lines.pop()
