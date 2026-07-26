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
import enum
import json
from typing import Optional

from update_all.cli_output_formatting import bold
from update_all.config import Config
from update_all.constants import BACKGROUND_JOBS_SOFT_TIMEOUT, FILE_settings_screen_model_json_zip, \
    FILE_update_all_self_update_resume, FILE_update_all_pyz
from update_all.databases import all_dbs, ALL_DB_IDS
from update_all.downloader_service import DownloaderService
from update_all.fetcher import Fetcher
from update_all.file_system import FileSystem
from update_all.ini_repository import IniRepository
from update_all.logger import Logger
from update_all.other import GenericProvider


_UPDATE_FILES = (FILE_update_all_pyz, FILE_settings_screen_model_json_zip)


@enum.unique
class UpdateAllResumePoint(enum.Enum):
    SETTINGS_SCREEN = 'settings_screen'
    AFTER_DOWNLOADER = 'after_downloader'


class UpdateAllSelfUpdateService:
    def __init__(
            self,
            config_provider: GenericProvider[Config],
            logger: Logger,
            file_system: FileSystem,
            ini_repository: IniRepository,
            downloader_service: DownloaderService,
            fetcher: Fetcher,
    ):
        self._config_provider = config_provider
        self._logger = logger
        self._file_system = file_system
        self._ini_repository = ini_repository
        self._downloader_service = downloader_service
        self._fetcher = fetcher

    def can_check_for_update(self) -> bool:
        config = self._config_provider.get()
        if config.skip_downloader:
            return False
        return all(self._file_system.is_file(path) for path in _UPDATE_FILES)

    def is_update_needed(
            self,
            expected_hashes: dict[str, str],
            installed_hashes: dict[str, str],
    ) -> bool:
        for path, expected_hash in expected_hashes.items():
            installed_hash = installed_hashes[path]
            if installed_hash != expected_hash:
                self._logger.debug(f'Early Update All check found a changed {path}: {installed_hash} != {expected_hash}')
                return True

        return False

    def fetch_expected_hashes(self) -> dict[str, str]:
        config = self._config_provider.get()
        update_all_db = all_dbs(config.mirror).UPDATE_ALL_MISTER
        status, data = self._fetcher.fetch(
            config.update_all_mister_db_url or update_all_db.db_url,
            timeout=BACKGROUND_JOBS_SOFT_TIMEOUT,
            retry=0,
        )
        if status != 200:
            raise RuntimeError(f'Could not fetch {update_all_db.db_id} database: HTTP {status}')

        manifest = json.loads(data)
        if not isinstance(manifest, dict) or manifest.get('db_id') != update_all_db.db_id:
            raise ValueError(f'Fetched database is not {update_all_db.db_id}')

        files = manifest.get('files')
        if not isinstance(files, dict):
            raise ValueError(f'{update_all_db.db_id} database has no files dictionary')

        expected_hashes = {}
        for path in _UPDATE_FILES:
            description = files.get(path)
            expected_hash = description.get('hash') if isinstance(description, dict) else None
            if not isinstance(expected_hash, str) or not expected_hash.strip():
                raise ValueError(f'{update_all_db.db_id} database has no hash for {path}')
            expected_hashes[path] = expected_hash.strip().lower()

        return expected_hashes

    def hash_installed_files(self) -> dict[str, str]:
        return {
            path: self._file_system.hash(path).lower()
            for path in _UPDATE_FILES
        }

    def try_update_before_settings_and_prepare_restart(self) -> bool:
        try:
            config = self._config_provider.get()
            self._logger.print()
            self._logger.print(bold('A NEW VERSION OF UPDATE ALL IS AVAILABLE!'))
            self._logger.print()
            self._logger.print('Installing it now.')
            self._logger.print('The update process will continue automatically...')
            self._logger.print()
            return_code = self._downloader_service.execute_downloader_command(
                config,
                self._ini_repository.downloader_ini_standard_path(),
                ['--run-only', ALL_DB_IDS['UPDATE_ALL_MISTER']],
            )
            if return_code != 0:
                self._logger.debug(f'Early Update All Downloader run failed with error code {return_code}.')
                return False

            self._file_system.write_file_contents(
                FILE_update_all_self_update_resume,
                UpdateAllResumePoint.SETTINGS_SCREEN.value,
            )
            self._logger.debug('Early Update All update completed; restart destination: settings-screen.')
            return True
        except Exception as e:
            self._logger.debug('Could not complete the early Update All Downloader run.')
            self._logger.debug(e)
            return False

    def try_prepare_restart_after_downloader(self) -> bool:
        try:
            self._file_system.write_file_contents(
                FILE_update_all_self_update_resume,
                UpdateAllResumePoint.AFTER_DOWNLOADER.value,
            )
            self._logger.debug('Update All was updated by the standard Downloader; restart destination: after-downloader.')
            return True
        except Exception as e:
            self._logger.debug('Could not prepare the restart after the standard Downloader updated Update All.')
            self._logger.debug(e)
            return False

    def take_resume_point(self) -> Optional[UpdateAllResumePoint]:
        try:
            if not self._file_system.is_file(FILE_update_all_self_update_resume):
                return None
            resume_point = self._file_system.read_file_contents(FILE_update_all_self_update_resume)
        except Exception as e:
            self._logger.debug('Could not read the early Update All resume point.')
            self._logger.debug(e)
            self.remove_resume_point()
            return None

        try:
            parsed_resume_point = UpdateAllResumePoint(resume_point)
        except ValueError:
            self._logger.debug(f'Ignoring unknown early Update All resume point: {resume_point}')
            self.remove_resume_point()
            return None

        # Resume markers are one-shot. If consumption cannot be confirmed, resume before Downloader.
        if not self.remove_resume_point():
            return None
        return parsed_resume_point

    def remove_resume_point(self) -> bool:
        try:
            return self._file_system.unlink(FILE_update_all_self_update_resume, verbose=False)
        except Exception as e:
            self._logger.debug('Could not remove the early Update All resume point.')
            self._logger.debug(e)
            return False
