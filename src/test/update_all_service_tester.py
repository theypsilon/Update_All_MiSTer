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
from typing import Any, Callable, Optional
from test.countdown_stub import CountdownStub
from test.fake_filesystem import FileSystemFactory
from test.fetcher_stub import FetcherStub
from test.logger_tester import NoLogger
from test.mister_ini_repository_tester import MisterIniRepositoryTester
from test.mister_video_mode_service_tester import MisterVideoModeServiceTester
from test.retroachievements_service_tester import RetroAchievementsServiceTester
from test.retroaccount_gateway_tester import RetroAccountGatewayTester
from test.spy_os_utils import SpyOsUtils
from test.zaparoo_service_tester import ZaparooServiceTester
from update_all.arcade_organizer.arcade_organizer import ArcadeOrganizerService
from update_all.config import Config
from update_all.config_reader import ConfigReader
from update_all.encryption import Encryption
from update_all.environment_setup import EnvironmentSetup, EnvironmentSetupImpl, EnvironmentSetupResult
from update_all.constants import KENV_COMMIT, KENV_CURL_SSL, DEFAULT_CURL_SSL_OPTIONS, DEFAULT_COMMIT, \
    KENV_LOCATION_STR, DEFAULT_LOCATION_STR, MEDIA_FAT, DOWNLOADER_INI_STANDARD_PATH, DEFAULT_DEBUG, KENV_DEBUG, \
    KENV_TRANSITION_SERVICE_ONLY, FILE_patreon_key, COMMAND_STANDARD, FILE_timeline_short, KENV_TIMELINE_PLUS_PATH, \
    DEFAULT_TRANSITION_SERVICE_ONLY, KENV_SKIP_DOWNLOADER, DEFAULT_SKIP_DOWNLOADER, KENV_PATREON_KEY_PATH, KENV_COMMAND, \
    KENV_TIMELINE_SHORT_PATH, FILE_timeline_plus, KENV_HTTP_PROXY, KENV_HTTPS_PROXY, KENV_MIRROR_ID, \
    KENV_RETROACCOUNT_DOMAIN, DOMAIN_default_retroaccount, KENV_UPDATE_ALL_CHIP_ID_RESULT
from update_all.countdown import Countdown
from update_all.databases import DB_ID_DISTRIBUTION_MISTER, AllDBs, all_dbs
from update_all.ini_repository import IniRepository, IniRepositoryInitializationError
from update_all.jtcores_service import JtcoresService
from update_all.file_system import FileSystem
from update_all.local_repository import LocalRepository
from update_all.local_store import LocalStore
from update_all.log_viewer import LogViewer
from update_all.mister_ini_repository import MisterIniRepository
from update_all.mister_video_mode_service import MisterVideoModeService
from update_all.os_utils import OsUtils
from update_all.other import GenericProvider, TerminalSize
from update_all.retroachievements_service import RetroAchievementsService
from update_all.settings_screen import SettingsScreen
from update_all.settings_screen_printer import SettingsScreenPrinter, ColorThemeManager
from update_all.store_migrator import StoreMigrator, make_new_local_store
from update_all.timeline import Timeline
from update_all.transition_service import TransitionService
from update_all.retroaccount import RetroAccountService
from update_all.retroaccount_gateway import RetroAccountGateway
from update_all.ui_engine import UiContext, UiRuntime
from update_all.ui_engine_dialog_application import UiDialogDrawerFactory
from update_all.update_all_service import UpdateAllServiceFactory, UpdateAllService
from update_all.zaparoo_service import ZaparooService


