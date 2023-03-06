# Copyright (c) 2022-2023 José Manuel Barroso Galindo <theypsilon@gmail.com>
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

from update_all.config import Config
from update_all.local_store import LocalStore
from update_all.other import GenericProvider
from update_all.local_repository import LocalRepository
from update_all.config_reader import ConfigReader
from update_all.transition_service import TransitionService


class EnvironmentSetup(ABC):
    @abstractmethod
    def setup_environment(self) -> None:
        """Setups the application environment."""


class EnvironmentSetupImpl(EnvironmentSetup):
    def __init__(self, config_reader: ConfigReader,
                 config_provider: GenericProvider[Config],
                 transition_service: TransitionService,
                 local_repository: LocalRepository,
                 store_provider: GenericProvider[LocalStore]):
        self._config_reader = config_reader
        self._config_provider = config_provider
        self._transition_service = transition_service
        self._local_repository = local_repository
        self._store_provider = store_provider

    def setup_environment(self) -> None:
        config = Config()
        self._config_reader.fill_config_with_environment_and_mister_section(config)
        self._config_provider.initialize(config)
        local_store = self._local_repository.load_store()
        self._store_provider.initialize(local_store)
        self._transition_service.from_not_existing_downloader_ini(config)
        self._transition_service.from_update_all_1(config, local_store)
        self._config_reader.fill_config_with_ini_files(config)
        self._config_reader.fill_config_with_local_store(config, local_store)
