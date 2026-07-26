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
from concurrent.futures import Future
from typing import Optional

from update_all.config import Config
from update_all.constants import FILE_mister_downloader_needs_reboot, EXIT_CODE_REQUIRES_EARLY_EXIT, \
    COMMAND_SHOW_CHIP_ID_RESULT, FILE_update_all_pyz, FILE_settings_screen_model_json_zip, \
    FILE_update_all_early_update_resume, EXIT_CODE_CAN_CONTINUE, BACKGROUND_JOBS_SOFT_TIMEOUT
from update_all.countdown import CountdownOutcome
from update_all.environment_setup import EnvironmentSetupResult
from update_all.local_store import LocalStore
from update_all.other import GenericProvider
from update_all.update_all_background_jobs_service import UpdateAllEarlyUpdateCheck
from update_all.update_output import LtsvUpdateOutput
from update_all.update_all_service import UpdateAllService, UpdateAllServicePass
from test.countdown_stub import CountdownStub
from test.fake_filesystem import FileSystemFactory
from test.fetcher_stub import FetcherStub
from test.file_system_tester_state import FileSystemState
from test.logger_tester import LoggerSpy
from test.update_all_background_jobs_service_tester import UpdateAllBackgroundJobsServiceTester
from test.update_all_service_tester import UpdateAllServiceFactoryTester, UpdateAllServiceTester, \
    default_env, EnvironmentSetupStub, default_databases, local_store, RetroAccountServiceTester, SettingsScreenStub, \
    UpdateAllServiceFlowTester


def tester(files=None, folders=None, config: Config = None, store: LocalStore = None, env_stub: EnvironmentSetupStub = None,
           settings_screen=None, zaparoo_service=None, retroaccount=None, service_type=UpdateAllServiceTester,
           countdown=None, downloader_service=None, fetcher=None, logger=None):
    state = FileSystemState(files=files, folders=folders)
    config_provider = GenericProvider[Config]()
    config_provider.initialize(config or Config(databases=default_databases()))
    store_provider = GenericProvider[LocalStore]()
    store_provider.initialize(store or local_store())

    return service_type(
        logger=logger,
        environment_setup=env_stub or EnvironmentSetupStub(),
        file_system=FileSystemFactory(state=state, config_provider=config_provider).create_for_system_scope(),
        config_provider=config_provider,
        store_provider=store_provider,
        settings_screen=settings_screen,
        zaparoo_service=zaparoo_service,
        retroaccount=retroaccount,
        countdown=countdown,
        downloader_service=downloader_service,
        fetcher=fetcher,
    ), state


