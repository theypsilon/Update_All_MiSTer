#!/usr/bin/env python3
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

"""
Arcade Organizer PC Launcher

Standalone script to run the Arcade Organizer on a PC (Windows, Mac, Linux).
Place this file at the root of your MiSTer file tree (e.g. the SD card root)
and run it with Python 3.9+.

It downloads the Update All pyz, imports ArcadeOrganizerService, and runs
the organizer against the local file tree.

Environment variables:
  UPDATE_ALL_SOURCE       URL or local path to update_all.pyz
  PC_LAUNCHER_NO_WAIT     Set to '1' to skip the "Press Enter" prompt
  INI_FILE                Path to the arcade organizer INI file
"""

import json
import os
import sys
from pathlib import Path
from shutil import copy, copyfileobj
from tempfile import NamedTemporaryFile
from urllib.request import urlopen, Request


_DEFAULT_RELEASE_API = 'https://api.github.com/repos/theypsilon/Update_All_MiSTer/releases/latest'
_PYZ_ASSET_NAME = 'update_all.pyz'


def _find_pyz_url():
    """Fetch the latest release from GitHub API and return the update_all.pyz download URL."""
    print('Fetching latest Update All release info...')
    req = Request(_DEFAULT_RELEASE_API, headers={'Accept': 'application/vnd.github+json'})
    with urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    for asset in data.get('assets', []):
        if asset['name'] == _PYZ_ASSET_NAME:
            return asset['browser_download_url']
    raise RuntimeError(f'Could not find {_PYZ_ASSET_NAME} in latest release assets')


def _fetch_pyz():
    """Download or copy the update_all.pyz to a temp file. Returns the temp file path."""
    source = os.environ.get('UPDATE_ALL_SOURCE', '')

    if source and not source.startswith('http://') and not source.startswith('https://'):
        # Local file path
        with NamedTemporaryFile(suffix='.pyz', delete=False) as temp:
            temp_name = temp.name
            temp.close()
            copy(source, temp_name)
        return temp_name

    url = source if source else _find_pyz_url()

    print(f'Downloading {url} ...')
    with NamedTemporaryFile(suffix='.pyz', mode='wb', delete=False) as temp:
        temp_name = temp.name
        with urlopen(url, timeout=180) as in_stream:
            if in_stream.status != 200:
                raise RuntimeError(f'HTTP {in_stream.status} when downloading {url}')
            copyfileobj(in_stream, temp)

    print('Download complete.')
    return temp_name


def _find_ini_file(base_path):
    """Find the INI file: env override > {script_name}.ini > update_arcade-organizer.ini > None."""
    env_ini = os.environ.get('INI_FILE', '')
    if env_ini:
        return env_ini

    script_ini = Path(os.path.realpath(__file__)).with_suffix('.ini')
    if script_ini.is_file():
        return str(script_ini)

    default_ini = Path(base_path) / 'Scripts' / 'update_arcade-organizer.ini'
    if default_ini.is_file():
        return str(default_ini)

    return str(default_ini)


def main():
    base_path = os.path.dirname(os.path.realpath(__file__))

    print(f'Arcade Organizer PC Launcher')
    print(f'Base path: {base_path}')
    print()

    temp_pyz = None
    result = 1
    try:
        temp_pyz = _fetch_pyz()

        # Add the pyz to sys.path so we can import from it
        sys.path.insert(0, temp_pyz)

        from update_all.arcade_organizer.arcade_organizer import ArcadeOrganizerService
        from update_all.logger import PrintLogger

        ini_file = _find_ini_file(base_path)
        print(f'INI file: {ini_file}')
        print()

        logger = PrintLogger()
        ao_service = ArcadeOrganizerService(logger)
        config = ao_service.make_arcade_organizer_config(ini_file, base_path, '')

        # Force NO_SYMLINKS on Windows since symlinks require elevated privileges
        if os.name == 'nt':
            config['NO_SYMLINKS'] = True

        success = ao_service.run_arcade_organizer_organize_all_mras(config)
        result = 0 if success else 1

    except Exception as e:
        print(f'ERROR: {e}')
        result = 1

    if temp_pyz:
        try:
            os.unlink(temp_pyz)
        except FileNotFoundError:
            pass

    if os.environ.get('PC_LAUNCHER_NO_WAIT') != '1':
        input('\nPress Enter to continue...')

    return result


if __name__ == '__main__':
    exit(main())
