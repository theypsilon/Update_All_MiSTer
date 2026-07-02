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

from test.ui_model_test_utils import special_navigate_targets, gather_target_variables, \
    gather_formatter_declarations, gather_target_formatters, \
    gather_navigate_targets, gather_section_names, gather_all_nodes, ensure_node_is_correct
from test.update_all_service_tester import default_databases
from update_all.config_reader import Config
from update_all.databases import model_variables_by_db_id, db_ids_by_model_variables, AllDBs, all_dbs
from update_all.settings_screen_model import settings_screen_model
from update_all.ui_engine import EffectChain, Interpolator, UiApplication, UiContext, UiRuntime, UiSection, \
    UiSectionFactory, execute_ui_engine
from update_all.ui_model_utilities import gather_variable_declarations, dynamic_convert_string


class TestSettingsScreenModel(unittest.TestCase):

    def setUp(self) -> None:
        self.model = settings_screen_model()

    def test___there_are_some_navigate_nodes(self):
        nodes = [n for n in gather_all_nodes(self.model) if 'type' in n and n['type'] == 'navigate']
        self.assertGreater(len(nodes), len(self.model['items']))

    def test_all_navigate_nodes___have_no_invalid_targets(self):
        navigate_nodes = [n for n in gather_all_nodes(self.model) if 'type' in n and n['type'] == 'navigate']
        invalid_target_nodes = [n for n in navigate_nodes if n['target'] not in self.model['items'] and n['target'] not in special_navigate_targets()]

        self.assertEqual([], invalid_target_nodes)

    def test_main_variables___have_length_greater_than_5(self):
        self.assertGreater(len(gather_variable_declarations(self.model, "ua_ini")), 5)

    def test_ao_variables___have_length_greater_than_5(self):
        self.assertGreater(len(gather_variable_declarations(self.model, "ao_ini")), 5)

    def test_ao_variables___all_start_with_arcade_organizer_prefix_except_ao_toggle(self):
        ao_toggle = 'arcade_organizer'

        ao_vars = gather_variable_declarations(self.model, "ao_ini")
        with_prefix = [v for v in ao_vars if v.startswith("arcade_organizer_")]
        non_prefix = [v for v in ao_vars if v not in with_prefix]

        self.assertEqual(len(ao_vars) - 1, len(with_prefix))
        self.assertEqual([ao_toggle], non_prefix)

    def test_ao_variables_with_prefix___all_have_correct_rename_in_description(self):
        assertions = 0

        for variable, description in gather_variable_declarations(self.model, "ao_ini").items():
            if variable == "arcade_organizer":
                continue

            self.assertEqual(variable.replace("arcade_organizer_", ''), description['rename'])
            assertions += 1

        self.assertGreaterEqual(assertions, 1)

    def test_config_default_values___match_main_variables_default_values(self):
        config = Config()

        main_variables = gather_variable_declarations(self.model, "ua_ini")

        default_config_values = {variable: getattr(config, variable) for variable in main_variables if hasattr(config, variable)}
        for db_id, variable in model_variables_by_db_id().items():
            default_config_values[variable] = db_id in default_databases()

        default_model_main_values = {variable: dynamic_convert_string(description['default']) for variable, description in main_variables.items()}

        intersection = set(default_config_values) & set(default_model_main_values)

        self.assertGreaterEqual(len(intersection), 5)
        self.assertEqual({k: v for k, v in default_config_values.items() if k in intersection}, default_model_main_values)

    def test_all_database_variables_are_declared_in_the_model_except_update_all(self):
        db_variables = set(db_ids_by_model_variables())
        model_variables = set(gather_variable_declarations(self.model, 'db')) | set(gather_variable_declarations(self.model, 'separate_db'))

        self.assertGreaterEqual(len(db_variables), 5)
        self.assertEqual(db_variables - {all_dbs('').UPDATE_ALL_MISTER.db_id}, model_variables)

    def test_target_variables_are_declared_in_the_model(self):
        target_variables = gather_target_variables(self.model)
        declared_variables = set(gather_variable_declarations(self.model))

        self.assertGreaterEqual(len(target_variables), 5)
        self.assertEqual(target_variables, declared_variables)

    def test_target_formatters_are_declared_in_the_model(self):
        target_formatters = gather_target_formatters(self.model)
        declared_formatters = set(gather_formatter_declarations(self.model))

        intersection = target_formatters & declared_formatters

        self.assertGreaterEqual(len(intersection), 5)
        self.assertEqual(target_formatters, intersection)

    def test_declared_formatters_not_used_as_target_are_variables(self):
        target_formatters = gather_target_formatters(self.model)
        declared_formatters = set(gather_formatter_declarations(self.model))

        non_target_formatters = declared_formatters - target_formatters
        declared_variables = set(gather_variable_declarations(self.model))

        intersection = non_target_formatters & declared_variables

        self.assertGreaterEqual(len(intersection), 1)
        self.assertEqual(non_target_formatters, intersection)

    def test_navigate_targets_except_main_menus_are_items_or_special_navigate_targets(self):
        navigate_targets = gather_navigate_targets(self.model) | {
            'main_menu_login',
            'main_menu_account',
            'test_menu',
            'retroaccount_device_verification_result',
        }
        section_names = set(gather_section_names(self.model)) | set(special_navigate_targets())

        self.assertGreaterEqual(len(section_names), 1)
        self.assertEqual(navigate_targets, section_names)

    def test_retroaccount_link_fpga_id_entry___confirms_before_extracting_chip_id(self):
        entry = self.model['items']['retroaccount_account_menu']['entries'][2]
        action = entry['actions']['ok'][0]
        confirmation = action['false'][0]

        self.assertEqual('# Link FPGA ID', entry['title'])
        self.assertEqual('{retroaccount_device_verification_description}', entry['description'])
        self.assertEqual('condition', action['type'])
        self.assertEqual('retroaccount_device_verified', action['variable'])
        self.assertEqual('Link FPGA ID', confirmation['header'])
        self.assertEqual('confirm', confirmation['ui'])
        self.assertEqual('Back', confirmation['preselected_action'])
        self.assertIn('around 10 seconds', confirmation['text'][-1])
        self.assertEqual([
            {'type': 'extract_chip_id'},
            {'type': 'navigate', 'target': 'retroaccount_device_verification_status'},
        ], confirmation['actions'][0]['fixed'])

    def test_retroaccount_login_entry___opens_account_submenu_after_success(self):
        entry = next(entry for entry in self.model['items']['main_menu_login']['entries'] if entry.get('title') == '# Login')
        device_login = entry['actions']['ok'][0]
        main_menu_idle = self.model['items']['main_menu_account']['on_idle'][1]

        self.assertEqual('# Login', entry['title'])
        self.assertEqual('device_login', device_login['ui'])
        self.assertEqual([
            {'type': 'set_variable', 'target': 'retroaccount_open_account_after_login', 'value': 'true'},
            {'type': 'apply_theme'},
            {'type': 'navigate', 'target': 'main_menu_account'},
        ], device_login['success_effects'])
        self.assertEqual('retroaccount_open_account_after_login', main_menu_idle['variable'])
        self.assertEqual([
            {'type': 'set_variable', 'target': 'retroaccount_open_account_after_login', 'value': 'false'},
            {'type': 'navigate', 'target': 'retroaccount_account_menu'},
        ], main_menu_idle['true'])

    def test_retroaccount_account_entry___keeps_static_description(self):
        entry = next(entry for entry in self.model['items']['main_menu_account']['entries'] if entry.get('title') == '# Account')

        self.assertEqual('From RetroAccount. {retroaccount_checking}', entry['description'])


    def test_retroaccount_linked_fpga_id_entry___explains_that_fpga_id_is_linked(self):
        entry = self.model['items']['retroaccount_account_menu']['entries'][2]
        message = entry['actions']['ok'][0]['true'][0]

        self.assertEqual('message', message['ui'])
        self.assertEqual('FPGA ID Linked', message['header'])
        self.assertIn('FPGA ID is linked', message['text'][0])
        self.assertEqual('{retroaccount_verified_chip_id_message}', message['text'][1])

    def test_retroaccount_manage_account_entry___shows_device_label(self):
        entry = self.model['items']['retroaccount_account_menu']['entries'][3]
        message = entry['actions']['ok'][0]

        self.assertEqual('# Manage Your Account', entry['title'])
        self.assertEqual('Manage Your Account', message['header'])
        self.assertEqual('{device_label:device_label_message}', message['text'][0])

    def test_mrext_entry___when_enabling_with_zaparoo_disabled___asks_to_enable_zaparoo(self):
        app = self._execute_tools_mrext_action('false', 'false')

        self.assertEqual('true', app.ui.get_value('mrext/all'))
        self.assertEqual('false', app.ui.get_value('ZaparooProject/Zaparoo_MiSTer'))
        self.assertEqual('confirm', app.last_confirm['ui'])
        self.assertEqual('Activate Zaparoo?', app.last_confirm['header'])
        self.assertEqual('Yes', app.last_confirm['preselected_action'])

    def test_mrext_zaparoo_confirmation_yes___enables_zaparoo_and_asks_about_active_frontend(self):
        app = self._execute_tools_mrext_action('false', 'false', confirm_action_title='Yes')

        self.assertEqual('true', app.ui.get_value('mrext/all'))
        self.assertEqual('true', app.ui.get_value('ZaparooProject/Zaparoo_MiSTer'))
        self.assertEqual('false', app.ui.get_value('zaparoo_frontend_active'))
        self.assertEqual('confirm', app.last_confirm['ui'])
        self.assertEqual('Zaparoo Frontend', app.last_confirm['header'])
        self.assertEqual([
            'Do you want the Zaparoo frontend',
            'to be active after being installed?',
        ], app.last_confirm['text'])
        self.assertEqual('Yes', app.last_confirm['preselected_action'])

    def test_mrext_zaparoo_confirmation_yes_and_active_frontend_yes___sets_zaparoo_options(self):
        app = self._execute_tools_mrext_action('false', 'false', confirm_action_title=['Yes', 'Yes'])

        self.assertEqual('true', app.ui.get_value('mrext/all'))
        self.assertEqual('true', app.ui.get_value('ZaparooProject/Zaparoo_MiSTer'))
        self.assertEqual('true', app.ui.get_value('zaparoo_frontend_active'))

    def test_mrext_zaparoo_confirmation_yes_and_active_frontend_no___keeps_zaparoo_frontend_disabled(self):
        app = self._execute_tools_mrext_action('false', 'false', confirm_action_title=['Yes', 'No'])

        self.assertEqual('true', app.ui.get_value('mrext/all'))
        self.assertEqual('true', app.ui.get_value('ZaparooProject/Zaparoo_MiSTer'))
        self.assertEqual('false', app.ui.get_value('zaparoo_frontend_active'))

    def test_mrext_zaparoo_confirmation_yes___when_zaparoo_frontend_is_active___does_not_ask_about_it(self):
        app = self._execute_tools_mrext_action(
            'false',
            'false',
            confirm_action_title='Yes',
            zaparoo_frontend_active='true',
        )

        self.assertEqual('true', app.ui.get_value('mrext/all'))
        self.assertEqual('true', app.ui.get_value('ZaparooProject/Zaparoo_MiSTer'))
        self.assertEqual('true', app.ui.get_value('zaparoo_frontend_active'))
        self.assertEqual(1, len(app.confirms))
        self.assertEqual('Activate Zaparoo?', app.last_confirm['header'])

    def test_mrext_entry___when_disabling_mrext___does_not_ask_to_enable_zaparoo(self):
        app = self._execute_tools_mrext_action('true', 'false')

        self.assertIsNone(app.last_confirm)
        self.assertEqual('false', app.ui.get_value('mrext/all'))
        self.assertEqual('false', app.ui.get_value('ZaparooProject/Zaparoo_MiSTer'))

    def test_mrext_entry___when_zaparoo_is_already_enabled___does_not_ask_to_enable_zaparoo(self):
        app = self._execute_tools_mrext_action('false', 'true')

        self.assertIsNone(app.last_confirm)
        self.assertEqual('true', app.ui.get_value('mrext/all'))
        self.assertEqual('true', app.ui.get_value('ZaparooProject/Zaparoo_MiSTer'))

    def test_zaparoo_tools_entry___opens_zaparoo_submenu(self):
        entry = next(entry for entry in self.model['items']['tools_and_scripts_menu']['entries'] if entry['title'] == '# Zaparoo')

        self.assertEqual('{ZaparooProject/Zaparoo_MiSTer:enabled} NFC Launcher & Zaparoo Frontend', entry['description'])
        self.assertEqual([{'type': 'navigate', 'target': 'zaparoo_menu'}], entry['actions']['ok'])

    def test_retroachievements_other_cores_entry___is_second_and_uses_setup_effect(self):
        other_cores = self.model['items']['other_cores_menu']
        entry = other_cores['entries'][1]
        action = entry['actions']['ok']

        self.assertEqual('# RetroAchievements Cores', entry['title'])
        self.assertEqual('theypsilon/RetroAchievementsDB_MiSTer', list(other_cores['variables'])[1])
        self.assertEqual({'type': 'retroachievements_db_toggle'}, action[0])
        self.assertEqual('condition', action[1]['type'])
        self.assertEqual('retroachievements_cfg_status', action[1]['variable'])
        self.assertEqual([], action[1]['ok'])
        self.assertEqual('RetroAchievements Setup', action[1]['installed'][0]['header'])
        self.assertEqual('RetroAchievements Setup', action[1]['missing_credentials'][0]['header'])
        self.assertEqual(action, entry['actions']['toggle'])

    def test_zaparoo_submenu___has_enabled_and_frontend_options(self):
        entries = self.model['items']['zaparoo_menu']['entries']

        self.assertEqual('# Zaparoo Database', entries[0]['title'])
        self.assertEqual('{ZaparooProject/Zaparoo_MiSTer:enabled}', entries[0]['description'])
        self.assertEqual('{zaparoo_frontend_active:yesno}', entries[1]['description'])
        self.assertEqual(2, len(entries))

    def test_zaparoo_database_entry___when_enabling___asks_about_active_frontend(self):
        app = self._execute_tools_zaparoo_action('false', 'false')

        self.assertEqual('true', app.ui.get_value('ZaparooProject/Zaparoo_MiSTer'))
        self.assertEqual('false', app.ui.get_value('zaparoo_frontend_active'))
        self.assertEqual('confirm', app.last_confirm['ui'])
        self.assertEqual('Zaparoo Frontend', app.last_confirm['header'])
        self.assertEqual([
            'Do you want the Zaparoo frontend',
            'to be active after being installed?',
        ], app.last_confirm['text'])
        self.assertEqual('Yes', app.last_confirm['preselected_action'])

    def test_zaparoo_frontend_confirmation_yes___sets_zaparoo_frontend_active(self):
        app = self._execute_tools_zaparoo_action('false', 'false', confirm_action_title='Yes')

        self.assertEqual('true', app.ui.get_value('ZaparooProject/Zaparoo_MiSTer'))
        self.assertEqual('true', app.ui.get_value('zaparoo_frontend_active'))

    def test_zaparoo_frontend_confirmation_no___keeps_zaparoo_frontend_disabled(self):
        app = self._execute_tools_zaparoo_action('false', 'false', confirm_action_title='No')

        self.assertEqual('true', app.ui.get_value('ZaparooProject/Zaparoo_MiSTer'))
        self.assertEqual('false', app.ui.get_value('zaparoo_frontend_active'))

    def test_zaparoo_database_entry___when_enabling_with_frontend_active___does_not_prompt(self):
        app = self._execute_tools_zaparoo_action('false', 'true')

        self.assertIsNone(app.last_confirm)
        self.assertEqual('true', app.ui.get_value('ZaparooProject/Zaparoo_MiSTer'))
        self.assertEqual('true', app.ui.get_value('zaparoo_frontend_active'))

    def test_zaparoo_database_entry___when_disabling___keeps_active_frontend_without_prompting(self):
        app = self._execute_tools_zaparoo_action('true', 'true')

        self.assertIsNone(app.last_confirm)
        self.assertEqual('false', app.ui.get_value('ZaparooProject/Zaparoo_MiSTer'))
        self.assertEqual('true', app.ui.get_value('zaparoo_frontend_active'))

    def test_zaparoo_frontend_entry___rotates_frontend_active_preference(self):
        app = self._execute_tools_action(
            self._zaparoo_frontend_action_chain(),
            {
                'ZaparooProject/Zaparoo_MiSTer': 'true',
                'zaparoo_frontend_active': 'false',
            },
            entrypoint='zaparoo_menu',
            initial_history=['tools_and_scripts_menu'],
        )

        self.assertEqual('true', app.ui.get_value('zaparoo_frontend_active'))
        self.assertEqual('true', app.ui.get_value('ZaparooProject/Zaparoo_MiSTer'))

    def test_zaparoo_frontend_entry___when_active___rotates_frontend_inactive(self):
        app = self._execute_tools_zaparoo_frontend_action('true', 'true')

        self.assertEqual('false', app.ui.get_value('zaparoo_frontend_active'))
        self.assertEqual('true', app.ui.get_value('ZaparooProject/Zaparoo_MiSTer'))

    def test_zaparoo_frontend_entry___when_enabling_with_zaparoo_database_disabled___asks_to_enable_database(self):
        app = self._execute_tools_zaparoo_frontend_action('false', 'false')

        self.assertEqual('false', app.ui.get_value('ZaparooProject/Zaparoo_MiSTer'))
        self.assertEqual('false', app.ui.get_value('zaparoo_frontend_active'))
        self.assertEqual('confirm', app.last_confirm['ui'])
        self.assertEqual('Enable Zaparoo DB?', app.last_confirm['header'])
        self.assertEqual([
            'To enable Zaparoo Frontend,',
            'you also need to enable the Zaparoo DB.',
            'Do you want to enable it?',
        ], app.last_confirm['text'])
        self.assertEqual('Yes', app.last_confirm['preselected_action'])

    def test_zaparoo_frontend_entry___database_confirmation_yes___enables_database_and_frontend(self):
        app = self._execute_tools_zaparoo_frontend_action('false', 'false', confirm_action_title='Yes')

        self.assertEqual('true', app.ui.get_value('ZaparooProject/Zaparoo_MiSTer'))
        self.assertEqual('true', app.ui.get_value('zaparoo_frontend_active'))

    def test_zaparoo_frontend_entry___database_confirmation_no___keeps_database_and_frontend_disabled(self):
        app = self._execute_tools_zaparoo_frontend_action('false', 'false', confirm_action_title='No')

        self.assertEqual('false', app.ui.get_value('ZaparooProject/Zaparoo_MiSTer'))
        self.assertEqual('false', app.ui.get_value('zaparoo_frontend_active'))

    def _mrext_action_chain(self):
        entry = next(entry for entry in self.model['items']['tools_and_scripts_menu']['entries'] if 'MiSTer Extensions' in entry['title'])
        return entry['actions']['ok']

    def _zaparoo_action_chain(self):
        return self.model['items']['zaparoo_menu']['entries'][0]['actions']['ok']

    def _zaparoo_frontend_action_chain(self):
        return self.model['items']['zaparoo_menu']['entries'][1]['actions']['ok']

    def _execute_tools_mrext_action(
            self,
            mrext_value,
            zaparoo_value,
            confirm_action_title=None,
            zaparoo_frontend_active='false',
    ):
        return self._execute_tools_action(self._mrext_action_chain(), {
            'mrext/all': mrext_value,
            'ZaparooProject/Zaparoo_MiSTer': zaparoo_value,
            'zaparoo_frontend_active': zaparoo_frontend_active,
        }, confirm_action_title)

    def _execute_tools_zaparoo_action(self, zaparoo_value, zaparoo_frontend_active, confirm_action_title=None):
        return self._execute_tools_action(self._zaparoo_action_chain(), {
            'ZaparooProject/Zaparoo_MiSTer': zaparoo_value,
            'zaparoo_frontend_active': zaparoo_frontend_active,
        }, confirm_action_title, entrypoint='zaparoo_menu', initial_history=['tools_and_scripts_menu'])

    def _execute_tools_zaparoo_frontend_action(self, zaparoo_value, zaparoo_frontend_active, confirm_action_title=None):
        return self._execute_tools_action(self._zaparoo_frontend_action_chain(), {
            'ZaparooProject/Zaparoo_MiSTer': zaparoo_value,
            'zaparoo_frontend_active': zaparoo_frontend_active,
        }, confirm_action_title, entrypoint='zaparoo_menu', initial_history=['tools_and_scripts_menu'])

    def _execute_tools_action(self, action_chain, initial_values, confirm_action_title=None, entrypoint='tools_and_scripts_menu', initial_history=None):
        app = ToolsMenuActionApplication(
            action_chain,
            initial_values,
            confirm_action_title,
        )
        execute_ui_engine(entrypoint, self.model, app, RuntimeStub(), initial_history=initial_history)
        return app

    def test_retroaccount_device_verification_result___attaches_chip_id_before_displaying_message(self):
        screen = self.model['items']['retroaccount_device_verification_result']

        self.assertEqual('message', screen['ui'])
        self.assertEqual('Link FPGA ID', screen['header'])
        self.assertEqual([
            '{retroaccount_device_verification_message}',
            '{retroaccount_verified_chip_id_message}',
        ], screen['text'])
        self.assertEqual([{'type': 'retroaccount_attach_chip_id_to_device'}], screen['on_idle'])

    def test_retroaccount_device_verification_status___displays_message_without_attaching_again(self):
        screen = self.model['items']['retroaccount_device_verification_status']

        self.assertEqual('message', screen['ui'])
        self.assertEqual('Link FPGA ID', screen['header'])
        self.assertEqual([
            '{retroaccount_device_verification_message}',
            '{retroaccount_verified_chip_id_message}',
        ], screen['text'])
        self.assertNotIn('on_idle', screen)

    def test_all_nodes_are_correct(self):
        nodes = [ensure_node_is_correct(n) for n in gather_all_nodes(self.model)]
        self.assertGreaterEqual(len(nodes), 5)

    def test_all_db_variables_have_boolean_values(self):
        db_variables = gather_variable_declarations(self.model, "db")
        self.assertGreaterEqual(len(db_variables), 5)

        values = set()
        for variable, description in db_variables.items():
            values.add(description['default'])
            self.assertEqual(2, len(description['values']), variable)
            for v in description['values']:
                values.add(v)

        self.assertEqual({'true', 'false'}, values)


