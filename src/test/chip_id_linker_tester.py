import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from test.chip_id_system_tester import ChipIdSystemTester
from test.console_system_tester import ConsoleSystemTester
from test.degauss_console_tester import DegaussConsoleTester
from test.logger_tester import LoggerSpy
from test.zaparoo_console_tester import ZaparooConsoleTester
from update_all.chip_id_linker.chip_id_linker import ChipIdLinker, _parse_args, _validate_args, \
    _write_update_all_relaunch_script, _write_zaparoo_relaunch_script, _relaunch_update_all_from_scripts_menu
from update_all.logger import FileLoggerDecorator


class ChipIdLinkerTester(ChipIdLinker):
    def __init__(self, logger=None, env=None, environment=None, root=None):
        self.directory = tempfile.TemporaryDirectory() if root is None else None
        self.root = Path(self.directory.name if root is None else root)
        self.script_path = self.root / 'script'
        self.events_path = self.root / 'events'
        self.origins_path = self.root / 'origins'
        self.marker_path = self.root / 'started'
        self.logger = logger if logger is not None else LoggerSpy()
        log_path = str(self.root / 'linker.log')
        self.file_logger = FileLoggerDecorator(self.logger, log_path)
        system = ChipIdSystemTester(self.root, self.file_logger, environment=environment)
        system.log_path = log_path
        self.console = ConsoleSystemTester()
        super().__init__(self.file_logger, log_path, {} if env is None else env, system, self.console)
        self.degauss = DegaussConsoleTester(self.console)
        self.zaparoo = ZaparooConsoleTester(
            self.console,
            on_acquire=lambda tty: system.path('/sys/devices/virtual/tty/tty0/active').write_text(f'tty{tty}\n'),
        )

    def run_command(self, argv):
        args = _parse_args([*argv, '--log', self.log_path])
        _validate_args(args)
        self.system.worker_marker_path = args.startup_marker
        return self.run(args)

    def relaunch(self, chip_id_result='', restore_menu=False, confirm_start=False):
        return _relaunch_update_all_from_scripts_menu(
            self, str(self.root), restore_menu_after_relaunch=restore_menu,
            require_script_start_confirmation=confirm_start, chip_id_result=chip_id_result,
        )

    def start_late_degauss(self):
        self.system.f9_console_after = None
        self.system.schedule(0.2, self.degauss.start_frontend)
        self.console.before_stop = self._enable_f9_after_degauss_stop

    def _enable_f9_after_degauss_stop(self, process):
        self.system.f9_console_after = 1

    def run_hard_exit_worker(self):
        script = '''from test.chip_id_linker_tester import ChipIdLinkerTester
import sys

linker = ChipIdLinkerTester(root=sys.argv[3])
linker.system.hard_exit_on_load = 23
linker.log_path = sys.argv[1]
linker.system.log_path = linker.log_path
linker.run_command(['--rbf', '/tmp/Linker.rbf', '--update-all-dir', '/tmp', '--startup-marker', sys.argv[2]])
'''
        environment = dict(os.environ)
        environment['TMPDIR'] = str(self.root)
        marker = self.root / 'worker.started'
        process = subprocess.run(
            [sys.executable, '-c', script, self.log_path, str(marker), str(self.root)],
            cwd=Path(__file__).resolve().parents[1], env=environment, capture_output=True, text=True, timeout=10,
        )
        return process, list(self.root.rglob('worker.started'))

    def install_test_archive(self, exit_code=23, continue_exit_code=0, restore_exit_code=0,
                             require_start_marker=True, signal_parent=None):
        archive_path = self.root / '.config/update_all/update_all.pyz'
        archive_path.parent.mkdir(parents=True)
        main = f'''import json, os, sys
if '--blank-display' in sys.argv:
    sys.exit(0)
with open({str(self.events_path)!r}, 'a') as events:
    events.write(json.dumps(sys.argv[1:]) + '\\n')
with open({str(self.origins_path)!r}, 'a') as origins:
    origins.write(json.dumps(os.environ.get('LAUNCH_ORIGIN_ID')) + '\\n')
if '--restore-after-relaunch' in sys.argv:
    sys.exit({restore_exit_code})
if {require_start_marker!r}:
    assert os.path.exists({str(self.marker_path)!r})
if {signal_parent!r} is not None:
    os.kill(os.getppid(), {signal_parent!r})
sys.exit({continue_exit_code} if '--continue' in sys.argv else {exit_code})
'''
        with zipfile.ZipFile(archive_path, 'w') as archive:
            archive.writestr('__main__.py', main)

    def write_relaunch_script(self, token, restore_menu=True, confirm_start=True):
        if token:
            _write_zaparoo_relaunch_script(
                self, str(self.script_path), str(self.root), token, restore_menu_after_relaunch=restore_menu,
                start_marker_path=str(self.marker_path) if confirm_start else None,
                run_pyz_path=str(self.root / 'run.pyz'),
            )
        else:
            _write_update_all_relaunch_script(
                self, str(self.script_path), str(self.root), restore_menu_after_relaunch=restore_menu,
                start_marker_path=str(self.marker_path) if confirm_start else None,
                run_pyz_path=str(self.root / 'run.pyz'),
            )

    def run_relaunch_script(self, env=None):
        return subprocess.run(['bash', str(self.script_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=5, env=env)

    def read_events(self):
        return [json.loads(line) for line in self.events_path.read_text().splitlines()]

    def read_origins(self):
        return [json.loads(line) for line in self.origins_path.read_text().splitlines()]

    def close(self):
        self.file_logger.finalize()
        self.system.close_remaining_descriptors()
        self.console.close()
        if self.directory is not None:
            self.directory.cleanup()
