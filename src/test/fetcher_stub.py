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

from typing import Any, Optional

from update_all.config import Config
from update_all.fetcher import Fetcher
from update_all.other import GenericProvider


FetchCall = tuple[str, Optional[str], Any, Any, Optional[float]]
FetchResponse = tuple[int, bytes]


class FetcherStub(Fetcher):
    def __init__(
            self,
            response: FetchResponse = (200, b''),
            responses: Optional[list[FetchResponse]] = None,
            config_provider: GenericProvider[Config] = None,
    ):
        if config_provider is None:
            config_provider = GenericProvider[Config]()
            config_provider.initialize(Config())
        super().__init__(config_provider, logger=None)
        self._response = response
        self._responses = list(responses or [])
        self.calls: list[FetchCall] = []

    def fetch(self, url: str, method=None, body=None, headers=None, timeout=None, retry=3) -> FetchResponse:
        del retry
        self.calls.append((url, method, body, headers, timeout))
        if self._responses:
            return self._responses.pop(0)
        return self._response
