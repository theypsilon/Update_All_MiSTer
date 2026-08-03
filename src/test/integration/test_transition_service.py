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
import unittest
import json
from pathlib import Path
from typing import Dict, Any, List

from test.fake_filesystem import FileSystemFactory
from test.file_system_tester_state import FileSystemState
from test.ini_assertions import assertEqualIni, testableIni
from test.testing_objects import downloader_ini, update_all_ini, update_arcade_organizer_ini, update_names_txt_ini, \
    update_jtcores_ini, downloader_store, manuals_ini, ini_with_db_ids as downloader_ini_with_db_ids, all_manuals_db_ids
from test.update_all_service_tester import TransitionServiceTester, local_store, IniRepositoryTester, \
    ConfigReaderTester, default_env
from test.update_output_tester import UpdateOutputTester
from test.spy_os_utils import SpyOsUtils
from update_all.config import Config
from update_all.constants import KENV_SKIP_DOWNLOADER
from update_all.databases import ALL_DB_IDS, all_dbs, DB_ID_DISTRIBUTION_MISTER, DB_ID_MREXT_ALL, DB_ID_MREXT_TAPTO, \
    DB_ID_ZAPAROO_MISTER
from update_all.ini_repository import read_ini_contents
from update_all.transition_service import RELATED_DATABASE_ACTIVATION_RELATIONSHIPS
from update_all.update_output import NoopUpdateOutput


def test_transitions(files: Dict[str, str] = None, store=None, update_output=None):
    config = Config()
    fs_state = FileSystemState(config=config, files=None if files is None else {filename: read_content(path) for filename, path in files.items()})
    return test_transitions_with_state(config, fs_state, store, update_output)


def test_transitions_with_contents(files: Dict[str, str], store=None, update_output=None):
    config = Config()
    fs_state = FileSystemState(config=config, files={filename: {'content': content} for filename, content in files.items()})
    return test_transitions_with_state(config, fs_state, store, update_output)


def test_transitions_with_state(config: Config, fs_state: FileSystemState, store=None, update_output=None):
    store = store or local_store()
    update_output = update_output or NoopUpdateOutput()
    fs = FileSystemFactory(state=fs_state).create_for_system_scope()
    ini_repos = IniRepositoryTester(file_system=fs)
    config_reader = ConfigReaderTester(downloader_ini_repository=ini_repos, file_system=fs)
    sut = TransitionServiceTester(file_system=fs, ini_repository=ini_repos)
    downloader_ini = config_reader.read_downloader_ini()
    sut.from_old_db_ids_to_new_db_ids(downloader_ini, update_output)
    sut.removing_obsolete_db_ids(downloader_ini, update_output)
    config_reader.fill_config_with_mister_section(config, downloader_ini)
    config_reader.fill_config_with_environment(config)
    config_reader.fill_config_with_database_sections(config, downloader_ini)
    sut.from_not_existing_downloader_ini(config, update_output)
    sut.from_update_all_1(config, store, update_output)
    sut.from_just_names_txt_enabled_to_arcade_names_txt_enabled(config, store, update_output)
    sut.from_active_databases_to_related_databases(config, store, update_output)
    sut.from_old_db_urls_to_actual_db_urls(config, downloader_ini, update_output)
    sut.from_no_update_all_mister_db_to_adding_it(config, downloader_ini, update_output)
    return fs_state


def run_manuals_transition(files: Dict[str, str], store=None, update_output=None, os_utils=None, env=None):
    config = Config()
    fs_state = FileSystemState(config=config, files={filename: {'content': content} for filename, content in files.items()})
    fs = FileSystemFactory(state=fs_state).create_for_system_scope()
    os_utils = os_utils or SpyOsUtils()
    ini_repos = IniRepositoryTester(file_system=fs, os_utils=os_utils)
    config_reader = ConfigReaderTester(downloader_ini_repository=ini_repos, file_system=fs, env=None if env is None else {**default_env(), **env})
    sut = TransitionServiceTester(file_system=fs, os_utils=os_utils, ini_repository=ini_repos)
    config_reader.fill_config_with_environment(config)
    config_reader.fill_config_with_database_sections(config, config_reader.read_downloader_ini())
    sut.from_select_all_manuals_to_adding_new_manuals_dbs(config, store or local_store(), update_output or NoopUpdateOutput())
    return fs_state


def manuals_db_ids_in(fs_state: FileSystemState) -> List[str]:
    path = manuals_ini.lower()
    if path not in fs_state.files:
        return []

    return read_ini_contents(fs_state.files[path]['content']).sections()


