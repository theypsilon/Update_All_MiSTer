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

from test.main_tester import MainTester
from update_all.constants import KENV_UPDATE_ALL_MISTER_DB_URL, KENV_UPDATE_ALL_DOWNLOADER_PATH, \
    KENV_UPDATE_ALL_DOWNLOADER_URL, KENV_UPDATE_ALL_NON_INTERACTIVE, \
    KENV_UPDATE_ALL_DOWNLOADER_PYTHON_COMPATIBLE_PATH, EXIT_CODE_REQUIRES_EARLY_EXIT
from update_all.environment_setup import EnvironmentSetupResult
from update_all.update_output import LtsvUpdateOutput
from update_all.update_all_service import UpdateAllServicePass


class TestMain(unittest.TestCase):
    def setUp(self):
        self.main = MainTester()

    def test_read_env___with_update_all_mister_url_override___includes_override(self):
        override = 'http://127.0.0.1:8765/update_all_db.json'

        result = self.main.read_env({KENV_UPDATE_ALL_MISTER_DB_URL: override})

        self.assertEqual(override, result[KENV_UPDATE_ALL_MISTER_DB_URL])

    def test_read_env___with_downloader_overrides___includes_path_and_url(self):
        environment = {
            KENV_UPDATE_ALL_DOWNLOADER_PATH: '/tmp/fake_downloader',
            KENV_UPDATE_ALL_DOWNLOADER_URL: 'http://127.0.0.1:8765/downloader.pyz',
            KENV_UPDATE_ALL_DOWNLOADER_PYTHON_COMPATIBLE_PATH: '/tmp/python3.9',
        }

        result = self.main.read_env(environment)

        for key, value in environment.items():
            self.assertEqual(value, result[key])

    def test_read_env___with_non_interactive_override___includes_override(self):
        result = self.main.read_env({KENV_UPDATE_ALL_NON_INTERACTIVE: 'true'})

        self.assertEqual('true', result[KENV_UPDATE_ALL_NON_INTERACTIVE])

    def test_execute_update_all___with_chip_id_linker_command___delegates_to_chip_id_linker_command(self):
        process, loaded_modules = self.main.run_linker_help()

        self.assertEqual(0, process.returncode, process.stderr)
        self.assertIn('Update All FPGA ID linker launcher', process.stdout)
        self.assertIn('--blank-display', process.stdout)
        self.assertIn('--zaparoo-console-lease', process.stdout)
        self.assertIn('update_all.chip_id_linker', loaded_modules)
        self.assertNotIn('update_all.update_all_service', loaded_modules)
        self.assertNotIn('update_all.settings_screen', loaded_modules)
        self.assertNotIn('update_all.retroaccount', loaded_modules)

    def test_linker_package_imports_only_shared_primitives(self):
        loaded_modules = self.main.loaded_application_modules('update_all.chip_id_linker')

        outside_package = {name for name in loaded_modules
                           if name != 'update_all.chip_id_linker' and not name.startswith('update_all.chip_id_linker.')}
        self.assertEqual({'update_all.constants', 'update_all.logger', 'update_all.other'}, outside_package)

    def test_normal_update_service_does_not_import_linker_package(self):
        loaded_modules = self.main.loaded_application_modules('update_all.update_all_service')

        self.assertFalse(any(name == 'update_all.chip_id_linker' or name.startswith('update_all.chip_id_linker.')
                             for name in loaded_modules), loaded_modules)

    def test_run_command___with_retroaccount_sync_argument___runs_retroaccount_sync_pass(self):
        service = self.main.create_update_all_service()

        result = service.run_command(['update_all.pyz', '--retroaccount-sync'])

        self.assertEqual(0, result)
        self.assertEqual(1, len(self.main.retroaccount.mister_sync_calls))
        self.assertIsInstance(self.main.retroaccount.mister_sync_calls[0], LtsvUpdateOutput)
        self.assertIn('Update All flow started: pass=RetroAccountSync.', self.main.logger.debug_lines)
        self.assertEqual('Update All flow finished: exit_code=0.', self.main.logger.debug_lines[-1])

    def test_run_command_preserves_normal_run_modes(self):
        for args, expected in (([], UpdateAllServicePass.NewRun),
                               (['--continue'], UpdateAllServicePass.Continue),
                               (['--no-continue'], UpdateAllServicePass.NewRunNonStop),
                               (['--unknown'], UpdateAllServicePass.NewRun)):
            with self.subTest(args=args):
                main = MainTester()
                service = main.create_update_all_service()

                result = service.run_command(['update_all.pyz'] + args)

                self.assertEqual(0, result)
                self.assertIn(f'Update All flow started: pass={expected.name}.', main.logger.debug_lines)
                self.assertEqual('Update All flow finished: exit_code=0.', main.logger.debug_lines[-1])

    def test_run_command_preserves_service_exit_code(self):
        service = self.main.create_update_all_service(EnvironmentSetupResult(requires_early_exit=True))

        result = service.run_command(['update_all.pyz', '--retroaccount-sync'])

        self.assertEqual(EXIT_CODE_REQUIRES_EARLY_EXIT, result)
        self.assertEqual([], self.main.retroaccount.mister_sync_calls)
        self.assertEqual(f'Update All flow finished: exit_code={result}.', self.main.logger.debug_lines[-1])
