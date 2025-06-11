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

import os
import hashlib
import shutil
import json
import tempfile
import re
import zipfile
import filecmp
from abc import ABC, abstractmethod
from pathlib import Path
from update_all.config import AllowDelete
from update_all.constants import K_ALLOW_DELETE, FOLDER_scripts_config_lc
from update_all.other import ClosableValue


class FileSystemFactory:
    def __init__(self, config, path_dictionary, logger):
        self._config = config
        self._path_dictionary = path_dictionary
        self._logger = logger
        self._unique_temp_filenames = set()
        self._unique_temp_filenames.add(None)

    def create_for_system_scope(self):
        return self.create_for_config(self._config)

    def create_for_config(self, config):
        return _FileSystem(config, self._path_dictionary, self._logger, self._unique_temp_filenames)


class FileSystem(ABC):

    @abstractmethod
    def temp_file(self):
        """interface"""

    @abstractmethod
    def temp_file_by_id(self, file_id):
        """interface"""

    @abstractmethod
    def clean_temp_files_with_ids(self):
        """interface"""

    @abstractmethod
    def unique_temp_filename(self):
        """interface"""

    @abstractmethod
    def resolve(self, path):
        """interface"""

    @abstractmethod
    def is_file(self, path):
        """interface"""

    @abstractmethod
    def is_folder(self, path):
        """interface"""

    @abstractmethod
    def compare_files(self, source, target) -> bool:
        """interface"""

    @abstractmethod
    def read_file_contents(self, path):
        """interface"""

    @abstractmethod
    def read_file_binary(self, path):
        """interface"""

    @abstractmethod
    def write_file_contents(self, path, content):
        """interface"""

    @abstractmethod
    def write_file_bytes(self, path, content_bytes):
        """interface"""

    @abstractmethod
    def touch(self, path):
        """interface"""

    @abstractmethod
    def move(self, source, target):
        """interface"""

    @abstractmethod
    def copy(self, source, target):
        """interface"""

    @abstractmethod
    def copy_fast(self, source, target):
        """interface"""

    def hash(self, path: str) -> str:
        """interface"""

    @abstractmethod
    def make_dirs(self, path):
        """interface"""

    @abstractmethod
    def make_dirs_parent(self, path):
        """interface"""

    @abstractmethod
    def folder_has_items(self, path):
        """interface"""

    @abstractmethod
    def folders(self):
        """interface"""

    @abstractmethod
    def remove_folder(self, path):
        """interface"""

    @abstractmethod
    def remove_non_empty_folder(self, path):
        """interface"""

    @abstractmethod
    def download_target_path(self, path):
        """interface"""

    @abstractmethod
    def unlink(self, path, verbose=True):
        """interface"""

    @abstractmethod
    def delete_previous(self, file):
        """interface"""

    @abstractmethod
    def load_dict_from_file(self, path, suffix=None):
        """interface"""

    @abstractmethod
    def save_json_on_zip(self, db, path):
        """interface"""

    @abstractmethod
    def save_json(self, db, path):
        """interface"""

    @abstractmethod
    def unzip_contents(self, file, path, contained_files):
        """interface"""


class _FileSystem(FileSystem):
    def __init__(self, config, path_dictionary, logger, unique_temp_filenames):
        self._config = config
        self._path_dictionary = path_dictionary
        self._logger = logger
        self._unique_temp_filenames = unique_temp_filenames
        self._temp_files_with_ids = {}

    def temp_file(self):
        return tempfile.NamedTemporaryFile(prefix='temp_file')

    def temp_file_by_id(self, file_id):
        if file_id not in self._temp_files_with_ids:
            self._temp_files_with_ids[file_id] = tempfile.NamedTemporaryFile()
        return self._temp_files_with_ids[file_id]

    def clean_temp_files_with_ids(self):
        for file_id in list(self._temp_files_with_ids):
            temp_file = self._temp_files_with_ids[file_id]
            temp_file.close()
            del self._temp_files_with_ids[file_id]

    def unique_temp_filename(self):
        name = None
        while name in self._unique_temp_filenames:
            name = os.path.join(tempfile._get_default_tempdir(), next(tempfile._get_candidate_names()))
        self._unique_temp_filenames.add(name)
        return ClosableValue(name, lambda: self._unique_temp_filenames.remove(name))

    def resolve(self, path):
        return str(Path(self._path(path)).resolve())

    def is_file(self, path):
        return os.path.isfile(self._path(path))

    def is_folder(self, path):
        return os.path.isdir(self._path(path))

    def compare_files(self, source, target) -> bool:
        return filecmp.cmp(self._path(source), self._path(target), shallow=False)

    def read_file_contents(self, path):
        with open(self._path(path), 'r') as f:
            return f.read()

    def read_file_binary(self, path):
        with open(self._path(path), 'rb') as f:
            return f.read()

    def write_file_contents(self, path, content):
        with open(self._path(path), 'w') as f:
            return f.write(content)

    def write_file_bytes(self, path, content_bytes):
        with open(self._path(path), 'wb') as f:
            return f.write(content_bytes)

    def touch(self, path):
        return Path(self._path(path)).touch()

    def move(self, source, target):
        self._makedirs(self._parent_folder(target))
        os.replace(self._path(source), self._path(target))

    def copy(self, source, target):
        return shutil.copyfile(self._path(source), self._path(target))

    def copy_fast(self, source, target):
        with open(self._path(source), 'rb') as fsource:
            with open(self._path(target), 'wb') as ftarget:
                shutil.copyfileobj(fsource, ftarget, length=1024 * 1024 * 4)

    def hash(self, path: str) -> str:
        return hash_file(self._path(path))

    def make_dirs(self, path):
        return self._makedirs(self._path(path))

    def make_dirs_parent(self, path):
        return self._makedirs(self._parent_folder(path))

    def _parent_folder(self, path):
        return absolute_parent_folder(self._path(path))

    @staticmethod
    def _makedirs(target):
        try:
            os.makedirs(target, exist_ok=True)
        except FileExistsError as e:
            if e.errno == 17:
                return
            raise e

    def folder_has_items(self, path):
        try:
            for _ in os.scandir(self._path(path)):
                return True

        except FileNotFoundError as e:
            self._ignore_error(e)
        except NotADirectoryError as e:
            self._ignore_error(e)

        return False

    def folders(self):
        raise Exception('folders Not implemented')

    def remove_folder(self, path):
