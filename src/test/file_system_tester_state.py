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
from update_all.config import Config
from update_all.constants import MEDIA_FAT


class FileSystemState:
    def __init__(self, files=None, folders=None, base_path=None, config=None, path_dictionary=None):
        self.path_dictionary = path_dictionary if path_dictionary is not None else {}
        self.config = config if config is not None else Config(base_path=base_path or MEDIA_FAT)
        base_path = _fix_base_path(self.config.base_path)
        self.files = _fs_paths(files, base_path) if files is not None else {}
        self.folders = _fs_folders(folders, base_path) if folders is not None else {}
        self.temp_files_with_ids = {}

    def add_file(self, base_path, file, description):
        if base_path is None:
            base_path = self.config.base_path

        if base_path is not self.config.base_path:
            self.set_non_base_path(base_path, file)

        path = file.lower() if file[0] == '/' else base_path.lower() + '/' + file.lower()

        self.files[path] = self.fix_description(file, description)
        return self

    def set_non_base_path(self, base, file):
        self.path_dictionary[file.lower()] = base

    def add_full_file_path(self, path, fixed_description):
        self.files[path.lower()] = fixed_description
        return self

    def add_folder(self, base_path, folder, description=None):
        if base_path is None:
            base_path = self.config.base_path

        path = folder.lower() if folder[0] == '/' else base_path.lower() + '/' + folder.lower()

        self.folders[path] = {} if description is None else description
        return self

    def add_folders(self, folders):
        for folder, description in folders.items():
            self.add_folder(base_path=None, folder=folder, description=description)

        return self

    def add_full_folder_path(self, path):
        self.folders[path.lower()] = {}
        return self

    @staticmethod
    def fix_description(file, description):
        fixed_description = {
            'hash': description['hash'] if 'hash' in description else file,
            'size': description['size'] if 'size' in description else 1
        }

        if 'unzipped_json' in description:
            fixed_description['unzipped_json'] = description['unzipped_json']
        if 'zipped_files' in description:
            fixed_description['zipped_files'] = description['zipped_files']
        if 'content' in description:
            fixed_description['content'] = description['content']

        return fixed_description


def _fs_paths(paths, base_path):
    return {k.lower() if k[0] == '/' else base_path + k.lower(): _clean_description(v) for k, v in paths.items()}


def _fs_folders(paths, base_path):
    return {p.lower() if p[0] == '/' else base_path + p.lower(): {} for p in paths}


def _fix_base_path(base_path):
    return base_path + '/' if (base_path != '' and base_path[-1] != '/') else base_path


def _fs_system_paths(paths):
    paths = {p: True for p in paths} if isinstance(paths, list) else paths
    if not isinstance(paths, dict):
        raise Exception('system_paths should be a dict.')
    return paths


def _clean_description(description):
    result = {}
    if 'hash' in description:
        result['hash'] = description['hash']
    if 'size' in description:
        result['size'] = description['size']
    if 'unzipped_json' in description:
        result['unzipped_json'] = description['unzipped_json']
    if 'zipped_files' in description:
        result['zipped_files'] = description['zipped_files']
    if 'content' in description:
        result['content'] = description['content']
    return result
