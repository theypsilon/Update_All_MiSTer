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
BASE_PATH="/media/fat"

ENCC_FORKS="false" # Possible values: "true", "false"

MAIN_UPDATER="true"
MAIN_UPDATER_INI="${EXPORTED_INI_PATH}" # Probably /media/fat/Scripts/update_all.ini

JOTEGO_UPDATER="true"
JOTEGO_UPDATER_INI="${EXPORTED_INI_PATH}" # Probably /media/fat/Scripts/update_all.ini

UNOFFICIAL_UPDATER="false"
UNOFFICIAL_UPDATER_INI="${EXPORTED_INI_PATH}" # Probably /media/fat/Scripts/update_all.ini

LLAPI_UPDATER="false"
LLAPI_UPDATER_INI="${EXPORTED_INI_PATH}" # Probably /media/fat/Scripts/update_all.ini

BIOS_GETTER="true"
BIOS_GETTER_INI="/media/fat/Scripts/update_bios-getter.ini"
BIOS_GETTER_FORCE_FULL_RESYNC="false"

MAME_GETTER="true"
MAME_GETTER_INI="/media/fat/Scripts/update_mame-getter.ini"
MAME_GETTER_FORCE_FULL_RESYNC="false"

HBMAME_GETTER="true"
HBMAME_GETTER_INI="/media/fat/Scripts/update_hbmame-getter.ini"
HBMAME_GETTER_FORCE_FULL_RESYNC="false"

ARCADE_ORGANIZER="true"
ARCADE_ORGANIZER_INI="/media/fat/Scripts/update_arcade-organizer.ini"
ARCADE_ORGANIZER_FORCE_FULL_RESYNC="false"

WAIT_TIME_FOR_READING=4
AUTOREBOOT="true"

# ============ UNRELEASED ============
COUNTDOWN_TIME=0
NAMES_TXT="false"

# ========= CODE STARTS HERE =========
UPDATE_ALL_VERSION="1.1"
UPDATE_ALL_PC_UPDATER="${UPDATE_ALL_PC_UPDATER:-false}"
UPDATE_ALL_OS="${UPDATE_ALL_OS:-MiSTer_Linux}"
ORIGINAL_SCRIPT_PATH="${0}"
INI_PATH="${ORIGINAL_SCRIPT_PATH%.*}.ini"
LOG_FILENAME="$(basename ${EXPORTED_INI_PATH%.*}.log)"
WORK_PATH="/media/fat/Scripts/.update_all"
GLOG_TEMP="/tmp/tmp.global.${LOG_FILENAME}"
GLOG_PATH="${WORK_PATH}/${LOG_FILENAME}"

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
    trap "mv ${GLOG_TEMP} ${GLOG_PATH}" EXIT
}

load_ini_file() {
    local INI_PATH="${1}"

    if [ ! -f ${INI_PATH} ] ; then
        return
    fi

    local TMP=$(mktemp)
    dos2unix < "${INI_PATH}" 2> /dev/null | grep -v "^exit" > ${TMP} || true

    source ${TMP}
    rm -f ${TMP}
}

load_vars_from_ini() {
    local INI_PATH="${1}"

    if [ ! -f ${INI_PATH} ] ; then
        return
    fi

    local TMP=$(mktemp)
    dos2unix < "${INI_PATH}" 2> /dev/null | grep -v "^exit" > ${TMP} || true

    for var in "${@:2}" ; do
        source <(grep ${var} ${TMP})
    done
    rm -f ${TMP}
}

load_single_var_from_ini() {
    local VAR="${1}"
    local INI_PATH="${2}"

    local TMP=$(mktemp)
    dos2unix < "${INI_PATH}" 2> /dev/null | grep -v "^exit" > ${TMP} || true

    declare -n VALUE="${VAR}"
    VALUE=
    source <(grep ${VAR} ${TMP})

    rm -f ${TMP}

    echo "${VALUE}"
}

initialize() {
    initialize_global_log

    echo "Executing 'Update All' script"
    echo "The All-in-One Updater for MiSTer"
    echo "Version ${UPDATE_ALL_VERSION}"

    if [[ "${UPDATE_ALL_PC_UPDATER}" == "true" ]] && [[ "${EXPORTED_INI_PATH}" == "/tmp/update_all.ini" ]] ; then
        EXPORTED_INI_PATH="update_all.ini"
    fi

    echo
    echo "Reading INI file '${EXPORTED_INI_PATH}':"
    if [ -f ${EXPORTED_INI_PATH} ] ; then
        cp ${EXPORTED_INI_PATH} ${INI_PATH} 2> /dev/null || true
        load_ini_file "${INI_PATH}"
        echo "OK."
    else
        echo "Not found."
    fi

    LOG_FILENAME="$(basename ${EXPORTED_INI_PATH%.*}.log)"
    WORK_PATH="/media/fat/Scripts/.update_all"

    if [ ! -d ${WORK_PATH} ] ; then
        mkdir -p ${WORK_PATH}
        MAME_GETTER_FORCE_FULL_RESYNC="true"
        HBMAME_GETTER_FORCE_FULL_RESYNC="true"
        ARCADE_ORGANIZER_FORCE_FULL_RESYNC="true"

        echo
        echo "Creating '${WORK_PATH}' for the first time."
        echo "Performing a full forced update."
    fi

    if [[ "${ALWAYS_ASSUME_NEW_STANDARD_MRA:-false}" == "true" ]] || [[ "${ALWAYS_ASSUME_NEW_ALTERNATIVE_MRA:-false}" == "true" ]] ; then
        MAME_GETTER_FORCE_FULL_RESYNC="true"
        HBMAME_GETTER_FORCE_FULL_RESYNC="true"
        ARCADE_ORGANIZER_FORCE_FULL_RESYNC="true"

        echo
        echo "'ALWAYS_ASSUME_NEW_STANDARD_MRA' and 'ALWAYS_ASSUME_NEW_ALTERNATIVE_MRA' options"
        echo "are deprecated and will be removed in a later version of Update All."
        echo
        echo "Please, change your INI file and use these options accordingly:"
        echo "    MAME_GETTER_FORCE_FULL_RESYNC=\"true\""
        echo "    HBMAME_GETTER_FORCE_FULL_RESYNC=\"true\""
        echo "    ARCADE_ORGANIZER_FORCE_FULL_RESYNC=\"true\""
        sleep ${WAIT_TIME_FOR_READING}
    fi

    if [[ "${UPDATE_ALL_PC_UPDATER}" == "true" ]] ; then
        MAIN_UPDATER_INI="${EXPORTED_INI_PATH}"
        JOTEGO_UPDATER_INI="${EXPORTED_INI_PATH}"
        UNOFFICIAL_UPDATER_INI="${EXPORTED_INI_PATH}"
        LLAPI_UPDATER_INI="${EXPORTED_INI_PATH}"
        MAME_GETTER_INI="${EXPORTED_INI_PATH}"
        HBMAME_GETTER_INI="${EXPORTED_INI_PATH}"
        ARCADE_ORGANIZER_INI="${EXPORTED_INI_PATH}"
        ARCADE_ORGANIZER="false"
        if [[ "${UPDATE_ALL_PC_UPDATER_ENCC_FORKS:-}" == "true" ]] ; then
            ENCC_FORKS="true"
        fi
    fi
}

MAIN_UPDATER_URL="https://raw.githubusercontent.com/MiSTer-devel/Updater_script_MiSTer/master/mister_updater.sh"
DB9_UPDATER_URL="https://raw.githubusercontent.com/theypsilon/Updater_script_MiSTer_DB9/master/mister_updater.sh"
select_main_updater() {
    case "${ENCC_FORKS}" in
        true)
            MAIN_UPDATER_URL="${DB9_UPDATER_URL}"
            ;;
        *)
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

