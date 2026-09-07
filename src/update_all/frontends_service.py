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


class FrontendsService:
    """Frontend behavior that cannot be expressed as a MiSTer.ini edit.

    Today that is one thing: dropping a stale lastcore.dat when a frontend with its own
    menu core is switched off. With bootcore=lastcore, Main records the name of every
    core it starts and boots it next time, excluding only the literal menu.rbf. A
    frontend whose Main build starts the menu from a differently named core file
    (Zaparoo's zaparoo/menu_zaparoo.rbf) therefore gets that menu core recorded, and
    stock Main would boot it instead of its own menu while the files are still
    installed. Frontends running on the stock menu.rbf, like Degauss, never hit this
    and do not need this cleanup.
    """

    def __init__(
            self,
            file_system: FileSystem,
            logger: Logger,
    ):
        self._file_system = file_system
        self._logger = logger

    def on_frontend_deleted(self, changed: bool, contents: str) -> None:
        """Post-apply hook for such a frontend's mister_ini_del edit."""
        if not changed:
            return

        if _has_lastcore_bootcore(contents):
            self._file_system.unlink(FILE_lastcore_dat, verbose=False)


def _has_lastcore_bootcore(contents: str) -> bool:
    for line in contents.splitlines():
        match = re.match(r'^\s*bootcore\s*=\s*(.*?)\s*(?:[;#].*)?$', line, re.IGNORECASE)
        if match is not None and re.sub(r'\s+', '', match.group(1)).lower() == 'lastcore':
            return True

    return False
