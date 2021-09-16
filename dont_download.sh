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
set_default_options() {
    BASE_PATH="/media/fat"

    ENCC_FORKS="false" # Possible values: "true", "false"
    DOWNLOADER_WHEN_POSSIBLE="false" # Possible values: "true", "false"

    MAIN_UPDATER="true"
    MAIN_UPDATER_INI="${EXPORTED_INI_PATH}" # Probably update_all.ini

    JOTEGO_UPDATER="true"
    JOTEGO_UPDATER_INI="${EXPORTED_INI_PATH}" # Probably update_all.ini

    UNOFFICIAL_UPDATER="false"
    UNOFFICIAL_UPDATER_INI="${EXPORTED_INI_PATH}" # Probably update_all.ini

    LLAPI_UPDATER="false"
    LLAPI_UPDATER_INI="${EXPORTED_INI_PATH}" # Probably update_all.ini

    ARCADE_OFFSET_DOWNLOADER="false"

    BIOS_GETTER="true"
    BIOS_GETTER_INI="update_bios-getter.ini"

    MAME_GETTER="true"
    MAME_GETTER_INI="update_mame-getter.ini"

    HBMAME_GETTER="true"
    HBMAME_GETTER_INI="update_hbmame-getter.ini"

    NAMES_TXT_UPDATER="false"
    NAMES_TXT_UPDATER_INI="update_names-txt.ini"
    NAMES_REGION="US"
    NAMES_CHAR_CODE="CHAR18"
    NAMES_SORT_CODE="Common"

    ARCADE_ORGANIZER="true"
    ARCADE_ORGANIZER_INI="update_arcade-organizer.ini"

    COUNTDOWN_TIME=15
    WAIT_TIME_FOR_READING=4
    AUTOREBOOT="true"
    KEEP_USBMOUNT_CONF="false"

    if [[ "${UPDATE_ALL_PC_UPDATER_ENCC_FORKS:-}" == "true" ]] ; then
        ENCC_FORKS="true"
    fi

    ARCADE_ORGANIZER_2_ALPHA_ENABLED="false"
}
set_default_options
# ========= CODE STARTS HERE =========
UPDATE_ALL_VERSION="1.3"
if [ -f /media/fat/payoyo_cheese.txt ] ; then
    UPDATE_ALL_VERSION="1.4"
fi
UPDATE_ALL_PC_UPDATER="${UPDATE_ALL_PC_UPDATER:-false}"
UPDATE_ALL_OS="${UPDATE_ALL_OS:-MiSTer_Linux}"
UPDATE_ALL_LAUNCHER_MD5="ac10fbada40e3e5f133bc0eee0dd53d5"
AUTO_UPDATE_LAUNCHER="${AUTO_UPDATE_LAUNCHER:-true}"
ORIGINAL_SCRIPT_PATH="${0}"
ORIGINAL_INI_PATH="${ORIGINAL_SCRIPT_PATH%.*}.ini"
CURRENT_DIR="$(dirname ${EXPORTED_INI_PATH})/"
LOG_FILENAME="$(basename ${EXPORTED_INI_PATH%.*}.log)"
SETTINGS_ON_FILENAME="settings-on"
WORK_OLD_PATH="/media/fat/Scripts/.update_all"
WORK_NEW_PATH="/media/fat/Scripts/.config/update_all"
WORK_PATH=
MISTER_MAIN_UPDATER_WORK_FOLDER="/media/fat/Scripts/.mister_updater"
MISTER_DOWNLOADER_WORK_FOLDER="/media/fat/Scripts/.config/downloader"
JOTEGO_UPDATER_WORK_FOLDER="/media/fat/Scripts/.mister_updater_jt"
UNOFFICIAL_UPDATER_WORK_FOLDER="/media/fat/Scripts/.mister_updater_unofficials"
MAME_GETTER_LASTRUN_PATH="/media/fat/Scripts/.config/mame-getter/last_run"
HBMAME_GETTER_LASTRUN_PATH="/media/fat/Scripts/.config/hbmame-getter/last_run"
ARCADE_ORGANIZER_INSTALLED_NAMES_TXT="/media/fat/Scripts/.config/arcade-organizer/installed_names.txt"
ARCADE_ORGANIZER_FOLDER_OPTION_1="/media/fat/_Arcade/_Organized"
ARCADE_ORGANIZER_FOLDER_OPTION_2="/media/fat/_Arcade"
ARCADE_ORGANIZER_FOLDER_OPTION_3="/media/fat/_Arcade Organized"
MISTER_INI_PATH="/media/fat/MiSTer.ini"
NAMES_TXT_PATH="/media/fat/names.txt"
USBMOUNT_CONF_PATH="/etc/usbmount/usbmount.conf"
USBMOUNT_CONF_TMP="/tmp/ua_usbmount.conf"
GLOG_TEMP="/tmp/tmp.global.${LOG_FILENAME}"
GLOG_PATH=".update_all.log"
UPDATE_ALL_URL="https://raw.githubusercontent.com/theypsilon/Update_All_MiSTer/master/update_all.sh"
MISTER_DEVEL_UPDATER_URL="https://raw.githubusercontent.com/MiSTer-devel/Updater_script_MiSTer/master/mister_updater.sh"
MISTER_DEVEL_LINUX_ONLY_UPDATER_URL="https://raw.githubusercontent.com/theypsilon/Updater_script_Linux_Only_MiSTer/master/mister_updater.sh"
DOWNLOADER_URL=""
MISTER_DB9_UPDATER_URL="https://raw.githubusercontent.com/MiSTer-DB9/Updater_script_MiSTer_DB9/master/mister_updater.sh"
JOTEGO_UPDATER_URL="https://raw.githubusercontent.com/jotego/Updater_script_MiSTer/master/mister_updater.sh"
UNOFFICIAL_UPDATER_URL="https://raw.githubusercontent.com/theypsilon/Updater_script_MiSTer_Unofficial/master/mister_updater.sh"
LLAPI_UPDATER_URL="https://raw.githubusercontent.com/MiSTer-LLAPI/Updater_script_MiSTer/master/llapi_updater.sh"
NAMES_TXT_UPDATER_URL="https://raw.githubusercontent.com/theypsilon/Names_TXT_Updater_MiSTer/master/dont_download.sh"
BIOS_GETTER_URL="https://raw.githubusercontent.com/theypsilon/MiSTer_BIOS_SCRIPTS/master/bios-getter.sh"
MAME_GETTER_URL="https://raw.githubusercontent.com/atrac17/MiSTer_MAME_SCRIPTS/master/mame-merged-set-getter.sh"
HBMAME_GETTER_URL="https://raw.githubusercontent.com/atrac17/MiSTer_MAME_SCRIPTS/master/hbmame-merged-set-getter.sh"
ARCADE_ORGANIZER_URL="https://raw.githubusercontent.com/theypsilon/_arcade-organizer/master/_arcade-organizer.sh"
ARCADE_ORGANIZER_2BETA_URL="https://raw.githubusercontent.com/theypsilon/_arcade-organizer/2.0/_arcade-organizer.sh"
INI_REFERENCES=( \
    "EXPORTED_INI_PATH" \
    "MAIN_UPDATER_INI" \
    "JOTEGO_UPDATER_INI" \
    "UNOFFICIAL_UPDATER_INI" \
    "LLAPI_UPDATER_INI" \
    "BIOS_GETTER_INI" \
    "MAME_GETTER_INI" \
    "HBMAME_GETTER_INI" \
    "NAMES_TXT_UPDATER_INI" \
    "ARCADE_ORGANIZER_INI" \
)

DOWNLOADER_DB9_DB_URL="https://raw.githubusercontent.com/MiSTer-DB9/Distribution_MiSTer/main/dbencc.json.zip"
DOWNLOADER_JT_BETAS_DB_URL="https://raw.githubusercontent.com/theypsilon/JT_Cores_MiSTer/jtbin/jtbindb.json.zip"
DOWNLOADER_JT_STABLE_DB_URL="https://raw.githubusercontent.com/theypsilon/JT_Cores_MiSTer/jtstable/jtstabledb.json.zip"
DOWNLOADER_JT_DB_ID="jtcores"
DOWNLOADER_LLAPI_DB_URL="https://raw.githubusercontent.com/theypsilon/LLAPI_Folder_MiSTer/main/llapidb.json.zip"
DOWNLOADER_LLAPI_DB_ID="llapi_folder"
DOWNLOADER_UNOFFICIALS_DB_URL="https://raw.githubusercontent.com/theypsilon/Distribution_Unofficial_MiSTer/main/unofficialdb.json.zip"
DOWNLOADER_UNOFFICIALS_DB_ID="theypsilon_unofficial_distribution"
DOWNLOADER_ARCADE_OFFSET_DB_URL="https://raw.githubusercontent.com/theypsilon/Arcade_Offset_Folder_MiSTer/db/arcadeoffsetdb.json.zip"
DOWNLOADER_ARCADE_OFFSET_DB_ID="arcade_offset_folder"

CACHE_UPDATE_ALL_PATH="/media/fat/Scripts/.cache/update_all"
CACHE_MAME_GETTER_PATH="/media/fat/Scripts/.cache/mame-getter"
CACHE_HBMAME_GETTER_PATH="/media/fat/Scripts/.cache/hbmame-getter"
CACHE_ARCADE_ORGANIZER_PATH="/media/fat/Scripts/.cache/arcade-organizer"

CONFIG_FOLDER_PATH="/media/fat/Scripts/.config"
CONFIG_UPDATE_ALL_PATH="/media/fat/Scripts/.config/update_all"
CONFIG_MAME_GETTER_PATH="/media/fat/Scripts/.config/mame-getter"
CONFIG_HBMAME_GETTER_PATH="/media/fat/Scripts/.config/hbmame-getter"
CONFIG_ARCADE_ORGANIZER_PATH="/media/fat/Scripts/.config/arcade-organizer"

enable_global_log() {
    if [[ "${UPDATE_ALL_OS}" == "WINDOWS" ]] ; then return ; fi
    exec >  >(tee -ia ${GLOG_TEMP})
    exec 2> >(tee -ia ${GLOG_TEMP} >&2)
}

disable_global_log() {
    if [[ "${UPDATE_ALL_OS}" == "WINDOWS" ]] ; then return ; fi
    exec 1>&6 ; exec 2>&7
}

initialize_global_log() {
    if [[ "${UPDATE_ALL_OS}" == "WINDOWS" ]] ; then return ; fi
    rm ${GLOG_TEMP} 2> /dev/null || true
    exec 6>&1 ; exec 7>&2 # Saving stdout and stderr
    enable_global_log
    trap trap_global_log EXIT
}

TRAP_GLOBAL_LOG_RAN="false"
trap_global_log() {
    if [[ "${TRAP_GLOBAL_LOG_RAN}" == "true" ]] ; then return ; fi
    mv "${GLOG_TEMP}" "${GLOG_PATH}" 2> /dev/null
    TRAP_GLOBAL_LOG_RAN="true"
}

load_ini_file() {
    local INI_PATH="${1}"

    if [ ! -f ${INI_PATH} ] ; then
        return
    fi

    local TMP=$(mktemp)
    dos2unix < "${INI_PATH}" 2> /dev/null | grep -v "^exit" > ${TMP} || true

    set +u
    source ${TMP}
    set -u

    rm -f ${TMP}
}

load_vars_from_ini() {
    local INI_PATH="${1}"

    if [ ! -f ${INI_PATH} ] ; then
        return
    fi

    local TMP_1=$(mktemp)
    dos2unix < "${INI_PATH}" 2> /dev/null | grep -v "^exit" > ${TMP_1} || true
    for var in "${@:2}" ; do
        local TMP_2=$(mktemp)
        grep "^ *${var}=" ${TMP_1} >> ${TMP_2} || true
        source ${TMP_2}
        rm -f ${TMP_2}
    done
    rm -f ${TMP_1}
}

load_single_var_from_ini() {
    local VAR="${1}"
    local INI_PATH="${2}"

    local TMP_1=$(mktemp)
    dos2unix < "${INI_PATH}" 2> /dev/null | grep -v "^exit" > ${TMP_1} || true

    local TMP_2=$(mktemp)
    grep "^ *${VAR}=" ${TMP_1} >> ${TMP_2} || true

    local -n VALUE="${VAR}"
    VALUE=
    source ${TMP_2}

    rm -f ${TMP_1} ${TMP_2}

    echo "${VALUE}"
}

fetch_or_exit() {
    local SCRIPT_PATH="${1}"
    local SCRIPT_URL="${2}"

    if curl ${CURL_RETRY} --silent --show-error ${SSL_SECURITY_OPTION} --fail --location -o ${SCRIPT_PATH} ${SCRIPT_URL} ; then return ; fi

    echo "There was some network problem."
    echo
    echo "Following file couldn't be downloaded:"
    echo ${@: -1}
    echo
    echo "Please try again later."
    echo
    exit 1
}

fetch_or_continue() {
    local SCRIPT_PATH="${1}"
    local SCRIPT_URL="${2}"

    curl ${CURL_RETRY} --silent --show-error ${SSL_SECURITY_OPTION} --fail --location -o ${SCRIPT_PATH} ${SCRIPT_URL}
}

make_folder() {
    local FOLDER_PATH="${1}"
    mkdir -p "${FOLDER_PATH}"
}

initialize() {
    if [[ "${UPDATE_ALL_PC_UPDATER}" != "true" ]] && [[ "$(pwd)" != "$(cd ${CURRENT_DIR} && pwd)" ]] ; then
        message_ignored_root_ini "update_all.ini"
        message_ignored_root_ini "update.ini"
        message_ignored_root_ini "update_jtcores.ini"
        message_ignored_root_ini "update_unofficials.ini"
        message_ignored_root_ini "update_llapi.ini"
        message_ignored_root_ini "update_bios-getter.ini"
        message_ignored_root_ini "update_mame-getter.ini"
        message_ignored_root_ini "update_hbmame-getter.ini"
        message_ignored_root_ini "update_names-txt.ini"
        message_ignored_root_ini "update_arcade-organizer.ini"
        if [ ${#MESSAGE_IGNORED_ROOT_INI_ARRAY[@]} -ne 0 ] ; then
            echo "NEW CHANGE! As of 2021.07.17, Update All will now look for INI files"
            echo "            stored in the same folder as $(basename ${EXPORTED_INI_PATH%.*}).sh"
            echo "            Any INI files at $(pwd) will be ignored."
            echo


            for INI in "${MESSAGE_IGNORED_ROOT_INI_ARRAY[@]}" ; do
                echo "WARNING! $(pwd)/${INI} will be ignored."
                if [ -f "/media/fat/Scripts/${INI}" ] ; then
                    echo "         /media/fat/Scripts/${INI} will be used instead."
                else
                    echo "         default values will be used instead."
                fi
            done

            echo
            echo "Waiting 30 seconds because of the warning messages..."
            echo
            echo "TIP: Move or remove these files to avoid the warnings."

            sleep 30s
        fi
        cd "${CURRENT_DIR}"
    fi

    if [[ "${UPDATE_ALL_PC_UPDATER}" != "true" ]] && [[ "${AUTO_UPDATE_LAUNCHER}" == "true" ]] && [ -d "${BASE_PATH}/Scripts/" ] ; then
        local OLD_SCRIPT_PATH="${EXPORTED_INI_PATH%.*}.sh"
        if [ ! -f "${OLD_SCRIPT_PATH}" ] || [[ "$(md5sum ${OLD_SCRIPT_PATH} | awk '{print $1}')" != "${UPDATE_ALL_LAUNCHER_MD5}" ]] ; then
            local MAYBE_NEW_LAUNCHER="/tmp/ua_maybe_new_launcher.sh"
            rm "${MAYBE_NEW_LAUNCHER}" 2> /dev/null || true
            fetch_or_continue "${MAYBE_NEW_LAUNCHER}" "${UPDATE_ALL_URL}" > /dev/null 2>&1 || true
            if [ -f "${MAYBE_NEW_LAUNCHER}" ] && [[ "$(md5sum ${MAYBE_NEW_LAUNCHER} | awk '{print $1}')" == "${UPDATE_ALL_LAUNCHER_MD5}" ]] ; then
                rm "${OLD_SCRIPT_PATH}" 2> /dev/null || true
                cp "${MAYBE_NEW_LAUNCHER}" "${OLD_SCRIPT_PATH}" || true
            fi
        fi
    fi

    initialize_global_log

    echo "Executing 'Update All' script"
    echo "The All-in-One Updater for MiSTer"
    echo "Version ${UPDATE_ALL_VERSION}"

    if [[ "${UPDATE_ALL_PC_UPDATER}" == "true" ]] ; then
        EXPORTED_INI_PATH="update_all.ini"
    fi

    mkdir -p "${CONFIG_FOLDER_PATH}"
    [ -d "${CACHE_UPDATE_ALL_PATH}" ] && mv "${CACHE_UPDATE_ALL_PATH}" "${CONFIG_UPDATE_ALL_PATH}"
    [ -d "${CACHE_MAME_GETTER_PATH}" ] && mv "${CACHE_MAME_GETTER_PATH}" "${CONFIG_MAME_GETTER_PATH}"
    [ -d "${CACHE_HBMAME_GETTER_PATH}" ] && mv "${CACHE_HBMAME_GETTER_PATH}" "${CONFIG_HBMAME_GETTER_PATH}"
    [ -d "${CACHE_ARCADE_ORGANIZER_PATH}" ] && mv "${CACHE_ARCADE_ORGANIZER_PATH}" "${CONFIG_ARCADE_ORGANIZER_PATH}"

    WORK_PATH="${WORK_OLD_PATH}"
    if [ ! -d "${WORK_PATH}" ] ; then
        WORK_PATH="${WORK_NEW_PATH}"
        if [ ! -d "${WORK_PATH}" ] ; then
            make_folder "${WORK_PATH}"

            echo
            echo "Creating '${WORK_PATH}' for the first time."

            if [ ! -f "${EXPORTED_INI_PATH}" ] ; then
                echo "MAIN_UPDATER_INI=\"update.ini\"" >> "${EXPORTED_INI_PATH}"
                echo "JOTEGO_UPDATER_INI=\"update_jtcores.ini\"" >> "${EXPORTED_INI_PATH}"
                echo "UNOFFICIAL_UPDATER_INI=\"update_unofficials.ini\"" >> "${EXPORTED_INI_PATH}"
                echo "LLAPI_UPDATER_INI=\"update_llapi.ini\"" >> "${EXPORTED_INI_PATH}"
                if [ -f /media/fat/payoyo_cheese.txt ] ; then
                    echo "DOWNLOADER_WHEN_POSSIBLE=\"true\"" >> "${EXPORTED_INI_PATH}"
                fi
            fi
        fi
    fi

    GLOG_PATH="${WORK_PATH}/${LOG_FILENAME}"

    echo
    echo "Reading INI file '${EXPORTED_INI_PATH}':"
    if [ -f "${EXPORTED_INI_PATH}" ] ; then
        cp "${EXPORTED_INI_PATH}" "${ORIGINAL_INI_PATH}" 2> /dev/null || true
        load_ini_file "${ORIGINAL_INI_PATH}"
        post_load_update_all_ini
        echo "OK."
    else
        echo "Not found."
    fi

    if [ -f /media/fat/payoyo_cheese.txt ] && [[ "${DOWNLOADER_WHEN_POSSIBLE}" == "false" ]] ; then
        if ! grep -q '[^[:space:]]' "${MAIN_UPDATER_INI}" 2> /dev/null && \
            ! grep -q '[^[:space:]]' "${UNOFFICIAL_UPDATER_INI}" 2> /dev/null && \
            ! grep -q '[^[:space:]]' "${LLAPI_UPDATER_INI}" 2> /dev/null && \
            ! grep -v "DOWNLOAD_BETA_CORES=" "${JOTEGO_UPDATER_INI}" 2> /dev/null | grep -q '[^[:space:]]' ; then

            echo "DOWNLOADER_WHEN_POSSIBLE=\"true\"" >> "${EXPORTED_INI_PATH}"
            DOWNLOADER_WHEN_POSSIBLE="true"
        fi
    fi

    export SSL_SECURITY_OPTION
    export CURL_RETRY

    if [[ "${UPDATE_ALL_OS}" == "WINDOWS" ]] ; then
        export TERMINFO="terminfo"
    fi
}


MESSAGE_IGNORED_ROOT_INI_ARRAY=()
message_ignored_root_ini() {
    if [ -f "${1}" ] ; then
        MESSAGE_IGNORED_ROOT_INI_ARRAY+=("${1}")
    fi
}

post_load_update_all_ini() {
    if [[ "${UPDATE_ALL_PC_UPDATER}" != "true" ]] ; then
        return
    fi
    ARCADE_ORGANIZER="false"
    for ref in "${INI_REFERENCES[@]}" ; do
        local -n INI_FILE="${ref}"
        INI_FILE=$(echo "${INI_FILE}" | sed "s%${BASE_PATH}/Scripts/%%g")
    done
}

SELECT_MAIN_UPDATER_RET=
select_main_updater() {
    case "${ENCC_FORKS}" in
        true)
            SELECT_MAIN_UPDATER_RET="${MISTER_DB9_UPDATER_URL}"
            ;;
        *)
            SELECT_MAIN_UPDATER_RET="${MISTER_DEVEL_UPDATER_URL}"
            ;;
    esac
}