fetch_or_exit() {
    if curl ${@} ; then return ; fi

    echo "There was some network problem."
    echo
    echo "Following file couldn't be downloaded:"
    echo ${@: -1}
    echo
    echo "Please try again later."
    echo
    exit 1
}

UPDATER_RET=0
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

    fetch_or_exit ${CURL_RETRY} ${SSL_SECURITY_OPTION} --fail --location -o ${SCRIPT_PATH} ${SCRIPT_URL}

    sed -i "s%INI_PATH=%INI_PATH=\"${SCRIPT_INI}\" #%g" ${SCRIPT_PATH}
    sed -i 's/${AUTOREBOOT}/false/g' ${SCRIPT_PATH}
    sed -i 's/--max-time 120/--max-time 240/g' ${SCRIPT_PATH}
    if [[ "${UPDATE_ALL_PC_UPDATER}" == "true" ]] ; then
        sed -i 's/\/media\/fat/\.\./g ' ${SCRIPT_PATH}
        sed -i 's/UPDATE_LINUX="true"/UPDATE_LINUX="false"/g' ${SCRIPT_PATH}
    fi
    if [[ "${UPDATE_ALL_OS}" == "WINDOWS" ]] ; then
        sed -i "s/ *60)/77)/g" ${SCRIPT_PATH}
    fi

    set +e
    cat ${SCRIPT_PATH} | bash -
    UPDATER_RET=$?
    set -e

    sleep ${WAIT_TIME_FOR_READING}
}

run_mame_getter_script() {
    local SCRIPT_TITLE="${1}"
    local SCRIPT_READ_INI="${2}"
    local SCRIPT_CONDITION="${3}"
    local SCRIPT_INI="${4}"
    local SCRIPT_URL="${5}"
    local MRA_INPUT="${6}"

    local SCRIPT_FILENAME="${SCRIPT_URL/*\//}"
    local SCRIPT_PATH="/tmp/${SCRIPT_FILENAME%.*}.sh"

    draw_separator

    echo "Downloading the most recent $(basename ${SCRIPT_FILENAME}) script."
    echo " "

    fetch_or_exit ${CURL_RETRY} ${SSL_SECURITY_OPTION} --fail --location -o ${SCRIPT_PATH} ${SCRIPT_URL}
    echo

    local INIFILE_FIXED=$(mktemp)
    if [ -f "${SCRIPT_INI}" ] ; then
        dos2unix < "${SCRIPT_INI}" 2> /dev/null > ${INIFILE_FIXED}
    fi

    ${SCRIPT_READ_INI} ${SCRIPT_PATH} ${INIFILE_FIXED}

    rm ${INIFILE_FIXED}

    if ${SCRIPT_CONDITION} ; then
        echo
        echo "STARTING: ${SCRIPT_TITLE}"
        chmod +x ${SCRIPT_PATH}
        sed -i "s%INIFILE=%INIFILE=\"${SCRIPT_INI}\" #%g" ${SCRIPT_PATH}
        if [[ "${UPDATE_ALL_PC_UPDATER}" == "true" ]] ; then
            sed -i 's/\/media\/fat/\.\./g ' ${SCRIPT_PATH}
        fi
        if [[ "${UPDATE_ALL_OS}" == "WINDOWS" ]] ; then
            sed -i 's/#!\/bin\/bash/#!bash/g ' ${SCRIPT_PATH}
        fi

        set +e
        if [ -s ${MRA_INPUT} ] ; then
            ${SCRIPT_PATH} --input-file ${MRA_INPUT}
        else
            ${SCRIPT_PATH}
        fi
        local SCRIPT_RET=$?
        set -e

        if [ $SCRIPT_RET -ne 0 ]; then
            FAILING_UPDATERS+=("${SCRIPT_TITLE}")
        fi

        rm ${SCRIPT_PATH}
        echo "FINISHED: ${SCRIPT_TITLE}"
        echo
        sleep ${WAIT_TIME_FOR_READING}
    else
        echo "Skipping ${SCRIPT_TITLE}..."
    fi
}

