#!/bin/bash
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

set -euo pipefail

RUN_SCRIPT_PATH="/tmp/update_all.sh"
LATEST_SCRIPT_PATH="/media/fat/Scripts/.config/update_all/update_all.pyz"
CACERT_PEM_0="/etc/ssl/certs/cacert.pem"
CACERT_PEM_1="/media/fat/Scripts/.config/downloader/cacert.pem"

if (( $(date +%Y) < 2000 )) ; then
    NTP_SERVER="0.pool.ntp.org"
    echo "Syncing date and time with $NTP_SERVER"
    echo
    if ntpdate -s -b -u $NTP_SERVER ; then
        echo "Date and time is:"
        echo "$(date)"
        echo
    elif [[ "${CURL_SSL:-}" != "--insecure" ]] ; then
	      echo "Unable to sync."
        echo "Please, try again later."
        exit 1
    fi
fi

if [ -s "${CACERT_PEM_1}" ] ; then
    export SSL_CERT_FILE="${CACERT_PEM_1}"
elif [ -s "${CACERT_PEM_0}" ] ; then
    export SSL_CERT_FILE="${CACERT_PEM_0}"
elif [[ "${CURL_SSL:-}" != "--insecure" ]] ; then
    set +e
    dialog --keep-window --title "Bad Certificates" --defaultno \
        --yesno "CA certificates need to be fixed, do you want me to fix them?\n\nNOTE: This operation will delete files at /etc/ssl/certs" \
        7 65
    DIALOG_RET=$?
    set -e

    if [[ "${DIALOG_RET}" != "0" ]] ; then
        echo "No secure connection is possible without fixing the certificates."
        exit 1
    fi

    RO_ROOT="false"
    if mount | grep "on / .*[(,]ro[,$]" -q ; then
        RO_ROOT="true"
    fi
    [ "${RO_ROOT}" == "true" ] && mount / -o remount,rw
    rm /etc/ssl/certs/* 2> /dev/null || true
    echo
    echo "Installing cacert.pem from https://curl.se"
    curl --insecure --location -o /tmp/cacert.pem "https://curl.se/ca/cacert.pem"
    curl --insecure --location -o /tmp/cacert.pem.sha256 "https://curl.se/ca/cacert.pem.sha256"

    DOWNLOAD_SHA256=$(cat /tmp/cacert.pem.sha256 | awk '{print $1}')
    CALCULATED_SHA256=$(sha256sum /tmp/cacert.pem | awk '{print $1}')

    if [[ "${DOWNLOAD_SHA256}" == "${CALCULATED_SHA256}" ]]; then
        mv /tmp/cacert.pem "${CACERT_PEM_0}"
        sync
    else
        echo "Checksum validation for downloaded CA certificate failed."
        echo "Please try again later."
        exit 0
    fi

    [ "${RO_ROOT}" == "true" ] && mount / -o remount,ro

    export SSL_CERT_FILE="${CACERT_PEM_0}"
fi

download_file() {
    local DOWNLOAD_PATH="${1}"
    local DOWNLOAD_URL="${2}"
    set +e
    curl ${CURL_SSL:-} --silent --fail --location -o "${DOWNLOAD_PATH}" "${DOWNLOAD_URL}"
    local CMD_RET=$?
    set -e

    case ${CMD_RET} in
        0)
            return
            ;;
        60|77|35|51|58|59|82|83)
            echo ; echo "No secure connection is possible without fixing the certificates."
            exit 1
            ;;
        *)
            echo ; echo "No internet connection, please try again later."
            exit 1
            ;;
    esac
}

echo -n "Launching Update All"

rm ${RUN_SCRIPT_PATH} 2> /dev/null || true

if [ -s "${LATEST_SCRIPT_PATH}" ] ; then
    cp "${LATEST_SCRIPT_PATH}" "${RUN_SCRIPT_PATH}"
else
    download_file "${RUN_SCRIPT_PATH}" "https://raw.githubusercontent.com/theypsilon/Update_All_MiSTer/master/dont_download2.sh"
    echo -n "!"
fi

echo ; echo
chmod +x "${RUN_SCRIPT_PATH}"

set +e
${RUN_SCRIPT_PATH}
UA_RET=$?
set -e

if [[ ${UA_RET} -eq 2 ]] && [ -s "${LATEST_SCRIPT_PATH}" ] ; then
    cp "${LATEST_SCRIPT_PATH}" "${RUN_SCRIPT_PATH}"
    set +e
    ${RUN_SCRIPT_PATH} --continue
    UA_RET=$?
    set -e
fi

if [[ ${UA_RET} -ne 0 ]] ; then
    echo -e "Update All failed!\n"
    exit 1
fi

rm ${RUN_SCRIPT_PATH} 2> /dev/null || true

exit 0
