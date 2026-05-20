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

from typing import Optional

from test.fake_filesystem import FileSystemFactory
from test.fetcher_stub import FetchResponse, FetcherStub
from test.logger_tester import NoLogger
from update_all.config import Config
from update_all.file_system import FileSystem
from update_all.other import GenericProvider
from update_all.retroaccount_gateway import RetroAccountGateway


class RetroAccountGatewayTester(RetroAccountGateway):
    def __init__(
            self,
            status: int = 200,
            body: bytes = b'',
            responses: Optional[list[FetchResponse]] = None,
            config_provider: GenericProvider[Config] = None,
            file_system: FileSystem = None,
            fetcher: FetcherStub = None,
    ):
        if config_provider is None:
            config_provider = GenericProvider[Config]()
            config_provider.initialize(Config(retroaccount_domain='https://retroaccount.test'))

        self.fetcher = fetcher or FetcherStub((status, body), responses=responses, config_provider=config_provider)
        super().__init__(
            config_provider,
            NoLogger(),
            file_system or FileSystemFactory().create_for_system_scope(),
            self.fetcher,
        )
