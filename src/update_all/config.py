# Copyright (c) 2022 José Manuel Barroso Galindo <theypsilon@gmail.com>

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
from dataclasses import dataclass, field
from enum import unique, IntEnum
from typing import Set

from update_all.constants import DEFAULT_CURL_SSL_OPTIONS, DEFAULT_COMMIT, MEDIA_FAT
from update_all.databases import DB_ID_DISTRIBUTION_MISTER, DB_ID_JTCORES, AllDBs


@dataclass
class Config:
    # Not really a config
    start_time: float = 0.0

    # From the environment
    curl_ssl: str = DEFAULT_CURL_SSL_OPTIONS
    commit: str = DEFAULT_COMMIT

    # General options
    base_path: str = MEDIA_FAT
    base_system_path: str = MEDIA_FAT
    paths_from_downloader_ini: bool = False

    update_linux: bool = True
    not_mister: bool = False
    verbose: bool = False
    temporary_downloader_ini: bool = False

    # Global Updating Toggles
    databases: Set[str] = field(default_factory=lambda: {DB_ID_DISTRIBUTION_MISTER, DB_ID_JTCORES, AllDBs.COIN_OP_COLLECTION.db_id})
    arcade_organizer: bool = True

    # Specific Updating Toggles
    encc_forks: bool = False
    download_beta_cores: bool = False
    names_region: str = 'JP'
    names_char_code: str = 'CHAR18'
    names_sort_code: str = 'Common'
    hbmame_filter: bool = False

    # Misc Options
    wait_time_for_reading: int = 2
    countdown_time: int = 15
    autoreboot: bool = True


@unique
class AllowDelete(IntEnum):
    NONE = 0
    ALL = 1
    OLD_RBF = 2

