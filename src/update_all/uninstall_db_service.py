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

from update_all.config import Config
from update_all.downloader_fingerprints import read_installed_db_ids
from update_all.downloader_service import DownloaderService
from update_all.file_system import FileSystem
from update_all.ini_repository import IniRepository
from update_all.logger import Logger
from update_all.other import GenericProvider


class UninstallDbService:
    def __init__(
            self,
            ini_repository: IniRepository,
            config_provider: GenericProvider[Config],
            downloader_service: DownloaderService,
            file_system: FileSystem,
            logger: Logger,
    ):
        self._ini_repository = ini_repository
        self._config_provider = config_provider
        self._downloader_service = downloader_service
        self._file_system = file_system
        self._logger = logger

    def uninstall(self, db_ids: list[str], force: bool = False) -> int:
        config = self._config_provider.get()
        installed_db_ids = read_installed_db_ids(self._file_system, self._logger)
        selected_db_ids = [db_id for db_id in db_ids if db_id.lower() in installed_db_ids]

        if not selected_db_ids:
            return 0

        args = ['--uninstall', *selected_db_ids]
        if force:
            args.append('--force')

        return_code = self._downloader_service.execute_downloader_command(
            config,
            self._ini_repository.downloader_ini_standard_path(),
            args,
        )

        if return_code == 0:
            for db_id in selected_db_ids:
                config.set_database_enabled(db_id, False)

        return return_code