draw_separator() {
    echo
    echo
    echo "################################################################################"
    echo "#==============================================================================#"
    echo "################################################################################"
    echo
    sleep 1
}

RUN_UPDATER_SCRIPT_RET=0
run_updater_script() {
    local SCRIPT_URL="${1}"
    local SCRIPT_INI="${2}"

    draw_separator

    echo "Downloading and executing"
    [[ ${SCRIPT_URL} =~ ^([a-zA-Z]+://)?raw.githubusercontent.com(:[0-9]+)?/([a-zA-Z0-9_-]*)/([a-zA-Z0-9_-]*)/.*$ ]] || true
    echo "https://github.com/${BASH_REMATCH[3]}/${BASH_REMATCH[4]}"
    echo ""

    local SCRIPT_PATH="/tmp/ua_current_updater.sh"
    rm ${SCRIPT_PATH} 2> /dev/null || true

    fetch_or_exit "${SCRIPT_PATH}" "${SCRIPT_URL}"

    sed -i "s%INI_PATH=%INI_PATH=\"${SCRIPT_INI}\" #%g" ${SCRIPT_PATH}
    sed -i 's/${AUTOREBOOT}/false/g' ${SCRIPT_PATH}
    if [[ "${SCRIPT_URL}" != "${MISTER_DEVEL_LINUX_ONLY_UPDATER_URL}" ]] ; then
        sed -i 's/UPDATE_LINUX="true"/UPDATE_LINUX="false"/g' ${SCRIPT_PATH}
    fi
    if [[ "${UPDATE_ALL_PC_UPDATER}" == "true" ]] ; then
        sed -i 's/\/media\/fat/\.\./g ' ${SCRIPT_PATH}
    fi
    if [[ "${UPDATE_ALL_OS}" == "WINDOWS" ]] ; then
        sed -i "s/ *60)/77)/g" ${SCRIPT_PATH}
    fi
    if [[ "${SCRIPT_URL}" == "${MISTER_DEVEL_UPDATER_URL}" ]] && [ -f "${MISTER_MAIN_UPDATER_WORK_FOLDER}/db9" ] ; then
        sed -i 's/if \[\[ "$MAX_VERSION" > "$MAX_LOCAL_VERSION" \]\]/if \[\[ "$MAX_VERSION" > "$MAX_LOCAL_VERSION" \]\] || ! \[\[ "${CORE_URL}" =~ SD-Installer \]\]/g' ${SCRIPT_PATH}
        pushd "${MISTER_MAIN_UPDATER_WORK_FOLDER}" > /dev/null 2>&1
        rm -rf db9 || true
        rm -rf *.last_successful_run || true
        rm -rf *.log || true
        rm -rf menu_* || true
        rm -rf MiSTer_* || true
        popd > /dev/null 2>&1
    fi

    set +e
    cat ${SCRIPT_PATH} | bash -
    RUN_UPDATER_SCRIPT_RET=$?
    set -e

    sleep ${WAIT_TIME_FOR_READING}
}

RUN_DOWNLOADER_SCRIPT_RET=0
run_downloader_script() {
    local SCRIPT_URL="${1}"

    draw_separator

    if [[ "${2:-}" != "" ]] ; then
        echo "Running ${2:-}"
        echo
    fi

    local SCRIPT_PATH="/tmp/ua_current_updater.sh"
    rm ${SCRIPT_PATH} 2> /dev/null || true

    fetch_or_exit "${SCRIPT_PATH}" "${SCRIPT_URL}"
    chmod +x ${SCRIPT_PATH}

    export DOWNLOADER_LAUNCHER_PATH="downloader.ini"
    export ALLOW_REBOOT="0"

    set +e
    ${SCRIPT_PATH}
    RUN_DOWNLOADER_SCRIPT_RET=$?
    set -e

    sleep ${WAIT_TIME_FOR_READING}
}

RUN_MAME_GETTER_SCRIPT_SKIPPED=
run_mame_getter_script() {
    local SCRIPT_TITLE="${1}"
    local SCRIPT_URL="${2}"
    local SCRIPT_INI="${3}"

    local SCRIPT_FILENAME="${SCRIPT_URL/*\//}"
    local SCRIPT_PATH="/tmp/${SCRIPT_FILENAME%.*}.sh"

    draw_separator

    echo "Downloading the most recent $(basename ${SCRIPT_FILENAME}) script."
    echo " "

    fetch_or_exit "${SCRIPT_PATH}" "${SCRIPT_URL}"
    echo

    if [[ "${UPDATE_ALL_PC_UPDATER}" == "true" ]] ; then
        sed -i 's/\/media\/fat/\.\./g ' ${SCRIPT_PATH}
    fi
    if [[ "${UPDATE_ALL_OS}" == "WINDOWS" ]] ; then
        sed -i 's/#!\/bin\/bash/#!bash/g ' ${SCRIPT_PATH}
    fi

    echo
    echo "STARTING: ${SCRIPT_TITLE}"
    chmod +x ${SCRIPT_PATH}
    sed -i "s%INIFILE=%INIFILE=\"${SCRIPT_INI}\" #%g" ${SCRIPT_PATH}

    set +e
    ${SCRIPT_PATH}
    local SCRIPT_RET=$?
    set -e

    if [ $SCRIPT_RET -ne 0 ]; then
        FAILING_UPDATERS+=("${SCRIPT_TITLE}")
    fi

    rm ${SCRIPT_PATH}
    echo "FINISHED: ${SCRIPT_TITLE}"
    echo
    sleep ${WAIT_TIME_FOR_READING}
}

RUN_QUIET_MAME_GETTER_SCRIPT_OUTPUT=
run_quiet_mame_getter_script() {
    local SCRIPT_URL="${1}"
    local SCRIPT_INI="${2}"
    local SCRIPT_ARGS="${3}"

    RUN_QUIET_MAME_GETTER_SCRIPT_OUTPUT=""

    local SCRIPT_PATH="/tmp/ua_temp_script"
    rm "${SCRIPT_PATH}" 2> /dev/null || true

    fetch_or_continue "${SCRIPT_PATH}" "${SCRIPT_URL}" > /dev/null 2>&1 || return

    if [[ "${UPDATE_ALL_PC_UPDATER}" == "true" ]] ; then
        sed -i 's/\/media\/fat/\.\./g ' ${SCRIPT_PATH}
    fi
    if [[ "${UPDATE_ALL_OS}" == "WINDOWS" ]] ; then
        sed -i 's/#!\/bin\/bash/#!bash/g ' ${SCRIPT_PATH}
    fi
    sed -i "s%INIFILE=%INIFILE=\"${SCRIPT_INI}\" #%g" ${SCRIPT_PATH}

    chmod +x ${SCRIPT_PATH}
    ${SCRIPT_PATH} "${SCRIPT_ARGS}" > "/tmp/ua_temp_output"

    RUN_QUIET_MAME_GETTER_SCRIPT_OUTPUT="/tmp/ua_temp_output"
}

category_path() {
    local CATEGORY="${1}"
    local CURRENT_UPDATER_INI="${2}"
    (
        declare -A CORE_CATEGORY_PATHS
        if [ -f ${CURRENT_UPDATER_INI} ] ; then
            local TMP=$(mktemp)
            dos2unix < "${CURRENT_UPDATER_INI}" 2> /dev/null | grep -v "^exit" > ${TMP}
            source ${TMP}
            rm -f ${TMP}
        fi
        echo ${CORE_CATEGORY_PATHS[${CATEGORY}]:-${BASE_PATH}/_Arcade}
    )
}

arcade_paths() {
    declare -A PATHS

    for INI in "${@}" ; do
        PATHS[$(category_path "arcade-cores" ${INI})]=1
    done
    for p in "${!PATHS[@]}" ; do
        echo ${p}
    done
}

delete_if_empty() {
    local DELETED_EMPTY_DIRS=()
    for dir in "${@}" ; do
        if [ -d "${dir}" ] ; then
            local LS_RET=$(ls -A "${dir}")
            if [ -z "${LS_RET}" ] ; then
                rm -rf "${dir}"
                DELETED_EMPTY_DIRS+=("${dir}")
            fi
        fi
    done

    if [ ${#DELETED_EMPTY_DIRS[@]} -ge 1 ] ; then
        echo "Following directories have been deleted because they were empty:"
        for dir in "${DELETED_EMPTY_DIRS[@]}" ; do
            echo " - $dir"
        done
        echo
    fi
}

install_scripts() {
    draw_separator

    echo "Installing update_all.sh in MiSTer /Scripts directory."
    make_folder "../Scripts"

    rm /tmp/ua_install.update_all.sh 2> /dev/null || true

    set +e
    fetch_or_continue "/tmp/ua_install.update_all.sh" "${UPDATE_ALL_URL}"
    local RET_CURL=$?
    set -e

    if [ ${RET_CURL} -ne 0 ] ; then
        FAILING_UPDATERS+=("Install-update_all.sh-to/Scripts")
        return
    fi

    cp /tmp/ua_install.update_all.sh ../Scripts/update_all.sh

    local INI_FILES=( \
        "update_all.ini" \
        "${MAIN_UPDATER_INI}" \
        "${JOTEGO_UPDATER_INI}" \
        "${UNOFFICIAL_UPDATER_INI}" \
        "${LLAPI_UPDATER_INI}" \
        "${BIOS_GETTER_INI}" \
        "${MAME_GETTER_INI}" \
        "${HBMAME_GETTER_INI}" \
        "${NAMES_TXT_UPDATER_INI}" \
        "${ARCADE_ORGANIZER_INI}" \
    )

    for ref in "${INI_REFERENCES[@]}" ; do
        local -n INI_FILE="${ref}"
        if [ -f "${INI_FILE}" ] ; then
            echo "           ${INI_FILE} too."
            cp "${INI_FILE}" "../Scripts/${INI_FILE}"
        fi
    done

    echo
    echo "Installing arcade_organizer.sh in MiSTer /Scripts directory."
    rm /tmp/ua_install.arcade_organizer.sh 2> /dev/null || true

    set +e
    fetch_or_continue "/tmp/ua_install.arcade_organizer.sh" "${ARCADE_ORGANIZER_URL}"
    local RET_CURL=$?
    set -e

    if [ ${RET_CURL} -ne 0 ] ; then
        FAILING_UPDATERS+=("Install-arcade_organizer.sh-to/Scripts")
        return
    fi

    cp /tmp/ua_install.arcade_organizer.sh ../Scripts/arcade_organizer.sh
}

sequence() {
    echo "Sequence:"
    local UPDATER_KIND="Updater"
    if [[ "${DOWNLOADER_WHEN_POSSIBLE}" == "true" ]] && [[ "${UPDATE_ALL_PC_UPDATER}" != "true" ]] ; then
        UPDATER_KIND="Downloader"
    fi
    if [[ "${MAIN_UPDATER}" == "true" ]] ; then
        if [[ "${ENCC_FORKS}" == "true" ]] ; then
            echo "- Main ${UPDATER_KIND}: DB9 / SNAC8"
        else
            echo "- Main ${UPDATER_KIND}: MiSTer-devel"
        fi
    fi
    if [[ "${JOTEGO_UPDATER}" == "true" ]] ; then
        echo "- Jotego ${UPDATER_KIND}"
    fi
    if [[ "${UNOFFICIAL_UPDATER}" == "true" ]] ; then
        echo "- Unofficial ${UPDATER_KIND}"
    fi
    if [[ "${LLAPI_UPDATER}" == "true" ]] ; then
        echo "- LLAPI ${UPDATER_KIND}"
    fi
    if [[ "${ARCADE_OFFSET_DOWNLOADER}" == "true" ]] ; then
        echo "- Arcade Offset Downloader"
    fi
    if [[ "${BIOS_GETTER}" == "true" ]] ; then
        echo "- BIOS Getter"
    fi
    if [[ "${MAME_GETTER}" == "true" ]] ; then
        echo "- MAME Getter"
    fi
    if [[ "${HBMAME_GETTER}" == "true" ]] ; then
        echo "- HBMAME Getter"
    fi
    if [[ "${NAMES_TXT_UPDATER}" == "true" ]] ; then
        echo "- Names TXT Updater"
    fi
    if [[ "${ARCADE_ORGANIZER}" == "true" ]] ; then
        echo "- Arcade Organizer"
    fi
    if [[ "${UPDATE_ALL_PC_UPDATER}" == "true" ]] ; then
        echo "- Install update_all.sh && arcade_organizer.sh at /Scripts"
    fi
}

countdown() {
    local BOLD_IN="$(tput bold)"
    local BOLD_OUT="$(tput sgr0)"
    echo
    echo " ${BOLD_IN}*${BOLD_OUT}Press <${BOLD_IN}UP${BOLD_OUT}>, To enter the SETTINGS screen."
    echo -n " ${BOLD_IN}*${BOLD_OUT}Press <${BOLD_IN}DOWN${BOLD_OUT}>, To continue now."
    local COUNTDOWN_SELECTION="continue"
    if [ -f "${SETTINGS_ON_FILENAME}" ] ; then
        COUNTDOWN_TIME=-1
        COUNTDOWN_SELECTION="menu"
    fi
    set +e
    echo -e '\e[3A\e[K'
    for (( i=0; i <= COUNTDOWN_TIME ; i++)); do
        local SECONDS=$(( COUNTDOWN_TIME - i ))
        if (( SECONDS < 10 )) ; then
            SECONDS=" ${SECONDS}"
        fi
        printf "\rStarting in ${SECONDS} seconds."
        for (( j=0; j < i; j++)); do
            printf "."
        done
        read -r -s -N 1 -t 1 key
        if [[ "${key}" == "A" ]]; then
                COUNTDOWN_SELECTION="menu"
                break
        elif [[ "${key}" == "B" ]]; then
                COUNTDOWN_SELECTION="continue"
                break
        fi
    done
    set -e
    echo -e '\e[2B\e[K'
    if [[ "${COUNTDOWN_SELECTION}" == "menu" ]] ; then
        settings_menu_update_all
        sequence
        sleep ${WAIT_TIME_FOR_READING}
    fi
}

run_update_all() {

    initialize
    echo

    sequence
    echo

    if dialog > /dev/null 2>&1 && [ ${COUNTDOWN_TIME} -gt 0 ] ; then
        if [[ -t 0 || -t 1 || -t 2 ]] ; then
            disable_global_log
            countdown
            enable_global_log
        else
            echo "SORRY!"
            echo "Can't display the SETTINGS screen because fb terminal is off."
            echo "Maybe you have fb_terminal=0 on MiSTer.ini?"
            echo "NOTE: It could still work if you also add the following lines in MiSTer.ini:"
            echo "    [Menu]"
            echo "    vga_scaler=1"
            sleep ${WAIT_TIME_FOR_READING}
            sleep ${WAIT_TIME_FOR_READING}
        fi
        echo
    fi

    echo "Start time: $(date)"

    local REBOOT_NEEDED="false"
    FAILING_UPDATERS=()

    if [[ "${MAIN_UPDATER}" == "true" ]] ; then
        if [[ "${DOWNLOADER_WHEN_POSSIBLE}" == "true" ]] && [[ "${UPDATE_ALL_PC_UPDATER}" != "true" ]] ; then
            export UPDATE_LINUX="false"
            if [[ "${ENCC_FORKS}" == "true" ]] ; then
                export DEFAULT_DB_URL="${DOWNLOADER_DB9_DB_URL}"
            fi
            run_downloader_script "${DOWNLOADER_URL}" "MiSTer Downloader"
            if [ $RUN_DOWNLOADER_SCRIPT_RET -ne 0 ]; then
                FAILING_UPDATERS+=("MiSTer Downloader")
            fi
        else
            select_main_updater
            run_updater_script ${SELECT_MAIN_UPDATER_RET} ${MAIN_UPDATER_INI}
            if [ $RUN_UPDATER_SCRIPT_RET -ne 0 ]; then
                FAILING_UPDATERS+=("${MISTER_MAIN_UPDATER_WORK_FOLDER}/${LOG_FILENAME}")
            fi
            sleep 1
            if [[ "${UPDATE_ALL_PC_UPDATER}" != "true" ]] && tail -n 30 ${GLOG_TEMP} | grep -q "You should reboot" ; then
                REBOOT_NEEDED="true"
            fi
        fi
    fi

    if [[ "${JOTEGO_UPDATER}" == "true" ]] ; then
        if [[ "${DOWNLOADER_WHEN_POSSIBLE}" == "true" ]] && [[ "${UPDATE_ALL_PC_UPDATER}" != "true" ]] ; then
            settings_reset_domain_ini_files
            settings_add_domain_ini_file "update_jtcores.ini"
            load_vars_from_ini "$(settings_domain_ini_file ${JOTEGO_UPDATER_INI})" "DOWNLOAD_BETA_CORES"
            if [[ "${DOWNLOAD_BETA_CORES:-false}" == "true" ]] ; then
                export DEFAULT_DB_URL="${DOWNLOADER_JT_BETAS_DB_URL}"
            else
                export DEFAULT_DB_URL="${DOWNLOADER_JT_STABLE_DB_URL}"
            fi
            export DEFAULT_DB_ID="${DOWNLOADER_JT_DB_ID}"
            run_downloader_script "${DOWNLOADER_URL}" "JT Downloader"
            if [ $RUN_DOWNLOADER_SCRIPT_RET -ne 0 ]; then
                FAILING_UPDATERS+=("JT Downloader")
            fi
        else
            run_updater_script "${JOTEGO_UPDATER_URL}" "${JOTEGO_UPDATER_INI}"
            if [ $RUN_UPDATER_SCRIPT_RET -ne 0 ]; then
                FAILING_UPDATERS+=("${JOTEGO_UPDATER_WORK_FOLDER}/${LOG_FILENAME}")
            fi
        fi
    fi

    if [[ "${UNOFFICIAL_UPDATER}" == "true" ]] ; then
        if [[ "${DOWNLOADER_WHEN_POSSIBLE}" == "true" ]] && [[ "${UPDATE_ALL_PC_UPDATER}" != "true" ]] ; then
            export DEFAULT_DB_URL="${DOWNLOADER_UNOFFICIALS_DB_URL}"
            export DEFAULT_DB_ID="${DOWNLOADER_UNOFFICIALS_DB_ID}"
            run_downloader_script "${DOWNLOADER_URL}" "Unofficial Downloader"
            if [ $RUN_DOWNLOADER_SCRIPT_RET -ne 0 ]; then
                FAILING_UPDATERS+=("Unofficial Downloader")
            fi
        else
            run_updater_script "${UNOFFICIAL_UPDATER_URL}" "${UNOFFICIAL_UPDATER_INI}"
            if [ $RUN_UPDATER_SCRIPT_RET -ne 0 ]; then
                FAILING_UPDATERS+=("${UNOFFICIAL_UPDATER_WORK_FOLDER}/${LOG_FILENAME}")
            fi
        fi
    fi

    if [[ "${LLAPI_UPDATER}" == "true" ]] ; then
        if [[ "${DOWNLOADER_WHEN_POSSIBLE}" == "true" ]] && [[ "${UPDATE_ALL_PC_UPDATER}" != "true" ]] ; then
            export DEFAULT_DB_URL="${DOWNLOADER_LLAPI_DB_URL}"
            export DEFAULT_DB_ID="${DOWNLOADER_LLAPI_DB_ID}"
            run_downloader_script "${DOWNLOADER_URL}" "LLAPI Downloader"
            if [ $RUN_DOWNLOADER_SCRIPT_RET -ne 0 ]; then
                FAILING_UPDATERS+=("LLAPI Downloader")
            fi
        else
            run_updater_script "${LLAPI_UPDATER_URL}" "${LLAPI_UPDATER_INI}"
            if [ $RUN_UPDATER_SCRIPT_RET -ne 0 ]; then
                FAILING_UPDATERS+=("LLAPI")
            fi
        fi
    fi

    if [[ "${ARCADE_OFFSET_DOWNLOADER}" == "true" ]] ; then
        export DEFAULT_DB_URL="${DOWNLOADER_ARCADE_OFFSET_DB_URL}"
        export DEFAULT_DB_ID="${DOWNLOADER_ARCADE_OFFSET_DB_ID}"
        run_downloader_script "${DOWNLOADER_URL}" "Arcade Offset Downloader"
        if [ $RUN_DOWNLOADER_SCRIPT_RET -ne 0 ]; then
            FAILING_UPDATERS+=("Arcade Offset Downloader")
        fi
    fi

    if [[ "${BIOS_GETTER}" == "true" ]] ; then
        run_mame_getter_script "BIOS-GETTER" "${BIOS_GETTER_URL}" "${BIOS_GETTER_INI}"
        sleep ${WAIT_TIME_FOR_READING}
        sleep ${WAIT_TIME_FOR_READING}
    fi

    if [[ "${MAME_GETTER}" == "true" ]] ; then
        run_mame_getter_script "MAME-GETTER" "${MAME_GETTER_URL}" "${MAME_GETTER_INI}"
    fi

    if [[ "${HBMAME_GETTER}" == "true" ]] ; then
        run_mame_getter_script "HBMAME-GETTER" "${HBMAME_GETTER_URL}" "${HBMAME_GETTER_INI}"
    fi

    if [[ "${NAMES_TXT_UPDATER}" == "true" ]] ; then
        run_updater_script "${NAMES_TXT_UPDATER_URL}" "${NAMES_TXT_UPDATER_INI}"
        if [ $RUN_UPDATER_SCRIPT_RET -ne 0 ]; then
            FAILING_UPDATERS+=("Names.txt_Updater")
        fi
    fi

    if [[ "${ARCADE_ORGANIZER}" == "true" ]] ; then
        local ao_url=
        if [[ "${ARCADE_ORGANIZER_2_ALPHA_ENABLED}" == "true" ]] ; then
            ao_url="${ARCADE_ORGANIZER_2BETA_URL}"
        else
            ao_url="${ARCADE_ORGANIZER_URL}"
        fi
        run_mame_getter_script "_ARCADE-ORGANIZER" "${ao_url}" "${ARCADE_ORGANIZER_INI}"
    fi

    if [[ "${UPDATE_ALL_PC_UPDATER}" == "true" ]] ; then
        install_scripts
    fi

    draw_separator

    delete_if_empty \
        "${BASE_PATH}/games/mame" \
        "${BASE_PATH}/games/hbmame" \
        "${BASE_PATH}/_Arcade/mame" \
        "${BASE_PATH}/_Arcade/hbmame" \
        "${BASE_PATH}/_Arcade/mra_backup" \
        "${BASE_PATH}/_Arcade/_Organized" \
        "${BASE_PATH}/_Arcade Organized" \
        "/media/fat/Scripts/.cache"

    if [[ "${UPDATE_ALL_PC_UPDATER}" != "true" ]] && [[ "${MAIN_UPDATER}" == "true" ]] ; then
        if [[ "${KEEP_USBMOUNT_CONF}" == "true" ]] ; then
            cp "${USBMOUNT_CONF_PATH}" "${USBMOUNT_CONF_TMP}"
            echo "KEEP_USBMOUNT_CONF: ${USBMOUNT_CONF_PATH} saved."
        fi
        
        if [[ "${DOWNLOADER_WHEN_POSSIBLE}" == "true" ]] && [[ "${UPDATE_ALL_PC_UPDATER}" != "true" ]] ; then
            export UPDATE_LINUX="only"
            unset DEFAULT_DB_URL
            unset DEFAULT_DB_ID
            run_downloader_script "${DOWNLOADER_URL}" "Linux Update"
            if [ $RUN_DOWNLOADER_SCRIPT_RET -ne 0 ]; then
                FAILING_UPDATERS+=("${MISTER_DOWNLOADER_WORK_FOLDER}/downloader.log")
            fi
        else
            run_updater_script ${MISTER_DEVEL_LINUX_ONLY_UPDATER_URL} ${MAIN_UPDATER_INI}
            if [ $RUN_UPDATER_SCRIPT_RET -ne 0 ]; then
                FAILING_UPDATERS+=("${MISTER_MAIN_UPDATER_WORK_FOLDER}/${LOG_FILENAME}")
            fi
            sleep 1
            if tail -n 30 ${GLOG_TEMP} | grep -q "You should reboot" ; then
                REBOOT_NEEDED="true"
            fi
        fi
        if [[ "${KEEP_USBMOUNT_CONF}" == "true" ]] && ! diff -q "${USBMOUNT_CONF_PATH}" "${USBMOUNT_CONF_TMP}" ; then
            sync
            cp "${USBMOUNT_CONF_PATH}" "${USBMOUNT_CONF_PATH}.backup"
            cp "${USBMOUNT_CONF_TMP}" "${USBMOUNT_CONF_PATH}"
            sync
            echo "${USBMOUNT_CONF_PATH} was replaced by the Main Downloader!"
            echo "Restoring old version because KEEP_USBMOUNT_CONF=\"true\""
            echo "There is a backup for the newest version available at '${USBMOUNT_CONF_PATH}.backup' in case you want to revert this operation."
            sleep ${WAIT_TIME_FOR_READING}
            sleep ${WAIT_TIME_FOR_READING}
            sleep ${WAIT_TIME_FOR_READING}
        fi
    fi

    local EXIT_CODE=0
    if [ ${#FAILING_UPDATERS[@]} -ge 1 ] ; then
        echo "There were some errors in the Updaters."
        echo "Therefore, MiSTer hasn't been fully updated."
        echo
        echo "Check these logs from the Updaters that failed:"
        for log_file in ${FAILING_UPDATERS[@]} ; do
            echo " - $log_file"
        done
        echo
        echo "Maybe a network problem?"
        echo "Check your connection and then run this script again."
        EXIT_CODE=1
    else
        echo "Update All ${UPDATE_ALL_VERSION} finished. Your MiSTer has been updated successfully!"
    fi

    local END_TIME=$(date)

    echo
    echo "End time: ${END_TIME}"
    echo

    if [[ "${UPDATE_ALL_OS}" != "WINDOWS" ]] ; then
        echo "Full log for more details: ${GLOG_PATH}"
        echo
    fi

    if [[ "${UPDATE_ALL_PC_UPDATER}" != "true" ]] && { \
        [ -f /tmp/MiSTer_downloader_needs_reboot ] || \
        [ -f /tmp/ua_reboot_needed ] || \
        [[ "${REBOOT_NEEDED}" == "true" ]] ; \
    } ; then
        REBOOT_PAUSE=$((2 + WAIT_TIME_FOR_READING * 2))
        if [[ "${AUTOREBOOT}" == "true" && "${REBOOT_PAUSE}" -ge 0 ]] ; then
            echo "Rebooting in ${REBOOT_PAUSE} seconds"
            sleep "${REBOOT_PAUSE}"
            trap_global_log
            reboot now
        else
            echo "You should reboot"
            echo
        fi
    fi

    exit ${EXIT_CODE:-1}
}

# # #      S E T T I N G S     S C R E E N      # # #

### SETTINGS GLOBAL TMP VARS ##
SETTINGS_TMP_BREAK="/tmp/ua_break"
SETTINGS_TMP_CONTINUE="/tmp/ua_continue"
SETTINGS_TMP_BLACK_DIALOGRC="/tmp/ua_black_dialog"
SETTINGS_TMP_RED_DIALOGRC="/tmp/ua_red_dialog"

settings_menu_update_all() {
    rm "${SETTINGS_TMP_BREAK}" 2> /dev/null || true
    rm "${SETTINGS_TMP_CONTINUE}" 2> /dev/null || true

    ### SETTINGS GLOBAL OPTIONS ##
    SETTINGS_OPTIONS_MAIN_UPDATER=("true" "false")
    SETTINGS_OPTIONS_ENCC_FORKS=("false" "true")
    SETTINGS_OPTIONS_JOTEGO_UPDATER=("true" "false")
    SETTINGS_OPTIONS_UNOFFICIAL_UPDATER=("false" "true")
    SETTINGS_OPTIONS_LLAPI_UPDATER=("false" "true")
    SETTINGS_OPTIONS_BIOS_GETTER=("true" "false")
    SETTINGS_OPTIONS_MAME_GETTER=("true" "false")
    SETTINGS_OPTIONS_HBMAME_GETTER=("true" "false")
    SETTINGS_OPTIONS_ARCADE_ORGANIZER=("true" "false")
    SETTINGS_OPTIONS_NAMES_TXT_UPDATER=("false" "true")

    ### SETTINGS INI FILES ##
    settings_reset_domain_ini_files
    settings_add_domain_ini_file "${EXPORTED_INI_PATH}"
    settings_add_domain_ini_file "update.ini"
    settings_add_domain_ini_file "update_jtcores.ini"
    settings_add_domain_ini_file "update_unofficials.ini"
    settings_add_domain_ini_file "update_llapi.ini"
    settings_add_domain_ini_file "update_bios-getter.ini"
    settings_add_domain_ini_file "update_mame-getter.ini"
    settings_add_domain_ini_file "update_hbmame-getter.ini"
    settings_add_domain_ini_file "update_names-txt.ini"
    settings_add_domain_ini_file "update_arcade-organizer.ini"
    settings_add_domain_ini_file "${MAIN_UPDATER_INI}"
    settings_add_domain_ini_file "${JOTEGO_UPDATER_INI}"
    settings_add_domain_ini_file "${UNOFFICIAL_UPDATER_INI}"
    settings_add_domain_ini_file "${LLAPI_UPDATER_INI}"
    settings_add_domain_ini_file "${BIOS_GETTER_INI}"
    settings_add_domain_ini_file "${MAME_GETTER_INI}"
    settings_add_domain_ini_file "${HBMAME_GETTER_INI}"
    settings_add_domain_ini_file "${NAMES_TXT_UPDATER_INI}"
    settings_add_domain_ini_file "${ARCADE_ORGANIZER_INI}"
    settings_create_domain_ini_files

    rm "${SETTINGS_TMP_BLACK_DIALOGRC}" 2> /dev/null || true
    dialog --create-rc "${SETTINGS_TMP_BLACK_DIALOGRC}"
    sed -i "s/use_colors = OFF/use_colors = ON/g;
            s/use_shadow = OFF/use_shadow = ON/g;
            s/BLUE/BLACK/g" "${SETTINGS_TMP_BLACK_DIALOGRC}"

    rm "${SETTINGS_TMP_RED_DIALOGRC}" 2> /dev/null || true
    dialog --create-rc "${SETTINGS_TMP_RED_DIALOGRC}"
    sed -i "s/use_colors = OFF/use_colors = ON/g;
            s/use_shadow = OFF/use_shadow = ON/g;
            s/BLUE/RED/g" "${SETTINGS_TMP_RED_DIALOGRC}"

    local TMP=$(mktemp)
    while true ; do
        (
            local MAIN_UPDATER="${SETTINGS_OPTIONS_MAIN_UPDATER[0]}"
            local JOTEGO_UPDATER="${SETTINGS_OPTIONS_JOTEGO_UPDATER[0]}"
            local UNOFFICIAL_UPDATER="${SETTINGS_OPTIONS_UNOFFICIAL_UPDATER[0]}"
            local LLAPI_UPDATER="${SETTINGS_OPTIONS_LLAPI_UPDATER[0]}"
            local BIOS_GETTER="${SETTINGS_OPTIONS_BIOS_GETTER[0]}"
            local MAME_GETTER="${SETTINGS_OPTIONS_MAME_GETTER[0]}"
            local HBMAME_GETTER="${SETTINGS_OPTIONS_HBMAME_GETTER[0]}"
            local ARCADE_ORGANIZER="${SETTINGS_OPTIONS_ARCADE_ORGANIZER[0]}"
            local NAMES_TXT_UPDATER="${SETTINGS_OPTIONS_NAMES_TXT_UPDATER[0]}"
            local ENCC_FORKS="${SETTINGS_OPTIONS_ENCC_FORKS[0]}"
            local ARCADE_ORGANIZER_2_ALPHA_ENABLED="false"
            local DOWNLOADER_WHEN_POSSIBLE="false"

            load_ini_file "$(settings_domain_ini_file ${EXPORTED_INI_PATH})"

            if [[ "${UPDATE_ALL_PC_UPDATER}" == "true" ]] ; then
                ARCADE_ORGANIZER="false"
            fi

            local SCRIPT_TYPE=
            if [[ "${DOWNLOADER_WHEN_POSSIBLE}" == "true" ]] && [[ "${UPDATE_ALL_PC_UPDATER}" != "true" ]] ; then
                SCRIPT_TYPE="Downloader"
            else
                SCRIPT_TYPE="Updater"
            fi

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 Main ${SCRIPT_TYPE}"
            fi

            set +e
            dialog --keep-window \
                --default-item "${DEFAULT_SELECTION}" \
                --cancel-label "Abort" --ok-label "Select" --extra-button --extra-label "Toggle" \
                --title "Update All ${UPDATE_ALL_VERSION} Settings" \
                --menu "Settings loaded from '$(settings_normalize_ini_file ${EXPORTED_INI_PATH})'" 19 75 25 \
                "1 Main ${SCRIPT_TYPE}"  "$(settings_active_tag ${MAIN_UPDATER}) Main MiSTer cores from $([[ ${ENCC_FORKS} == 'true' ]] && echo 'MiSTer-DB9' || echo 'MiSTer-devel')" \
                "2 Jotego ${SCRIPT_TYPE}" "$(settings_active_tag ${JOTEGO_UPDATER}) Cores made by Jotego" \
                "3 Unofficial ${SCRIPT_TYPE}"  "$(settings_active_tag ${UNOFFICIAL_UPDATER}) Some unofficial cores" \
                "4 LLAPI ${SCRIPT_TYPE}" "$(settings_active_tag ${LLAPI_UPDATER}) Forks adapted to LLAPI" \
                "5 BIOS Getter" "$(settings_active_tag ${BIOS_GETTER}) BIOS files for your systems" \
                "6 MAME Getter" "$(settings_active_tag ${MAME_GETTER}) MAME ROMs for arcades" \
                "7 HBMAME Getter" "$(settings_active_tag ${HBMAME_GETTER}) HBMAME ROMs for arcades" \
                "8 Names TXT Updater" "$(settings_active_tag ${NAMES_TXT_UPDATER}) Better core names in the menus" \
                "9 Arcade Organizer" "$(settings_active_tag ${ARCADE_ORGANIZER}) Creates folder for easy navigation" \
                "0 Misc" "" \
                "SAVE" "Writes all changes to the INI file/s" \
                "EXIT and RUN UPDATE ALL" "" 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e

            case "${DEFAULT_SELECTION}" in
                "0")
                    case "$(cat ${TMP})" in
                        "1 Main ${SCRIPT_TYPE}") settings_menu_main_updater ;;
                        "2 Jotego ${SCRIPT_TYPE}") settings_menu_jotego_updater ;;
                        "3 Unofficial ${SCRIPT_TYPE}") settings_menu_unofficial_updater ;;
                        "4 LLAPI ${SCRIPT_TYPE}") settings_menu_llapi_updater ;;
                        "5 BIOS Getter") settings_menu_bios_getter ;;
                        "6 MAME Getter") settings_menu_mame_getter ;;
                        "7 HBMAME Getter") settings_menu_hbmame_getter ;;
                        "8 Names TXT Updater") settings_menu_names_txt ;;
                        "9 Arcade Organizer")
                            if [[ "${ARCADE_ORGANIZER_2_ALPHA_ENABLED}" == "true" ]] ; then
                                settings_menu_2beta_arcade_organizer
                            else
                                settings_menu_arcade_organizer
                            fi
                            ;;
                        "0 Misc") settings_menu_misc ;;
                        "SAVE") settings_menu_save ;;
                        "EXIT and RUN UPDATE ALL") settings_menu_exit_and_run ;;
                        *) settings_menu_cancel ;;
                    esac
                    ;;
                "3")
                    case "$(cat ${TMP})" in
                        "1 Main ${SCRIPT_TYPE}") settings_change_var "MAIN_UPDATER" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                        "2 Jotego ${SCRIPT_TYPE}") settings_change_var "JOTEGO_UPDATER" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                        "3 Unofficial ${SCRIPT_TYPE}") settings_change_var "UNOFFICIAL_UPDATER" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                        "4 LLAPI ${SCRIPT_TYPE}") settings_change_var "LLAPI_UPDATER" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                        "5 BIOS Getter") settings_change_var "BIOS_GETTER" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                        "6 MAME Getter") settings_change_var "MAME_GETTER" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                        "7 HBMAME Getter") settings_change_var "HBMAME_GETTER" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                        "8 Names TXT Updater") settings_change_var "NAMES_TXT_UPDATER" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                        "9 Arcade Organizer") settings_change_var "ARCADE_ORGANIZER" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                        "0 Misc") ;;
                        "SAVE") ;;
                        "EXIT and RUN UPDATE ALL") ;;
                        *) settings_menu_cancel ;;
                    esac
                    ;;
                *) settings_menu_cancel ;;
            esac
        )
        if [ -f "${SETTINGS_TMP_CONTINUE}" ] ; then
            rm "${SETTINGS_TMP_CONTINUE}" 2> /dev/null
            break
        fi
        if [ -f "${SETTINGS_TMP_BREAK}" ] ; then
            rm "${SETTINGS_TMP_BREAK}" 2> /dev/null
            rm ${TMP}
            exit 0
        fi
    done
    rm ${TMP}

    clear

    if [ -f "${ORIGINAL_INI_PATH}" ] ; then
        set_default_options
        load_ini_file "${ORIGINAL_INI_PATH}"
        post_load_update_all_ini
    fi
}

