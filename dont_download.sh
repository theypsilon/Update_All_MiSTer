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
ENCC_FORKS="dialog" # Possible values: "true", "false" or "dialog"

MAIN_UPDATER="true"
MAIN_UPDATER_INI="${EXPORTED_INI_PATH}" # Probably /media/fat/Scripts/update_all.ini

JOTEGO_UPDATER="true"
JOTEGO_UPDATER_INI="${EXPORTED_INI_PATH}" # Probably /media/fat/Scripts/update_all.ini

UNOFFICIAL_UPDATER="false"
UNOFFICIAL_UPDATER_INI="${EXPORTED_INI_PATH}" # Probably /media/fat/Scripts/update_all.ini

MAME_GETTER="true"
MAME_GETTER_INI="/media/fat/Scripts/update_mame-getter.ini"

HBMAME_GETTER="true"
HBMAME_GETTER_INI="/media/fat/Scripts/update_hbmame-getter.ini"

ARCADE_ORGANIZER="true"
ARCADE_ORGANIZER_INI="/media/fat/Scripts/update_arcade-organizer.ini"

ALWAYS_ASSUME_NEW_STANDARD_MRA="false"
ALWAYS_ASSUME_NEW_ALTERNATIVE_MRA="false"

WAIT_TIME_FOR_READING=4

# ========= CODE STARTS HERE =========
ORIGINAL_SCRIPT_PATH="${0}"
INI_PATH="${ORIGINAL_SCRIPT_PATH%.*}.ini"
LOG_FILENAME="$(basename ${EXPORTED_INI_PATH%.*}.log)"

echo "Executing 'Update All' script for MiSTer"
echo "Version 1.0"

echo
echo "Reading INI file '${EXPORTED_INI_PATH}':"
if [ -f ${EXPORTED_INI_PATH} ] ; then
    cp ${EXPORTED_INI_PATH} ${INI_PATH}

	TMP=$(mktemp)
	dos2unix < "${INI_PATH}" 2> /dev/null | grep -v "^exit" > ${TMP}
	source ${TMP}
	rm -f ${TMP}

    echo "OK."
else
    echo "Not found."
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
    echo "${SCRIPT_URL}"
    echo ""

    set +e
    curl \
        ${CURL_RETRY} \
        ${SSL_SECURITY_OPTION} \
        --fail \
        --location \
        "${SCRIPT_URL}/blob/master/mister_updater.sh?raw=true" | \
		sed "s%INI_PATH=%INI_PATH=\"${SCRIPT_INI}\" #%g" | \
		sed 's/AUTOREBOOT="true"/AUTOREBOOT="false"/g' | \
        bash -

    UPDATER_RET=$?
    set -e

    sleep ${WAIT_TIME_FOR_READING}
}

run_mame_getter_script() {
    local SCRIPT_TITLE="${1}"
    local SCRIPT_URL="${2}"
    local SCRIPT_INI="${3}"

    local SCRIPT_FILENAME="${SCRIPT_URL/*\//}"
    SCRIPT_FILENAME="${SCRIPT_FILENAME%.*}"

    draw_separator

    echo "STARTING: ${SCRIPT_TITLE}"
    echo ""
    echo "Downloading the most recent ${SCRIPT_FILENAME} script."
    echo " "

    wget -q -t 3 --output-file=/tmp/wget-log --show-progress -O /tmp/${SCRIPT_FILENAME}.sh ${SCRIPT_URL}
    chmod +x /tmp/${SCRIPT_FILENAME}.sh
    sed -i "s%INIFILE=%INIFILE=\"${SCRIPT_INI}\" #%g" /tmp/${SCRIPT_FILENAME}.sh
    /tmp/${SCRIPT_FILENAME}.sh
    rm /tmp/${SCRIPT_FILENAME}.sh
    echo "FINISHED: ${SCRIPT_TITLE}"

    sleep ${WAIT_TIME_FOR_READING}
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
if [[ "${MAME_GETTER}" == "true" ]] ; then
    echo "- MAME Getter (forced: ${ALWAYS_ASSUME_NEW_STANDARD_MRA})"
fi
if [[ "${HBMAME_GETTER}" == "true" ]] ; then
    echo "- HBMAME Getter (forced: ${ALWAYS_ASSUME_NEW_ALTERNATIVE_MRA})"
fi
if [[ "${ARCADE_ORGANIZER}" == "true" ]] ; then
    if [[ "${ALWAYS_ASSUME_NEW_STANDARD_MRA:-no}" == "yes" ]] || [[ "${ALWAYS_ASSUME_NEW_ALTERNATIVE_MRA:-no}" == "yes" ]] ; then
        FORCED_ORGANIZER="true"
    else
        FORCED_ORGANIZER="false"
    fi
    echo "- Arcade Organizer (forced: ${FORCED_ORGANIZER})"
fi

sleep ${WAIT_TIME_FOR_READING}

FAILING_UPDATERS=()

if [[ "${MAIN_UPDATER}" == "true" ]] ; then
    case "${ENCC_FORKS}" in
        true)
            MAIN_UPDATER_URL="https://github.com/theypsilon/Updater_script_MiSTer_DB9"
            ;;
        false)
            MAIN_UPDATER_URL="https://github.com/MiSTer-devel/Updater_script_MiSTer"
            ;;
        *)
            sleep ${WAIT_TIME_FOR_READING}
            sleep ${WAIT_TIME_FOR_READING}
            set +e
            dialog --title "Extended Native Controller Compatibility"  --yesno "Would you like to install unofficial forks from MiSTer-devel cores that are patched to be compatible with native Genesis (DB9), and NeoGeo/Supergun (DB15) controllers?\n\nIn order to use them, you require an unofficial SNAC8 adapter.\n\nMore info at: https://github.com/theypsilon/Update_All_MiSTer/wiki" 11 75
            DIALOG_RET=$?
            set -e
            case $DIALOG_RET in
                0)
                    SELECTION="ENCC_FORKS=\"true\""
                    MAIN_UPDATER_URL="https://github.com/theypsilon/Updater_script_MiSTer_DB9"
                    ;;
                1)
                    SELECTION="ENCC_FORKS=\"false\""
                    MAIN_UPDATER_URL="https://github.com/MiSTer-devel/Updater_script_MiSTer"
                    ;;
                *)
                    echo
                    echo "Execution aborted by user input."
                    exit 1
                    ;;
            esac
            set +e
            dialog --title "Save ENCC selection?"  --yesno "Would you like to save your previous selection in ${EXPORTED_INI_PATH/*\//}?\n\n${SELECTION}\n\nSaving this will stop this dialog from appearing the next time you run this script." 10 75
            DIALOG_RET=$?
            set -e
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
                    exit 1
                    ;;
            esac
            ;;
    esac
    run_updater_script ${MAIN_UPDATER_URL} ${MAIN_UPDATER_INI}
    if [ $UPDATER_RET -ne 0 ]; then
        FAILING_UPDATERS+=("/media/fat/Scripts/.mister_updater/${LOG_FILENAME}")
    fi
