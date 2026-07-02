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
from test.logger_tester import NoLogger
from test.mister_ini_repository_tester import MisterIniRepositoryTester
from test.spy_os_utils import SpyOsUtils
from update_all.config import Config
from update_all.file_system import FileSystem
from update_all.logger import Logger
from update_all.mister_ini_repository import MisterIniRepository
from update_all.mister_video_mode_service import MisterVideoModeService
from update_all.os_utils import OsUtils
from update_all.other import GenericProvider


class MisterVideoModeServiceTester(MisterVideoModeService):
    def __init__(
            self,
            logger: Logger = None,
            file_system: FileSystem = None,
            files=None,
            config: Config = None,
            config_provider: GenericProvider[Config] = None,
            os_utils: OsUtils = None,
            mister_ini_repository: MisterIniRepository = None,
    ):
        self.logger = logger or NoLogger()
        self.config_provider = config_provider or GenericProvider[Config]()
        self.config = self._get_or_initialize_config(config)
        self.file_system = (
            file_system
            or FileSystemFactory.from_state(files=files or {}, config=self.config).create_for_system_scope()
        )
        self.os_utils = os_utils or SpyOsUtils()
        self.mister_ini_repository = (
            mister_ini_repository
            or MisterIniRepositoryTester(file_system=self.file_system, logger=self.logger)
        )
        super().__init__(
            self.logger,
            self.file_system,
            self.config_provider,
            self.os_utils,
            self.mister_ini_repository,
        )

    def _get_or_initialize_config(self, config: Config = None) -> Config:
        try:
            return self.config_provider.get()
        except Exception:
            config = config or Config()
            self.config_provider.initialize(config)
            return config
