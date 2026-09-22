import json
import os
from pathlib import Path
import subprocess
import sys

from test.fake_filesystem import FileSystemFactory
from test.logger_tester import LoggerSpy
from test.update_all_service_tester import EnvironmentSetupStub, RetroAccountServiceTester, UpdateAllServiceTester, local_store
from update_all.config import Config
from update_all.constants import KENV_LAUNCH_ORIGIN_ID
from update_all.other import GenericProvider


class MainTester:
    def __init__(self):
        self.logger = LoggerSpy()

    def create_update_all_service(self, environment_setup_result=None):
        config_provider = GenericProvider()
        config_provider.initialize(Config(non_interactive=True, skip_downloader=True))
        store_provider = GenericProvider()
        store_provider.initialize(local_store())
        file_system = FileSystemFactory(config_provider=config_provider).create_for_system_scope()
        self.environment_setup = EnvironmentSetupStub(environment_setup_result)
        self.retroaccount = RetroAccountServiceTester(file_system=file_system, config_provider=config_provider)
        return UpdateAllServiceTester(
            logger=self.logger,
            config_provider=config_provider,
            store_provider=store_provider,
            file_system=file_system,
            environment_setup=self.environment_setup,
            retroaccount=self.retroaccount,
        )

    def run_linker_help(self):
        process = subprocess.run(
            [sys.executable, '-c', '''import json
import sys
from update_all.main import execute_update_all
from update_all.logger import PrintLogger
from update_all.other import GenericProvider

try:
    execute_update_all(PrintLogger(), GenericProvider(), {}, args=sys.argv)
except SystemExit:
    print(json.dumps(sorted(name for name in sys.modules if name.startswith('update_all.'))))
    raise
''', '--chip-id-linker', '--help'],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True,
            timeout=10,
        )
        return process, json.loads(process.stdout.splitlines()[-1])

    def loaded_application_modules(self, module_name):
        process = subprocess.run(
            [sys.executable, '-c', '''import importlib
import json
import sys

importlib.import_module(sys.argv[1])
print(json.dumps(sorted(name for name in sys.modules if name.startswith('update_all.'))))
''', module_name],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True,
            timeout=10, check=True,
        )
        return json.loads(process.stdout)

    def read_env(self, environment):
        process = subprocess.run(
            [sys.executable, '-c', '''import json
from update_all.main import read_env

print(json.dumps(read_env('default-commit', 123.0)))
'''],
            cwd=Path(__file__).resolve().parents[1], env=environment, capture_output=True, text=True,
            timeout=10, check=True,
        )
        return json.loads(process.stdout)

    def read_launch_origin(self, value=None):
        environment = dict(os.environ)
        environment.pop(KENV_LAUNCH_ORIGIN_ID, None)
        if value is not None:
            environment[KENV_LAUNCH_ORIGIN_ID] = value
        process = subprocess.run(
            [sys.executable, '-c', '''import json
from update_all.main import read_env
from update_all.config import Config
from update_all.constants import KENV_LAUNCH_ORIGIN_ID
from test.update_all_service_tester import ConfigReaderTester

environment = read_env('test', 0.0)
config = Config()
ConfigReaderTester(env=environment).fill_config_with_environment(config)
print(json.dumps([environment[KENV_LAUNCH_ORIGIN_ID], config.launch_origin_id]))
'''],
            cwd=Path(__file__).resolve().parents[1], env=environment, capture_output=True, text=True,
            timeout=10, check=True,
        )
        return json.loads(process.stdout)
