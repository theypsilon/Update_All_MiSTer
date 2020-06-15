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

HBMAME_GETTER="true"
HBMAME_GETTER_INI="/media/fat/Scripts/update_hbmame-getter.ini"

ARCADE_ORGANIZER="true"
ARCADE_ORGANIZER_INI="/media/fat/Scripts/update_arcade-organizer.ini"

ALWAYS_ASSUME_NEW_STANDARD_MRA="false"
ALWAYS_ASSUME_NEW_ALTERNATIVE_MRA="false"

WAIT_TIME_FOR_READING=4
AUTOREBOOT="true"

# ========= CODE STARTS HERE =========
ORIGINAL_SCRIPT_PATH="${0}"
INI_PATH="${ORIGINAL_SCRIPT_PATH%.*}.ini"
LOG_FILENAME="$(basename ${EXPORTED_INI_PATH%.*}.log)"
WORK_PATH="/media/fat/Scripts/.update_all"
GLOG_TEMP="/tmp/tmp.global.${LOG_FILENAME}"
GLOG_PATH="${WORK_PATH}/${LOG_FILENAME}"

rm ${GLOG_TEMP} 2> /dev/null || true
enable_global_log() {
    exec >  >(tee -ia ${GLOG_TEMP})
    exec 2> >(tee -ia ${GLOG_TEMP} >&2)
}
disable_global_log() {
    exec 1>&6 ; exec 2>&7
}
exec 6>&1 ; exec 7>&2 # Saving stdout and stderr
enable_global_log
trap "mv ${GLOG_TEMP} ${GLOG_PATH}" EXIT

echo "Executing 'Update All' script for MiSTer"
echo "Version 1.0"

echo
echo "Reading INI file '${EXPORTED_INI_PATH}':"
if [ -f ${EXPORTED_INI_PATH} ] ; then
    cp ${EXPORTED_INI_PATH} ${INI_PATH}

    TMP=$(mktemp)
    dos2unix < "${INI_PATH}" 2> /dev/null | grep -v "^exit" > ${TMP} || true
    source ${TMP}
    rm -f ${TMP}

    echo "OK."
else
    echo "Not found."
fi

if [ ! -d ${WORK_PATH} ] ; then
    mkdir -p ${WORK_PATH}
    ALWAYS_ASSUME_NEW_STANDARD_MRA="true"
    ALWAYS_ASSUME_NEW_ALTERNATIVE_MRA="true"

    echo
    echo "Creating '${WORK_PATH}' for the first time."
    echo "Performing a full forced update."
fi

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

    set +e
    curl \
        ${CURL_RETRY} \
        ${SSL_SECURITY_OPTION} \
        --fail \
        --location \
        ${SCRIPT_URL} | \
        sed "s%INI_PATH=%INI_PATH=\"${SCRIPT_INI}\" #%g" | \
        sed 's/${AUTOREBOOT}/false/g' | \
        bash -

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

    local SCRIPT_FILENAME="${SCRIPT_URL/*\//}"
    local SCRIPT_PATH="/tmp/${SCRIPT_FILENAME%.*}.sh"

    draw_separator

    echo "Downloading the most recent $(basename ${SCRIPT_FILENAME}) script."
    echo " "

    wget -q -t 3 --output-file=/tmp/wget-log --show-progress -O ${SCRIPT_PATH} ${SCRIPT_URL}
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

        disable_global_log
        ${SCRIPT_PATH}
        enable_global_log

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
    [[ "${NEW_STANDARD_MRA:-false}" == "true" ]] || \
    [[ "${ALWAYS_ASSUME_NEW_STANDARD_MRA:-false}" == "true" ]] || \
    [[ "${NEW_ALTERNATIVE_MRA:-false}" == "true" ]] || \
    [[ "${ALWAYS_ASSUME_NEW_ALTERNATIVE_MRA:-false}" == "true" ]] || \
    [ ! -d ${MAME_GETTER_ROMDIR} ] || [ -z "$(ls -A ${MAME_GETTER_ROMDIR})" ]
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
    [[ "${NEW_ALTERNATIVE_MRA:-false}" == "true" ]] || \
    [[ "${ALWAYS_ASSUME_NEW_ALTERNATIVE_MRA:-false}" == "true" ]] || \
    [ ! -d ${HBMAME_GETTER_ROMDIR} ] || [ -z "$(ls -A ${HBMAME_GETTER_ROMDIR})" ]
}

