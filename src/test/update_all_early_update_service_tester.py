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
from test.fake_filesystem import FileSystemFactory
from test.fetcher_stub import FetcherStub
from test.logger_tester import NoLogger
from test.spy_os_utils import SpyOsUtils
from update_all.config import Config
from update_all.constants import DOWNLOADER_INI_STANDARD_PATH, MEDIA_FAT
from update_all.downloader_service import DownloaderService
from update_all.fetcher import Fetcher
from update_all.file_system import FileSystem
from update_all.ini_repository import IniRepository
from update_all.logger import Logger
from update_all.other import GenericProvider
from update_all.update_all_early_update_service import UpdateAllEarlyUpdateService


class UpdateAllEarlyUpdateServiceTester(UpdateAllEarlyUpdateService):
    def __init__(
            self,
            config_provider: GenericProvider[Config] = None,
            logger: Logger = None,
            file_system: FileSystem = None,
            ini_repository: IniRepository = None,
            downloader_service: DownloaderService = None,
            fetcher: Fetcher = None,
    ):
        if config_provider is None:
            config_provider = GenericProvider[Config]()
            config_provider.initialize(Config())
        logger = logger or NoLogger()
        file_system = file_system or FileSystemFactory(
            config_provider=config_provider,
        ).create_for_system_scope()

        super().__init__(
            config_provider,
            logger,
            file_system,
            ini_repository or _IniRepositoryStub(),
            downloader_service or DownloaderService(logger, file_system, SpyOsUtils()),
            fetcher or FetcherStub(config_provider=config_provider),
        )


class _IniRepositoryStub:
    def downloader_ini_standard_path(self) -> str:
        return f'{MEDIA_FAT}/{DOWNLOADER_INI_STANDARD_PATH}'
