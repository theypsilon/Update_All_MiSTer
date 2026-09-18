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

from dataclasses import dataclass
from typing import Optional

from update_all.config import Config
from update_all.databases import DB_ID_DISTRIBUTION_MISTER, ALL_DB_IDS, all_dbs, MANUALS_DB_ID_PREFIX, ARTWORK_DB_ID_PREFIX
from update_all.downloader_fingerprints import read_installed_db_ids
from update_all.downloader_service import DownloaderService
from update_all.file_system import FileSystem
from update_all.ini_repository import IniRepository
from update_all.logger import Logger
from update_all.other import GenericProvider


class DatabaseManagerService:
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

    def list_installed_dbs(self) -> Optional[list['InstalledDb']]:
        config = self._config_provider.get()
        return_code, output = self._downloader_service.read_downloader_command_output(
            config,
            self._ini_repository.downloader_ini_standard_path(),
            ['--list-dbs', 'all'],
        )
        if return_code != 0:
            self._logger.debug('Downloader could not list the installed databases')
            self._logger.debug(output)
            return None

        # Downloader reports ids lowercased; known databases get their canonical spelling and title back.
        known_dbs = {db_id.lower(): dbs[0] for db_id, dbs in all_dbs(config.mirror).databases_by_ids().items()}
        excluded = {DB_ID_DISTRIBUTION_MISTER.lower(), ALL_DB_IDS['UPDATE_ALL_MISTER'].lower()}
        result = []
        for installed in installed_dbs_from_ltsv(output):
            lower_id = installed.db_id.lower()
            if lower_id in excluded:
                continue
            known = known_dbs.get(lower_id)
            result.append(InstalledDb(known.db_id, known.title, installed.description, installed.configured, installed.db_url) if known is not None else installed)
        return sorted(result, key=_list_priority)

    def update(self, db_id: str) -> int:
        return self._downloader_service.execute_downloader_command(
            self._config_provider.get(),
            self._ini_repository.downloader_ini_standard_path(),
            ['--run-only', db_id],
            None,
        )

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
            None,
        )

        if return_code == 0:
            for db_id in selected_db_ids:
                config.set_database_enabled(db_id, False)

        return return_code


@dataclass(frozen=True)
class InstalledDb:
    db_id: str
    title: str
    description: str
    configured: bool
    db_url: str


def _list_priority(db: InstalledDb) -> int:
    lower_id = db.db_id.lower()
    return 2 if lower_id.startswith(MANUALS_DB_ID_PREFIX) else 1 if lower_id.startswith(ARTWORK_DB_ID_PREFIX) else 0


def installed_dbs_from_ltsv(output: str) -> list[InstalledDb]:
    configured: dict[str, tuple[str, str]] = {}
    installed_ids: list[str] = []
    for line in output.splitlines():
        fields = line.split('\t')
        if fields[0] != 'DLP1':
            continue
        db_id = _ltsv_field(fields, 'db')
        if not db_id:
            continue
        if 'event:installed_db' in fields:
            installed_ids.append(db_id)
        elif 'event:configured_db' in fields:
            configured[db_id.lower()] = (_ltsv_field(fields, 'description'), _ltsv_field(fields, 'url'))
    result = []
    for db_id in installed_ids:
        description, db_url = configured.get(db_id.lower(), ('', ''))
        result.append(InstalledDb(db_id, db_id, description, db_id.lower() in configured, db_url))
    return result


def _ltsv_field(fields: list[str], key: str) -> str:
    prefix = f'{key}:'
    return next((field[len(prefix):] for field in fields if field.startswith(prefix)), '')