ARCADE_ORGANIZER_ORGDIR=
ARCADE_ORGANIZER_MRADIR=
read_ini_arcade_organizer() {
    local SCRIPT_PATH="${1}"
    local SCRIPT_INI="${2}"

    ARCADE_ORGANIZER_ORGDIR=$(grep "^[^#;]" "${SCRIPT_PATH}" | grep "ORGDIR=" | head -n 1 | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^"//' -e 's/"$//')
    ARCADE_ORGANIZER_MRADIR=$(grep "^[^#;]" "${SCRIPT_PATH}" | grep "MRADIR=" | head -n 1 | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^"//' -e 's/"$//')

    if [ ! -s ${SCRIPT_INI} ] ; then
        return
    fi

    if [ `grep -c "ORGDIR=" "${SCRIPT_INI}"` -gt 0 ]
    then
        ARCADE_ORGANIZER_ORGDIR=`grep "ORGDIR" "${SCRIPT_INI}" | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^"//' -e 's/"$//'`
    fi 2>/dev/null 

    if [ `grep -c "MRADIR=" "${SCRIPT_INI}"` -gt 0 ]
    then
        ARCADE_ORGANIZER_MRADIR=`grep "MRADIR=" "${SCRIPT_INI}" | awk -F "=" '{print$2}' | sed -e 's/^ *//' -e 's/ *$//' -e 's/^"//' -e 's/"$//'`
    fi 2>/dev/null
}

should_run_arcade_organizer() {
    [[ "${NEW_STANDARD_MRA:-false}" == "true" ]] || \
    [[ "${NEW_ALTERNATIVE_MRA:-false}" == "true" ]] || \
    [ ! -d ${ARCADE_ORGANIZER_ORGDIR} ] || [ -z "$(ls -A ${ARCADE_ORGANIZER_ORGDIR})" ]
}

contains_str() {
    local FILE="${1}"
    local STR="${2}"
    if [ ! -f ${FILE} ] ; then
        return 1
    fi
    if grep -q "${STR}" ${FILE} ; then
        return 0
    else
        return 1
    fi
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
    echo "- MAME Getter (forced: ${ALWAYS_ASSUME_NEW_STANDARD_MRA})"
fi
if [[ "${HBMAME_GETTER}" == "true" ]] ; then
    echo "- HBMAME Getter (forced: ${ALWAYS_ASSUME_NEW_ALTERNATIVE_MRA})"
fi
if [[ "${ARCADE_ORGANIZER}" == "true" ]] ; then
    if [[ "${ALWAYS_ASSUME_NEW_STANDARD_MRA:-false}" == "true" ]] || [[ "${ALWAYS_ASSUME_NEW_ALTERNATIVE_MRA:-false}" == "true" ]] ; then
        FORCED_ORGANIZER="true"
    else
        FORCED_ORGANIZER="false"
    fi
    echo "- Arcade Organizer (forced: ${FORCED_ORGANIZER})"
fi

sleep ${WAIT_TIME_FOR_READING}

echo
echo "Start time: $(date)"

REBOOT_NEEDED="false"
FAILING_UPDATERS=()

if [[ "${MAIN_UPDATER}" == "true" ]] ; then
    case "${ENCC_FORKS}" in
        true)
            MAIN_UPDATER_URL="https://raw.githubusercontent.com/theypsilon/Updater_script_MiSTer_DB9/master/mister_updater.sh"
            ;;
        false)
            MAIN_UPDATER_URL="https://raw.githubusercontent.com/MiSTer-devel/Updater_script_MiSTer/master/mister_updater.sh"
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
                    MAIN_UPDATER_URL="https://raw.githubusercontent.com/theypsilon/Updater_script_MiSTer_DB9/master/mister_updater.sh"
                    ;;
                1)
                    SELECTION="ENCC_FORKS=\"false\""
                    MAIN_UPDATER_URL="https://raw.githubusercontent.com/MiSTer-devel/Updater_script_MiSTer/master/mister_updater.sh"
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
    run_updater_script ${MAIN_UPDATER_URL} ${MAIN_UPDATER_INI}
    if [ $UPDATER_RET -ne 0 ]; then
        FAILING_UPDATERS+=("/media/fat/Scripts/.mister_updater/${LOG_FILENAME}")
    fi
    if tail -n 30 ${GLOG_TEMP} | grep -q "You should reboot" ; then
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