class ToolsMenuActionApplication(UiApplication):
    def __init__(self, action_chain, initial_values, confirm_action_title=None):
        self.action_chain = action_chain
        self.initial_values = initial_values
        self.confirm_action_titles = self._confirm_action_titles(confirm_action_title)
        self.ui = None
        self.confirms = []
        self.last_confirm = None

    def initialize_ui(self, ui: UiContext) -> UiSectionFactory:
        self.ui = ui
        for key, value in self.initial_values.items():
            ui.set_value(key, value)
        return ToolsMenuSectionFactory(self)

    def next_confirm_action_title(self):
        if len(self.confirm_action_titles) == 0:
            return None

        return self.confirm_action_titles.pop(0)

    @staticmethod
    def _confirm_action_titles(confirm_action_title):
        if confirm_action_title is None:
            return []

        if isinstance(confirm_action_title, list):
            return list(confirm_action_title)

        return [confirm_action_title]


class RuntimeStub(UiRuntime):
    def initialize_runtime(self, cb):
        cb()

    def update(self) -> None:
        pass

    def interrupt(self) -> None:
        pass

    def resume(self) -> None:
        pass


class ToolsMenuSectionFactory(UiSectionFactory):
    def __init__(self, app):
        self.app = app

    def create_ui_section(self, ui_type: str, data: dict, _interpolator: Interpolator) -> UiSection:
        if ui_type == 'menu':
            return MenuActionSection(self.app.action_chain)

        if ui_type == 'confirm':
            self.app.confirms.append(data)
            self.app.last_confirm = data
            return ConfirmActionSection(data, self.app.next_confirm_action_title())

        raise ValueError(f'Unexpected ui_type: {ui_type}')


class MenuActionSection(UiSection):
    def __init__(self, action_chain):
        self.action_chain = action_chain
        self.processed = False

    def process_key(self):
        if self.processed:
            return EffectChain([{'type': 'navigate', 'target': 'exit_and_run'}])

        self.processed = True
        return EffectChain(self.action_chain)

    def reset(self) -> None:
        pass

    def clear(self) -> None:
        pass


class ConfirmActionSection(UiSection):
    def __init__(self, data, action_title):
        self.data = data
        self.action_title = action_title

    def process_key(self):
        if self.action_title is None:
            return EffectChain([{'type': 'navigate', 'target': 'exit_and_run'}])

        action = next(action for action in self.data['actions'] if action['title'] == self.action_title)
        return EffectChain(action['fixed'])

    def reset(self) -> None:
        pass

    def clear(self) -> None:
        pass
