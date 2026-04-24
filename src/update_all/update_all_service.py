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
import datetime
import enum
import os
import time
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional

from update_all.analogue_pocket.firmware_update import pocket_firmware_update
from update_all.analogue_pocket.pocket_backup import pocket_backup
from update_all.analogue_pocket.utils import is_pocket_mounted
from update_all.arcade_organizer.arcade_organizer import ArcadeOrganizerService
from update_all.cli_output_formatting import CLEAR_SCREEN
from update_all.config import Config
from update_all.databases import Database, all_dbs
from update_all.downloader_utils import prepare_latest_downloader
from update_all.encryption import Encryption
from update_all.environment_setup import EnvironmentSetup, EnvironmentSetupImpl
from update_all.constants import UPDATE_ALL_VERSION, FILE_update_all_log, FILE_mister_downloader_needs_reboot, \
    MEDIA_FAT, \
    ARCADE_ORGANIZER_INI, MISTER_DOWNLOADER_VERSION, EXIT_CODE_REQUIRES_EARLY_EXIT, FILE_update_all_pyz, \
    EXIT_CODE_CAN_CONTINUE, supporter_plus_patrons, FILE_downloader_needs_reboot_after_linux_update, \
    FILE_downloader_run_signal, FILE_downloader_launcher_downloader_script, FILE_downloader_launcher_update_script, \
    COMMAND_TIMELINE, COMMAND_LATEST_LOG, BACKGROUND_JOBS_HARD_TIMEOUT, \
    FILE_update_all_print_tmp_log, FILE_mister_version, FILE_JOTEGO_mra_pack_ini, BACKGROUND_JOBS_SOFT_TIMEOUT
from update_all.countdown import Countdown, CountdownImpl, CountdownOutcome
from update_all.ini_repository import IniRepository, active_databases
from update_all.local_store import LocalStore
from update_all.log_viewer import LogViewer, create_log_document, to_overscanned_doc
from update_all.other import GenericProvider, terminal_size
from update_all.logger import Logger, close_print_tmp_log_file
from update_all.os_utils import OsUtils, LinuxOsUtils
from update_all.settings_screen import SettingsScreen
from update_all.settings_screen_standard_curses_printer import SettingsScreenStandardCursesPrinter
from update_all.settings_screen_trivial_curses_printer import SettingsScreenTrivialCursesPrinter
from update_all.store_migrator import StoreMigrator
from update_all.migrations import migrations
from update_all.local_repository import LocalRepository
from update_all.file_system import FileSystemFactory, FileSystem
from update_all.config_reader import ConfigReader
from update_all.timeline import Timeline
from update_all.transition_service import TransitionService
from update_all.fetcher import Fetcher
from update_all.mister_video_mode_ui import MisterVideoModeService
from update_all.retroaccount import RetroAccountService
from update_all.retroaccount_gateway import RetroAccountGateway


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
        fetcher = Fetcher(config_provider, logger=None)
        os_utils = LinuxOsUtils(config_provider=config_provider, logger=self._logger, fetcher=fetcher)
        ini_repository = IniRepository(self._logger, file_system=file_system, os_utils=os_utils)
        config_reader = ConfigReader(self._logger, env, ini_repository=ini_repository)
        store_migrator = StoreMigrator(migrations(), self._logger)
        local_repository = LocalRepository(self._logger, file_system, store_migrator)
        self._local_repository_provider.initialize(local_repository)
        transition_service = TransitionService(logger=self._logger, file_system=file_system, os_utils=os_utils, ini_repository=ini_repository)
        printer = SettingsScreenStandardCursesPrinter()
        ao_service = ArcadeOrganizerService(self._logger, fetcher)
        encryption = Encryption(self._logger, config_provider, file_system)
        retroaccount_gateway = RetroAccountGateway(config_provider, self._logger, file_system, fetcher)
        retroaccount = RetroAccountService(self._logger, file_system, config_provider, retroaccount_gateway, encryption)
        mister_video_mode_service = MisterVideoModeService(self._logger, file_system, config_provider, os_utils)
        settings_screen = SettingsScreen(
            logger=self._logger,
            config_provider=config_provider,
            file_system=file_system,
            ini_repository=ini_repository,
            os_utils=os_utils,
            mister_video_mode_service=mister_video_mode_service,
            settings_screen_printer=printer,
            local_repository=local_repository,
            store_provider=store_provider,
            ui_runtime=printer,
            ao_service=ao_service,
            encryption=encryption,
            retroaccount=retroaccount
        )
        environment_setup = EnvironmentSetupImpl(
            logger=self._logger,
            config_reader=config_reader,
            config_provider=config_provider,
            transition_service=transition_service,
            local_repository=local_repository,
            store_provider=store_provider,
            file_system=file_system
        )
        timeline = Timeline(self._logger, config_provider, file_system, encryption, retroaccount)
        return UpdateAllService(
            config_provider,
            self._logger,
            file_system,
            os_utils,
            CountdownImpl(self._logger),
            settings_screen,
            store_provider=store_provider,
            ini_repository=ini_repository,
            environment_setup=environment_setup,
            ao_service=ao_service,
            local_repository=local_repository,
            log_viewer=LogViewer(file_system, config_provider, store_provider, retroaccount),
            timeline=timeline,
            retroaccount=retroaccount,
            fetcher=fetcher
        )