MAME_GETTER_ROMDIR=
MAME_GETTER_MRADIR=
read_ini_mame_getter() {
    local SCRIPT_PATH="${1}"
    local SCRIPT_INI="${2}"

    if [ -s ${SCRIPT_PATH} ] ; then
        MAME_GETTER_ROMDIR=$(grep "^[^#;]" "${SCRIPT_PATH}" | grep "ROMMAME=" | head -n 1 | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^"//' -e 's/"$//')
        MAME_GETTER_MRADIR=$(grep "^[^#;]" "${SCRIPT_PATH}" | grep "MRADIR=" | head -n 1 | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^"//' -e 's/"$//')
    fi

    if [ ! -s ${SCRIPT_INI} ] ; then
        return
    fi

    if [ `grep -c "ROMDIR=" "${SCRIPT_INI}"` -gt 0 ]
    then
        MAME_GETTER_ROMDIR=`grep "ROMDIR" "${SCRIPT_INI}" | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^"//' -e 's/"$//'`
    fi 2>/dev/null

    if [ `grep -c "ROMMAME=" "${SCRIPT_INI}"` -gt 0 ]
    then
        MAME_GETTER_ROMDIR=`grep "ROMMAME" "${SCRIPT_INI}" | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^"//' -e 's/"$//'`
    fi 2>/dev/null

    if [ `grep -c "MRADIR=" "${SCRIPT_INI}"` -gt 0 ]
    then
        MAME_GETTER_MRADIR=`grep "MRADIR=" "${SCRIPT_INI}" | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^"//' -e 's/"$//'`
    fi 2>/dev/null
}

should_run_mame_getter() {
    [[ "${MAME_GETTER_FORCE_FULL_RESYNC}" == "true" ]] || \
    [ -s ${UPDATED_MAME_MRAS} ] || \
    [ ! -d ${MAME_GETTER_ROMDIR} ] || \
    [ -z "$(ls -A ${MAME_GETTER_ROMDIR})" ]
}

HBMAME_GETTER_ROMDIR=
HBMAME_GETTER_MRADIR=
read_ini_hbmame_getter() {
    local SCRIPT_PATH="${1}"
    local SCRIPT_INI="${2}"

    if [ -s ${SCRIPT_PATH} ] ; then
        HBMAME_GETTER_ROMDIR=$(grep "^[^#;]" "${SCRIPT_PATH}" | grep "ROMHBMAME=" | head -n 1 | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^"//' -e 's/"$//')
        HBMAME_GETTER_MRADIR=$(grep "^[^#;]" "${SCRIPT_PATH}" | grep "MRADIR=" | head -n 1 | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^"//' -e 's/"$//')
    fi

    if [ ! -s ${SCRIPT_INI} ] ; then
        return
    fi

    if [ `grep -c "ROMDIR=" "${SCRIPT_INI}"` -gt 0 ]
    then
        HBMAME_GETTER_ROMDIR=`grep "ROMDIR" "${SCRIPT_INI}" | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^"//' -e 's/"$//'`
    fi 2>/dev/null

    if [ `grep -c "ROMHBMAME=" "${SCRIPT_INI}"` -gt 0 ]
    then
        HBMAME_GETTER_ROMDIR=`grep "ROMHBMAME" "${SCRIPT_INI}" | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^"//' -e 's/"$//'`
    fi 2>/dev/null

    if [ `grep -c "MRADIR=" "${SCRIPT_INI}"` -gt 0 ]
    then
        HBMAME_GETTER_MRADIR=`grep "MRADIR=" "${SCRIPT_INI}" | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^"//' -e 's/"$//'`
    fi 2>/dev/null
}

should_run_hbmame_getter() {
    [[ "${HBMAME_GETTER_FORCE_FULL_RESYNC}" == "true" ]] || \
    [ -s ${UPDATED_HBMAME_MRAS} ] || \
    [ ! -d ${HBMAME_GETTER_ROMDIR} ] || \
    [ -z "$(ls -A ${HBMAME_GETTER_ROMDIR})" ]
}

ARCADE_ORGANIZER_ORGDIR=
ARCADE_ORGANIZER_MRADIR=
ARCADE_ORGANIZER_SKIPALTS=
read_ini_arcade_organizer() {
    local SCRIPT_PATH="${1}"
    local SCRIPT_INI="${2}"

    if [ -s ${SCRIPT_PATH} ] ; then
        ARCADE_ORGANIZER_ORGDIR=$(grep "^[^#;]" "${SCRIPT_PATH}" | grep "ORGDIR" | head -n 1 | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^ *"//' -e 's/" *$//')
        ARCADE_ORGANIZER_MRADIR=$(grep "^[^#;]" "${SCRIPT_PATH}" | grep "MRADIR=" | head -n 1 | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^ *"//' -e 's/" *$//')
        ARCADE_ORGANIZER_SKIPALTS=$(grep "^[^#;]" "${SCRIPT_PATH}" | grep "SKIPALTS=" | head -n 1 | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^ *"//' -e 's/" *$//')
    fi

    if [ ! -s ${SCRIPT_INI} ] ; then
        return
    fi

    if [ `grep -c "ORGDIR=" "${SCRIPT_INI}"` -gt 0 ]
    then
        ARCADE_ORGANIZER_ORGDIR=`grep "ORGDIR" "${SCRIPT_INI}" | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^ *"//' -e 's/" *$//'`
    fi 2>/dev/null 

    if [ `grep -c "MRADIR=" "${SCRIPT_INI}"` -gt 0 ]
    then
        ARCADE_ORGANIZER_MRADIR=`grep "MRADIR=" "${SCRIPT_INI}" | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^ *"//' -e 's/" *$//'`
    fi 2>/dev/null

    if [ `grep -c "SKIPALTS=" "${SCRIPT_INI}"` -gt 0 ]
    then
        ARCADE_ORGANIZER_SKIPALTS=`grep "SKIPALTS=" "${SCRIPT_INI}" | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^ *"//' -e 's/" *$//'`
    fi 2>/dev/null

    if [[ "${ARCADE_ORGANIZER_SKIPALTS}" == "true" ]] && [ -s ${UPDATED_MRAS} ] ; then
        sed -i "/\/_alternatives\//d ; /^ *$/d" ${UPDATED_MRAS}
    fi

    if [ -d "${ARCADE_ORGANIZER_ORGDIR}" ] ; then
        find "${ARCADE_ORGANIZER_ORGDIR}/" -xtype l -exec rm {} \; || true
    fi
}

should_run_arcade_organizer() {
    [[ "${ARCADE_ORGANIZER_FORCE_FULL_RESYNC}" == "true" ]] || \
    [ -s ${UPDATED_MRAS} ] || \
    [ ! -d ${ARCADE_ORGANIZER_ORGDIR} ] || \
    [ -z "$(ls -A ${ARCADE_ORGANIZER_ORGDIR})" ]
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
        if [ -d ${dir} ] && [ -z "$(ls -A ${dir})" ] ; then
            rm -rf "${dir}"
            DELETED_EMPTY_DIRS+=(${dir})
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

UPDATED_MRAS=".none"
UPDATED_MAME_MRAS=".none"
UPDATED_HBMAME_MRAS=".none"
LAST_MRA_PROCESSING_PATH=
find_mras() {
    if [[ "${UPDATE_ALL_OS}" == "WINDOWS" ]] ; then
        touch .none
        return
    fi

    draw_separator

    UPDATED_MRAS=$(mktemp)
    UPDATED_MAME_MRAS=$(mktemp)
    UPDATED_HBMAME_MRAS=$(mktemp)

    LAST_MRA_PROCESSING_PATH="${WORK_PATH}/$(basename ${EXPORTED_INI_PATH%.*}.last_mra_processing)"

    local LAST_MRA_PROCESSING_TIME=$(date --date='@-86400')
    if [ -f ${LAST_MRA_PROCESSING_PATH} ] ; then
        LAST_MRA_PROCESSING_TIME=$(cat "${LAST_MRA_PROCESSING_PATH}" | sed '2q;d')
    fi

    for path in $(arcade_paths ${MAIN_UPDATER_INI} ${JOTEGO_UPDATER_INI} ${UNOFFICIAL_UPDATER_INI}) ; do
        find ${path}/ -maxdepth 1 -type f -name "*.mra" -newerct "${LAST_MRA_PROCESSING_TIME}" >> ${UPDATED_MRAS}
        if [ -d ${path}/_alternatives ] ; then
            find ${path}/_alternatives/  -type f -name "*.mra" -newerct "${LAST_MRA_PROCESSING_TIME}" >> ${UPDATED_MRAS}
        fi
    done

    if [ -s ${UPDATED_MRAS} ] ; then
        cat ${UPDATED_MRAS} | grep -ve 'HBMame\.mra$' > ${UPDATED_MAME_MRAS} || true
        cat ${UPDATED_MRAS} | grep -e 'HBMame\.mra$' > ${UPDATED_HBMAME_MRAS} || true
    fi

    local UPDATED_MRAS_WCL=$(wc -l ${UPDATED_MRAS} | awk '{print $1}')
    echo "Found ${UPDATED_MRAS_WCL} new MRAs."
    if [ ${UPDATED_MRAS_WCL} -ge 1 ] ; then
        echo "$(wc -l ${UPDATED_MAME_MRAS} | awk '{print $1}') use mame."
        echo "$(wc -l ${UPDATED_HBMAME_MRAS} | awk '{print $1}') use hbmame."
    fi
    sleep ${WAIT_TIME_FOR_READING}
    echo

    if [[ "${MAME_GETTER_FORCE_FULL_RESYNC}" == "true" ]] ; then
        rm ${UPDATED_MAME_MRAS}
    fi
    if [[ "${HBMAME_GETTER_FORCE_FULL_RESYNC}" == "true" ]] ; then
        rm ${UPDATED_HBMAME_MRAS}
    fi
    if [[ "${ARCADE_ORGANIZER_FORCE_FULL_RESYNC}" == "true" ]] ; then
        rm ${UPDATED_MRAS}
    fi
}

sequence() {
    echo "Sequence:"
    if [[ "${MAIN_UPDATER}" == "true" ]] ; then
        if [[ "${ENCC_FORKS}" == "true" ]] ; then
            echo "- Main Updater: DB9 / SNAC8"
        else
            echo "- Main Updater: MiSTer-devel"
        fi
    fi
    if [[ "${JOTEGO_UPDATER}" == "true" ]] ; then
        echo "- Jotego Updater"
    fi
    if [[ "${UNOFFICIAL_UPDATER}" == "true" ]] ; then
        echo "- Unofficial Updater"
    fi
    if [[ "${LLAPI_UPDATER}" == "true" ]] ; then
        echo "- LLAPI Updater"
    fi
    if [[ "${NAMES_TXT}" == "true" ]] ; then
        echo "- names.txt (EARLY ALPHA, DON'T USE!)"
    fi
    if [[ "${MAME_GETTER}" == "true" ]] ; then
        echo "- MAME Getter (forced: ${MAME_GETTER_FORCE_FULL_RESYNC})"
    fi
    if [[ "${HBMAME_GETTER}" == "true" ]] ; then
        echo "- HBMAME Getter (forced: ${HBMAME_GETTER_FORCE_FULL_RESYNC})"
    fi
    if [[ "${ARCADE_ORGANIZER}" == "true" ]] ; then
        echo "- Arcade Organizer (forced: ${ARCADE_ORGANIZER_FORCE_FULL_RESYNC})"
    fi
    if [[ "${UPDATE_ALL_PC_UPDATER}" == "true" ]] && [ ! -f ../Scripts/update_all.sh ] ; then
        echo "- update_all.sh Script"
    fi
}

countdown() {
    local BOLD_IN="$(tput bold)"
    local BOLD_OUT="$(tput sgr0)"
    echo
    echo " ${BOLD_IN}*${BOLD_OUT}Press <${BOLD_IN}UP${BOLD_OUT}>, To enter the SETTINGS screen."
    echo -n " ${BOLD_IN}*${BOLD_OUT}Press <${BOLD_IN}DOWN${BOLD_OUT}>, To continue now."
    local COUNTDOWN_SELECTION="continue"
    set +e
    echo -e '\e[3A\e[K'
    for (( i=0; i <= (( COUNTDOWN_TIME )); i++)); do
        local SECONDS=$(( COUNTDOWN_TIME - i ))
        if (( SECONDS < 10 )) ; then
            SECONDS=" ${SECONDS}"
        fi
        printf "\rStarting in ${SECONDS} seconds."
        for (( j=0; j < i; j++)); do
            printf "."
        done
        read -r -s -N 1 -t 1 key
        if [ "$key" = "A" ]; then
                COUNTDOWN_SELECTION="menu"
                break
        fi
        if [ "$key" = "B" ]; then
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

    if [ ${COUNTDOWN_TIME} -gt 0 ] ; then
        if [[ -t 0 || -t 1 || -t 2 ]] ; then
            disable_global_log
            countdown
            enable_global_log
        else
            echo "Not displaying countdown because fb_terminal=0 (on MiSTer.ini)"
            sleep ${WAIT_TIME_FOR_READING}
        fi
        echo
    fi

    echo "Start time: $(date)"

    local REBOOT_NEEDED="false"
    FAILING_UPDATERS=()

    if [[ "${MAIN_UPDATER}" == "true" ]] ; then
        select_main_updater
        run_updater_script ${MAIN_UPDATER_URL} ${MAIN_UPDATER_INI}
        if [ $UPDATER_RET -ne 0 ]; then
            FAILING_UPDATERS+=("/media/fat/Scripts/.mister_updater/${LOG_FILENAME}")
        fi
        sleep 1
        if [[ "${UPDATE_ALL_PC_UPDATER}" != "true" ]] && tail -n 30 ${GLOG_TEMP} | grep -q "You should reboot" ; then
            REBOOT_NEEDED="true"
        fi
    fi

    if [[ "${JOTEGO_UPDATER}" == "true" ]] ; then
        run_updater_script https://raw.githubusercontent.com/jotego/Updater_script_MiSTer/master/mister_updater.sh ${JOTEGO_UPDATER_INI}
        if [ $UPDATER_RET -ne 0 ]; then
            FAILING_UPDATERS+=("/media/fat/Scripts/.mister_updater_jt/${LOG_FILENAME}")
        fi
    fi

    if [[ "${UNOFFICIAL_UPDATER}" == "true" ]] ; then
        run_updater_script https://raw.githubusercontent.com/theypsilon/Updater_script_MiSTer_Unofficial/master/mister_updater.sh ${UNOFFICIAL_UPDATER_INI}
        if [ $UPDATER_RET -ne 0 ]; then
            FAILING_UPDATERS+=("/media/fat/Scripts/.mister_updater_unofficials/${LOG_FILENAME}")
        fi
    fi

    if [[ "${LLAPI_UPDATER}" == "true" ]] ; then
        run_updater_script https://raw.githubusercontent.com/MiSTer-LLAPI/Updater_script_MiSTer/master/llapi_updater.sh ${LLAPI_UPDATER_INI}
        if [ $UPDATER_RET -ne 0 ]; then
            FAILING_UPDATERS+=("LLAPI")
        fi
    fi

    if [[ "${NAMES_TXT}" == "true" ]] ; then
        draw_separator

        echo "Checking names.txt"
        echo "WARNING! This is a WIP feature that can be removed at any time."
        echo "         DON'T USE IT!"
        echo
        rm /tmp/ua_names.txt 2> /dev/null || true
        fetch_or_exit ${CURL_RETRY} ${SSL_SECURITY_OPTION} --fail --location -o /tmp/ua_names.txt https://raw.githubusercontent.com/ThreepwoodLeBrush/Names_MiSTer/master/names_CHAR28_Manufacturer_US.txt
        if ! diff /tmp/ua_names.txt "${BASE_PATH}/names.txt" > /dev/null 2>&1 ; then
            cp /tmp/ua_names.txt "${BASE_PATH}/names.txt"
            echo "New names.txt installed."
        else
            echo "Skipping names.txt..."
        fi
    fi

    local NEW_MRA_TIME=$(date)

    find_mras

    if [[ "${MAME_GETTER}" == "true" ]] ; then
        run_mame_getter_script "MAME-GETTER" read_ini_mame_getter should_run_mame_getter ${MAME_GETTER_INI} \
        https://raw.githubusercontent.com/MAME-GETTER/MiSTer_MAME_SCRIPTS/master/mame-merged-set-getter.sh "${UPDATED_MAME_MRAS}"
    fi

    if [[ "${HBMAME_GETTER}" == "true" ]] ; then
        run_mame_getter_script "HBMAME-GETTER" read_ini_hbmame_getter should_run_hbmame_getter ${HBMAME_GETTER_INI} \
        https://raw.githubusercontent.com/MAME-GETTER/MiSTer_MAME_SCRIPTS/master/hbmame-merged-set-getter.sh "${UPDATED_HBMAME_MRAS}"
    fi

    if [[ "${ARCADE_ORGANIZER}" == "true" ]] ; then
        run_mame_getter_script "_ARCADE-ORGANIZER" read_ini_arcade_organizer should_run_arcade_organizer ${ARCADE_ORGANIZER_INI} \
        https://raw.githubusercontent.com/MAME-GETTER/_arcade-organizer/master/_arcade-organizer.sh "${UPDATED_MRAS}"
    fi

    rm ${UPDATED_MRAS} 2> /dev/null || true
    rm ${UPDATED_MAME_MRAS} 2> /dev/null || true
    rm ${UPDATED_HBMAME_MRAS} 2> /dev/null || true

    if [[ "${UPDATE_ALL_PC_UPDATER}" == "true" ]] && [ ! -f ../Scripts/update_all.sh ] ; then
        draw_separator
        echo "Installing update_all.sh in MiSTer /Scripts directory."
        mkdir -p ../Scripts
        fetch_or_exit ${CURL_RETRY} ${SSL_SECURITY_OPTION} --fail --location -o ../Scripts/update_all.sh https://raw.githubusercontent.com/theypsilon/Update_All_MiSTer/master/update_all.sh

        if [ -f update_all.ini ] ; then
            echo "Installing update_all.ini too."
            cp update_all.ini ../Scripts/update_all.ini
        fi
    fi

    draw_separator

    delete_if_empty \
        "${BASE_PATH}/games/mame" \
        "${BASE_PATH}/games/hbmame" \
        "${BASE_PATH}/_Arcade/mame" \
        "${BASE_PATH}/_Arcade/hbmame" \
        "${BASE_PATH}/_Arcade/mra_backup"

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

    echo
    echo "End time: $(date)"
    echo

    if [[ "${UPDATE_ALL_OS}" != "WINDOWS" ]] ; then
        echo "Full log for more details: ${GLOG_PATH}"
        echo
    fi

    if [[ "${EXIT_CODE}" == "0" ]] && [[ "${LAST_MRA_PROCESSING_PATH}" != "" ]]; then
        echo "${UPDATE_ALL_VERSION}" > "${LAST_MRA_PROCESSING_PATH}"
        echo "${NEW_MRA_TIME}" >> "${LAST_MRA_PROCESSING_PATH}"
    fi

    if [[ "${REBOOT_NEEDED}" == "true" ]] ; then
        REBOOT_PAUSE=$((WAIT_TIME_FOR_READING * 2))
        if [[ "${AUTOREBOOT}" == "true" && "${REBOOT_PAUSE}" -ge 0 ]] ; then
            echo "Rebooting in ${REBOOT_PAUSE} seconds"
            sleep "${REBOOT_PAUSE}"
            reboot now
        else
            echo "You should reboot"
            echo
        fi
    fi

    exit ${EXIT_CODE:-1}
}

SETTINGS_TMP_UPDATE_ALL_INI="/tmp/ua.$(basename ${EXPORTED_INI_PATH})"
SETTINGS_TMP_MAIN_UPDATER_INI="/tmp/ua.update.ini"
SETTINGS_TMP_JOTEGO_UPDATER_INI="/tmp/ua.update_jtcores.ini"
SETTINGS_TMP_UNOFFICIAL_UPDATER_INI="/tmp/ua.update_unofficials.ini"
SETTINGS_TMP_LLAPI_UPDATER_INI="/tmp/ua.update_llapi.ini"
SETTINGS_TMP_MAME_GETTER_INI="/tmp/ua.mame_getter.ini"
SETTINGS_TMP_HBMAME_GETTER_INI="/tmp/ua.hbmame_getter.ini"
SETTINGS_TMP_ARCADE_ORGANIZER_INI="/tmp/ua.arcade_organizer.ini"

SETTINGS_TMP_BREAK="/tmp/ua_break"
SETTINGS_TMP_CONTINUE="/tmp/ua_continue"

declare -A SELECTED_INI_FILES
settings_menu_update_all() {
    rm "${SETTINGS_TMP_BREAK}" 2> /dev/null || true
    rm "${SETTINGS_TMP_CONTINUE}" 2> /dev/null || true

    SELECTED_INI_FILES=()
    SELECTED_INI_FILES["$(basename ${EXPORTED_INI_PATH})"]="${SETTINGS_TMP_UPDATE_ALL_INI}"
    SELECTED_INI_FILES["update.ini"]="${SETTINGS_TMP_MAIN_UPDATER_INI}"
    SELECTED_INI_FILES["update_jtcores.ini"]="${SETTINGS_TMP_JOTEGO_UPDATER_INI}"
    SELECTED_INI_FILES["update_unofficials.ini"]="${SETTINGS_TMP_UNOFFICIAL_UPDATER_INI}"
    SELECTED_INI_FILES["update_llapi.ini"]="${SETTINGS_TMP_LLAPI_UPDATER_INI}"
    SELECTED_INI_FILES["update_mame-getter.ini"]="${SETTINGS_TMP_MAME_GETTER_INI}"
    SELECTED_INI_FILES["update_hbmame-getter.ini"]="${SETTINGS_TMP_HBMAME_GETTER_INI}"
    SELECTED_INI_FILES["update_arcade-organizer.ini"]="${SETTINGS_TMP_ARCADE_ORGANIZER_INI}"

    for key in ${!SELECTED_INI_FILES[@]} ; do
        local value="${SELECTED_INI_FILES[${key}]}"
        settings_make_ini_from "${key}" "${value}"
    done

    local TMP=$(mktemp)
    while true ; do
        (
            load_ini_file "${SETTINGS_TMP_UPDATE_ALL_INI}"

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 Main Updater"
            fi

            set +e
            dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Abort" --ok-label "Select" --title "Update All Settings" \
                --menu "Settings loaded from '$(basename ${EXPORTED_INI_PATH})'\n\n" 16 75 25 \
                "1 Main Updater"  "$(settings_active_tag ${MAIN_UPDATER}) Main MiSTer cores and resources" \
                "2 Jotego Updater" "$(settings_active_tag ${JOTEGO_UPDATER}) Cores made by Jotego" \
                "3 Unofficial Updater"  "$(settings_active_tag ${UNOFFICIAL_UPDATER}) Some unofficial cores" \
                "4 LLAPI Updater" "$(settings_active_tag ${LLAPI_UPDATER}) Forks adapted to LLAPI" \
                "5 MAME Getter" "$(settings_active_tag ${MAME_GETTER}) MAME ROMs for arcades" \
                "6 HBMAME Getter" "$(settings_active_tag ${HBMAME_GETTER}) HBMAME ROMs for arcades" \
                "7 Arcade Organizer" "$(settings_active_tag ${ARCADE_ORGANIZER}) Creates folder for easy navigation" \
                "SAVE" "Writes all changes to the INI file/s" \
                "EXIT and RUN UPDATE ALL" "" 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e
            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi
            case "${DEFAULT_SELECTION}" in
                "1 Main Updater") settings_menu_main_updater ;;
                "2 Jotego Updater") settings_menu_jotego_updater ;;
                "3 Unofficial Updater") settings_menu_unofficial_updater ;;
                "4 LLAPI Updater") settings_menu_llapi_updater ;;
                "5 MAME Getter") settings_menu_mame_getter ;;
                "6 HBMAME Getter") settings_menu_hbmame_getter ;;
                "7 Arcade Organizer") settings_menu_arcade_organizer ;;
                "SAVE") settings_menu_save ;;
                "EXIT and RUN UPDATE ALL") settings_menu_exit_and_run ;;
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

    if [ -f ${INI_PATH} ] ; then
        load_ini_file "${INI_PATH}"
    fi
}

