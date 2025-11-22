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

LATEST_SCRIPT_PATH="/media/fat/Scripts/.config/update_all/update_all.pyz"
RUN_SCRIPT_PATH="/tmp/update_all.sh"

if [ ! -s "${LATEST_SCRIPT_PATH}" ] ; then
    echo "Run Update All first and try again."
    exit 1
fi

cp "${LATEST_SCRIPT_PATH}" "${RUN_SCRIPT_PATH}"
chmod +x "${RUN_SCRIPT_PATH}"

export COMMAND=latest_log

${RUN_SCRIPT_PATH}