def calculate_supporter_shoutout(config: Config, supporter_name: str) -> str:
    usable_columns = config.term_size.columns - config.overscan_dim.cols * 2
    message_tiers = [
        f"Today's shoutout is for {supporter_name}! - Join us at patreon.com/theypsilon",
        f"Shoutout to {supporter_name}! patreon.com/theypsilon",
        f"Thanks {supporter_name}! patreon.com/theypsilon",
    ]

    for message in message_tiers:
        if len(message) <= usable_columns:
            return message

    return message_tiers[-1]


def calculate_outro_summary(config: Config, run_time: str, timestamp: str) -> str:
    usable_columns = config.term_size.columns - config.overscan_dim.cols * 2
    message_tiers = [
        f'Update All {UPDATE_ALL_VERSION} ({config.commit[0:3]}) by theypsilon. Run time: {run_time}s at {timestamp}',
        f'Update All {UPDATE_ALL_VERSION} by theypsilon {run_time}s {timestamp}',
        f'Update All {UPDATE_ALL_VERSION}: {run_time}s {timestamp}',
        f'Update All {UPDATE_ALL_VERSION}: {run_time}s',
    ]

    for message in message_tiers:
        if len(message) <= usable_columns:
            return message

    return message_tiers[-1]


def format_run_time(elapsed_seconds: float) -> str:
    total_seconds = int(elapsed_seconds)
    centiseconds = int((elapsed_seconds - total_seconds) * 100)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f'{hours}:{minutes:02}:{seconds:02}.{centiseconds:02}'
    return f'{minutes:02}:{seconds:02}.{centiseconds:02}'


def calculate_success_summary(config: Config, log_path: str) -> str:
    usable_columns = config.term_size.columns - config.overscan_dim.cols * 2
    message_tiers = [
        f'Success! More details at: {log_path}',
        f'Success! Log: {log_path}',
        'Success! Log saved.',
    ]

    for message in message_tiers:
        if len(message) <= usable_columns:
            return message

    return message_tiers[-1]


def calculate_reading_sections_summary(config: Config, downloader_ini_path: str) -> Optional[str]:
    usable_columns = config.term_size.columns - config.overscan_dim.cols * 2
    message = f'Reading sections from {downloader_ini_path}'
    if len(message) <= usable_columns:
        return message
    return None


