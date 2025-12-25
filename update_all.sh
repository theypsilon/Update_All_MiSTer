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

RUN_TOOL_PATH="/tmp/update_all.sh"
REMOTE_TOOL_URL="https://raw.githubusercontent.com/theypsilon/Update_All_MiSTer/master/dont_download2.sh"
LATEST_TOOL_PATH="/media/fat/Scripts/.config/update_all/update_all.pyz"
MIRROR_FILE_PATH="/media/fat/Scripts/update_all.mirror"
CACERT_PEM_0="/etc/ssl/certs/cacert.pem"
CACERT_PEM_1="/media/fat/Scripts/.config/downloader/cacert.pem"

# NTP SETUP
if (( 10#$(date +%Y) < 2000 )) ; then
    NTP_SERVERS=(
        "time.apple.com"
        "time.amazonaws.cn"
        "ntp.ntsc.ac.cn"
        "cn.pool.ntp.org"
        "ntp.aliyun.com"
        "ntp.tencent.com"
        "ntp.rt.ru"
    )
    NTP_CONF="/etc/ntp.conf"
    for server in "${NTP_SERVERS[@]}"; do
        if ! grep -qF "${server}" "${NTP_CONF}"; then
            echo "server $server iburst" >> "${NTP_CONF}" 2>/dev/null || true
        fi
    done
    NTP_PID="/var/run/ntpd.pid"
    start-stop-daemon -K -p "${NTP_PID}" || true
    rm -f "${NTP_PID}" || true
    start-stop-daemon -S -q -p "${NTP_PID}" -x "/usr/sbin/ntpd" -- -g -p "${NTP_PID}" || true
    connected=0
    for ((i=1; i<=10; i++)); do
        if ntpq -c "rv 0" 2>&1 | grep -qiE "connection refused|sync_unspec" ; then
            printf "."
            sleep 3
        else
            connected=1
            break
        fi
    done
    printf "\n"
    if (( connected )); then
        echo "Date and time is:"
        date
        echo
    elif [[ "${CURL_SSL:-}" != "--insecure" ]] ; then
        echo "Unable to sync."
        echo "Please, try again later."
        exit 1
    fi
fi

# CERTS SETUP
if [ -s "${CACERT_PEM_1}" ] ; then
    export SSL_CERT_FILE="${CACERT_PEM_1}"
elif [ -s "${CACERT_PEM_0}" ] ; then
    export SSL_CERT_FILE="${CACERT_PEM_0}"
elif [[ "${CURL_SSL:-}" != "--insecure" ]] ; then
    set +e
    curl "https://github.com" > /dev/null 2>&1
    CURL_RET=$?
    set -e

    case $CURL_RET in
      0)
        ;;
      *)
        if ! which dialog > /dev/null 2>&1 ; then
            echo "ERROR: CURL returned error code ${CURL_RET}."
            exit $CURL_RET
        fi

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
        ;;
    esac
fi

# LAUNCHER
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

rm ${RUN_TOOL_PATH} 2> /dev/null || true

if [ -s "${MIRROR_FILE_PATH}" ] ; then
    TEMP_MIRROR_TOOL_URL=$(grep -o '"mirror_tool_url"[[:space:]]*:[[:space:]]*"[^"]*"' "${MIRROR_FILE_PATH}" | cut -d'"' -f4 || true)
    TEMP_MIRROR_ID=$(grep -o '"mirror_id"[[:space:]]*:[[:space:]]*"[^"]*"' "${MIRROR_FILE_PATH}" | cut -d'"' -f4 || true)

    if [ -n "${TEMP_MIRROR_TOOL_URL}" ] && [ -n "${TEMP_MIRROR_ID}" ] ; then
        export MIRROR_TOOL_URL="${TEMP_MIRROR_TOOL_URL}"
        export MIRROR_ID="${TEMP_MIRROR_ID}"
    else
        echo "WARNING: ${MIRROR_FILE_PATH} is invalid."
        echo "         Please replace it with a valid mirror file."
        echo "         Falling back to default download source."
        echo
    fi
fi

if [ -s "${LATEST_TOOL_PATH}" ] ; then
    cp "${LATEST_TOOL_PATH}" "${RUN_TOOL_PATH}"
else
    download_file "${RUN_TOOL_PATH}" "${MIRROR_TOOL_URL:-${REMOTE_TOOL_URL}}"
    echo -n "!"
fi

echo ; echo
chmod +x "${RUN_TOOL_PATH}"

set +e
${RUN_TOOL_PATH}
UA_RET=$?
set -e

if [[ ${UA_RET} -eq 2 ]] && [ -s "${LATEST_TOOL_PATH}" ] ; then
    cp "${LATEST_TOOL_PATH}" "${RUN_TOOL_PATH}"
    set +e
    ${RUN_TOOL_PATH} --continue
    UA_RET=$?
    set -e
fi

if [[ ${UA_RET} -ne 0 ]] ; then
    echo -e "Update All failed!\n"
    exit 1
fi

rm ${RUN_TOOL_PATH} 2> /dev/null || true

exit 0