settings_menu_main_updater() {
    local TMP=$(mktemp)

    SETTINGS_OPTIONS_MAIN_UPDATER_INI=("$(settings_normalize_ini_file ${EXPORTED_INI_PATH})" "update.ini")
    settings_try_add_ini_option 'SETTINGS_OPTIONS_MAIN_UPDATER_INI' "${MAIN_UPDATER_INI}"
    SETTINGS_OPTIONS_DOWNLOAD_NEW_CORES=("true" "false")
    SETTINGS_OPTIONS_UPDATE_LINUX=("true" "false")
    SETTINGS_OPTIONS_UPDATE_CHEATS=("once" "true" "false")
    SETTINGS_OPTIONS_MAME_ALT_ROMS=("true" "false")

    while true ; do
        (
            local MAIN_UPDATER="${SETTINGS_OPTIONS_MAIN_UPDATER[0]}"
            local MAIN_UPDATER_INI="${SETTINGS_OPTIONS_MAIN_UPDATER_INI[0]}"
            local ENCC_FORKS="${SETTINGS_OPTIONS_ENCC_FORKS[0]}"
            local DOWNLOAD_NEW_CORES="${SETTINGS_OPTIONS_DOWNLOAD_NEW_CORES[0]}"
            local UPDATE_CHEATS="${SETTINGS_OPTIONS_UPDATE_CHEATS[0]}"
            local UPDATE_LINUX="${SETTINGS_OPTIONS_UPDATE_LINUX[0]}"
            local MAME_ALT_ROMS="${SETTINGS_OPTIONS_MAME_ALT_ROMS[0]}"
            local DOWNLOADER_WHEN_POSSIBLE="false"

            load_vars_from_ini "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" "MAIN_UPDATER" "MAIN_UPDATER_INI" "ENCC_FORKS" "DOWNLOADER_WHEN_POSSIBLE"
            load_vars_from_ini "$(settings_domain_ini_file ${MAIN_UPDATER_INI})" "DOWNLOAD_NEW_CORES" "MAME_ALT_ROMS" "UPDATE_CHEATS" "UPDATE_LINUX"

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 $(settings_active_action ${MAIN_UPDATER})"
            fi

            local ACTIVATE="1 $(settings_active_action ${MAIN_UPDATER})"

            if [[ "${DOWNLOADER_WHEN_POSSIBLE}" == "true" ]] && [[ "${UPDATE_ALL_PC_UPDATER}" != "true" ]] ; then
                set +e
                dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --title "Main Downloader Settings" \
                    --menu "$(settings_menu_descr_text ${EXPORTED_INI_PATH} ${EXPORTED_INI_PATH})" 10 75 25 \
                    "${ACTIVATE}" "Activated: ${MAIN_UPDATER}" \
                    "2 Cores versions" "$([[ ${ENCC_FORKS} == 'true' ]] && echo 'DB9 / SNAC8 forks with ENCC' || echo 'Official Cores from MiSTer-devel')" \
                    "BACK"  "" 2> ${TMP}
                DEFAULT_SELECTION="$?"
                set -e
            else
                set +e
                dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --title "Main Updater Settings" \
                    --menu "$(settings_menu_descr_text ${EXPORTED_INI_PATH} ${MAIN_UPDATER_INI})" 16 75 25 \
                    "${ACTIVATE}" "Activated: ${MAIN_UPDATER}" \
                    "2 Cores versions" "$([[ ${ENCC_FORKS} == 'true' ]] && echo 'DB9 / SNAC8 forks with ENCC' || echo 'Official Cores from MiSTer-devel')" \
                    "3 INI file"  "$(settings_normalize_ini_file ${MAIN_UPDATER_INI})" \
                    "4 Install new Cores" "${DOWNLOAD_NEW_CORES}" \
                    "5 Install MRA-Alternatives" "${MAME_ALT_ROMS}" \
                    "6 Install Cheats" "${UPDATE_CHEATS}" \
                    "7 Install Linux updates" "${UPDATE_LINUX}" \
                    "8 Force full resync" "Clears \"last_successful_run\" file et al" \
                    "BACK"  "" 2> ${TMP}
                DEFAULT_SELECTION="$?"
                set -e
            fi

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "${ACTIVATE}") settings_change_var "MAIN_UPDATER" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                "2 Cores versions") settings_change_var "ENCC_FORKS" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                "3 INI file") settings_change_var "MAIN_UPDATER_INI" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                "4 Install new Cores") settings_change_var "DOWNLOAD_NEW_CORES" "$(settings_domain_ini_file ${MAIN_UPDATER_INI})" ;;
                "5 Install MRA-Alternatives") settings_change_var "MAME_ALT_ROMS" "$(settings_domain_ini_file ${MAIN_UPDATER_INI})" ;;
                "6 Install Cheats") settings_change_var "UPDATE_CHEATS" "$(settings_domain_ini_file ${MAIN_UPDATER_INI})" ;;
                "7 Install Linux updates") settings_change_var "UPDATE_LINUX" "$(settings_domain_ini_file ${MAIN_UPDATER_INI})" ;;
                "8 Force full resync")
                    local SOMETHING="false"
                    if [ -f "${MISTER_MAIN_UPDATER_WORK_FOLDER}/$(basename ${EXPORTED_INI_PATH%.*}).last_successful_run" ] ; then
                        SOMETHING="true"
                        set +e
                        dialog --keep-window --title "Delete last_successful_run" --defaultno \
                            --yesno "Your next update will become much slower\nif you delete \"last_successful_run\"\nBut it will perform a full resync.\n\nAre you sure you want to delete it?" \
                            9 45
                        local SURE_RET=$?
                        set -e
                        if [[ "${SURE_RET}" == "0" ]] ; then
                            rm "${MISTER_MAIN_UPDATER_WORK_FOLDER}/$(basename ${EXPORTED_INI_PATH%.*}).last_successful_run"
                            set +e
                            dialog --keep-window --msgbox "Removed file:\n/Scripts/.mister_updater/$(basename ${EXPORTED_INI_PATH%.*}).last_successful_run" 6 75
                            set -e
                        fi
                    fi

                    local MISTER_MAIN_BINARY="${MISTER_MAIN_UPDATER_WORK_FOLDER}/MiSTer_20"*
                    MISTER_MAIN_BINARY=$(echo ${MISTER_MAIN_BINARY})
                    if [ -f "${MISTER_MAIN_BINARY}" ] ; then
                        SOMETHING="true"
                        set +e
                        dialog --keep-window --title "Delete $(basename ${MISTER_MAIN_BINARY})" --defaultno \
                            --yesno "Select \"YES\" if you want to force an update on the MiSTer binary" \
                            5 75
                        local SURE_RET=$?
                        set -e
                        if [[ "${SURE_RET}" == "0" ]] ; then
                            rm "${MISTER_MAIN_BINARY}"
                            set +e
                            dialog --keep-window --msgbox "Removed file:\n/${MISTER_MAIN_BINARY}" 6 75
                            set -e
                        fi
                    fi

                    local MISTER_MENU_CORE="${MISTER_MAIN_UPDATER_WORK_FOLDER}/menu_20"*
                    MISTER_MENU_CORE=$(echo ${MISTER_MENU_CORE})
                    if [ -f "${MISTER_MENU_CORE}" ] ; then
                        SOMETHING="true"
                        set +e
                        dialog --keep-window --title "Delete $(basename ${MISTER_MENU_CORE})" --defaultno \
                            --yesno "Select \"YES\" if you want to force an update on the menu core" \
                            5 75
                        local SURE_RET=$?
                        set -e
                        if [[ "${SURE_RET}" == "0" ]] ; then
                            rm "${MISTER_MENU_CORE}"
                            set +e
                            dialog --keep-window --msgbox "Removed file:\n/${MISTER_MENU_CORE}" 6 75
                            set -e
                        fi
                    fi

                    local MRA_ALTERNATIVES_ZIP="${MISTER_MAIN_UPDATER_WORK_FOLDER}/MRA-Alternatives_"*
                    MRA_ALTERNATIVES_ZIP=$(echo ${MRA_ALTERNATIVES_ZIP})
                    if [ -f "${MRA_ALTERNATIVES_ZIP}" ] ; then
                        SOMETHING="true"
                        set +e
                        dialog --keep-window --title "Delete $(basename ${MRA_ALTERNATIVES_ZIP})" --defaultno \
                            --yesno "Select \"YES\" if you want to force an update on MRA-Alternatives" \
                            5 75
                        local SURE_RET=$?
                        set -e
                        if [[ "${SURE_RET}" == "0" ]] ; then
                            rm "${MRA_ALTERNATIVES_ZIP}"
                            set +e
                            dialog --keep-window --msgbox "Removed file:\n/${MRA_ALTERNATIVES_ZIP}" 6 75
                            set -e
                        fi
                    fi

                    local FILTERS_ZIP="${MISTER_MAIN_UPDATER_WORK_FOLDER}/Filters_"*
                    FILTERS_ZIP=$(echo ${FILTERS_ZIP})
                    if [ -f "${FILTERS_ZIP}" ] ; then
                        SOMETHING="true"
                        set +e
                        dialog --keep-window --title "Delete $(basename ${FILTERS_ZIP})" --defaultno \
                            --yesno "Select \"YES\" if you want to force an update on Filters" \
                            5 75
                        local SURE_RET=$?
                        set -e
                        if [[ "${SURE_RET}" == "0" ]] ; then
                            rm "${FILTERS_ZIP}"
                            set +e
                            dialog --keep-window --msgbox "Removed file:\n/${FILTERS_ZIP}" 6 75
                            set -e
                        fi
                    fi

                    if [[ "${SOMETHING}" == "false" ]] ; then
                        set +e
                        dialog --keep-window --msgbox "Nothing to be cleared" 5 27
                        set -e
                    fi
                    ;;
                *) echo > "${SETTINGS_TMP_BREAK}" ;;
            esac
        )
        if [ -f "${SETTINGS_TMP_BREAK}" ] ; then
            rm "${SETTINGS_TMP_BREAK}" 2> /dev/null
            break
        fi
    done
    rm ${TMP}
}