#        if self._config.get()[K_ALLOW_DELETE] != AllowDelete.ALL:
#            return

        self._logger.print('Deleting empty folder %s' % path)
        try:
            os.rmdir(self._path(path))
        except FileNotFoundError as e:
            self._ignore_error(e)
        except NotADirectoryError as e:
            self._ignore_error(e)

    def _ignore_error(self, e):
        self._logger.debug(e)
        self._logger.debug('Ignoring error.')

    def remove_non_empty_folder(self, path):
#        if self._config.get()[K_ALLOW_DELETE] != AllowDelete.ALL:
#            return

        try:
            shutil.rmtree(self._path(path))
        except Exception as e:
            self._logger.debug(e)
            self._logger.debug('Ignoring error.')

    def download_target_path(self, path):
        return self._path(path)

    def unlink(self, path, verbose=True):
        verbose = verbose and not path.startswith('/tmp/')
#        if self._config.get()[K_ALLOW_DELETE] != AllowDelete.ALL:
#            if self._config.get()[K_ALLOW_DELETE] == AllowDelete.OLD_RBF and path[-4:].lower() == ".rbf":
#                return self._unlink(path, verbose)
#
#            return True

        return self._unlink(path, verbose)

    def delete_previous(self, file):
        if self._config.get()[K_ALLOW_DELETE] != AllowDelete.ALL:
            return True

        path = Path(self._path(file))
        if not self.is_folder(str(path.parent)):
            return

        regex = re.compile("^(.+_)[0-9]{8}([.][a-zA-Z0-9]+)$", )
        m = regex.match(path.name)
        if m is None:
            return

        g = m.groups()
        if g is None:
            return

        start = g[0].lower()
        ext = g[1].lower()

        deleted = False
        for child in path.parent.iterdir():
            name = child.name.lower()
            if name.startswith(start) and name.endswith(ext) and regex.match(name):
                child.unlink()
                deleted = True

        if deleted:
            self._logger.print('Deleted previous "%s"* files.' % start)

    def load_dict_from_file(self, path, suffix=None):
        path = self._path(path)
        if suffix is None:
            suffix = Path(path).suffix.lower()
        if suffix == '.json':
            return _load_json(path)
        elif suffix == '.zip':
            return _load_json_from_zip(path)
        else:
            raise Exception('File type "%s" not supported' % suffix)

    def save_json_on_zip(self, db, path):
        json_name = Path(path).stem
        zip_path = Path(self._path(path)).absolute()

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.writestr(json_name, json.dumps(db))

    def save_json(self, db, path):
        with open(self._path(path), 'w') as f:
            json.dump(db, f)

    def unzip_contents(self, file, path, contained_files):
        raise NotImplementedError('No need on update_all')

    def _unlink(self, path, verbose):
        if verbose:
            self._logger.print('Removing %s' % path)
        try:
            Path(self._path(path)).unlink()
            return True
        except FileNotFoundError as _:
            return False

    def _path(self, path):
        if path[0] == '/':
            return path

        first_part = self._config.get().base_path

        path_lower = path.lower()
        if path_lower in self._path_dictionary:
            first_part = self._path_dictionary[path_lower]

        if path_lower.startswith(FOLDER_scripts_config_lc):
            first_part = self._config.get().base_system_path

        return '%s/%s' % (first_part, path)


class InvalidFileResolution(Exception):
    pass


def hash_file(path: str) -> str:
    with open(path, "rb") as f:
        file_hash = hashlib.md5()
        chunk = f.read(8192)
        while chunk:
            file_hash.update(chunk)
            chunk = f.read(8192)
        return file_hash.hexdigest()


def absolute_parent_folder(absolute_path):
    return str(Path(absolute_path).parent)


def _load_json_from_zip(path):
    with zipfile.ZipFile(path) as jsonzipf:
        namelist = jsonzipf.namelist()
        if len(namelist) != 1:
            raise Exception('Could not load "%s", because it has %s elements!' % (path, len(namelist)))
        with jsonzipf.open(namelist[0]) as store_json_file:
            return json.loads(store_json_file.read())


def _load_json(file_path):
    with open(file_path, "r") as f:
        return json.loads(f.read())