class TestUpdateAllService(unittest.TestCase):
    def test_factory_create___on_default_environment___returns_update_all_service(self):
        self.assertIsInstance(UpdateAllServiceFactoryTester().create(default_env()), UpdateAllService)

    def test_full_run___on_default_environment___returns_0(self):
        sut, _ = tester()
        self.assertEqual(0, sut.full_run(UpdateAllServicePass.NewRun))

    def test_full_run___finishes_background_jobs_before_applying_zaparoo_frontend_preference(self):
        sut, _ = tester(service_type=UpdateAllServiceFlowTester)

        self.assertEqual(0, sut.full_run(UpdateAllServicePass.NewRun))

        self.assertEqual([
            'start_background_jobs',
            'finish_background_jobs_before_outro',
            'show_outro',
        ], sut.events)

    def test_full_run___with_no_databases_and_no_arcade_organizer___returns_0(self):
        sut, _ = tester(config=Config(arcade_organizer=False))
        self.assertEqual(0, sut.full_run(UpdateAllServicePass.NewRun))

    def test_full_run___when_non_interactive___skips_countdown_and_final_interactive_viewer(self):
        logger = LoggerSpy()
        countdown = CountdownStub(CountdownOutcome.SETTINGS_SCREEN)
        settings_screen = SettingsScreenStub()
        sut, _ = tester(
            config=Config(databases=default_databases(), non_interactive=True),
            countdown=countdown,
            settings_screen=settings_screen,
            logger=logger,
        )

        result = sut.full_run(UpdateAllServicePass.NewRun)

        self.assertEqual(0, result)
        self.assertEqual([], countdown.execute_count_calls)
        self.assertEqual(0, settings_screen.load_main_menu_calls)
        self.assertIn('Skipping settings countdown in non-interactive mode.', logger.debug_lines)
        self.assertIn('Skipping interactive log viewer and timeline in non-interactive mode.', logger.debug_lines)

    def test_full_run___when_non_interactive_continue_would_resume_settings___skips_settings_screen(self):
        logger = LoggerSpy()
        settings_screen = SettingsScreenStub()
        sut, _ = tester(
            files={FILE_update_all_early_update_resume: {'content': 'settings_screen'}},
            config=Config(databases=default_databases(), non_interactive=True),
            settings_screen=settings_screen,
            logger=logger,
        )

        result = sut.full_run(UpdateAllServicePass.Continue)

        self.assertEqual(0, result)
        self.assertEqual(0, settings_screen.load_main_menu_calls)
        self.assertIn('Skipping Settings Screen in non-interactive mode.', logger.debug_lines)

    def test_full_run___only_arcade_organizer___returns_0(self):
        sut, _ = tester(config=Config(arcade_organizer=True))
        self.assertEqual(0, sut.full_run(UpdateAllServicePass.NewRun))

    def test_full_run___only_downloader___returns_0(self):
        sut, _ = tester(config=Config(arcade_organizer=False, databases=default_databases()))
        self.assertEqual(0, sut.full_run(UpdateAllServicePass.NewRun))

    def test_full_run___only_downloader_without_linux___returns_0(self):
        sut, _ = tester(config=Config(arcade_organizer=False, databases=default_databases(), skip_linux_update=True))
        self.assertEqual(0, sut.full_run(UpdateAllServicePass.NewRun))

    def test_full_run___when_standard_downloader_fails___finishes_cleanup_and_reports_downloader_error(self):
        logger = LoggerSpy()
        downloader = _DownloaderServiceStub(update_return_code=7)
        sut, _ = tester(
            config=Config(arcade_organizer=False, databases=default_databases()),
            downloader_service=downloader,
            logger=logger,
        )

        result = sut.full_run(UpdateAllServicePass.NewRun)

        self.assertEqual(10, result)
        self.assertEqual(1, len(downloader.update_calls))
        self.assertEqual(1, downloader.cleanup_calls)
        self.assertIn('There were some errors in the Updaters.', logger.print_lines)
        self.assertIn(' - Scripts/.config/downloader/downloader.log', logger.print_lines)

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

    def test_full_run___ordinary_flows___preserve_standard_downloader_tail_order(self):
        standard_tail = [
            'pre_run_tweaks',
            'wait_for_retroaccount_before_downloader',
            'run_downloader',
            'sync_downloader_launcher',
            'run_pocket_tools',
            'run_arcade_organizer',
            'cleanup',
            'finish_background_jobs_before_outro',
            'show_outro',
            'show_interactive_log_viewer_and_timeline',
            'reboot_if_needed',
        ]
        cases = (
            (
                UpdateAllServicePass.Continue,
                None,
                CountdownOutcome.CONTINUE,
                [
                    'start_background_jobs',
                    *standard_tail,
                ],
            ),
            (
                UpdateAllServicePass.Continue,
                'settings_screen',
                CountdownOutcome.CONTINUE,
                [
                    'start_background_jobs',
                    'show_settings_screen',
                    'print_sequence',
                    *standard_tail,
                ],
            ),
            (
                UpdateAllServicePass.NewRun,
                None,
                CountdownOutcome.CONTINUE,
                [
                    'start_background_jobs',
                    'print_sequence',
                    'print_sequence',
                    *standard_tail,
                ],
            ),
            (
                UpdateAllServicePass.NewRun,
                None,
                CountdownOutcome.SETTINGS_SCREEN,
                [
                    'start_background_jobs',
                    'print_sequence',
                    'show_settings_screen',
                    'print_sequence',
                    *standard_tail,
                ],
            ),
        )

        for run_pass, resume_point, countdown_outcome, expected_events in cases:
            with self.subTest(run_pass=run_pass, resume_point=resume_point, countdown_outcome=countdown_outcome):
                files = {} if resume_point is None else {
                    FILE_update_all_early_update_resume: {'content': resume_point},
                }
                sut, _ = tester(
                    files=files,
                    countdown=CountdownStub(countdown_outcome),
                    service_type=_DownloaderTailOrderUpdateAllService,
                )

                result = sut.full_run(run_pass)

                self.assertEqual(0, result)
                self.assertEqual(expected_events, sut.events)

    def test_full_run___when_early_update_hashes_match___runs_normal_downloader_without_targeted_update(self):
        files = _early_update_files('pyz-md5', 'model-md5')
        fetcher = FetcherStub(response=(200, _update_all_db('pyz-md5', 'model-md5')))
        downloader = _DownloaderServiceStub()
        sut, _ = tester(
            files=files,
            fetcher=fetcher,
            downloader_service=downloader,
        )

        result = sut.full_run(UpdateAllServicePass.NewRun)

        self.assertEqual(0, result)
        self.assertEqual(1, len(fetcher.calls))
        self.assertEqual([], downloader.command_calls)
        self.assertEqual(1, len(downloader.update_calls))

    def test_full_run___when_either_early_update_file_is_missing___does_not_fetch_or_run_targeted_update(self):
        cases = (
            {FILE_settings_screen_model_json_zip: {'hash': 'model-md5'}},
            {FILE_update_all_pyz: {'hash': 'pyz-md5'}},
        )

        for files in cases:
            with self.subTest(files=files):
                fetcher = FetcherStub(response=(200, _update_all_db('new-pyz-md5', 'new-model-md5')))
                downloader = _DownloaderServiceStub()
                sut, _ = tester(
                    files=files,
                    fetcher=fetcher,
                    downloader_service=downloader,
                )

                result = sut.full_run(UpdateAllServicePass.NewRun)

                self.assertEqual(0, result)
                self.assertEqual([], fetcher.calls)
                self.assertEqual([], downloader.command_calls)
                self.assertEqual(1, len(downloader.update_calls))

    def test_full_run___when_early_update_is_needed_before_settings___updates_quietly_and_resumes_at_settings(self):
        downloader = _DownloaderServiceStub()
        settings_screen = SettingsScreenStub()
        sut, state = tester(
            files=_early_update_files('old-pyz-md5', 'old-model-md5'),
            fetcher=FetcherStub(response=(200, _update_all_db('new-pyz-md5', 'new-model-md5'))),
            downloader_service=downloader,
            countdown=CountdownStub(CountdownOutcome.SETTINGS_SCREEN),
            settings_screen=settings_screen,
        )

        result = sut.full_run(UpdateAllServicePass.NewRun)

        self.assertEqual(EXIT_CODE_CAN_CONTINUE, result)
        self.assertEqual(0, settings_screen.load_main_menu_calls)
        self.assertEqual([], downloader.update_calls)
        self.assertEqual([
            (
                '/media/fat/downloader.ini',
                ['--run-only', 'update_all_mister'],
                True,
            ),
        ], downloader.command_calls)
        self.assertEqual(
            'settings_screen',
            state.files[FILE_update_all_early_update_resume]['content'],
        )

    def test_full_run___after_early_update_before_settings___resumes_settings_then_runs_standard_downloader_once(self):
        downloader = _DownloaderServiceStub()
        settings_screen = SettingsScreenStub()
        sut, state = tester(
            files=_early_update_files('old-pyz-md5', 'old-model-md5'),
            fetcher=FetcherStub(response=(200, _update_all_db('new-pyz-md5', 'new-model-md5'))),
            downloader_service=downloader,
            countdown=CountdownStub(CountdownOutcome.SETTINGS_SCREEN),
            settings_screen=settings_screen,
        )

        first_result = sut.full_run(UpdateAllServicePass.NewRun)
        second_result = sut.full_run(UpdateAllServicePass.Continue)

        self.assertEqual(EXIT_CODE_CAN_CONTINUE, first_result)
        self.assertEqual(0, second_result)
        self.assertEqual(1, settings_screen.load_main_menu_calls)
        self.assertEqual(1, len(downloader.command_calls))
        self.assertEqual(1, len(downloader.update_calls))
        self.assertNotIn(FILE_update_all_early_update_resume, state.files)

    def test_full_run___when_early_update_is_needed_before_downloader___updates_quietly_and_resumes_at_downloader(self):
        downloader = _DownloaderServiceStub()
        sut, state = tester(
            files=_early_update_files('old-pyz-md5', 'old-model-md5'),
            fetcher=FetcherStub(response=(200, _update_all_db('new-pyz-md5', 'new-model-md5'))),
            downloader_service=downloader,
        )

        result = sut.full_run(UpdateAllServicePass.NewRun)

        self.assertEqual(EXIT_CODE_CAN_CONTINUE, result)
        self.assertEqual([], downloader.update_calls)
        self.assertNotIn(FILE_update_all_early_update_resume, state.files)

    def test_full_run___when_targeted_early_update_fails___continues_with_normal_downloader(self):
        downloader = _DownloaderServiceStub(command_return_code=7)
        sut, state = tester(
            files=_early_update_files('old-pyz-md5', 'old-model-md5'),
            fetcher=FetcherStub(response=(200, _update_all_db('new-pyz-md5', 'new-model-md5'))),
            downloader_service=downloader,
        )

        result = sut.full_run(UpdateAllServicePass.NewRun)

        self.assertEqual(0, result)
        self.assertEqual(1, len(downloader.command_calls))
        self.assertEqual(1, len(downloader.update_calls))
        self.assertNotIn(FILE_update_all_early_update_resume, state.files)

    def test_full_run___when_targeted_early_update_succeeds___restarts_without_rechecking_installed_files(self):
        downloader = _DownloaderServiceStub()
        sut, state = tester(
            files=_early_update_files('old-pyz-md5', 'old-model-md5'),
            fetcher=FetcherStub(response=(200, _update_all_db('new-pyz-md5', 'new-model-md5'))),
            downloader_service=downloader,
        )

        result = sut.full_run(UpdateAllServicePass.NewRun)

        self.assertEqual(EXIT_CODE_CAN_CONTINUE, result)
        self.assertEqual(1, len(downloader.command_calls))
        self.assertEqual([], downloader.update_calls)
        self.assertNotIn(FILE_update_all_early_update_resume, state.files)

    def test_full_run___when_early_update_manifest_is_invalid___continues_with_normal_downloader(self):
        responses = (
            (503, b''),
            (200, b'not-json'),
            (200, b'{"files": {}}'),
        )

        for response in responses:
            with self.subTest(response=response):
                downloader = _DownloaderServiceStub()
                fetcher = FetcherStub(response=response)
                sut, _ = tester(
                    files=_early_update_files('old-pyz-md5', 'old-model-md5'),
                    fetcher=fetcher,
                    downloader_service=downloader,
                )

                result = sut.full_run(UpdateAllServicePass.NewRun)

                self.assertEqual(0, result)
                self.assertEqual(1, len(fetcher.calls))
                self.assertEqual([], downloader.command_calls)
                self.assertEqual(1, len(downloader.update_calls))

    def test_full_run___for_non_default_entrypoint___does_not_fetch_or_run_targeted_update(self):
        fetcher = FetcherStub(response=(200, _update_all_db('new-pyz-md5', 'new-model-md5')))
        downloader = _DownloaderServiceStub()
        sut, _ = tester(
            files=_early_update_files('old-pyz-md5', 'old-model-md5'),
            fetcher=fetcher,
            downloader_service=downloader,
        )

        result = sut.full_run(UpdateAllServicePass.NewRunNonStop)

        self.assertEqual(0, result)
        self.assertEqual([], fetcher.calls)
        self.assertEqual([], downloader.command_calls)
        self.assertEqual(1, len(downloader.update_calls))

    def test_full_run___when_early_update_check_times_out___waits_once_and_continues_expected_flow(self):
        cases = (
            (CountdownOutcome.SETTINGS_SCREEN, 1),
            (CountdownOutcome.CONTINUE, 0),
        )

        for countdown_outcome, expected_settings_calls in cases:
            with self.subTest(countdown_outcome=countdown_outcome):
                downloader = _DownloaderServiceStub()
                settings_screen = SettingsScreenStub()
                sut, _ = tester(
                    files=_early_update_files('old-pyz-md5', 'old-model-md5'),
                    countdown=CountdownStub(countdown_outcome),
                    downloader_service=downloader,
                    settings_screen=settings_screen,
                    service_type=_PendingBackgroundUpdateAllService,
                )

                result = sut.full_run(UpdateAllServicePass.NewRun)

                self.assertEqual(0, result)
                self.assertEqual([BACKGROUND_JOBS_SOFT_TIMEOUT], sut.early_update_wait_calls)
                self.assertEqual(expected_settings_calls, settings_screen.load_main_menu_calls)
                self.assertEqual([], downloader.command_calls)
                self.assertEqual(1, len(downloader.update_calls))

    def test_full_run___when_continuing_early_update___resumes_at_recorded_point(self):
        cases = (
            ('settings_screen', 1),
            ('downloader', 0),
            ('unknown', 0),
        )

        for resume_point, expected_settings_calls in cases:
            with self.subTest(resume_point=resume_point):
                settings_screen = SettingsScreenStub()
                downloader = _DownloaderServiceStub()
                sut, state = tester(
                    files={
                        FILE_update_all_early_update_resume: {'content': resume_point},
                    },
                    settings_screen=settings_screen,
                    downloader_service=downloader,
                )

                result = sut.full_run(UpdateAllServicePass.Continue)

                self.assertEqual(0, result)
                self.assertEqual(expected_settings_calls, settings_screen.load_main_menu_calls)
                self.assertEqual(1, len(downloader.update_calls))
                self.assertNotIn(FILE_update_all_early_update_resume, state.files)

    def test_full_run___when_continuing_without_early_update_marker___runs_standard_downloader(self):
        settings_screen = SettingsScreenStub()
        downloader = _DownloaderServiceStub()
        sut, _ = tester(
            settings_screen=settings_screen,
            downloader_service=downloader,
        )

        result = sut.full_run(UpdateAllServicePass.Continue)

        self.assertEqual(0, result)
        self.assertEqual(0, settings_screen.load_main_menu_calls)
        self.assertEqual(1, len(downloader.update_calls))

    def test_full_run___when_early_update_marker_cannot_be_read___runs_standard_downloader(self):
        settings_screen = SettingsScreenStub()
        downloader = _DownloaderServiceStub()
        sut, _ = tester(
            files={
                FILE_update_all_early_update_resume: {'content': 'settings_screen'},
            },
            settings_screen=settings_screen,
            downloader_service=downloader,
        )

        def unreadable_marker(_path):
            raise OSError('unreadable')

        def unremovable_marker(_path, verbose=True):
            del verbose
            raise OSError('unremovable')

        sut._file_system.read_file_contents = unreadable_marker
        sut._file_system.unlink = unremovable_marker

        result = sut.full_run(UpdateAllServicePass.Continue)

        self.assertEqual(0, result)
        self.assertEqual(0, settings_screen.load_main_menu_calls)
        self.assertEqual(1, len(downloader.update_calls))


