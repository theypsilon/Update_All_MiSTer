#!/usr/bin/env bash

set -euo pipefail

CURL_RETRY="--connect-timeout 15 --max-time 120 --retry 3 --retry-delay 5 --silent --show-error"
ALLOW_INSECURE_SSL="true"
SSL_SECURITY_OPTION="--insecure"
EXPORTED_INI_PATH="update_all.ini"

UPDATE_ALL_SOURCE="true"
source dont_download.sh

set -x

FAKE_UPDATER="https://raw.githubusercontent.com/theypsilon/Update_All_MiSTer/master/.github/fake.sh"

MISTER_DEVEL_UPDATER_URL="${FAKE_UPDATER}"
MISTER_DB9_UPDATER_URL="${FAKE_UPDATER}"
JOTEGO_UPDATER_URL="${FAKE_UPDATER}"
UNOFFICIAL_UPDATER_URL="${FAKE_UPDATER}"
LLAPI_UPDATER_URL="${FAKE_UPDATER}"
NAMES_TXT_UPDATER_URL="${FAKE_UPDATER}"
BIOS_GETTER_URL="${FAKE_UPDATER}"
MAME_GETTER_URL="${FAKE_UPDATER}"
HBMAME_GETTER_URL="${FAKE_UPDATER}"
ARCADE_ORGANIZER_URL="${FAKE_UPDATER}"

FAKE_MEDIA_FAT="media_fat"

BASE_PATH="${FAKE_MEDIA_FAT}"
WORK_OLD_PATH="${FAKE_MEDIA_FAT}/Scripts/.update_all"
WORK_NEW_PATH="${FAKE_MEDIA_FAT}/Scripts/.cache/update_all"
MISTER_MAIN_UPDATER_WORK_FOLDER="${FAKE_MEDIA_FAT}/Scripts/.mister_updater"
JOTEGO_UPDATER_WORK_FOLDER="${FAKE_MEDIA_FAT}/Scripts/.mister_updater_jt"
UNOFFICIAL_UPDATER_WORK_FOLDER="${FAKE_MEDIA_FAT}/Scripts/.mister_updater_unofficials"

AUTOREBOOT="false"
UNOFFICIAL_UPDATER="true"
LLAPI_UPDATER="true"
NAMES_TXT_UPDATER="true"
ENCC_FORKS="false"

run_update_all

ENCC_FORKS="true"

run_update_all