settings_menu_jotego_updater() {
    local TMP=$(mktemp)

    SETTINGS_OPTIONS_JOTEGO_UPDATER_INI=("$(settings_normalize_ini_file ${EXPORTED_INI_PATH})" "update_jtcores.ini")
    settings_try_add_ini_option 'SETTINGS_OPTIONS_JOTEGO_UPDATER_INI' "${JOTEGO_UPDATER_INI}"
    SETTINGS_OPTIONS_DOWNLOAD_BETA_CORES=("false" "true")
    SETTINGS_OPTIONS_MAME_ALT_ROMS=("true" "false")

    while true ; do
        (
            local JOTEGO_UPDATER="${SETTINGS_OPTIONS_JOTEGO_UPDATER[0]}"
            local JOTEGO_UPDATER_INI="${SETTINGS_OPTIONS_JOTEGO_UPDATER_INI[0]}"
            local DOWNLOAD_BETA_CORES="${SETTINGS_OPTIONS_DOWNLOAD_BETA_CORES[0]}"
            local MAME_ALT_ROMS="${SETTINGS_OPTIONS_MAME_ALT_ROMS[0]}"

            load_vars_from_ini "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" "JOTEGO_UPDATER" "JOTEGO_UPDATER_INI"
            load_ini_file "$(settings_domain_ini_file ${JOTEGO_UPDATER_INI})"

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 $(settings_active_action ${JOTEGO_UPDATER})"
            fi

            local ACTIVATE="1 $(settings_active_action ${JOTEGO_UPDATER})"
            if [[ "${DOWNLOADER_WHEN_POSSIBLE}" == "true" ]] && [[ "${UPDATE_ALL_PC_UPDATER}" != "true" ]] ; then
                set +e
                dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --title "Jotego Downloader Settings" \
                    --menu "$(settings_menu_descr_text ${EXPORTED_INI_PATH} ${JOTEGO_UPDATER_INI})" 10 75 25 \
                    "${ACTIVATE}" "Activated: ${JOTEGO_UPDATER}" \
                    "3 Install Beta Cores" "${DOWNLOAD_BETA_CORES}" \
                    "BACK"  "" 2> ${TMP}
                DEFAULT_SELECTION="$?"
                set -e
            else
                set +e
                dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --title "Jotego Updater Settings" \
                    --menu "$(settings_menu_descr_text ${EXPORTED_INI_PATH} ${JOTEGO_UPDATER_INI})" 13 75 25 \
                    "${ACTIVATE}" "Activated: ${JOTEGO_UPDATER}" \
                    "2 INI file"  "$(settings_normalize_ini_file ${JOTEGO_UPDATER_INI})" \
                    "3 Install Beta Cores" "${DOWNLOAD_BETA_CORES}" \
                    "4 Install MRA-Alternatives" "${MAME_ALT_ROMS}" \
                    "5 Force full resync" "Clears \"last_successful_run\" file et al" \
                    "BACK"  "" 2> ${TMP}
                DEFAULT_SELECTION="$?"
                set -e
            fi

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "${ACTIVATE}") settings_change_var "JOTEGO_UPDATER" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                "2 INI file") settings_change_var "JOTEGO_UPDATER_INI" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                "3 Install Beta Cores") settings_change_var "DOWNLOAD_BETA_CORES" "$(settings_domain_ini_file ${JOTEGO_UPDATER_INI})" ;;
                "4 Install MRA-Alternatives") settings_change_var "MAME_ALT_ROMS" "$(settings_domain_ini_file ${JOTEGO_UPDATER_INI})" ;;
                "5 Force full resync")
                    local SOMETHING="false"
                    if [ -f "${JOTEGO_UPDATER_WORK_FOLDER}/$(basename ${EXPORTED_INI_PATH%.*}).last_successful_run" ] ; then
                        SOMETHING="true"
                        set +e
                        dialog --keep-window --title "Delete last_successful_run" --defaultno \
                            --yesno "Your next update will become much slower\nif you delete \"last_successful_run\"\nBut it will perform a full resync.\n\nAre you sure you want to delete it?" \
                            9 45
                        local SURE_RET=$?
                        set -e
                        if [[ "${SURE_RET}" == "0" ]] ; then
                            rm "${JOTEGO_UPDATER_WORK_FOLDER}/$(basename ${EXPORTED_INI_PATH%.*}).last_successful_run"
                            set +e
                            dialog --keep-window --msgbox "Removed file:\n/Scripts/.mister_updater_jt/$(basename ${EXPORTED_INI_PATH%.*}).last_successful_run" 6 75
                            set -e
                        fi
                    fi

                    local MRA_ALTERNATIVES_ZIP=${JOTEGO_UPDATER_WORK_FOLDER}/MRA-Alternatives_*
                    MRA_ALTERNATIVES_ZIP=$(echo ${MRA_ALTERNATIVES_ZIP})
                    if [ -f "${MRA_ALTERNATIVES_ZIP}" ] ; then
                        SOMETHING="true"
                        set +e
                        dialog --keep-window --title "Delete $(basename ${MRA_ALTERNATIVES_ZIP})" --defaultno \
                            --yesno "Select \"YES\" if you want to force an update on MRA-Alternatives" \
                            5 75
                        local SURE_RET=$?
                        set -e
                        if [[ "${SURE_RET}" == "0" ]] ; then
                            rm "${MRA_ALTERNATIVES_ZIP}"
                            set +e
                            dialog --keep-window --msgbox "Removed file:\n/${MRA_ALTERNATIVES_ZIP}" 6 75
                            set -e
                        fi
                    fi

                    local BETA_MRA_ALTERNATIVES_ZIP=${JOTEGO_UPDATER_WORK_FOLDER}/BetaMRA-Alternatives_*
                    BETA_MRA_ALTERNATIVES_ZIP=$(echo ${BETA_MRA_ALTERNATIVES_ZIP})
                    if [ -f "${BETA_MRA_ALTERNATIVES_ZIP}" ] ; then
                        SOMETHING="true"
                        set +e
                        dialog --keep-window --title "Delete $(basename ${BETA_MRA_ALTERNATIVES_ZIP})" --defaultno \
                            --yesno "Select \"YES\" if you want to force an update on Beta MRA-Alternatives" \
                            5 75
                        local SURE_RET=$?
                        set -e
                        if [[ "${SURE_RET}" == "0" ]] ; then
                            rm "${BETA_MRA_ALTERNATIVES_ZIP}"
                            set +e
                            dialog --keep-window --msgbox "Removed file:\n/${BETA_MRA_ALTERNATIVES_ZIP}" 6 75
                            set -e
                        fi
                    fi

                    if [[ "${SOMETHING}" == "false" ]] ; then
                        set +e
                        dialog --keep-window --msgbox "Nothing to be cleared" 5 27
                        set -e
                    fi
                    ;;
                *) echo > "${SETTINGS_TMP_BREAK}" ;;
            esac
        )
        if [ -f "${SETTINGS_TMP_BREAK}" ] ; then
            rm "${SETTINGS_TMP_BREAK}" 2> /dev/null
            break
        fi
    done
    rm ${TMP}
}

settings_menu_unofficial_updater() {
    local TMP=$(mktemp)

    SETTINGS_OPTIONS_UNOFFICIAL_UPDATER_INI=("$(settings_normalize_ini_file ${EXPORTED_INI_PATH})" "update_unofficials.ini")
    settings_try_add_ini_option 'SETTINGS_OPTIONS_UNOFFICIAL_UPDATER_INI' "${UNOFFICIAL_UPDATER_INI}"
    SETTINGS_OPTIONS_DOWNLOAD_NEW_CORES=("true" "false")
    SETTINGS_OPTIONS_MAME_ALT_ROMS=("true" "false")

    while true ; do
        (
            local UNOFFICIAL_UPDATER="${SETTINGS_OPTIONS_UNOFFICIAL_UPDATER[0]}"
            local UNOFFICIAL_UPDATER_INI="${SETTINGS_OPTIONS_UNOFFICIAL_UPDATER_INI[0]}"
            local DOWNLOAD_NEW_CORES="${SETTINGS_OPTIONS_DOWNLOAD_NEW_CORES[0]}"
            local MAME_ALT_ROMS="${SETTINGS_OPTIONS_MAME_ALT_ROMS[0]}"

            load_vars_from_ini "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" "UNOFFICIAL_UPDATER" "UNOFFICIAL_UPDATER_INI"
            load_ini_file "$(settings_domain_ini_file ${UNOFFICIAL_UPDATER_INI})"

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 $(settings_active_action ${UNOFFICIAL_UPDATER})"
            fi

            local ACTIVATE="1 $(settings_active_action ${UNOFFICIAL_UPDATER})"

            if [[ "${DOWNLOADER_WHEN_POSSIBLE}" == "true" ]] && [[ "${UPDATE_ALL_PC_UPDATER}" != "true" ]] ; then
                set +e
                dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --title "Unofficial Downloader Settings" \
                    --menu "$(settings_menu_descr_text ${EXPORTED_INI_PATH} ${EXPORTED_INI_PATH})" 9 75 25 \
                    "${ACTIVATE}" "Activated: ${UNOFFICIAL_UPDATER}" \
                    "BACK"  "" 2> ${TMP}
                DEFAULT_SELECTION="$?"
                set -e
            else
                set +e
                dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --title "Unofficial Updater Settings" \
                    --menu "$(settings_menu_descr_text ${EXPORTED_INI_PATH} ${UNOFFICIAL_UPDATER_INI})" 13 75 25 \
                    "${ACTIVATE}" "Activated: ${UNOFFICIAL_UPDATER}" \
                    "2 INI file"  "$(settings_normalize_ini_file ${UNOFFICIAL_UPDATER_INI})" \
                    "3 Install new Cores" "${DOWNLOAD_NEW_CORES}" \
                    "4 Install MRA-Alternatives" "${MAME_ALT_ROMS}" \
                    "5 Force full resync" "Clears \"last_successful_run\" file" \
                    "BACK"  "" 2> ${TMP}
                DEFAULT_SELECTION="$?"
                set -e
            fi

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "${ACTIVATE}") settings_change_var "UNOFFICIAL_UPDATER" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                "2 INI file") settings_change_var "UNOFFICIAL_UPDATER_INI" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                "3 Install new Cores") settings_change_var "DOWNLOAD_NEW_CORES" "$(settings_domain_ini_file ${UNOFFICIAL_UPDATER_INI})" ;;
                "4 Install MRA-Alternatives") settings_change_var "MAME_ALT_ROMS" "$(settings_domain_ini_file ${UNOFFICIAL_UPDATER_INI})" ;;
                "5 Force full resync")
                    if [ -f "${UNOFFICIAL_UPDATER_WORK_FOLDER}/$(basename ${EXPORTED_INI_PATH%.*}).last_successful_run" ] ; then
                        set +e
                        dialog --keep-window --title "Are you sure?" --defaultno \
                            --yesno "Your next update will become much slower\nif you delete \"last_successful_run\"" \
                            6 45
                        local SURE_RET=$?
                        set -e
                        if [[ "${SURE_RET}" == "0" ]] ; then
                            rm "${UNOFFICIAL_UPDATER_WORK_FOLDER}/$(basename ${EXPORTED_INI_PATH%.*}).last_successful_run"
                            set +e
                            dialog --keep-window --msgbox "Removed file:\n/Scripts/.mister_updater_unofficials/$(basename ${EXPORTED_INI_PATH%.*}).last_successful_run" 6 75
                            set -e
                        else
                            set +e
                            dialog --keep-window --msgbox "Operaton Canceled" 5 22
                            set -e
                        fi
                    else
                        set +e
                        dialog --keep-window --msgbox "File doesn't exist:\n/Scripts/.mister_updater_unofficials/$(basename ${EXPORTED_INI_PATH%.*}).last_successful_run" 6 75
                        set -e
                    fi
                    ;;
                *) echo > "${SETTINGS_TMP_BREAK}" ;;
            esac
        )
        if [ -f "${SETTINGS_TMP_BREAK}" ] ; then
            rm "${SETTINGS_TMP_BREAK}" 2> /dev/null
            break
        fi
    done
    rm ${TMP}
}

