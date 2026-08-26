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
from concurrent.futures import TimeoutError
from threading import Event

from test.fake_filesystem import FileSystemFactory
from test.fetcher_stub import FetcherStub
from test.file_system_tester_state import FileSystemState
from test.update_all_background_jobs_service_tester import UpdateAllBackgroundJobsServiceTester
from test.update_all_self_update_service_tester import UpdateAllSelfUpdateServiceTester
from update_all.config import Config
from update_all.constants import BACKGROUND_JOBS_SOFT_TIMEOUT, FILE_settings_screen_model_json_zip, FILE_update_all_pyz
from update_all.other import GenericProvider
from update_all.update_output import NoopUpdateOutput


class TestUpdateAllBackgroundJobsService(unittest.TestCase):
    def test_start_background_jobs___runs_early_tasks_and_retroaccount_sync_concurrently(self):
        first_early_task_started = Event()
        second_early_task_started = Event()
        retroaccount_started = Event()
        self_update_service = _ConcurrentSelfUpdateServiceStub(
            first_early_task_started,
            second_early_task_started,
            retroaccount_started,
        )
        retroaccount = _ConcurrentRetroAccountServiceStub(
            first_early_task_started,
            second_early_task_started,
            retroaccount_started,
        )
        sut = UpdateAllBackgroundJobsServiceTester(
            self_update_service=self_update_service,
            retroaccount=retroaccount,
        )

        check = sut.start_background_jobs(check_for_self_update=True)

        self.assertIsNotNone(check)
        self.assertFalse(sut.wait_for_self_update_needed_with_soft_timeout(check))
        sut.finish_background_jobs_before_outro(None)
        self.assertEqual(1, len(retroaccount.mister_sync_calls))
        self.assertIsInstance(retroaccount.mister_sync_calls[0], NoopUpdateOutput)

    def test_start_background_jobs___overlaps_manifest_fetch_with_sequential_installed_file_hashing(self):
        config_provider = GenericProvider[Config]()
        config_provider.initialize(Config())
        state = FileSystemState(files=_self_update_files('pyz', 'model'))
        file_system = FileSystemFactory(
            state=state,
            config_provider=config_provider,
        ).create_for_system_scope()
        fetcher = FetcherStub(
            response=(200, _update_all_db('pyz', 'model')),
            config_provider=config_provider,
        )
        self_update_service = UpdateAllSelfUpdateServiceTester(
            config_provider=config_provider,
            file_system=file_system,
            fetcher=fetcher,
        )
        hash_started = Event()
        fetch_started = Event()
        original_hash = file_system.hash
        original_fetch = fetcher.fetch

        def coordinated_hash(path):
            hash_started.set()
            if not fetch_started.wait(1):
                raise RuntimeError('Manifest fetch did not overlap installed file hashing')
            return original_hash(path)

        def coordinated_fetch(*args, **kwargs):
            fetch_started.set()
            if not hash_started.wait(1):
                raise RuntimeError('Installed file hashing did not overlap manifest fetch')
            return original_fetch(*args, **kwargs)

        file_system.hash = coordinated_hash
        fetcher.fetch = coordinated_fetch
        sut = UpdateAllBackgroundJobsServiceTester(self_update_service=self_update_service)

        check = sut.start_background_jobs(check_for_self_update=True)

        self.assertIsNotNone(check)
        self.assertFalse(sut.wait_for_self_update_needed_with_soft_timeout(check))
        sut.finish_background_jobs_before_outro(None)
        self.assertTrue(hash_started.is_set())
        self.assertTrue(fetch_started.is_set())

    def test_wait_for_self_update_needed_with_soft_timeout___uses_the_single_five_second_gate_and_discards_on_timeout(self):
        sut = UpdateAllBackgroundJobsServiceTester()
        check = _SelfUpdateCheckStub(completed=False)

        result = sut.wait_for_self_update_needed_with_soft_timeout(check)

        self.assertIsNone(result)
        self.assertEqual([BACKGROUND_JOBS_SOFT_TIMEOUT], check.wait_calls)
        self.assertEqual(1, check.cancel_calls)

    def test_wait_for_retroaccount_before_downloader___uses_one_bounded_future_wait_for_every_outcome(self):
        for error in (None, TimeoutError(), RuntimeError('sync failed')):
            with self.subTest(error=error):
                sut = UpdateAllBackgroundJobsServiceTester()
                future = _ResultFutureStub(error)
                sut._retroaccount_future = future

                sut.wait_for_retroaccount_before_downloader()

                self.assertEqual([BACKGROUND_JOBS_SOFT_TIMEOUT], future.result_calls)

    def test_discard_self_update_check___cancels_check(self):
        sut = UpdateAllBackgroundJobsServiceTester()
        check = _SelfUpdateCheckStub()

        sut.discard_self_update_check(check)

        self.assertEqual(1, check.cancel_calls)

    def test_finish_background_jobs_before_outro___discards_unconsumed_self_update_check(self):
        sut = UpdateAllBackgroundJobsServiceTester()
        check = _SelfUpdateCheckStub()

        sut.finish_background_jobs_before_outro(check)

        self.assertEqual(1, check.cancel_calls)


class _SelfUpdateCheckStub:
    def __init__(self, completed: bool = True):
        self._completed = completed
        self.wait_calls = []
        self.cancel_calls = 0

    def wait(self, timeout: float) -> bool:
        self.wait_calls.append(timeout)
        return self._completed

    def cancel(self) -> None:
        self.cancel_calls += 1


class _ResultFutureStub:
    def __init__(self, error):
        self._error = error
        self.result_calls = []

    def result(self, timeout=None):
        self.result_calls.append(timeout)
        if self._error is not None:
            raise self._error


class _SelfUpdateServiceStub:
    def can_check_for_update(self) -> bool:
        return True

    def fetch_expected_hashes(self):
        return {}

    def hash_installed_files(self):
        return {}

    def is_update_needed(self, _expected_hashes, _installed_hashes):
        return False


class _ConcurrentSelfUpdateServiceStub(_SelfUpdateServiceStub):
    def __init__(
            self,
            first_task_started: Event,
            second_task_started: Event,
            retroaccount_started: Event,
    ):
        super().__init__()
        self._first_task_started = first_task_started
        self._second_task_started = second_task_started
        self._retroaccount_started = retroaccount_started

    def fetch_expected_hashes(self):
        return self._run_task(self._first_task_started)

    def hash_installed_files(self):
        return self._run_task(self._second_task_started)

    def _run_task(self, task_started: Event):
        task_started.set()
        if not self._retroaccount_started.wait(1):
            raise RuntimeError('RetroAccount sync did not overlap the early update tasks')
        return {}


class _ConcurrentRetroAccountServiceStub:
    def __init__(
            self,
            first_early_task_started: Event,
            second_early_task_started: Event,
            retroaccount_started: Event,
    ):
        self._first_early_task_started = first_early_task_started
        self._second_early_task_started = second_early_task_started
        self._retroaccount_started = retroaccount_started
        self.mister_sync_calls = []

    def mister_sync(self, output) -> None:
        self.mister_sync_calls.append(output)
        self._retroaccount_started.set()
        if not self._first_early_task_started.wait(1) or not self._second_early_task_started.wait(1):
            raise RuntimeError('Early update tasks did not overlap RetroAccount sync')




def _self_update_files(pyz_hash: str, model_hash: str) -> dict[str, dict[str, str]]:
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