draw_separator

if [[ "${MAME_GETTER}" == "true" ]] || [[ "${ARCADE_ORGANIZER}" == "true" ]] ; then
    if contains_str "/media/fat/Scripts/.mister_updater/${LOG_FILENAME}" "\.mra" || \
        contains_str "/media/fat/Scripts/.mister_updater_jt/${LOG_FILENAME}" "\.mra" || \
        contains_str "/media/fat/Scripts/.mister_updater_unofficials/${LOG_FILENAME}" "\.mra"
    then
        echo "Detected new MRA files."
        NEW_STANDARD_MRA="true"
    fi
fi

if [[ "${HBMAME_GETTER}" == "true" ]] || [[ "${ARCADE_ORGANIZER}" == "true" ]] ; then
    if contains_str "/media/fat/Scripts/.mister_updater/${LOG_FILENAME}" "MRA-Alternatives_[0-9]*\.zip" || \
        contains_str "/media/fat/Scripts/.mister_updater_jt/${LOG_FILENAME}" "MRA-Alternatives_[0-9]*\.zip" || \
        contains_str "/media/fat/Scripts/.mister_updater_unofficials/${LOG_FILENAME}" "MRA-Alternatives_[0-9]*\.zip"
    then
        echo "Detected new MRA-Alternatives."
        NEW_ALTERNATIVE_MRA="true"
    fi
fi

if [[ "${NEW_STANDARD_MRA:-false}" != "true" ]] && [[ "${NEW_ALTERNATIVE_MRA:-false}" != "true" ]] ; then
    echo "No new MRA detected."
fi

sleep ${WAIT_TIME_FOR_READING}
echo

if [[ "${MAME_GETTER}" == "true" ]] ; then
    run_mame_getter_script "MAME-GETTER" read_ini_mame_getter should_run_mame_getter ${MAME_GETTER_INI} \
    https://raw.githubusercontent.com/MAME-GETTER/MiSTer_MAME_SCRIPTS/master/mame-merged-set-getter.sh
fi

if [[ "${HBMAME_GETTER}" == "true" ]] ; then
    run_mame_getter_script "HBMAME-GETTER" read_ini_hbmame_getter should_run_hbmame_getter ${HBMAME_GETTER_INI} \
    https://raw.githubusercontent.com/MAME-GETTER/MiSTer_MAME_SCRIPTS/master/hbmame-merged-set-getter.sh
fi

if [[ "${ARCADE_ORGANIZER}" == "true" ]] ; then
    run_mame_getter_script "_ARCADE-ORGANIZER" read_ini_arcade_organizer should_run_arcade_organizer ${ARCADE_ORGANIZER_INI} \
    https://raw.githubusercontent.com/MAME-GETTER/_arcade-organizer/master/_arcade-organizer.sh
fi

draw_separator

delete_if_empty \
    "${BASE_PATH}/games/mame" \
    "${BASE_PATH}/games/hbmame" \
    "${BASE_PATH}/_Arcade/mame" \
    "${BASE_PATH}/_Arcade/hbmame" \
    "${BASE_PATH}/_Arcade/mra_backup"

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
    echo "Update All 1.0 finished. Your MiSTer has been updated successfully!"
    EXIT_CODE=0
fi

echo
echo "End time: $(date)"
echo
echo "Full log for more details: ${GLOG_PATH}"
echo

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
