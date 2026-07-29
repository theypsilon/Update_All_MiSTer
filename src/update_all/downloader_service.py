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

import hashlib
import json
import zipfile
from io import BytesIO
from typing import Optional
from urllib.parse import quote, urlparse

from update_all.config import Config
from update_all.constants import DOWNLOADER_LATEST_BIN_PATH, DOWNLOADER_LATEST_BIN_PYTHON_COMPATIBLE, \
    DOWNLOADER_LATEST_ZIP_PATH, DOWNLOADER_URL, FILE_JOTEGO_mra_pack_ini, FILE_downloader_run_signal, MEDIA_FAT
from update_all.databases import DB_ID_DISTRIBUTION_MISTER, Database, all_dbs
from update_all.fetcher import Fetcher
from update_all.file_system import FileSystem
from update_all.ini_repository import IniRepository
from update_all.logger import Logger
from update_all.os_utils import OsUtils


class DownloaderService:
    def __init__(
            self,
            logger: Logger,
            file_system: FileSystem,
            os_utils: OsUtils,
            ini_repository: IniRepository,
            fetcher: Fetcher,
    ):
        self._logger = logger
        self._file_system = file_system
        self._os_utils = os_utils
        self._ini_repository = ini_repository
        self._fetcher = fetcher
        self._temp_launchers: list[str] = []

    def execute_downloader(self, config: Config, downloader_ini_path: str, skip_linux_update: bool, logfile: Optional[str], default_db: Optional[Database], quiet: bool = False) -> int:
        env = self._prepare_env(config, downloader_ini_path, skip_linux_update, logfile, default_db)

        if not quiet:
            if default_db is None:
                self._logger.print('Running MiSTer Downloader')
            else:
                self._logger.print('Running ' + default_db.title)

        return self._run_with_fallbacks(config, env, quiet)

    def execute_downloader_command(self, config: Config, downloader_ini_path: str, args: list[str], logfile: Optional[str], quiet: bool = False) -> int:
        env = self._prepare_env(config, downloader_ini_path, config.skip_linux_update, logfile, None)
        return self._run_with_fallbacks(config, env, quiet, args=args)

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

    def _run_with_fallbacks(self, config: Config, env: dict[str, str], quiet: bool, args: Optional[list[str]] = None) -> int:
        attempts = ((True, True), (False, True), (False, False))
        for attempt, (consider_bin, consider_zip) in enumerate(attempts):
            self._logger.debug('Preparing Downloader launcher attempt ', attempt + 1, '/', len(attempts))
            downloader_file = self._prepare_latest_downloader(config, consider_bin, consider_zip)
            if downloader_file is None:
                self._logger.debug('Downloader launcher preparation failed')
                return 1

            self._temp_launchers.append(downloader_file)
            if attempt == 0 and not quiet:
                self._logger.print()

            return_code = self._os_utils.execute_process(downloader_file, env, quiet, args=args)
            if attempt == len(attempts) - 1 or not self._file_system.is_file(FILE_downloader_run_signal):
                self._logger.debug('Downloader launcher finished with exit code ', return_code)
                return return_code

            self._logger.debug('Downloader launcher failed startup check; trying fallback')
            self._logger.print(
                f"WARNING! {downloader_file} didn't work as expected with error code {return_code}!\n"
            )

        return 1

    def _prepare_latest_downloader(
            self,
            config: Config,
            consider_bin: bool,
            consider_zip: bool = True,
    ) -> Optional[str]:
        downloader_bin_path = config.downloader_path or DOWNLOADER_LATEST_BIN_PATH
        downloader_python_compatible_path = config.downloader_python_compatible_path or DOWNLOADER_LATEST_BIN_PYTHON_COMPATIBLE

        if consider_bin and self._file_system.is_file(downloader_bin_path) and self._file_system.is_file(downloader_python_compatible_path):
            return self._prepare_local_downloader(
                downloader_bin_path,
                '/tmp/ua_downloader_bin',
            )

        if consider_zip and self._file_system.is_file(DOWNLOADER_LATEST_ZIP_PATH):
            return self._prepare_local_downloader(
                DOWNLOADER_LATEST_ZIP_PATH,
                '/tmp/ua_downloader_latest.zip',
            )

        content = self._download_bootstrap_downloader(config)
        if content is None:
            return None

        target_path = '/tmp/ua_downloader_dd.pyz'
        self._file_system.write_file_bytes(target_path, content)
        try:
            self._os_utils.make_executable(target_path)
        except Exception as e:
            self._logger.print('ERROR! Failed to make the bootstrap Downloader executable')
            self._logger.debug(e)
        return target_path

    def _prepare_local_downloader(self, source_path: str, target_path: str) -> str:
        self._logger.debug('Using latest downloader from ', source_path)
        try:
            self._file_system.copy(source_path, target_path)
            self._file_system.touch(FILE_downloader_run_signal)
            self._os_utils.make_executable(target_path)
        except Exception as e:
            self._logger.print(f'ERROR! Failed to copy or make executable {source_path}')
            self._logger.debug(e)
        return target_path

    def _download_bootstrap_downloader(self, config: Config) -> Optional[bytes]:
        if config.downloader_url:
            self._logger.debug('Using configured Downloader bootstrap URL: ', config.downloader_url)
            return self._fetch(config.downloader_url)

        db_defs = all_dbs(config.mirror)
        distribution_databases = (
            ('configured', self._ini_repository.resolved_database_url(DB_ID_DISTRIBUTION_MISTER)),
            ('official', db_defs.MISTER_DEVEL_DISTRIBUTION_MISTER.db_url),
        )
        attempted_db_urls = set()
        for source, db_url in distribution_databases:
            if not db_url or db_url in attempted_db_urls:
                continue
            attempted_db_urls.add(db_url)

            self._logger.debug('Trying ', source, ' Distribution database for Downloader bootstrap: ', db_url)
            content = self._download_bootstrap_downloader_from_db(db_url)
            if content is not None:
                return content

        self._logger.debug('Falling back to direct Downloader bootstrap: ', DOWNLOADER_URL)
        return self._fetch(DOWNLOADER_URL, retry=3)

    def _download_bootstrap_downloader_from_db(self, db_url: str) -> Optional[bytes]:
        db_content = self._fetch(db_url, retry=3)
        if db_content is None:
            return None

        try:
            downloader_url, expected_hash, expected_size = _load_downloader_description(db_content)
        except Exception as e:
            self._logger.debug('Could not resolve the bootstrap Downloader from database ', db_url)
            self._logger.debug(e)
            return None

        self._logger.debug('Distribution database resolved Downloader bootstrap file: ', downloader_url)
        content = self._fetch(downloader_url, retry=1)
        if content is None:
            return None

        if len(content) != expected_size:
            self._logger.debug(
                'Bootstrap Downloader size mismatch from ', downloader_url,
                ': calculated ', len(content), ' != expected ', expected_size
            )
            return None

        calculated_hash = hashlib.md5(content).hexdigest()
        if calculated_hash.lower() != expected_hash.lower():
            self._logger.debug(
                'Bootstrap Downloader hash mismatch from ', downloader_url,
                ': calculated ', calculated_hash, ' != expected ', expected_hash
            )
            return None

        self._logger.debug('Downloader bootstrap integrity validated')
        return content

    def _fetch(self, url: str, retry: int = 0) -> Optional[bytes]:
        try:
            status, content = self._fetcher.fetch(url, timeout=180, retry=retry)
        except Exception as e:
            self._logger.debug('Could not fetch the bootstrap Downloader from ', url)
            self._logger.debug(e)
            return None

        if status != 200:
            self._logger.debug('Could not fetch the bootstrap Downloader from ', url, ': HTTP ', status)
            return None
        return content

    def cleanup_temp_launchers(self) -> None:
        for file in self._temp_launchers:
            if self._file_system.is_file(file):
                self._file_system.unlink(file, verbose=False)

        self._temp_launchers = []


