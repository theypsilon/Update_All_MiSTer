# Copyright (c) 2022-2025 José Manuel Barroso Galindo <theypsilon@gmail.com>

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
from typing import Set, Optional, TypedDict

from update_all.analogue_pocket.http_gateway import HttpConfig
from update_all.constants import DEFAULT_CURL_SSL_OPTIONS, DEFAULT_COMMIT, MEDIA_FAT, FILE_patreon_key, \
    FILE_timeline_short, FILE_timeline_plus, COMMAND_STANDARD, DOMAIN_default_retroaccount


class EnvDict(TypedDict):
    CURL_SSL: str
    COMMIT: str
    LOCATION_STR: str
    DEBUG: str
    TRANSITION_SERVICE_ONLY: str
    SKIP_DOWNLOADER: str
    PATREON_KEY_PATH: str
    COMMAND: str
    TIMELINE_SHORT_PATH: str
    TIMELINE_PLUS_PATH: str
    HTTP_PROXY: Optional[str]
    HTTPS_PROXY: Optional[str]
    MIRROR_ID: str
    RETROACCOUNT_FEATURE_FLAG: str
    RETROACCOUNT_DOMAIN: str

@dataclass
class Config:
    # Not really a config
    start_time: float = 0.0

    # From the environment
    curl_ssl: str = DEFAULT_CURL_SSL_OPTIONS
    commit: str = DEFAULT_COMMIT
    skip_downloader: bool = False
    patreon_key_path: str = FILE_patreon_key
    timeline_short_path: str = FILE_timeline_short
    timeline_plus_path: str = FILE_timeline_plus
    command: str = COMMAND_STANDARD
    http_proxy: str = ''
    http_config: Optional[HttpConfig] = None
    retroaccount_feature_flag: bool = False
    retroaccount_domain: str = DOMAIN_default_retroaccount

    # General options
    base_path: str = MEDIA_FAT
    base_system_path: str = MEDIA_FAT
    paths_from_downloader_ini: bool = False

    update_linux: bool = True
    not_mister: bool = False
    verbose: bool = False
    temporary_downloader_ini: bool = False
    transition_service_only: bool = False

    # Global Updating Toggles
    mirror: str = ''
    databases: Set[str] = field(default_factory=lambda: set())
    arcade_organizer: bool = False

    # Specific Updating Toggles
    encc_forks: str = "devel"  # Possible values: "devel", "db9", "aitorgomez"
    download_beta_cores: bool = False
    names_region: str = 'JP'
    names_char_code: str = 'CHAR18'
    names_sort_code: str = 'Common'
    hbmame_filter: bool = False
    rannysnice_wallpapers_filter: str = 'ar16-9'

    # Misc Options
    countdown_time: int = 15
    autoreboot: bool = True
    pocket_firmware_update: bool = False
    pocket_backup: bool = False
    log_viewer: bool = True
    timeline_after_logs: bool = True

@unique
class AllowDelete(IntEnum):
    NONE = 0
    ALL = 1
    OLD_RBF = 2
