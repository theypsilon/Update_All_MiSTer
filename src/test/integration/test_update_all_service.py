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
from unittest.mock import MagicMock

from update_all.config import Config
from update_all.constants import FILE_mister_downloader_needs_reboot, EXIT_CODE_REQUIRES_EARLY_EXIT, COMMAND_SHOW_CHIP_ID_RESULT
from update_all.environment_setup import EnvironmentSetupResult
from update_all.local_store import LocalStore
from update_all.other import GenericProvider
from update_all.update_all_service import UpdateAllService, UpdateAllServicePass
from test.fake_filesystem import FileSystemFactory
from test.file_system_tester_state import FileSystemState
from test.update_all_service_tester import UpdateAllServiceFactoryTester, UpdateAllServiceTester, \
    default_env, EnvironmentSetupStub, default_databases, local_store


def tester(files=None, folders=None, config: Config = None, store: LocalStore = None, env_stub: EnvironmentSetupStub = None,
           settings_screen=None):
    state = FileSystemState(files=files, folders=folders)
    config_provider = GenericProvider[Config]()
    config_provider.initialize(config or Config(databases=default_databases()))
    store_provider = GenericProvider[LocalStore]()
    store_provider.initialize(store or local_store())

    return UpdateAllServiceTester(
        environment_setup=env_stub or EnvironmentSetupStub(),
        file_system=FileSystemFactory(state=state, config_provider=config_provider).create_for_system_scope(),
        config_provider=config_provider,
        store_provider=store_provider,
        settings_screen=settings_screen,
    ), state


class TestUpdateAllService(unittest.TestCase):
    def test_factory_create___on_default_environment___returns_update_all_service(self):
        self.assertIsInstance(UpdateAllServiceFactoryTester().create(default_env()), UpdateAllService)

    def test_full_run___on_default_environment___returns_0(self):
        sut, _ = tester()
        self.assertEqual(0, sut.full_run(UpdateAllServicePass.NewRun))

    def test_full_run___with_no_databases_and_no_arcade_organizer___returns_0(self):
        sut, _ = tester(config=Config(arcade_organizer=False))
        self.assertEqual(0, sut.full_run(UpdateAllServicePass.NewRun))

    def test_full_run___only_arcade_organizer___returns_0(self):
        sut, _ = tester(config=Config(arcade_organizer=True))
        self.assertEqual(0, sut.full_run(UpdateAllServicePass.NewRun))

    def test_full_run___only_downloader___returns_0(self):
        sut, _ = tester(config=Config(arcade_organizer=False, databases=default_databases()))
        self.assertEqual(0, sut.full_run(UpdateAllServicePass.NewRun))

    def test_full_run___only_downloader_without_linux___returns_0(self):
        sut, _ = tester(config=Config(arcade_organizer=False, databases=default_databases(), update_linux=False))
        self.assertEqual(0, sut.full_run(UpdateAllServicePass.NewRun))

    def test_full_run___when_reboot_is_needed___returns_0(self):
        sut, _ = tester(files={FILE_mister_downloader_needs_reboot: {'content': 'true'}})
        self.assertEqual(0, sut.full_run(UpdateAllServicePass.NewRun))

    def test_full_run___when_reboot_is_needed_but_is_disabled___returns_0(self):
        sut, _ = tester(
            files={FILE_mister_downloader_needs_reboot: {'content': 'true'}},
            config=Config(databases=default_databases(), autoreboot=False)
        )
        self.assertEqual(0, sut.full_run(UpdateAllServicePass.NewRun))

    def test_full_run___when_reboot_is_needed_but_is_not_mister___returns_0(self):
        sut, _ = tester(
            files={FILE_mister_downloader_needs_reboot: {'content': 'true'}},
            config=Config(databases=default_databases(), not_mister=True)
        )
        self.assertEqual(0, sut.full_run(UpdateAllServicePass.NewRun))

    def test_full_run___when_env_setup_requires_early_exit___returns_exit_code_requires_early_exit(self):
        stub = EnvironmentSetupStub(EnvironmentSetupResult(requires_early_exit=True))
        sut, _ = tester(config=Config(databases=default_databases(), transition_service_only=True), env_stub=stub)
        self.assertEqual(EXIT_CODE_REQUIRES_EARLY_EXIT, sut.full_run(UpdateAllServicePass.NewRun))

    def test_full_run___with_show_chip_id_result_command___opens_chip_id_result_menu_and_returns_without_update_flow(self):
        events = []
        settings_screen = MagicMock()
        settings_screen.load_chip_id_result_menu.side_effect = lambda: events.append('menu')
        sut, _ = tester(
            config=Config(databases=default_databases(), command=COMMAND_SHOW_CHIP_ID_RESULT),
            settings_screen=settings_screen,
        )
        sut._start_background_jobs = MagicMock(side_effect=lambda: events.append('start_background_jobs'))
        sut._hard_wait_background_jobs = MagicMock(side_effect=lambda: events.append('hard_wait_background_jobs'))

        result = sut.full_run(UpdateAllServicePass.NewRun)

        self.assertEqual(0, result)
        self.assertEqual(['menu'], events)
        sut._start_background_jobs.assert_not_called()
        settings_screen.load_chip_id_result_menu.assert_called_once_with()
        sut._hard_wait_background_jobs.assert_not_called()

    def test_full_run___with_show_chip_id_result_command_and_menu_failure___returns_without_update_flow(self):
        events = []
        settings_screen = MagicMock()
        settings_screen.load_chip_id_result_menu.side_effect = RuntimeError('boom')
        sut, _ = tester(
            config=Config(databases=default_databases(), command=COMMAND_SHOW_CHIP_ID_RESULT),
            settings_screen=settings_screen,
        )
        sut._start_background_jobs = MagicMock(side_effect=lambda: events.append('start_background_jobs'))
        sut._hard_wait_background_jobs = MagicMock(side_effect=lambda: events.append('hard_wait_background_jobs'))

        result = sut.full_run(UpdateAllServicePass.NewRun)

        self.assertEqual(0, result)
        self.assertEqual([], events)
        sut._start_background_jobs.assert_not_called()
        settings_screen.load_chip_id_result_menu.assert_called_once_with()
        sut._hard_wait_background_jobs.assert_not_called()
