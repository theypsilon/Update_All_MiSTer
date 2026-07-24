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
    gather_navigate_targets, gather_section_names, gather_all_nodes, ensure_node_is_correct, \
    gather_effect_chains, is_terminal_effect
from test.update_all_service_tester import default_databases
from update_all.config_reader import Config
from update_all.databases import model_variables_by_db_id, db_ids_by_model_variables, AllDBs, all_dbs
from update_all.settings_screen_model import settings_screen_model, uninstall_db_action, uninstall_db_action_for_id, \
    uninstall_db_action_manuals
from update_all.ui_engine import EffectChain, Interpolator, UiApplication, UiContext, UiRuntime, UiSection, \
    UiSectionFactory, execute_ui_engine
from update_all.mister_ini_edits import parse_mister_ini_add, parse_mister_ini_del
from update_all.ui_model_utilities import gather_variable_declarations, dynamic_convert_string, expand_type, \
    gather_effects_by_type


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
        # <db_id>_installed variables are seeded at runtime from the downloader
        # fingerprints file, so they are intentionally not declared in the model.
        target_variables = {v for v in gather_target_variables(self.model) if not v.endswith('_installed')}
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

    def test_exit_and_run___with_unsaved_changes___offers_save_or_ignore_as_menu_entries(self):
        for menu in ('main_menu_login', 'main_menu_account'):
            entry = self._entry(menu, 'EXIT and RUN UPDATE ALL')
            condition = entry['actions']['ok'][1]
            dialog = condition['true'][0]

            self.assertEqual('', entry['description'])
            self.assertEqual('needs_save', condition['variable'])
            self.assertEqual('menu', dialog['ui'])
            self.assertEqual('Unsaved Changes', dialog['header'])
            self.assertEqual([
                'SAVE AND RUN',
                'IGNORE CHANGES AND RUN',
            ], [option['title'] for option in dialog['entries']])
            self.assertEqual([
                {'type': 'save'},
                {'type': 'navigate', 'target': 'exit_and_run'},
            ], dialog['entries'][0]['actions']['ok'])
            self.assertEqual([
                {'type': 'prepare_exit_without_save'},
                {'type': 'navigate', 'target': 'exit_and_run'},
            ], dialog['entries'][1]['actions']['ok'])
            self.assertEqual([
                {'type': 'navigate', 'target': 'exit_and_run'},
            ], condition['false'])

    def _entry(self, menu, title):
        for entry in self.model['items'][menu]['entries']:
            if entry and entry.get('title') == title:
                return entry
        raise AssertionError(f'Entry "{title}" not found in menu "{menu}".')

    def _assert_uninstall_action(self, menu, title, variable, db_id, uninstall_title):
        entry = self._entry(menu, title)
        action = entry['actions'].get('uninstall')
        self.assertIsNotNone(action, f'{menu}: {title}')
        self.assertEqual(f'{db_id}_installed', action['if'], f'{menu}: {title}')

        ui = action['chain'][0]['actions'][0]['fixed'][0]
        self.assertEqual('uninstall_db', ui['ui'], f'{menu}: {title}')
        self.assertEqual([db_id], ui['db_ids'], f'{menu}: {title}')
        self.assertEqual(uninstall_title, ui['title'], f'{menu}: {title}')
        self.assertEqual(
            [
                {'type': 'set_variable', 'target': variable, 'value': 'false'},
                {'type': 'set_variable', 'target': f'{db_id}_installed', 'value': 'false'},
            ],
            ui['on_success'][:2],
            f'{menu}: {title}',
        )

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
        self.assertEqual('mister_ini_add', action[1]['type'])
        self.assertEqual('theypsilon/RetroAchievementsDB_MiSTer', action[1]['variable'])
        self.assertEqual({'RA_*': {'main': 'MiSTer_RA'}}, action[1]['target'])
        self.assertEqual('condition', action[2]['type'])
        self.assertEqual('retroachievements_cfg_status', action[2]['variable'])
        self.assertEqual([], action[2]['ok'])
        self.assertEqual('RetroAchievements Setup', action[2]['installed'][0]['header'])
        self.assertEqual('RetroAchievements Setup', action[2]['missing_credentials'][0]['header'])
        self.assertEqual(action, entry['actions']['toggle'])

    def test_other_cores_menu___has_select_info_back_buttons(self):
        menu = dict(self.model['items']['other_cores_menu'])
        expand_type(menu, self.model['base_types'])

        self.assertEqual('ui', menu['type'])
        self.assertEqual([
            {'title': 'Select', 'type': 'symbol', 'symbol': 'ok'},
            {'title': 'Info', 'type': 'symbol', 'symbol': 'info'},
            {'title': 'Back', 'type': 'fixed', 'fixed': [{'type': 'navigate', 'target': 'back'}]},
        ], menu['actions'])

    def test_other_cores_db_entries___have_conditional_uninstall_action(self):
        expected = {
            '# Coin-Op Collection': ('coin_op_collection_downloader', 'Coin-OpCollection/Distribution-MiSTerFPGA'),
            '# RetroAchievements Cores': ('theypsilon/RetroAchievementsDB_MiSTer', 'theypsilon/RetroAchievementsDB_MiSTer'),
            '# Physical CD Support': ('MultiDatabases/physical-disc', 'MultiDatabases/physical-disc'),
            '# Unofficial Distribution': ('unofficial_updater', 'theypsilon_unofficial_distribution'),
            '# Arcade Offset': ('arcade_offset_downloader', 'arcade_offset_folder'),
            '# LLAPI Forks Folder': ('llapi_updater', 'llapi_folder'),
            '# Y/C Builds': ('MikeS11/YC_Builds-MiSTer', 'MikeS11/YC_Builds-MiSTer'),
            "# agg23's MiSTer Cores": ('agg23_db', 'agg23_db'),
            '# Paprium MegaDrive': ('MultiDatabases/paprium', 'MultiDatabases/paprium'),
            '# MMS2 GB Core': ('MultiDatabases/mms2-gb', 'MultiDatabases/mms2-gb'),
            '# Alt Cores': ('ajgowans/alt-cores', 'ajgowans/alt-cores'),
            '# Dual RAM Console Cores': ('TheJesusFish/Dual-Ram-Console-Cores', 'TheJesusFish/Dual-Ram-Console-Cores'),
            '# MiSTer Frontier': ('MiSTerOrganize/MiSTer_Frontier', 'MiSTerOrganize/MiSTer_Frontier'),
            '# DreamSTer': ('MultiDatabases/dreamster', 'MultiDatabases/dreamster'),
            '# Sonic Mania MiSTer': ('MultiDatabases/sonic-mania', 'MultiDatabases/sonic-mania'),
            '# MiSTer Duke3D': ('MultiDatabases/duke3d', 'MultiDatabases/duke3d'),
            '# MiSTer Quake': ('MultiDatabases/mister-quake', 'MultiDatabases/mister-quake'),
            '# MegaVGMDrive': ('MultiDatabases/megavgmdrive', 'MultiDatabases/megavgmdrive'),
        }

        # Entries that write to MiSTer.ini on install must undo those edits on uninstall.
        ini_del_targets = {
            '# RetroAchievements Cores': {'RA_*': {'main': 'MiSTer_RA'}},
            '# Physical CD Support': {'CD-*': {'main': 'MiSTer_Physical-CD'}},
            '# Sonic Mania MiSTer': {
                'Sonic Mania': {'main': 'MiSTer_SonicMania'},
                'Sonic Mania (4:3)': {'main': 'MiSTer_SonicMania'},
            },
            '# MiSTer Duke3D': {
                'DUKE3D': {'main': 'Mister_duke3d', 'vga_scaler': '0'},
                'Mister_duke3d': {'main': 'Mister_duke3d', 'vga_scaler': '0'},
            },
            '# MiSTer Quake': {
                'Quake': {'main': 'MiSTer_Quake', 'vga_scaler': '0'},
                'MiSTer_Quake': {'main': 'MiSTer_Quake', 'vga_scaler': '0'},
            },
        }

        for title, (variable, db_id) in expected.items():
            entry = self._entry('other_cores_menu', title)
            action = entry['actions'].get('uninstall')
            self.assertIsNotNone(action, title)
            self.assertEqual(f'{db_id}_installed', action['if'], title)

            confirm = action['chain'][0]
            self.assertEqual('confirm', confirm['ui'], title)
            self.assertEqual('No', confirm['preselected_action'], title)

            yes, no = confirm['actions']
            ui = yes['fixed'][0]
            self.assertEqual('uninstall_db', ui['ui'], title)
            self.assertEqual([db_id], ui['db_ids'], title)
            self.assertEqual(title.lstrip('# '), ui['title'], title)

            expected_on_success = [
                {'type': 'set_variable', 'target': variable, 'value': 'false'},
                {'type': 'set_variable', 'target': f'{db_id}_installed', 'value': 'false'},
            ]
            if title in ini_del_targets:
                expected_on_success.append(
                    {'type': 'mister_ini_del', 'immediate': True, 'variable': variable, 'target': ini_del_targets[title]},
                )
            expected_on_success.append({'type': 'navigate', 'target': 'back'})

            self.assertEqual(expected_on_success, ui['on_success'], title)
            self.assertEqual([{'type': 'navigate', 'target': 'back'}], no['fixed'], title)

    def test_primary_tools_and_extra_content_db_entries___have_explicit_uninstall_actions(self):
        expected = [
            ('jtcores_menu', '# JTCORES Enabled', 'jotego_updater', 'jtcores', 'JTCORES for MiSTer'),
            ('arcade_roms_database_menu', '# Arcade ROMs Database Enabled', 'arcade_roms_db_downloader',
             'arcade_roms_db', 'Arcade ROMs Database'),
            ('names_txt_menu', '# Arcade Names TXT', 'arcade_names_txt', 'arcade_names_txt', 'Arcade Names TXT'),
            ('tools_and_scripts_menu', '# MiSTer Extensions (wizzo)', 'mrext/all', 'mrext/all',
             'MiSTer Extensions'),
            ('tools_and_scripts_menu', '# MiSTer Super Attract Mode', 'mistersam_files_downloader',
             'MiSTer_SAM_files', 'MiSTer Super Attract Mode'),
            ('tools_and_scripts_menu', '# Anime0t4ku MiSTer Scripts', 'anime0t4ku_mister_scripts',
             'anime0t4ku_mister_scripts', 'Anime0t4ku MiSTer Scripts'),
            ('tools_and_scripts_menu', '# tty2oled Add-on script', 'tty2oled_files_downloader',
             'tty2oled_files', 'tty2oled Add-on script'),
            ('tools_and_scripts_menu', '# i2c2oled Add-on script', 'i2c2oled_files_downloader',
             'i2c2oled_files', 'i2c2oled Add-on script'),
            ('tools_and_scripts_menu', '# RetroSpy utility', 'retrospy/retrospy-MiSTer',
             'retrospy/retrospy-MiSTer', 'RetroSpy utility'),
            ('zaparoo_menu', '# Zaparoo Database', 'ZaparooProject/Zaparoo_MiSTer',
             'ZaparooProject/Zaparoo_MiSTer', 'Zaparoo'),
            ('extra_content_menu', '# BIOS Database', 'bios_getter', 'bios_db', 'BIOS Database'),
            ('extra_content_menu', '# Dinierto GBA Borders', 'Dinierto/MiSTer-GBA-Borders',
             'Dinierto/MiSTer-GBA-Borders', 'Dinierto GBA Borders'),
            ('extra_content_menu', '# Uberyoji Boot ROMs', 'uberyoji_mister_boot_roms_mgl',
             'uberyoji_mister_boot_roms_mgl', 'Uberyoji Boot ROMs'),
            ('rannysnice_wallpapers_menu', '# Wallpapers Enabled', 'Ranny-Snice/Ranny-Snice-Wallpapers',
             'Ranny-Snice/Ranny-Snice-Wallpapers', 'Ranny Snice Wallpapers'),
            ('anime0t4ku_wallpapers_menu', '# Unrestricted Anime0t4ku 16:9 Wallpapers',
             'anime0t4ku_wallpapers', 'anime0t4ku_wallpapers', 'Unrestricted Anime0t4ku Wallpapers'),
            ('anime0t4ku_wallpapers_menu', '# PCN Challenge 16:9 Wallpapers',
             'pcn_challenge_wallpapers', 'pcn_challenge_wallpapers', 'PCN Challenge Wallpapers'),
        ]

        for args in expected:
            self._assert_uninstall_action(*args)

    def test_distribution_and_names_txt_entries___do_not_offer_uninstall(self):
        excluded = [
            ('main_menu_login', '# Main Distribution'),
            ('main_menu_account', '# Main Distribution'),
            ('main_distribution_menu', '# Distribution Enabled'),
            ('tools_and_scripts_menu', '# Names TXT'),
            ('names_txt_menu', '# Names TXT'),
        ]

        for menu, title in excluded:
            self.assertNotIn('uninstall', self._entry(menu, title)['actions'], f'{menu}: {title}')

    def test_manuals_select_all_entry___has_uninstall_all_for_every_manual_database(self):
        manual_db_ids = list(gather_variable_declarations(self.model, 'manuals'))
        entry = self.model['items']['game_manuals_en_db_menu']['entries'][0]
        action = entry['actions']['uninstall_all']

        self.assertEqual('ajgowans_manuals_dbs_installed', action['if'])
        ui = action['chain'][0]['actions'][0]['fixed'][0]
        self.assertEqual(manual_db_ids, ui['db_ids'])
        self.assertEqual('All Manuals Databases', ui['title'])
        self.assertEqual(
            {'type': 'select_all_ajgowans_manuals_dbs', 'action': 'unapply'},
            ui['on_success'][-2],
        )

    def test_each_manual_database_entry___has_its_own_uninstall_action(self):
        manual_variables = gather_variable_declarations(self.model, 'manuals')
        entries = self.model['items']['game_manuals_en_db_menu']['entries']
        matched_variables = set()

        for entry in entries:
            if not entry:
                continue

            variables = [
                variable for variable in manual_variables
                if f'{{{variable}:' in entry.get('description', '')
            ]
            if not variables:
                continue

            self.assertEqual(1, len(variables), entry['title'])
            variable = variables[0]
            matched_variables.add(variable)
            self._assert_uninstall_action(
                'game_manuals_en_db_menu',
                entry['title'],
                variable,
                variable,
                f"{entry['title'].lstrip('# ')} Manuals",
            )

            ui = entry['actions']['uninstall']['chain'][0]['actions'][0]['fixed'][0]
            self.assertIn(
                {'type': 'select_all_ajgowans_manuals_dbs', 'action': 'unapply'},
                ui['on_success'],
                entry['title'],
            )

        self.assertEqual(set(manual_variables), matched_variables)

    def test_entries_that_lead_to_a_menu___do_not_offer_uninstall(self):
        submenu_targets = set(self.model['items'])
        for menu, item in self.model['items'].items():
            for entry in item.get('entries', []):
                if not entry:
                    continue
                targets = _navigate_targets(entry.get('actions', {}).get('ok', []))
                if targets & submenu_targets:
                    self.assertNotIn(
                        'uninstall',
                        entry['actions'],
                        f"{menu}: {entry.get('title')} -> {sorted(targets & submenu_targets)}",
                    )

    def test_zaparoo_database_toggle_uninstall___disables_frontend_and_immediately_removes_its_ini_sections(self):
        expected_cleanup = [
            {'type': 'set_variable', 'target': 'zaparoo_frontend_active', 'value': 'false'},
            {
                'type': 'mister_ini_del',
                'immediate': True,
                'variable': 'zaparoo_frontend_active',
                'target': {
                    'mister': {'main': 'zaparoo/MiSTer_Zaparoo'},
                    'menu': {'main': 'zaparoo/MiSTer_Zaparoo'},
                },
            },
        ]

        action = self._entry('zaparoo_menu', '# Zaparoo Database')['actions']['uninstall']
        ui = action['chain'][0]['actions'][0]['fixed'][0]
        self.assertEqual(expected_cleanup, ui['on_success'][2:-1])

    def test_uninstall_db_action___with_on_success_effects___inserts_them_right_before_navigate_back(self):
        extra = [{'type': 'set_variable', 'target': 'some_flag', 'value': 'true'}]

        action = uninstall_db_action('some_var', 'some/db', 'Some DB', on_success=extra)

        ui = action['chain'][0]['actions'][0]['fixed'][0]
        self.assertEqual([
            {'type': 'set_variable', 'target': 'some_var', 'value': 'false'},
            {'type': 'set_variable', 'target': 'some/db_installed', 'value': 'false'},
            {'type': 'set_variable', 'target': 'some_flag', 'value': 'true'},
            {'type': 'navigate', 'target': 'back'},
        ], ui['on_success'])

    def test_uninstall_db_action___without_on_success_effects___only_resets_variables_then_navigates_back(self):
        action = uninstall_db_action('some_var', 'some/db', 'Some DB')

        ui = action['chain'][0]['actions'][0]['fixed'][0]
        self.assertEqual([
            {'type': 'set_variable', 'target': 'some_var', 'value': 'false'},
            {'type': 'set_variable', 'target': 'some/db_installed', 'value': 'false'},
            {'type': 'navigate', 'target': 'back'},
        ], ui['on_success'])

    def test_uninstall_db_action_for_id___uses_db_id_as_the_variable(self):
        extra = [{'type': 'set_variable', 'target': 'some_flag', 'value': 'true'}]

        self.assertEqual(
            uninstall_db_action('some/db', 'some/db', 'Some DB', on_success=extra),
            uninstall_db_action_for_id('some/db', 'Some DB', on_success=extra),
        )

    def test_uninstall_db_action_manuals___resets_each_database_and_aggregate_state(self):
        db_ids = ['manuals/one', 'manuals/two']
        extra = [{'type': 'set_variable', 'target': 'some_flag', 'value': 'true'}]

        action = uninstall_db_action_manuals('all_manuals', db_ids, 'Game Manuals', on_success=extra)

        self.assertEqual('all_manuals', action['if'])
        confirm = action['chain'][0]
        self.assertEqual([
            'This will uninstall 2 manuals databases.',
            ' ',
            'All their contents will be deleted from your system.',
            'Do you really want to uninstall them?',
        ], confirm['text'])

        ui = confirm['actions'][0]['fixed'][0]
        self.assertEqual(db_ids, ui['db_ids'])
        self.assertEqual([
            {'type': 'set_variable', 'target': 'manuals/one', 'value': 'false'},
            {'type': 'set_variable', 'target': 'manuals/two', 'value': 'false'},
            {'type': 'set_variable', 'target': 'manuals/one_installed', 'value': 'false'},
            {'type': 'set_variable', 'target': 'manuals/two_installed', 'value': 'false'},
            {'type': 'set_variable', 'target': 'all_manuals', 'value': 'false'},
            {'type': 'set_variable', 'target': 'some_flag', 'value': 'true'},
            {'type': 'navigate', 'target': 'back'},
        ], ui['on_success'])

    def test_other_cores_entries___are_in_expected_order(self):
        entries = self.model['items']['other_cores_menu']['entries']

        self.assertEqual([
            '# Coin-Op Collection',
            '# RetroAchievements Cores',
            '# Physical CD Support',
            '# Unofficial Distribution',
            '# Arcade Offset',
            '# LLAPI Forks Folder',
            '# Y/C Builds',
            "# agg23's MiSTer Cores",
            '# Paprium MegaDrive',
            '# MMS2 GB Core',
            '# Alt Cores',
            '# Dual RAM Console Cores',
            '# MiSTer Frontier',
            '# DreamSTer',
            '# Sonic Mania MiSTer',
            '# MiSTer Duke3D',
            '# MiSTer Quake',
            '# MegaVGMDrive',
        ], [entry.get('title') for entry in entries])

    def test_dreamster_entry___toggles_without_message_and_exposes_requirements_as_info(self):
        app = self._execute_multidatabase_action('# DreamSTer', 'MultiDatabases/dreamster', 'false')

        self.assertEqual('true', app.ui.get_value('MultiDatabases/dreamster'))
        self.assertEqual([], app.messages)
        self.assertEqual([], app.mister_ini_effects)
        info = self._execute_other_cores_info('# DreamSTer')
        self.assertEqual('DreamSTer', info.messages[0]['header'])
        self.assertIn('dc_boot.bin', ' '.join(info.messages[0]['text']))
        self.assertIn('dc_flash.bin', ' '.join(info.messages[0]['text']))

    def test_dreamster_entry___when_disabling___rotates_without_message(self):
        app = self._execute_multidatabase_action('# DreamSTer', 'MultiDatabases/dreamster', 'true')

        self.assertEqual('false', app.ui.get_value('MultiDatabases/dreamster'))
        self.assertEqual([], app.messages)
        self.assertEqual([], app.mister_ini_effects)

    def test_duke3d_entry___when_enabling___arms_ini_sections_without_message_and_exposes_info(self):
        app = self._execute_multidatabase_action('# MiSTer Duke3D', 'MultiDatabases/duke3d', 'false')

        self.assertEqual('true', app.ui.get_value('MultiDatabases/duke3d'))
        self.assertEqual([], app.messages)
        self.assertEqual([
            {'type': 'mister_ini_add', 'variable': 'MultiDatabases/duke3d',
             'target': {'DUKE3D': {'main': 'Mister_duke3d', 'vga_scaler': '0'},
                        'Mister_duke3d': {'main': 'Mister_duke3d', 'vga_scaler': '0'}}},
        ], app.mister_ini_effects)
        info = self._execute_other_cores_info('# MiSTer Duke3D')
        self.assertIn('DUKE3D.GRP', ' '.join(info.messages[0]['text']))

    def test_duke3d_entry___when_disabling___rotates_without_firing_anything(self):
        app = self._execute_multidatabase_action('# MiSTer Duke3D', 'MultiDatabases/duke3d', 'true')

        self.assertEqual('false', app.ui.get_value('MultiDatabases/duke3d'))
        self.assertEqual([], app.messages)
        self.assertEqual([], app.mister_ini_effects)

    def test_megavgmdrive_entry___toggles_without_message_and_exposes_vgm_folder_as_info(self):
        app = self._execute_multidatabase_action('# MegaVGMDrive', 'MultiDatabases/megavgmdrive', 'false')

        self.assertEqual('true', app.ui.get_value('MultiDatabases/megavgmdrive'))
        self.assertEqual([], app.messages)
        self.assertEqual([], app.mister_ini_effects)
        info = self._execute_other_cores_info('# MegaVGMDrive')
        self.assertIn('games/MegaVGMDrive/', ' '.join(info.messages[0]['text']))

    def test_quake_entry___when_enabling___arms_ini_sections_without_message_and_exposes_info(self):
        app = self._execute_multidatabase_action('# MiSTer Quake', 'MultiDatabases/mister-quake', 'false')

        self.assertEqual('true', app.ui.get_value('MultiDatabases/mister-quake'))
        self.assertEqual([], app.messages)
        self.assertEqual([
            {'type': 'mister_ini_add', 'variable': 'MultiDatabases/mister-quake',
             'target': {'Quake': {'main': 'MiSTer_Quake', 'vga_scaler': '0'},
                        'MiSTer_Quake': {'main': 'MiSTer_Quake', 'vga_scaler': '0'}}},
        ], app.mister_ini_effects)
        info = self._execute_other_cores_info('# MiSTer Quake')
        self.assertIn('PAK0.PAK', ' '.join(info.messages[0]['text']))

    def test_mms2_gb_entry___toggles_without_message_and_exposes_hardware_requirements_as_info(self):
        app = self._execute_multidatabase_action('# MMS2 GB Core', 'MultiDatabases/mms2-gb', 'false')

        self.assertEqual('true', app.ui.get_value('MultiDatabases/mms2-gb'))
        self.assertEqual([], app.messages)
        self.assertEqual([], app.mister_ini_effects)
        info = self._execute_other_cores_info('# MMS2 GB Core')
        self.assertIn('Heber Multisystem 2', ' '.join(info.messages[0]['text']))
        self.assertIn('USER button', ' '.join(info.messages[0]['text']))

    def test_paprium_entry___toggles_without_message_and_exposes_rom_folder_as_info(self):
        app = self._execute_multidatabase_action('# Paprium MegaDrive', 'MultiDatabases/paprium', 'false')

        self.assertEqual('true', app.ui.get_value('MultiDatabases/paprium'))
        self.assertEqual([], app.messages)
        self.assertEqual([], app.mister_ini_effects)
        info = self._execute_other_cores_info('# Paprium MegaDrive')
        self.assertIn('games/PapriumMD/', ' '.join(info.messages[0]['text']))

    def test_physical_disc_entry___when_enabling___arms_cd_section_without_message_and_exposes_info(self):
        app = self._execute_multidatabase_action('# Physical CD Support', 'MultiDatabases/physical-disc', 'false')

        self.assertEqual('true', app.ui.get_value('MultiDatabases/physical-disc'))
        self.assertEqual([], app.messages)
        self.assertEqual([
            {'type': 'mister_ini_add', 'variable': 'MultiDatabases/physical-disc',
             'target': {'CD-*': {'main': 'MiSTer_Physical-CD'}}},
        ], app.mister_ini_effects)
        info = self._execute_other_cores_info('# Physical CD Support')
        self.assertIn('USB CD-drive', ' '.join(info.messages[0]['text']))
        self.assertIn('Zaparoo', ' '.join(info.messages[0]['text']))

    def test_sonic_mania_entry___when_enabling___arms_ini_sections_without_message_and_exposes_info(self):
        app = self._execute_multidatabase_action('# Sonic Mania MiSTer', 'MultiDatabases/sonic-mania', 'false')

        self.assertEqual('true', app.ui.get_value('MultiDatabases/sonic-mania'))
        self.assertEqual([], app.messages)
        self.assertEqual([
            {'type': 'mister_ini_add', 'variable': 'MultiDatabases/sonic-mania',
             'target': {'Sonic Mania': {'main': 'MiSTer_SonicMania'},
                        'Sonic Mania (4:3)': {'main': 'MiSTer_SonicMania'}}},
        ], app.mister_ini_effects)
        info = self._execute_other_cores_info('# Sonic Mania MiSTer')
        self.assertIn('Data.rsdk', ' '.join(info.messages[0]['text']))

    def _execute_multidatabase_action(self, title, variable, value):
        entry = self._entry('other_cores_menu', title)
        return self._execute_tools_action(
            entry['actions']['ok'],
            {variable: value},
            entrypoint='other_cores_menu',
            initial_history=['main_menu_login'],
        )

    def _execute_other_cores_info(self, title):
        entry = self._entry('other_cores_menu', title)
        return self._execute_tools_action(
            entry['actions']['info'],
            {},
            entrypoint='other_cores_menu',
            initial_history=['main_menu_login'],
        )

    def test_jtcores_submenu___has_no_separate_auto_enable_option(self):
        entries = self.model['items']['jtcores_menu']['entries']

        self.assertEqual('# JTCORES Enabled', entries[0]['title'])
        self.assertEqual('# Install Private Releases', entries[1]['title'])
        self.assertEqual(2, len(entries))

    def test_jt_private_releases_entry___when_disabled___enables_private_releases_and_allows_auto_enable(self):
        app = self._execute_jt_private_releases_action(
            download_beta_cores='false',
            allow_retroaccount_jt_beta_auto_enable='false',
            retroaccount_jtbeta_access_active='false',
        )

        self.assertEqual('true', app.ui.get_value('download_beta_cores'))
        self.assertEqual('true', app.ui.get_value('allow_retroaccount_jt_beta_auto_enable'))

    def test_jt_private_releases_entry___when_enabled_and_jtbeta_access_active___disables_private_releases_and_blocks_auto_enable(self):
        app = self._execute_jt_private_releases_action(
            download_beta_cores='true',
            allow_retroaccount_jt_beta_auto_enable='true',
            retroaccount_jtbeta_access_active='true',
        )

        self.assertEqual('false', app.ui.get_value('download_beta_cores'))
        self.assertEqual('false', app.ui.get_value('allow_retroaccount_jt_beta_auto_enable'))

    def test_jt_private_releases_entry___when_enabled_without_jtbeta_access_active___disables_private_releases_and_keeps_auto_enable_preference(self):
        app = self._execute_jt_private_releases_action(
            download_beta_cores='true',
            allow_retroaccount_jt_beta_auto_enable='true',
            retroaccount_jtbeta_access_active='false',
        )

        self.assertEqual('false', app.ui.get_value('download_beta_cores'))
        self.assertEqual('true', app.ui.get_value('allow_retroaccount_jt_beta_auto_enable'))

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
        self.assertEqual([
            {'type': 'mister_ini_add', 'variable': 'zaparoo_frontend_active',
             'target': {'mister': {'main': 'zaparoo/MiSTer_Zaparoo'}}},
        ], app.mister_ini_effects)

    def test_zaparoo_frontend_entry___when_active___rotates_frontend_inactive(self):
        app = self._execute_tools_zaparoo_frontend_action('true', 'true')

        self.assertEqual('false', app.ui.get_value('zaparoo_frontend_active'))
        self.assertEqual('true', app.ui.get_value('ZaparooProject/Zaparoo_MiSTer'))
        self.assertEqual([
            {'type': 'mister_ini_del', 'variable': 'zaparoo_frontend_active',
             'target': {'mister': {'main': 'zaparoo/MiSTer_Zaparoo'},
                        'menu': {'main': 'zaparoo/MiSTer_Zaparoo'}}},
        ], app.mister_ini_effects)

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
        self.assertEqual([
            {'type': 'mister_ini_add', 'variable': 'zaparoo_frontend_active',
             'target': {'mister': {'main': 'zaparoo/MiSTer_Zaparoo'}}},
        ], app.mister_ini_effects)

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

    def _jt_private_releases_action_chain(self):
        return self.model['items']['jtcores_menu']['entries'][1]['actions']['ok']

    def _execute_jt_private_releases_action(
            self,
            download_beta_cores,
            allow_retroaccount_jt_beta_auto_enable,
            retroaccount_jtbeta_access_active,
    ):
        return self._execute_tools_action(self._jt_private_releases_action_chain(), {
            'download_beta_cores': download_beta_cores,
            'allow_retroaccount_jt_beta_auto_enable': allow_retroaccount_jt_beta_auto_enable,
            'retroaccount_jtbeta_access_active': retroaccount_jtbeta_access_active,
        }, entrypoint='jtcores_menu')

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

    def test_mister_ini_edits___all_parse_and_reference_declared_variables(self):
        declared_variables = set(gather_variable_declarations(self.model))

        adds = []
        for effect in gather_effects_by_type(self.model, 'mister_ini_add'):
            spec = parse_mister_ini_add(effect)
            self.assertIn(spec.variable, declared_variables, spec.variable)
            adds.append(spec)

        dels = []
        for effect in gather_effects_by_type(self.model, 'mister_ini_del'):
            spec = parse_mister_ini_del(effect)
            self.assertIn(spec.variable, declared_variables, spec.variable)
            dels.append(spec)

        # RetroAchievements is add-only (no del); Zaparoo and the MultiDatabases that
        # document MiSTer.ini sections have adds, only Zaparoo has a del.
        multidb_ini_variables = {
            'MultiDatabases/duke3d',
            'MultiDatabases/mister-quake',
            'MultiDatabases/physical-disc',
            'MultiDatabases/sonic-mania',
        }
        self.assertEqual(
            {'theypsilon/RetroAchievementsDB_MiSTer', 'zaparoo_frontend_active'} | multidb_ini_variables,
            {spec.variable for spec in adds},
        )
        self.assertEqual({'zaparoo_frontend_active'}, {spec.variable for spec in dels})

        # Every site that activates a feature fires its add; every site that
        # deactivates the Zaparoo frontend fires the del. RA fires from its "ok" and
        # "toggle" chains; the Zaparoo frontend prompt is embedded in both the mrext
        # and the zaparoo database flows; each MultiDatabase fires its add from its
        # enable message only (pruning at save time covers the disable path).
        self.assertEqual(2, len([s for s in adds if s.variable == 'theypsilon/RetroAchievementsDB_MiSTer']))
        self.assertEqual(5, len([s for s in adds if s.variable == 'zaparoo_frontend_active']))
        for variable in multidb_ini_variables:
            self.assertEqual(1, len([s for s in adds if s.variable == variable]), variable)
        self.assertEqual(3, len(dels))

        for spec in [s for s in adds if s.variable == 'theypsilon/RetroAchievementsDB_MiSTer']:
            self.assertEqual({'RA_*': {'main': 'MiSTer_RA'}}, spec.target)
        for spec in [s for s in adds if s.variable == 'zaparoo_frontend_active']:
            self.assertEqual({'mister': {'main': 'zaparoo/MiSTer_Zaparoo'}}, spec.target)
        for spec in dels:
            self.assertEqual(
                {'mister': {'main': 'zaparoo/MiSTer_Zaparoo'}, 'menu': {'main': 'zaparoo/MiSTer_Zaparoo'}},
                spec.target,
            )

        # MultiDatabase targets are identical at both firing sites.
        targets = {}
        for spec in adds:
            if spec.variable in multidb_ini_variables:
                targets.setdefault(spec.variable, set()).add(str(spec.target))
        for variable in multidb_ini_variables:
            self.assertEqual(1, len(targets[variable]), variable)

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

    def test_effect_chains___have_no_unreachable_effects_after_terminal_effects(self):
        # ui_engine.resolve_effect_chain returns at the first 'ui', 'condition', or
        # 'navigate' effect, so anything after one of those in a chain never runs.
        violations = _chain_violations(self.model)

        self.assertEqual([], violations)


