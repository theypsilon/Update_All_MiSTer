# Copyright (c) 2021-2026 José Manuel Barroso Galindo <theypsilon@gmail.com>
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
# https://github.com/MiSTer-devel/Downloader_MiSTer

import os

POCKET_JSON: str = "Analogue_Pocket.json"


def get_pocket_mount(mounts: list[str]) -> str or None:
    """Search for the Pocket folder in list of mounts and return the first match."""
    for mount in mounts:
        if os.path.exists(os.path.join(mount, POCKET_JSON)):
            return mount
    return None


def pocket_mount():
    USB_MOUNTS: list[str] = [
        "/media/usb0",
        "/media/usb1",
        "/media/usb2",
        "/media/usb3",
        "/media/usb4",
        "/media/usb5",
        "/media/usb6",
        "/media/usb7",
    ]
    return get_pocket_mount(USB_MOUNTS)


def is_pocket_mounted():
    return pocket_mount() is not None