def _early_update_files(pyz_hash: str, model_hash: str) -> dict[str, dict[str, str]]:
    return {
        FILE_update_all_pyz: {'hash': pyz_hash},
        FILE_settings_screen_model_json_zip: {'hash': model_hash},
    }


def _update_all_db(pyz_hash: str, model_hash: str) -> bytes:
    return json.dumps({
        'db_id': 'update_all_mister',
        'files': {
            FILE_update_all_pyz: {'hash': pyz_hash},
            FILE_settings_screen_model_json_zip: {'hash': model_hash},
        },
    }).encode()


class _DownloaderTailOrderUpdateAllService(UpdateAllServiceTester):
    def __init__(self, *args, **kwargs):
        events = []
        kwargs['background_jobs_service'] = _RecordingStartBackgroundJobsService(events)
        super().__init__(*args, **kwargs)
        self.events = events

    def _show_settings_screen(self) -> None:
        self.events.append('show_settings_screen')

    def _print_sequence(self) -> None:
        self.events.append('print_sequence')

    def _pre_run_tweaks(self) -> None:
        self.events.append('pre_run_tweaks')
        super()._pre_run_tweaks()

    def _run_downloader(self) -> None:
        self.events.append('run_downloader')

    def _sync_downloader_launcher(self) -> None:
        self.events.append('sync_downloader_launcher')

    def _run_pocket_tools(self) -> None:
        self.events.append('run_pocket_tools')

    def _run_arcade_organizer(self) -> None:
        self.events.append('run_arcade_organizer')

    def _cleanup(self) -> None:
        self.events.append('cleanup')

    def _show_outro(self) -> None:
        self.events.append('show_outro')

    def _show_interactive_log_viewer_and_timeline(self) -> None:
        self.events.append('show_interactive_log_viewer_and_timeline')

    def _reboot_if_needed(self) -> None:
        self.events.append('reboot_if_needed')


