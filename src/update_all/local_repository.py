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

from typing import TypedDict, Union
from urllib.parse import urlparse
from update_all.config import Config
from update_all.other import GenericProvider
from update_all.constants import FILE_update_all_zipped_storage, FILE_update_all_log, FILE_update_all_storage, \
    FILE_pocket_firmware_details_json
from update_all.local_store import LocalStore
from update_all.store_migrator import make_new_local_store


class FirmwareInfo(TypedDict):
    url: str
    version: str
    file: str
    md5: str
    size: float


class LocalRepository:

    def __init__(self, config_provider: GenericProvider[Config], logger, file_system, store_migrator):
        self._config_provider = config_provider
        self._logger = logger
        self._file_system = file_system
        self._store_migrator = store_migrator
        self._pocket_firmware_info = None

    def pocket_firmware_info(self) -> Union[FirmwareInfo, Exception]:
        if self._pocket_firmware_info is None:
            try:
                details = self._file_system.load_dict_from_file(FILE_pocket_firmware_details_json)
                assert (isinstance(details['url'], str))
                assert (isinstance(details['version'], str))
                assert (isinstance(details['file'], str))
                assert (isinstance(details['md5'], str))
                assert (isinstance(details['size'], float))
                assert (len(details.keys()) == 5)
                assert (float(details['version']) > 2.0)
                netloc = urlparse(details['url']).netloc
                assert (netloc == 'analogue.co' or netloc.endswith('.analogue.co'))
                self._pocket_firmware_info = details
            except Exception as e:
                self._pocket_firmware_info = e
        return self._pocket_firmware_info

    def load_store(self) -> LocalStore:
        self._logger.bench('Loading store...')

        local_store_props = None
        for store_file_path in (FILE_update_all_storage, FILE_update_all_zipped_storage):
            if self._file_system.is_file(store_file_path):
                try:
                    local_store_props = self._file_system.load_dict_from_file(store_file_path)
                    break
                except Exception as e:
                    self._logger.debug(e)
                    self._logger.print('Could not load store')

        if local_store_props is None:
            local_store_props = make_new_local_store(self._store_migrator)

        self._store_migrator.migrate(local_store_props)  # exception must be fixed, users are not modifying this by hand

        return LocalStore(local_store_props)

    def save_store(self, local_store_wrapper: LocalStore):
        if not local_store_wrapper.needs_save():
            self._logger.debug('Skipping local_store saving...')
            return

        local_store = local_store_wrapper.unwrap_props()

        self._file_system.make_dirs_parent(FILE_update_all_zipped_storage)
        self._file_system.save_json(local_store, FILE_update_all_storage)
        local_store_wrapper.mark_as_cleaned()

    def save_log_from_tmp(self, path):
        self._file_system.make_dirs_parent(FILE_update_all_log)
        self._file_system.copy(path, FILE_update_all_log)
