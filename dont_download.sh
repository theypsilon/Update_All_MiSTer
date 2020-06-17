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

ENCC_FORKS="dialog" # Possible values: "true", "false" or "dialog"

MAIN_UPDATER="true"
MAIN_UPDATER_INI="${EXPORTED_INI_PATH}" # Probably /media/fat/Scripts/update_all.ini

JOTEGO_UPDATER="true"
JOTEGO_UPDATER_INI="${EXPORTED_INI_PATH}" # Probably /media/fat/Scripts/update_all.ini

UNOFFICIAL_UPDATER="false"
UNOFFICIAL_UPDATER_INI="${EXPORTED_INI_PATH}" # Probably /media/fat/Scripts/update_all.ini

LLAPI_UPDATER="false"
LLAPI_UPDATER_INI="${EXPORTED_INI_PATH}" # Probably /media/fat/Scripts/update_all.ini

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

# ========= CODE STARTS HERE =========
UPDATE_ALL_VERSION="1.0"
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

initialize() {
    initialize_global_log

    echo "Executing 'Update All' script"
    echo "The All-in-One Updater for MiSTer"
    echo "Version ${UPDATE_ALL_VERSION}"

    echo
    echo "Reading INI file '${EXPORTED_INI_PATH}':"
    if [ -f ${EXPORTED_INI_PATH} ] ; then
        cp ${EXPORTED_INI_PATH} ${INI_PATH} 2> /dev/null || true

        TMP=$(mktemp)
        dos2unix < "${INI_PATH}" 2> /dev/null | grep -v "^exit" > ${TMP} || true

        source ${TMP}
        rm -f ${TMP}
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
dialog_main_updater() {
    if [[ "${UPDATE_ALL_OS}" == "WINDOWS" ]] ; then return ; fi
    case "${ENCC_FORKS}" in
        true)
            MAIN_UPDATER_URL="${DB9_UPDATER_URL}"
            ;;
        false)
            ;;
        *)
            sleep ${WAIT_TIME_FOR_READING}
            sleep ${WAIT_TIME_FOR_READING}
            disable_global_log
            set +e
            dialog --title "Extended Native Controller Compatibility"  --yesno "Would you like to install unofficial forks from MiSTer-devel cores that are patched to be compatible with native Genesis (DB9), and NeoGeo/Supergun (DB15) controllers?\n\nIn order to use them, you require an unofficial SNAC8 adapter.\n\nMore info at: https://github.com/theypsilon/Update_All_MiSTer/wiki" 11 75
            DIALOG_RET=$?
            set -e
            enable_global_log
            case $DIALOG_RET in
                0)
                    SELECTION="ENCC_FORKS=\"true\""
                    MAIN_UPDATER_URL="${DB9_UPDATER_URL}"
                    ;;
                1)
                    SELECTION="ENCC_FORKS=\"false\""
                    ;;
                *)
                    echo
                    echo "Execution aborted by user input."
                    echo "You pressed ESC/Back button."
                    exit 0
                    ;;
            esac
            disable_global_log
            set +e
            dialog --title "Save ENCC selection?"  --yesno "Would you like to save your previous selection in ${EXPORTED_INI_PATH/*\//}?\n\n${SELECTION}\n\nSaving this will stop this dialog from appearing the next time you run this script." 10 75
            DIALOG_RET=$?
            set -e
            enable_global_log
            case $DIALOG_RET in
                0)
                    if grep "ENCC_FORKS" ${EXPORTED_INI_PATH} 2> /dev/null ; then
                        sed -i '/ENCC_FORKS/d' ${EXPORTED_INI_PATH} 2> /dev/null
                    fi
                    echo >> ${EXPORTED_INI_PATH}
                    echo "${SELECTION}" >> ${EXPORTED_INI_PATH}
                    ;;
                1)
                    ;;
                *)
                    echo
                    echo "Execution aborted by user input."
                    echo "You pressed ESC/Back button."
                    exit 0
                    ;;
            esac
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

    curl ${CURL_RETRY} ${SSL_SECURITY_OPTION} --fail --location -o ${SCRIPT_PATH} ${SCRIPT_URL}

    sed -i "s%INI_PATH=%INI_PATH=\"${SCRIPT_INI}\" #%g" ${SCRIPT_PATH}
    sed -i 's/${AUTOREBOOT}/false/g' ${SCRIPT_PATH}
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

    curl ${CURL_RETRY} ${SSL_SECURITY_OPTION} --fail --location -o ${SCRIPT_PATH} ${SCRIPT_URL}
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

        disable_global_log
        set +e
        if [ -s ${MRA_INPUT} ] ; then
            ${SCRIPT_PATH} --input-file ${MRA_INPUT}
        else
            ${SCRIPT_PATH}
        fi
        local SCRIPT_RET=$?
        set -e
        enable_global_log

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

    MAME_GETTER_ROMDIR=$(grep "^[^#;]" "${SCRIPT_PATH}" | grep "ROMMAME=" | head -n 1 | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^"//' -e 's/"$//')
    MAME_GETTER_MRADIR=$(grep "^[^#;]" "${SCRIPT_PATH}" | grep "MRADIR=" | head -n 1 | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^"//' -e 's/"$//')

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

    HBMAME_GETTER_ROMDIR=$(grep "^[^#;]" "${SCRIPT_PATH}" | grep "ROMHBMAME=" | head -n 1 | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^"//' -e 's/"$//')
    HBMAME_GETTER_MRADIR=$(grep "^[^#;]" "${SCRIPT_PATH}" | grep "MRADIR=" | head -n 1 | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^"//' -e 's/"$//')

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

    ARCADE_ORGANIZER_ORGDIR=$(grep "^[^#;]" "${SCRIPT_PATH}" | grep "ORGDIR" | head -n 1 | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^ *"//' -e 's/" *$//')
    ARCADE_ORGANIZER_MRADIR=$(grep "^[^#;]" "${SCRIPT_PATH}" | grep "MRADIR=" | head -n 1 | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^ *"//' -e 's/" *$//')
    ARCADE_ORGANIZER_SKIPALTS=$(grep "^[^#;]" "${SCRIPT_PATH}" | grep "SKIPALTS=" | head -n 1 | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^ *"//' -e 's/" *$//')

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

run_update_all() {

    initialize

    echo
    echo "Sequence:"
    if [[ "${MAIN_UPDATER}" == "true" ]] ; then
        echo "- Main Updater (ENCC_FORKS: ${ENCC_FORKS})"
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
    if [[ "${MAME_GETTER}" == "true" ]] ; then
        echo "- MAME Getter (forced: ${MAME_GETTER_FORCE_FULL_RESYNC})"
    fi
    if [[ "${HBMAME_GETTER}" == "true" ]] ; then
        echo "- HBMAME Getter (forced: ${HBMAME_GETTER_FORCE_FULL_RESYNC})"
    fi
    if [[ "${ARCADE_ORGANIZER}" == "true" ]] ; then
        echo "- Arcade Organizer (forced: ${ARCADE_ORGANIZER_FORCE_FULL_RESYNC})"
    fi

    sleep ${WAIT_TIME_FOR_READING}

    echo
    echo "Start time: $(date)"

    local REBOOT_NEEDED="false"
    FAILING_UPDATERS=()

    if [[ "${MAIN_UPDATER}" == "true" ]] ; then
        dialog_main_updater
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
        echo "Installing update_all.sh in /Scripts"
        mkdir -p ../Scripts
        curl ${CURL_RETRY} ${SSL_SECURITY_OPTION} --fail --location -o ../Scripts/update_all.sh https://raw.githubusercontent.com/theypsilon/Update_All_MiSTer/master/update_all.sh
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

if [[ "${UPDATE_ALL_SOURCE:-false}" != "true" ]] ; then
    run_update_all
fi
