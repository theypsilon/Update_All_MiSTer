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


def prepare_latest_downloader(os_utils: OsUtils, file_system: FileSystem, logger: Logger, consider_bin: bool) -> Optional[str]:
    has_bin = file_system.is_file(DOWNLOADER_LATEST_BIN_PATH)
    is_bin_python_compatible = file_system.is_file(DOWNLOADER_LATEST_BIN_PYTHON_COMPATIBLE)
    if consider_bin and has_bin and is_bin_python_compatible:
        temp_file = file_system.temp_file_by_id('downloader.sh')
        file_system.copy(DOWNLOADER_LATEST_ZIP_PATH, temp_file.name)
        file_system.touch(FILE_downloader_run_signal)
        logger.debug('Using latest downloader from %s' % DOWNLOADER_LATEST_ZIP_PATH)
        return temp_file.name
    elif file_system.is_file(DOWNLOADER_LATEST_ZIP_PATH):
        temp_file = file_system.temp_file_by_id('downloader.sh')
        file_system.copy(DOWNLOADER_LATEST_ZIP_PATH, temp_file.name)
        logger.debug('Using latest downloader from %s' % DOWNLOADER_LATEST_ZIP_PATH)
        logger.debug(f'consider_bin: {consider_bin}, has_bin: {has_bin}, is_bin_python_compatible: {is_bin_python_compatible}')
        return temp_file.name
    else:
        content = os_utils.download(DOWNLOADER_URL)
        if content is None:
            return None

        temp_file = file_system.temp_file_by_id('downloader.sh')
        file_system.write_file_bytes(temp_file.name, content)
        logger.debug('Fetching latest downloader from %s' % DOWNLOADER_URL)
        return temp_file.name
