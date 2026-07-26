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
from test.logger_tester import NoLogger
from test.update_all_self_update_service_tester import UpdateAllSelfUpdateServiceTester
from update_all.logger import Logger
from update_all.retroaccount import RetroAccountService
from update_all.update_all_background_jobs_service import UpdateAllBackgroundJobsService
from update_all.update_all_self_update_service import UpdateAllSelfUpdateService


class UpdateAllBackgroundJobsServiceTester(UpdateAllBackgroundJobsService):
    def __init__(
            self,
            logger: Logger = None,
            retroaccount: RetroAccountService = None,
            self_update_service: UpdateAllSelfUpdateService = None,
    ):
        super().__init__(
            logger or NoLogger(),
            retroaccount or _RetroAccountServiceStub(),
            self_update_service or UpdateAllSelfUpdateServiceTester(),
        )


class _RetroAccountServiceStub:
    def __init__(self):
        self.mister_sync_calls = []

    def mister_sync(self, output) -> None:
        self.mister_sync_calls.append(output)