### SETTINGS OPTIONS: MAIN UPDATER ##
SETTINGS_OPTIONS_MAIN_UPDATER=("true" "false")
SETTINGS_OPTIONS_MAIN_UPDATER_INI=("$(basename ${EXPORTED_INI_PATH})" "update.ini")
SETTINGS_OPTIONS_ENCC_FORKS=("false" "true")
SETTINGS_OPTIONS_DOWNLOAD_NEW_CORES=("true" "false")
SETTINGS_OPTIONS_UPDATE_LINUX=("true" "false")
SETTINGS_OPTIONS_UPDATE_CHEATS=("once" "true" "false")
SETTINGS_OPTIONS_MAME_ALT_ROMS=("true" "false")
SETTINGS_OPTIONS_AUTOREBOOT=("true" "false")

settings_menu_main_updater() {
    local TMP=$(mktemp)
    while true ; do
        (
            local MAIN_UPDATER="${SETTINGS_OPTIONS_MAIN_UPDATER[0]}"
            local MAIN_UPDATER_INI="${SETTINGS_OPTIONS_MAIN_UPDATER_INI[0]}"
            local ENCC_FORKS="${SETTINGS_OPTIONS_ENCC_FORKS[0]}"
            local DOWNLOAD_NEW_CORES="${SETTINGS_OPTIONS_DOWNLOAD_NEW_CORES[0]}"
            local UPDATE_CHEATS="${SETTINGS_OPTIONS_UPDATE_CHEATS[0]}"
            local UPDATE_LINUX="${SETTINGS_OPTIONS_UPDATE_LINUX[0]}"
            local MAME_ALT_ROMS="${SETTINGS_OPTIONS_MAME_ALT_ROMS[0]}"
            local AUTOREBOOT="${SETTINGS_OPTIONS_AUTOREBOOT[0]}"

            load_vars_from_ini "${SETTINGS_TMP_UPDATE_ALL_INI}" "MAIN_UPDATER" "MAIN_UPDATER_INI" "ENCC_FORKS"
            load_ini_file "${SELECTED_INI_FILES[${MAIN_UPDATER_INI}]}"

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 $(settings_active_action ${MAIN_UPDATER})"
            fi

            local ACTIVATE="1 $(settings_active_action ${MAIN_UPDATER})"

            set +e
            dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --title "Main Updater Settings" \
                --menu "$(settings_menu_descr_text $(basename ${EXPORTED_INI_PATH}) ${MAIN_UPDATER_INI})" 16 75 25 \
                "${ACTIVATE}" "Activated: ${MAIN_UPDATER}" \
                "2 Cores versions" "$([[ ${ENCC_FORKS} == 'true' ]] && echo 'DB9 / SNAC8 forks with ENCC' || echo 'Official Cores from MiSTer-devel')" \
                "3 INI file"  "$(basename ${MAIN_UPDATER_INI})" \
                "4 Install new Cores" "${DOWNLOAD_NEW_CORES}" \
                "5 Install MRA-Alternatives" "${MAME_ALT_ROMS}" \
                "6 Install Cheats" "${UPDATE_CHEATS}" \
                "7 Install new Linux versions" "${UPDATE_LINUX}" \
                "8 Autoreboot (if needed)" "${AUTOREBOOT}" \
                "BACK"  "" 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "${ACTIVATE}") settings_change_var "MAIN_UPDATER" "${SETTINGS_TMP_UPDATE_ALL_INI}" ;;
                "2 Cores versions") settings_change_var "ENCC_FORKS" "${SETTINGS_TMP_UPDATE_ALL_INI}" ;;
                "3 INI file") settings_change_var "MAIN_UPDATER_INI" "${SETTINGS_TMP_UPDATE_ALL_INI}" ;;
                "4 Install new Cores") settings_change_var "DOWNLOAD_NEW_CORES" "${SELECTED_INI_FILES[${MAIN_UPDATER_INI}]}" ;;
                "5 Install MRA-Alternatives") settings_change_var "MAME_ALT_ROMS" "${SELECTED_INI_FILES[${MAIN_UPDATER_INI}]}" ;;
                "6 Install Cheats") settings_change_var "UPDATE_CHEATS" "${SELECTED_INI_FILES[${MAIN_UPDATER_INI}]}" ;;
                "7 Install new Linux versions") settings_change_var "UPDATE_LINUX" "${SELECTED_INI_FILES[${MAIN_UPDATER_INI}]}" ;;
                "8 Autoreboot (if needed)") settings_change_var "AUTOREBOOT" "${SELECTED_INI_FILES[${MAIN_UPDATER_INI}]}" ;;
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