class UpdateAllService:
    def __init__(self, config_provider: GenericProvider[Config],
                 logger: Logger,
                 file_system: FileSystem,
                 os_utils: OsUtils,
                 countdown: Countdown,
                 settings_screen: SettingsScreen,
                 store_provider: GenericProvider[LocalStore],
                 ini_repository: IniRepository,
                 environment_setup: EnvironmentSetup,
                 ao_service: ArcadeOrganizerService,
                 log_viewer: LogViewer,
                 local_repository: LocalRepository,
                 timeline: Timeline,
                 retroaccount: RetroAccountService,
                 fetcher: Fetcher):
        self._config_provider = config_provider
        self._logger = logger
        self._file_system = file_system
        self._os_utils = os_utils
        self._countdown = countdown
        self._settings_screen = settings_screen
        self._store_provider = store_provider
        self._ini_repository = ini_repository
        self._environment_setup = environment_setup
        self._ao_service = ao_service
        self._local_repository = local_repository
        self._log_viewer = log_viewer
        self._timeline = timeline
        self._retroaccount = retroaccount
        self._fetcher = fetcher
        self._exit_code = 0
        self._end_time = 0.0
        self._error_reports: list[str] = []
        self._temp_launchers: list[str] = []
        self._timeline_after_log_doc: list[str] = []
        self._executor: Optional[ThreadPoolExecutor] = None
        self._background_job_future: Optional[Future] = None
        self._update_all_md5: Optional[str] = None

    def full_run(self, run_pass: UpdateAllServicePass) -> int:
        if self._is_media_fat_read_only():
            self._logger.print('The SD card is temporarily not writable.')
            self._logger.print('This is usually resolved by rebooting your MiSTer.')
            return 0

        ts = terminal_size()
        if run_pass == UpdateAllServicePass.Continue:
            self._environment_setup.setup_environment(ts)
            self._pre_run_tweaks()
        else:
            env_result = self._environment_setup.setup_environment(ts)
            if env_result.requires_early_exit:
                return EXIT_CODE_REQUIRES_EARLY_EXIT

            command = self._config_provider.get().command
            if command == COMMAND_TIMELINE:
                self._download_update_all_db_and_show_interactive_timeline()
                return self._exit_code
            elif command == COMMAND_LATEST_LOG:
                self._show_log_viewer_with_latest_log()
                return self._exit_code

            self._test_routine()
            self._start_background_jobs()
            self._show_intro()
            self._countdown_for_settings_screen()
            self._print_sequence()
            self._pre_run_tweaks()
            self._soft_wait_background_jobs()
            self._run_downloader()
            self._sync_downloader_launcher()

            if run_pass == UpdateAllServicePass.NewRun and self._update_all_md5 is not None:
                new_update_all_md5 = self._calc_md5()
                if self._update_all_md5 != new_update_all_md5:
                    self._logger.debug(f'Update All has changed: {self._update_all_md5} != {new_update_all_md5}')
                    return EXIT_CODE_CAN_CONTINUE

        self._run_pocket_tools()
        self._run_arcade_organizer()
        self._cleanup()
        self._hard_wait_background_jobs()
        self._show_outro()
        self._show_interactive_log_viewer_and_timeline()
        self._reboot_if_needed()
        return self._exit_code

    def _is_media_fat_read_only(self) -> bool:
        if not os.path.isfile(FILE_mister_version):
            return False
        try:
            with open('/proc/mounts') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 4 and parts[1] == MEDIA_FAT:
                        return 'ro' in parts[3].split(',')
        except OSError:
            pass
        return False

    def _test_routine(self) -> None:
        test_routine = os.environ.get('TEST_ROUTINE', None)
        if test_routine is None:
            return

        if test_routine == 'TIMELINE':
            config = self._config_provider.get()
            ts = config.term_size
            oc = config.overscan_dim
            columns = ts.columns
            cols_overscan = oc.cols
            log_doc = create_log_document(FILE_update_all_log if self._file_system.is_file(FILE_update_all_log) else 'test_log_viewer.log')
            timeline_doc = self._timeline.load_timeline_doc(env_check_skip=True)
            log_doc = to_overscanned_doc(log_doc, columns, cols_overscan)
            timeline_doc = to_overscanned_doc(timeline_doc, columns, cols_overscan)
            total_doc = [*log_doc, *timeline_doc]
            index = len(timeline_doc)
            if index > 2:
                index -= 2

            self._log_viewer.show(total_doc, {}, index)
        elif test_routine == 'SETTINGS_SCREEN':
            self._settings_screen.load_test_menu()
        elif test_routine == 'POCKET_FIRMWARE_UPDATE':
            pocket_firmware_update(self._config_provider.get().curl_ssl, self._local_repository, self._logger, self._config_provider.get().http_config)
        elif test_routine == 'POCKET_BACKUP':
            pocket_backup(self._logger)
        else:
            self._logger.print(f"Test routine '{test_routine}' not implemented!")
            return

        exit(0)

    def _start_background_jobs(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._background_job_future = self._executor.submit(self._background_job)

    def _background_job(self) -> None:
        self._logger.bench('UpdateAllService: Background job START')
        self._update_all_md5 = self._calc_md5()
        self._retroaccount.mister_sync()
        self._logger.bench('UpdateAllService: Background job END')

    def _show_intro(self) -> None:
        config = self._config_provider.get()
        ts = config.term_size
        oc = config.overscan_dim
        usable = ts.columns - oc.cols * 2
        def _center(text):
            return text.center(usable)

        self._logger.print()
        title_text = f" Update All {UPDATE_ALL_VERSION} "
        title_dashes = usable - len(title_text)
        left_dashes = title_dashes // 2
        right_dashes = title_dashes - left_dashes
        self._logger.print(_center("-" * left_dashes + title_text + "-" * right_dashes))
        subtitle = "The All-in-One Updater for MiSTer"
        if len(subtitle) > usable:
            subtitle = "The Updater for MiSTer"
        powered = f"- Powered by Downloader {MISTER_DOWNLOADER_VERSION} -"
        if len(powered) > usable:
            powered = f"- Downloader {MISTER_DOWNLOADER_VERSION} -"
        self._logger.print(_center(subtitle))
        self._logger.print(_center("-" * min(33, usable)))
        self._logger.print(_center(powered))
        self._logger.print()
        if not self._retroaccount.is_update_all_extras_active():
            self._logger.print()
            if not ts.cnarrow:
                self._logger.print(_center("╔═════════════════════════════════════════════════╗"))
                self._logger.print(_center("║  Become a patron to unlock exclusive features!  ║"))
                self._logger.print(_center("║           www.patreon.com/theypsilon            ║"))
                self._logger.print(_center("╚═════════════════════════════════════════════════╝"))
            else:
                self._logger.print(_center("Become a patron to unlock"))
                self._logger.print(_center("exclusive features!"))
                self._logger.print(_center("www.patreon.com/theypsilon"))
        else:
            self._logger.print()
            if not ts.cnarrow:
                self._logger.print(_center("╔═══════════════════════════════════════╗"))
                self._logger.print(_center("║  Thank you so much for your support!  ║"))
                self._logger.print(_center("╚═══════════════════════════════════════╝"))
            else:
                self._logger.print(_center("Thank you so much"))
                self._logger.print(_center("for your support!"))

        self._logger.print()
        reading_sections_summary = calculate_reading_sections_summary(config, self._ini_repository.downloader_ini_standard_path())
        if reading_sections_summary is not None:
            self._logger.print(reading_sections_summary)
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
            self._logger.print()
            self._logger.debug(e)
            self._logger.print('Recovering from error by suspending settings screen.\n')
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

    def _calc_md5(self) -> Optional[float]:
        if not self._file_system.is_file(FILE_update_all_pyz):
            return None

        return self._file_system.file_mtime(FILE_update_all_pyz)

    def _run_downloader(self) -> None:
        config = self._config_provider.get()
        if len(active_databases(config)) == 0 or config.skip_downloader:
            return

        self._draw_separator()
        return_code = self._execute_downloader(config, self._ini_repository.downloader_ini_path_tweaked_by_config(config), config.update_linux, None, None)
        if return_code != 0:
            self._exit_code = 10
            self._error_reports.append('Scripts/.config/downloader/downloader.log')

    def _execute_downloader(self, config: Config, downloader_ini_path: str, update_linux: bool, logfile: Optional[str], default_db: Optional[Database], quiet: bool = False) -> int:
        ts = config.term_size
        oc = config.overscan_dim
        env = {
            'DOWNLOADER_INI_PATH': downloader_ini_path,
            'ALLOW_REBOOT': '0',
            'CURL_SSL': config.curl_ssl,
            'COLUMNS': str(ts.columns - oc.cols * 2),
            'LINES': str(ts.lines - oc.lines * 2),
            'UPDATE_LINUX': 'true' if update_linux else 'false',
        }
        if self._file_system.is_file(FILE_JOTEGO_mra_pack_ini):
            env['EXTRA_DROP_IN_DATABASE_FILES'] = FILE_JOTEGO_mra_pack_ini
        if logfile is not None:
            env['LOGFILE'] = logfile
        if default_db is not None:
            env['DEFAULT_DB_ID'] = default_db.db_id
            env['DEFAULT_DB_URL'] = default_db.db_url

        if not quiet:
            if default_db is None:
                self._logger.print('Running MiSTer Downloader')
            else:
                self._logger.print('Running ' + default_db.title)

        downloader_file = prepare_latest_downloader(self._os_utils, self._file_system, self._logger, consider_bin=True)
        if downloader_file is None:
            return 1

        self._temp_launchers.append(downloader_file)
        if not quiet:
            self._logger.print()

        if not config.paths_from_downloader_ini and config.base_path != MEDIA_FAT:
            env['DEFAULT_BASE_PATH'] = config.base_path

        if config.not_mister:
            env['DEBUG'] = 'true'

        return_code = self._os_utils.execute_process(downloader_file, env, quiet)
        if not self._file_system.is_file(FILE_downloader_run_signal):
            return return_code

        self._logger.print(f"WARNING! {downloader_file} didn't work as expected with error code {return_code}!\n")

        downloader_file = prepare_latest_downloader(self._os_utils, self._file_system, self._logger, consider_bin=False)
        if downloader_file is None:
            return 1

        self._temp_launchers.append(downloader_file)
        return_code = self._os_utils.execute_process(downloader_file, env, quiet)
        if not self._file_system.is_file(FILE_downloader_run_signal):
            return return_code

        self._logger.print(f"WARNING! {downloader_file} didn't work as expected with error code {return_code}!\n")

        downloader_file = prepare_latest_downloader(self._os_utils, self._file_system, self._logger, consider_bin=False, consider_zip=False)
        if downloader_file is None:
            return 1

        self._temp_launchers.append(downloader_file)
        return self._os_utils.execute_process(downloader_file, env, quiet)

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
            if pocket_firmware_update(self._config_provider.get().curl_ssl, self._local_repository, self._logger, self._config_provider.get().http_config):
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

        success = self._ao_service.run_arcade_organizer_organize_all_mras(self._ao_service.make_arcade_organizer_config(f'{config.base_path}/{ARCADE_ORGANIZER_INI}', config.base_path, config.http_proxy))
        if success is False:
            self._exit_code = 12
            self._error_reports.append('Arcade Organizer')

        self._logger.print()
        self._logger.print("FINISHED: Arcade Organizer")

    def _soft_wait_background_jobs(self) -> None:
        if self._executor is None:
            return

        if self._background_job_future is None:
            return

        deadline = time.monotonic() + BACKGROUND_JOBS_SOFT_TIMEOUT
        self._logger.bench("UpdateAllService: Background Soft Wait START")
        while not self._retroaccount.has_synced() and time.monotonic() < deadline:
            time.sleep(0.1)

        if self._retroaccount.has_synced():
            self._logger.bench("UpdateAllService: Background Soft Wait END completed")
        else:
            self._logger.bench("UpdateAllService: Background Soft Wait END pending")

    def _hard_wait_background_jobs(self) -> None:
        if self._executor is not None:
            if self._background_job_future is not None:
                try:
                    deadline = time.monotonic() + BACKGROUND_JOBS_HARD_TIMEOUT
                    while not self._background_job_future.done() and time.monotonic() < deadline:
                        self._logger.print('.', end='', flush=True)
                        time.sleep(0.25)

                    if not self._background_job_future.done():
                        self._fetcher.cleanup()
                        self._background_job_future.result(timeout=5)
                    self._background_job_future = None
                    self._logger.print(flush=True)

                except Exception as e:
                    self._logger.debug('Background job did not finish in time')
                    self._logger.debug(e)

            self._executor.shutdown(wait=False)
            self._executor = None

    def _cleanup(self) -> None:
        for file in self._temp_launchers:
            if self._file_system.is_file(file):
                self._file_system.unlink(file, verbose=False)

        self._file_system.clean_temp_files_with_ids()

    def _show_outro(self) -> None:
        self._draw_separator()
        config = self._config_provider.get()

        self._end_time = time.monotonic()
        run_time = format_run_time(self._end_time - config.start_time)
        self._logger.print(calculate_outro_summary(config, run_time, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self._logger.debug(f"Commit: {config.commit}")
        self._logger.debug(f"Boot time: {config.boot_time}")
        for kind, debug_msg in self._retroaccount.consume_important_messages():
            if kind == 'debug': self._logger.debug(debug_msg)
            elif kind == 'print': self._logger.print(debug_msg)
            else: self._logger.debug(f'Unknown message kind from RetroAccount: {kind} with message: {debug_msg}')

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
            self._logger.print(calculate_success_summary(config, FILE_update_all_log))

        self._logger.print()
        days_since_epoch = int(time.time() // 86400)
        supporter_of_the_day = supporter_plus_patrons[days_since_epoch % len(supporter_plus_patrons)]
        self._logger.print(calculate_supporter_shoutout(self._config_provider.get(), supporter_of_the_day))

    def _show_interactive_log_viewer_and_timeline(self) -> None:
        config = self._config_provider.get()
        if config.log_viewer:
            try:
                close_print_tmp_log_file()
                log_doc = create_log_document(FILE_update_all_print_tmp_log) if config.log_viewer else []
                timeline_doc = []
                if config.timeline_after_logs:
                    try:
                        timeline_doc = self._timeline.load_timeline_doc()
                    except Exception as e:
                        self._logger.debug(e)
                        self._logger.debug('Recovering from error by suspending timeline generation after logs.')

                config = self._config_provider.get()
                ts = config.term_size
                oc = config.overscan_dim
                columns = ts.columns
                cols_overscan = oc.cols
                usable = columns - cols_overscan * 2

                if len(log_doc) > 0 and len(timeline_doc) > 0:
                    log_doc.append("\n")
                    log_doc.append("=" * usable + "\n")
                    log_doc.append("\n")
                    log_doc.append("GO DOWN TO CHECK A SUMMARY OF WHAT'S BEEN UPDATED!!".center(usable) + "\n")

                log_doc = to_overscanned_doc(log_doc, columns, cols_overscan)
                timeline_doc = to_overscanned_doc(timeline_doc, columns, cols_overscan)
                total_doc = [*log_doc, *timeline_doc]
                index = len(timeline_doc)
                if index > 5:
                    index -= 5

                if len(total_doc) > 0:
                    self._log_viewer.show(total_doc, {}, index)
            except Exception as e:
                self._logger.debug(e)
                self._logger.debug('Recovering from error by suspending log viewer.')

    def _show_log_viewer_with_latest_log(self) -> None:
        config = self._config_provider.get()
        ts = config.term_size
        oc = config.overscan_dim
        try:
            latest_log = create_log_document(self._file_system.resolve(FILE_update_all_log))
            latest_log = to_overscanned_doc(latest_log, ts.columns, oc.cols)
            self._log_viewer.show(latest_log, {}, 0)
        except Exception as e:
            self._logger.debug(e)
            self._logger.print("Could not load the latest log. Please try again after running Update All.")

    def _download_update_all_db_and_show_interactive_timeline(self) -> None:
        config = self._config_provider.get()
        timeline_log = f'{config.base_system_path}/Scripts/.config/downloader/timeline_download.log'
        timeline_ini = '/tmp/timeline_downloader.ini'
        self._file_system.unlink(timeline_ini)
        db_defs = all_dbs(config.mirror)
        return_code = self._execute_downloader(config, timeline_ini, False, timeline_log, db_defs.UPDATE_ALL_MISTER, quiet=True)
        self._logger.print()
        if return_code != 0:
            self._logger.print('The Timeline data could not be updated because of an internet connection problem. Try again later to see an updated Timeline.')

        timeline_doc = self._timeline.load_timeline_doc(env_check_skip=True)
        if len(timeline_doc) > 0:
            self._logger.print('Showing interactive Update Timeline viewer:')
            timeline_doc = to_overscanned_doc(timeline_doc, config.term_size.columns, config.overscan_dim.cols)
            self._log_viewer.show(timeline_doc, {}, len(timeline_doc))
        else:
            self._logger.print('No timeline entries found. Try again later!')

        self._logger.print(''.join(timeline_doc))

    def _reboot_if_needed(self) -> None:
        config = self._config_provider.get()
        if config.not_mister:
            return

        linux_reboot = self._file_system.is_file(FILE_downloader_needs_reboot_after_linux_update)
        if not self._file_system.is_file(FILE_mister_downloader_needs_reboot) and not linux_reboot:
            return

        if not config.autoreboot:
            self._logger.print("You should reboot")
            self._logger.print()
            return

        outro_time = int(time.monotonic() - self._end_time)
        prudent_time = 30 if linux_reboot else 5

        if outro_time < prudent_time:
            reboot_time = prudent_time - outro_time
            self._logger.print(f"\nRebooting in {reboot_time} seconds...")
            self._os_utils.sleep(reboot_time)
        else:
            self._logger.print("\nRebooting now...")

        self._logger.finalize()
        self._os_utils.reboot()

    def _print_sequence(self) -> None:
        self._logger.print('Sequence:')
        lines = 0
        config = self._config_provider.get()
        manuals_cnt = 0
        for db in active_databases(config):
            if db.db_id.startswith('ajgowans/manualsdb-'):
                manuals_cnt += 1
            else:
                lines += 1
                self._logger.print(f'- {db.title}')
        if manuals_cnt > 0:
            lines += 1
            self._logger.print(f'- {manuals_cnt} Game Manuals (EN) DBs')
        if config.arcade_organizer:
            lines += 1
            self._logger.print('- Arcade Organizer')
        if config.pocket_firmware_update:
            lines += 1
            self._logger.print('- Analogue Pocket Firmware')

        if config.pocket_backup:
            lines += 1
            self._logger.print('- Analogue Pocket Backup')

        if self._file_system.is_file(FILE_JOTEGO_mra_pack_ini):
            lines += 1
            self._logger.print('- JT MRA Kai')

        if lines == 0:
            self._logger.print('- Nothing to do!')

        self._logger.print()

    def _draw_separator(self) -> None:
        config = self._config_provider.get()
        usable = config.term_size.columns - config.overscan_dim.cols * 2
        self._logger.print()
        self._logger.print()
        self._logger.print("#" * usable)
        self._logger.print("#" + "=" * (usable - 2) + "#")
        self._logger.print("#" * usable)
        self._logger.print()