settings_menu_llapi_updater() {
    local TMP=$(mktemp)

    SETTINGS_OPTIONS_LLAPI_UPDATER_INI=("$(settings_normalize_ini_file ${EXPORTED_INI_PATH})" "update_llapi.ini")
    settings_try_add_ini_option 'SETTINGS_OPTIONS_LLAPI_UPDATER_INI' "${LLAPI_UPDATER_INI}"
    SETTINGS_OPTIONS_DOWNLOAD_NEW_CORES=("true" "false")

    while true ; do
        (
            local LLAPI_UPDATER="${SETTINGS_OPTIONS_LLAPI_UPDATER[0]}"
            local LLAPI_UPDATER_INI="${SETTINGS_OPTIONS_LLAPI_UPDATER_INI[0]}"
            local DOWNLOAD_NEW_CORES="${SETTINGS_OPTIONS_DOWNLOAD_NEW_CORES[0]}"

            load_vars_from_ini "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" "LLAPI_UPDATER" "LLAPI_UPDATER_INI"
            load_ini_file "$(settings_domain_ini_file ${LLAPI_UPDATER_INI})"

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 $(settings_active_action ${LLAPI_UPDATER})"
            fi

            local ACTIVATE="1 $(settings_active_action ${LLAPI_UPDATER})"

            if [[ "${DOWNLOADER_WHEN_POSSIBLE}" == "true" ]] && [[ "${UPDATE_ALL_PC_UPDATER}" != "true" ]] ; then
                set +e
                dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --title "LLAPI Downloader Settings" \
                    --menu "$(settings_menu_descr_text ${EXPORTED_INI_PATH} ${EXPORTED_INI_PATH})" 9 75 25 \
                    "${ACTIVATE}" "Activated: ${LLAPI_UPDATER}" \
                    "BACK"  "" 2> ${TMP}
                DEFAULT_SELECTION="$?"
                set -e
            else
                set +e
                dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --title "LLAPI Updater Settings" \
                    --menu "$(settings_menu_descr_text ${EXPORTED_INI_PATH} ${LLAPI_UPDATER_INI})" 11 75 25 \
                    "${ACTIVATE}" "Activated: ${LLAPI_UPDATER}" \
                    "2 INI file"  "$(settings_normalize_ini_file ${LLAPI_UPDATER_INI})" \
                    "3 Install new Cores" "${DOWNLOAD_NEW_CORES}" \
                    "BACK"  "" 2> ${TMP}
                DEFAULT_SELECTION="$?"
                set -e
            fi

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi
            DEFAULT_SELECTION="$(cat ${TMP})"
            case "${DEFAULT_SELECTION}" in
                "${ACTIVATE}") settings_change_var "LLAPI_UPDATER" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                "2 INI file") settings_change_var "LLAPI_UPDATER_INI" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                "3 Install new Cores") settings_change_var "DOWNLOAD_NEW_CORES" "$(settings_domain_ini_file ${LLAPI_UPDATER_INI})" ;;
                *) echo > "${SETTINGS_TMP_BREAK}" ;;
            esac
        )
        if [ -f "${SETTINGS_TMP_BREAK}" ] ; then
            rm "${SETTINGS_TMP_BREAK}" 2> /dev/null
            break
        fi
    done
    rm ${TMP}
}

settings_menu_bios_getter() {
    local TMP=$(mktemp)

    SETTINGS_OPTIONS_BIOS_GETTER_INI=("update_bios-getter.ini" "$(settings_normalize_ini_file ${EXPORTED_INI_PATH})")
    settings_try_add_ini_option 'SETTINGS_OPTIONS_BIOS_GETTER_INI' "${BIOS_GETTER_INI}"

    while true ; do
        (
            local BIOS_GETTER="${SETTINGS_OPTIONS_BIOS_GETTER[0]}"
            local BIOS_GETTER_INI="${SETTINGS_OPTIONS_BIOS_GETTER_INI[0]}"

            load_vars_from_ini "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" "BIOS_GETTER" "BIOS_GETTER_INI"
            load_ini_file "$(settings_domain_ini_file ${BIOS_GETTER_INI})"

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 $(settings_active_action ${BIOS_GETTER})"
            fi

            local ACTIVATE="1 $(settings_active_action ${BIOS_GETTER})"

            set +e
            dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --title "BIOS-Getter Settings" \
                --menu "$(settings_menu_descr_text ${EXPORTED_INI_PATH} ${BIOS_GETTER_INI})" 10 75 25 \
                "${ACTIVATE}" "Activated: ${BIOS_GETTER}" \
                "2 INI file"  "$(settings_normalize_ini_file ${BIOS_GETTER_INI})" \
                "BACK"  "" 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "${ACTIVATE}") settings_change_var "BIOS_GETTER" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                "2 INI file") settings_change_var "BIOS_GETTER_INI" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                *) echo > "${SETTINGS_TMP_BREAK}" ;;
            esac
        )
        if [ -f "${SETTINGS_TMP_BREAK}" ] ; then
            rm "${SETTINGS_TMP_BREAK}" 2> /dev/null
            break
        fi
    done
    rm ${TMP}
}

settings_menu_mame_getter() {
    local TMP=$(mktemp)

    SETTINGS_OPTIONS_MAME_GETTER_INI=("update_mame-getter.ini" "$(settings_normalize_ini_file ${EXPORTED_INI_PATH})")
    settings_try_add_ini_option 'SETTINGS_OPTIONS_MAME_GETTER_INI' "${MAME_GETTER_INI}"
    SETTINGS_OPTIONS_ROMMAME=("games/mame" "_Arcade/mame")

    while true ; do
        (
            local MAME_GETTER="${SETTINGS_OPTIONS_MAME_GETTER[0]}"
            local MAME_GETTER_INI="${SETTINGS_OPTIONS_MAME_GETTER_INI[0]}"
            local ROMMAME="${SETTINGS_OPTIONS_ROMMAME[0]}"

            load_vars_from_ini "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" "MAME_GETTER" "MAME_GETTER_INI"
            load_ini_file "$(settings_domain_ini_file ${MAME_GETTER_INI})"

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 $(settings_active_action ${MAME_GETTER})"
            fi

            local ACTIVATE="1 $(settings_active_action ${MAME_GETTER})"

            set +e
            dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --title "MAME-Getter Settings" \
                --menu "$(settings_menu_descr_text ${EXPORTED_INI_PATH} ${MAME_GETTER_INI})" 13 75 25 \
                "${ACTIVATE}" "Activated: ${MAME_GETTER}" \
                "2 INI file"  "$(settings_normalize_ini_file ${MAME_GETTER_INI})" \
                "3 MAME ROM directory" "${ROMMAME}" \
                "4 Clean MAME ROMs" "Deletes the mame folder" \
                "5 Force full resync" "Clears \"last_run\" file" \
                "BACK"  "" 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "${ACTIVATE}") settings_change_var "MAME_GETTER" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                "2 INI file") settings_change_var "MAME_GETTER_INI" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                "3 MAME ROM directory") settings_change_var "ROMMAME" "$(settings_domain_ini_file ${MAME_GETTER_INI})" ;;
                "4 Clean MAME ROMs")
                    run_quiet_mame_getter_script "${MAME_GETTER_URL}" "$(settings_domain_ini_file ${MAME_GETTER_INI})" --print-ini-options
                    if [[ "${RUN_QUIET_MAME_GETTER_SCRIPT_OUTPUT}" == "" ]] ; then
                        settings_menu_connection_problem
                        continue
                    fi

                    local ROMMAME=$(load_single_var_from_ini "ROMMAME" "${RUN_QUIET_MAME_GETTER_SCRIPT_OUTPUT}")

                    if [ -d "${ROMMAME}" ] ; then
                        set +e
                        DIALOGRC="${SETTINGS_TMP_BLACK_DIALOGRC}" dialog --keep-window --title "ARE YOU SURE?" --defaultno \
                            --yesno "WARNING! You will lose ALL the data contained in the folder:\n${ROMMAME}" \
                            6 66
                        local SURE_RET=$?
                        set -e
                        if [[ "${SURE_RET}" == "0" ]] ; then
                            rm -rf "${ROMMAME}"
                            set +e
                            dialog --keep-window --msgbox "${ROMMAME} Removed" 5 36
                            set -e
                        else
                            set +e
                            dialog --keep-window --msgbox "Operaton Canceled" 5 22
                            set -e
                        fi
                    else
                        set +e
                        dialog --keep-window --msgbox "${ROMMAME} doesn't exist" 5 50
                        set -e
                    fi
                    ;;
                "5 Force full resync")
                    if [ -f "${MAME_GETTER_LASTRUN_PATH}" ] ; then
                        set +e
                        dialog --keep-window --title "Are you sure?" --defaultno \
                            --yesno "Your next update will become much slower\nif you delete \"last_run\"" \
                            6 45
                        local SURE_RET=$?
                        set -e
                        if [[ "${SURE_RET}" == "0" ]] ; then
                            rm "${MAME_GETTER_LASTRUN_PATH}"
                            set +e
                            dialog --keep-window --msgbox "Removed file:\n${MAME_GETTER_LASTRUN_PATH}" 6 75
                            set -e
                        else
                            set +e
                            dialog --keep-window --msgbox "Operaton Canceled" 5 22
                            set -e
                        fi
                    else
                        set +e
                        dialog --keep-window --msgbox "File doesn't exist:\n${MAME_GETTER_LASTRUN_PATH}" 6 75
                        set -e
                    fi
                    ;;
                *) echo > "${SETTINGS_TMP_BREAK}" ;;
            esac
        )
        if [ -f "${SETTINGS_TMP_BREAK}" ] ; then
            rm "${SETTINGS_TMP_BREAK}" 2> /dev/null
            break
        fi
    done
    rm ${TMP}
}

settings_menu_hbmame_getter() {
    local TMP=$(mktemp)

    SETTINGS_OPTIONS_HBMAME_GETTER_INI=("update_hbmame-getter.ini" "$(settings_normalize_ini_file ${EXPORTED_INI_PATH})")
    settings_try_add_ini_option 'SETTINGS_OPTIONS_HBMAME_GETTER_INI' "${HBMAME_GETTER_INI}"
    SETTINGS_OPTIONS_ROMHBMAME=("games/hbmame" "_Arcade/hbmame")

    while true ; do
        (
            local HBMAME_GETTER="${SETTINGS_OPTIONS_HBMAME_GETTER[0]}"
            local HBMAME_GETTER_INI="${SETTINGS_OPTIONS_HBMAME_GETTER_INI[0]}"
            local ROMHBMAME="${SETTINGS_OPTIONS_ROMHBMAME[0]}"

            load_vars_from_ini "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" "HBMAME_GETTER" "HBMAME_GETTER_INI"
            load_ini_file "$(settings_domain_ini_file ${HBMAME_GETTER_INI})"

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 $(settings_active_action ${HBMAME_GETTER})"
            fi

            local ACTIVATE="1 $(settings_active_action ${HBMAME_GETTER})"

            set +e
            dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --title "HBMAME-Getter Settings" \
                --menu "$(settings_menu_descr_text ${EXPORTED_INI_PATH} ${HBMAME_GETTER_INI})" 13 75 25 \
                "${ACTIVATE}" "Activated: ${HBMAME_GETTER}" \
                "2 INI file"  "$(settings_normalize_ini_file ${HBMAME_GETTER_INI})" \
                "3 HBMAME ROM directory" "${ROMHBMAME}" \
                "4 Clean HBMAME ROMs" "Deletes the hbmame folder" \
                "5 Force full resync" "Clears \"last_run\" file" \
                "BACK"  "" 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "${ACTIVATE}") settings_change_var "HBMAME_GETTER" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                "2 INI file") settings_change_var "HBMAME_GETTER_INI" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                "3 HBMAME ROM directory") settings_change_var "ROMHBMAME" "$(settings_domain_ini_file ${HBMAME_GETTER_INI})" ;;
                "4 Clean HBMAME ROMs")
                    run_quiet_mame_getter_script "${HBMAME_GETTER_URL}" "$(settings_domain_ini_file ${HBMAME_GETTER_INI})" --print-ini-options
                    if [[ "${RUN_QUIET_MAME_GETTER_SCRIPT_OUTPUT}" == "" ]] ; then
                        settings_menu_connection_problem
                        continue
                    fi

                    local ROMHBMAME=$(load_single_var_from_ini "ROMHBMAME" "${RUN_QUIET_MAME_GETTER_SCRIPT_OUTPUT}")

                    if [ -d "${ROMHBMAME}" ] ; then
                        set +e
                        DIALOGRC="${SETTINGS_TMP_BLACK_DIALOGRC}" dialog --keep-window --title "ARE YOU SURE?" --defaultno \
                            --yesno "WARNING! You will lose ALL the data contained in the folder:\n${ROMHBMAME}" \
                            6 66
                        local SURE_RET=$?
                        set -e
                        if [[ "${SURE_RET}" == "0" ]] ; then
                            rm -rf "${ROMHBMAME}"
                            set +e
                            dialog --keep-window --msgbox "${ROMHBMAME} Removed" 5 36
                            set -e
                        else
                            set +e
                            dialog --keep-window --msgbox "Operaton Canceled" 5 22
                            set -e
                        fi
                    else
                        set +e
                        dialog --keep-window --msgbox "${ROMHBMAME} doesn't exist" 5 50
                        set -e
                    fi
                    ;;
                "5 Force full resync")
                    if [ -f "${HBMAME_GETTER_LASTRUN_PATH}" ] ; then
                        set +e
                        dialog --keep-window --title "Are you sure?" --defaultno \
                            --yesno "Your next update will become much slower\nif you delete \"last_run\"" \
                            6 45
                        local SURE_RET=$?
                        set -e
                        if [[ "${SURE_RET}" == "0" ]] ; then
                            rm "${HBMAME_GETTER_LASTRUN_PATH}"
                            set +e
                            dialog --keep-window --msgbox "Removed file:\n${HBMAME_GETTER_LASTRUN_PATH}" 6 75
                            set -e
                        else
                            set +e
                            dialog --keep-window --msgbox "Operaton Canceled" 5 22
                            set -e
                        fi
                    else
                        set +e
                        dialog --keep-window --msgbox "File doesn't exist:\n${HBMAME_GETTER_LASTRUN_PATH}" 6 75
                        set -e
                    fi
                    ;;
                *) echo > "${SETTINGS_TMP_BREAK}" ;;
            esac
        )
        if [ -f "${SETTINGS_TMP_BREAK}" ] ; then
            rm "${SETTINGS_TMP_BREAK}" 2> /dev/null
            break
        fi
    done
    rm ${TMP}
}

settings_menu_names_txt() {
    local TMP=$(mktemp)

    SETTINGS_OPTIONS_NAMES_TXT_UPDATER_INI=("update_names-txt.ini" "$(settings_normalize_ini_file ${EXPORTED_INI_PATH})")
    settings_try_add_ini_option 'SETTINGS_OPTIONS_NAMES_TXT_UPDATER_INI' "${NAMES_TXT_UPDATER_INI}"
    SETTINGS_OPTIONS_NAMES_REGION=("US" "EU" "JP")
    SETTINGS_OPTIONS_NAMES_CHAR_CODE=("CHAR18" "CHAR28")
    SETTINGS_OPTIONS_NAMES_SORT_CODE=("Common" "Manufacturer")

    while true ; do
        (
            local NAMES_TXT_UPDATER="${SETTINGS_OPTIONS_NAMES_TXT_UPDATER[0]}"
            local NAMES_TXT_UPDATER_INI="${SETTINGS_OPTIONS_NAMES_TXT_UPDATER_INI[0]}"
            local NAMES_REGION="${SETTINGS_OPTIONS_NAMES_REGION[0]}"
            local NAMES_CHAR_CODE="${SETTINGS_OPTIONS_NAMES_CHAR_CODE[0]}"
            local NAMES_SORT_CODE="${SETTINGS_OPTIONS_NAMES_SORT_CODE[0]}"

            load_vars_from_ini "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" "NAMES_TXT_UPDATER" "NAMES_TXT_UPDATER_INI" "NAMES_REGION" "NAMES_CHAR_CODE" "NAMES_SORT_CODE"
            load_ini_file "$(settings_domain_ini_file ${NAMES_TXT_UPDATER_INI})"

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 $(settings_active_action ${NAMES_TXT_UPDATER})"
            fi

            local ACTIVATE="1 $(settings_active_action ${NAMES_TXT_UPDATER})"

            set +e
            dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --title "Names TXT Updater Settings" \
                --menu "$(settings_menu_descr_text ${EXPORTED_INI_PATH} ${NAMES_TXT_UPDATER_INI})
"$'\n'"Installs name.txt file containing curated names for your cores.
You can also contribute to the naming of the cores at:
https://github.com/ThreepwoodLeBrush/Names_MiSTer" 18 75 25 \
                "${ACTIVATE}" "Activated: ${NAMES_TXT_UPDATER}" \
                "2 INI file"  "$(settings_normalize_ini_file ${NAMES_TXT_UPDATER_INI})" \
                "3 Region" "${NAMES_REGION}" \
                "4 Char Code" "${NAMES_CHAR_CODE}" \
                "5 Sort Code" "${NAMES_SORT_CODE}" \
                "6 Remove \"names.txt\"" "Back to standard core names based on RBF files" \
                "BACK"  "" 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "${ACTIVATE}")
                    settings_change_var "NAMES_TXT_UPDATER" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})"
                    local NEW_NAMES_TXT_UPDATER=$(load_single_var_from_ini "NAMES_TXT_UPDATER" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})")
                    if [[ "${NEW_NAMES_TXT_UPDATER}" == "true" ]] && [ ! -f "${ARCADE_ORGANIZER_INSTALLED_NAMES_TXT}" ] && [ -f "${NAMES_TXT_PATH}" ] ; then
                        set +e
                        DIALOGRC="${SETTINGS_TMP_BLACK_DIALOGRC}" dialog --keep-window --msgbox "WARNING! Your current names.txt file will be overwritten after updating" 5 76
                        set -e
                    fi
                    ;;
                "2 INI file") settings_change_var "NAMES_TXT_UPDATER_INI" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                "3 Region") settings_change_var "NAMES_REGION" "$(settings_domain_ini_file ${NAMES_TXT_UPDATER_INI})" ;;
                "4 Char Code") settings_change_var "NAMES_CHAR_CODE" "$(settings_domain_ini_file ${NAMES_TXT_UPDATER_INI})"
                    local NEW_NAMES_CHAR_CODE=$(load_single_var_from_ini "NAMES_CHAR_CODE" "$(settings_domain_ini_file ${NAMES_TXT_UPDATER_INI})")
                    if [[ "${NEW_NAMES_CHAR_CODE}" == "CHAR28" ]] && ! grep -q "rbf_hide_datecode=1" "${MISTER_INI_PATH}" 2> /dev/null ; then
                        set +e
                        dialog --keep-window --msgbox "It's recommended to set rbf_hide_datecode=1 on MiSTer.ini when using CHAR28" 5 80
                        set -e
                    fi
                    ;;
                "5 Sort Code")  settings_change_var "NAMES_SORT_CODE" "$(settings_domain_ini_file ${NAMES_TXT_UPDATER_INI})" ;;
                "6 Remove \"names.txt\"")
                    if [ -f "${NAMES_TXT_PATH}" ] ; then
                        set +e
                        dialog --keep-window --title "Are you sure?" --defaultno \
                            --yesno "If you have done changes to names.txt, they will be lost" \
                            5 62
                        local SURE_RET=$?
                        set -e
                        if [[ "${SURE_RET}" == "0" ]] ; then
                            rm "${NAMES_TXT_PATH}"
                            set +e
                            dialog --keep-window --msgbox "names.txt Removed" 5 22
                            set -e
                        else
                            set +e
                            dialog --keep-window --msgbox "Operaton Canceled" 5 22
                            set -e
                        fi
                    else
                        set +e
                        dialog --keep-window --msgbox "names.txt doesn't exist" 5 29
                        set -e
                    fi
                    ;;
                *) echo > "${SETTINGS_TMP_BREAK}" ;;
            esac
        )
        if [ -f "${SETTINGS_TMP_BREAK}" ] ; then
            rm "${SETTINGS_TMP_BREAK}" 2> /dev/null
            break
        fi
    done
    rm ${TMP}
}

