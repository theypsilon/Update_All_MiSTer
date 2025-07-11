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
import datetime
import enum
import os
import time
from typing import List, Optional

from update_all.analogue_pocket.firmware_update import pocket_firmware_update
from update_all.analogue_pocket.pocket_backup import pocket_backup
from update_all.analogue_pocket.utils import is_pocket_mounted
from update_all.arcade_organizer.arcade_organizer import ArcadeOrganizerService
from update_all.cli_output_formatting import CLEAR_SCREEN
from update_all.config import Config
from update_all.databases import Database
from update_all.downloader_utils import prepare_latest_downloader
from update_all.environment_setup import EnvironmentSetup, EnvironmentSetupImpl
from update_all.constants import UPDATE_ALL_VERSION, FILE_update_all_log, FILE_mister_downloader_needs_reboot, \
    MEDIA_FAT, \
    ARCADE_ORGANIZER_INI, MISTER_DOWNLOADER_VERSION, EXIT_CODE_REQUIRES_EARLY_EXIT, FILE_update_all_pyz, \
    EXIT_CODE_CAN_CONTINUE, supporter_plus_patrons, FILE_downloader_needs_reboot_after_linux_update, \
    FILE_downloader_run_signal, FILE_downloader_launcher_downloader_script, FILE_downloader_launcher_update_script
from update_all.countdown import Countdown, CountdownImpl, CountdownOutcome
from update_all.ini_repository import IniRepository, active_databases
from update_all.local_store import LocalStore
from update_all.log_viewer import LogViewer
from update_all.other import Checker, GenericProvider
from update_all.logger import Logger
from update_all.os_utils import OsUtils, LinuxOsUtils
from update_all.settings_screen import SettingsScreen
from update_all.settings_screen_standard_curses_printer import SettingsScreenStandardCursesPrinter
from update_all.settings_screen_trivial_curses_printer import SettingsScreenTrivialCursesPrinter
from update_all.store_migrator import StoreMigrator
from update_all.migrations import migrations
from update_all.local_repository import LocalRepository
from update_all.file_system import FileSystemFactory, FileSystem
from update_all.config_reader import ConfigReader
from update_all.transition_service import TransitionService


@enum.unique
class UpdateAllServicePass(enum.Enum):
    NewRun = 0
    Continue = 1
    NewRunNonStop = 2

class UpdateAllServiceFactory:
    def __init__(self, logger: Logger, local_repository_provider: GenericProvider[LocalRepository]):
        self._logger = logger
        self._local_repository_provider = local_repository_provider

    def create(self, env: dict[str, str]):
        config_provider = GenericProvider[Config]()
        store_provider = GenericProvider[LocalStore]()
        file_system = FileSystemFactory(config_provider, {}, self._logger).create_for_system_scope()
        os_utils = LinuxOsUtils(config_provider=config_provider, logger=self._logger)
        ini_repository = IniRepository(self._logger, file_system=file_system, os_utils=os_utils)
        config_reader = ConfigReader(self._logger, env, ini_repository=ini_repository)
        store_migrator = StoreMigrator(migrations(), self._logger)
        local_repository = LocalRepository(config_provider, self._logger, file_system, store_migrator)
        self._local_repository_provider.initialize(local_repository)
        checker = Checker(file_system=file_system)
        transition_service = TransitionService(logger=self._logger, file_system=file_system, os_utils=os_utils, ini_repository=ini_repository)
        printer = SettingsScreenStandardCursesPrinter()
        ao_service = ArcadeOrganizerService(self._logger)
        settings_screen = SettingsScreen(
            logger=self._logger,
            config_provider=config_provider,
            file_system=file_system,
            ini_repository=ini_repository,
            os_utils=os_utils,
            settings_screen_printer=printer,
            checker=checker,
            local_repository=local_repository,
            store_provider=store_provider,
            ui_runtime=printer,
            ao_service=ao_service
        )
        environment_setup = EnvironmentSetupImpl(
            config_reader=config_reader,
            config_provider=config_provider,
            transition_service=transition_service,
            local_repository=local_repository,
            store_provider=store_provider
        )
        return UpdateAllService(
            config_provider,
            self._logger,
            file_system,
            os_utils,
            CountdownImpl(self._logger),
            settings_screen,
            checker=checker,
            store_provider=store_provider,
            ini_repository=ini_repository,
            environment_setup=environment_setup,
            ao_service=ao_service,
            local_repository=local_repository,
            log_viewer=LogViewer()
        )


