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
from abc import abstractmethod, ABC
from dataclasses import dataclass
import time

from update_all.config import Config
from update_all.file_system import FileSystem
from update_all.local_store import LocalStore
from update_all.logger import Logger
from update_all.other import GenericProvider
from update_all.local_repository import LocalRepository
from update_all.config_reader import ConfigReader
from update_all.transition_service import TransitionService


@dataclass
class EnvironmentSetupResult:
    requires_early_exit: bool = False


class EnvironmentSetup(ABC):
    @abstractmethod
    def setup_environment(self) -> EnvironmentSetupResult:
        """Setups the application environment."""


class EnvironmentSetupImpl(EnvironmentSetup):
    def __init__(self, logger: Logger, config_reader: ConfigReader,
                 config_provider: GenericProvider[Config],
                 transition_service: TransitionService,
                 local_repository: LocalRepository,
                 store_provider: GenericProvider[LocalStore],
                 file_system: FileSystem):
        self._logger = logger
        self._config_reader = config_reader
        self._config_provider = config_provider
        self._transition_service = transition_service
        self._local_repository = local_repository
        self._store_provider = store_provider
        self._file_system = file_system

    def setup_environment(self) -> EnvironmentSetupResult:
        config = Config()
        config.start_time = time.monotonic()

        self._config_provider.initialize(config)
        self._config_reader.fill_config_with_environment(config)

        local_store = self._local_repository.load_store()
        self._store_provider.initialize(local_store)
        downloader_ini = self._config_reader.read_downloader_ini()
        self._config_reader.fill_config_with_mister_section(config, downloader_ini)
        self._config_reader.fill_config_with_local_store(config, local_store)
        self._logger.configure(config)

        self._transition_service.from_old_db_ids_to_new_db_ids(downloader_ini)
        self._transition_service.removing_obsolete_db_ids(downloader_ini)
        self._transition_service.from_not_existing_downloader_ini(config)
        self._transition_service.from_update_all_1(config, local_store)
        self._config_reader.fill_config_with_database_sections(config, downloader_ini)
        self._transition_service.from_just_names_txt_enabled_to_arcade_names_txt_enabled(config, local_store)
        self._transition_service.from_old_db_urls_to_actual_db_urls(config, downloader_ini)
        self._transition_service.from_no_update_all_mister_db_to_adding_it(config, downloader_ini)
        if local_store.needs_save():
            self._local_repository.save_store(local_store)

        self._config_reader.read_retroaccount_cfg(config, self._file_system)
        self._config_reader.debug_log(config, local_store)
        return EnvironmentSetupResult(requires_early_exit=config.transition_service_only)