settings_menu_arcade_organizer() {
    local TMP=$(mktemp)

    SETTINGS_OPTIONS_ARCADE_ORGANIZER_INI=("update_arcade-organizer.ini" "$(settings_normalize_ini_file ${EXPORTED_INI_PATH})")
    settings_try_add_ini_option 'SETTINGS_OPTIONS_ARCADE_ORGANIZER_INI' "${ARCADE_ORGANIZER_INI}"
    SETTINGS_OPTIONS_SKIPALTS=("true" "false")
    SETTINGS_OPTIONS_ORGDIR=("${ARCADE_ORGANIZER_FOLDER_OPTION_1}" "${ARCADE_ORGANIZER_FOLDER_OPTION_2}" "${ARCADE_ORGANIZER_FOLDER_OPTION_3}")

    while true ; do
        (
            local ARCADE_ORGANIZER="${SETTINGS_OPTIONS_ARCADE_ORGANIZER[0]}"
            local ARCADE_ORGANIZER_INI="${SETTINGS_OPTIONS_ARCADE_ORGANIZER_INI[0]}"
            local SKIPALTS="${SETTINGS_OPTIONS_SKIPALTS[0]}"
            local ORGDIR="${SETTINGS_OPTIONS_ORGDIR[0]}"

            load_vars_from_ini "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" "ARCADE_ORGANIZER" "ARCADE_ORGANIZER_INI"
            load_ini_file "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})"

            if [[ "${UPDATE_ALL_PC_UPDATER}" == "true" ]] ; then
                ARCADE_ORGANIZER="false"
            fi

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 $(settings_active_action ${ARCADE_ORGANIZER})"
            fi

            local ACTIVATE="1 $(settings_active_action ${ARCADE_ORGANIZER})"

            set +e
            dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --title "Arcade Organizer Settings" \
                --menu "$(settings_menu_descr_text ${EXPORTED_INI_PATH} ${ARCADE_ORGANIZER_INI})" 13 75 25 \
                "${ACTIVATE}" "Activated: ${ARCADE_ORGANIZER}" \
                "2 INI file"  "$(settings_normalize_ini_file ${ARCADE_ORGANIZER_INI})" \
                "3 Skip MRA-Alternatives" "${SKIPALTS}" \
                "4 Organized Folders" "${ORGDIR}/*" \
                "5 Clean Folders" "Deletes the Arcade Organizer folders" \
                "BACK"  "" 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "${ACTIVATE}")
                    if [[ "${UPDATE_ALL_PC_UPDATER}" != "true" ]] ; then
                        settings_change_var "ARCADE_ORGANIZER" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})"
                    else
                        set +e
                        dialog --keep-window --msgbox "Arcade Organizer should be run from MiSTer\n\nRun arcade_organizer.sh there after the first run of 'Update All' is done" 7 77
                        set -e
                    fi
                    ;;
                "2 INI file") settings_change_var "ARCADE_ORGANIZER_INI" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                "3 Skip MRA-Alternatives") settings_change_var "SKIPALTS" "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "4 Organized Folders") settings_change_var "ORGDIR" "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "5 Clean Folders")
                    run_quiet_mame_getter_script "${ARCADE_ORGANIZER_URL}" "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" --print-orgdir-folders
                    if [[ "${RUN_QUIET_MAME_GETTER_SCRIPT_OUTPUT}" == "" ]] ; then
                        settings_menu_connection_problem
                        continue
                    fi

                    local ORGDIR_FOLDERS=()
                    local YESNO_MESSAGE="WARNING! You will lose ALL the data contained in the folders:"
                    while IFS="" read -r p || [ -n "${p}" ] ; do
                        if [ -d "${p}" ] ; then
                            ORGDIR_FOLDERS+=( "${p}" )
                            YESNO_MESSAGE="${YESNO_MESSAGE}\n  ${p}"
                        fi
                    done < "${RUN_QUIET_MAME_GETTER_SCRIPT_OUTPUT}"

                    if [ "${#ORGDIR_FOLDERS[@]}" -ge 1 ] ; then
                        set +e
                        DIALOGRC="${SETTINGS_TMP_BLACK_DIALOGRC}" dialog --keep-window --title "ARE YOU SURE?" --defaultno \
                            --yesno "${YESNO_MESSAGE}" \
                            $((${#ORGDIR_FOLDERS[@]} + 5)) 66
                        local SURE_RET=$?
                        set -e
                        if [[ "${SURE_RET}" == "0" ]] ; then
                            for p in "${ORGDIR_FOLDERS[@]}" ; do
                                rm -rf "${p}"
                            done
                            set +e
                            dialog --keep-window --msgbox "Organized folder Cleared" 5 29
                            set -e
                        else
                            set +e
                            dialog --keep-window --msgbox "Operaton Canceled" 5 22
                            set -e
                        fi
                    else
                        set +e
                        dialog --keep-window --msgbox "Organized folder doesn't exist" 5 35
                        set -e
                    fi
                    delete_if_empty "${BASE_PATH}/_Arcade/_Organized" "${BASE_PATH}/_Arcade Organized" > /dev/null
                    ;;
                *) echo > "${SETTINGS_TMP_BREAK}" ;;
            esac
        )
        if [ -f "${SETTINGS_TMP_BREAK}" ] ; then
            rm "${SETTINGS_TMP_BREAK}" 2> /dev/null
            break
        fi
    done
    rm ${TMP}
}

settings_menu_2beta_arcade_organizer() {
    local TMP=$(mktemp)

    SETTINGS_OPTIONS_ARCADE_ORGANIZER_INI=("update_arcade-organizer.ini" "$(settings_normalize_ini_file ${EXPORTED_INI_PATH})")
    settings_try_add_ini_option 'SETTINGS_OPTIONS_ARCADE_ORGANIZER_INI' "${ARCADE_ORGANIZER_INI}"
    SETTINGS_OPTIONS_SKIPALTS=("true" "false")
    SETTINGS_OPTIONS_ORGDIR=("${ARCADE_ORGANIZER_FOLDER_OPTION_1}" "${ARCADE_ORGANIZER_FOLDER_OPTION_2}" "${ARCADE_ORGANIZER_FOLDER_OPTION_3}")
    SETTINGS_OPTIONS_TOPDIR=("" "platform" "core" "year")
    SETTINGS_OPTIONS_PREPEND_YEAR=("false" "true")
    SETTINGS_OPTIONS_MAD_DB=("https://raw.githubusercontent.com/theypsilon/MAD_Database_MiSTer/db/mad_db.json.zip" "https://raw.githubusercontent.com/misteraddons/MiSTer_Arcade_MAD/db/mad_db.json.zip")
    SETTINGS_OPTIONS_VERBOSE=("false" "true")

    while true ; do
        (
            local ARCADE_ORGANIZER="${SETTINGS_OPTIONS_ARCADE_ORGANIZER[0]}"
            local ARCADE_ORGANIZER_INI="${SETTINGS_OPTIONS_ARCADE_ORGANIZER_INI[0]}"
            local SKIPALTS="${SETTINGS_OPTIONS_SKIPALTS[0]}"
            local ORGDIR="${SETTINGS_OPTIONS_ORGDIR[0]}"
            local TOPDIR="${SETTINGS_OPTIONS_TOPDIR[0]}"
            local PREPEND_YEAR="${SETTINGS_OPTIONS_PREPEND_YEAR[0]}"
            local MAD_DB="${SETTINGS_OPTIONS_MAD_DB[0]}"
            local VERBOSE="${SETTINGS_OPTIONS_VERBOSE[0]}"

            load_vars_from_ini "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" "ARCADE_ORGANIZER" "ARCADE_ORGANIZER_INI"
            load_ini_file "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})"

            if [[ "${UPDATE_ALL_PC_UPDATER}" == "true" ]] ; then
                ARCADE_ORGANIZER="false"
            fi

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 $(settings_active_action ${ARCADE_ORGANIZER})"
            fi

            local ACTIVATE="1 $(settings_active_action ${ARCADE_ORGANIZER})"
            local MAD_DB_DESCRIPTION="${MAD_DB#*.*/}"
            MAD_DB_DESCRIPTION="${MAD_DB_DESCRIPTION%.zip}"
            MAD_DB_DESCRIPTION="${MAD_DB_DESCRIPTION:0:50}"

            if [[ "${TOPDIR}" == "" ]] ; then
                TOPDIR_DESCRIPTION="Disabled"
            else
                TOPDIR_DESCRIPTION="From '${TOPDIR}' subfolder"
            fi
            set +e
            dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --no-shadow --title "Arcade Organizer 2.0~Beta Settings" \
                --menu "$(settings_menu_descr_text ${EXPORTED_INI_PATH} ${ARCADE_ORGANIZER_INI})" 22 80 25 \
                "${ACTIVATE}"               "Activated: ${ARCADE_ORGANIZER}" \
                "2 INI file"                "$(settings_normalize_ini_file ${ARCADE_ORGANIZER_INI})" \
                "3 Organized Folders"       "${ORGDIR}/*" \
                "4 Selected Database"         "${MAD_DB_DESCRIPTION}" \
                "5 Top additional folders"    "${TOPDIR_DESCRIPTION}" \
                "6 Skip MRA-Alternatives"   "$(settings_menu_yesno_bool_text ${SKIPALTS})" \
                "7 Chronological sort below"  "$(settings_menu_yesno_bool_text ${PREPEND_YEAR})" \
                "8 Verbose script output"     "$(settings_menu_yesno_bool_text ${VERBOSE})" \
                "9 Alphabetic"        "Options for 0-9 and A-Z folders" \
                "0 Region"            "Options for Regions (World, Japan, USA...)" \
                "A Collections"       "Options for Platform, Core, Category, Year..." \
                "S Video & Input"     "Options for Rotation, Resolution, Inputs..." \
                "D Extra Software"    "Options for Hombrew, Bootleg, Hacks..." \
                "F Advanced Submenu"  "Advanced Options" \
                "BACK"                        "                                               " 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "${ACTIVATE}")
                    if [[ "${UPDATE_ALL_PC_UPDATER}" != "true" ]] ; then
                        settings_change_var "ARCADE_ORGANIZER" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})"
                    else
                        set +e
                        dialog --keep-window --msgbox "Arcade Organizer should be run from MiSTer\n\nRun arcade_organizer.sh there after the first run of 'Update All' is done" 7 77
                        set -e
                    fi
                    ;;
                "2 INI file") settings_change_var "ARCADE_ORGANIZER_INI" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                "6 Skip MRA-Alternatives") settings_change_var "SKIPALTS" "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "3 Organized Folders") settings_change_var "ORGDIR" "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "4 Selected Database") settings_change_var "MAD_DB" "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "7 Chronological sort below") settings_change_var "PREPEND_YEAR" "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "5 Top additional folders") settings_change_var "TOPDIR" "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "8 Verbose script output")  settings_change_var "VERBOSE" "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "9 Alphabetic") settings_menu_ao_alphabetic_options ;;
                "0 Region") settings_menu_ao_region_options ;;
                "A Collections") settings_menu_ao_collections_options ;;
                "S Video & Input") settings_menu_ao_video_and_inputs_options ;;
                "D Extra Software") settings_menu_ao_extra_software_options ;;
                "F Advanced Submenu") settings_menu_ao_advanced_options ;;
                *) echo > "${SETTINGS_TMP_BREAK}" ;;
            esac
        )
        if [ -f "${SETTINGS_TMP_BREAK}" ] ; then
            rm "${SETTINGS_TMP_BREAK}" 2> /dev/null
            break
        fi
    done
    rm ${TMP}
}

settings_menu_ao_advanced_options() {
    local TMP=$(mktemp)

    while true ; do
        (
            load_vars_from_ini "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" "ARCADE_ORGANIZER_INI"
            load_ini_file "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})"

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="BACK"
            fi

            set +e
            dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --no-shadow --title "Arcade Organizer 2.0~Beta Advanced Options" \
                --menu "$(settings_menu_descr_text ${ARCADE_ORGANIZER_INI} ${ARCADE_ORGANIZER_INI})" 22 80 25 \
                "1 Clean Folders"           "Deletes the Arcade Organizer folders" \
                "BACK"  "                                               " 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "1 Clean Folders")
                    run_quiet_mame_getter_script "${ARCADE_ORGANIZER_2BETA_URL}" "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" --print-orgdir-folders
                    if [[ "${RUN_QUIET_MAME_GETTER_SCRIPT_OUTPUT}" == "" ]] ; then
                        settings_menu_connection_problem
                        continue
                    fi

                    local ORGDIR_FOLDERS=()
                    local YESNO_MESSAGE="WARNING! You will lose ALL the data contained in the folders:"
                    while IFS="" read -r p || [ -n "${p}" ] ; do
                        if [ -d "${p}" ] ; then
                            ORGDIR_FOLDERS+=( "${p}" )
                            YESNO_MESSAGE="${YESNO_MESSAGE}\n  ${p}"
                        fi
                    done < "${RUN_QUIET_MAME_GETTER_SCRIPT_OUTPUT}"

                    if [ "${#ORGDIR_FOLDERS[@]}" -ge 1 ] ; then
                        set +e
                        DIALOGRC="${SETTINGS_TMP_BLACK_DIALOGRC}" dialog --keep-window --title "ARE YOU SURE?" --defaultno \
                            --yesno "${YESNO_MESSAGE}" \
                            $((${#ORGDIR_FOLDERS[@]} + 5)) 66
                        local SURE_RET=$?
                        set -e
                        if [[ "${SURE_RET}" == "0" ]] ; then
                            for p in "${ORGDIR_FOLDERS[@]}" ; do
                                rm -rf "${p}"
                            done

                            set +e
                            dialog --keep-window --msgbox "Organized folder Cleared" 5 29
                            set -e
                        else
                            set +e
                            dialog --keep-window --msgbox "Operaton Canceled" 5 22
                            set -e
                        fi
                    else
                        set +e
                        dialog --keep-window --msgbox "Organized folder doesn't exist" 5 35
                        set -e
                    fi
                    delete_if_empty "${BASE_PATH}/_Arcade/_Organized" "${BASE_PATH}/_Arcade Organized" > /dev/null
                    ;;
                *) echo > "${SETTINGS_TMP_BREAK}" ;;
            esac
        )
        if [ -f "${SETTINGS_TMP_BREAK}" ] ; then
            rm "${SETTINGS_TMP_BREAK}" 2> /dev/null
            break
        fi
    done
    rm ${TMP}
}

settings_menu_ao_alphabetic_options() {
    local TMP=$(mktemp)

    SETTINGS_OPTIONS_AZ_DIR=("true" "false")

    while true ; do
        (
            local AZ_DIR="${SETTINGS_OPTIONS_AZ_DIR[0]}"

            load_vars_from_ini "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" "ARCADE_ORGANIZER_INI"
            load_ini_file "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})"

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 Alphabetic folders"
            fi

            set +e
            dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --no-shadow --title "Arcade Organizer 2.0~Beta Alphabetic Options" \
                --menu "$(settings_menu_descr_text ${ARCADE_ORGANIZER_INI} ${ARCADE_ORGANIZER_INI})" 22 80 25 \
                "1 Alphabetic folders"               "$(settings_menu_yesno_bool_text ${AZ_DIR})" \
                "BACK"  "                                               " 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "1 Alphabetic folders") settings_change_var "AZ_DIR" "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                *) echo > "${SETTINGS_TMP_BREAK}" ;;
            esac
        )
        if [ -f "${SETTINGS_TMP_BREAK}" ] ; then
            rm "${SETTINGS_TMP_BREAK}" 2> /dev/null
            break
        fi
    done
    rm ${TMP}
}

settings_menu_ao_region_options() {
    local TMP=$(mktemp)

    SETTINGS_OPTIONS_REGION_DIR=("true" "false")
    SETTINGS_OPTIONS_REGION_MAIN=("DEV PREFERRED" "Japan" "World" "USA" "Asia" "Europe" "Hispanic" "Spain" "Argentina" "Italy" "Brazil" "France" "German" "Germany")
    SETTINGS_OPTIONS_REGION_OTHER=("1" "0" "2")

    while true ; do
        (
            local REGION_DIR="${SETTINGS_OPTIONS_REGION_DIR[0]}"
            local REGION_MAIN="${SETTINGS_OPTIONS_REGION_MAIN[0]}"
            local REGION_OTHER="${SETTINGS_OPTIONS_REGION_OTHER[0]}"

            load_vars_from_ini "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" "ARCADE_ORGANIZER_INI"
            load_ini_file "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})"

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 Region folders"
            fi

            if [[ "${REGION_MAIN}" == "DEV PREFERRED" ]] ; then
                REGION_MAIN_DESCRIPTION="Region preferred by the MiSTer Core author"
            else
                REGION_MAIN_DESCRIPTION="${REGION_MAIN}"
            fi

            set +e
            dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --no-shadow --title "Arcade Organizer 2.0~Beta Region Options" \
                --menu "$(settings_menu_descr_text ${ARCADE_ORGANIZER_INI} ${ARCADE_ORGANIZER_INI})" 22 80 25 \
                "1 Region folders"               "$(settings_menu_yesno_bool_text ${REGION_DIR})" \
                "2 Main region"                  "${REGION_MAIN_DESCRIPTION}" \
                "3 MRAs with other regions"                  "$(settings_menu_boolflagpresence_text ${REGION_OTHER} Region)" \
                "BACK"  "                                               " 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "1 Region folders") settings_change_var "REGION_DIR" "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "2 Main region") settings_change_var "REGION_MAIN" "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "3 MRAs with other regions") settings_change_var "REGION_OTHER" "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                *) echo > "${SETTINGS_TMP_BREAK}" ;;
            esac
        )
        if [ -f "${SETTINGS_TMP_BREAK}" ] ; then
            rm "${SETTINGS_TMP_BREAK}" 2> /dev/null
            break
        fi
    done
    rm ${TMP}
}

