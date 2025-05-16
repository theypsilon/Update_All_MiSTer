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
from pathlib import Path
from typing import Dict, Any

from test.ini_assertions import testableIni
from test.testing_objects import downloader_ini, update_all_ini, update_jtcores_ini, update_names_txt_ini
from update_all.config import Config
from update_all.constants import KENV_DEBUG, KENV_LOCATION_STR, FILE_update_all_storage, KENV_TRANSITION_SERVICE_ONLY
from update_all.databases import DB_ID_NAMES_TXT, AllDBs, DB_ID_ARCADE_NAMES_TXT
from update_all.environment_setup import EnvironmentSetupResult
from update_all.local_store import LocalStore
from update_all.other import GenericProvider
from test.fake_filesystem import FileSystemFactory
from test.file_system_tester_state import FileSystemState
from test.update_all_service_tester import EnvironmentSetupTester, default_databases, default_env
import unittest


class TestEnvironmentSetup(unittest.TestCase):

    def assertSetup(self, files: Dict[str, Any] = None, env: dict[str, str] = None, expected_files: Dict[str, str] = None, expected_config: Config = None, expected_result: EnvironmentSetupResult = None) -> None:
        state = FileSystemState(files=None if files is None else {k: {'content': processIni(v)} for k, v in files.items()})
        config_provider = GenericProvider[Config]()
        store_provider = GenericProvider[LocalStore]()

        file_system = FileSystemFactory(state=state, config_provider=config_provider).create_for_system_scope()
        environment_setup = EnvironmentSetupTester(
            file_system=file_system,
            config_provider=config_provider,
            store_provider=store_provider,
            env=None if env is None else {**default_env(), **env}
        )
        expected_files = expected_files or {k: v['content'].strip() for k, v in state.files.items()}
        expected_files = {k: processIni(v.strip()) for k, v in expected_files.items()}

        result = environment_setup.setup_environment()

        config = config_provider.get()
        config.start_time = 0.0
        self.assertEqual(expected_files, {k: processIni(v['content'].strip()) for k, v in state.files.items() if 'content' in v and not k.endswith(FILE_update_all_storage.lower())})
        self.assertEqual(expected_config or Config(), config)
        self.assertEqual(expected_result or EnvironmentSetupResult(), result)

    def test_setup___with_empty_files___generates_default_downloader_ini_and_config_with_default_databases(self):
        self.assertSetup(
            files={},
            expected_files={downloader_ini: Path('test/fixtures/downloader_ini/default_downloader.ini').read_text()},
            expected_config=Config(databases=default_databases())
        )

    def test_setup___with_empty_downloader_ini_and_custom_location_str___returns_config_with_custom_paths_and_not_mister_activated(self):
        self.assertSetup(
            files={downloader_ini: ''},
            env={KENV_LOCATION_STR: '/custom'},
            expected_files={downloader_ini: Path('test/fixtures/downloader_ini/downloader_ini_empty_but_update_all.ini').read_text()},
            expected_config=Config(not_mister=True, base_path='/custom', base_system_path='/custom', databases={AllDBs.UPDATE_ALL_MISTER.db_id})
        )

    def test_setup___with_empty_downloader_ini___returns_empty_config(self):
        self.assertSetup(
            files={downloader_ini: ''},
            expected_files={downloader_ini: Path('test/fixtures/downloader_ini/downloader_ini_empty_but_update_all.ini').read_text()},
            expected_config=Config(databases={AllDBs.UPDATE_ALL_MISTER.db_id})
        )

    def test_setup___with_empty_downloader_ini_and_debug_env___returns_config_with_verbose_activated(self):
        self.assertSetup(
            files={downloader_ini: ''},
            expected_files={downloader_ini: Path('test/fixtures/downloader_ini/downloader_ini_empty_but_update_all.ini').read_text()},
            env={KENV_DEBUG: 'true'},
            expected_config=Config(verbose=True, databases={AllDBs.UPDATE_ALL_MISTER.db_id})
        )

    def test_setup___with_default_downloader_ini_and_update_all_ini_with_disabled_arcade_organizer___returns_config_with_default_databases_and_disabled_ao(self):
        self.assertSetup(files={
            downloader_ini: Path('test/fixtures/downloader_ini/default_downloader.ini').read_text(),
            update_all_ini: Path('test/fixtures/update_all_ini/complete_ua_first.ini').read_text()
        }, expected_files={
            downloader_ini: Path('test/fixtures/downloader_ini/default_downloader.ini').read_text(),
        }, expected_config=Config(databases=default_databases(), arcade_organizer=False))

    def test_setup___with_only_update_all_ini_with_disabled_arcade_organizer___returns_empty_config(self):
        self.assertSetup(files={
            update_all_ini: Path('test/fixtures/update_all_ini/complete_ua_first.ini').read_text(),
            update_jtcores_ini: Path('test/fixtures/update_jtcores_ini/complete_jt.ini').read_text(),
            update_names_txt_ini: Path('test/fixtures/update_names-txt_ini/complete_nt.ini').read_text(),
        }, expected_files={
            downloader_ini: Path('test/fixtures/downloader_ini/complete_downloader_first.ini').read_text(),
        }, expected_config=Config(databases=default_databases(add=[DB_ID_NAMES_TXT, DB_ID_ARCADE_NAMES_TXT]), arcade_organizer=False, encc_forks="db9", download_beta_cores=True, names_region='EU', names_char_code='CHAR28'))

    def test_setup___with_downloader_with_custom_names_db___returns_empty_config(self):
        self.assertSetup(files={
            downloader_ini: Path('test/fixtures/downloader_ini/complete_downloader_first.ini').read_text()
        }, expected_config=Config(databases=default_databases(add=[DB_ID_NAMES_TXT, DB_ID_ARCADE_NAMES_TXT]), encc_forks="db9", download_beta_cores=True, names_region='EU', names_char_code='CHAR28'))

    def test_setup___with_downloader_with_rannysnice_43_wallpapers_db___returns_empty_config(self):
        self.assertSetup(files={
            downloader_ini: Path('test/fixtures/downloader_ini/rannysnice_43_wallpapers_downloader.ini').read_text()
        }, expected_config=Config(databases=default_databases(add=[AllDBs.RANNYSNICE_WALLPAPERS.db_id]), rannysnice_wallpapers_filter='ar4-3'))

    def test_setup___with_downloader_with_just_jtpremium_db___returns_config_has_jtpremium_and_beta_Cores(self):
        self.assertSetup(
            files={downloader_ini: Path('test/fixtures/downloader_ini/just_jtpremium.ini').read_text()},
            expected_config=Config(databases={AllDBs.JTCORES.db_id, AllDBs.UPDATE_ALL_MISTER.db_id}, download_beta_cores=True),
            expected_files={downloader_ini: Path('test/fixtures/downloader_ini/just_jtcores_with_mister_inheritance.ini').read_text()}
        )

    def test_setup___with_downloader_with_just_jtcores_db___returns_config_has_not_jtpremium_neither_beta_cores(self):
        self.assertSetup(files={
            downloader_ini: Path('test/fixtures/downloader_ini/just_jtcores.ini').read_text()
        }, expected_config=Config(databases={AllDBs.JTCORES.db_id, AllDBs.UPDATE_ALL_MISTER.db_id}, download_beta_cores=False))

    def test_setup___with_downloader_with_just_jtcores_with_mister_inheritance_filter_db___returns_config_has_not_jtpremium_but_has_beta_cores(self):
        self.assertSetup(files={
            downloader_ini: Path('test/fixtures/downloader_ini/just_jtcores_with_mister_inheritance.ini').read_text()
        }, expected_config=Config(databases={AllDBs.JTCORES.db_id, AllDBs.UPDATE_ALL_MISTER.db_id}, download_beta_cores=True))

    def test_setup___with_downloader_with_just_jtcores_and_negated_jtbeta_db___returns_config_has_not_jtpremium_neither_beta_cores(self):
        self.assertSetup(files={
            downloader_ini: Path('test/fixtures/downloader_ini/just_jtcores_with_negated_jtbeta.ini').read_text()
        }, expected_config=Config(databases={AllDBs.JTCORES.db_id, AllDBs.UPDATE_ALL_MISTER.db_id}, download_beta_cores=False))

    def test_setup___with_mistersam_on_main_branch___writes_downloader_ini_with_mistersam_on_db_branch(self):
        self.assertSetup(
            files={downloader_ini: Path('test/fixtures/downloader_ini/db_url_changes/mistersam_on_main.ini').read_text()},
            expected_config=Config(databases={AllDBs.MISTERSAM_FILES.db_id, AllDBs.UPDATE_ALL_MISTER.db_id}),
            expected_files={downloader_ini: Path('test/fixtures/downloader_ini/db_url_changes/mistersam_on_db.ini').read_text()}
        )

    def test_setup___with_transition_service_only_env_var___returns_requires_early_exit_result(self):
        self.assertSetup(
            env={KENV_TRANSITION_SERVICE_ONLY: ' TRUE '},
            files={
                downloader_ini: Path('test/fixtures/downloader_ini/default_downloader.ini').read_text(),
            },
            expected_config=Config(databases=default_databases(), transition_service_only=True),
            expected_result=EnvironmentSetupResult(requires_early_exit=True)
        )


def processIni(maybe_ini):
    try:
        return testableIni(maybe_ini)
    except Exception as _e:
        return maybe_ini
