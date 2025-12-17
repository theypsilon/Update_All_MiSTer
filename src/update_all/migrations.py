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

from update_all.store_migrator import Migration


def migrations() -> list[Migration]:
    return [migration_v1, migration_v2, migration_v3, migration_v4]

def migration_v1(local_store) -> None:
    """create arcade_names_txt field"""

    local_store['introduced_arcade_names_txt'] = False
    local_store['_dirty'] = True

def migration_v2(local_store) -> None:
    """create arcade_names_txt field"""

    local_store['pocket_firmware_update'] = False
    local_store['pocket_backup'] = False
    local_store['_dirty'] = True

def migration_v3(local_store) -> None:
    """create summary screen field"""

    local_store['log_viewer'] = True

def migration_v4(local_store) -> None:
    """create timeline_after_logs field"""

    local_store['timeline_after_logs'] = True