def _load_downloader_description(content: bytes) -> tuple[str, str, int]:
    content_buffer = BytesIO(content)
    if zipfile.is_zipfile(content_buffer):
        content_buffer.seek(0)
        with zipfile.ZipFile(content_buffer) as db_zip:
            json_files = [name for name in db_zip.namelist() if not name.endswith('/') and name.lower().endswith('.json')]
            if len(json_files) != 1:
                raise ValueError(f'Database archive must contain exactly one JSON file, found {len(json_files)}')
            db = json.loads(db_zip.read(json_files[0]))
    else:
        db = json.loads(content)

    if not isinstance(db, dict):
        raise ValueError('Database contents must be a JSON object')

    description = db['files'][DOWNLOADER_LATEST_ZIP_PATH]
    if 'url' in description:
        url = description['url']
    else:
        base_files_url = db.get('base_files_url')
        url = None
        if isinstance(base_files_url, str) and base_files_url.strip() != '':
            url = base_files_url + quote(DOWNLOADER_LATEST_ZIP_PATH)
    expected_hash = description['hash']
    expected_size = description['size']
    parsed_url = urlparse(url) if isinstance(url, str) else None
    if parsed_url is None or parsed_url.scheme.lower() not in ('http', 'https') or parsed_url.netloc == '':
        raise ValueError('Bootstrap Downloader needs a valid URL')
    if not isinstance(expected_hash, str) or len(expected_hash) != 32:
        raise ValueError('Bootstrap Downloader needs a valid MD5 hash')
    try:
        int(expected_hash, 16)
    except ValueError as e:
        raise ValueError('Bootstrap Downloader needs a valid MD5 hash') from e
    if not isinstance(expected_size, int) or isinstance(expected_size, bool) or expected_size < 0:
        raise ValueError('Bootstrap Downloader needs a valid size')
    return url, expected_hash, expected_size
