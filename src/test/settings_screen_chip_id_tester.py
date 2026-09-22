import json
import os
from pathlib import Path
import subprocess
import sys

from test.chip_id_linker_tester import ChipIdLinkerTester
from test.update_all_service_tester import SettingsScreenTester
from update_all.constants import KENV_LAUNCH_ORIGIN_ID
from update_all.other import GenericProvider
from update_all.settings_screen import _PendingChipIdExtraction


class SettingsScreenChipIdTester(SettingsScreenTester):
    @staticmethod
    def run_with_inherited_origin(origin):
        environment = dict(os.environ)
        environment.pop(KENV_LAUNCH_ORIGIN_ID, None)
        if origin is not None:
            environment[KENV_LAUNCH_ORIGIN_ID] = origin
        process = subprocess.run(
            [sys.executable, '-c', '''import json
import os
from test.settings_screen_chip_id_tester import SettingsScreenChipIdTester
from test.update_all_service_tester import ConfigReaderTester
from update_all.config import Config
from update_all.constants import KENV_LAUNCH_ORIGIN_ID
from update_all.main import read_env

config = Config()
ConfigReaderTester(env=read_env('test', 0.0)).fill_config_with_environment(config)
screen = SettingsScreenChipIdTester(config)
try:
    screen.start_worker()
    # agetty may reset the environment; the wrapper must restore its saved origin.
    relaunch_environment = dict(os.environ)
    if KENV_LAUNCH_ORIGIN_ID in relaunch_environment:
        relaunch_environment[KENV_LAUNCH_ORIGIN_ID] = 'unrelated-launcher'
    process = screen.linker.run_relaunch_script(env=relaunch_environment)
    print(json.dumps({
        'returncode': process.returncode,
        'stderr': process.stderr.decode(),
        'origins': screen.linker.read_origins(),
        'events': screen.linker.read_events(),
        'log_path': screen.linker.log_path,
    }))
finally:
    screen.close()
'''],
            cwd=Path(__file__).resolve().parents[1], env=environment, capture_output=True, text=True,
            timeout=20, check=True,
        )
        return json.loads(process.stdout)

    def __init__(self, config):
        provider = GenericProvider()
        provider.initialize(config)
        super().__init__(config_provider=provider)
        self.linker = ChipIdLinkerTester()
        self.workers = []

    def start_worker(self):
        self.linker.install_test_archive(exit_code=2)
        self._pending_chip_id_extraction = _PendingChipIdExtraction(
            command=[sys.executable, '-c', '''import os
import sys
from pathlib import Path
from update_all.chip_id_linker.chip_id_linker import ChipIdLinker, _write_update_all_relaunch_script, _write_worker_startup_marker
from update_all.chip_id_linker.chip_id_system import ChipIdSystem
from update_all.chip_id_linker.console_system import ConsoleSystem
from update_all.logger import PrintLogger
from update_all.main import read_env

root = Path(sys.argv[1])
logger = PrintLogger()
linker = ChipIdLinker(logger, str(root / 'linker.log'), read_env('test', 0.0),
                      ChipIdSystem(os.environ), ConsoleSystem(logger.debug, '/proc', '/dev'))
_write_update_all_relaunch_script(
    linker, str(root / 'script'), str(root),
    start_marker_path=str(root / 'started'), run_pyz_path=str(root / 'run.pyz'),
)
_write_worker_startup_marker(str(root / 'worker.started'), linker)
''', str(self.linker.root)],
            startup_marker_path=str(self.linker.root / 'worker.started'),
            bootstrap_log_path=str(self.linker.root / 'bootstrap.log'),
        )
        self._start_pending_chip_id_extraction_after_ui_shutdown()
        for worker in self.workers:
            if worker.wait(timeout=5) != 0:
                raise AssertionError((self.linker.root / 'bootstrap.log').read_text())
        if not self.linker.script_path.exists():
            raise AssertionError((self.linker.root / 'bootstrap.log').read_text())

    def _wait_for_chip_id_worker_startup(self, process, marker_path):
        self.workers.append(process)
        return super()._wait_for_chip_id_worker_startup(process, marker_path)

    def close(self):
        for worker in self.workers:
            if worker.poll() is None:
                worker.kill()
            worker.wait(timeout=5)
        self.linker.close()