class _PendingBackgroundUpdateAllService(UpdateAllServiceTester):
    def __init__(self, *args, **kwargs):
        background_jobs_service = _PendingBackgroundJobsService()
        kwargs['background_jobs_service'] = background_jobs_service
        super().__init__(*args, **kwargs)
        self._pending_background_jobs_service = background_jobs_service

    @property
    def early_update_wait_calls(self):
        return self._pending_background_jobs_service.early_update_check.wait_calls


class _RecordingStartBackgroundJobsService(UpdateAllBackgroundJobsServiceTester):
    def __init__(self, events: list[str]):
        super().__init__()
        self._events = events

    def start_background_jobs(self, check_for_early_update: bool = False):
        del check_for_early_update
        self._events.append('start_background_jobs')
        return None

    def wait_for_retroaccount_before_downloader(self) -> None:
        self._events.append('wait_for_retroaccount_before_downloader')

    def finish_background_jobs_before_outro(self) -> None:
        self._events.append('finish_background_jobs_before_outro')


class _PendingBackgroundJobsService(UpdateAllBackgroundJobsServiceTester):
    def __init__(self):
        super().__init__()
        self.early_update_check = None

    def start_background_jobs(
            self,
            check_for_early_update: bool = False,
    ) -> Optional[UpdateAllEarlyUpdateCheck]:
        if not check_for_early_update:
            return None

        self.early_update_check = _ImmediateTimeoutEarlyUpdateCheck()
        return self.early_update_check


class _ImmediateTimeoutEarlyUpdateCheck(UpdateAllEarlyUpdateCheck):
    def __init__(self):
        super().__init__(Future(), Future())
        self.wait_calls = []

    def wait(self, timeout: float) -> bool:
        self.wait_calls.append(timeout)
        return False


class _DownloaderServiceStub:
    def __init__(
            self,
            command_return_code: int = 0,
            update_return_code: int = 0,
    ):
        self.command_return_code = command_return_code
        self.update_return_code = update_return_code
        self.command_calls = []
        self.update_calls = []
        self.cleanup_calls = 0

    def execute_downloader_command(self, _config, downloader_ini_path, args, quiet=False):
        self.command_calls.append((downloader_ini_path, args, quiet))
        return self.command_return_code

    def execute_downloader(self, config, downloader_ini_path, skip_linux_update, logfile, default_db, quiet=False):
        self.update_calls.append((
            config,
            downloader_ini_path,
            skip_linux_update,
            logfile,
            default_db,
            quiet,
        ))
        return self.update_return_code

    def cleanup_temp_launchers(self):
        self.cleanup_calls += 1