### SETTINGS OPTIONS: JOTEGO UPDATER ##
SETTINGS_OPTIONS_JOTEGO_UPDATER=("true" "false")
SETTINGS_OPTIONS_JOTEGO_UPDATER_INI=("$(basename ${EXPORTED_INI_PATH})" "update_jtcores.ini")
SETTINGS_OPTIONS_DOWNLOAD_NEW_CORES=("true" "false")
SETTINGS_OPTIONS_MAME_ALT_ROMS=("true" "false")

settings_menu_jotego_updater() {
    local TMP=$(mktemp)
    while true ; do
        (
            local JOTEGO_UPDATER="${SETTINGS_OPTIONS_JOTEGO_UPDATER[0]}"
            local JOTEGO_UPDATER_INI="${SETTINGS_OPTIONS_JOTEGO_UPDATER_INI[0]}"
            local DOWNLOAD_NEW_CORES="${SETTINGS_OPTIONS_DOWNLOAD_NEW_CORES[0]}"
            local MAME_ALT_ROMS="${SETTINGS_OPTIONS_MAME_ALT_ROMS[0]}"

            load_vars_from_ini "${SETTINGS_TMP_UPDATE_ALL_INI}" "JOTEGO_UPDATER" "JOTEGO_UPDATER_INI"
            load_ini_file "${SELECTED_INI_FILES[${JOTEGO_UPDATER_INI}]}"

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 $(settings_active_action ${JOTEGO_UPDATER})"
            fi

            local ACTIVATE="1 $(settings_active_action ${JOTEGO_UPDATER})"

            set +e
            dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --title "Jotego Updater Settings" \
                --menu "$(settings_menu_descr_text $(basename ${EXPORTED_INI_PATH}) ${JOTEGO_UPDATER_INI})" 12 75 25 \
                "${ACTIVATE}" "Activated: ${JOTEGO_UPDATER}" \
                "2 INI file"  "$(basename ${JOTEGO_UPDATER_INI})" \
                "3 Install new Cores" "${DOWNLOAD_NEW_CORES}" \
                "4 Install MRA-Alternatives" "${MAME_ALT_ROMS}" \
                "BACK"  "" 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "${ACTIVATE}") settings_change_var "JOTEGO_UPDATER" "${SETTINGS_TMP_UPDATE_ALL_INI}" ;;
                "2 INI file") settings_change_var "JOTEGO_UPDATER_INI" "${SETTINGS_TMP_UPDATE_ALL_INI}" ;;
                "3 Install new Cores") settings_change_var "DOWNLOAD_NEW_CORES" "${SELECTED_INI_FILES[${JOTEGO_UPDATER_INI}]}" ;;
                "4 Install MRA-Alternatives") settings_change_var "MAME_ALT_ROMS" "${SELECTED_INI_FILES[${JOTEGO_UPDATER_INI}]}" ;;
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

