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

from update_all.constants import FILE_MiSTer_ini, FILE_lastcore_dat
from update_all.file_system import FileSystem
from update_all.logger import Logger
from update_all.mister_ini_repository import (
    FILE_mister_ini_backup_pending,
    FILE_mister_ini_pending,
    MisterIniRepository,
)


FILE_zaparoo_frontend = 'zaparoo/MiSTer_Zaparoo'
FILE_zaparoo_mister_ini_pending = FILE_mister_ini_pending
FILE_zaparoo_mister_ini_backup_pending = FILE_mister_ini_backup_pending
ZAPAROO_FRONTEND_MISTER_INI_SECTIONS = ('mister', 'menu')


class ZaparooService:
    def __init__(
            self,
            file_system: FileSystem,
            logger: Logger,
            mister_ini_repository: MisterIniRepository,
    ):
        self._file_system = file_system
        self._logger = logger
        self._mister_ini_repository = mister_ini_repository
        self._frontend_activation_applied = False

    def frontend_activation_applied(self) -> bool:
        return self._frontend_activation_applied

    def set_frontend_active(self, active: bool) -> None:
        if active:
            self._enable_frontend_active()
        else:
            self._disable_frontend_active()

    def is_frontend_active(self) -> bool:
        return self._mister_ini_repository.has_mister_ini_key(
            ZAPAROO_FRONTEND_MISTER_INI_SECTIONS,
            'main',
            FILE_zaparoo_frontend,
        )

    def would_change_frontend_active_in_mister_ini(self, active: bool) -> bool:
        if active:
            if self.is_frontend_active():
                return False

            changed, _contents = self._mister_ini_repository.ensure_mister_ini_key(
                'mister',
                'main',
                FILE_zaparoo_frontend,
                create_if_missing=True,
                prepend_section=True,
                dry_run=True,
            )
            return changed

        changed, _contents = self._mister_ini_repository.remove_mister_ini_key_from_sections(
            ZAPAROO_FRONTEND_MISTER_INI_SECTIONS,
            'main',
            FILE_zaparoo_frontend,
            dry_run=True,
        )
        return changed

    def _enable_frontend_active(self) -> None:
        try:
            if self.is_frontend_active():
                return

            changed, _mister_ini = self._mister_ini_repository.ensure_mister_ini_key(
                'mister',
                'main',
                FILE_zaparoo_frontend,
                create_if_missing=True,
                prepend_section=True,
            )
            if changed:
                self._frontend_activation_applied = True
        except Exception as e:
            self._logger.print(
                f'ERROR! Could not activate Zaparoo frontend in {FILE_MiSTer_ini}'
            )
            self._logger.debug(e)

    def _disable_frontend_active(self) -> None:
        try:
            changed, mister_ini = self._mister_ini_repository.remove_mister_ini_key_from_sections(
                ZAPAROO_FRONTEND_MISTER_INI_SECTIONS,
                'main',
                FILE_zaparoo_frontend,
            )
            if changed:
                self._frontend_activation_applied = False
                if _has_lastcore_bootcore(mister_ini):
                    self._file_system.unlink(FILE_lastcore_dat, verbose=False)
        except Exception as e:
            self._logger.print(
                f'ERROR! Could not remove Zaparoo frontend from {FILE_MiSTer_ini}'
            )
            self._logger.debug(e)


def _has_lastcore_bootcore(contents: str) -> bool:
    for line in contents.splitlines():
        match = re.match(r'^\s*bootcore\s*=\s*(.*?)\s*(?:[;#].*)?$', line, re.IGNORECASE)
        if match is not None and re.sub(r'\s+', '', match.group(1)).lower() == 'lastcore':
            return True

    return False
