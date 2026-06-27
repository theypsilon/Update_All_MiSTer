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

from update_all.config import Config
from update_all.constants import FILE_mister_downloader_needs_reboot, EXIT_CODE_REQUIRES_EARLY_EXIT, COMMAND_SHOW_CHIP_ID_RESULT, \
    FILE_MiSTer_ini
from update_all.environment_setup import EnvironmentSetupResult
from update_all.local_store import LocalStore
from update_all.other import GenericProvider
from update_all.update_output import LtsvUpdateOutput
from update_all.update_all_service import UpdateAllService, UpdateAllServicePass
from update_all.zaparoo_service import FILE_zaparoo_frontend
from test.fake_filesystem import FileSystemFactory
from test.file_system_tester_state import FileSystemState
from test.update_all_service_tester import UpdateAllServiceFactoryTester, UpdateAllServiceTester, \
    default_env, EnvironmentSetupStub, default_databases, local_store, RetroAccountServiceTester, SettingsScreenStub, \
    UpdateAllServiceFlowTester
from test.zaparoo_service_tester import ZaparooServiceTester


def tester(files=None, folders=None, config: Config = None, store: LocalStore = None, env_stub: EnvironmentSetupStub = None,
           settings_screen=None, zaparoo_service=None, retroaccount=None, service_type=UpdateAllServiceTester):
    state = FileSystemState(files=files, folders=folders)
    config_provider = GenericProvider[Config]()
    config_provider.initialize(config or Config(databases=default_databases()))
    store_provider = GenericProvider[LocalStore]()
    store_provider.initialize(store or local_store())

    return service_type(
        environment_setup=env_stub or EnvironmentSetupStub(),
        file_system=FileSystemFactory(state=state, config_provider=config_provider).create_for_system_scope(),
        config_provider=config_provider,
        store_provider=store_provider,
        settings_screen=settings_screen,
        zaparoo_service=zaparoo_service,
        retroaccount=retroaccount,
    ), state


class TestUpdateAllService(unittest.TestCase):
    def test_factory_create___on_default_environment___returns_update_all_service(self):
        self.assertIsInstance(UpdateAllServiceFactoryTester().create(default_env()), UpdateAllService)

    def test_full_run___on_default_environment___returns_0(self):
        sut, _ = tester()
        self.assertEqual(0, sut.full_run(UpdateAllServicePass.NewRun))

    def test_full_run___applies_zaparoo_frontend_preference_after_hard_waiting_background_jobs(self):
        sut, _ = tester(service_type=UpdateAllServiceFlowTester)

        self.assertEqual(0, sut.full_run(UpdateAllServicePass.NewRun))

        self.assertEqual([
            'start_background_jobs',
            'hard_wait_background_jobs',
            'apply_zaparoo_frontend_preference',
            'show_outro',
        ], sut.events)

    def test_apply_zaparoo_frontend_preference___when_both_zaparoo_flags_are_disabled___does_not_call_zaparoo_service(self):
        zaparoo_service = ZaparooServiceTester()
        sut, _ = tester(zaparoo_service=zaparoo_service)

        sut._apply_zaparoo_frontend_preference()

        self.assertEqual([], zaparoo_service.calls)

    def test_apply_zaparoo_frontend_preference___when_frontend_active_is_enabled___keeps_frontend_active(self):
        store = local_store()
        store.set_zaparoo_frontend_active(True)
        zaparoo_service = ZaparooServiceTester(files={
            FILE_zaparoo_frontend: {'content': 'frontend'},
        })
        sut, _ = tester(store=store, zaparoo_service=zaparoo_service)

        sut._apply_zaparoo_frontend_preference()

        self.assertEqual(['apply_frontend_activation'], zaparoo_service.calls)

    def test_apply_zaparoo_frontend_preference___when_frontend_active_is_disabled___removes_zaparoo_frontend_main(self):
        store = local_store()
        store.generic_set('zaparoo_frontend_active', False)
        zaparoo_service = ZaparooServiceTester(files={
            FILE_MiSTer_ini: {'content': '[mister]\nmain=zaparoo/MiSTer_Zaparoo\nfoo=bar\n'},
        })
        sut, _ = tester(store=store, zaparoo_service=zaparoo_service)

        sut._apply_zaparoo_frontend_preference()

        self.assertEqual(
            '[mister]\nfoo=bar\n',
            zaparoo_service.file_system.read_file_contents(FILE_MiSTer_ini),
        )

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
        settings_screen = SettingsScreenStub(load_chip_id_result_menu_result='menu')
        sut, _ = tester(
            config=Config(databases=default_databases(), command=COMMAND_SHOW_CHIP_ID_RESULT),
            settings_screen=settings_screen,
            service_type=UpdateAllServiceFlowTester,
        )

        result = sut.full_run(UpdateAllServicePass.NewRun)

        self.assertEqual(0, result)
        self.assertEqual([], sut.events)
        self.assertEqual(1, settings_screen.load_chip_id_result_menu_calls)

    def test_full_run___with_show_chip_id_result_command_and_menu_failure___returns_without_update_flow(self):
        settings_screen = SettingsScreenStub(load_chip_id_result_menu_result=RuntimeError('boom'))
        sut, _ = tester(
            config=Config(databases=default_databases(), command=COMMAND_SHOW_CHIP_ID_RESULT),
            settings_screen=settings_screen,
            service_type=UpdateAllServiceFlowTester,
        )

        result = sut.full_run(UpdateAllServicePass.NewRun)

        self.assertEqual(0, result)
        self.assertEqual([], sut.events)
        self.assertEqual(1, settings_screen.load_chip_id_result_menu_calls)

    def test_full_run___with_retroaccount_sync_pass___syncs_and_returns_without_update_flow(self):
        env_stub = EnvironmentSetupStub()
        retroaccount = RetroAccountServiceTester()
        sut, _ = tester(
            config=Config(databases=default_databases()),
            env_stub=env_stub,
            retroaccount=retroaccount,
            service_type=UpdateAllServiceFlowTester,
        )

        result = sut.full_run(UpdateAllServicePass.RetroAccountSync)

        self.assertEqual(0, result)
        self.assertEqual([], sut.events)
        self.assertEqual(1, len(retroaccount.mister_sync_calls))
        self.assertIsInstance(retroaccount.mister_sync_calls[0], LtsvUpdateOutput)
        self.assertEqual(1, len(env_stub.setup_environment_calls))
        self.assertIs(retroaccount.mister_sync_calls[0], env_stub.setup_environment_calls[0][1])
