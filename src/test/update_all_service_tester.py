# Copyright (c) 2022-2024 José Manuel Barroso Galindo <theypsilon@gmail.com>

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
from typing import Tuple, Any, List, Set, Dict, Callable, Optional
from unittest.mock import MagicMock

from test.countdown_stub import CountdownStub
from test.fake_filesystem import FileSystemFactory
from test.logger_tester import NoLogger
from test.spy_os_utils import SpyOsUtils
from update_all.config import Config
from update_all.config_reader import ConfigReader
from update_all.environment_setup import EnvironmentSetup, EnvironmentSetupImpl, EnvironmentSetupResult
from update_all.constants import KENV_COMMIT, KENV_CURL_SSL, DEFAULT_CURL_SSL_OPTIONS, DEFAULT_COMMIT, \
    KENV_LOCATION_STR, DEFAULT_LOCATION_STR, MEDIA_FAT, DOWNLOADER_INI_STANDARD_PATH, DEFAULT_DEBUG, KENV_DEBUG, KENV_KEY_IGNORE_TIME, DEFAULT_KEY_IGNORE_TIME, KENV_TRANSITION_SERVICE_ONLY, \
    DEFAULT_TRANSITION_SERVICE_ONLY
from update_all.countdown import Countdown
from update_all.databases import DB_ID_DISTRIBUTION_MISTER, AllDBs
from update_all.ini_repository import IniRepository, IniRepositoryInitializationError
from update_all.file_system import FileSystem
from update_all.local_repository import LocalRepository
from update_all.local_store import LocalStore
from update_all.os_utils import OsUtils
from update_all.other import Checker, GenericProvider
from update_all.settings_screen import SettingsScreen
from update_all.settings_screen_printer import SettingsScreenPrinter, SettingsScreenThemeManager
from update_all.store_migrator import StoreMigrator, make_new_local_store
from update_all.transition_service import TransitionService
from update_all.ui_engine import UiContext, UiRuntime
from update_all.ui_engine_dialog_application import UiDialogDrawerFactory
from update_all.update_all_service import UpdateAllServiceFactory, UpdateAllService


def default_env():
    return {
        KENV_CURL_SSL: DEFAULT_CURL_SSL_OPTIONS,
        KENV_COMMIT: DEFAULT_COMMIT,
        KENV_LOCATION_STR: DEFAULT_LOCATION_STR,
        KENV_DEBUG: DEFAULT_DEBUG,
        KENV_KEY_IGNORE_TIME: DEFAULT_KEY_IGNORE_TIME,
        KENV_TRANSITION_SERVICE_ONLY: DEFAULT_TRANSITION_SERVICE_ONLY
    }


def local_store():
    return LocalStore(make_new_local_store(StoreMigratorTester()))


class UpdateAllServiceFactoryTester(UpdateAllServiceFactory):
    def __init__(self):
        super().__init__(NoLogger(), GenericProvider[LocalRepository]())


class ConfigReaderTester(ConfigReader):
    def __init__(self, downloader_ini_repository: IniRepository = None, file_system: FileSystem = None, env: dict[str, str] = None):
        super().__init__(NoLogger(), env or default_env(), downloader_ini_repository or IniRepositoryTester(file_system=file_system))


class StoreMigratorTester(StoreMigrator):
    def __init__(self):
        super().__init__([], NoLogger())


class LocalRepositoryTester(LocalRepository):
    def __init__(self, config_provider: GenericProvider[Config] = None, file_system: FileSystem = None, store_migrator: StoreMigrator = None):
        super().__init__(
            config_provider=config_provider or GenericProvider[Config](),
            logger=NoLogger(),
            file_system=file_system or FileSystemFactory().create_for_system_scope(),
            store_migrator=store_migrator or StoreMigratorTester()
        )


class IniRepositoryTester(IniRepository):
    def __init__(self, file_system: FileSystem = None, os_utils: OsUtils = None):
        super().__init__(
            logger=NoLogger(),
            file_system=file_system or FileSystemFactory().create_for_system_scope(),
            os_utils=os_utils or SpyOsUtils()
        )

    def downloader_ini_standard_path(self):
        try:
            return super().downloader_ini_standard_path()
        except IniRepositoryInitializationError as _e:
            return f'{MEDIA_FAT}/{DOWNLOADER_INI_STANDARD_PATH}'


class SettingsScreenPrinterStub(SettingsScreenPrinter):
    def __init__(self, factory: UiDialogDrawerFactory = None, theme_manager: SettingsScreenThemeManager = None):
        self._factory = factory or MagicMock()
        self._theme_manager = theme_manager or MagicMock()

    def initialize_screen(self) -> Tuple[UiDialogDrawerFactory, SettingsScreenThemeManager]:
        return self._factory, self._theme_manager


class UiRuntimeStub(UiRuntime):
    def initialize_runtime(self, cb: Callable[[], None]) -> None: pass
    def update(self) -> None: pass
    def interrupt(self) -> None: pass
    def resume(self) -> None: pass


class CheckerTester(Checker):
    def __init__(self, file_system: FileSystem = None):
        super().__init__(file_system or FileSystemFactory().create_for_system_scope())


