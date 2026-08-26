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
import unittest

from test.fake_filesystem import FileSystemFactory as FakeFileSystemFactory
from test.file_system_tester_state import FileSystemState
from test.logger_tester import NoLogger
from update_all.config import Config
from update_all.constants import FILE_MiSTer_ini, FILE_MiSTer_ini_update_all_backup
from update_all.file_system import FileSystemFactory
from update_all.other import GenericProvider


_BASE_PATH = '/media/usb0'
_BASE_SYSTEM_PATH = '/media/fat'

# The staging and backup siblings MisterIniRepository derives from the target path. They must
# resolve to the same drive as MiSTer.ini itself, or committing an edit would move across devices.
_MISTER_INI_SIBLINGS = [
    f'.{FILE_MiSTer_ini}.new',
    FILE_MiSTer_ini_update_all_backup,
    f'{FILE_MiSTer_ini_update_all_backup}.new',
]


class TestFileSystemPathResolution(unittest.TestCase):

    def test_resolve___mister_ini___uses_base_path(self):
        self.assertEqual(f'{_BASE_PATH}/{FILE_MiSTer_ini}', _resolve(FILE_MiSTer_ini))

    def test_resolve___mister_ini_staging_and_backup_siblings___land_on_the_same_drive_as_mister_ini(self):
        for path in _MISTER_INI_SIBLINGS:
            with self.subTest(path=path):
                self.assertEqual(f'{_BASE_PATH}/{path}', _resolve(path))

    def test_resolve___mister_ini_alt_config_variants___use_base_path(self):
        for path in ['MiSTer_alt1.ini', '.MiSTer_alt1.ini.new']:
            with self.subTest(path=path):
                self.assertEqual(f'{_BASE_PATH}/{path}', _resolve(path))

    def test_resolve___scripts_config_files___use_base_system_path(self):
        path = 'Scripts/.config/update_all/update_all.json'
        self.assertEqual(f'{_BASE_SYSTEM_PATH}/{path}', _resolve(path))

    def test_resolve___downloader_ini___uses_base_path(self):
        self.assertEqual(f'{_BASE_PATH}/downloader.ini', _resolve('downloader.ini'))

    def test_resolve___content_paths___use_base_path(self):
        for path in ['games/mame/jtbeta.zip', '_Arcade/mame/jtbeta.zip', 'Scripts/update_all.sh']:
            with self.subTest(path=path):
                self.assertEqual(f'{_BASE_PATH}/{path}', _resolve(path))

    def test_resolve___absolute_paths___are_returned_untouched(self):
        for path in ['/media/fat/retroachievements.cfg', '/tmp/downloader_run_signal']:
            with self.subTest(path=path):
                self.assertEqual(path, _resolve(path))

    def test_resolve___fake_filesystem___picks_the_same_drive_as_the_production_one(self):
        # Both implementations carry their own copy of this rule; keep them from drifting.
        # The fake lower-cases paths, so only the resolved drive is comparable.
        paths = [
            FILE_MiSTer_ini, *_MISTER_INI_SIBLINGS, 'MiSTer_alt1.ini',
            'Scripts/.config/update_all/update_all.json', 'downloader.ini',
            'games/mame/jtbeta.zip', '/tmp/downloader_run_signal',
        ]
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(_drive_of(_resolve(path)), _drive_of(_fake_resolve(path)))


def _config() -> Config:
    return Config(base_path=_BASE_PATH, base_system_path=_BASE_SYSTEM_PATH)


def _resolve(path: str) -> str:
    config_provider = GenericProvider[Config]()
    config_provider.initialize(_config())
    return FileSystemFactory(config_provider, {}, NoLogger()).create_for_system_scope().resolve(path)


def _fake_resolve(path: str) -> str:
    state = FileSystemState(config=_config())
    return FakeFileSystemFactory(state=state).create_for_system_scope().resolve(path)


def _drive_of(resolved_path: str) -> str:
    return '/'.join(resolved_path.split('/')[:3])


if __name__ == '__main__':
    unittest.main()
