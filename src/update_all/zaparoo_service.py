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

from update_all.constants import FILE_MiSTer_ini, FILE_MiSTer_ini_update_all_backup, FILE_lastcore_dat
from update_all.file_system import FileSystem
from update_all.logger import Logger


FILE_zaparoo_frontend = 'zaparoo/MiSTer_Zaparoo'
FILE_zaparoo_mister_ini_pending = f'.{FILE_MiSTer_ini}.new'
FILE_zaparoo_mister_ini_backup_pending = f'{FILE_MiSTer_ini_update_all_backup}.new'
ZAPAROO_FRONTEND_MAIN_LINE = f'main={FILE_zaparoo_frontend}\n'


class ZaparooService:
    def __init__(self, file_system: FileSystem, logger: Logger):
        self._file_system = file_system
        self._logger = logger
        self._frontend_activation_applied = False

    def frontend_activation_applied(self) -> bool:
        return self._frontend_activation_applied

    def set_frontend_active(self, active: bool) -> None:
        if active:
            self._enable_frontend_active()
        else:
            self._disable_frontend_active()

    def _enable_frontend_active(self) -> None:
        if not self._file_system.is_file(FILE_zaparoo_frontend):
            return

        try:
            self._apply_frontend_activation()
        except Exception as e:
            self._logger.print(
                f'ERROR! Could not activate Zaparoo frontend in {FILE_MiSTer_ini}'
            )
            self._logger.debug(e)
            self._safe_unlink_pending()

    def _disable_frontend_active(self) -> None:
        try:
            self._apply_frontend_deactivation()
        except Exception as e:
            self._logger.print(
                f'ERROR! Could not remove Zaparoo frontend from {FILE_MiSTer_ini}'
            )
            self._logger.debug(e)
            self._safe_unlink_pending()

    def _apply_frontend_activation(self) -> None:
        mister_ini_exists = self._file_system.is_file(FILE_MiSTer_ini)
        current_contents = (
            self._file_system.read_file_contents(FILE_MiSTer_ini)
            if mister_ini_exists
            else ''
        )
        updated_contents = keep_zaparoo_frontend_active_in_mister_ini(current_contents)

        if not self._write_mister_ini_if_changed(current_contents, updated_contents, backup_current=mister_ini_exists):
            return

        self._frontend_activation_applied = True

    def _apply_frontend_deactivation(self) -> None:
        if not self._file_system.is_file(FILE_MiSTer_ini):
            return

        current_contents = self._file_system.read_file_contents(FILE_MiSTer_ini)
        updated_contents = remove_zaparoo_frontend_active_from_mister_ini(current_contents)

        if self._write_mister_ini_if_changed(current_contents, updated_contents, backup_current=True):
            self._frontend_activation_applied = False
            if has_bootcore_lastcore(current_contents):
                self._file_system.unlink(FILE_lastcore_dat, verbose=False)

    def _write_mister_ini_if_changed(self, current_contents: str, updated_contents: str, backup_current: bool) -> bool:
        if mister_ini_contents_equivalent(updated_contents, current_contents):
            return False

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
            return False

        if backup_current:
            self._write_mister_ini_backup()

        self._file_system.move(FILE_zaparoo_mister_ini_pending, FILE_MiSTer_ini)
        self._file_system.fsync_parent_dir(FILE_MiSTer_ini)
        return True

    def _write_mister_ini_backup(self) -> None:
        try:
            self._file_system.copy(FILE_MiSTer_ini, FILE_zaparoo_mister_ini_backup_pending)
            self._file_system.fsync(FILE_zaparoo_mister_ini_backup_pending)
            self._file_system.move(FILE_zaparoo_mister_ini_backup_pending, FILE_MiSTer_ini_update_all_backup)
            self._file_system.fsync_parent_dir(FILE_MiSTer_ini_update_all_backup)
        except Exception:
            self._file_system.unlink(FILE_zaparoo_mister_ini_backup_pending, verbose=False)
            raise

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


def remove_zaparoo_frontend_active_from_mister_ini(contents: str) -> str:
    if contents == '':
        return contents

    lines = contents.splitlines(keepends=True)
    section_range = _find_mister_section_range(lines)

    if section_range is None:
        return contents

    section_start, section_end = section_range
    zaparoo_main_line_indexes = []
    for index in range(section_start + 1, section_end):
        value = _main_value(lines[index])
        if value is not None and value.lower() == FILE_zaparoo_frontend.lower():
            zaparoo_main_line_indexes.append(index)

    if len(zaparoo_main_line_indexes) == 0:
        return contents

    for index in reversed(zaparoo_main_line_indexes):
        del lines[index]

    return ''.join(lines)


def has_bootcore_lastcore(contents: str) -> bool:
    for line in contents.splitlines():
        value = _bootcore_value(line)
        if value is not None and re.sub(r'\s+', '', value).lower() == 'lastcore':
            return True

    return False


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
    return _ini_value(line, 'main')


def _bootcore_value(line):
    return _ini_value(line, 'bootcore')


def _ini_value(line, name):
    match = re.match(rf'^\s*{re.escape(name)}\s*=\s*(.*?)\s*(?:[;#].*)?$', _line_body(line), re.IGNORECASE)
    return match.group(1).strip() if match is not None else None


def _line_body(line):
    return line.rstrip('\r\n')


def _ensure_previous_line_has_newline(lines, index):
    if index >= 0 and not lines[index].endswith(('\n', '\r')):
        lines[index] += '\n'
