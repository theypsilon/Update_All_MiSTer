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

from typing import Optional

from update_all.config import Config
from update_all.constants import FILE_JOTEGO_mra_pack_ini, FILE_downloader_run_signal, MEDIA_FAT
from update_all.databases import Database
from update_all.downloader_utils import prepare_latest_downloader
from update_all.file_system import FileSystem
from update_all.logger import Logger
from update_all.os_utils import OsUtils


class DownloaderService:
    def __init__(self, logger: Logger, file_system: FileSystem, os_utils: OsUtils):
        self._logger = logger
        self._file_system = file_system
        self._os_utils = os_utils
        self._temp_launchers: list[str] = []

    def execute_downloader(self, config: Config, downloader_ini_path: str, skip_linux_update: bool, logfile: Optional[str], default_db: Optional[Database], quiet: bool = False) -> int:
        env = self._prepare_env(config, downloader_ini_path, skip_linux_update, logfile, default_db)

        if not quiet:
            if default_db is None:
                self._logger.print('Running MiSTer Downloader')
            else:
                self._logger.print('Running ' + default_db.title)

        return self._run_with_fallbacks(env, quiet)

    def execute_downloader_command(self, config: Config, downloader_ini_path: str, args: list[str], quiet: bool = False) -> int:
        env = self._prepare_env(config, downloader_ini_path, config.skip_linux_update, None, None)
        return self._run_with_fallbacks(env, quiet, args=args)

    def _prepare_env(self, config: Config, downloader_ini_path: str, skip_linux_update: bool, logfile: Optional[str], default_db: Optional[Database]) -> dict[str, str]:
        ts = config.term_size
        oc = config.overscan_dim
        env = {
            'DOWNLOADER_INI_PATH': downloader_ini_path,
            'ALLOW_REBOOT': '0',
            'CURL_SSL': config.curl_ssl,
            'COLUMNS': str(ts.columns - oc.cols * 2),
            'LINES': str(ts.lines - oc.lines * 2),
        }
        if skip_linux_update:
            env['UPDATE_LINUX'] = 'false'
        if self._file_system.is_file(FILE_JOTEGO_mra_pack_ini):
            env['EXTRA_DROP_IN_DATABASE_FILES'] = FILE_JOTEGO_mra_pack_ini
        if logfile is not None:
            env['LOGFILE'] = logfile
        if default_db is not None:
            env['DEFAULT_DB_ID'] = default_db.db_id
            env['DEFAULT_DB_URL'] = default_db.db_url
        if not config.paths_from_downloader_ini and config.base_path != MEDIA_FAT:
            env['DEFAULT_BASE_PATH'] = config.base_path
        if config.not_mister:
            env['DEBUG'] = 'true'
        return env

    def _run_with_fallbacks(self, env: dict[str, str], quiet: bool, args: Optional[list[str]] = None) -> int:
        downloader_file = prepare_latest_downloader(self._os_utils, self._file_system, self._logger, consider_bin=True)
        if downloader_file is None:
            return 1

        self._temp_launchers.append(downloader_file)
        if not quiet:
            self._logger.print()

        return_code = self._os_utils.execute_process(downloader_file, env, quiet, args=args)
        if not self._file_system.is_file(FILE_downloader_run_signal):
            return return_code

        self._logger.print(f"WARNING! {downloader_file} didn't work as expected with error code {return_code}!\n")

        downloader_file = prepare_latest_downloader(self._os_utils, self._file_system, self._logger, consider_bin=False)
        if downloader_file is None:
            return 1

        self._temp_launchers.append(downloader_file)
        return_code = self._os_utils.execute_process(downloader_file, env, quiet, args=args)
        if not self._file_system.is_file(FILE_downloader_run_signal):
            return return_code

        self._logger.print(f"WARNING! {downloader_file} didn't work as expected with error code {return_code}!\n")

        downloader_file = prepare_latest_downloader(self._os_utils, self._file_system, self._logger, consider_bin=False, consider_zip=False)
        if downloader_file is None:
            return 1

        self._temp_launchers.append(downloader_file)
        return self._os_utils.execute_process(downloader_file, env, quiet, args=args)

    def cleanup_temp_launchers(self) -> None:
        for file in self._temp_launchers:
            if self._file_system.is_file(file):
                self._file_system.unlink(file, verbose=False)

        self._temp_launchers = []
