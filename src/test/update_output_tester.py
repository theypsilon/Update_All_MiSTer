# Copyright (c) 2022-2026 José Manuel Barroso Galindo <theypsilon@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# You can download the latest version of this tool from:
# https://github.com/theypsilon/Update_All_MiSTer

from typing import Optional

from test.spy_os_utils import SpyOsUtils
from update_all.update_output import UpdateOutput, UpdateOutputField


class UpdateOutputTester(UpdateOutput):
    def __init__(self, os_utils: Optional[SpyOsUtils] = None):
        self._os_utils = os_utils
        self.transition_calls = []
        self.sleep_calls_at_transition = []
        self.sync_started_calls = 0
        self.sync_finished_calls = 0
        self.jtbeta_updated_calls = 0
        self.credentials_removed_calls = []

    def transition(self, transition: str, **fields: UpdateOutputField) -> None:
        self.transition_calls.append((transition, fields))
        if self._os_utils is not None:
            self.sleep_calls_at_transition.append(list(self._os_utils.calls_to_sleep))

    def sync_started(self) -> None:
        self.sync_started_calls += 1

    def sync_finished(self) -> None:
        self.sync_finished_calls += 1

    def jtbeta_updated(self) -> None:
        self.jtbeta_updated_calls += 1

    def credentials_removed(self, reason: str) -> None:
        self.credentials_removed_calls.append(reason)
