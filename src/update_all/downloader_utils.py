#!/usr/bin/env python3
# Copyright (c) 2022-2024 José Manuel Barroso Galindo <theypsilon@gmail.com>
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


from update_all.os_utils import OsUtils
from update_all.constants import DOWNLOADER_URL, DOWNLOADER_LATEST_ZIP_PATH, DOWNLOADER_LATEST_BIN_PATH, \
    DOWNLOADER_LATEST_BIN_PYTHON_COMPATIBLE, FILE_downloader_run_signal
from update_all.file_system import FileSystem
from typing import Optional
from update_all.logger import Logger

tmp_downloader_bin = '/tmp/ua_downloader_bin'
tmp_downloader_latest = '/tmp/ua_downloader_latest.zip'
tmp_dont_download = '/tmp/ua_downloader_dd.pyz'


def prepare_latest_downloader(os_utils: OsUtils, file_system: FileSystem, logger: Logger, consider_bin: bool, consider_zip: bool = True) -> Optional[str]:
    if consider_bin and file_system.is_file(DOWNLOADER_LATEST_BIN_PATH) and file_system.is_file(DOWNLOADER_LATEST_BIN_PYTHON_COMPATIBLE):
        logger.debug('Using latest downloader from %s' % DOWNLOADER_LATEST_BIN_PATH)
        try:
            file_system.copy(DOWNLOADER_LATEST_BIN_PATH, tmp_downloader_bin)
            file_system.touch(FILE_downloader_run_signal)
            os_utils.make_executable(tmp_downloader_bin)
        except Exception as e:
            logger.print('ERROR! Failed to copy or make executable downloader_bin')
            logger.debug(e)
        return tmp_downloader_bin
    elif consider_zip and file_system.is_file(DOWNLOADER_LATEST_ZIP_PATH):
        logger.debug('Using latest downloader from %s' % DOWNLOADER_LATEST_ZIP_PATH)
        try:
            file_system.copy(DOWNLOADER_LATEST_ZIP_PATH, tmp_downloader_latest)
            file_system.touch(FILE_downloader_run_signal)
            os_utils.make_executable(tmp_downloader_latest)
        except Exception as e:
            logger.print('ERROR! Failed to copy or make executable downloader_latest.zip')
            logger.debug(e)
        return tmp_downloader_latest
    else:
        logger.debug('Fetching latest downloader from %s' % DOWNLOADER_URL)
        content = os_utils.download(DOWNLOADER_URL)
        if content is None:
            return None

        file_system.write_file_bytes(tmp_dont_download, content)
        try:
            os_utils.make_executable(tmp_dont_download)
        except Exception as e:
            logger.print('ERROR! Failed to make executable from downloader dont_download.zip')
            logger.debug(e)
        return tmp_dont_download


def downloader_temp_files() -> list[str]:
    return [tmp_downloader_bin, tmp_downloader_latest, tmp_dont_download]
