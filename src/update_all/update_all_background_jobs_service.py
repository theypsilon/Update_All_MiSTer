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
import time
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError, wait
from typing import Optional

from update_all.constants import BACKGROUND_JOBS_HARD_TIMEOUT, BACKGROUND_JOBS_SOFT_TIMEOUT
from update_all.fetcher import Fetcher
from update_all.logger import Logger
from update_all.retroaccount import RetroAccountService
from update_all.update_all_early_update_service import UpdateAllEarlyUpdateService
from update_all.update_output import NoopUpdateOutput


class UpdateAllEarlyUpdateCheck:
    def __init__(self, expected_hashes_future: Future, installed_hashes_future: Future):
        self._futures = (expected_hashes_future, installed_hashes_future)

    def wait(self, timeout: float) -> bool:
        _done, pending = wait(self._futures, timeout=timeout)
        return not pending

    def results(self) -> tuple[dict[str, str], dict[str, str]]:
        expected_hashes_future, installed_hashes_future = self._futures
        return expected_hashes_future.result(), installed_hashes_future.result()

    def cancel(self) -> None:
        for future in self._futures:
            future.cancel()


class UpdateAllBackgroundJobsService:
    def __init__(
            self,
            logger: Logger,
            fetcher: Fetcher,
            retroaccount: RetroAccountService,
            early_update_service: UpdateAllEarlyUpdateService,
    ):
        self._logger = logger
        self._fetcher = fetcher
        self._retroaccount = retroaccount
        self._early_update_service = early_update_service
        self._executor: Optional[ThreadPoolExecutor] = None
        self._retroaccount_future: Optional[Future] = None

    def start_background_jobs(
            self,
            check_for_early_update: bool = False,
    ) -> Optional[UpdateAllEarlyUpdateCheck]:
        executor = ThreadPoolExecutor(max_workers=3)
        self._executor = executor
        early_update_check = self._start_early_update_check(executor) if check_for_early_update else None
        self._retroaccount_future = executor.submit(self._sync_retroaccount)
        return early_update_check

    def wait_for_early_update_check(self, check: UpdateAllEarlyUpdateCheck) -> bool:
        return check.wait(BACKGROUND_JOBS_SOFT_TIMEOUT)

    def finish_early_update_check(self, check: UpdateAllEarlyUpdateCheck) -> bool:
        expected_hashes, installed_hashes = check.results()
        return self._early_update_service.is_update_needed(
            expected_hashes,
            installed_hashes,
        )

    def abort_early_update_check(self, check: UpdateAllEarlyUpdateCheck) -> None:
        self._early_update_service.abort_check()
        check.cancel()

    def wait_for_retroaccount_before_downloader(self) -> None:
        if self._retroaccount_future is None:
            return

        self._logger.bench("UpdateAllService: Background Soft Wait START")
        try:
            self._retroaccount_future.result(timeout=BACKGROUND_JOBS_SOFT_TIMEOUT)
            self._logger.bench("UpdateAllService: Background Soft Wait END completed")
        except TimeoutError:
            self._logger.bench("UpdateAllService: Background Soft Wait END pending")
        except Exception as e:
            self._logger.debug('RetroAccount background job failed before Downloader.')
            self._logger.debug(e)
            self._logger.bench("UpdateAllService: Background Soft Wait END failed")

    def stop_background_jobs_for_restart(self) -> None:
        if self._retroaccount_future is not None and not self._retroaccount_future.done():
            self._fetcher.cleanup()
            self._retroaccount_future.cancel()
        self._retroaccount_future = None

        if self._executor is not None:
            self._executor.shutdown(wait=False, cancel_futures=True)
            self._executor = None

    def finish_background_jobs_before_outro(self) -> None:
        if self._executor is None:
            return

        if self._retroaccount_future is not None:
            try:
                deadline = time.monotonic() + BACKGROUND_JOBS_HARD_TIMEOUT
                while not self._retroaccount_future.done() and time.monotonic() < deadline:
                    self._logger.print('.', end='', flush=True)
                    time.sleep(0.25)

                if not self._retroaccount_future.done():
                    self._fetcher.cleanup()
                    self._retroaccount_future.result(timeout=5)
                self._retroaccount_future = None
                self._logger.print(flush=True)

            except Exception as e:
                self._logger.debug('Background job did not finish in time')
                self._logger.debug(e)

        self._executor.shutdown(wait=False)
        self._executor = None

    def _sync_retroaccount(self) -> None:
        self._logger.bench('UpdateAllService: Background job START')
        self._retroaccount.mister_sync(NoopUpdateOutput())
        self._logger.bench('UpdateAllService: Background job END')

    def _start_early_update_check(
            self,
            executor: ThreadPoolExecutor,
    ) -> Optional[UpdateAllEarlyUpdateCheck]:
        if not self._early_update_service.can_check_for_update():
            self._logger.debug('Early Update All check skipped.')
            return None
        return UpdateAllEarlyUpdateCheck(
            executor.submit(self._early_update_service.fetch_expected_hashes),
            executor.submit(self._early_update_service.hash_installed_files),
        )
