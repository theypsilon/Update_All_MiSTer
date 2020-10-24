#!/usr/bin/env bash

set -euo pipefail

EXPORTED_INI_PATH="update_all.ini"
UPDATE_ALL_SOURCE="true"
source dont_download.sh

fetch_or_exit() {
    echo "" > "${1}"
}

fetch_or_continue() {
    echo "" > "${1}"
}

UPDATE_ALL_LAUNCHER_MD5="68b329da9893e34099c7d8ad5cb9c940"

FAKE_MEDIA_FAT="media_fat"

BASE_PATH="${FAKE_MEDIA_FAT}"
WORK_OLD_PATH="${FAKE_MEDIA_FAT}/Scripts/.update_all"
WORK_NEW_PATH="${FAKE_MEDIA_FAT}/Scripts/.cache/update_all"
MISTER_MAIN_UPDATER_WORK_FOLDER="${FAKE_MEDIA_FAT}/Scripts/.mister_updater"
JOTEGO_UPDATER_WORK_FOLDER="${FAKE_MEDIA_FAT}/Scripts/.mister_updater_jt"
UNOFFICIAL_UPDATER_WORK_FOLDER="${FAKE_MEDIA_FAT}/Scripts/.mister_updater_unofficials"
ARCADE_ORGANIZER_INSTALLED_NAMES_TXT="${FAKE_MEDIA_FAT}/Scripts/.cache/arcade-organizer/installed_names.txt"
ARCADE_ORGANIZER_FOLDER_OPTION_1="${FAKE_MEDIA_FAT}/_Arcade/_Organized"
ARCADE_ORGANIZER_FOLDER_OPTION_2="${FAKE_MEDIA_FAT}/_Arcade"
MISTER_INI_PATH="${FAKE_MEDIA_FAT}/MiSTer.ini"
NAMES_TXT_PATH="${FAKE_MEDIA_FAT}/names.txt"

mkdir -p "${FAKE_MEDIA_FAT}"
echo "wrong" > "${EXPORTED_INI_PATH%.*}.sh"
mkdir -p "${BASE_PATH}/Scripts/"
mkdir -p "${MISTER_MAIN_UPDATER_WORK_FOLDER}"
echo "" > "${MISTER_MAIN_UPDATER_WORK_FOLDER}/db9"
mkdir -p "${BASE_PATH}/games/mame"

UNOFFICIAL_UPDATER="true"
LLAPI_UPDATER="true"
NAMES_TXT_UPDATER="true"

COUNTDOWN_TIME=0
WAIT_TIME_FOR_READING=0
AUTOREBOOT="false"

set -x

run_update_all
