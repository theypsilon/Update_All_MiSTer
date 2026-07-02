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

from typing import Final, Optional

from update_all.constants import FILE_MiSTer_ini, MEDIA_FAT
from update_all.file_system import FileSystem
from update_all.logger import Logger
from update_all.mister_ini_repository import MisterIniRepository
from update_all.os_utils import OsUtils


RETROACHIEVEMENTS_CFG_PATH: Final[str] = f'{MEDIA_FAT}/retroachievements.cfg'
RETROACHIEVEMENTS_CFG_URL: Final[str] = 'https://raw.githubusercontent.com/odelot/Main_MiSTer/refs/heads/master/retroachievements.cfg'
RETROACHIEVEMENTS_MISTER_INI_SECTION: Final[str] = 'RA_*'
RETROACHIEVEMENTS_MISTER_INI_KEY: Final[str] = 'main'
RETROACHIEVEMENTS_MISTER_INI_VALUE: Final[str] = 'MiSTer_RA'


class RetroAchievementsService:
    def __init__(
            self,
            file_system: FileSystem,
            os_utils: OsUtils,
            logger: Logger,
            mister_ini_repository: MisterIniRepository,
    ):
        self._file_system = file_system
        self._os_utils = os_utils
        self._logger = logger
        self._mister_ini_repository = mister_ini_repository

    def prepare_enable(self) -> str:
        status = self.cfg_status()
        if status in ('missing_file', 'missing_password_field'):
            return 'installed' if self.install_cfg() else 'install_failed'

        return status

    def set_mister_ini_active(self, active: bool) -> None:
        if active:
            self._try_ensure_mister_ini_block()
        else:
            self._try_remove_mister_ini_block()

    def would_change_mister_ini_active(self, active: bool) -> bool:
        if active:
            changed, _contents = self._mister_ini_repository.ensure_mister_ini_key(
                RETROACHIEVEMENTS_MISTER_INI_SECTION,
                RETROACHIEVEMENTS_MISTER_INI_KEY,
                RETROACHIEVEMENTS_MISTER_INI_VALUE,
                create_if_missing=True,
                dry_run=True,
            )
            return changed

        changed, _contents = self._mister_ini_repository.remove_mister_ini_key(
            RETROACHIEVEMENTS_MISTER_INI_SECTION,
            RETROACHIEVEMENTS_MISTER_INI_KEY,
            RETROACHIEVEMENTS_MISTER_INI_VALUE,
            remove_empty_section=True,
            dry_run=True,
        )
        return changed

    def enable(self) -> str:
        return self.prepare_enable()

    def disable(self) -> None:
        pass

    def cfg_status(self) -> str:
        if not self._file_system.is_file(RETROACHIEVEMENTS_CFG_PATH):
            return 'missing_file'

        try:
            contents = self._file_system.read_file_contents(RETROACHIEVEMENTS_CFG_PATH)
        except Exception as e:
            self._logger.debug('Could not read RetroAchievements configuration file')
            self._logger.debug(e)
            return 'missing_password_field'

        password = self._cfg_password(contents)
        if password is None:
            return 'missing_password_field'
        if password == '':
            return 'missing_credentials'
        return 'ok'

    def install_cfg(self) -> bool:
        content = self._os_utils.download(RETROACHIEVEMENTS_CFG_URL)
        if content is None or len(content) == 0:
            return False

        try:
            self._file_system.write_file_contents(RETROACHIEVEMENTS_CFG_PATH, content.decode('utf-8'))
            return True
        except Exception as e:
            self._logger.debug('Could not install RetroAchievements configuration file')
            self._logger.debug(e)
            return False

    def _try_ensure_mister_ini_block(self) -> None:
        try:
            self._mister_ini_repository.ensure_mister_ini_key(
                RETROACHIEVEMENTS_MISTER_INI_SECTION,
                RETROACHIEVEMENTS_MISTER_INI_KEY,
                RETROACHIEVEMENTS_MISTER_INI_VALUE,
                create_if_missing=True,
            )
        except Exception as e:
            self._logger.print(f'ERROR! Could not update {FILE_MiSTer_ini} for RetroAchievements')
            self._logger.debug(e)

    def _try_remove_mister_ini_block(self) -> None:
        try:
            self._mister_ini_repository.remove_mister_ini_key(
                RETROACHIEVEMENTS_MISTER_INI_SECTION,
                RETROACHIEVEMENTS_MISTER_INI_KEY,
                RETROACHIEVEMENTS_MISTER_INI_VALUE,
                remove_empty_section=True,
            )
        except Exception as e:
            self._logger.print(f'ERROR! Could not remove RetroAchievements from {FILE_MiSTer_ini}')
            self._logger.debug(e)

    @staticmethod
    def _cfg_password(contents: str) -> Optional[str]:
        for line in contents.splitlines():
            stripped = line.strip()
            if stripped == '' or stripped.startswith('#') or '=' not in stripped:
                continue

            key, value = stripped.split('=', 1)
            if key.strip().lower() == 'password':
                return value.strip()

        return None