def _chain_violations(model):
    violations = []
    for location, chain in gather_effect_chains(model):
        for index, effect in enumerate(chain[:-1]):
            if is_terminal_effect(effect):
                violations.append(f'{location}[{index}]')
    return violations


def _navigate_targets(node):
    if isinstance(node, list):
        result = set()
        for item in node:
            result.update(_navigate_targets(item))
        return result

    if not isinstance(node, dict):
        return set()

    result = {node['target']} if node.get('type') == 'navigate' else set()
    for value in node.values():
        result.update(_navigate_targets(value))
    return result


class TestGatherEffectChains(unittest.TestCase):
    """Pins the checker itself: it must catch unreachable effects wherever chains live."""

    def test_condition_in_the_middle_of_a_chain___is_flagged(self):
        violations = _chain_violations(self._model_with_chain([
            {'type': 'condition', 'variable': 'v', 'true': [], 'false': []},
            {'type': 'set_variable', 'target': 'v', 'value': 'true'},
        ]))

        self.assertEqual(['model.items.menu.entries[0].actions.ok[0]'], violations)

    def test_navigate_in_the_middle_of_a_chain___is_flagged(self):
        violations = _chain_violations(self._model_with_chain([
            {'type': 'navigate', 'target': 'back'},
            {'type': 'set_variable', 'target': 'v', 'value': 'true'},
        ]))

        self.assertEqual(1, len(violations))

    def test_ui_effect_in_the_middle_of_a_chain___is_flagged(self):
        violations = _chain_violations(self._model_with_chain([
            {'ui': 'message', 'text': ['hi']},
            {'type': 'set_variable', 'target': 'v', 'value': 'true'},
        ]))

        self.assertEqual(1, len(violations))

    def test_terminal_effect_as_last_element___is_not_flagged(self):
        violations = _chain_violations(self._model_with_chain([
            {'type': 'set_variable', 'target': 'v', 'value': 'true'},
            {'type': 'navigate', 'target': 'back'},
        ]))

        self.assertEqual([], violations)

    def test_chain_without_terminal_effects___is_not_flagged(self):
        violations = _chain_violations(self._model_with_chain([
            {'type': 'set_variable', 'target': 'v', 'value': 'true'},
            {'type': 'rotate_variable', 'target': 'v'},
        ]))

        self.assertEqual([], violations)

    def test_violation_inside_a_condition_branch___is_flagged(self):
        violations = _chain_violations(self._model_with_chain([
            {'type': 'condition', 'variable': 'v', 'true': [
                {'type': 'navigate', 'target': 'back'},
                {'type': 'set_variable', 'target': 'v', 'value': 'true'},
            ], 'false': []},
        ]))

        self.assertEqual(['model.items.menu.entries[0].actions.ok[0].true[0]'], violations)

    def test_violation_inside_a_fixed_action___is_flagged(self):
        violations = _chain_violations({'items': {'menu': {'entries': [{
            'ui': 'confirm',
            'actions': [
                {'title': 'Yes', 'type': 'fixed', 'fixed': [
                    {'type': 'condition', 'variable': 'v', 'true': [], 'false': []},
                    {'type': 'navigate', 'target': 'back'},
                ]},
            ],
        }]}}})

        self.assertEqual(['model.items.menu.entries[0].actions[0].fixed[0]'], violations)

    def test_violation_in_on_idle___is_flagged(self):
        violations = _chain_violations({'items': {'menu': {
            'entries': [],
            'on_idle': [
                {'type': 'navigate', 'target': 'back'},
                {'type': 'set_variable', 'target': 'v', 'value': 'true'},
            ],
        }}})

        self.assertEqual(['model.items.menu.on_idle[0]'], violations)

    @staticmethod
    def _model_with_chain(chain):
        return {'items': {'menu': {'entries': [{'actions': {'ok': chain}}]}}}