class TestTransitionService(unittest.TestCase):
    def test_on_empty_state___writes_default_downloader_ini(self):
        fs = test_transitions()
        assertEqualIni(self, 'test/fixtures/downloader_ini/default_downloader.ini', fs.files[downloader_ini]['content'])

    def test_transition_event___is_emitted_before_waiting(self):
        config = Config()
        fs_state = FileSystemState(config=config, files={})
        fs = FileSystemFactory(state=fs_state).create_for_system_scope()
        os_utils = SpyOsUtils()
        ini_repos = IniRepositoryTester(file_system=fs, os_utils=os_utils)
        output = UpdateOutputTester(os_utils)
        sut = TransitionServiceTester(file_system=fs, os_utils=os_utils, ini_repository=ini_repos)

        sut.from_not_existing_downloader_ini(config, output)

        self.assertEqual([(
            'from_not_existing_downloader_ini',
            {
                'downloader_ini': ini_repos.downloader_ini_standard_path(),
                'db_ids': ','.join([
                    ALL_DB_IDS["UPDATE_ALL_MISTER"],
                    DB_ID_DISTRIBUTION_MISTER,
                    ALL_DB_IDS["JTCORES"],
                    ALL_DB_IDS["COIN_OP_COLLECTION"],
                ]),
            }
        )], output.transition_calls)
        self.assertEqual([[]], output.sleep_calls_at_transition)
        self.assertEqual([10.0], os_utils.calls_to_sleep)

    def test_with_dirty_downloader_ini___writes_nothing(self):
        fs = test_transitions(files={downloader_ini: 'test/fixtures/downloader_ini/dirty_downloader.ini'})
        assertEqualIni(self, 'test/fixtures/downloader_ini/dirty_downloader.ini', fs.files[downloader_ini]['content'])

    def test_with_downloader_ini_and_other_inis_with_disabled_ao___just_keeps_downloader_ini(self):
        fs = test_transitions(files={
            downloader_ini: 'test/fixtures/downloader_ini/default_downloader.ini',
            update_all_ini: 'test/fixtures/update_all_ini/complete_ua_first.ini',
        })
        self.assertEqualFiles({
            downloader_ini: 'test/fixtures/downloader_ini/default_downloader.ini',
        }, fs.files)

    def test_with_update_all_ini_with_names_and_encc___writes_corresponding_downloader_ini(self):
        fs = test_transitions(files={
            update_all_ini: 'test/fixtures/update_all_ini/complete_ua_first.ini',
            update_names_txt_ini: 'test/fixtures/update_names-txt_ini/complete_nt.ini',
            update_jtcores_ini: 'test/fixtures/update_jtcores_ini/complete_jt.ini',
        })
        self.assertEqualFiles({
            downloader_ini: 'test/fixtures/downloader_ini/complete_downloader_first.ini',
        }, fs.files)

    def test_with_just_update_all_ini_with_opposite_to_defaults___writes_corresponding_downloader_ini(self):
        fs = test_transitions(files={
            update_all_ini: 'test/fixtures/update_all_ini/complete_ua_second.ini',
        })
        self.assertEqualFiles({
            downloader_ini: 'test/fixtures/downloader_ini/complete_downloader_second.ini',
        }, fs.files)

    def test_with_just_update_jtcores_ini___writes_corresponding_downloader_ini(self):
        fs = test_transitions(files={
            update_jtcores_ini: 'test/fixtures/update_jtcores_ini/complete_jt.ini',
        })
        self.assertEqualFiles({
            downloader_ini: 'test/fixtures/downloader_ini/default_premium_downloader.ini',
        }, fs.files)

    def test_with_just_jtpremium_in_downloader_ini___writes_downloader_ini_with_jtcores_with_mister_inheritance(self):
        fs = test_transitions(files={
            downloader_ini: 'test/fixtures/downloader_ini/just_jtpremium.ini',
        })
        self.assertEqualFiles({
            downloader_ini: 'test/fixtures/downloader_ini/just_jtcores_with_mister_inheritance.ini',
        }, fs.files)

    def test_with_just_jtpremium_with_filter_wtf_in_downloader_ini___writes_downloader_ini_with_jtcores_with_filter_wtf(self):
        fs = test_transitions(files={
            downloader_ini: 'test/fixtures/downloader_ini/just_jtpremium_with_filter_wtf.ini',
        })
        self.assertEqualFiles({
            downloader_ini: 'test/fixtures/downloader_ini/just_jtcores_with_filter_wtf.ini',
        }, fs.files)

    def test_mistersam_on_main_branch___writes_downloader_ini_with_mistersam_on_db_branch(self):
        fs = test_transitions(files={
            downloader_ini: 'test/fixtures/downloader_ini/db_url_changes/mistersam_on_main.ini',
        })
        self.assertEqualFiles({
            downloader_ini: 'test/fixtures/downloader_ini/db_url_changes/mistersam_on_db.ini',
        }, fs.files)

    def test_coin_op_from_atrac17_ini___writes_downloader_ini_with_coin_op_org_db_id_and_url(self):
        fs = test_transitions(files={
            downloader_store: 'test/fixtures/downloader_ini/db_id_changes/old_coin_op_to_new_before.json',
            downloader_ini: 'test/fixtures/downloader_ini/db_id_changes/old_coin_op_to_new_before.ini',
        })
        self.assertEqualFiles({
            downloader_store: 'test/fixtures/downloader_ini/db_id_changes/old_coin_op_to_new_after.json',
            downloader_ini: 'test/fixtures/downloader_ini/db_id_changes/old_coin_op_to_new_after.ini',
        }, fs.files)

    def test_n64_dev_ini___writes_downloader_ini_without_n64_dev_database(self):
        fs = test_transitions(files={
            downloader_store: 'test/fixtures/downloader_ini/db_id_removes/n64_dev_before.json',
            downloader_ini: 'test/fixtures/downloader_ini/db_id_removes/n64_dev_before.ini',
        })
        self.assertEqualFiles({
            downloader_store: 'test/fixtures/downloader_ini/db_id_removes/n64_dev_after.json',
            downloader_ini: 'test/fixtures/downloader_ini/db_id_removes/n64_dev_after.ini',
        }, fs.files)

    def test_related_mrext_all___activates_zaparoo_without_deactivating_mrext(self):
        source = DB_ID_MREXT_ALL
        target = DB_ID_ZAPAROO_MISTER
        store = local_store()
        fs = test_transitions_with_contents({
            downloader_ini: downloader_ini_with_db_ids(source),
        }, store=store)

        self.assertEqual(
            testableIni(downloader_ini_with_db_ids(source, target, ALL_DB_IDS['UPDATE_ALL_MISTER'])),
            testableIni(fs.files[downloader_ini]['content'])
        )
        self.assertEqual([target], store.get_introduced_related_database_ids())

    def test_related_mrext_tapto___activates_zaparoo_without_deactivating_mrext_tapto(self):
        source = DB_ID_MREXT_TAPTO
        target = DB_ID_ZAPAROO_MISTER
        fs = test_transitions_with_contents({
            downloader_ini: downloader_ini_with_db_ids(source),
        })

        self.assertEqual(
            testableIni(downloader_ini_with_db_ids(source, target, ALL_DB_IDS['UPDATE_ALL_MISTER'])),
            testableIni(fs.files[downloader_ini]['content'])
        )

    def test_related_sources_for_single_relationship___activate_zaparoo_once(self):
        source_1 = DB_ID_MREXT_ALL
        source_2 = DB_ID_MREXT_TAPTO
        target = DB_ID_ZAPAROO_MISTER
        fs = test_transitions_with_contents({
            downloader_ini: downloader_ini_with_db_ids(source_1, source_2),
        })

        self.assertEqual(
            testableIni(downloader_ini_with_db_ids(source_1, source_2, target, ALL_DB_IDS['UPDATE_ALL_MISTER'])),
            testableIni(fs.files[downloader_ini]['content'])
        )

    def test_without_related_source___does_not_activate_zaparoo(self):
        source = ALL_DB_IDS['JTCORES']
        target = DB_ID_ZAPAROO_MISTER
        fs = test_transitions_with_contents({
            downloader_ini: downloader_ini_with_db_ids(source),
        })

        self.assertEqual(
            testableIni(downloader_ini_with_db_ids(source, ALL_DB_IDS['UPDATE_ALL_MISTER'])),
            testableIni(fs.files[downloader_ini]['content'])
        )
        self.assertNotIn(target, fs.files[downloader_ini]['content'])

    def test_related_zaparoo_already_active___records_target_as_introduced(self):
        source = DB_ID_MREXT_ALL
        target = DB_ID_ZAPAROO_MISTER
        store = local_store()
        fs = test_transitions_with_contents({
            downloader_ini: downloader_ini_with_db_ids(source, target),
        }, store=store)

        self.assertEqual(
            testableIni(downloader_ini_with_db_ids(source, target, ALL_DB_IDS['UPDATE_ALL_MISTER'])),
            testableIni(fs.files[downloader_ini]['content'])
        )
        self.assertEqual([target], store.get_introduced_related_database_ids())

    def test_related_zaparoo_previously_introduced___does_not_activate_it_again(self):
        source = DB_ID_MREXT_ALL
        target = DB_ID_ZAPAROO_MISTER
        store = local_store()
        store.set_introduced_related_database_ids([target])
        store.mark_as_cleaned()
        fs = test_transitions_with_contents({
            downloader_ini: downloader_ini_with_db_ids(source),
        }, store=store)

        self.assertEqual(
            testableIni(downloader_ini_with_db_ids(source, ALL_DB_IDS['UPDATE_ALL_MISTER'])),
            testableIni(fs.files[downloader_ini]['content'])
        )
        self.assertEqual([target], store.get_introduced_related_database_ids())

    def test_manuals_select_all_active_and_one_manuals_db_missing___activates_the_missing_one(self):
        already_active = all_manuals_db_ids()
        missing = already_active.pop()
        store = local_store()
        store.set_ajgowans_manuals_dbs_general_selector(True)

        fs = run_manuals_transition({
            downloader_ini: downloader_ini_with_db_ids(ALL_DB_IDS['JTCORES']),
            manuals_ini: downloader_ini_with_db_ids(*already_active),
        }, store=store)

        self.assertEqual(sorted(all_manuals_db_ids()), sorted(manuals_db_ids_in(fs)))
        self.assertIn(missing, manuals_db_ids_in(fs))

    def test_manuals_select_all_inactive_and_one_manuals_db_missing___does_not_activate_it(self):
        already_active = all_manuals_db_ids()
        missing = already_active.pop()

        fs = run_manuals_transition({
            downloader_ini: downloader_ini_with_db_ids(ALL_DB_IDS['JTCORES']),
            manuals_ini: downloader_ini_with_db_ids(*already_active),
        }, store=local_store())

        self.assertEqual(sorted(already_active), sorted(manuals_db_ids_in(fs)))
        self.assertNotIn(missing, manuals_db_ids_in(fs))

    def test_manuals_select_all_active_and_no_manuals_db_active___activates_all_of_them(self):
        store = local_store()
        store.set_ajgowans_manuals_dbs_general_selector(True)

        fs = run_manuals_transition({
            downloader_ini: downloader_ini_with_db_ids(ALL_DB_IDS['JTCORES']),
        }, store=store)

        self.assertEqual(sorted(all_manuals_db_ids()), sorted(manuals_db_ids_in(fs)))

    def test_manuals_select_all_active_and_skipping_downloader___does_not_activate_anything(self):
        store = local_store()
        store.set_ajgowans_manuals_dbs_general_selector(True)

        fs = run_manuals_transition({
            downloader_ini: downloader_ini_with_db_ids(ALL_DB_IDS['JTCORES']),
        }, store=store, env={KENV_SKIP_DOWNLOADER: 'true'})

        self.assertEqual([], manuals_db_ids_in(fs))

    def test_manuals_select_all_active_and_every_manuals_db_active___emits_no_transition(self):
        store = local_store()
        store.set_ajgowans_manuals_dbs_general_selector(True)
        os_utils = SpyOsUtils()
        output = UpdateOutputTester(os_utils)

        run_manuals_transition({
            downloader_ini: downloader_ini_with_db_ids(ALL_DB_IDS['JTCORES']),
            manuals_ini: downloader_ini_with_db_ids(*all_manuals_db_ids()),
        }, store=store, update_output=output, os_utils=os_utils)

        self.assertEqual([], output.transition_calls)
        self.assertEqual([], os_utils.calls_to_sleep)

    def test_manuals_transition_event___is_emitted_with_added_db_ids_and_does_not_wait(self):
        already_active = all_manuals_db_ids()
        missing = already_active.pop()
        store = local_store()
        store.set_ajgowans_manuals_dbs_general_selector(True)
        os_utils = SpyOsUtils()
        output = UpdateOutputTester(os_utils)

        run_manuals_transition({
            downloader_ini: downloader_ini_with_db_ids(ALL_DB_IDS['JTCORES']),
            manuals_ini: downloader_ini_with_db_ids(*already_active),
        }, store=store, update_output=output, os_utils=os_utils)

        self.assertEqual([(
            'from_select_all_manuals_to_adding_new_manuals_dbs',
            {'db_ids': missing},
        )], output.transition_calls)
        self.assertEqual([], os_utils.calls_to_sleep)

    def test_related_database_relationships___has_only_zaparoo_relationship(self):
        self.assertEqual(1, len(RELATED_DATABASE_ACTIVATION_RELATIONSHIPS))
        self.assertEqual((
            DB_ID_ZAPAROO_MISTER,
            (
                DB_ID_MREXT_ALL,
                DB_ID_MREXT_TAPTO,
            ),
        ), RELATED_DATABASE_ACTIVATION_RELATIONSHIPS[0])

    def assertEqualFiles(self, expected, actual):
        actual = {filename.lower(): read_description(description) for filename, description in actual.items()}
        expected = {filename.lower(): read_json_or_text(path) for filename, path in expected.items()}
        self.assertEqual(expected, actual)


def read_description(description: Dict[str, Any]) -> Dict[str, str]:
    return description['json'] if 'json' in description else description['content'].strip()


def read_json_or_text(path: str) -> Dict[str, str]:
    p = Path(__file__).parent.parent.parent / path
    return json.loads(p.read_text()) if p.suffix == '.json' else p.read_text().strip()


def read_content(path: str) -> Dict[str, str]:
    p = Path(__file__).parent.parent.parent / path
    return {'content': p.read_text()}
