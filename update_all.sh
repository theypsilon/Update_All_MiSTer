#!/bin/bash
# Copyright (c) 2020 José Manuel Barroso Galindo <theypsilon@gmail.com>

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

# Version 1.0 - 2020-06-07 - First commit

set -euo pipefail


# ========= OPTIONS ==================
CURL_RETRY="--connect-timeout 15 --max-time 600 --retry 3 --retry-delay 5"
ALLOW_INSECURE_SSL="true"

# ========= CODE STARTS HERE =========
if [[ "${0}" == "bash" ]] ; then
    ORIGINAL_SCRIPT_PATH="$(ps -o comm,pid | awk -v PPID=${PPID} '$2 == PPID {print $1}')"
else
    ORIGINAL_SCRIPT_PATH="${0}"
fi

INI_PATH="${ORIGINAL_SCRIPT_PATH%.*}.ini"
if [[ -f "${INI_PATH}" ]] ; then
    TMP=$(mktemp)
    dos2unix < "${INI_PATH}" 2> /dev/null | grep -v "^exit" > ${TMP} || true
    set +u
    source ${TMP}
    set -u
    rm -f ${TMP}
fi

set +e

SSL_SECURITY_OPTION=""
curl ${CURL_RETRY} --silent --show-error "https://github.com" > /dev/null 2>&1
case $? in
    0)
        ;;
    60)
        if [[ "${ALLOW_INSECURE_SSL}" == "true" ]]
        then
            SSL_SECURITY_OPTION="--insecure"
        else
            echo "CA certificates need"
            echo "to be fixed for"
            echo "using SSL certificate"
            echo "verification."
            echo "Please fix them i.e."
            echo "using security_fixes.sh"
            exit 2
        fi
        ;;
    *)
        echo "No Internet connection"
        exit 1
        ;;
esac
set -e

SCRIPT_PATH="/tmp/${ORIGINAL_SCRIPT_PATH/*\//}"
rm ${SCRIPT_PATH} 2> /dev/null || true

if [[ "${DEBUG_UPDATER:-false}" != "true" ]] || [ ! -f dont_download.sh ] ; then
    REPOSITORY_URL="https://github.com/theypsilon/Update_All_MiSTer"
    echo "Downloading"
    echo "${REPOSITORY_URL}"
    echo ""

    curl \
        ${CURL_RETRY} --silent --show-error \
        ${SSL_SECURITY_OPTION} \
        --fail \
        --location \
        -o "${SCRIPT_PATH}" \
        "${REPOSITORY_URL}/blob/master/dont_download.sh?raw=true"
else
    cp dont_download.sh ${SCRIPT_PATH}
    export AUTO_UPDATE_LAUNCHER="false"
    export DEBUG_UPDATER
fi

export CURL_RETRY
export ALLOW_INSECURE_SSL
export SSL_SECURITY_OPTION
export EXPORTED_INI_PATH="${INI_PATH}"

bash "${SCRIPT_PATH}" || echo -e "Script ${ORIGINAL_SCRIPT_PATH} failed!\n"

rm ${SCRIPT_PATH} 2> /dev/null || true

exit 0
