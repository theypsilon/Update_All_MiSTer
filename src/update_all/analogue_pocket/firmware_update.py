# Copyright (c) 2022-2024 José Manuel Barroso Galindo <theypsilon@gmail.com>

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

from typing import TypedDict
import ssl
from pathlib import Path
import glob
import os

from update_all.analogue_pocket.http_gateway import HttpGateway, write_incoming_stream
from update_all.analogue_pocket.utils import pocket_mount
from update_all.file_system import hash_file
from update_all.logger import Logger
from update_all.analogue_pocket.pocket_firmware_details import pocket_firmware_details


class FirmwareInfo(TypedDict):
    url: str
    version: str
    file: str
    md5: str
    size: float


def latest_firmware_info() -> FirmwareInfo:
    return pocket_firmware_details()


def pocket_firmware_update(ssl_ctx: ssl.SSLContext, logger: Logger):
    firmware_info = latest_firmware_info()

    mount = pocket_mount()
    if mount is None:
        logger.print('ERROR! Analogue Pocket not found!')
        logger.print('Troubleshooting steps:')
        logger.print(' - 1. Connect your Pocket to the MiSTer USB port.')
        logger.print(" - 2. Make sure your Pocket is on.")
        logger.print(' - 3. Make sure your Pocket is mounting the SD card.')
        logger.print(' - 4. Try this tool again.')
        return False

    already_on_latest_firmware = False
    for firmware in glob.glob(os.path.join(mount, 'pocket_firmware*.bin')):
        firmware_name = Path(firmware).name.lower()
        if firmware_name == firmware_info['file'].lower():
            already_on_latest_firmware = True
            break

        logger.print(f'Removing old firmware file: {firmware_name}')
        os.remove(firmware)

    if already_on_latest_firmware:
        logger.print(f'Your Pocket already contains the latest firmware version {firmware_info["version"]}')
        return True

    target_file = Path(mount) / Path(firmware_info['file'])

    logger.print(f'Updating Analogue Pocket firmware to version {firmware_info["version"]}...')

    with HttpGateway(ssl_ctx=ssl_ctx, timeout=180, logger=None) as http:
        with http.open(firmware_info['url'], 'GET') as (final_url, in_stream):
            if in_stream.status != 200:
                logger.print(f'ERROR! Bad http status!: {in_stream.status}')
                return False

            logger.debug(f'Downloading from {final_url} to {target_file}...')
            logger.print(f'Downloading firmware to {target_file}...')
            write_incoming_stream(in_stream, str(target_file), timeout=180)

    if not target_file.exists():
        logger.print(f'ERROR! Missing file {firmware_info["file"]}')
        return False

    decimals = count_decimals(firmware_info['size'])
    size = round(float(target_file.stat().st_size) / 1_000_000, decimals)
    logger.print(f'Downloaded {size}MB')
    if size != firmware_info['size']:
        logger.print(f'ERROR! Wrong size! {size} != {firmware_info["size"]}')
        return False

    logger.print(f'Verifying MD5...')
    md5 = hash_file(str(target_file))
    if md5 != firmware_info['md5']:
        logger.print(f'ERROR! Wrong MD5! {md5} != {firmware_info["md5"]}')
        return False

    logger.print('Firmware updated successfully!')

    return True


def count_decimals(number):
    number_str = str(number)
    if '.' in number_str:
        return len(number_str.split('.')[1])
    else:
        return 0
