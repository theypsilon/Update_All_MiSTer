# Copyright (c) 2022 José Manuel Barroso Galindo <theypsilon@gmail.com>

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
from update_all.config_reader import Config
from update_all.databases import model_variables_by_db_id, db_ids_by_model_variables
from update_all.settings_screen_model import settings_screen_model
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
            default_config_values[variable] = db_id in config.databases

        default_model_main_values = {variable: dynamic_convert_string(description['default']) for variable, description in main_variables.items()}

        intersection = set(default_config_values) & set(default_model_main_values)

        self.assertGreaterEqual(len(intersection), 5)
        self.assertEqual({k: v for k, v in default_config_values.items() if k in intersection}, default_model_main_values)

    def test_all_database_variables_are_declared_in_the_model(self):
        db_variables = set(db_ids_by_model_variables())
        model_variables = set(gather_variable_declarations(self.model, 'db'))

        self.assertGreaterEqual(len(db_variables), 5)
        self.assertEqual(db_variables, model_variables)

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
        navigate_targets = gather_navigate_targets(self.model) | {'main_menu', 'test_menu'}
        section_names = set(gather_section_names(self.model)) | set(special_navigate_targets())

        self.assertGreaterEqual(len(section_names), 1)
        self.assertEqual(navigate_targets, section_names)

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