class ToolsMenuActionApplication(UiApplication):
    def __init__(self, action_chain, initial_values, confirm_action_title=None):
        self.action_chain = action_chain
        self.initial_values = initial_values
        self.confirm_action_titles = self._confirm_action_titles(confirm_action_title)
        self.ui = None
        self.confirms = []
        self.last_confirm = None
        self.messages = []
        self.mister_ini_effects = []

    def initialize_ui(self, ui: UiContext) -> UiSectionFactory:
        self.ui = ui
        for key, value in self.initial_values.items():
            ui.set_value(key, value)
        ui.add_custom_effects({
            'mister_ini_add': lambda effect: self.mister_ini_effects.append(effect),
            'mister_ini_del': lambda effect: self.mister_ini_effects.append(effect),
        })
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

        if ui_type == 'message':
            self.app.messages.append(data)
            return MessageActionSection(data)

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


class MessageActionSection(UiSection):
    def __init__(self, data):
        self.data = data
        self.idle_done = False

    def process_key(self):
        if not self.idle_done and 'on_idle' in self.data:
            self.idle_done = True
            return EffectChain(self.data['on_idle'])

        return EffectChain(self.data.get('effects', [{'type': 'navigate', 'target': 'back'}]))

    def reset(self) -> None:
        pass

    def clear(self) -> None:
        pass
