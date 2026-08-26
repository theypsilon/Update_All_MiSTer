import os
import signal
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import ANY, call, patch

from update_all import chip_id_linker
from test.logger_tester import LoggerSpy, NoLogger
from update_all.logger import FileLoggerDecorator


class TestChipIdLinker(unittest.TestCase):
    def test_main___blank_display_command___does_not_require_rbf_or_update_all_launcher(self):
        log_path = _temp_file(b'stale\n')

        with patch('update_all.chip_id_linker._blank_chip_id_core_display') as blank_display:
            result = chip_id_linker.run_chip_id_linker_command(_logger(), ['--blank-display', '--log', log_path])

        self.assertEqual(0, result)
        blank_display.assert_called_once()
        self.assertEqual(log_path, blank_display.call_args.args[0].log_path)
        with open(log_path, 'rb') as log_file:
            self.assertEqual(b'stale\n', log_file.read())
        _remove(log_path)

    def test_main___restore_after_relaunch_command___does_not_clear_existing_log(self):
        log_path = _temp_file(b'stale\n')

        with patch('update_all.chip_id_linker._restore_display_after_update_all_relaunch') as restore_display:
            result = chip_id_linker.run_chip_id_linker_command(_logger(), ['--restore-after-relaunch', '--log', log_path])

        self.assertEqual(0, result)
        restore_display.assert_called_once()
        self.assertEqual(log_path, restore_display.call_args.args[0].log_path)
        self.assertEqual(False, restore_display.call_args.args[1])
        with open(log_path, 'rb') as log_file:
            self.assertEqual(b'stale\n', log_file.read())
        _remove(log_path)

    def test_main___extract_only_command___does_not_require_update_all_launcher_and_prints_result(self):
        log_path = _temp_file(b'stale\n')

        with patch('update_all.chip_id_linker._extract_chip_id_without_relaunch', return_value='0123456789abcdef') as extract, \
                patch('builtins.print') as print_result:
            result = chip_id_linker.run_chip_id_linker_command(_logger(), [
                '--extract-only',
                '--rbf',
                '/media/fat/Scripts/.config/update_all/Linker.rbf',
                '--log',
                log_path,
            ])

        self.assertEqual(0, result)
        extract.assert_called_once()
        self.assertEqual('/media/fat/Scripts/.config/update_all/Linker.rbf', extract.call_args.args[0])
        self.assertEqual(log_path, extract.call_args.args[1].log_path)
        print_result.assert_called_once_with('0123456789abcdef')
        self.assertFalse(os.path.exists(log_path))
        _remove(log_path)

    def test_main___detached_extraction_command___starts_with_clean_log(self):
        log_path = _temp_file(b'stale\n')

        with patch('update_all.chip_id_linker._run_detached_chip_id_extraction') as run_extraction:
            result = chip_id_linker.run_chip_id_linker_command(_logger(), [
                '--rbf',
                '/media/fat/Scripts/.config/update_all/Linker.rbf',
                '--update-all-dir',
                '/media/fat/Scripts',
                '--log',
                log_path,
            ])

        self.assertEqual(0, result)
        run_extraction.assert_called_once()
        self.assertEqual(log_path, run_extraction.call_args.args[0].log_path)
        self.assertEqual('/media/fat/Scripts/.config/update_all/Linker.rbf', run_extraction.call_args.args[1])
        self.assertEqual('/media/fat/Scripts', run_extraction.call_args.args[2])
        self.assertFalse(os.path.exists(log_path))
        _remove(log_path)

    def test_main___detached_extraction_command___publishes_marker_and_log_before_extraction(self):
        with tempfile.TemporaryDirectory() as base_path:
            log_path = os.path.join(base_path, 'chip-id-linker.log')
            marker_path = os.path.join(base_path, 'worker.started')
            logger = FileLoggerDecorator(NoLogger(), log_path)

            def run_extraction(linker, _rbf_path, _update_all_dir):
                self.assertTrue(os.path.isfile(marker_path))
                with open(log_path) as log_file:
                    self.assertIn('_write_worker_startup_marker: wrote', log_file.read())
                linker.debug('worker extraction entered')
                with open(log_path) as log_file:
                    self.assertIn('worker extraction entered', log_file.read())

            with patch('update_all.chip_id_linker._run_detached_chip_id_extraction', side_effect=run_extraction):
                result = chip_id_linker.run_chip_id_linker_command(logger, [
                    '--rbf',
                    '/media/fat/Scripts/.config/update_all/Linker.rbf',
                    '--update-all-dir',
                    '/media/fat/Scripts',
                    '--startup-marker',
                    marker_path,
                    '--log',
                    log_path,
                ])
            logger.finalize()

            self.assertEqual(0, result)
            with open(marker_path) as marker_file:
                self.assertTrue(marker_file.read().strip().isdigit())
            with open(log_path) as log_file:
                self.assertEqual(1, log_file.read().count('worker extraction entered'))

    def test_main___detached_extraction_command___preserves_eager_log_after_hard_exit(self):
        worker_code = (
            'import os\n'
            'import sys\n'
            'import tempfile\n'
            'from update_all import chip_id_linker\n'
            'from update_all.logger import FileLoggerDecorator, PrintLogger\n'
            'tempfile.tempdir = sys.argv[3]\n'
            'def crash_after_log(linker, _rbf_path, _update_all_dir):\n'
            '    linker.debug("worker log before hard exit")\n'
            '    os._exit(23)\n'
            'chip_id_linker._run_detached_chip_id_extraction = crash_after_log\n'
            'logger = FileLoggerDecorator(PrintLogger(), sys.argv[1])\n'
            'chip_id_linker.run_chip_id_linker_command(logger, [\n'
            '    "--rbf", "/tmp/Linker.rbf",\n'
            '    "--update-all-dir", "/tmp",\n'
            '    "--startup-marker", sys.argv[2],\n'
            '    "--log", sys.argv[1],\n'
            '])\n'
        )
        with tempfile.TemporaryDirectory() as base_path:
            log_path = os.path.join(base_path, 'chip-id-linker.log')
            marker_path = os.path.join(base_path, 'worker.started')

            process = subprocess.run(
                [sys.executable, '-c', worker_code, log_path, marker_path, base_path],
                cwd=os.path.dirname(os.path.dirname(chip_id_linker.__file__)),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            self.assertEqual(23, process.returncode, process.stderr)
            self.assertTrue(os.path.isfile(marker_path))
            with open(log_path) as log_file:
                log = log_file.read()
            self.assertIn('_write_worker_startup_marker: wrote', log)
            self.assertIn('worker log before hard exit', log)

    def test_main___blank_display_command___appends_log_when_finalized(self):
        log_path = _temp_file(b'primary\n')
        logger = FileLoggerDecorator(NoLogger(), log_path)

        with patch('update_all.chip_id_linker._blank_chip_id_core_display', side_effect=lambda linker: linker.debug('blank display')):
            result = chip_id_linker.run_chip_id_linker_command(logger, ['--blank-display', '--log', log_path])
        logger.finalize()

        self.assertEqual(0, result)
        with open(log_path, 'rb') as log_file:
            self.assertEqual(b'primary\nblank display\n', log_file.read())
        _remove(log_path)

    def test_main___detached_extraction_command___preserves_direct_relaunch_script_log_when_finalized(self):
        log_path = _temp_file(b'stale\n')
        logger = FileLoggerDecorator(NoLogger(), log_path)

        def run_extraction(linker, _rbf_path, _update_all_dir):
            linker.debug('primary helper')
            with open(log_path, 'a') as log_file:
                log_file.write('relaunch_script: started\n')

        with patch('update_all.chip_id_linker._run_detached_chip_id_extraction', side_effect=run_extraction):
            result = chip_id_linker.run_chip_id_linker_command(logger, [
                '--rbf',
                '/media/fat/Scripts/.config/update_all/Linker.rbf',
                '--update-all-dir',
                '/media/fat/Scripts',
                '--log',
                log_path,
            ])
        logger.finalize()

        self.assertEqual(0, result)
        with open(log_path) as log_file:
            log = log_file.read()
        self.assertNotIn('stale', log)
        self.assertIn('relaunch_script: started\n', log)
        self.assertIn('primary helper\n', log)
        _remove(log_path)

    def test_extract_chip_id_without_relaunch___loads_core_reads_id_and_restores_menu(self):
        rbf_path = _temp_file(b'rbf')
        log_path = '/tmp/update_all_test_chipid.log'

        with patch('update_all.chip_id_linker._read_chip_id_from_memory', return_value='0123456789abcdef'), \
                patch('update_all.chip_id_linker._prepare_display_before_chip_id_core_load'), \
                patch('update_all.chip_id_linker._wait_for_firmware_core_restart_after_load', return_value=None), \
                patch('update_all.chip_id_linker._wait_for_hps_fpga_lw_bridge_ready_after_core_load', return_value=None), \
                patch('update_all.chip_id_linker._restore_menu_after_chip_id', return_value=None) as restore_menu, \
                patch('update_all.chip_id_linker.os.open', return_value=123) as os_open, \
                patch('update_all.chip_id_linker.os.write') as os_write, \
                patch('update_all.chip_id_linker.os.close') as os_close:
            result = chip_id_linker._extract_chip_id_without_relaunch(rbf_path, _linker(log_path))

        self.assertEqual('0123456789abcdef', result)
        os_open.assert_called_once_with('/dev/MiSTer_cmd', os.O_WRONLY | os.O_NONBLOCK)
        os_write.assert_called_once_with(123, f'load_core {rbf_path}'.encode())
        os_close.assert_called_once_with(123)
        restore_menu.assert_called_once_with(ANY)
        _remove(rbf_path, log_path)

    def test_run_detached_chip_id_extraction___writes_load_core_to_fifo_and_relaunches_with_chip_id_result(self):
        rbf_path = _temp_file(b'rbf')
        log_path = '/tmp/update_all_test_chipid.log'

        with patch('update_all.chip_id_linker._read_chip_id_from_memory', return_value='0123456789abcdef'), \
                patch('update_all.chip_id_linker._relaunch_update_all_from_scripts_menu', return_value=None) as relaunch, \
                patch('update_all.chip_id_linker._prepare_display_before_chip_id_core_load'), \
                patch('update_all.chip_id_linker._wait_for_firmware_core_restart_after_load', return_value=None), \
                patch('update_all.chip_id_linker._wait_for_hps_fpga_lw_bridge_ready_after_core_load', return_value=None), \
                patch('update_all.chip_id_linker._restore_menu_after_chip_id') as restore_menu, \
                patch('update_all.chip_id_linker.os.open', return_value=123) as os_open, \
                patch('update_all.chip_id_linker.os.write') as os_write, \
                patch('update_all.chip_id_linker.os.close') as os_close:
            chip_id_linker._run_detached_chip_id_extraction(_linker(log_path), rbf_path, '/media/fat/Scripts')

        os_open.assert_has_calls([
            call('/dev/MiSTer_cmd', os.O_WRONLY | os.O_NONBLOCK),
        ])
        os_write.assert_has_calls([
            call(123, f'load_core {rbf_path}'.encode()),
        ])
        self.assertEqual(1, os_close.call_count)
        restore_menu.assert_not_called()
        relaunch.assert_called_once_with(
            ANY,
            '/media/fat/Scripts',
            restore_menu_after_relaunch=True,
            require_script_start_confirmation=True,
            chip_id_result='0123456789abcdef',
        )
        _remove(rbf_path, log_path)

    def test_run_detached_chip_id_extraction___when_fifo_write_fails___relaunches_with_failure_result(self):
        rbf_path = _temp_file(b'rbf')
        log_path = '/tmp/update_all_test_chipid.log'

        with patch('update_all.chip_id_linker._read_chip_id_from_memory', return_value='0123456789abcdef') as read_mem, \
                patch('update_all.chip_id_linker._relaunch_update_all_from_scripts_menu') as relaunch, \
                patch('update_all.chip_id_linker._prepare_display_before_chip_id_core_load'), \
                patch('update_all.chip_id_linker.os.open', return_value=123), \
                patch('update_all.chip_id_linker.os.write', side_effect=OSError('boom')), \
                patch('update_all.chip_id_linker.os.close'):
            chip_id_linker._run_detached_chip_id_extraction(_linker(log_path), rbf_path, '/media/fat/Scripts')

        read_mem.assert_not_called()
        relaunch.assert_called_once_with(
            ANY,
            '/media/fat/Scripts',
            require_script_start_confirmation=True,
            chip_id_result='FAILURE_LOAD_CORE_FIFO',
        )
        _remove(rbf_path, log_path)

    def test_run_detached_chip_id_extraction___when_firmware_restart_is_not_observed___relaunches_with_failure_result_without_reading_memory(self):
        rbf_path = _temp_file(b'rbf')
        log_path = '/tmp/update_all_test_chipid.log'

        with patch('update_all.chip_id_linker._read_chip_id_from_memory', return_value='0123456789abcdef') as read_mem, \
                patch('update_all.chip_id_linker._relaunch_update_all_from_scripts_menu', return_value=None) as relaunch, \
                patch('update_all.chip_id_linker._prepare_display_before_chip_id_core_load'), \
                patch('update_all.chip_id_linker._wait_for_firmware_core_restart_after_load', return_value='FAILURE_FIRMWARE_CORE_RESTART_TIMEOUT'), \
                patch('update_all.chip_id_linker._wait_for_hps_fpga_lw_bridge_ready_after_core_load') as wait_bridge_ready, \
                patch('update_all.chip_id_linker._restore_menu_after_chip_id') as restore_menu, \
                patch('update_all.chip_id_linker.os.open', return_value=123), \
                patch('update_all.chip_id_linker.os.write') as os_write, \
                patch('update_all.chip_id_linker.os.close') as os_close:
            chip_id_linker._run_detached_chip_id_extraction(_linker(log_path), rbf_path, '/media/fat/Scripts')

        read_mem.assert_not_called()
        wait_bridge_ready.assert_not_called()
        os_write.assert_has_calls([
            call(123, f'load_core {rbf_path}'.encode()),
        ])
        self.assertEqual(1, os_close.call_count)
        restore_menu.assert_not_called()
        relaunch.assert_called_once_with(
            ANY,
            '/media/fat/Scripts',
            restore_menu_after_relaunch=True,
            require_script_start_confirmation=True,
            chip_id_result='FAILURE_FIRMWARE_CORE_RESTART_TIMEOUT',
        )
        _remove(rbf_path, log_path)

    def test_run_detached_chip_id_extraction___when_menu_restore_fails___logs_restore_failure(self):
        rbf_path = _temp_file(b'rbf')
        log_path = '/tmp/update_all_test_chipid.log'

        with patch('update_all.chip_id_linker._read_chip_id_from_memory', return_value='0123456789abcdef'), \
                patch('update_all.chip_id_linker._relaunch_update_all_from_scripts_menu', return_value='FAILURE_RELAUNCH_TIMEOUT') as relaunch, \
                patch('update_all.chip_id_linker._prepare_display_before_chip_id_core_load'), \
                patch('update_all.chip_id_linker._wait_for_firmware_core_restart_after_load', return_value=None), \
                patch('update_all.chip_id_linker._wait_for_hps_fpga_lw_bridge_ready_after_core_load', return_value=None), \
                patch('update_all.chip_id_linker.os.open', return_value=123), \
                patch('update_all.chip_id_linker.os.write', side_effect=[None, OSError('boom')]), \
                patch('update_all.chip_id_linker.os.close'):
            chip_id_linker._run_detached_chip_id_extraction(_linker(log_path), rbf_path, '/media/fat/Scripts')

        relaunch.assert_called_once_with(
            ANY,
            '/media/fat/Scripts',
            restore_menu_after_relaunch=True,
            require_script_start_confirmation=True,
            chip_id_result='0123456789abcdef',
        )
        _remove(rbf_path, log_path)

    def test_relaunch_update_all_from_scripts_menu___writes_tmp_script_and_starts_agetty(self):
        process = _ProcessTester(pid=456)
        script_path = '/tmp/update_all_test_relaunch_script'
        handoff_path = '/tmp/update_all_test_chip_id_result'
        log_path = '/tmp/update_all_test_chipid.log'

        with patch('update_all.chip_id_linker.CHIP_ID_RELAUNCH_SCRIPT_PATH', script_path), \
                patch('update_all.chip_id_linker.CHIP_ID_RESULT_HANDOFF_PATH', handoff_path), \
                patch('update_all.chip_id_linker._clear_visible_script_processes', return_value=None) as clear_scripts, \
                patch('update_all.chip_id_linker.CHIP_ID_RELAUNCH_AFTER_SCRIPT_CLEAR_SETTLE_SECONDS', 0), \
                patch('update_all.chip_id_linker._reset_script_tty') as reset_tty, \
                patch('update_all.chip_id_linker._open_script_console') as open_script_console, \
                patch('update_all.chip_id_linker._switch_to_relaunch_tty') as switch_to_relaunch_tty, \
                patch('update_all.chip_id_linker.subprocess.Popen', return_value=process) as popen:
            result = chip_id_linker._relaunch_update_all_from_scripts_menu(
                _linker(log_path),
                '/media/fat/Scripts',
                chip_id_result='0123456789abcdef',
            )

        self.assertIsNone(result)
        clear_scripts.assert_called_once_with(ANY)
        reset_tty.assert_called_once_with(ANY)
        open_script_console.assert_called_once_with(ANY)
        switch_to_relaunch_tty.assert_called_once_with(ANY)
        with open(handoff_path) as handoff_file:
            self.assertEqual('0123456789abcdef\n', handoff_file.read())
        popen.assert_called_once_with([
            'setsid',
            '/sbin/agetty',
            '-a',
            'root',
            '-l',
            script_path,
            '--nohostname',
            '-L',
            'tty7',
            'linux',
        ])
        with open(script_path) as result_file:
            script = result_file.read()
        self.assertIn('reset_update_all_tty()', script)
        self.assertIn('stty sane', script)
        self.assertNotIn('restore_update_all_display_and_exit()', script)
        self.assertIn('trap restore_update_all_display EXIT INT TERM HUP', script)
        self.assertIn('log_update_all_relaunch "started tty=', script)
        self.assertIn('UPDATE_ALL_DIR=/media/fat/Scripts', script)
        self.assertIn('UPDATE_ALL_PYZ=/media/fat/Scripts/.config/update_all/update_all.pyz', script)
        self.assertIn('UPDATE_ALL_RUN_PYZ=/tmp/update_all_chipid.pyz', script)
        self.assertIn('UPDATE_ALL_PYTHON=', script)
        self.assertIn('copy_update_all_pyz()', script)
        self.assertIn('schedule_chip_id_display_blank()', script)
        self.assertIn('sleep 0.25', script)
        self.assertIn('"$UPDATE_ALL_PYTHON" "$UPDATE_ALL_PYZ" --chip-id-linker --blank-display --log /tmp/update_all_test_chipid.log', script)
        self.assertIn('run_update_all_pyz()', script)
        self.assertIn('cp "$UPDATE_ALL_PYZ" "$UPDATE_ALL_RUN_PYZ"', script)
        self.assertIn('schedule_chip_id_display_blank\n  "$UPDATE_ALL_PYTHON" "$UPDATE_ALL_RUN_PYZ"', script)
        self.assertIn('"$UPDATE_ALL_PYTHON" "$UPDATE_ALL_RUN_PYZ"', script)
        self.assertIn('schedule_chip_id_display_blank\n    "$UPDATE_ALL_PYTHON" "$UPDATE_ALL_RUN_PYZ" --continue', script)
        self.assertIn('"$UPDATE_ALL_PYTHON" "$UPDATE_ALL_RUN_PYZ" --continue', script)
        self.assertIn('log_update_all_relaunch "running pyz $UPDATE_ALL_RUN_PYZ"', script)
        self.assertNotIn('run_update_all_launcher()', script)
        self.assertNotIn('falling back to launcher', script)
        self.assertNotIn('UPDATE_ALL_LAUNCHER', script)
        self.assertIn('log_update_all_relaunch "Update All exited with $EXITSTATUS"', script)
        self.assertIn('restore_update_all_display()', script)
        self.assertIn('--restore-after-relaunch --log /tmp/update_all_test_chipid.log', script)
        self.assertNotIn('--restore-menu-after-relaunch', script)
        self.assertNotIn('COMMAND=', script)
        self.assertNotIn('UPDATE_ALL_CHIP_ID_RESULT', script)
        self.assertIn('cd "$UPDATE_ALL_DIR"', script)
        self.assertNotIn('Press any key to continue', script)
        _remove(script_path, handoff_path, log_path)

    def test_relaunch_update_all_from_scripts_menu___when_start_confirmation_required___writes_marker_and_waits(self):
        process = _ProcessTester(pid=456)
        script_path = '/tmp/update_all_test_relaunch_script'
        marker_path = '/tmp/update_all_test_chipid_relaunch_started'
        handoff_path = '/tmp/update_all_test_chip_id_result'
        log_path = '/tmp/update_all_test_chipid.log'

        with patch('update_all.chip_id_linker.CHIP_ID_RELAUNCH_SCRIPT_PATH', script_path), \
                patch('update_all.chip_id_linker.CHIP_ID_RELAUNCH_SCRIPT_STARTED_PATH', marker_path), \
                patch('update_all.chip_id_linker.CHIP_ID_RESULT_HANDOFF_PATH', handoff_path), \
                patch('update_all.chip_id_linker._clear_visible_script_processes', return_value=None), \
                patch('update_all.chip_id_linker._clear_relaunch_script_start_marker', return_value=None) as clear_marker, \
                patch('update_all.chip_id_linker.CHIP_ID_RELAUNCH_AFTER_SCRIPT_CLEAR_SETTLE_SECONDS', 0), \
                patch('update_all.chip_id_linker._reset_script_tty'), \
                patch('update_all.chip_id_linker._open_script_console'), \
                patch('update_all.chip_id_linker._switch_to_relaunch_tty'), \
                patch('update_all.chip_id_linker._wait_for_relaunch_script_start', return_value=None) as wait_for_start, \
                patch('update_all.chip_id_linker.subprocess.Popen', return_value=process):
            result = chip_id_linker._relaunch_update_all_from_scripts_menu(
                _linker(log_path),
                '/media/fat/Scripts',
                restore_menu_after_relaunch=True,
                require_script_start_confirmation=True,
                chip_id_result='0123456789abcdef',
            )

        self.assertIsNone(result)
        clear_marker.assert_called_once_with(marker_path, ANY)
        wait_for_start.assert_called_once_with(process, marker_path, ANY)
        with open(script_path) as result_file:
            script = result_file.read()
        self.assertIn('mark_update_all_relaunch_started()', script)
        self.assertIn(f'> {marker_path}', script)
        self.assertIn('started marker written', script)
        _remove(script_path, marker_path, handoff_path, log_path)

    def test_relaunch_update_all_from_scripts_menu___when_script_does_not_start___terminates_agetty_and_returns_failure(self):
        process = _ProcessTester(pid=456, poll_result=None)
        script_path = '/tmp/update_all_test_relaunch_script'
        marker_path = '/tmp/update_all_test_chipid_relaunch_started'
        handoff_path = '/tmp/update_all_test_chip_id_result'
        log_path = '/tmp/update_all_test_chipid.log'

        with patch('update_all.chip_id_linker.CHIP_ID_RELAUNCH_SCRIPT_PATH', script_path), \
                patch('update_all.chip_id_linker.CHIP_ID_RELAUNCH_SCRIPT_STARTED_PATH', marker_path), \
                patch('update_all.chip_id_linker.CHIP_ID_RESULT_HANDOFF_PATH', handoff_path), \
                patch('update_all.chip_id_linker.CHIP_ID_RELAUNCH_SCRIPT_START_TIMEOUT_SECONDS', 0), \
                patch('update_all.chip_id_linker._clear_visible_script_processes', return_value=None), \
                patch('update_all.chip_id_linker.CHIP_ID_RELAUNCH_AFTER_SCRIPT_CLEAR_SETTLE_SECONDS', 0), \
                patch('update_all.chip_id_linker._reset_script_tty'), \
                patch('update_all.chip_id_linker._open_script_console'), \
                patch('update_all.chip_id_linker._switch_to_relaunch_tty'), \
                patch('update_all.chip_id_linker.os.path.exists', return_value=False), \
                patch('update_all.chip_id_linker._terminate_relaunch_process') as terminate_relaunch_process, \
                patch('update_all.chip_id_linker.subprocess.Popen', return_value=process):
            result = chip_id_linker._relaunch_update_all_from_scripts_menu(
                _linker(log_path),
                '/media/fat/Scripts',
                require_script_start_confirmation=True,
                chip_id_result='0123456789abcdef',
            )

        self.assertEqual('FAILURE_RELAUNCH_SCRIPT_START_TIMEOUT', result)
        terminate_relaunch_process.assert_called_once_with(process, ANY)
        _remove(script_path, marker_path, handoff_path, log_path)

    def test_wait_for_relaunch_script_start___returns_none_when_marker_appears(self):
        process = _ProcessTester(poll_result=None)

        with patch('update_all.chip_id_linker.os.path.exists', side_effect=[False, True]), \
                patch('update_all.chip_id_linker.time.sleep') as sleep:
            result = chip_id_linker._wait_for_relaunch_script_start(
                process,
                '/tmp/update_all_test_chipid_relaunch_started',
                _linker(),
            )

        self.assertIsNone(result)
        sleep.assert_called_once_with(0.05)

    def test_wait_for_relaunch_script_start___returns_failure_when_agetty_exits_before_marker(self):
        process = _ProcessTester(poll_result=1)

        with patch('update_all.chip_id_linker.os.path.exists', return_value=False), \
                patch('update_all.chip_id_linker.time.sleep') as sleep:
            result = chip_id_linker._wait_for_relaunch_script_start(
                process,
                '/tmp/update_all_test_chipid_relaunch_started',
                _linker(),
            )

        self.assertEqual('FAILURE_RELAUNCH_PROCESS_EXIT_1', result)
        sleep.assert_not_called()

    def test_restore_display_after_update_all_relaunch___presses_f12_and_restores_ttys_without_reloading_menu(self):
        log_path = '/tmp/update_all_test_chipid.log'

        with patch('update_all.chip_id_linker._create_uinput_keyboard', return_value=123) as create_keyboard, \
                patch('update_all.chip_id_linker._press_f12_for_menu') as press_f12, \
                patch('update_all.chip_id_linker._destroy_uinput_keyboard') as destroy_keyboard, \
                patch('update_all.chip_id_linker._reset_tty') as reset_tty, \
                patch('update_all.chip_id_linker._restore_cursor_blink') as restore_cursor, \
                patch('update_all.chip_id_linker._restore_menu_after_chip_id', return_value=None) as restore_menu, \
                patch('update_all.chip_id_linker.time.sleep') as sleep:
            result = chip_id_linker._restore_display_after_update_all_relaunch(_linker(log_path))

        self.assertIsNone(result)
        create_keyboard.assert_called_once_with(ANY)
        press_f12.assert_called_once_with(123, ANY)
        destroy_keyboard.assert_called_once_with(123, ANY)
        reset_tty.assert_has_calls([
            call('1', '_restore_display_after_update_all_relaunch', ANY),
            call('7', '_restore_display_after_update_all_relaunch', ANY),
        ])
        restore_cursor.assert_called_once_with(ANY)
        restore_menu.assert_not_called()
        sleep.assert_has_calls([
            call(chip_id_linker.CHIP_ID_RELAUNCH_CONSOLE_CLOSE_SETTLE_SECONDS),
            call(chip_id_linker.CHIP_ID_RELAUNCH_MENU_SETTLE_SECONDS),
        ])

    def test_restore_display_after_update_all_relaunch___when_requested___closes_console_then_reloads_menu(self):
        log_path = '/tmp/update_all_test_chipid.log'

        with patch('update_all.chip_id_linker._create_uinput_keyboard', return_value=123), \
                patch('update_all.chip_id_linker._press_f12_for_menu') as press_f12, \
                patch('update_all.chip_id_linker._destroy_uinput_keyboard'), \
                patch('update_all.chip_id_linker._reset_tty'), \
                patch('update_all.chip_id_linker._restore_cursor_blink'), \
                patch('update_all.chip_id_linker._restore_menu_after_chip_id', return_value=None) as restore_menu_call, \
                patch('update_all.chip_id_linker.time.sleep'):
            result = chip_id_linker._restore_display_after_update_all_relaunch(_linker(log_path), restore_menu_after_relaunch=True)

        self.assertIsNone(result)
        press_f12.assert_called_once_with(123, ANY)
        restore_menu_call.assert_called_once_with(ANY)

    def test_restore_display_after_update_all_relaunch___when_menu_restore_fails___still_closes_console(self):
        log_path = '/tmp/update_all_test_chipid.log'

        with patch('update_all.chip_id_linker._create_uinput_keyboard', return_value=123), \
                patch('update_all.chip_id_linker._press_f12_for_menu') as press_f12, \
                patch('update_all.chip_id_linker._destroy_uinput_keyboard'), \
                patch('update_all.chip_id_linker._reset_tty') as reset_tty, \
                patch('update_all.chip_id_linker._restore_cursor_blink'), \
                patch('update_all.chip_id_linker._restore_menu_after_chip_id', return_value='FAILURE_RESTORE_MENU_CORE_TIMEOUT_LINKER'), \
                patch('update_all.chip_id_linker.time.sleep') as sleep:
            result = chip_id_linker._restore_display_after_update_all_relaunch(_linker(log_path), restore_menu_after_relaunch=True)

        self.assertEqual('FAILURE_RESTORE_MENU_CORE_TIMEOUT_LINKER', result)
        press_f12.assert_called_once_with(123, ANY)
        reset_tty.assert_has_calls([
            call('1', '_restore_display_after_update_all_relaunch', ANY),
            call('7', '_restore_display_after_update_all_relaunch', ANY),
        ])
        sleep.assert_called_once_with(chip_id_linker.CHIP_ID_RELAUNCH_CONSOLE_CLOSE_SETTLE_SECONDS)

    def test_write_update_all_relaunch_script___when_direct_chipid_relaunch___restores_menu_after_exit(self):
        script_path = '/tmp/update_all_test_relaunch_script'
        log_path = '/tmp/update_all_test_chipid.log'

        chip_id_linker._write_update_all_relaunch_script(
            _linker(log_path),
            script_path,
            '/media/fat/Scripts',
            restore_menu_after_relaunch=True,
        )

        with open(script_path) as result_file:
            script = result_file.read()
        self.assertIn('--restore-after-relaunch --restore-menu-after-relaunch --log /tmp/update_all_test_chipid.log', script)
        _remove(script_path, log_path)

    def test_write_update_all_relaunch_script___uses_current_update_all_archive_when_available(self):
        script_path = '/tmp/update_all_test_relaunch_script'
        log_path = '/tmp/update_all_test_chipid.log'
        current_archive_path = _temp_zipapp()

        with patch('update_all.chip_id_linker.sys.argv', [current_archive_path, '--chip-id-linker']):
            chip_id_linker._write_update_all_relaunch_script(
                _linker(log_path),
                script_path,
                '/media/fat/Scripts',
            )

        with open(script_path) as result_file:
            script = result_file.read()
        self.assertIn(f'UPDATE_ALL_PYZ={current_archive_path}', script)
        self.assertNotIn('UPDATE_ALL_PYZ=/media/fat/Scripts/.config/update_all/update_all.pyz', script)
        _remove(script_path, current_archive_path, log_path)

    def test_write_update_all_relaunch_script___forwards_inherited_environment_without_command_or_stale_result(self):
        script_path = '/tmp/update_all_test_relaunch_script'
        log_path = '/tmp/update_all_test_chipid.log'

        inherited_environment = {
            'LOCATION_STR': '/media/fat',
            'CURL_SSL': '--insecure',
            'SSL_CERT_FILE': '/media/fat/Scripts/.config/downloader/cacert.pem',
            'MIRROR_ID': 'example',
            'HTTP_PROXY': 'http://proxy.example:8080',
            'VALUE_WITH_SPACE': 'hello world',
            'COMMAND': 'STANDARD',
            'UPDATE_ALL_CHIP_ID_RESULT': 'stale',
            'PWD': '/tmp',
            'BAD-NAME': 'bad',
            'BASH_FUNC_bad%%': '() { bad; }',
        }

        with patch.dict(chip_id_linker.os.environ, inherited_environment, clear=True):
            chip_id_linker._write_update_all_relaunch_script(
                _linker(log_path),
                script_path,
                '/media/fat/Scripts',
            )

        with open(script_path) as result_file:
            script = result_file.read()
        self.assertIn('export LOCATION_STR=/media/fat', script)
        self.assertIn('export CURL_SSL=--insecure', script)
        self.assertIn('export SSL_CERT_FILE=/media/fat/Scripts/.config/downloader/cacert.pem', script)
        self.assertIn('export MIRROR_ID=example', script)
        self.assertIn('export HTTP_PROXY=http://proxy.example:8080', script)
        self.assertIn("export VALUE_WITH_SPACE='hello world'", script)
        self.assertNotIn('COMMAND=', script)
        self.assertNotIn('UPDATE_ALL_CHIP_ID_RESULT', script)
        self.assertNotIn('export PWD=', script)
        self.assertNotIn('BAD-NAME', script)
        self.assertNotIn('BASH_FUNC_bad', script)
        _remove(script_path, log_path)

    def test_clear_visible_script_processes___terminates_stale_script_process_before_relaunch(self):
        active_process = [(123, '123 root S /bin/bash /tmp/script')]

        with patch('update_all.chip_id_linker.CHIP_ID_RELAUNCH_SCRIPT_DRAIN_SECONDS', 0), \
                patch('update_all.chip_id_linker._visible_script_processes', side_effect=[active_process, active_process, []]), \
                patch('update_all.chip_id_linker.os.kill') as os_kill:
            result = chip_id_linker._clear_visible_script_processes(_linker())

        self.assertIsNone(result)
        os_kill.assert_called_once_with(123, signal.SIGTERM)

    def test_open_script_console___from_menu_core___uses_zaparoo_f9_handoff_before_target_tty(self):
        with patch('update_all.chip_id_linker._create_uinput_keyboard', return_value=123) as create_keyboard, \
                patch('update_all.chip_id_linker._destroy_uinput_keyboard') as destroy_keyboard, \
                patch('update_all.chip_id_linker._switch_to_open_console_tty') as switch_open_tty, \
                patch('update_all.chip_id_linker._active_core_name', return_value='MENU'), \
                patch('update_all.chip_id_linker._active_tty', return_value='tty1'), \
                patch('update_all.chip_id_linker._wait_for_framebuffer_ready') as wait_fb, \
                patch('update_all.chip_id_linker._is_tty_console_ready', return_value=True) as is_tty_ready, \
                patch('update_all.chip_id_linker._press_f9_for_console') as press_f9, \
                patch('update_all.chip_id_linker.time.sleep') as sleep:
            chip_id_linker._open_script_console(_linker())

        create_keyboard.assert_called_once_with(ANY)
        press_f9.assert_called_once_with(123, ANY)
        wait_fb.assert_called_once()
        self.assertEqual(2, switch_open_tty.call_count)
        is_tty_ready.assert_called_once_with('3', ANY)
        destroy_keyboard.assert_called_once_with(123, ANY)
        sleep.assert_called_once_with(0.05)

    def test_open_script_console___presses_f9_until_console_is_ready(self):
        with patch('update_all.chip_id_linker._create_uinput_keyboard', return_value=123), \
                patch('update_all.chip_id_linker._destroy_uinput_keyboard'), \
                patch('update_all.chip_id_linker._switch_to_open_console_tty'), \
                patch('update_all.chip_id_linker._active_core_name', return_value='MENU'), \
                patch('update_all.chip_id_linker._active_tty', side_effect=['tty2', 'tty1']), \
                patch('update_all.chip_id_linker._wait_for_framebuffer_ready'), \
                patch('update_all.chip_id_linker._is_tty_console_ready', return_value=True), \
                patch('update_all.chip_id_linker._press_f9_for_console') as press_f9, \
                patch('update_all.chip_id_linker.time.sleep'):
            chip_id_linker._open_script_console(_linker())

        self.assertEqual(2, press_f9.call_count)
        press_f9.assert_has_calls([
            call(123, ANY),
            call(123, ANY),
        ])

    def test_relaunch_update_all_from_scripts_menu___hands_off_the_result_before_opening_the_console(self):
        script_path = '/tmp/update_all_test_relaunch_script'
        handoff_path = '/tmp/update_all_test_chip_id_result'
        log_path = '/tmp/update_all_test_chipid.log'
        handoff_seen_by_console = []

        def open_script_console(_linker_arg):
            with open(handoff_path) as handoff_file:
                handoff_seen_by_console.append(handoff_file.read())
            raise TimeoutError('timeout waiting for script console on tty3; current tty is tty3')

        with patch('update_all.chip_id_linker.CHIP_ID_RELAUNCH_SCRIPT_PATH', script_path), \
                patch('update_all.chip_id_linker.CHIP_ID_RESULT_HANDOFF_PATH', handoff_path), \
                patch('update_all.chip_id_linker._clear_visible_script_processes', return_value=None), \
                patch('update_all.chip_id_linker.CHIP_ID_RELAUNCH_AFTER_SCRIPT_CLEAR_SETTLE_SECONDS', 0), \
                patch('update_all.chip_id_linker._reset_script_tty'), \
                patch('update_all.chip_id_linker._open_script_console', side_effect=open_script_console), \
                patch('update_all.chip_id_linker.subprocess.Popen') as popen:
            result = chip_id_linker._relaunch_update_all_from_scripts_menu(
                _linker(log_path),
                '/media/fat/Scripts',
                restore_menu_after_relaunch=True,
                require_script_start_confirmation=True,
                chip_id_result='FAILURE_MEM_SIGBUS',
            )

        self.assertEqual('FAILURE_RELAUNCH_TIMEOUTERROR', result)
        self.assertEqual(['FAILURE_MEM_SIGBUS\n'], handoff_seen_by_console)
        popen.assert_not_called()
        with open(handoff_path) as handoff_file:
            self.assertEqual('FAILURE_MEM_SIGBUS\n', handoff_file.read())
        _remove(script_path, handoff_path, log_path)

    def test_relaunch_update_all_from_scripts_menu___when_the_handoff_cannot_be_written___fails_before_touching_the_console(self):
        with patch('update_all.chip_id_linker.CHIP_ID_RESULT_HANDOFF_PATH', '/nonexistent_update_all_dir/chip_id_result'), \
                patch('update_all.chip_id_linker._clear_visible_script_processes') as clear_scripts, \
                patch('update_all.chip_id_linker._open_script_console') as open_script_console, \
                patch('update_all.chip_id_linker.subprocess.Popen') as popen:
            result = chip_id_linker._relaunch_update_all_from_scripts_menu(
                _linker(), '/media/fat/Scripts', chip_id_result='0123456789abcdef'
            )

        self.assertEqual('FAILURE_RELAUNCH_HANDOFF_WRITE', result)
        clear_scripts.assert_not_called()
        open_script_console.assert_not_called()
        popen.assert_not_called()

    def test_write_chip_id_result_handoff___replaces_a_previous_result(self):
        with tempfile.TemporaryDirectory() as directory:
            handoff_path = os.path.join(directory, 'update_all_chip_id_result')

            self.assertIsNone(chip_id_linker._write_chip_id_result_handoff(handoff_path, 'FAILURE_MEM_SIGBUS', _linker()))
            self.assertIsNone(chip_id_linker._write_chip_id_result_handoff(handoff_path, '0123456789abcdef', _linker()))

            self.assertEqual(['update_all_chip_id_result'], os.listdir(directory))
            with open(handoff_path) as handoff_file:
                self.assertEqual('0123456789abcdef\n', handoff_file.read())

    def test_write_chip_id_result_handoff___without_a_result___writes_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            handoff_path = os.path.join(directory, 'update_all_chip_id_result')

            self.assertIsNone(chip_id_linker._write_chip_id_result_handoff(handoff_path, '', _linker()))

            self.assertEqual([], os.listdir(directory))

    def test_write_chip_id_result_handoff___when_the_directory_is_unusable___returns_a_failure_code(self):
        logger = LoggerSpy()
        handoff_path = '/nonexistent_update_all_dir/update_all_chip_id_result'

        result = chip_id_linker._write_chip_id_result_handoff(handoff_path, '0123456789abcdef', _linker(logger=logger))

        self.assertEqual('FAILURE_RELAUNCH_HANDOFF_WRITE', result)
        self.assertTrue(any(line.startswith('_write_chip_id_result_handoff: failed: ') for line in logger.debug_lines))

    def test_read_chip_id_from_memory_after_core_load___retries_transient_sigbus_until_chip_id_is_ready(self):
        with patch('update_all.chip_id_linker._read_chip_id_from_memory', side_effect=['FAILURE_MEM_SIGBUS', '0123456789abcdef']) as read_mem, \
                patch('update_all.chip_id_linker._wait_for_hps_fpga_lw_bridge_ready_after_core_load', return_value=None), \
                patch('update_all.chip_id_linker._is_firmware_fifo_available', return_value=True), \
                patch('update_all.chip_id_linker.time.sleep') as sleep:
            result = chip_id_linker._read_chip_id_from_memory_after_core_load(_linker())

        self.assertEqual('0123456789abcdef', result)
        self.assertEqual(2, read_mem.call_count)
        sleep.assert_called_once_with(0.1)

    def test_read_chip_id_from_memory_after_core_load___does_not_retry_bad_magic_after_bridge_safe_gate(self):
        with patch('update_all.chip_id_linker._read_chip_id_from_memory', return_value='FAILURE_BAD_MAGIC_00000000') as read_mem:
            result = chip_id_linker._read_chip_id_from_memory_after_core_load(_linker())

        self.assertEqual('FAILURE_BAD_MAGIC_00000000', result)
        read_mem.assert_called_once()

    def test_wait_for_firmware_core_restart_after_load___returns_none_when_core_name_marker_is_rewritten(self):
        with patch('update_all.chip_id_linker._file_mtime_ns', side_effect=[100, 200]), \
                patch('update_all.chip_id_linker.time.sleep') as sleep:
            result = chip_id_linker._wait_for_firmware_core_restart_after_load(100, _linker())

        self.assertIsNone(result)
        sleep.assert_called_once_with(0.05)

    def test_wait_for_firmware_core_restart_after_load___returns_failure_when_marker_does_not_change(self):
        with patch('update_all.chip_id_linker.CHIP_ID_FIRMWARE_CORE_RESTART_TIMEOUT_SECONDS', 0), \
                patch('update_all.chip_id_linker._file_mtime_ns', return_value=100), \
                patch('update_all.chip_id_linker.time.sleep') as sleep:
            result = chip_id_linker._wait_for_firmware_core_restart_after_load(100, _linker())

        self.assertEqual('FAILURE_FIRMWARE_CORE_RESTART_TIMEOUT', result)
        sleep.assert_not_called()

    def test_wait_for_hps_fpga_lw_bridge_ready_after_core_load___waits_for_stable_safe_status(self):
        ready_status = chip_id_linker.HpsFpgaStatus(fpga_mode=4, init_done=True, bridge_reset=0)

        with patch('update_all.chip_id_linker.CHIP_ID_HPS_FPGA_READY_STABLE_SECONDS', 0), \
                patch('update_all.chip_id_linker._read_hps_fpga_status', side_effect=[ready_status, ready_status]), \
                patch('update_all.chip_id_linker.time.sleep') as sleep:
            result = chip_id_linker._wait_for_hps_fpga_lw_bridge_ready_after_core_load(_linker())

        self.assertIsNone(result)
        sleep.assert_called_once_with(0.05)

    def test_wait_for_hps_fpga_lw_bridge_ready_after_core_load___returns_failure_without_touching_lw_bridge_when_status_read_fails(self):
        with patch('update_all.chip_id_linker._read_hps_fpga_status', side_effect=OSError('boom')):
            result = chip_id_linker._wait_for_hps_fpga_lw_bridge_ready_after_core_load(_linker())

        self.assertEqual('FAILURE_HPS_FPGA_STATUS_READ', result)

    def test_read_chip_id_from_registers___with_valid_registers___returns_chip_id(self):
        result = chip_id_linker._read_chip_id_from_registers(_chip_id_memory(id_hi=0x01234567, id_lo=0x89abcdef), 0, _linker())

        self.assertEqual('0123456789abcdef', result)

    def test_read_chip_id_from_registers___with_unsupported_version___returns_error_code(self):
        result = chip_id_linker._read_chip_id_from_registers(_chip_id_memory(version=0x00020000), 0, _linker())

        self.assertEqual('FAILURE_UNSUPPORTED_VERSION_00020000', result)

    def test_read_chip_id_from_registers___with_xor_mismatch___returns_error_code(self):
        result = chip_id_linker._read_chip_id_from_registers(_chip_id_memory(id_xor=0), 0, _linker())

        self.assertEqual('FAILURE_ID_XOR_MISMATCH_00000000_cbc0c1cc', result)

    def test_write_chip_id_display_control_to_registers___writes_blank_control(self):
        memory = bytearray(_chip_id_memory())

        result = chip_id_linker._write_chip_id_display_control_to_registers(
            memory,
            0,
            chip_id_linker.CHIP_ID_DISPLAY_CONTROL_BLANK,
            _linker(),
        )

        self.assertIsNone(result)
        self.assertEqual(
            chip_id_linker.CHIP_ID_DISPLAY_CONTROL_BLANK,
            struct.unpack_from('<I', memory, chip_id_linker.CHIP_ID_REG_DISPLAY_CONTROL)[0],
        )

    def test_write_chip_id_display_control_to_registers___rejects_bad_magic(self):
        memory = bytearray(_chip_id_memory())
        struct.pack_into('<I', memory, chip_id_linker.CHIP_ID_REG_MAGIC, 0)

        result = chip_id_linker._write_chip_id_display_control_to_registers(
            memory,
            0,
            chip_id_linker.CHIP_ID_DISPLAY_CONTROL_BLANK,
            _linker(),
        )

        self.assertEqual('FAILURE_DISPLAY_CONTROL_BAD_MAGIC_00000000', result)
        self.assertEqual(0, struct.unpack_from('<I', memory, chip_id_linker.CHIP_ID_REG_DISPLAY_CONTROL)[0])



def _logger():
    return _ChipIdLinkerCommandLoggerTester()


class _ChipIdLinkerCommandLoggerTester(NoLogger):
    def __init__(self):
        self.logfile_calls = []

    def set_logfile(self, logfile_path, append=False, eager=False):
        self.logfile_calls.append((logfile_path, append, eager))


class _ProcessTester:
    def __init__(self, pid=0, poll_result=None):
        self.pid = pid
        self._poll_result = poll_result

    def poll(self):
        return self._poll_result


def _chip_id_memory(id_hi=0x01234567, id_lo=0x89abcdef, version=0x00010000, status=1, id_xor=None) -> bytes:
    if id_xor is None:
        id_xor = id_lo ^ id_hi ^ 0x43484944

    memory = bytearray(0x20)
    struct.pack_into('<I', memory, 0x00, 0x43484944)
    struct.pack_into('<I', memory, 0x04, version)
    struct.pack_into('<I', memory, 0x08, status)
    struct.pack_into('<I', memory, 0x0c, id_lo)
    struct.pack_into('<I', memory, 0x10, id_hi)
    struct.pack_into('<I', memory, 0x14, id_xor)
    return bytes(memory)


def _temp_file(content: bytes) -> str:
    with tempfile.NamedTemporaryFile(delete=False) as file:
        file.write(content)
        return file.name


def _temp_zipapp() -> str:
    with tempfile.NamedTemporaryFile(delete=False) as file:
        path = file.name
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('__main__.py', '')
    return path


def _linker(log_path='/tmp/update_all_test_chipid.log', logger=None):
    return chip_id_linker.ChipIdLinker(logger or NoLogger(), log_path)


def _remove(*paths: str) -> None:
    for path in paths:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