### SETTINGS OPTIONS: UNOFFICIAL UPDATER ##
SETTINGS_OPTIONS_UNOFFICIAL_UPDATER=("false" "true")
SETTINGS_OPTIONS_UNOFFICIAL_UPDATER_INI=("$(basename ${EXPORTED_INI_PATH})" "update_unofficials.ini")
SETTINGS_OPTIONS_DOWNLOAD_NEW_CORES=("true" "false")
SETTINGS_OPTIONS_MAME_ALT_ROMS=("true" "false")

settings_menu_unofficial_updater() {
    local TMP=$(mktemp)
    while true ; do
        (
            local UNOFFICIAL_UPDATER="${SETTINGS_OPTIONS_UNOFFICIAL_UPDATER[0]}"
            local UNOFFICIAL_UPDATER_INI="${SETTINGS_OPTIONS_UNOFFICIAL_UPDATER_INI[0]}"
            local DOWNLOAD_NEW_CORES="${SETTINGS_OPTIONS_DOWNLOAD_NEW_CORES[0]}"
            local MAME_ALT_ROMS="${SETTINGS_OPTIONS_MAME_ALT_ROMS[0]}"

            load_vars_from_ini "${SETTINGS_TMP_UPDATE_ALL_INI}" "UNOFFICIAL_UPDATER" "UNOFFICIAL_UPDATER_INI"
            load_ini_file "${SELECTED_INI_FILES[${UNOFFICIAL_UPDATER_INI}]}"

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 $(settings_active_action ${UNOFFICIAL_UPDATER})"
            fi

            local ACTIVATE="1 $(settings_active_action ${UNOFFICIAL_UPDATER})"

            set +e
            dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --title "Unofficial Updater Settings" \
                --menu "$(settings_menu_descr_text $(basename ${EXPORTED_INI_PATH}) ${UNOFFICIAL_UPDATER_INI})" 12 75 25 \
                "${ACTIVATE}" "Activated: ${UNOFFICIAL_UPDATER}" \
                "2 INI file"  "$(basename ${UNOFFICIAL_UPDATER_INI})" \
                "3 Install new Cores" "${DOWNLOAD_NEW_CORES}" \
                "4 Install MRA-Alternatives" "${MAME_ALT_ROMS}" \
                "BACK"  "" 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "${ACTIVATE}") settings_change_var "UNOFFICIAL_UPDATER" "${SETTINGS_TMP_UPDATE_ALL_INI}" ;;
                "2 INI file") settings_change_var "UNOFFICIAL_UPDATER_INI" "${SETTINGS_TMP_UPDATE_ALL_INI}" ;;
                "3 Install new Cores") settings_change_var "DOWNLOAD_NEW_CORES" "${SELECTED_INI_FILES[${UNOFFICIAL_UPDATER_INI}]}" ;;
                "4 Install MRA-Alternatives") settings_change_var "MAME_ALT_ROMS" "${SELECTED_INI_FILES[${UNOFFICIAL_UPDATER_INI}]}" ;;
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