settings_menu_ao_collections_options() {
    local TMP=$(mktemp)

    SETTINGS_OPTIONS_PLATFORM_DIR=("true" "false")
    SETTINGS_OPTIONS_CORE_DIR=("true" "false")
    SETTINGS_OPTIONS_CATEGORY_DIR=("true" "false")
    SETTINGS_OPTIONS_MANUFACTURER_DIR=("true" "false")
    SETTINGS_OPTIONS_SERIES_DIR=("true" "false")
    SETTINGS_OPTIONS_BEST_OF_DIR=("true" "false")

    while true ; do
        (
            local PLATFORM_DIR="${SETTINGS_OPTIONS_PLATFORM_DIR[0]}"
            local CORE_DIR="${SETTINGS_OPTIONS_CORE_DIR[0]}"
            local CATEGORY_DIR="${SETTINGS_OPTIONS_CATEGORY_DIR[0]}"
            local MANUFACTURER_DIR="${SETTINGS_OPTIONS_MANUFACTURER_DIR[0]}"
            local SERIES_DIR="${SETTINGS_OPTIONS_SERIES_DIR[0]}"
            local BEST_OF_DIR="${SETTINGS_OPTIONS_BEST_OF_DIR[0]}"

            load_vars_from_ini "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" "ARCADE_ORGANIZER_INI"
            load_ini_file "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})"

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 Platform folders"
            fi

            set +e
            dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --no-shadow --title "Arcade Organizer 2.0~Beta Collections Options" \
                --menu "$(settings_menu_descr_text ${ARCADE_ORGANIZER_INI} ${ARCADE_ORGANIZER_INI})" 22 80 25 \
                "1 Platform folders"               "$(settings_menu_yesno_bool_text ${PLATFORM_DIR})" \
                "2 MiSTer Core folders"            "$(settings_menu_yesno_bool_text ${CORE_DIR})" \
                "3 Year options"                   "" \
                "4 Category folders"               "$(settings_menu_yesno_bool_text ${CATEGORY_DIR})" \
                "5 Manufacturer folders"           "$(settings_menu_yesno_bool_text ${MANUFACTURER_DIR})" \
                "6 Series folders"                 "$(settings_menu_yesno_bool_text ${SERIES_DIR})" \
                "7 Best-of folders"                "$(settings_menu_yesno_bool_text ${BEST_OF_DIR})" \
                "BACK"  "                                               " 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "1 Platform folders"    ) settings_change_var "PLATFORM_DIR"     "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "2 MiSTer Core folders" ) settings_change_var "CORE_DIR"         "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "3 Year options"        ) settings_menu_ao_year_options ;;
                "4 Category folders"    ) settings_change_var "CATEGORY_DIR"     "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "5 Manufacturer folders") settings_change_var "MANUFACTURER_DIR" "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "6 Series folders"      ) settings_change_var "SERIES_DIR"       "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "7 Best-of folders"     ) settings_change_var "BEST_OF_DIR"      "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                *) echo > "${SETTINGS_TMP_BREAK}" ;;
            esac
        )
        if [ -f "${SETTINGS_TMP_BREAK}" ] ; then
            rm "${SETTINGS_TMP_BREAK}" 2> /dev/null
            break
        fi
    done
    rm ${TMP}
}

settings_menu_ao_year_options() {
    local TMP=$(mktemp)

    SETTINGS_OPTIONS_YEAR_DIR=("true" "false")
    SETTINGS_OPTIONS_DECADES_DIR=("true" "false")

    while true ; do
        (
            local YEAR_DIR="${SETTINGS_OPTIONS_YEAR_DIR[0]}"
            local DECADES_DIR="${SETTINGS_OPTIONS_DECADE_DIR[0]}"

            load_vars_from_ini "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" "ARCADE_ORGANIZER_INI"
            load_ini_file "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})"

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 Year folders"
            fi

            if [[ "${YEAR_DIR}" == "true" ]] ; then
                set +e
                dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --no-shadow --title "Arcade Organizer 2.0~Beta Year Options" \
                --menu "$(settings_menu_descr_text ${ARCADE_ORGANIZER_INI} ${ARCADE_ORGANIZER_INI})" 22 80 25 \
                    "1 Year folders"            "$(settings_menu_yesno_bool_text ${YEAR_DIR})" \
                    "2 Decade folders"         "$(settings_menu_yesno_bool_text ${DECADES_DIR})" \
                    "BACK"  "                                               " 2> ${TMP}
                DEFAULT_SELECTION="$?"
                set -e
            else
                set +e
                dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --no-shadow --title "Arcade Organizer 2.0~Beta Year Options" \
                --menu "$(settings_menu_descr_text ${ARCADE_ORGANIZER_INI} ${ARCADE_ORGANIZER_INI})" 22 80 25 \
                    "1 Year folders"            "$(settings_menu_yesno_bool_text ${YEAR_DIR})" \
                    "BACK"  "                                               " 2> ${TMP}
                DEFAULT_SELECTION="$?"
                set -e
            fi

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "1 Year folders" ) settings_change_var "YEAR_DIR"         "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "2 Decade folders"        ) settings_change_var "DECADES_DIR"         "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                *) echo > "${SETTINGS_TMP_BREAK}" ;;
            esac
        )
        if [ -f "${SETTINGS_TMP_BREAK}" ] ; then
            rm "${SETTINGS_TMP_BREAK}" 2> /dev/null
            break
        fi
    done
    rm ${TMP}
}

settings_menu_ao_video_and_inputs_options() {
    local TMP=$(mktemp)

    SETTINGS_OPTIONS_RESOLUTION_DIR=("true" "false")
    SETTINGS_OPTIONS_ROTATION_DIR=("true" "false")
    SETTINGS_OPTIONS_MOVE_INPUTS_DIR=("true" "false")
    SETTINGS_OPTIONS_NUM_BUTTONS_DIR=("true" "false")
    SETTINGS_OPTIONS_SPECIAL_CONTROLS_DIR=("true" "false")
    SETTINGS_OPTIONS_NUM_CONTROLLERS_DIR=("true" "false")
    SETTINGS_OPTIONS_COCKTAIL_DIR=("true" "false")
    SETTINGS_OPTIONS_NUM_MONITORS_DIR=("true" "false")

    while true ; do
        (
            local RESOLUTION_DIR="${SETTINGS_OPTIONS_RESOLUTION_DIR[0]}"
            local ROTATION_DIR="${SETTINGS_OPTIONS_ROTATION_DIR[0]}"
            local MOVE_INPUTS_DIR="${SETTINGS_OPTIONS_MOVE_INPUTS_DIR[0]}"
            local NUM_BUTTONS_DIR="${SETTINGS_OPTIONS_NUM_BUTTONS_DIR[0]}"
            local SPECIAL_CONTROLS_DIR="${SETTINGS_OPTIONS_SPECIAL_CONTROLS_DIR[0]}"
            local NUM_CONTROLLERS_DIR="${SETTINGS_OPTIONS_NUM_CONTROLLERS_DIR[0]}"
            local COCKTAIL_DIR="${SETTINGS_OPTIONS_COCKTAIL_DIR[0]}"
            local NUM_MONITORS_DIR="${SETTINGS_OPTIONS_NUM_MONITORS_DIR[0]}"

            load_vars_from_ini "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" "ARCADE_ORGANIZER_INI"
            load_ini_file "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})"

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 Resolution options"
            fi

            set +e
            dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --no-shadow --title "Arcade Organizer 2.0~Beta Video & Inputs Options" \
                --menu "$(settings_menu_descr_text ${ARCADE_ORGANIZER_INI} ${ARCADE_ORGANIZER_INI})" 22 80 25 \
                "1 Resolution options"          "" \
                "2 Rotation options"            "" \
                "3 Move Inputs folders"         "$(settings_menu_yesno_bool_text ${MOVE_INPUTS_DIR})" \
                "4 Num Buttons folders"         "$(settings_menu_yesno_bool_text ${NUM_BUTTONS_DIR})" \
                "5 Special Inputs folders"      "$(settings_menu_yesno_bool_text ${SPECIAL_CONTROLS_DIR})" \
                "6 Num Controllers folders"     "$(settings_menu_yesno_bool_text ${NUM_CONTROLLERS_DIR})" \
                "7 Cockail folders"             "$(settings_menu_yesno_bool_text ${COCKTAIL_DIR})" \
                "8 Num Monitors folders"        "$(settings_menu_yesno_bool_text ${NUM_MONITORS_DIR})" \
                "BACK"  "                                               " 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "1 Resolution options"    ) settings_menu_ao_resolution_options ;;
                "2 Rotation options" ) settings_menu_ao_rotation_options ;;
                "3 Move Inputs folders"        ) settings_change_var "MOVE_INPUTS_DIR"         "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "4 Num Buttons folders"    ) settings_change_var "NUM_BUTTONS_DIR"     "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "5 Special Inputs folders") settings_change_var "SPECIAL_CONTROLS_DIR" "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "6 Num Controllers folders"      ) settings_change_var "NUM_CONTROLLERS_DIR"       "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "7 Cockail folders"     ) settings_change_var "COCKTAIL_DIR"      "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "8 Num Monitors folders"     ) settings_change_var "NUM_MONITORS_DIR"      "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                *) echo > "${SETTINGS_TMP_BREAK}" ;;
            esac
        )
        if [ -f "${SETTINGS_TMP_BREAK}" ] ; then
            rm "${SETTINGS_TMP_BREAK}" 2> /dev/null
            break
        fi
    done
    rm ${TMP}
}

settings_menu_ao_resolution_options() {
    local TMP=$(mktemp)

    SETTINGS_OPTIONS_RESOLUTION_DIR=("true" "false")
    SETTINGS_OPTIONS_RESOLUTION_15KHZ=("true" "false")
    SETTINGS_OPTIONS_RESOLUTION_24KHZ=("true" "false")
    SETTINGS_OPTIONS_RESOLUTION_31KHZ=("true" "false")
    SETTINGS_OPTIONS_ROTATION_270=("true" "false")
    SETTINGS_OPTIONS_FLIP=("true" "false")
    SETTINGS_OPTIONS_COCKTAIL_DIR=("true" "false")
    SETTINGS_OPTIONS_NUM_MONITORS_DIR=("true" "false")

    while true ; do
        (
            local RESOLUTION_DIR="${SETTINGS_OPTIONS_RESOLUTION_DIR[0]}"
            local RESOLUTION_15KHZ="${SETTINGS_OPTIONS_RESOLUTION_15KHZ[0]}"
            local RESOLUTION_24KHZ="${SETTINGS_OPTIONS_RESOLUTION_24KHZ[0]}"
            local RESOLUTION_31KHZ="${SETTINGS_OPTIONS_RESOLUTION_31KHZ[0]}"
            local ROTATION_270="${SETTINGS_OPTIONS_ROTATION_270[0]}"
            local FLIP="${SETTINGS_OPTIONS_FLIP[0]}"

            load_vars_from_ini "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" "ARCADE_ORGANIZER_INI"
            load_ini_file "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})"

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 Resolution folders"
            fi

            set +e
            dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --no-shadow --title "Arcade Organizer 2.0~Beta Resolution Options" \
            --menu "$(settings_menu_descr_text ${ARCADE_ORGANIZER_INI} ${ARCADE_ORGANIZER_INI})" 22 80 25 \
                "1 Resolution folders"            "$(settings_menu_yesno_bool_text ${RESOLUTION_DIR})" \
                "2 15 kHz Scan Rate"         "$(settings_menu_yesno_bool_text ${RESOLUTION_15KHZ})" \
                "3 24 kHz Scan Rate"         "$(settings_menu_yesno_bool_text ${RESOLUTION_24KHZ})" \
                "4 31 kHz Scan Rate"         "$(settings_menu_yesno_bool_text ${RESOLUTION_31KHZ})" \
                "BACK"  "                                               " 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "1 Resolution folders" ) settings_change_var "RESOLUTION_DIR"         "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "2 15 kHz Scan Rate"        ) settings_change_var "RESOLUTION_15KHZ"         "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "3 24 kHz Scan Rate"    ) settings_change_var "RESOLUTION_24KHZ"     "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "4 31 kHz Scan Rate"      ) settings_change_var "RESOLUTION_31KHZ" "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                *) echo > "${SETTINGS_TMP_BREAK}" ;;
            esac
        )
        if [ -f "${SETTINGS_TMP_BREAK}" ] ; then
            rm "${SETTINGS_TMP_BREAK}" 2> /dev/null
            break
        fi
    done
    rm ${TMP}
}

settings_menu_ao_rotation_options() {
    local TMP=$(mktemp)

    SETTINGS_OPTIONS_ROTATION_DIR=("true" "false")
    SETTINGS_OPTIONS_ROTATION_0=("true" "false")
    SETTINGS_OPTIONS_ROTATION_90=("true" "false")
    SETTINGS_OPTIONS_ROTATION_180=("true" "false")
    SETTINGS_OPTIONS_ROTATION_270=("true" "false")
    SETTINGS_OPTIONS_FLIP=("true" "false")

    while true ; do
        (
            local ROTATION_DIR="${SETTINGS_OPTIONS_ROTATION_DIR[0]}"
            local ROTATION_0="${SETTINGS_OPTIONS_ROTATION_0[0]}"
            local ROTATION_90="${SETTINGS_OPTIONS_ROTATION_90[0]}"
            local ROTATION_180="${SETTINGS_OPTIONS_ROTATION_180[0]}"
            local ROTATION_270="${SETTINGS_OPTIONS_ROTATION_270[0]}"
            local FLIP="${SETTINGS_OPTIONS_FLIP[0]}"

            load_vars_from_ini "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" "ARCADE_ORGANIZER_INI"
            load_ini_file "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})"

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 Rotation folders"
            fi

            set +e
            dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --no-shadow --title "Arcade Organizer 2.0~Beta Rotation Options" \
            --menu "$(settings_menu_descr_text ${ARCADE_ORGANIZER_INI} ${ARCADE_ORGANIZER_INI})" 22 80 25 \
                "1 Rotation folders"            "$(settings_menu_yesno_bool_text ${ROTATION_DIR})" \
                "2 Horizontal"         "$(settings_menu_yesno_bool_text ${ROTATION_0})" \
                "3 Vertical Clockwise"         "$(settings_menu_yesno_bool_text ${ROTATION_90})" \
                "4 Vertical Counter-Clockwise"      "$(settings_menu_yesno_bool_text ${ROTATION_270})" \
                "5 Horizontal (reversed)"         "$(settings_menu_yesno_bool_text ${ROTATION_180})" \
                "6 Cores with Flip in opposite Rotations"     "$(settings_menu_yesno_bool_text ${FLIP})" \
                "BACK"  "                                               " 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "1 Rotation folders" ) settings_change_var "ROTATION_DIR"         "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "2 Horizontal"        ) settings_change_var "ROTATION_0"         "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "3 Vertical Clockwise"    ) settings_change_var "ROTATION_90"     "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "4 Vertical Counter-Clockwise") settings_change_var "ROTATION_270" "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "5 Horizontal (reversed)"      ) settings_change_var "ROTATION_180" "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "6 Cores with Flip in opposite Rotations"      ) settings_change_var "FLIP"       "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                *) echo > "${SETTINGS_TMP_BREAK}" ;;
            esac
        )
        if [ -f "${SETTINGS_TMP_BREAK}" ] ; then
            rm "${SETTINGS_TMP_BREAK}" 2> /dev/null
            break
        fi
    done
    rm ${TMP}
}

settings_menu_ao_extra_software_options() {
    local TMP=$(mktemp)

    SETTINGS_OPTIONS_HOMEBREW=("1" "0" "2")
    SETTINGS_OPTIONS_BOOTLEG=("1" "0" "2")
    SETTINGS_OPTIONS_HACKS=("1" "0" "2")
    SETTINGS_OPTIONS_TRANSLATIONS=("1" "0" "2")
    SETTINGS_OPTIONS_ENHANCEMENTS=("1" "0" "2")

    while true ; do
        (
            local HOMEBREW="${SETTINGS_OPTIONS_HOMEBREW[0]}"
            local BOOTLEG="${SETTINGS_OPTIONS_BOOTLEG[0]}"
            local HACKS="${SETTINGS_OPTIONS_HACKS[0]}"
            local TRANSLATIONS="${SETTINGS_OPTIONS_TRANSLATIONS[0]}"
            local ENHANCEMENTS="${SETTINGS_OPTIONS_ENHANCEMENTS[0]}"

            load_vars_from_ini "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" "ARCADE_ORGANIZER_INI"
            load_ini_file "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})"

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 Hombrew"
            fi

            set +e
            dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --no-shadow --title "Arcade Organizer 2.0~Beta Extra Software Options" \
                --menu "$(settings_menu_descr_text ${ARCADE_ORGANIZER_INI} ${ARCADE_ORGANIZER_INI})" 22 80 25 \
                "1 Hombrew"          "$(settings_menu_boolflagpresence_text ${HOMEBREW} Hombrew)" \
                "2 Bootleg"            "$(settings_menu_boolflagpresence_text ${BOOTLEG} Bootleg)" \
                "3 Enhancements"      "$(settings_menu_boolflagpresence_text ${ENHANCEMENTS} Enhancements)" \
                "4 Translations"         "$(settings_menu_boolflagpresence_text ${TRANSLATIONS} Translations)" \
                "5 Hacks"         "$(settings_menu_boolflagpresence_text ${HACKS} Hacks)" \
                "BACK"  "                                               " 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "1 Hombrew"    ) settings_change_var "HOMEBREW"     "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "2 Bootleg" ) settings_change_var "BOOTLEG"         "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "5 Hacks"        ) settings_change_var "HACKS"         "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "4 Translations"    ) settings_change_var "TRANSLATIONS"     "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                "3 Enhancements") settings_change_var "ENHANCEMENTS" "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})" ;;
                *) echo > "${SETTINGS_TMP_BREAK}" ;;
            esac
        )
        if [ -f "${SETTINGS_TMP_BREAK}" ] ; then
            rm "${SETTINGS_TMP_BREAK}" 2> /dev/null
            break
        fi
    done
    rm ${TMP}
}

