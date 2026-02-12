#!/bin/bash
# Copyright (c) 2026 José Manuel Barroso Galindo <theypsilon@gmail.com>

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

rm -f /media/fat/Scripts/.config/downloader/downloader_bin /media/fat/Scripts/.config/downloader/downloader_latest.zip
rm -f /media/fat/Scripts/.config/update_all/update_all_bin /media/fat/Scripts/.config/update_all/update_all.pyz

DOWNLOADER_INI="/media/fat/downloader.ini"
PROXY_VALUE=""
if [ -f "$DOWNLOADER_INI" ]; then
    PROXY_VALUE=$(grep -i "^[[:space:]]*http_proxy[[:space:]]*=" "$DOWNLOADER_INI" 2>/dev/null | head -n 1 | sed 's/^[^=]*=[[:space:]]*//' | sed 's/[[:space:]]*[#;].*$//' | sed 's/[[:space:]]*$//')
    if [ ! -n "$PROXY_VALUE" ]; then
        echo "ERROR: 'http_proxy' field has an empty value in $DOWNLOADER_INI. Fix it to use this."
        exit -1
    fi
else
    echo "ERROR: $DOWNLOADER_INI not found, create it with a 'http_proxy' field to use this."
    exit -1
fi

export http_proxy="$PROXY_VALUE"
export HTTP_PROXY="$PROXY_VALUE"

/media/fat/Scripts/update_all.sh
