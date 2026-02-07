#!/usr/bin/env python3
# Copyright (c) 2022-2026 José Manuel Barroso Galindo <theypsilon@gmail.com>

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
  PC_LAUNCHER_NO_WAIT     Set to '1' to skip the "Press Enter" prompt
  INI_FILE                Path to the arcade organizer INI file
"""

import os
import sys
import hashlib
from pathlib import Path
from shutil import copyfileobj
from tempfile import NamedTemporaryFile
from urllib.request import urlopen


_PYZ_URL = 'https://github.com/theypsilon/Update_All_MiSTer/releases/latest/download/update_all.pyz'
_PYZ_SHA256_URL = 'https://github.com/theypsilon/Update_All_MiSTer/releases/latest/download/update_all.pyz.sha256'
_MAD_DB_URL = 'https://raw.githubusercontent.com/MiSTer-devel/ArcadeDatabase_MiSTer/refs/heads/db/mad_db.json.zip'
_MAD_DB_MD5_URL = 'https://raw.githubusercontent.com/MiSTer-devel/ArcadeDatabase_MiSTer/refs/heads/db/mad_db.json.zip.md5'
_LOCAL_PYZ_RELATIVE_PATH = Path('Scripts') / '.config' / 'update_all' / 'update_all.pyz'
_LOCAL_MAD_DB_RELATIVE_PATH = Path('Scripts') / '.config' / 'update_all' / 'mad_db.json.zip'


def _fetch_pyz():
    """Download or copy the update_all.pyz to a temp file. Returns the temp file path."""
    temp_name = _download_with_hash(_PYZ_URL, _PYZ_SHA256_URL, 'sha256', '.pyz')
    print('Download complete.')
    return temp_name


def _fetch_mad_db():
    temp_name = _download_with_hash(_MAD_DB_URL, _MAD_DB_MD5_URL, 'md5', '.json.zip')
    print('MAD_DB download complete.')
    return temp_name


def _download_with_hash(url: str, hash_url: str, algo: str, suffix: str) -> str:
    print(f'Downloading {url} ...')
    with NamedTemporaryFile(suffix=suffix, mode='wb', delete=False) as temp:
        temp_name = temp.name
        with urlopen(url, timeout=180) as in_stream:
            if in_stream.status != 200:
                raise RuntimeError(f'HTTP {in_stream.status} when downloading {url}')
            copyfileobj(in_stream, temp)

    print(f'Validating {algo.upper()} {hash_url} ...')
    with urlopen(hash_url, timeout=30) as hash_stream:
        if hash_stream.status != 200:
            raise RuntimeError(f'HTTP {hash_stream.status} when downloading {hash_url}')
        expected_text = hash_stream.read().decode().strip()

    expected_hash = expected_text.split()[0]
    hasher = hashlib.new(algo)
    with open(temp_name, 'rb') as fp:
        hasher.update(fp.read())
    actual_hash = hasher.hexdigest()

    if actual_hash != expected_hash:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise RuntimeError(f'Corrupted download: {algo.upper()} mismatch')

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
    temp_files = []
    result = 1
    try:
        local_pyz = Path(base_path) / _LOCAL_PYZ_RELATIVE_PATH
        if local_pyz.is_file():
            temp_pyz = str(local_pyz)
            print(f'Using local update_all.pyz: {local_pyz}')
        else:
            temp_pyz = _fetch_pyz()
            temp_files.append(temp_pyz)

        local_mad_db = Path(base_path) / _LOCAL_MAD_DB_RELATIVE_PATH
        if local_mad_db.is_file():
            print(f'Using local MAD_DB: {local_mad_db}')
        else:
            mad_db_path = _fetch_mad_db()
            temp_files.append(mad_db_path)
            os.environ['MAD_DB'] = mad_db_path

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

    for temp_file in temp_files:
        try:
            os.unlink(temp_file)
        except FileNotFoundError:
            pass

    if os.environ.get('PC_LAUNCHER_NO_WAIT') != '1':
        input('\nPress Enter to continue...')

    return result


if __name__ == '__main__':
    exit(main())
