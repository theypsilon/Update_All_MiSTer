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
from contextlib import contextmanager
from unittest.mock import patch

import update_all.main as main_module
import update_all.chip_id_linker as chip_id_linker_module
import update_all.update_all_service as update_all_service_module
from update_all.constants import KENV_UPDATE_ALL_MISTER_DB_URL, KENV_UPDATE_ALL_DOWNLOADER_PATH, \
    KENV_UPDATE_ALL_DOWNLOADER_URL, KENV_UPDATE_ALL_NON_INTERACTIVE, \
    KENV_UPDATE_ALL_DOWNLOADER_PYTHON_COMPATIBLE_PATH
from update_all.main import execute_update_all, initial_logfile_path, read_env
from update_all.update_all_service import UpdateAllServicePass


class TestMain(unittest.TestCase):
    def test_read_env___with_update_all_mister_url_override___includes_override(self):
        override = 'http://127.0.0.1:8765/update_all_db.json'

        with patch.dict(main_module.os.environ, {KENV_UPDATE_ALL_MISTER_DB_URL: override}):
            result = read_env('default-commit', 123.0)

        self.assertEqual(override, result[KENV_UPDATE_ALL_MISTER_DB_URL])

    def test_read_env___with_downloader_overrides___includes_path_and_url(self):
        path = '/tmp/fake_downloader'
        url = 'http://127.0.0.1:8765/downloader.pyz'
        python_compatible_path = '/tmp/python3.9'

        with patch.dict(main_module.os.environ, {
            KENV_UPDATE_ALL_DOWNLOADER_PATH: path,
            KENV_UPDATE_ALL_DOWNLOADER_URL: url,
            KENV_UPDATE_ALL_DOWNLOADER_PYTHON_COMPATIBLE_PATH: python_compatible_path,
        }):
            result = read_env('default-commit', 123.0)

        self.assertEqual(path, result[KENV_UPDATE_ALL_DOWNLOADER_PATH])
        self.assertEqual(url, result[KENV_UPDATE_ALL_DOWNLOADER_URL])
        self.assertEqual(python_compatible_path, result[KENV_UPDATE_ALL_DOWNLOADER_PYTHON_COMPATIBLE_PATH])

    def test_read_env___with_non_interactive_override___includes_override(self):
        with patch.dict(main_module.os.environ, {KENV_UPDATE_ALL_NON_INTERACTIVE: 'true'}):
            result = read_env('default-commit', 123.0)

        self.assertEqual('true', result[KENV_UPDATE_ALL_NON_INTERACTIVE])

    def test_initial_logfile_path___when_media_fat_log_dir_exists___returns_media_fat_path(self):
        with _replace(main_module.os.path, 'isdir', _FunctionStub(True)):
            result = initial_logfile_path()

        self.assertEqual('/media/fat/Scripts/.config/update_all/update_all.log', result)

    def test_initial_logfile_path___when_media_fat_log_dir_does_not_exist___returns_leaf_relative_path(self):
        with _replace(main_module.os.path, 'isdir', _FunctionStub(False)):
            result = initial_logfile_path()

        self.assertEqual('update_all.log', result)

    def test_execute_update_all___with_chip_id_linker_command___delegates_to_chip_id_linker_command(self):
        logger = _LoggerStub()
        local_repository_provider = _LocalRepositoryProviderStub()

        run_linker = _FunctionSpy(return_value=123)
        with _replace(chip_id_linker_module, 'run_chip_id_linker_command', run_linker):
            result = execute_update_all(
                logger,
                local_repository_provider,
                {},
                args=['update_all.pyz', '--chip-id-linker', '--blank-display', '--log', '/tmp/chipid.log'],
            )

        self.assertEqual(123, result)
        run_linker.assert_called_once_with(logger, ['--blank-display', '--log', '/tmp/chipid.log'])

    def test_execute_update_all___with_retroaccount_sync_argument___runs_retroaccount_sync_pass(self):
        logger = _LoggerStub()
        local_repository_provider = object()
        factory_class = _FactoryClassSpy()

        with _replace(update_all_service_module, 'UpdateAllServiceFactory', factory_class):
            result = execute_update_all(
                logger,
                local_repository_provider,
                {'ENV': 'value'},
                args=['update_all.pyz', '--retroaccount-sync'],
            )

        self.assertEqual(123, result)
        self.assertEqual((logger, local_repository_provider), factory_class.call)
        self.assertEqual({'ENV': 'value'}, factory_class.factory.env)
        self.assertEqual(UpdateAllServicePass.RetroAccountSync, factory_class.factory.service.run_pass)
        self.assertEqual(['Update All flow finished: exit_code=123.'], logger.debug_lines)


@contextmanager
def _replace(target, attribute, replacement):
    original = getattr(target, attribute)
    setattr(target, attribute, replacement)
    try:
        yield replacement
    finally:
        setattr(target, attribute, original)


class _FunctionStub:
    def __init__(self, return_value):
        self._return_value = return_value

    def __call__(self, *_args, **_kwargs):
        return self._return_value


class _FunctionSpy:
    def __init__(self, return_value=None):
        self._return_value = return_value
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self._return_value

    def assert_called_once_with(self, *args, **kwargs):
        if self.calls != [(args, kwargs)]:
            raise AssertionError(f'Expected one call with {(args, kwargs)}, got {self.calls}')


class _LoggerStub:
    def __init__(self):
        self.debug_lines = []

    def debug(self, message):
        self.debug_lines.append(message)


class _LocalRepositoryProviderStub:
    pass


class _FactoryClassSpy:
    def __init__(self):
        self.call = None
        self.factory = _FactoryStub()

    def __call__(self, logger, local_repository_provider):
        self.call = (logger, local_repository_provider)
        return self.factory


class _FactoryStub:
    def __init__(self):
        self.env = None
        self.service = _ServiceStub()

    def create(self, env):
        self.env = env
        return self.service


class _ServiceStub:
    def __init__(self):
        self.run_pass = None

    def full_run(self, run_pass):
        self.run_pass = run_pass
        return 123


if __name__ == '__main__':
    unittest.main()