fi

if [[ "${JOTEGO_UPDATER}" == "true" ]] ; then
    run_updater_script https://github.com/jotego/Updater_script_MiSTer ${JOTEGO_UPDATER_INI}
    if [ $UPDATER_RET -ne 0 ]; then
        FAILING_UPDATERS+=("/media/fat/Scripts/.mister_updater_jt/${LOG_FILENAME}")
    fi
fi

if [[ "${UNOFFICIAL_UPDATER}" == "true" ]] ; then
    run_updater_script https://github.com/theypsilon/Updater_script_MiSTer_Unofficial ${UNOFFICIAL_UPDATER_INI}
    if [ $UPDATER_RET -ne 0 ]; then
        FAILING_UPDATERS+=("/media/fat/Scripts/.mister_updater_unofficials/${LOG_FILENAME}")
    fi
fi

draw_separator

if [[ "${MAME_GETTER}" == "true" ]] || [[ "${ARCADE_ORGANIZER}" == "true" ]] ; then
    if grep -q "\.mra" /media/fat/Scripts/.mister_updater{,_jt,_unofficials}/"${LOG_FILENAME}" ; then
        echo "Detected new MRA files."
        NEW_STANDARD_MRA="yes"
    fi
fi

if [[ "${HBMAME_GETTER}" == "true" ]] || [[ "${ARCADE_ORGANIZER}" == "true" ]] ; then
    if grep -q "MRA-Alternatives_[0-9]*\.zip" /media/fat/Scripts/.mister_updater{,_jt,_unofficials}/"${LOG_FILENAME}" ; then
        echo "Detected new MRA-Alternatives."
        NEW_ALTERNATIVE_MRA="yes"
    fi
fi

if [[ "${NEW_STANDARD_MRA:-no}" != "yes" ]] && [[ "${NEW_ALTERNATIVE_MRA:-no}" != "yes" ]] ; then
    echo "No new MRA detected."
fi

sleep ${WAIT_TIME_FOR_READING}
echo

if [[ "${NEW_STANDARD_MRA:-no}" == "yes" ]] || [[ "${ALWAYS_ASSUME_NEW_STANDARD_MRA:-false}" == "true" ]] ; then
    if [[ "${MAME_GETTER}" == "true" ]] ; then
        run_mame_getter_script "MAME-GETTER" https://raw.githubusercontent.com/MAME-GETTER/MiSTer_MAME_SCRIPTS/master/mame-merged-set-getter.sh ${MAME_GETTER_INI}
    fi
fi

if [[ "${NEW_ALTERNATIVE_MRA:-no}" == "yes" ]] || [[ "${ALWAYS_ASSUME_NEW_ALTERNATIVE_MRA:-false}" == "true" ]] ; then
    if [[ "${HBMAME_GETTER}" == "true" ]] ; then
        run_mame_getter_script "HBMAME-GETTER" https://raw.githubusercontent.com/MAME-GETTER/MiSTer_MAME_SCRIPTS/master/hbmame-merged-set-getter.sh ${HBMAME_GETTER_INI}
    fi
fi

if [[ "${NEW_STANDARD_MRA:-no}" == "yes" ]] || [[ "${NEW_ALTERNATIVE_MRA:-no}" == "yes" ]] ; then
    if [[ "${ARCADE_ORGANIZER}" == "true" ]] ; then
        run_mame_getter_script " _ARCADE-ORGANIZER" https://github.com/MAME-GETTER/_arcade-organizer/raw/master/_arcade-organizer.sh ${ARCADE_ORGANIZER_INI}
    fi
fi


if [ ${#FAILING_UPDATERS[@]} -ge 1 ] ; then
    echo "There were some errors in the Updaters."
    echo "Therefore, MiSTer hasn't been fully updated."
    echo
    echo "Check the following logs for more information:"
    for log_file in ${FAILING_UPDATERS[@]} ; do
        echo " - $log_file"
    done
    echo
    echo "Maybe a network problem?"
    echo "Check your connection and then run this script again."
    exit 1
fi

echo "Your MiSTer has been updated successfully!"
echo
echo "Update All script finished."
echo

exit 0
