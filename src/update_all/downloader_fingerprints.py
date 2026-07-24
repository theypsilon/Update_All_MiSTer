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

from typing import Optional, Set

from update_all.constants import FILE_downloader_fingerprints_json
from update_all.file_system import FileSystem
from update_all.logger import Logger


def try_read_installed_db_ids(file_system: FileSystem, logger: Logger) -> Optional[Set[str]]:
    if not file_system.is_file(FILE_downloader_fingerprints_json):
        return None

    try:
        fingerprints = file_system.load_dict_from_file(FILE_downloader_fingerprints_json)
        if isinstance(fingerprints, dict):
            return {db_id.lower() for db_id in fingerprints}
    except Exception as e:
        logger.debug(f'Could not load {FILE_downloader_fingerprints_json}.')
        logger.debug(e)

    return None


def read_installed_db_ids(file_system: FileSystem, logger: Logger) -> Set[str]:
    installed_db_ids = try_read_installed_db_ids(file_system, logger)
    return installed_db_ids if installed_db_ids is not None else set()
