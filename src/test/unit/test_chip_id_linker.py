import os
import signal
import struct
import unittest
from pathlib import Path

from test.chip_id_linker_tester import ChipIdLinkerTester
from test.chip_id_system_tester import ChipIdProcessTester
from update_all.chip_id_linker import chip_id_linker
from update_all.constants import KENV_LAUNCH_ORIGIN_ID


class TestChipIdLinker(unittest.TestCase):
    def setUp(self):
        self.linker = ChipIdLinkerTester()
        self.addCleanup(self.linker.close)
        self.system = self.linker.system
        self.rbf_path = '/media/fat/Scripts/.config/update_all/Linker.rbf'
        self.system.path(self.rbf_path).parent.mkdir(parents=True)
        self.system.path(self.rbf_path).write_bytes(b'rbf')
        self.update_all_dir = '/media/fat/Scripts'

    def test_main___blank_display_command___does_not_require_rbf_or_update_all_launcher(self):
        Path(self.linker.log_path).write_text('stale\n')

        result = self.linker.run_command(['--blank-display'])

        self.assertEqual(0, result)
        memory = self.system.path('/dev/mem').read_bytes()
        self.assertEqual(1, struct.unpack_from('<I', memory, chip_id_linker.CHIP_ID_REG_DISPLAY_CONTROL)[0])
        self.assertTrue(Path(self.linker.log_path).read_text().startswith('stale\n'))
        self.assertEqual([], self.system.core_commands)

    def test_main___restore_after_relaunch_command___does_not_clear_existing_log(self):
        Path(self.linker.log_path).write_text('stale\n')

        result = self.linker.run_command(['--restore-after-relaunch'])

        self.assertEqual(0, result)
        self.assertTrue(Path(self.linker.log_path).read_text().startswith('stale\n'))
        self.assertIn(('key', chip_id_linker.CHIP_ID_KEY_F12, 1), self.system.events)
        self.assertEqual([], self.system.core_commands)

    def test_main___extract_only_command___does_not_require_update_all_launcher_and_prints_result(self):
        Path(self.linker.log_path).write_text('stale\n')

        result = self.linker.run_command(['--extract-only', '--rbf', self.rbf_path])

        self.assertEqual(0, result)
        self.assertEqual(['0123456789abcdef'], self.system.printed_results)
        self.assertNotIn('stale', Path(self.linker.log_path).read_text().splitlines())
        self.assertEqual([f'load_core {self.rbf_path}', 'load_core menu.rbf'], self.system.core_commands)
        self.assertEqual([], self.system.popen_calls)

    def test_main___detached_extraction_command___starts_with_clean_log(self):
        Path(self.linker.log_path).write_text('stale\n')

        result = self.linker.run_command(['--rbf', self.rbf_path, '--update-all-dir', self.update_all_dir])

        self.assertEqual(0, result)
        self.assertNotIn('stale', Path(self.linker.log_path).read_text().splitlines())
        self.assertEqual([f'load_core {self.rbf_path}'], self.system.core_commands)
        self.assertEqual('0123456789abcdef\n', self.system.read_text(chip_id_linker.CHIP_ID_RESULT_HANDOFF_PATH))
        self.assertEqual(1, len(self.system.popen_calls))

    def test_main___detached_extraction_command___publishes_marker_and_log_before_extraction(self):
        marker = str(self.linker.root / 'worker.started')

        result = self.linker.run_command([
            '--rbf', self.rbf_path, '--update-all-dir', self.update_all_dir, '--startup-marker', marker,
        ])

        self.assertEqual(0, result)
        observation = self.system.observations_at_load[0]
        self.assertTrue(observation['marker'])
        self.assertIn('_write_worker_startup_marker: wrote', observation['log'])
        self.assertIn('_load_core: writing command:', observation['log'])
        self.assertEqual(str(os.getpid()), Path(marker).read_text().strip())
        self.assertEqual(1, Path(self.linker.log_path).read_text().count('_run_detached_chip_id_extraction: started'))

    def test_main___detached_extraction_command___preserves_eager_log_after_hard_exit(self):
        process, markers = self.linker.run_hard_exit_worker()

        self.assertEqual(23, process.returncode, process.stderr)
        self.assertEqual([self.linker.root / 'worker.started'], markers)
        log = Path(self.linker.log_path).read_text()
        self.assertIn('_write_worker_startup_marker: wrote', log)
        self.assertIn('worker log before hard exit', log)

    def test_main___blank_display_command___appends_log_when_finalized(self):
        Path(self.linker.log_path).write_text('primary\n')

        result = self.linker.run_command(['--blank-display'])
        self.linker.file_logger.finalize()

        self.assertEqual(0, result)
        log = Path(self.linker.log_path).read_text()
        self.assertTrue(log.startswith('primary\n'))
        self.assertEqual(1, log.count('_blank_chip_id_core_display: requesting black display'))
        self.assertEqual(1, log.count('_write_chip_id_display_control: writer process completed'))

    def test_main___detached_extraction_command___preserves_direct_relaunch_script_log_when_finalized(self):
        Path(self.linker.log_path).write_text('stale\n')
        self.system.append_external_log_on_load = True

        result = self.linker.run_command(['--rbf', self.rbf_path, '--update-all-dir', self.update_all_dir])
        self.linker.file_logger.finalize()

        self.assertEqual(0, result)
        log = Path(self.linker.log_path).read_text()
        self.assertNotIn('stale', log.splitlines())
        self.assertIn('relaunch_script: started\n', log)
        self.assertIn('_run_detached_chip_id_extraction: started', log)
        self.assertEqual(1, log.count('relaunch_script: started\n'))

    def test_extract_chip_id_without_relaunch___loads_core_reads_id_and_restores_menu(self):
        result = chip_id_linker._extract_chip_id_without_relaunch(self.rbf_path, self.linker)

        self.assertEqual('0123456789abcdef', result)
        self.assertEqual([f'load_core {self.rbf_path}', 'load_core menu.rbf'], self.system.core_commands)
        self.assertEqual([('/dev/MiSTer_cmd', os.O_WRONLY | os.O_NONBLOCK)] * 2,
                         [call for call in self.system.opened_devices if call[0] == '/dev/MiSTer_cmd'])
        self.assertEqual(2, self.system.closed_devices.count('/dev/MiSTer_cmd'))
        self.assertEqual('MENU\n', self.system.read_text(chip_id_linker.CHIP_ID_MENU_CORE_NAME_PATH))
        self.assertEqual([], self.system.popen_calls)

    def test_run_detached_chip_id_extraction___writes_load_core_to_fifo_and_relaunches_with_chip_id_result(self):
        chip_id_linker._run_detached_chip_id_extraction(self.linker, self.rbf_path, self.update_all_dir)

        self.assertEqual([f'load_core {self.rbf_path}'], self.system.core_commands)
        self.assertEqual(1, self.system.closed_devices.count('/dev/MiSTer_cmd'))
        self.assertEqual('0123456789abcdef\n', self.system.read_text(chip_id_linker.CHIP_ID_RESULT_HANDOFF_PATH))
        script = self.system.read_text(chip_id_linker.CHIP_ID_RELAUNCH_SCRIPT_PATH)
        self.assertIn('--restore-menu-after-relaunch', script)
        self.assertIn('mark_update_all_relaunch_started()', script)
        self.assertEqual(1, len(self.system.popen_calls))

    def test_run_detached_chip_id_extraction___when_fifo_write_fails___relaunches_with_failure_result(self):
        self.system.failed_core_loads.add(self.rbf_path)

        chip_id_linker._run_detached_chip_id_extraction(self.linker, self.rbf_path, self.update_all_dir)

        self.assertEqual([], self.system.memory_maps)
        self.assertEqual([], self.system.isolated_processes)
        self.assertEqual('FAILURE_LOAD_CORE_FIFO\n', self.system.read_text(chip_id_linker.CHIP_ID_RESULT_HANDOFF_PATH))
        script = self.system.read_text(chip_id_linker.CHIP_ID_RELAUNCH_SCRIPT_PATH)
        self.assertNotIn('--restore-menu-after-relaunch', script)
        self.assertIn('mark_update_all_relaunch_started()', script)
        self.assertEqual(1, self.system.closed_devices.count('/dev/MiSTer_cmd'))
        self.assertEqual(1, len(self.system.popen_calls))

    def test_run_detached_chip_id_extraction___when_firmware_restart_is_not_observed___relaunches_with_failure_result_without_reading_memory(self):
        self.system.firmware_restarts = False

        chip_id_linker._run_detached_chip_id_extraction(self.linker, self.rbf_path, self.update_all_dir)

        self.assertEqual([], self.system.memory_maps)
        self.assertEqual([], self.system.isolated_processes)
        self.assertEqual([f'load_core {self.rbf_path}'], self.system.core_commands)
        self.assertEqual(1, self.system.closed_devices.count('/dev/MiSTer_cmd'))
        self.assertEqual('FAILURE_FIRMWARE_CORE_RESTART_TIMEOUT\n',
                         self.system.read_text(chip_id_linker.CHIP_ID_RESULT_HANDOFF_PATH))
        script = self.system.read_text(chip_id_linker.CHIP_ID_RELAUNCH_SCRIPT_PATH)
        self.assertIn('--restore-menu-after-relaunch', script)
        self.assertEqual(1, len(self.system.popen_calls))

    def test_run_detached_chip_id_extraction___when_menu_restore_fails___logs_restore_failure(self):
        self.system.f9_console_after = None
        self.system.failed_core_loads.add('menu.rbf')

        chip_id_linker._run_detached_chip_id_extraction(self.linker, self.rbf_path, self.update_all_dir)

        self.assertEqual([f'load_core {self.rbf_path}', 'load_core menu.rbf'], self.system.core_commands)
        self.assertEqual([], self.system.popen_calls)
        self.assertTrue(any('final result after fallback: FAILURE_RESTORE_MENU_FIFO' in line
                            for line in self.linker.logger.debug_lines))
        self.assertEqual('0123456789abcdef\n', self.system.read_text(chip_id_linker.CHIP_ID_RESULT_HANDOFF_PATH))

    def test_relaunch_update_all_from_scripts_menu___writes_tmp_script_and_starts_agetty(self):
        result = chip_id_linker._relaunch_update_all_from_scripts_menu(
            self.linker, self.update_all_dir, chip_id_result='0123456789abcdef',
        )

        self.assertIsNone(result)
        self.assertEqual('0123456789abcdef\n', self.system.read_text(chip_id_linker.CHIP_ID_RESULT_HANDOFF_PATH))
        self.assertLess(self.system.events.index(('ps',)), self.system.events.index(('reset', '/dev/tty7')))
        self.assertLess(self.system.events.index(('reset', '/dev/tty7')), self.system.events.index(('key', 67, 1)))
        self.assertLess(self.system.events.index(('key', 67, 1)), self.system.events.index(('chvt', '7')))
        self.assertEqual([[
            'setsid', '/sbin/agetty', '-a', 'root', '-l', '/tmp/script', '--nohostname', '-L', 'tty7', 'linux',
        ]], self.system.popen_calls)
        script = self.system.read_text(chip_id_linker.CHIP_ID_RELAUNCH_SCRIPT_PATH)
        for text in (
            'reset_update_all_tty()', 'stty sane', 'trap restore_update_all_display EXIT INT TERM HUP',
            'log_update_all_relaunch "started tty=', 'UPDATE_ALL_DIR=/media/fat/Scripts',
            'UPDATE_ALL_PYZ=/media/fat/Scripts/.config/update_all/update_all.pyz',
            'UPDATE_ALL_RUN_PYZ=/tmp/update_all_chipid.pyz', 'UPDATE_ALL_PYTHON=', 'copy_update_all_pyz()',
            'schedule_chip_id_display_blank()', 'sleep 0.25',
            f'"$UPDATE_ALL_PYTHON" "$UPDATE_ALL_PYZ" --chip-id-linker --blank-display --log {self.linker.log_path}',
            'run_update_all_pyz()', 'cp "$UPDATE_ALL_PYZ" "$UPDATE_ALL_RUN_PYZ"',
            'schedule_chip_id_display_blank\n  "$UPDATE_ALL_PYTHON" "$UPDATE_ALL_RUN_PYZ"',
            'schedule_chip_id_display_blank\n    "$UPDATE_ALL_PYTHON" "$UPDATE_ALL_RUN_PYZ" --continue',
            'log_update_all_relaunch "running pyz $UPDATE_ALL_RUN_PYZ"',
            'log_update_all_relaunch "Update All exited with $EXITSTATUS"', 'restore_update_all_display()',
            f'--restore-after-relaunch --log {self.linker.log_path}', 'cd "$UPDATE_ALL_DIR"',
        ):
            self.assertIn(text, script)
        for text in ('restore_update_all_display_and_exit()', 'run_update_all_launcher()', 'falling back to launcher',
                     'UPDATE_ALL_LAUNCHER', '--restore-menu-after-relaunch', 'COMMAND=',
                     'UPDATE_ALL_CHIP_ID_RESULT', 'Press any key to continue'):
            self.assertNotIn(text, script)
        self.assertEqual(0o750, self.system.path(chip_id_linker.CHIP_ID_RELAUNCH_SCRIPT_PATH).stat().st_mode & 0o777)

    def test_relaunch_update_all_from_scripts_menu___when_start_confirmation_required___writes_marker_and_waits(self):
        marker = chip_id_linker.CHIP_ID_RELAUNCH_SCRIPT_STARTED_PATH
        self.system.path(marker).write_text('stale')

        result = chip_id_linker._relaunch_update_all_from_scripts_menu(
            self.linker, self.update_all_dir, restore_menu_after_relaunch=True,
            require_script_start_confirmation=True, chip_id_result='0123456789abcdef',
        )

        self.assertIsNone(result)
        self.assertIn(('remove', marker), self.system.events)
        self.assertEqual('456', self.system.read_text(marker))
        script = self.system.read_text(chip_id_linker.CHIP_ID_RELAUNCH_SCRIPT_PATH)
        self.assertIn('mark_update_all_relaunch_started()', script)
        self.assertIn(f'> {marker}', script)
        self.assertIn('started marker written', script)
        self.assertTrue(any('marker found at' in line for line in self.linker.logger.debug_lines))

    def test_relaunch_update_all_from_scripts_menu___when_script_does_not_start___terminates_agetty_and_returns_failure(self):
        self.system.relaunch_start_delay = None

        result = chip_id_linker._relaunch_update_all_from_scripts_menu(
            self.linker, self.update_all_dir, require_script_start_confirmation=True, chip_id_result='0123456789abcdef',
        )

        self.assertEqual('FAILURE_RELAUNCH_SCRIPT_START_TIMEOUT', result)
        self.assertTrue(self.system.relaunch_processes[0].terminated)
        self.assertFalse(self.system.relaunch_processes[0].killed)

    def test_wait_for_relaunch_script_start___returns_none_when_marker_appears(self):
        marker = str(self.linker.root / 'new-marker')
        process = ChipIdProcessTester()
        self.system.schedule(0.05, lambda: Path(marker).write_text('started'))

        result = chip_id_linker._wait_for_relaunch_script_start(process, marker, self.linker)

        self.assertIsNone(result)
        self.assertEqual([0.05], self.system.sleeps)

    def test_relaunch_update_all_from_scripts_menu___when_preparation_fails___releases_partial_lease_once(self):
        linker = ChipIdLinkerTester(env={KENV_LAUNCH_ORIGIN_ID: 'zaparoo_frontend'})
        self.addCleanup(linker.close)
        zaparoo = linker.zaparoo
        zaparoo.enable()
        zaparoo.acknowledge_acquire = False

        result = chip_id_linker._relaunch_update_all_from_scripts_menu(linker, self.update_all_dir)

        self.assertEqual('FAILURE_RELAUNCH_TIMEOUTERROR', result)
        self.assertIsNone(zaparoo.lease_nonce)
        self.assertEqual([
            ('/dev/MiSTer_cmd', 'zaparoo_console acquire nonce-1 7\n'),
            ('/dev/MiSTer_cmd', 'zaparoo_console release nonce-1\n'),
        ], linker.console.commands)
        self.assertEqual([], linker.system.popen_calls)

    def test_relaunch_update_all_from_scripts_menu___when_marker_clear_fails___releases_lease_once(self):
        linker = ChipIdLinkerTester(env={KENV_LAUNCH_ORIGIN_ID: 'zaparoo_frontend'})
        self.addCleanup(linker.close)
        zaparoo = linker.zaparoo
        zaparoo.enable()
        linker.system.path(chip_id_linker.CHIP_ID_RELAUNCH_SCRIPT_STARTED_PATH).mkdir()

        result = chip_id_linker._relaunch_update_all_from_scripts_menu(linker, self.update_all_dir)

        self.assertEqual('FAILURE_RELAUNCH_MARKER_CLEAR', result)
        self.assertIsNone(zaparoo.lease_nonce)
        self.assertEqual([
            ('/dev/MiSTer_cmd', 'zaparoo_console acquire nonce-1 7\n'),
            ('/dev/MiSTer_cmd', 'zaparoo_console release nonce-1\n'),
        ], linker.console.commands)
        self.assertEqual([], linker.system.popen_calls)

    def test_relaunch_update_all_from_scripts_menu___after_confirmed_start___leaves_lease_with_script(self):
        linker = ChipIdLinkerTester(env={KENV_LAUNCH_ORIGIN_ID: 'zaparoo_frontend'})
        self.addCleanup(linker.close)
        zaparoo = linker.zaparoo
        zaparoo.enable()

        result = chip_id_linker._relaunch_update_all_from_scripts_menu(linker, self.update_all_dir)

        self.assertIsNone(result)
        self.assertEqual('nonce-1', zaparoo.lease_nonce)
        self.assertEqual([('/dev/MiSTer_cmd', 'zaparoo_console acquire nonce-1 7\n')], linker.console.commands)
        self.assertEqual(1, len(linker.system.popen_calls))
        self.assertTrue(linker.system.exists(chip_id_linker.CHIP_ID_RELAUNCH_SCRIPT_STARTED_PATH))
        self.assertIn('--zaparoo-console-lease 123:1000:nonce-1',
                      linker.system.read_text(chip_id_linker.CHIP_ID_RELAUNCH_SCRIPT_PATH))

    def test_wait_for_relaunch_script_start___returns_failure_when_agetty_exits_before_marker(self):
        process = ChipIdProcessTester(returncode=1)

        result = chip_id_linker._wait_for_relaunch_script_start(process, str(self.linker.root / 'missing'), self.linker)

        self.assertEqual('FAILURE_RELAUNCH_PROCESS_EXIT_1', result)
        self.assertEqual([], self.system.sleeps)

    def test_wait_for_menu_core_after_restore___unrequested_menu_alias___times_out(self):
        self.system.rewrite_core_name('Zaparoo Launcher')

        result = chip_id_linker._wait_for_menu_core_after_restore(self.linker, ('MENU',))

        self.assertEqual('FAILURE_RESTORE_MENU_CORE_TIMEOUT_Zaparoo Launcher', result)
        self.assertGreaterEqual(self.system.monotonic(), chip_id_linker.CHIP_ID_MENU_CORE_READY_TIMEOUT_SECONDS)
        self.assertEqual([], self.linker.console.discovery_calls)

    def test_wait_for_menu_core_after_restore___waits_for_the_caller_selected_name(self):
        self.system.rewrite_core_name('MENU')
        self.system.schedule(0.2, lambda: self.system.rewrite_core_name('Custom Menu'))

        result = chip_id_linker._wait_for_menu_core_after_restore(self.linker, ('Custom Menu',))

        self.assertIsNone(result)
        self.assertEqual(0.2, self.system.monotonic())
        self.assertEqual([], self.linker.console.discovery_calls)

    def test_restore_menu_after_chip_id___accepts_supported_firmware_menu_names(self):
        self.system.menu_restores = False
        for menu_name in ('MENU', 'Zaparoo Launcher'):
            with self.subTest(menu_name=menu_name):
                self.system.rewrite_core_name('LINKER')
                self.system.schedule(0.2, lambda: self.system.rewrite_core_name(menu_name))

                result = chip_id_linker._restore_menu_after_chip_id(self.linker)

                self.assertIsNone(result)
                self.assertEqual('load_core menu.rbf', self.system.core_commands[-1])
                self.assertEqual(menu_name + '\n', self.system.read_text(chip_id_linker.CHIP_ID_MENU_CORE_NAME_PATH))
                self.assertEqual([], self.linker.console.discovery_calls)

    def test_restore_display_after_update_all_relaunch___presses_f12_and_restores_ttys_without_reloading_menu(self):
        result = chip_id_linker._restore_display_after_update_all_relaunch(self.linker)

        self.assertIsNone(result)
        self.assertEqual([
            ('keyboard_created', '/dev/uinput'), ('key', 88, 1), ('key', 88, 0),
            ('keyboard_destroyed', '/dev/uinput'), ('reset', '/dev/tty1'), ('reset', '/dev/tty7'),
        ], self.system.events)
        self.assertEqual('1\n', self.system.read_text(chip_id_linker.CHIP_ID_CURSOR_BLINK_PATH))
        self.assertEqual([], self.system.core_commands)
        self.assertEqual(chip_id_linker.CHIP_ID_RELAUNCH_MENU_SETTLE_SECONDS, self.system.sleeps[-1])

    def test_restore_display_after_update_all_relaunch___when_requested___closes_console_then_reloads_menu(self):
        result = chip_id_linker._restore_display_after_update_all_relaunch(self.linker, restore_menu_after_relaunch=True)

        self.assertIsNone(result)
        self.assertEqual(['load_core menu.rbf'], self.system.core_commands)
        self.assertLess(self.system.events.index(('key', 88, 1)), self.system.events.index(('core_command', 'load_core menu.rbf')))

    def test_restore_display_after_update_all_relaunch___when_menu_restore_fails___still_closes_console(self):
        self.system.rewrite_core_name('LINKER')
        self.system.menu_restores = False

        result = chip_id_linker._restore_display_after_update_all_relaunch(self.linker, restore_menu_after_relaunch=True)

        self.assertEqual('FAILURE_RESTORE_MENU_CORE_TIMEOUT_LINKER', result)
        self.assertIn(('key', 88, 1), self.system.events)
        self.assertIn(('reset', '/dev/tty1'), self.system.events)
        self.assertIn(('reset', '/dev/tty7'), self.system.events)
        self.assertEqual(chip_id_linker.CHIP_ID_MENU_CORE_READY_POLL_INTERVAL_SECONDS, self.system.sleeps[-1])

    def test_restore_display_after_update_all_relaunch___with_lease___resets_terminal_before_release(self):
        for restore_menu in (False, True):
            with self.subTest(restore_menu=restore_menu):
                linker = ChipIdLinkerTester()
                self.addCleanup(linker.close)
                linker.zaparoo.enable()
                lease = linker.zaparoo.detect()
                lease.acquire('7')
                linker.system.path(chip_id_linker.CHIP_ID_CURSOR_BLINK_PATH).write_text('0\n')

                result = chip_id_linker._restore_display_after_update_all_relaunch(
                    linker, restore_menu_after_relaunch=restore_menu, zaparoo_console_lease=lease.restore_token(),
                )

                self.assertIsNone(result)
                self.assertIsNone(linker.zaparoo.lease_nonce)
                self.assertEqual([
                    ('/dev/MiSTer_cmd', 'zaparoo_console acquire nonce-1 7\n'),
                    ('/dev/MiSTer_cmd', 'zaparoo_console release nonce-1\n'),
                ], linker.console.commands)
                expected_events = [('reset', '/dev/tty7')]
                if restore_menu:
                    expected_events.append(('core_command', 'load_core menu.rbf'))
                self.assertEqual(expected_events, linker.system.events)
                self.assertEqual('1\n', linker.system.read_text(chip_id_linker.CHIP_ID_CURSOR_BLINK_PATH))
                logs = linker.logger.debug_lines
                release_index = logs.index('Zaparoo console request: release nonce-1')
                self.assertLess(logs.index('_reset_script_tty: terminal reset sequence written to /dev/tty7'), release_index)
                self.assertLess(logs.index(f'_restore_cursor_blink: wrote {chip_id_linker.CHIP_ID_CURSOR_BLINK_PATH}'), release_index)
                if restore_menu:
                    self.assertLess(release_index, logs.index('_load_core: writing command: load_core menu.rbf'))
                self.assertEqual(chip_id_linker.CHIP_ID_RELAUNCH_MENU_SETTLE_SECONDS, linker.system.sleeps[-1])

    def test_restore_display_after_update_all_relaunch___with_lease___preserves_failure_precedence(self):
        for release_acknowledged, restore_menu, menu_restores, expected in (
            (False, False, True, 'FAILURE_RESTORE_ZAPAROO_CONSOLE'),
            (False, True, True, 'FAILURE_RESTORE_ZAPAROO_CONSOLE'),
            (False, True, False, 'FAILURE_RESTORE_MENU_CORE_TIMEOUT_LINKER'),
            (True, True, False, 'FAILURE_RESTORE_MENU_CORE_TIMEOUT_LINKER'),
        ):
            with self.subTest(release_acknowledged=release_acknowledged, restore_menu=restore_menu, menu_restores=menu_restores):
                linker = ChipIdLinkerTester()
                self.addCleanup(linker.close)
                linker.zaparoo.enable()
                lease = linker.zaparoo.detect()
                lease.acquire('7')
                linker.zaparoo.acknowledge_release = release_acknowledged
                linker.system.rewrite_core_name('LINKER')
                linker.system.menu_restores = menu_restores

                result = chip_id_linker._restore_display_after_update_all_relaunch(
                    linker, restore_menu_after_relaunch=restore_menu, zaparoo_console_lease=lease.restore_token(),
                )

                self.assertEqual(expected, result)
                self.assertIsNone(linker.zaparoo.lease_nonce)
                self.assertEqual(['load_core menu.rbf'] if restore_menu else [], linker.system.core_commands)
                if not release_acknowledged:
                    self.assertIn('Could not restore Zaparoo console after Update All', linker.logger.debug_lines)

    def test_write_update_all_relaunch_script___when_direct_chipid_relaunch___restores_menu_after_exit(self):
        self.linker.write_relaunch_script('', restore_menu=True)

        script = self.linker.script_path.read_text()

        self.assertIn(f'--restore-after-relaunch --restore-menu-after-relaunch --log {self.linker.log_path}', script)

    def test_write_update_all_relaunch_script___uses_current_update_all_archive_when_available(self):
        self.system.archive_path = '/tmp/running_update_all.pyz'

        self.linker.write_relaunch_script('')

        self.assertIn('UPDATE_ALL_PYZ=/tmp/running_update_all.pyz', self.linker.script_path.read_text())
        self.assertNotIn('UPDATE_ALL_PYZ=/media/fat/Scripts/.config/update_all/update_all.pyz', self.linker.script_path.read_text())

    def test_write_update_all_relaunch_script___forwards_inherited_environment_without_command_or_stale_result(self):
        self.system.environment = {
            'LOCATION_STR': '/media/fat', 'CURL_SSL': '--insecure',
            'SSL_CERT_FILE': '/media/fat/Scripts/.config/downloader/cacert.pem', 'MIRROR_ID': 'example',
            'HTTP_PROXY': 'http://proxy.example:8080', 'VALUE_WITH_SPACE': 'hello world',
            'COMMAND': 'STANDARD', 'UPDATE_ALL_CHIP_ID_RESULT': 'stale', 'PWD': '/tmp',
            'BAD-NAME': 'bad', 'BASH_FUNC_bad%%': '() { bad; }',
        }

        self.linker.write_relaunch_script('')

        script = self.linker.script_path.read_text()
        for text in ('export LOCATION_STR=/media/fat', 'export CURL_SSL=--insecure',
                     'export SSL_CERT_FILE=/media/fat/Scripts/.config/downloader/cacert.pem', 'export MIRROR_ID=example',
                     'export HTTP_PROXY=http://proxy.example:8080', "export VALUE_WITH_SPACE='hello world'"):
            self.assertIn(text, script)
        for text in ('COMMAND=', 'UPDATE_ALL_CHIP_ID_RESULT', 'export PWD=', 'BAD-NAME', 'BASH_FUNC_bad'):
            self.assertNotIn(text, script)

    def test_clear_visible_script_processes___terminates_stale_script_process_before_relaunch(self):
        self.system.visible_processes[123] = '123 root S /bin/bash /tmp/script'

        result = chip_id_linker._clear_visible_script_processes(self.linker)

        self.assertIsNone(result)
        self.assertEqual([(123, signal.SIGTERM)], self.system.signals)
        self.assertEqual({}, self.system.visible_processes)

    def test_open_script_console___from_menu_core___uses_zaparoo_f9_handoff_before_target_tty(self):
        chip_id_linker._open_script_console(self.linker)

        self.assertEqual([
            ('keyboard_created', '/dev/uinput'), ('chvt', '3'), ('key', 67, 1), ('key', 67, 0),
            ('chvt', '3'), ('keyboard_destroyed', '/dev/uinput'),
        ], self.system.events)
        self.assertEqual('tty3\n', self.system.read_text('/sys/devices/virtual/tty/tty0/active'))
        self.assertEqual(1, self.system.closed_devices.count('/dev/uinput'))

    def test_open_script_console___presses_f9_until_console_is_ready(self):
        self.system.f9_console_after = 2

        chip_id_linker._open_script_console(self.linker)

        self.assertEqual(2, self.system.f9_count)
        self.assertEqual(2, self.system.events.count(('key', 67, 1)))
        self.assertEqual(2, self.system.events.count(('key', 67, 0)))
        self.assertEqual('tty3\n', self.system.read_text('/sys/devices/virtual/tty/tty0/active'))

    def test_relaunch_update_all_from_scripts_menu___hands_off_the_result_before_opening_the_console(self):
        self.system.f9_console_after = None

        result = chip_id_linker._relaunch_update_all_from_scripts_menu(
            self.linker, self.update_all_dir, restore_menu_after_relaunch=True,
            require_script_start_confirmation=True, chip_id_result='FAILURE_MEM_SIGBUS',
        )

        self.assertEqual('FAILURE_RELAUNCH_TIMEOUTERROR', result)
        self.assertEqual(['FAILURE_MEM_SIGBUS\n'], self.system.handoffs_at_keyboard_open)
        self.assertEqual([], self.system.popen_calls)
        self.assertEqual('FAILURE_MEM_SIGBUS\n', self.system.read_text(chip_id_linker.CHIP_ID_RESULT_HANDOFF_PATH))

    def test_relaunch_update_all_from_scripts_menu___when_the_handoff_cannot_be_written___fails_before_touching_the_console(self):
        self.system.open_errors[chip_id_linker.CHIP_ID_RESULT_HANDOFF_PATH] = OSError('unusable directory')

        result = chip_id_linker._relaunch_update_all_from_scripts_menu(
            self.linker, self.update_all_dir, chip_id_result='0123456789abcdef',
        )

        self.assertEqual('FAILURE_RELAUNCH_HANDOFF_WRITE', result)
        self.assertEqual([], self.system.events)
        self.assertEqual([], self.system.opened_devices)
        self.assertEqual([], self.system.popen_calls)

    def test_write_chip_id_result_handoff___replaces_a_previous_result(self):
        handoff = str(self.linker.root / 'result')

        first = chip_id_linker._write_chip_id_result_handoff(handoff, 'FAILURE_MEM_SIGBUS', self.linker)
        second = chip_id_linker._write_chip_id_result_handoff(handoff, '0123456789abcdef', self.linker)

        self.assertIsNone(first)
        self.assertIsNone(second)
        self.assertEqual('0123456789abcdef\n', Path(handoff).read_text())
        self.assertEqual([Path(handoff)], list(self.linker.root.glob('result*')))

    def test_write_chip_id_result_handoff___without_a_result___writes_nothing(self):
        handoff = str(self.linker.root / 'result')

        result = chip_id_linker._write_chip_id_result_handoff(handoff, '', self.linker)

        self.assertIsNone(result)
        self.assertFalse(Path(handoff).exists())
        self.assertEqual([], list(self.linker.root.glob('result*')))

    def test_write_chip_id_result_handoff___when_the_directory_is_unusable___returns_a_failure_code(self):
        handoff = str(self.linker.root / 'missing-directory' / 'result')

        result = chip_id_linker._write_chip_id_result_handoff(handoff, '0123456789abcdef', self.linker)

        self.assertEqual('FAILURE_RELAUNCH_HANDOFF_WRITE', result)
        self.assertTrue(any('_write_chip_id_result_handoff: failed:' in line for line in self.linker.logger.debug_lines))

    def test_read_chip_id_from_memory_after_core_load___retries_transient_sigbus_until_chip_id_is_ready(self):
        self.system.process_exitcodes.append(-signal.SIGBUS)

        result = chip_id_linker._read_chip_id_from_memory_after_core_load(self.linker)

        self.assertEqual('0123456789abcdef', result)
        self.assertEqual(2, len(self.system.isolated_processes))
        self.assertIn(chip_id_linker.CHIP_ID_HPS_FPGAMGR_BASE, self.system.memory_maps)
        self.assertIn(('/dev/MiSTer_cmd', os.O_WRONLY | os.O_NONBLOCK), self.system.opened_devices)
        self.assertIn(0.1, self.system.sleeps)

    def test_read_chip_id_from_memory_after_core_load___does_not_retry_bad_magic_after_bridge_safe_gate(self):
        self.system.set_chip_id_memory(magic=0)

        result = chip_id_linker._read_chip_id_from_memory_after_core_load(self.linker)

        self.assertEqual('FAILURE_BAD_MAGIC_00000000', result)
        self.assertEqual(1, len(self.system.isolated_processes))
        self.assertNotIn(chip_id_linker.CHIP_ID_HPS_FPGAMGR_BASE, self.system.memory_maps)

    def test_wait_for_firmware_core_restart_after_load___returns_none_when_core_name_marker_is_rewritten(self):
        previous = self.system.stat(chip_id_linker.CHIP_ID_MENU_CORE_NAME_PATH).st_mtime_ns
        self.system.schedule(0.05, lambda: self.system.rewrite_core_name('LINKER'))

        result = chip_id_linker._wait_for_firmware_core_restart_after_load(previous, self.linker)

        self.assertIsNone(result)
        self.assertEqual([0.05], self.system.sleeps)

    def test_wait_for_firmware_core_restart_after_load___returns_failure_when_marker_does_not_change(self):
        previous = self.system.stat(chip_id_linker.CHIP_ID_MENU_CORE_NAME_PATH).st_mtime_ns

        result = chip_id_linker._wait_for_firmware_core_restart_after_load(previous, self.linker)

        self.assertEqual('FAILURE_FIRMWARE_CORE_RESTART_TIMEOUT', result)
        self.assertEqual(chip_id_linker.CHIP_ID_FIRMWARE_CORE_RESTART_TIMEOUT_SECONDS, self.system.monotonic())
        self.assertEqual(previous, self.system.stat(chip_id_linker.CHIP_ID_MENU_CORE_NAME_PATH).st_mtime_ns)

    def test_wait_for_hps_fpga_lw_bridge_ready_after_core_load___waits_for_stable_safe_status(self):
        result = chip_id_linker._wait_for_hps_fpga_lw_bridge_ready_after_core_load(self.linker)

        self.assertIsNone(result)
        self.assertGreaterEqual(self.system.monotonic(), chip_id_linker.CHIP_ID_HPS_FPGA_READY_STABLE_SECONDS)
        self.assertGreaterEqual(self.system.memory_maps.count(chip_id_linker.CHIP_ID_HPS_FPGAMGR_BASE), 2)
        self.assertNotIn(chip_id_linker.CHIP_ID_BASE, self.system.memory_maps)

    def test_wait_for_hps_fpga_lw_bridge_ready_after_core_load___returns_failure_without_touching_lw_bridge_when_status_read_fails(self):
        self.system.map_errors[chip_id_linker.CHIP_ID_HPS_FPGAMGR_BASE] = OSError('unreadable FPGA status')

        result = chip_id_linker._wait_for_hps_fpga_lw_bridge_ready_after_core_load(self.linker)

        self.assertEqual('FAILURE_HPS_FPGA_STATUS_READ', result)
        self.assertNotIn(chip_id_linker.CHIP_ID_BASE, self.system.memory_maps)
        self.assertEqual(['/dev/mem'], self.system.closed_devices)

    def test_read_chip_id_from_registers___with_valid_registers___returns_chip_id(self):
        memory = self.system.set_chip_id_memory(id_hi=0x01234567, id_lo=0x89abcdef)

        result = chip_id_linker._read_chip_id_from_registers(memory, 0, self.linker)

        self.assertEqual('0123456789abcdef', result)

    def test_read_chip_id_from_registers___with_unsupported_version___returns_error_code(self):
        memory = self.system.set_chip_id_memory(version=0x00020000)

        result = chip_id_linker._read_chip_id_from_registers(memory, 0, self.linker)

        self.assertEqual('FAILURE_UNSUPPORTED_VERSION_00020000', result)

    def test_read_chip_id_from_registers___with_xor_mismatch___returns_error_code(self):
        memory = self.system.set_chip_id_memory(id_xor=0)

        result = chip_id_linker._read_chip_id_from_registers(memory, 0, self.linker)

        self.assertEqual('FAILURE_ID_XOR_MISMATCH_00000000_cbc0c1cc', result)

    def test_write_chip_id_display_control_to_registers___writes_blank_control(self):
        memory = self.system.set_chip_id_memory()

        result = chip_id_linker._write_chip_id_display_control_to_registers(
            memory, 0, chip_id_linker.CHIP_ID_DISPLAY_CONTROL_BLANK, self.linker,
        )

        self.assertIsNone(result)
        self.assertEqual(1, struct.unpack_from('<I', memory, chip_id_linker.CHIP_ID_REG_DISPLAY_CONTROL)[0])

    def test_write_chip_id_display_control_to_registers___rejects_bad_magic(self):
        memory = self.system.set_chip_id_memory(magic=0)

        result = chip_id_linker._write_chip_id_display_control_to_registers(
            memory, 0, chip_id_linker.CHIP_ID_DISPLAY_CONTROL_BLANK, self.linker,
        )

        self.assertEqual('FAILURE_DISPLAY_CONTROL_BAD_MAGIC_00000000', result)
        self.assertEqual(0, struct.unpack_from('<I', memory, chip_id_linker.CHIP_ID_REG_DISPLAY_CONTROL)[0])
