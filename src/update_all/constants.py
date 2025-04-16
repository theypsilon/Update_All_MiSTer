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

# Default SSL option
from enum import unique, Enum
from typing import Final

# From patreon.com/theypsilon
supporter_plus_patrons: Final[tuple[str,...]] = ('Alex Frégeau', "The Sentinel's Playground Team", 'Thomas Williams', 'Wayne Booker')

# Default options
DEFAULT_CURL_SSL_OPTIONS: Final[str] = ''
DEFAULT_COMMIT: Final[str] = 'unknown'
DEFAULT_LOCATION_STR: Final[str] = 'MiSTer'
DEFAULT_DEBUG: Final[str] = 'false'
DEFAULT_KEY_IGNORE_TIME: Final[str] = '0.1'
DEFAULT_TRANSITION_SERVICE_ONLY: Final[str] = 'false'

MISTER_ENVIRONMENT: Final[str] = 'mister'
STANDARD_UI_THEME: Final[str] = 'Blue Installer'

# Downloader files
FILE_update_all_pyz: Final[str] = 'Scripts/.config/update_all/update_all.pyz'
FILE_update_all_zipped_storage: Final[str] = 'Scripts/.config/update_all/update_all.json.zip'
FILE_update_all_storage: Final[str] = 'Scripts/.config/update_all/update_all.json'
FILE_update_all_log: Final[str] = 'Scripts/.config/update_all/update_all.log'
FILE_pocket_firmware_details_json: Final[str] = "Scripts/.config/update_all/pocket_firmware_details.json"
FILE_arcade_database_mad_db_json_zip: Final[str] = "Scripts/.config/update_all/mad_db.json.zip"
FILE_update_all_ini: Final[str] = 'Scripts/update_all.ini'
FILE_update_jtcores_ini: Final[str] = 'Scripts/update_jtcores.ini'
FILE_update_jtcores_sh: Final[str] = 'Scripts/update_jtcores.sh'
FILE_update_names_txt_ini: Final[str] = 'Scripts/update_names-txt.ini'
FILE_update_names_txt_sh: Final[str] = 'Scripts/update_names-txt.sh'
FILE_MiSTer: Final[str] = 'MiSTer'
FILE_MiSTer_delme: Final[str] = '.MiSTer.delme'
FILE_MiSTer_ini: Final[str] = 'MiSTer.ini'
FOLDER_scripts: Final[str] = 'Scripts'
FOLDER_scripts_config_lc: Final[str] = 'scripts/.config'
FILE_downloader_temp_ini: Final[str] = '/tmp/downloader_temp.ini'

# Reboot files
FILE_downloader_needs_reboot_after_linux_update: Final[str] = '/tmp/downloader_needs_reboot_after_linux_update'
FILE_mister_downloader_needs_reboot: Final[str] = '/tmp/MiSTer_downloader_needs_reboot'

MEDIA_FAT: Final[str] = '/media/fat'

# Dictionary Keys:

# Config
K_BASE_PATH: Final[str] = 'base_path'
K_BASE_SYSTEM_PATH: Final[str] = 'base_system_path'
K_STORAGE_PRIORITY: Final[str] = 'storage_priority'
K_DATABASES: Final[str] = 'databases'
K_ALLOW_DELETE: Final[str] = 'allow_delete'
K_ALLOW_REBOOT: Final[str] = 'allow_reboot'
K_UPDATE_LINUX: Final[str] = 'update_linux'
K_PARALLEL_UPDATE: Final[str] = 'parallel_update'
K_DOWNLOADER_SIZE_MB_LIMIT: Final[str] = 'downloader_size_mb_limit'
K_DOWNLOADER_PROCESS_LIMIT: Final[str] = 'downloader_process_limit'
K_DOWNLOADER_TIMEOUT: Final[str] = 'downloader_timeout'
K_DOWNLOADER_RETRIES: Final[str] = 'downloader_retries'
K_ZIP_FILE_COUNT_THRESHOLD: Final[str] = 'zip_file_count_threshold'
K_ZIP_ACCUMULATED_MB_THRESHOLD: Final[str] = 'zip_accumulated_mb_threshold'
K_FILTER: Final[str] = 'filter'
K_VERBOSE: Final[str] = 'verbose'
K_CONFIG_PATH: Final[str] = 'config_path'
K_USER_DEFINED_OPTIONS: Final[str] = 'user_defined_options'
K_CURL_SSL: Final[str] = 'curl_ssl'
K_DB_URL: Final[str] = 'db_url'
K_SECTION: Final[str] = 'section'
K_OPTIONS: Final[str] = 'options'
K_DEBUG: Final[str] = 'debug'
K_FAIL_ON_FILE_ERROR: Final[str] = 'fail_on_file_error'
K_COMMIT: Final[str] = 'commit'
K_DEFAULT_DB_ID: Final[str] = 'default_db_id'
K_START_TIME: Final[str] = 'start_time'

# Update All old options
K_COUNTDOWN_TIME: Final[str] = "countdown_time"
K_WAIT_TIME_FOR_READING: Final[str] = "wait_time_for_reading"
K_AUTOREBOOT: Final[str] = "autoreboot"
K_KEEP_USBMOUNT_CONF: Final[str] = "keep_usbmount_conf"


# Env
KENV_CURL_SSL: Final[str] = 'CURL_SSL'
KENV_COMMIT: Final[str] = 'COMMIT'
KENV_LOCATION_STR: Final[str] = 'LOCATION_STR'
KENV_DEBUG: Final[str] = 'DEBUG'
KENV_KEY_IGNORE_TIME: Final[str] = 'KEY_IGNORE_TIME'
KENV_TRANSITION_SERVICE_ONLY: Final[str] = 'TRANSITION_SERVICE_ONLY'

# Exit codes
EXIT_CODE_REQUIRES_EARLY_EXIT: Final[int] = 1
EXIT_CODE_CAN_CONTINUE: Final[int] = 2

@unique
class PathType(Enum):
    FILE: str = 0
    FOLDER: str = 1


# Update All old constants
UPDATE_ALL_VERSION: Final[str] = "2.2"
MISTER_DOWNLOADER_VERSION: Final[str] = "2.1"
ARCADE_ORGANIZER_INSTALLED_NAMES_TXT: Final[str] = "Scripts/.config/arcade-organizer/installed_names.txt"
ARCADE_ORGANIZER_INI: Final[str] = "Scripts/update_arcade-organizer.ini"
DOWNLOADER_URL: Final[str] = "https://github.com/MiSTer-devel/Downloader_MiSTer/releases/download/latest/dont_download.zip"
DOWNLOADER_INI_STANDARD_PATH: Final[str] = "downloader.ini"
DOWNLOADER_STORE_STANDARD_PATH: Final[str] = "Scripts/.config/downloader/downloader.json"
DOWNLOADER_LATEST_ZIP_PATH: Final[str] = "Scripts/.config/downloader/downloader_latest.zip"
TEST_UNSTABLE_SPINNER_FIRMWARE_MD5: Final[str] = "b76bc57d75afce8b1040bc4d225ea3aa"