class UpdateAllService:
    def __init__(self, config_provider: GenericProvider[Config],
                 logger: Logger,
                 file_system: FileSystem,
                 os_utils: OsUtils,
                 countdown: Countdown,
                 settings_screen: SettingsScreen,
                 checker: Checker,
                 store_provider: GenericProvider[LocalStore],
                 ini_repository: IniRepository,
                 environment_setup: EnvironmentSetup,
                 ao_service: ArcadeOrganizerService,
                 log_viewer: LogViewer,
                 local_repository: LocalRepository):
        self._config_provider = config_provider
        self._logger = logger
        self._file_system = file_system
        self._os_utils = os_utils
        self._countdown = countdown
        self._settings_screen = settings_screen
        self._checker = checker
        self._store_provider = store_provider
        self._ini_repository = ini_repository
        self._environment_setup = environment_setup
        self._ao_service = ao_service
        self._local_repository = local_repository
        self._log_viewer = log_viewer
        self._exit_code = 0
        self._end_time = 0.0
        self._error_reports: List[str] = []
        self._temp_launchers: List[str] = []

    def full_run(self, run_pass: UpdateAllServicePass) -> int:
        if run_pass == UpdateAllServicePass.Continue:
            self._environment_setup.setup_environment()
            self._pre_run_tweaks()
        else:
            env_result = self._environment_setup.setup_environment()
            if env_result.requires_early_exit:
                return EXIT_CODE_REQUIRES_EARLY_EXIT

            self._test_routine()
            self._show_intro()
            self._countdown_for_settings_screen()
            self._print_sequence()
            self._pre_run_tweaks()

            update_all_mtime = self._get_mtime()
            self._run_downloader()
            self._sync_downloader_launcher()

            if run_pass == UpdateAllServicePass.NewRun and update_all_mtime is not None:
                new_update_all_mtime = self._get_mtime()
                if update_all_mtime != new_update_all_mtime:
                    self._logger.debug(f'Update All has changed: {update_all_mtime} != {new_update_all_mtime}')
                    return EXIT_CODE_CAN_CONTINUE

        self._run_pocket_tools()
        self._run_arcade_organizer()
        self._run_linux_update()
        self._cleanup()
        self._show_outro()
        self._finalize_log()
        self._show_interactive_summary()
        self._reboot_if_needed()
        return self._exit_code

    def _test_routine(self) -> None:
        test_routine = os.environ.get('TEST_ROUTINE', None)
        if test_routine is None:
            return

        if test_routine == 'LOG_VIEWER':
            self._log_viewer.show(FILE_update_all_log if self._file_system.is_file(FILE_update_all_log) else 'test_log_viewer.log')
        elif test_routine == 'SETTINGS_SCREEN':
            self._settings_screen.load_test_menu()
        elif test_routine == 'POCKET_FIRMWARE_UPDATE':
            pocket_firmware_update(self._config_provider.get().curl_ssl, self._local_repository, self._logger)
        elif test_routine == 'POCKET_BACKUP':
            pocket_backup(self._logger)
        else:
            self._logger.print(f"Test routine '{test_routine}' not implemented!")
            return

        exit(0)

    def _show_intro(self) -> None:
        self._logger.print()
        self._logger.print(f"                        ------- Update All {UPDATE_ALL_VERSION} --------                        ")
        self._logger.print(f"                        The All-in-One Updater for MiSTer")
        self._logger.print("                        ---------------------------------")
        self._logger.print(f"                          - Powered by Downloader {MISTER_DOWNLOADER_VERSION} -")
        self._logger.print()
        if self._checker.available_code < 2:
            self._logger.print()
            self._logger.print("               ╔═════════════════════════════════════════════════╗              ")
            self._logger.print("               ║  Become a patron to unlock exclusive features!  ║              ")
            self._logger.print("               ║           www.patreon.com/theypsilon            ║              ")
            self._logger.print("               ╚═════════════════════════════════════════════════╝              ")
        else:
            self._logger.print()
            self._logger.print("                    ╔═══════════════════════════════════════╗                   ")
            self._logger.print("                    ║  Thank you so much for your support!  ║                   ")
            self._logger.print("                    ╚═══════════════════════════════════════╝                   ")

        self._logger.print()
        self._logger.print(f'Reading sections from {self._ini_repository.downloader_ini_standard_path()}')
        self._logger.print()

    def _countdown_for_settings_screen(self) -> None:
        self._print_sequence()
        try:
            outcome = self._countdown.execute_count(self._store_provider.get().get_countdown_time())
        except Exception as e:
            self._logger.debug(e)
            self._logger.debug('Recovering from error by suspending countdown.')
            return

        if outcome == CountdownOutcome.CONTINUE:
            return
        elif outcome == CountdownOutcome.SETTINGS_SCREEN:
            pass
        else:
            raise NotImplementedError('No possible countdown outcome')

        self._logger.debug('Loading Settings Screen main menu.')
        try:
            self._settings_screen.load_main_menu()
        except Exception as e:
            self._logger.debug(e)
            self._logger.debug('Recovering from error by suspending settings screen.')
            return

        self._logger.print(CLEAR_SCREEN, end='')

    def _pre_run_tweaks(self):
        config = self._config_provider.get()

        self._logger.bench("Time reset on pre-run stage")
        config.start_time = time.monotonic()

        if config.not_mister:
            self._logger.debug('Not MiSTer environment!')
            config.arcade_organizer = False
            config.update_linux = False
            config.autoreboot = False

    @staticmethod
    def _get_mtime() -> Optional[float]:
        mtime_path = os.path.join('/media/fat', FILE_update_all_pyz)
        if not os.path.exists(mtime_path):
            return None

        return os.path.getmtime(mtime_path)

    def _run_downloader(self) -> None:
        config = self._config_provider.get()
        if len(active_databases(config)) == 0:
            return

        update_linux = config.update_linux
        arcade_organizer = config.arcade_organizer

        if update_linux and arcade_organizer:
            update_linux = False

        return_code = self._execute_downloader(config, self._ini_repository.downloader_ini_path_tweaked_by_config(config), update_linux, None, None)
        if return_code != 0:
            self._exit_code = 10
            self._error_reports.append('Scripts/.config/downloader/downloader.log')

    def _execute_downloader(self, config: Config, downloader_ini_path: str, update_linux: bool, logfile: Optional[str], default_db: Optional[Database]) -> int:
        self._draw_separator()
        env = {
            'DOWNLOADER_INI_PATH': downloader_ini_path,
            'ALLOW_REBOOT': '0',
            'CURL_SSL': config.curl_ssl,
            'UPDATE_LINUX': 'true' if update_linux else 'false',
        }
        if logfile is not None:
            env['LOGFILE'] = logfile
        if default_db is not None:
            env['DEFAULT_DB_ID'] = default_db.db_id
            env['DEFAULT_DB_URL'] = default_db.db_url
            self._logger.print('Running ' + default_db.title)
        else:
            self._logger.print('Running MiSTer Downloader')

        downloader_file = prepare_latest_downloader(self._os_utils, self._file_system, self._logger, consider_bin=True)
        if downloader_file is None:
            return 1

        self._temp_launchers.append(downloader_file)
        self._logger.print()

        if not config.paths_from_downloader_ini and config.base_path != MEDIA_FAT:
            env['DEFAULT_BASE_PATH'] = config.base_path

        if config.not_mister:
            env['DEBUG'] = 'true'

        return_code = self._os_utils.execute_process(downloader_file, env)
        if not self._file_system.is_file(FILE_downloader_run_signal):
            return return_code

        self._logger.print(f"WARNING! {downloader_file} didn't work as expected with error code {return_code}!\n")

        downloader_file = prepare_latest_downloader(self._os_utils, self._file_system, self._logger, consider_bin=False)
        if downloader_file is None:
            return 1

        self._temp_launchers.append(downloader_file)
        return_code = self._os_utils.execute_process(downloader_file, env)
        if not self._file_system.is_file(FILE_downloader_run_signal):
            return return_code

        self._logger.print(f"WARNING! {downloader_file} didn't work as expected with error code {return_code}!\n")

        downloader_file = prepare_latest_downloader(self._os_utils, self._file_system, self._logger, consider_bin=False, consider_zip=False)
        if downloader_file is None:
            return 1

        self._temp_launchers.append(downloader_file)
        return self._os_utils.execute_process(downloader_file, env)

    def _sync_downloader_launcher(self) -> None:
        if not self._file_system.is_file(FILE_downloader_launcher_downloader_script) or not self._file_system.is_file(FILE_downloader_launcher_update_script):
            return

        if self._file_system.compare_files(FILE_downloader_launcher_downloader_script, FILE_downloader_launcher_update_script):
            return

        self._file_system.copy(FILE_downloader_launcher_update_script, FILE_downloader_launcher_downloader_script)
        self._logger.print(f"Updated {FILE_downloader_launcher_downloader_script} launcher.")

    def _run_pocket_tools(self) -> None:
        if not is_pocket_mounted():
            return

        if self._config_provider.get().pocket_firmware_update:
            self._draw_separator()
            self._logger.print('Installing Analogue Pocket Firmware')
            self._logger.print()
            if pocket_firmware_update(self._config_provider.get().curl_ssl, self._local_repository, self._logger):
                self._logger.print()
                self._logger.print('Your Pocket firmware is on the latest version.')
            else:
                self._logger.print()
                self._logger.print('Your Pocket firmware could not be updated.')
                self._os_utils.sleep(6)

            self._logger.print()

        if self._config_provider.get().pocket_backup:
            self._draw_separator()
            self._logger.print('Backing up Analogue Pocket')
            self._logger.print()
            if pocket_backup(self._logger):
                self._logger.print()
                self._logger.print('Your Pocket backup is ready.')
            else:
                self._logger.print()
                self._logger.print('Your Pocket backup could not be created.')
                self._os_utils.sleep(6)

            self._logger.print()

    def _run_arcade_organizer(self) -> None:
        config = self._config_provider.get()
        if not config.arcade_organizer:
            return

        self._draw_separator()
        self._logger.print("Running Arcade Organizer")
        self._logger.print()

        success = self._ao_service.run_arcade_organizer_organize_all_mras(self._ao_service.make_arcade_organizer_config(f'{config.base_path}/{ARCADE_ORGANIZER_INI}'))
        if success is False:
            self._exit_code = 12
            self._error_reports.append('Arcade Organizer')

        self._logger.print()
        self._logger.print("FINISHED: Arcade Organizer")

    def _run_linux_update(self) -> None:
        config = self._config_provider.get()
        if not config.update_linux:
            return

        if len(active_databases(config)) == 0 or not config.arcade_organizer:
            return

        linux_db = Database(db_id='theypsilon/LinuxDB', db_url='https://raw.githubusercontent.com/theypsilon/LinuxDB_MiSTer/db/linuxdb.json', title='Linux Update')
        return_code = self._execute_downloader(config, '/tmp/linux_update.ini', True, f'{config.base_system_path}/Scripts/.config/downloader/update_linux.log', linux_db)
        if return_code != 0:
            self._exit_code = 11
            self._error_reports.append('Scripts/.config/downloader/update_linux.log')

    def _cleanup(self) -> None:
        for file in self._temp_launchers:
            if self._file_system.is_file(file):
                self._file_system.unlink(file, verbose=False)

        self._file_system.clean_temp_files_with_ids()

    def _show_outro(self) -> None:
        self._draw_separator()
        config = self._config_provider.get()

        self._end_time = time.monotonic()
        run_time = str(datetime.timedelta(seconds=self._end_time - config.start_time))[2:-4]
        self._logger.print(f'Update All {UPDATE_ALL_VERSION} ({config.commit[0:3]}) by theypsilon. Run time: {run_time}s at {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        self._logger.debug(f"Commit: {config.commit}")
        self._logger.print()

        if len(self._error_reports):
            self._logger.print("There were some errors in the Updaters.")
            self._logger.print("Therefore, MiSTer hasn't been fully updated.")
            self._logger.print()
            self._logger.print("Check these logs from the Updaters that failed:")
            for log_file in self._error_reports:
                self._logger.print(f" - {log_file}")

            self._logger.print()
            self._logger.print("Maybe a network problem?")
            self._logger.print("Check your connection and then run this script again.")
            self._logger.print()
            self._logger.print(f"Full log for more details: {FILE_update_all_log}")
        else:
            self._logger.print(f"Success! More details at: {FILE_update_all_log}")

        self._logger.print()
        days_since_epoch = int(time.time() // 86400)
        supporter_of_the_day = supporter_plus_patrons[days_since_epoch % len(supporter_plus_patrons)]
        longer_msg = f'Today\'s shoutout is for {supporter_of_the_day}! - Join us at patreon.com/theypsilon'
        if len(longer_msg) <= 80:
            self._logger.print(longer_msg)
        else:
            self._logger.print(f'Shoutout to {supporter_of_the_day}! patreon.com/theypsilon')

    def _finalize_log(self) -> None:
        config = self._config_provider.get()
        should_reboot = not config.not_mister and (
            self._file_system.is_file(FILE_mister_downloader_needs_reboot) or
            self._file_system.is_file(FILE_downloader_needs_reboot_after_linux_update)
        )
        if should_reboot and not config.autoreboot:
            self._logger.print("You should reboot")
            self._logger.print()

        self._logger.finalize()

    def _show_interactive_summary(self) -> None:
        if self._config_provider.get().log_viewer:
            try:
                self._log_viewer.show(self._file_system.resolve(FILE_update_all_log))
            except Exception as e:
                self._logger.debug(e)
                self._logger.debug('Recovering from error by suspending log viewer.')

    def _reboot_if_needed(self) -> None:
        config = self._config_provider.get()
        if config.not_mister:
            return

        linux_reboot = self._file_system.is_file(FILE_downloader_needs_reboot_after_linux_update)
        if not self._file_system.is_file(FILE_mister_downloader_needs_reboot) and not linux_reboot:
            return

        if not config.autoreboot:
            return

        outro_time = int(time.monotonic() - self._end_time)
        prudent_time = 30 if linux_reboot else 5

        if outro_time < prudent_time:
            reboot_time = prudent_time - outro_time
            self._logger.print(f"\nRebooting in {reboot_time} seconds...")
            self._os_utils.sleep(reboot_time)
        else:
            self._logger.print("\nRebooting now...")

        self._os_utils.reboot()

    def _print_sequence(self) -> None:
        self._logger.print('Sequence:')
        lines = 0
        config = self._config_provider.get()
        for db in active_databases(config):
            lines += 1
            self._logger.print(f'- {db.title}')
        if config.arcade_organizer:
            lines += 1
            self._logger.print('- Arcade Organizer')
        if config.pocket_firmware_update:
            lines += 1
            self._logger.print('- Analogue Pocket Firmware')

        if config.pocket_backup:
            lines += 1
            self._logger.print('- Analogue Pocket Backup')

        if lines == 0:
            self._logger.print('- Nothing to do!')

        self._logger.print()

    def _draw_separator(self) -> None:
        self._logger.print()
        self._logger.print()
        self._logger.print("################################################################################")
        self._logger.print("#==============================================================================#")
        self._logger.print("################################################################################")
        self._logger.print()
        self._os_utils.sleep(self._store_provider.get().get_wait_time_for_reading())
