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
import json
import unittest

from test.fake_filesystem import FileSystemFactory
from test.fetcher_stub import FetcherStub
from test.logger_tester import NoLogger
from test.spy_os_utils import SpyOsUtils
from test.update_all_service_tester import IniRepositoryTester
from update_all.config import Config
from update_all.constants import FILE_downloader_fingerprints_json
from update_all.downloader_service import DownloaderService
from update_all.other import GenericProvider
from update_all.uninstall_db_service import UninstallDbService


_DEFAULT_INSTALLED_AFTER = object()


def _sut(os_utils, config=None, installed_db_ids=(), installed_after=_DEFAULT_INSTALLED_AFTER):
    file_system = FileSystemFactory.from_state(files={
        FILE_downloader_fingerprints_json: {
            'content': json.dumps({db_id: {} for db_id in installed_db_ids}),
        },
    }).create_for_system_scope()
    config_provider = GenericProvider[Config]()
    config = config or Config()
    config_provider.initialize(config)
    logger = NoLogger()
    ini_repository = IniRepositoryTester(file_system=file_system)
    downloader_service = DownloaderService(
        logger,
        file_system,
        os_utils,
        ini_repository,
        FetcherStub(config_provider=config_provider),
    )

    if installed_after is _DEFAULT_INSTALLED_AFTER:
        installed_after = () if os_utils.execute_process_return_code == 0 else installed_db_ids

    def update_fingerprints_after_downloader():
        if installed_after is None:
            file_system.unlink(FILE_downloader_fingerprints_json, verbose=False)
        elif isinstance(installed_after, str):
            file_system.write_file_contents(FILE_downloader_fingerprints_json, installed_after)
        else:
            file_system.write_file_contents(
                FILE_downloader_fingerprints_json,
                json.dumps({db_id: {} for db_id in installed_after}),
            )

    os_utils.execute_process_action = update_fingerprints_after_downloader
    return UninstallDbService(
        ini_repository,
        config_provider,
        downloader_service,
        file_system,
        logger,
    ), config