### SETTINGS OPTIONS: LLAPI UPDATER ##
SETTINGS_OPTIONS_LLAPI_UPDATER=("false" "true")
SETTINGS_OPTIONS_LLAPI_UPDATER_INI=("$(basename ${EXPORTED_INI_PATH})" "update_llapi.ini")
SETTINGS_OPTIONS_DOWNLOAD_NEW_CORES=("true" "false")

settings_menu_llapi_updater() {
    local TMP=$(mktemp)
    while true ; do
        (
            local LLAPI_UPDATER="${SETTINGS_OPTIONS_LLAPI_UPDATER[0]}"
            local LLAPI_UPDATER_INI="${SETTINGS_OPTIONS_LLAPI_UPDATER_INI[0]}"
            local DOWNLOAD_NEW_CORES="${SETTINGS_OPTIONS_DOWNLOAD_NEW_CORES[0]}"

            load_vars_from_ini "${SETTINGS_TMP_UPDATE_ALL_INI}" "LLAPI_UPDATER" "LLAPI_UPDATER_INI"
            load_ini_file "${SELECTED_INI_FILES[${LLAPI_UPDATER_INI}]}"

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 $(settings_active_action ${LLAPI_UPDATER})"
            fi

            local ACTIVATE="1 $(settings_active_action ${LLAPI_UPDATER})"

            set +e
            dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --title "LLAPI Updater Settings" \
                --menu "$(settings_menu_descr_text $(basename ${EXPORTED_INI_PATH}) ${LLAPI_UPDATER_INI})" 11 75 25 \
                "${ACTIVATE}" "Activated: ${LLAPI_UPDATER}" \
                "2 INI file"  "$(basename ${LLAPI_UPDATER_INI})" \
                "3 Install new Cores" "${DOWNLOAD_NEW_CORES}" \
                "BACK"  "" 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi
            DEFAULT_SELECTION="$(cat ${TMP})"
            case "${DEFAULT_SELECTION}" in
                "${ACTIVATE}") settings_change_var "LLAPI_UPDATER" "${SETTINGS_TMP_UPDATE_ALL_INI}" ;;
                "2 INI file") settings_change_var "LLAPI_UPDATER_INI" "${SETTINGS_TMP_UPDATE_ALL_INI}" ;;
                "3 Install new Cores") settings_change_var "DOWNLOAD_NEW_CORES" "${SELECTED_INI_FILES[${LLAPI_UPDATER_INI}]}" ;;
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

### SETTINGS OPTIONS: MAME-GETTER ##
SETTINGS_OPTIONS_MAME_GETTER=("true" "false")
SETTINGS_OPTIONS_MAME_GETTER_INI=("update_mame-getter.ini" "$(basename ${EXPORTED_INI_PATH})")
SETTINGS_OPTIONS_ROMMAME=("games/mame" "_Arcade/mame")

settings_menu_mame_getter() {
    local TMP=$(mktemp)
    while true ; do
        (
            local MAME_GETTER="${SETTINGS_OPTIONS_MAME_GETTER[0]}"
            local MAME_GETTER_INI="${SETTINGS_OPTIONS_MAME_GETTER_INI[0]}"
            local ROMMAME="${SETTINGS_OPTIONS_ROMMAME[0]}"

            load_vars_from_ini "${SETTINGS_TMP_UPDATE_ALL_INI}" "MAME_GETTER" "MAME_GETTER_INI"
            load_ini_file "${SELECTED_INI_FILES[${MAME_GETTER_INI}]}"

            if [[ "${MAME_GETTER_ROMDIR}" != "" ]] ; then
                ROMMAME="${MAME_GETTER_ROMDIR}"
            fi

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 $(settings_active_action ${MAME_GETTER})"
            fi

            local ACTIVATE="1 $(settings_active_action ${MAME_GETTER})"

            set +e
            dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --title "MAME-Getter Settings" \
                --menu "$(settings_menu_descr_text $(basename ${EXPORTED_INI_PATH}) ${MAME_GETTER_INI})" 11 75 25 \
                "${ACTIVATE}" "Activated: ${MAME_GETTER}" \
                "2 INI file"  "$(basename ${MAME_GETTER_INI})" \
                "3 MAME ROM directory" "${ROMMAME}" \
                "BACK"  "" 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "${ACTIVATE}") settings_change_var "MAME_GETTER" "${SETTINGS_TMP_UPDATE_ALL_INI}" ;;
                "2 INI file") settings_change_var "MAME_GETTER_INI" "${SETTINGS_TMP_UPDATE_ALL_INI}" ;;
                "3 MAME ROM directory") settings_change_var "ROMMAME" "${SELECTED_INI_FILES[${MAME_GETTER_INI}]}" ;;
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

### SETTINGS OPTIONS: Arcade Organizer ##
SETTINGS_OPTIONS_HBMAME_GETTER=("true" "false")
SETTINGS_OPTIONS_HBMAME_GETTER_INI=("update_mame-getter.ini" "$(basename ${EXPORTED_INI_PATH})")
SETTINGS_OPTIONS_ROMHBMAME=("games/hbmame" "_Arcade/hbmame")

settings_menu_hbmame_getter() {
    local TMP=$(mktemp)
    while true ; do
        (
            local HBMAME_GETTER="${SETTINGS_OPTIONS_HBMAME_GETTER[0]}"
            local HBMAME_GETTER_INI="${SETTINGS_OPTIONS_HBMAME_GETTER_INI[0]}"
            local ROMHBMAME="${SETTINGS_OPTIONS_ROMHBMAME[0]}"

            load_vars_from_ini "${SETTINGS_TMP_UPDATE_ALL_INI}" "HBMAME_GETTER" "HBMAME_GETTER_INI"
            load_ini_file "${SELECTED_INI_FILES[${HBMAME_GETTER_INI}]}"

            if [[ "${HBMAME_GETTER_ROMDIR}" != "" ]] ; then
                ROMHBMAME="${HBMAME_GETTER_ROMDIR}"
            fi

            local DEFAULT_SELECTION=
            if [ -s ${TMP} ] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            else
                DEFAULT_SELECTION="1 $(settings_active_action ${HBMAME_GETTER})"
            fi

            local ACTIVATE="1 $(settings_active_action ${HBMAME_GETTER})"

            set +e
            dialog --keep-window --default-item "${DEFAULT_SELECTION}" --cancel-label "Back" --ok-label "Select" --title "HBMAME-Getter Settings" \
                --menu "$(settings_menu_descr_text $(basename ${EXPORTED_INI_PATH}) ${HBMAME_GETTER_INI})" 11 75 25 \
                "${ACTIVATE}" "Activated: ${HBMAME_GETTER}" \
                "2 INI file"  "$(basename ${HBMAME_GETTER_INI})" \
                "3 HBMAME ROM directory" "${ROMHBMAME}" \
                "BACK"  "" 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "${ACTIVATE}") settings_change_var "HBMAME_GETTER" "${SETTINGS_TMP_UPDATE_ALL_INI}" ;;
                "2 INI file") settings_change_var "HBMAME_GETTER_INI" "${SETTINGS_TMP_UPDATE_ALL_INI}" ;;
                "3 HBMAME ROM directory") settings_change_var "ROMHBMAME" "${SELECTED_INI_FILES[${HBMAME_GETTER_INI}]}" ;;
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