def default_env():
    return {
        KENV_CURL_SSL: DEFAULT_CURL_SSL_OPTIONS,
        KENV_COMMIT: DEFAULT_COMMIT,
        KENV_LOCATION_STR: DEFAULT_LOCATION_STR,
        KENV_DEBUG: DEFAULT_DEBUG,
        KENV_SKIP_DOWNLOADER: DEFAULT_SKIP_DOWNLOADER,
        KENV_TRANSITION_SERVICE_ONLY: DEFAULT_TRANSITION_SERVICE_ONLY,
        KENV_PATREON_KEY_PATH: FILE_patreon_key,
        KENV_COMMAND: COMMAND_STANDARD,
        KENV_UPDATE_ALL_CHIP_ID_RESULT: '',
        KENV_TIMELINE_SHORT_PATH: FILE_timeline_short,
        KENV_TIMELINE_PLUS_PATH: FILE_timeline_plus,
        KENV_HTTP_PROXY: '',
        KENV_HTTPS_PROXY: '',
        KENV_MIRROR_ID: '',
        KENV_RETROACCOUNT_DOMAIN: DOMAIN_default_retroaccount,
        'real_start_time': 0.0,
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
    def __init__(self, file_system: FileSystem = None, store_migrator: StoreMigrator = None):
        super().__init__(
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
    def __init__(self, factory: UiDialogDrawerFactory = None, theme_manager: ColorThemeManager = None):
        self._factory = factory or _UiDialogDrawerFactoryStub()
        self._theme_manager = theme_manager or _ColorThemeManagerStub()

    def initialize_screen(self, screen_dims=None):
        return self._factory, self._theme_manager, None


class _UiDialogDrawerFactoryStub:
    def create_ui_dialog_drawer(self, _interpolator):
        return None


class _ColorThemeManagerStub:
    def set_theme(self, _theme):
        pass


class UiRuntimeStub(UiRuntime):
    def initialize_runtime(self, cb: Callable[[], None]) -> None: pass
    def update(self) -> None: pass
    def interrupt(self) -> None: pass
    def resume(self) -> None: pass


class EncryptionTester(Encryption):
    def __init__(self, config_provider: GenericProvider[Config] = None, file_system: FileSystem = None):
        super().__init__(NoLogger(), config_provider or GenericProvider[Config](), file_system or FileSystemFactory().create_for_system_scope())


class TimelineTester(Timeline):
    def __init__(self, file_system: FileSystem = None, config_provider: GenericProvider[Config] = None, encryption: Encryption = None, retroaccount: RetroAccountService = None):
        config_provider = config_provider or GenericProvider[Config]()
        file_system = file_system or FileSystemFactory().create_for_system_scope()
        super().__init__(
            NoLogger(),
            config_provider,
            file_system,
            encryption or EncryptionTester(config_provider=config_provider, file_system=file_system),
            retroaccount or RetroAccountServiceTester(file_system=file_system, config_provider=config_provider)
        )

class SettingsScreenTester(SettingsScreen):
    def __init__(self, config_provider: GenericProvider[Config] = None,
                 file_system: FileSystem = None,
                 ini_repository: IniRepository = None,
                 os_utils: OsUtils = None,
                 settings_screen_printer: SettingsScreenPrinter = None,
                 ui_runtime: UiRuntime = None,
                 encryption: Encryption = None,
                 local_repository: LocalRepository = None,
                 store_provider: GenericProvider[LocalStore] = None,
                 ao_service: ArcadeOrganizerService = None,
                 retroaccount: RetroAccountService = None,
                 mister_video_mode_service: MisterVideoModeService = None,
                 mister_ini_repository: MisterIniRepository = None,
                 retroachievements_service: RetroAchievementsService = None,
                 zaparoo_service: ZaparooService = None):

        config_provider = config_provider or GenericProvider[Config]()
        store_provider = store_provider or GenericProvider[LocalStore]()
        file_system = file_system or FileSystemFactory(config_provider=config_provider).create_for_system_scope()
        os_utils = os_utils or SpyOsUtils()
        mister_ini_repository = mister_ini_repository or MisterIniRepositoryTester(file_system=file_system)
        ini_repository = ini_repository or IniRepositoryTester(file_system=file_system)
        super().__init__(
            logger=NoLogger(),
            config_provider=config_provider,
            file_system=file_system,
            ini_repository=ini_repository,
            os_utils=os_utils,
            mister_video_mode_service=(
                mister_video_mode_service
                or MisterVideoModeServiceTester(
                    logger=NoLogger(),
                    file_system=file_system,
                    config_provider=config_provider,
                    os_utils=os_utils,
                    mister_ini_repository=mister_ini_repository,
                )
            ),
            settings_screen_printer=settings_screen_printer or SettingsScreenPrinterStub(),
            ui_runtime=ui_runtime or UiRuntimeStub(),
            encryption=encryption or EncryptionTester(config_provider=config_provider, file_system=file_system),
            local_repository=local_repository or LocalRepositoryTester(file_system=file_system),
            store_provider=store_provider,
            ao_service=ao_service or ArcadeOrganizerServiceStub(),
            retroaccount=retroaccount or RetroAccountServiceTester(file_system=file_system, config_provider=config_provider),
            retroachievements_service=(
                retroachievements_service
                or RetroAchievementsServiceTester(
                    file_system=file_system,
                    os_utils=os_utils,
                    mister_ini_repository=mister_ini_repository,
                )
            ),
            zaparoo_service=(
                zaparoo_service
                or ZaparooServiceTester(
                    file_system=file_system,
                    mister_ini_repository=mister_ini_repository,
                )
            ),
        )


class SettingsScreenStub:
    def __init__(self, load_chip_id_result_menu_result=None):
        self._load_chip_id_result_menu_result = load_chip_id_result_menu_result
        self.load_chip_id_result_menu_calls = 0

    def load_chip_id_result_menu(self):
        self.load_chip_id_result_menu_calls += 1
        if isinstance(self._load_chip_id_result_menu_result, Exception):
            raise self._load_chip_id_result_menu_result
        return self._load_chip_id_result_menu_result


class UiContextStub(UiContext):
    def __init__(self):
        self.variables = {}
        self.effects = {}
        self.formatters = {}

    def get_value(self, key: str) -> str:
        return self.variables[key]

    def set_value(self, key: str, value: Any) -> None:
        self.variables[key] = value

    def add_custom_effects(self, effects: dict[str, Callable[[], None]]):
        self.effects = effects

    def add_custom_formatters(self, formatters: dict[str, Callable[[str], str]]):
        self.formatters = formatters


def ensure_str_lists(this: list[any]) -> list[str]:
    for value in this:
        if not isinstance(this, list):
            raise Exception(f'Value "{str(value)}" must be list, got "{str(type(value))}" instead.')

    return this


def default_databases(add: list[str] = None, sub: list[str] = None) -> set[str]:
    sub = ensure_str_lists(sub or [])
    return {value for value in {DB_ID_DISTRIBUTION_MISTER, all_dbs('').JTCORES.db_id, all_dbs('').COIN_OP_COLLECTION.db_id, all_dbs('').UPDATE_ALL_MISTER.db_id} if value not in sub} | set(ensure_str_lists(add or []))


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
        local_repository = local_repository or LocalRepositoryTester(file_system=file_system)

        super().__init__(NoLogger(), config_reader, config_provider, transition_service, local_repository, store_provider, file_system)


class EnvironmentSetupStub(EnvironmentSetup):
    def __init__(self, result: Optional[EnvironmentSetupResult] = None):
        self._result = result or EnvironmentSetupResult()
        self.setup_environment_calls = []

    def setup_environment(self, term_size: TerminalSize, update_output) -> EnvironmentSetupResult:
        self.setup_environment_calls.append((term_size, update_output))
        return self._result


class LogViewerTester(LogViewer):
    def show(self, file_path: str, popup_dict: Optional[dict[str, str]] = None, initial_index: int = 0) -> bool:
        return True

class UpdateAllServiceTester(UpdateAllService):
    def __init__(self, environment_setup: EnvironmentSetup = None,
                 config_provider: GenericProvider[Config] = None,
                 file_system: FileSystem = None,
                 os_utils: OsUtils = None,
                 countdown: Countdown = None,
                 settings_screen: SettingsScreen = None,
                 store_provider: GenericProvider[LocalStore] = None,
                 ini_repository: IniRepository = None,
                 local_repository: LocalRepository = None,
                 zaparoo_service: ZaparooService = None,
                 retroaccount: RetroAccountService = None):

        file_system = file_system or FileSystemFactory().create_for_system_scope()
        os_utils = os_utils or SpyOsUtils()
        config_provider = config_provider or GenericProvider[Config]()
        store_provider = store_provider or GenericProvider[LocalStore]()

        ao_service = ArcadeOrganizerServiceStub()
        retroaccount = retroaccount or RetroAccountServiceTester(file_system=file_system, config_provider=config_provider)
        environment_setup = environment_setup or EnvironmentSetupTester(file_system=file_system, os_utils=os_utils, config_provider=config_provider)
        zaparoo_service = zaparoo_service or ZaparooServiceTester(file_system=file_system)
        settings_screen = settings_screen or SettingsScreenTester(
            config_provider=config_provider,
            file_system=file_system,
            os_utils=os_utils,
            ao_service=ao_service,
            retroaccount=retroaccount,
            zaparoo_service=zaparoo_service,
        )
        self.ini_repository = ini_repository or IniRepositoryTester(file_system=file_system, os_utils=os_utils)

        super().__init__(
            config_provider=config_provider,
            logger=NoLogger(),
            file_system=file_system,
            os_utils=os_utils,
            countdown=countdown or CountdownStub(),
            settings_screen=settings_screen,
            store_provider=store_provider,
            ini_repository=self.ini_repository,
            environment_setup=environment_setup,
            ao_service=ao_service,
            local_repository=local_repository or LocalRepositoryTester(file_system=file_system),
            log_viewer=LogViewerTester(file_system, config_provider, store_provider, retroaccount),
            timeline=TimelineTester(file_system=file_system, config_provider=config_provider, retroaccount=retroaccount),
            retroaccount=retroaccount,
            zaparoo_service=zaparoo_service,
            fetcher=FetcherStub(config_provider=config_provider)
        )

    def _soft_wait_background_jobs(self) -> None:
        pass

    def _hard_wait_background_jobs(self) -> None:
        pass


class UpdateAllServiceFlowTester(UpdateAllServiceTester):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = []

    def _start_background_jobs(self) -> None:
        self.events.append('start_background_jobs')

    def _hard_wait_background_jobs(self) -> None:
        self.events.append('hard_wait_background_jobs')

    def _show_outro(self) -> None:
        self.events.append('show_outro')


class ArcadeOrganizerServiceStub(ArcadeOrganizerService):
    def __init__(self):
        super().__init__(NoLogger(), FetcherStub())

    def make_arcade_organizer_config(self, ini_file_str: str, base_path: str, http_proxy: str = '') -> dict[str, Any]:
        return {}

    def run_arcade_organizer_organize_all_mras(self, config: dict[str, Any]) -> bool:
        return True

    def run_arcade_organizer_print_orgdir_folders(self, config: dict[str, Any]) -> tuple[list[str], bool]:
        return [], True

    def run_arcade_organizer_print_ini_options(self, config: dict[str, Any]) -> bool:
        return True


class RetroAccountServiceTester(RetroAccountService):
    def __init__(self, file_system: FileSystem = None, config_provider: GenericProvider[Config] = None, retroaccount_gateway: RetroAccountGateway = None, encryption: Encryption = None, store_provider: GenericProvider[LocalStore] = None, jtcores_service: JtcoresService = None):
        config_provider = config_provider or GenericProvider[Config]()
        file_system = file_system or FileSystemFactory().create_for_system_scope()
        del store_provider
        super().__init__(
            NoLogger(),
            file_system,
            config_provider,
            retroaccount_gateway or RetroAccountGatewayTester(config_provider=config_provider, file_system=file_system),
            encryption or EncryptionTester(config_provider=config_provider, file_system=file_system),
            jtcores_service or JtcoresServiceStub(),
        )
        self.mister_sync_calls = []

    def mister_sync(self, output) -> None:
        self.mister_sync_calls.append(output)


class JtcoresServiceStub:
    def __init__(self):
        self.enable_private_beta_cores_from_retroaccount_if_allowed_calls = 0

    def enable_private_beta_cores_from_retroaccount_if_allowed(self) -> None:
        self.enable_private_beta_cores_from_retroaccount_if_allowed_calls += 1