settings_menu_misc() {
    local TMP=$(mktemp)

    SETTINGS_OPTIONS_AUTOREBOOT=("true" "false")
    SETTINGS_OPTIONS_WAIT_TIME_FOR_READING=("4" "0" "30")
    SETTINGS_OPTIONS_COUNTDOWN_TIME=("15" "4" "60")
    SETTINGS_OPTIONS_ARCADE_ORGANIZER_2_ALPHA_ENABLED=("false" "true")
    SETTINGS_OPTIONS_DOWNLOADER_WHEN_POSSIBLE=("false", "true")
    SETTINGS_OPTIONS_ARCADE_OFFSET_DOWNLOADER=("false" "true")

    while true ; do
        (
            local AUTOREBOOT="${SETTINGS_OPTIONS_AUTOREBOOT[0]}"
            local WAIT_TIME_FOR_READING="${SETTINGS_OPTIONS_WAIT_TIME_FOR_READING[0]}"
            local COUNTDOWN_TIME="${SETTINGS_OPTIONS_COUNTDOWN_TIME[0]}"
            local ARCADE_ORGANIZER_2_ALPHA_ENABLED="${SETTINGS_OPTIONS_ARCADE_ORGANIZER_2_ALPHA_ENABLED[0]}"
            local DOWNLOADER_WHEN_POSSIBLE="${SETTINGS_OPTIONS_DOWNLOADER_WHEN_POSSIBLE[0]}"
            local ARCADE_OFFSET_DOWNLOADER="${SETTINGS_OPTIONS_ARCADE_OFFSET_DOWNLOADER[0]}"

            load_vars_from_ini "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" "AUTOREBOOT" "WAIT_TIME_FOR_READING" "COUNTDOWN_TIME" "ARCADE_ORGANIZER_2_ALPHA_ENABLED" "DOWNLOADER_WHEN_POSSIBLE" "ARCADE_OFFSET_DOWNLOADER"

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 Autoreboot (if needed)"
            fi

            if [ -f /media/fat/payoyo_cheese.txt ] ; then
                set +e
                dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --title "Other Settings" \
                    --menu "" 14 75 25 \
                    "1 Use new Downloader" "$(settings_menu_yesno_bool_text ${DOWNLOADER_WHEN_POSSIBLE})" \
                    "2 Arcade Offset Downloader" "$(settings_menu_yesno_bool_text ${ARCADE_OFFSET_DOWNLOADER})" \
                    "3 Autoreboot (if needed)" "$(settings_menu_yesno_bool_text ${AUTOREBOOT})" \
                    "4 Pause (between updaters)" "${WAIT_TIME_FOR_READING} seconds" \
                    "5 Countdown Timer" "${COUNTDOWN_TIME} seconds" \
                    "6 Clear All Cores" "Removes all CORES and MRA folders." \
                    "7 Arcade Organizer 2.0 Beta" "$(settings_menu_yesno_bool_text ${ARCADE_ORGANIZER_2_ALPHA_ENABLED})" \
                    "BACK"  "" 2> ${TMP}
                DEFAULT_SELECTION="$?"
                set -e
            else
            set +e
            dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --title "Other Settings" \
                --menu "" 12 75 25 \
                "3 Autoreboot (if needed)" "${AUTOREBOOT}" \
                "4 Pause (between updaters)" "${WAIT_TIME_FOR_READING} seconds" \
                "5 Countdown Timer" "${COUNTDOWN_TIME} seconds" \
                "6 Clear All Cores" "Removes all CORES and MRA folders." \
                "7 Arcade Organizer 2.0 Beta" "$(settings_menu_yesno_bool_text ${ARCADE_ORGANIZER_2_ALPHA_ENABLED})" \
                "BACK"  "" 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e
            fi

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "1 Use new Downloader") settings_change_var "DOWNLOADER_WHEN_POSSIBLE" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                "2 Arcade Offset Downloader") settings_change_var "ARCADE_OFFSET_DOWNLOADER" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                "3 Autoreboot (if needed)") settings_change_var "AUTOREBOOT" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                "4 Pause (between updaters)") settings_change_var "WAIT_TIME_FOR_READING" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                "5 Countdown Timer") settings_change_var "COUNTDOWN_TIME" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ;;
                "6 Clear All Cores")
                    local FILES_FOLDERS=("_Arcade" "_Computer" "_Console" "_Other" "_Utility" "_LLAPI" "_Jotego" "_CPS1" "_Unofficial")

                    local TO_DELETE=()
                    local YESNO_MESSAGE="\n                          CRITICAL WARNING !!\n\nYou will lose ALL data contained in following folders:"
                    for i in "${FILES_FOLDERS[@]}" ; do
                        local ELEMENT="${BASE_PATH}/${i}"
                        if [ -d "${ELEMENT}" ] ; then
                            TO_DELETE+=( "${ELEMENT}" )
                            YESNO_MESSAGE="${YESNO_MESSAGE}\n  ${ELEMENT}/*"
                        elif [ -f "${ELEMENT}" ] ; then
                            TO_DELETE+=( "${ELEMENT}" )
                            YESNO_MESSAGE="${YESNO_MESSAGE}\n  ${ELEMENT}"
                        fi
                    done

                    if [ "${#TO_DELETE[@]}" -ge 1 ] ; then
                        set +e
                        DIALOGRC="${SETTINGS_TMP_RED_DIALOGRC}" dialog --keep-window --title "ARE YOU SURE?" --defaultno \
                            --yesno "${YESNO_MESSAGE}" \
                            $((${#TO_DELETE[@]} + 8)) 75
                        local SURE_RET=$?
                        set -e

                        if [[ "${SURE_RET}" == "0" ]] ; then
                            set +e
                            DIALOGRC="${SETTINGS_TMP_RED_DIALOGRC}" dialog --keep-window --title "BE CAREFUL" --defaultno \
                                --yesno "Are you REALLY sure?\n\nMake sure you have read the directory list in previous screen!\nEverything appearing there will be gone forever.\n\n\"Yes\" means you know what you are doing here. Otherwise, you might\nregret this later!" \
                                11 75
                            local SURE_RET=$?
                            set -e
                        fi

                        if [[ "${SURE_RET}" == "0" ]] ; then
                            DIALOGRC="${SETTINGS_TMP_RED_DIALOGRC}" dialog --infobox "Deleting files and folders, please wait..." 3 47

                            for dir in "${TO_DELETE[@]}" ; do
                                rm -rf "${dir}"
                            done

                            rm "${MISTER_MAIN_UPDATER_WORK_FOLDER}/$(basename ${EXPORTED_INI_PATH%.*}).last_successful_run" 2> /dev/null || true
                            rm "${MISTER_MAIN_UPDATER_WORK_FOLDER}/MRA-Alternatives_"* 2> /dev/null || true

                            rm "${JOTEGO_UPDATER_WORK_FOLDER}/$(basename ${EXPORTED_INI_PATH%.*}).last_successful_run" 2> /dev/null || true
                            rm "${JOTEGO_UPDATER_WORK_FOLDER}/MRA-Alternatives_"* 2> /dev/null || true

                            rm "${UNOFFICIAL_UPDATER_WORK_FOLDER}/$(basename ${EXPORTED_INI_PATH%.*}).last_successful_run" 2> /dev/null || true
                            rm "${UNOFFICIAL_UPDATER_WORK_FOLDER}/MRA-Alternatives_"* 2> /dev/null || true

                            set +e
                            dialog --keep-window --msgbox "All cores and MRAs have been removed" 5 45
                            set -e
                        else
                            set +e
                            dialog --keep-window --msgbox "Operaton Canceled" 5 22
                            set -e
                        fi
                    else
                        set +e
                        dialog --keep-window --msgbox "No folders or files to clear" 5 35
                        set -e
                    fi
                    ;;
                "7 Arcade Organizer 2.0 Beta")
                    if [[ "${ARCADE_ORGANIZER_2_ALPHA_ENABLED}" == "false" ]] ; then
                        set +e
                        dialog --keep-window --title "Are you sure?" --defaultno \
                            --yesno "You are activating a BETA version that might contain bugs." \
                            5 66
                        local SURE_RET=$?
                        set -e
                        if [[ "${SURE_RET}" == "0" ]] ; then
                            settings_change_var "ARCADE_ORGANIZER_2_ALPHA_ENABLED" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})"
                            touch "${ARCADE_ORGANIZER_INI}"
                        fi
                    else
                        settings_change_var "ARCADE_ORGANIZER_2_ALPHA_ENABLED" "$(settings_domain_ini_file ${EXPORTED_INI_PATH})"
                        touch "${ARCADE_ORGANIZER_INI}"
                    fi
                    ;;
                *) echo > "${SETTINGS_TMP_BREAK}" ;;
            esac
        )
        if [ -f "${SETTINGS_TMP_BREAK}" ] ; then
            rm "${SETTINGS_TMP_BREAK}" 2> /dev/null
            break
        fi
    done
    rm ${TMP}
}

settings_menu_connection_problem() {
    set +e
    dialog --keep-window --msgbox "Network Problem" 5 20
    set -e
}

settings_menu_exit_and_run() {

    settings_files_to_save

    if [ ${#SETTINGS_FILES_TO_SAVE_RET_ARRAY[@]} -ge 1 ] ; then
        set +e
        dialog --keep-window --title "INI file/s were not saved" \
            --yesno "Do you really want to run Update All without saving your changes?"$'\n'"(current changes will apply only for this run)" \
            7 70
        local SURE_RET=$?
        set -e
        case $SURE_RET in
            0)
                load_vars_from_ini "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" "MAIN_UPDATER_INI" "JOTEGO_UPDATER_INI" "UNOFFICIAL_UPDATER_INI" "LLAPI_UPDATER_INI" \
                    "BIOS_GETTER_INI" "MAME_GETTER_INI" "HBMAME_GETTER_INI" "NAMES_TXT_UPDATER_INI" "ARCADE_ORGANIZER_INI"

                cp "$(settings_domain_ini_file ${EXPORTED_INI_PATH})" ${ORIGINAL_INI_PATH}

                echo >> "${ORIGINAL_INI_PATH}"

                settings_place_replace_value "${ORIGINAL_INI_PATH}" "MAIN_UPDATER_INI" "$(settings_domain_ini_file ${MAIN_UPDATER_INI})"
                settings_place_replace_value "${ORIGINAL_INI_PATH}" "JOTEGO_UPDATER_INI" "$(settings_domain_ini_file ${JOTEGO_UPDATER_INI})"
                settings_place_replace_value "${ORIGINAL_INI_PATH}" "UNOFFICIAL_UPDATER_INI" "$(settings_domain_ini_file ${UNOFFICIAL_UPDATER_INI})"
                settings_place_replace_value "${ORIGINAL_INI_PATH}" "LLAPI_UPDATER_INI" "$(settings_domain_ini_file ${LLAPI_UPDATER_INI})"
                settings_place_replace_value "${ORIGINAL_INI_PATH}" "BIOS_GETTER_INI" "$(settings_domain_ini_file ${BIOS_GETTER_INI})"
                settings_place_replace_value "${ORIGINAL_INI_PATH}" "MAME_GETTER_INI" "$(settings_domain_ini_file ${MAME_GETTER_INI})"
                settings_place_replace_value "${ORIGINAL_INI_PATH}" "HBMAME_GETTER_INI" "$(settings_domain_ini_file ${HBMAME_GETTER_INI})"
                settings_place_replace_value "${ORIGINAL_INI_PATH}" "NAMES_TXT_UPDATER_INI" "$(settings_domain_ini_file ${NAMES_TXT_UPDATER_INI})"
                settings_place_replace_value "${ORIGINAL_INI_PATH}" "ARCADE_ORGANIZER_INI" "$(settings_domain_ini_file ${ARCADE_ORGANIZER_INI})"
                ;;
            *) return ;;
        esac
    fi

    echo > "${SETTINGS_TMP_CONTINUE}"
}

settings_menu_cancel() {

    settings_files_to_save

    if [ ${#SETTINGS_FILES_TO_SAVE_RET_ARRAY[@]} -ge 1 ] ; then
        set +e
        dialog --keep-window --title "INI file/s were not saved" \
            --yesno "Do you really want to abort Update All without saving your changes?" \
            6 50
        local SURE_RET=$?
        set -e
        case $SURE_RET in
            0) ;;
            *) return ;;
        esac
    else
        set +e
        dialog --keep-window --msgbox "Pressed ESC/Abort"$'\n'"Closing Update All..." 6 30
        set -e
    fi

    echo > "${SETTINGS_TMP_BREAK}"
}

settings_menu_save() {

    settings_files_to_save

    if [ ${#SETTINGS_FILES_TO_SAVE_RET_ARRAY[@]} -eq 0 ] ; then
        set +e
        dialog --keep-window --msgbox "No changes to save" 5 22
        set -e
        return
    fi

    set +e
    dialog --keep-window --title "Are you sure?" \
        --yes-label "Save" \
        --no-label "Cancel" \
        --yesno "Following files would be overwritten with your changes:"$'\n'"${SETTINGS_FILES_TO_SAVE_RET_TEXT}" \
        "$((6+${#SETTINGS_FILES_TO_SAVE_RET_ARRAY[@]}))" 75
    local SURE_RET=$?
    set -e
    case $SURE_RET in
        0)
            for file in "${SETTINGS_FILES_TO_SAVE_RET_ARRAY[@]}" ; do
                cp "${SETTINGS_INI_FILES[${file}]}" "${file}"
            done
            if [ -f "${EXPORTED_INI_PATH}" ] ; then
                cp "${EXPORTED_INI_PATH}" "${ORIGINAL_INI_PATH}" 2> /dev/null || true
            fi
            if [ -d ../updater-pc ] ; then
                for ref in "${INI_REFERENCES[@]}" ; do
                    local -n INI_FILE="${ref}"
                    cp "${INI_FILE}" "../updater-pc/$(basename ${INI_FILE})" 2> /dev/null || true
                done
            fi
            set +e
            dialog --keep-window --msgbox "   Saved" 0 0
            set -e
            if [ -f "${SETTINGS_ON_FILENAME}" ] ; then
                rm "${SETTINGS_ON_FILENAME}" 2> /dev/null || true
            fi
            ;;
        *) ;;
    esac
}

declare -A SETTINGS_INI_FILES
settings_reset_domain_ini_files() {
    SETTINGS_INI_FILES=()
}

settings_add_domain_ini_file() {
    local INI_FILE="$(settings_normalize_ini_file ${1})"
    SETTINGS_INI_FILES["${INI_FILE}"]="/tmp/ua_settings_${INI_FILE//\//_}"
}

settings_domain_ini_file() {
    local INI_FILE="$(settings_normalize_ini_file ${1})"
    echo "${SETTINGS_INI_FILES[${INI_FILE}]}"
}

settings_create_domain_ini_files() {
    for key in ${!SETTINGS_INI_FILES[@]} ; do
        local value="${SETTINGS_INI_FILES[${key}]}"
        settings_make_ini_from "${key}" "${value}"
    done
}

settings_normalize_ini_file() {
    echo "${@}" | sed "s%${CURRENT_DIR}%%gI ; s%^\./%%g"
}

SETTINGS_FILES_TO_SAVE_RET_ARRAY=()
SETTINGS_FILES_TO_SAVE_RET_TEXT=
settings_files_to_save() {
    SETTINGS_FILES_TO_SAVE_RET_TEXT=""
    SETTINGS_FILES_TO_SAVE_RET_ARRAY=()
    local TMP_1=$(mktemp)
    local TMP_2=$(mktemp)
    for file in ${!SETTINGS_INI_FILES[@]} ; do
        if [ -f "${file}" ] ; then
            cat "${file}" | sort > "${TMP_1}"
        fi
        if [ -f "${SETTINGS_INI_FILES[${file}]}" ] ; then
            cat "${SETTINGS_INI_FILES[${file}]}" | sort > "${TMP_2}"
        fi
        if ! diff -q "${TMP_1}" "${TMP_2}" > /dev/null 2>&1 && \
            { \
                grep -q '[^[:space:]]' "${file}" > /dev/null 2>&1 \
                || grep -q '[^[:space:]]' "${SETTINGS_INI_FILES[${file}]}" > /dev/null 2>&1 \
            ; }
        then
            SETTINGS_FILES_TO_SAVE_RET_TEXT="${SETTINGS_FILES_TO_SAVE_RET_TEXT}"$'\n'"${file}"
            SETTINGS_FILES_TO_SAVE_RET_ARRAY+=("${file}")
        fi
    done
    rm "${TMP_1}"
    rm "${TMP_2}"
}

settings_menu_descr_text() {
    local INI_A="$(settings_normalize_ini_file ${1})"
    local INI_B="$(settings_normalize_ini_file ${2})"
    if [[ "${INI_A}" == "${INI_B}" ]] ; then
        echo "Settings loaded from '${INI_A}'"
    else
        echo "Settings loaded from '${INI_A}' and '${INI_B}'"
    fi
}

settings_menu_yesno_bool_text() {
    local VALUE="${1}"
    if [[ "${VALUE}" == "true" ]] ; then
        echo "Yes"
    else
        echo "No"
    fi
}

settings_menu_boolflagpresence_text() {
    case "${1}" in
        "0") echo "Ignore them entirely" ;;
        "1") echo "Place them only on its ${2} folder" ;;
        *) echo "Place them everywhere" ;;
    esac
}

settings_try_add_ini_option() {
    local INI_OPTION_ARRAY_NAME="${1}"
    local MAYBE_NEW_INI="${2}"

    local -n INI_OPTIONS="${INI_OPTION_ARRAY_NAME}"
    MAYBE_NEW_INI="$(settings_normalize_ini_file ${MAYBE_NEW_INI})"

    local CONTAINED="false"
    for OPTION in ${INI_OPTIONS[@]} ; do
        if [[ "${OPTION}" == "${MAYBE_NEW_INI}" ]] ; then
            CONTAINED="true"
        fi
    done

    if [[ "${CONTAINED}" == "false" ]] ; then
        INI_OPTIONS+=("${MAYBE_NEW_INI}")
    fi
}

settings_change_var() {
    local VAR="${1}"
    local INI_PATH="${2}"
    local -n OPTIONS="SETTINGS_OPTIONS_${VAR}"
    local DEFAULT="${OPTIONS[0]}"

    local VALUE="$(load_single_var_from_ini ${VAR} ${INI_PATH})"
    if [[ "${VALUE}" == "" ]] ; then
        VALUE="${DEFAULT}"
    fi

    local NEXT_INDEX=-1
    for i in "${!OPTIONS[@]}" ; do
        local CURRENT="${OPTIONS[${i}]}"
        if [[ "${CURRENT}" == "${VALUE}" ]] || { \
            [ -f "${VALUE}" ] && \
            [[ "${CURRENT}" == "$(settings_normalize_ini_file ${VALUE})" ]]; \
        } ; then
            NEXT_INDEX=$((i + 1))
            if [ ${NEXT_INDEX} -ge ${#OPTIONS[@]} ] ; then
                NEXT_INDEX=0
            fi
            break
        fi
    done

    if [ ${NEXT_INDEX} -eq -1 ] ; then
        if [[ "${DEBUG_UPDATER:-false}" != "true" ]] ; then
            NEXT_INDEX=0
        else
            echo "Bug on NEXT_INDEX"
            echo "VAR: ${VAR}"
            echo "INI_PATH: ${INI_PATH}"
            echo "VALUE: ${VALUE}"
            echo "DEFAULT: ${DEFAULT}"
            exit 1
        fi
    fi

    VALUE="${OPTIONS[${NEXT_INDEX}]}"

    sed -i "/^${VAR}=/d" ${INI_PATH} 2> /dev/null

    if [[ "${VALUE}" != "${DEFAULT}" ]] ; then
        if [ ! -z "$(tail -c 1 "${INI_PATH}")" ] ; then
            echo >> "${INI_PATH}"
        fi
        echo -n "${VAR}=\"${VALUE}\"" >> "${INI_PATH}"
    fi
}

settings_place_replace_value() {
    local INI_FILE="${1}"
    local VAR="${2}"
    local VALUE="${3}"

    if grep -q "${VAR}" "${INI_FILE}" ; then
        sed -i "s%${VAR}=.*%${VAR}=\"${VALUE}\"%g" "${INI_FILE}"
    else
        echo "${VAR}=\"${VALUE}\"" >> "${INI_FILE}"
    fi
}

settings_make_ini_from() {
    local INI_SOURCE="${1}"
    local INI_TARGET="${2}"
    rm ${INI_TARGET} 2> /dev/null || true
    if [ -f ${INI_SOURCE} ] ; then
        cp ${INI_SOURCE} ${INI_TARGET}
    else
        touch ${INI_TARGET}
    fi
}


settings_active_tag() {
    local ACTIVE="${1}"
    if [[ "${ACTIVE}" == "true" ]] ; then
        echo "Enabled. "
    else
        echo "Disabled."
    fi
}

settings_active_action() {
    local ACTIVE="${1}"
    if [[ "${ACTIVE}" != "true" ]] ; then
        echo "Enable"
    else
        echo "Disable"
    fi
}

if [[ "${UPDATE_ALL_SOURCE:-false}" != "true" ]] ; then
    run_update_all
fi