### SETTINGS OPTIONS: ARCADE ORGANIZER ##
SETTINGS_OPTIONS_ARCADE_ORGANIZER=("true" "false")
SETTINGS_OPTIONS_ARCADE_ORGANIZER_INI=("update_arcade-organizer.ini" "$(basename ${EXPORTED_INI_PATH})")
SETTINGS_OPTIONS_SKIPALTS=("true" "false")

settings_menu_arcade_organizer() {
    local TMP=$(mktemp)
    while true ; do
        (
            local ARCADE_ORGANIZER="${SETTINGS_OPTIONS_ARCADE_ORGANIZER[0]}"
            local ARCADE_ORGANIZER_INI="${SETTINGS_OPTIONS_ARCADE_ORGANIZER_INI[0]}"
            local SKIPALTS="${SETTINGS_OPTIONS_SKIPALTS[0]}"

            load_vars_from_ini "${SETTINGS_TMP_UPDATE_ALL_INI}" "ARCADE_ORGANIZER" "ARCADE_ORGANIZER_INI"
            load_ini_file "${SELECTED_INI_FILES[${ARCADE_ORGANIZER_INI}]}"

            if [[ "${ARCADE_ORGANIZER_SKIPALTS}" != "" ]] ; then
                SKIPALTS="${ARCADE_ORGANIZER_SKIPALTS}"
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
                --menu "$(settings_menu_descr_text $(basename ${EXPORTED_INI_PATH}) ${ARCADE_ORGANIZER_INI})" 11 75 25 \
                "${ACTIVATE}" "Activated: ${ARCADE_ORGANIZER}" \
                "2 INI file"  "$(basename ${ARCADE_ORGANIZER_INI})" \
                "3 Skip MRA-Alternatives" "${SKIPALTS}" \
                "BACK"  "" 2> ${TMP}
            DEFAULT_SELECTION="$?"
            set -e

            if [[ "${DEFAULT_SELECTION}" == "0" ]] ; then
                DEFAULT_SELECTION="$(cat ${TMP})"
            fi

            case "${DEFAULT_SELECTION}" in
                "${ACTIVATE}") settings_change_var "ARCADE_ORGANIZER" "${SETTINGS_TMP_UPDATE_ALL_INI}" ;;
                "2 INI file") settings_change_var "ARCADE_ORGANIZER_INI" "${SETTINGS_TMP_UPDATE_ALL_INI}" ;;
                "3 Skip MRA-Alternatives") settings_change_var "SKIPALTS" "${SELECTED_INI_FILES[${ARCADE_ORGANIZER_INI}]}" ;;
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
                cp ${SETTINGS_TMP_UPDATE_ALL_INI} ${INI_PATH}
                sed -i "s%MAIN_UPDATER_INI=.*%MAIN_UPDATER_INI=\"${SETTINGS_TMP_MAIN_UPDATER_INI}\"%g" "${INI_PATH}"
                sed -i "s%JOTEGO_UPDATER_INI=.*%JOTEGO_UPDATER_INI=\"${SETTINGS_TMP_JOTEGO_UPDATER_INI}\"%g" "${INI_PATH}"
                sed -i "s%UNOFFICIAL_UPDATER_INI=.*%UNOFFICIAL_UPDATER_INI=\"${SETTINGS_TMP_UNOFFICIAL_UPDATER_INI}\"%g" "${INI_PATH}"
                sed -i "s%LLAPI_UPDATER_INI=.*%LLAPI_UPDATER_INI=\"${SETTINGS_TMP_LLAPI_UPDATER_INI}\"%g" "${INI_PATH}"
                sed -i "s%MAME_GETTER_INI=.*%MAME_GETTER_INI=\"${SETTINGS_TMP_MAME_GETTER_INI}\"%g" "${INI_PATH}"
                sed -i "s%HBMAME_GETTER_INI=.*%HBMAME_GETTER_INI=\"${SETTINGS_TMP_HBMAME_GETTER_INI}\"%g" "${INI_PATH}"
                sed -i "s%ARCADE_ORGANIZER_INI=.*%ARCADE_ORGANIZER_INI=\"${SETTINGS_TMP_ARCADE_ORGANIZER_INI}\"%g" "${INI_PATH}"
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

SETTINGS_FILES_TO_SAVE_RET_ARRAY=()
SETTINGS_FILES_TO_SAVE_RET_TEXT=
settings_files_to_save() {
    SETTINGS_FILES_TO_SAVE_RET_TEXT=""
    SETTINGS_FILES_TO_SAVE_RET_ARRAY=()
    for file in ${!SELECTED_INI_FILES[@]} ; do
        if ! diff -q "${file}" "${SELECTED_INI_FILES[${file}]}" > /dev/null 2>&1 && \
            { \
                grep -q '[^[:space:]]' "${file}" > /dev/null 2>&1 \
                || grep -q '[^[:space:]]' "${SELECTED_INI_FILES[${file}]}" > /dev/null 2>&1 \
            ; }
        then
            SETTINGS_FILES_TO_SAVE_RET_TEXT="${SETTINGS_FILES_TO_SAVE_RET_TEXT}"$'\n'"${file}"
            SETTINGS_FILES_TO_SAVE_RET_ARRAY+=("${file}")
        fi
    done
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
            for file in ${SETTINGS_FILES_TO_SAVE_RET_ARRAY[@]} ; do
                cp ${SELECTED_INI_FILES[${file}]} ${file}
            done
            if [ -f ${EXPORTED_INI_PATH} ] ; then
                cp ${EXPORTED_INI_PATH} ${INI_PATH} 2> /dev/null || true
            fi
            set +e
            dialog --keep-window --msgbox "   Saved" 0 0
            set -e
            ;;
        *) ;;
    esac
}

settings_menu_descr_text() {
    local INI_A="${1}"
    local INI_B="${2}"
    if [[ "${INI_A}" == "${INI_B}" ]] ; then
        echo "Settings loaded from '${INI_A}'"
    else
        echo "Settings loaded from '${INI_A}' and '${INI_B}'"
    fi
}

settings_change_var() {
    local VAR="${1}"
    local INI_PATH="${2}"
    declare -n OPTIONS="SETTINGS_OPTIONS_${VAR}"
    local DEFAULT="${OPTIONS[0]}"

    local VALUE="$(load_single_var_from_ini ${VAR} ${INI_PATH})"
    if [[ "${VALUE}" == "" ]] ; then
        VALUE="${DEFAULT}"
    fi

    local NEXT_INDEX=-1
    for i in "${!OPTIONS[@]}" ; do
        local CURRENT="${OPTIONS[${i}]}"
        if [[ "${CURRENT}" == "${VALUE}" ]] ; then
            NEXT_INDEX=$((i + 1))
            if [ ${NEXT_INDEX} -ge ${#OPTIONS[@]} ] ; then
                NEXT_INDEX=0
            fi
            break
        fi
    done

    if [ ${NEXT_INDEX} -eq -1 ] ; then
        echo "Bug on NEXT_INDEX"
        echo "VAR: ${VAR}"
        echo "INI_PATH: ${INI_PATH}"
        echo "VALUE: ${VALUE}"
        echo "DEFAULT: ${DEFAULT}"
        exit 1
    fi

    VALUE="${OPTIONS[${NEXT_INDEX}]}"

    sed -i "/^${VAR}=/d" ${INI_PATH} 2> /dev/null

    if [[ "${VALUE}" != "${DEFAULT}" ]] ; then
        if [ ! -z "$(tail -c 1 "${INI_PATH}")" ] ; then
            echo >> ${INI_PATH}
        fi
        echo -n "${VAR}=\"${VALUE}\"" >> ${INI_PATH}
    fi
}

settings_make_ini_from() {
    local INI_SOURCE="${1}"
    local INI_TARGET="${2}"
    rm ${INI_TARGET} 2> /dev/null || true
    echo $INI_SOURCE > tests.log
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
