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

from update_all.constants import FILE_lastcore_dat
from update_all.file_system import FileSystem
from update_all.logger import Logger


class ZaparooService:
    def __init__(
            self,
            file_system: FileSystem,
            logger: Logger,
    ):
        self._file_system = file_system
        self._logger = logger
        self._frontend_activation_applied = False

    def frontend_activation_applied(self) -> bool:
        return self._frontend_activation_applied

    def on_frontend_added(self, changed: bool, contents: str) -> None:
        """Post-apply hook for the Zaparoo frontend mister_ini_add edit.

        The MiSTer.ini write is handled by the generic mister_ini_add mechanism;
        this only tracks the "frontend enabled" signal shown in the outro.
        """
        if changed:
            self._frontend_activation_applied = True

    def on_frontend_deleted(self, changed: bool, contents: str) -> None:
        """Post-apply hook for the Zaparoo frontend mister_ini_del edit.

        Carries the residual behavior that cannot be expressed as an INI key: clearing
        the "frontend enabled" signal and dropping a stale lastcore.dat when the
        frontend is deactivated.
        """
        if not changed:
            return

        self._frontend_activation_applied = False
        if _has_lastcore_bootcore(contents):
            self._file_system.unlink(FILE_lastcore_dat, verbose=False)


def _has_lastcore_bootcore(contents: str) -> bool:
    for line in contents.splitlines():
        match = re.match(r'^\s*bootcore\s*=\s*(.*?)\s*(?:[;#].*)?$', line, re.IGNORECASE)
        if match is not None and re.sub(r'\s+', '', match.group(1)).lower() == 'lastcore':
            return True

    return False
