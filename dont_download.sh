#!/bin/bash
# Copyright (c) 2020-2022 José Manuel Barroso Galindo <theypsilon@gmail.com>

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

# You can download the latest version of this script from:
# https://github.com/theypsilon/Updater_All_MiSTer

#
# WARNING
#
# This code is archived. No PR's targeting this file will be merged.
#

set -euo pipefail

UPDATE_ALL_VERSION="1.4"
UPDATE_ALL_PC_UPDATER="${UPDATE_ALL_PC_UPDATER:-false}"
UPDATE_ALL_LAUNCHER_MD5="36d2f56032c49ca76f7cf4b48f11a90c"
UPDATE_ALL_URL="https://raw.githubusercontent.com/theypsilon/Update_All_MiSTer/master/update_all.sh"

if [[ "${UPDATE_ALL_PC_UPDATER}" != "true" ]] ; then
    OLD_SCRIPT_PATH="${EXPORTED_INI_PATH%.*}.sh"
    if [ ! -f "${OLD_SCRIPT_PATH}" ] || [[ "$(md5sum ${OLD_SCRIPT_PATH} | awk '{print $1}')" != "${UPDATE_ALL_LAUNCHER_MD5}" ]] ; then
        MAYBE_NEW_LAUNCHER="/tmp/ua_maybe_new_launcher.sh"
        rm "${MAYBE_NEW_LAUNCHER}" 2> /dev/null || true
        curl ${CURL_RETRY:-} --silent --show-error ${SSL_SECURITY_OPTION:-} --fail --location -o "${MAYBE_NEW_LAUNCHER}" "${UPDATE_ALL_URL}"
        if [ -f "${MAYBE_NEW_LAUNCHER}" ] && [[ "$(md5sum ${MAYBE_NEW_LAUNCHER} | awk '{print $1}')" == "${UPDATE_ALL_LAUNCHER_MD5}" ]] ; then
            rm "${OLD_SCRIPT_PATH}" 2> /dev/null || true
            cp "${MAYBE_NEW_LAUNCHER}" "${OLD_SCRIPT_PATH}" || true

            echo
            echo "Update All's launcher script has just been upgraded."
            echo "Please execute this again to run the new version."
            echo "This is a one-time only process."
            echo
            exit 0
        fi
    fi

    echo
    echo "Update All could not be upgraded to a newer version."
    echo "Try again later. It could be a temporal network issue."
    echo
    echo "If you keep getting this error, please reinstall Update All:"
    echo "https://github.com/theypsilon/Update_All_MiSTer"
    echo
    exit 1
else

    echo
    echo "###  ANNOUNCEMENT  ###"
    echo
    echo "As of 2022.12.31, Update All 'Updater PC' is no longer supported."
    echo
    echo "Please use the new 'PC Launcher' for the MiSTer Downloader. Check the 'PC Launcher for Windows, Mac and Linux' section at:"
    echo "https://github.com/MiSTer-devel/Downloader_MiSTer"
    echo
    echo "This alternative is much faster, more robust, and installs substantially more content."
    echo "Use the 'PC Launcher' with a downloader.ini file saved with Update All's Setting Screen to get the same content you'd typically get from Update All."
    echo
    exit 0
fi