class TestUninstallDbService(unittest.TestCase):
    def test_uninstall___runs_all_installed_database_ids_in_one_downloader_command(self):
        os_utils = SpyOsUtils()
        config = Config(databases={'distribution_mister', 'jtcores'})
        sut, _ = _sut(os_utils, config, ['distribution_mister', 'jtcores'])

        return_code = sut.uninstall(['distribution_mister', 'jtcores'])

        self.assertEqual(0, return_code)
        _launcher, env, _quiet, args = os_utils.calls_to_execute_process[0]
        self.assertEqual(['--uninstall', 'distribution_mister', 'jtcores'], args)
        self.assertEqual('0', env['ALLOW_REBOOT'])
        self.assertIn('DOWNLOADER_INI_PATH', env)

    def test_uninstall___when_forced___passes_force_to_downloader(self):
        os_utils = SpyOsUtils()
        sut, _ = _sut(os_utils, installed_db_ids=['distribution_mister'])

        self.assertEqual(0, sut.uninstall(['distribution_mister'], force=True))

        _launcher, _env, _quiet, args = os_utils.calls_to_execute_process[0]
        self.assertEqual(['--uninstall', 'distribution_mister', '--force'], args)

    def test_uninstall___with_no_database_ids___returns_success_without_running_downloader(self):
        os_utils = SpyOsUtils()
        sut, _ = _sut(os_utils)

        self.assertEqual(0, sut.uninstall([]))

        self.assertEqual([], os_utils.calls_to_execute_process)

    def test_uninstall___with_only_not_installed_database_ids___returns_success_without_running_downloader(self):
        os_utils = SpyOsUtils()
        config = Config(
            database_sources={'distribution_mister': ['downloader/dropins.ini']},
        )
        sut, config = _sut(os_utils, config)

        self.assertEqual(0, sut.uninstall(['distribution_mister', 'jtcores']))

        self.assertEqual([], os_utils.calls_to_execute_process)
        self.assertFalse(config.is_database_enabled('distribution_mister'))
        self.assertFalse(config.is_database_enabled('jtcores'))
        self.assertEqual(
            ['downloader/dropins.ini'],
            config.database_sources['distribution_mister'],
        )

    def test_uninstall___filters_installed_database_ids_case_insensitively(self):
        os_utils = SpyOsUtils()
        config = Config(databases={'jtcores'})
        sut, _ = _sut(os_utils, config, ['distribution_mister'])

        self.assertEqual(0, sut.uninstall(['DISTRIBUTION_MISTER', 'jtcores']))

        _launcher, _env, _quiet, args = os_utils.calls_to_execute_process[0]
        self.assertEqual(['--uninstall', 'DISTRIBUTION_MISTER'], args)

    def test_uninstall___includes_disabled_but_installed_manual_databases(self):
        os_utils = SpyOsUtils()
        config = Config(databases={'ajgowans/manualsdb-turbografxcd'})
        installed_db_ids = [
            'ajgowans/manualsdb-3do',
            'ajgowans/manualsdb-megadrive',
            'ajgowans/manualsdb-turbografxcd',
        ]
        sut, _ = _sut(os_utils, config, installed_db_ids)

        self.assertEqual(0, sut.uninstall([
            'ajgowans/manualsdb-3do',
            'ajgowans/manualsdb-megadrive',
            'ajgowans/manualsdb-pokemonmini',
            'ajgowans/manualsdb-turbografxcd',
        ]))

        _launcher, _env, _quiet, args = os_utils.calls_to_execute_process[0]
        self.assertEqual([
            '--uninstall',
            'ajgowans/manualsdb-3do',
            'ajgowans/manualsdb-megadrive',
            'ajgowans/manualsdb-turbografxcd',
        ], args)

    def test_uninstall___returns_the_downloader_error_code(self):
        os_utils = SpyOsUtils()
        os_utils.execute_process_return_code = 1
        config = Config(databases={'distribution_mister'})
        sut, _ = _sut(os_utils, config, ['distribution_mister'])

        self.assertEqual(1, sut.uninstall(['distribution_mister']))

    def test_uninstall___on_success___clears_stale_sources_for_all_uninstalled_database_ids(self):
        os_utils = SpyOsUtils()
        config = Config(
            databases={'MultiDatabases/duke3d', 'JTCORES'},
            database_sources={
                'multidatabases/duke3d': ['downloader/dropins.ini'],
                'jtcores': ['downloader/custom.ini'],
            },
        )
        sut, config = _sut(
            os_utils,
            config,
            ['MultiDatabases/duke3d', 'JTCORES'],
        )

        self.assertEqual(0, sut.uninstall(['multidatabases/duke3d', 'JTCORES']))

        self.assertFalse(config.is_database_enabled('MultiDatabases/duke3d'))
        self.assertFalse(config.is_database_enabled('jtcores'))
        self.assertNotIn('multidatabases/duke3d', config.database_sources)
        self.assertNotIn('jtcores', config.database_sources)

    def test_uninstall___on_failure___preserves_sources_in_config(self):
        os_utils = SpyOsUtils()
        os_utils.execute_process_return_code = 1
        config = Config(
            databases={'MultiDatabases/duke3d'},
            database_sources={'multidatabases/duke3d': ['downloader/dropins.ini']},
        )
        sut, config = _sut(os_utils, config, ['MultiDatabases/duke3d'])

        self.assertEqual(1, sut.uninstall(['multidatabases/duke3d']))

        self.assertTrue(config.is_database_enabled('MultiDatabases/duke3d'))
        self.assertEqual(
            ['downloader/dropins.ini'],
            config.database_sources['multidatabases/duke3d'],
        )

    def test_uninstall___when_a_batch_fails___leaves_reconciliation_to_the_caller(self):
        os_utils = SpyOsUtils()
        os_utils.execute_process_return_code = 1
        config = Config(databases={'MultiDatabases/duke3d', 'MultiDatabases/mister-quake'})
        sut, config = _sut(
            os_utils,
            config,
            ['MultiDatabases/duke3d', 'MultiDatabases/mister-quake'],
            installed_after=['MultiDatabases/mister-quake'],
        )

        return_code = sut.uninstall(['MultiDatabases/duke3d', 'MultiDatabases/mister-quake'])

        self.assertEqual(1, return_code)
        self.assertTrue(config.is_database_enabled('MultiDatabases/duke3d'))
        self.assertTrue(config.is_database_enabled('MultiDatabases/mister-quake'))

    def test_uninstall___after_partial_batch___a_retry_passes_only_the_database_still_installed(self):
        os_utils = SpyOsUtils()
        os_utils.execute_process_return_code = 22
        installed_after = ['MultiDatabases/mister-quake']
        config = Config(databases={'MultiDatabases/duke3d', 'MultiDatabases/mister-quake'})
        sut, config = _sut(
            os_utils,
            config,
            ['MultiDatabases/duke3d', 'MultiDatabases/mister-quake'],
            installed_after=installed_after,
        )

        first_return_code = sut.uninstall(['MultiDatabases/duke3d', 'MultiDatabases/mister-quake'])
        installed_after.clear()
        os_utils.execute_process_return_code = 0
        second_return_code = sut.uninstall(
            ['MultiDatabases/duke3d', 'MultiDatabases/mister-quake'],
            force=True,
        )

        self.assertEqual(22, first_return_code)
        self.assertEqual(0, second_return_code)
        self.assertEqual(
            ['--uninstall', 'MultiDatabases/mister-quake', '--force'],
            os_utils.calls_to_execute_process[1][3],
        )
        self.assertTrue(config.is_database_enabled('MultiDatabases/duke3d'))
        self.assertFalse(config.is_database_enabled('MultiDatabases/mister-quake'))