class SettingsScreenTester(SettingsScreen):
    def __init__(self, config_provider: GenericProvider[Config] = None,
                 file_system: FileSystem = None,
                 ini_repository: IniRepository = None,
                 os_utils: OsUtils = None,
                 settings_screen_printer: SettingsScreenPrinter = None,
                 ui_runtime: UiRuntime = None,
                 checker: Checker = None,
                 local_repository: LocalRepository = None,
                 store_provider: GenericProvider[LocalStore] = None):

        config_provider = config_provider or GenericProvider[Config]()
        file_system = file_system or FileSystemFactory(config_provider=config_provider).create_for_system_scope()
        super().__init__(
            logger=NoLogger(),
            config_provider=config_provider,
            file_system=file_system,
            ini_repository=ini_repository or IniRepositoryTester(file_system=file_system),
            os_utils=os_utils or SpyOsUtils(),
            settings_screen_printer=settings_screen_printer or SettingsScreenPrinterStub(),
            ui_runtime=ui_runtime or UiRuntimeStub(),
            checker=checker or CheckerTester(file_system=file_system),
            local_repository=local_repository or LocalRepositoryTester(config_provider=config_provider, file_system=file_system),
            store_provider=store_provider or GenericProvider[LocalStore]()
        )


class UiContextStub(UiContext):
    def __init__(self):
        self.variables = {}
        self.effects = {}
        self.formatters = {}

    def get_value(self, key: str) -> str:
        return self.variables[key]

    def set_value(self, key: str, value: Any) -> None:
        self.variables[key] = value

    def add_custom_effects(self, effects: Dict[str, Callable[[], None]]):
        self.effects = effects

    def add_custom_formatters(self, formatters: Dict[str, Callable[[str], str]]):
        self.formatters = formatters


def ensure_str_lists(this: List[any]) -> List[str]:
    for value in this:
        if not isinstance(this, list):
            raise Exception(f'Value "{str(value)}" must be list, got "{str(type(value))}" instead.')

    return this


def default_databases(add: List[str] = None, sub: List[str] = None) -> Set[str]:
    sub = ensure_str_lists(sub or [])
    return {value for value in {DB_ID_DISTRIBUTION_MISTER, AllDBs.JTCORES.db_id, AllDBs.COIN_OP_COLLECTION.db_id} if value not in sub} | set(ensure_str_lists(add or []))


class TransitionServiceTester(TransitionService):
    def __init__(self, file_system: FileSystem = None, os_utils: OsUtils = None, ini_repository: IniRepository = None):
        file_system = file_system or FileSystemFactory().create_for_system_scope()
        os_utils = os_utils or SpyOsUtils()
        super().__init__(logger=NoLogger(), file_system=file_system, os_utils=os_utils, ini_repository=ini_repository or IniRepositoryTester(file_system=file_system, os_utils=os_utils))


class EnvironmentSetupTester(EnvironmentSetupImpl):
    def __init__(self, config_reader: ConfigReader = None,
                 config_provider: GenericProvider[Config] = None,
                 transition_service: TransitionService = None,
                 local_repository: LocalRepository = None,
                 store_provider: GenericProvider[LocalStore] = None,
                 file_system: FileSystem = None,
                 os_utils: OsUtils = None,
                 env: dict[str, str] = None):

        file_system = file_system or FileSystemFactory().create_for_system_scope()
        os_utils = os_utils or SpyOsUtils()
        config_reader = config_reader or ConfigReaderTester(file_system=file_system, env=env)
        config_provider = config_provider or GenericProvider[Config]()
        store_provider = store_provider or GenericProvider[LocalStore]()

        transition_service = transition_service or TransitionServiceTester(file_system=file_system, os_utils=os_utils)
        local_repository = local_repository or LocalRepositoryTester(config_provider=config_provider, file_system=file_system)

        super().__init__(config_reader, config_provider, transition_service, local_repository, store_provider)


class EnvironmentSetupStub(EnvironmentSetup):
    def __init__(self, result: Optional[EnvironmentSetupResult] = None):
        self._result = result or EnvironmentSetupResult()

    def setup_environment(self) -> EnvironmentSetupResult:
        return self._result


class UpdateAllServiceTester(UpdateAllService):
    def __init__(self, environment_setup: EnvironmentSetup = None,
                 config_provider: GenericProvider[Config] = None,
                 file_system: FileSystem = None,
                 os_utils: OsUtils = None,
                 countdown: Countdown = None,
                 settings_screen: SettingsScreen = None,
                 store_provider: GenericProvider[LocalStore] = None,
                 ini_repository: IniRepository = None):

        file_system = file_system or FileSystemFactory().create_for_system_scope()
        os_utils = os_utils or SpyOsUtils()
        config_provider = config_provider or GenericProvider[Config]()

        environment_setup = environment_setup or EnvironmentSetupTester(file_system=file_system, os_utils=os_utils, config_provider=config_provider)
        settings_screen = settings_screen or SettingsScreenTester(config_provider=config_provider, file_system=file_system, os_utils=os_utils)
        self.ini_repository = ini_repository or IniRepositoryTester(file_system=file_system, os_utils=os_utils)

        super().__init__(
            environment_setup=environment_setup,
            config_provider=config_provider,
            logger=NoLogger(),
            file_system=file_system,
            os_utils=os_utils,
            countdown=countdown or CountdownStub(),
            settings_screen=settings_screen,
            checker=CheckerTester(),
            store_provider=store_provider or GenericProvider[LocalStore](),
            ini_repository=self.ini_repository
        )
