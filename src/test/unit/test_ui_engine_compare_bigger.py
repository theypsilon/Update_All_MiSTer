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

from update_all.ui_engine import EffectChain, Interpolator, UiApplication, UiContext, UiRuntime, UiSection, \
    UiSectionFactory, execute_ui_engine


def execute_chain(chain, variables=None):
    app = EffectChainApplication(chain, {'outcome': '', **(variables or {})})
    execute_ui_engine('entry', effect_chain_model(), app, RuntimeStub())
    return app


def _compare(left, right, target='outcome'):
    return {'type': 'compare_bigger', 'left': left, 'right': right, 'target': target}


class TestCompareBiggerAction(unittest.TestCase):
    def test_variable_vs_variable___left_bigger___writes_left(self):
        app = execute_chain([_compare('a', 'b')], {'a': '5', 'b': '3'})
        self.assertEqual('left', app.ui.get_value('outcome'))

    def test_variable_vs_variable___right_bigger___writes_right(self):
        app = execute_chain([_compare('a', 'b')], {'a': '3', 'b': '5'})
        self.assertEqual('right', app.ui.get_value('outcome'))

    def test_variable_vs_variable___equal___writes_equal(self):
        app = execute_chain([_compare('a', 'b')], {'a': '5', 'b': '5'})
        self.assertEqual('equal', app.ui.get_value('outcome'))

    def test_variable_vs_literal___under_literal___writes_right(self):
        app = execute_chain([_compare('size', 200)], {'size': '150'})
        self.assertEqual('right', app.ui.get_value('outcome'))

    def test_variable_vs_literal___over_literal___writes_left(self):
        app = execute_chain([_compare('size', 200)], {'size': '250'})
        self.assertEqual('left', app.ui.get_value('outcome'))

    def test_literal_vs_literal___equal(self):
        app = execute_chain([_compare(200, 200)])
        self.assertEqual('equal', app.ui.get_value('outcome'))

    def test_float_parsing___string_var_vs_literal_float(self):
        app = execute_chain([_compare('a', 2.0)], {'a': '1.5'})
        self.assertEqual('right', app.ui.get_value('outcome'))

    def test_composed_with_condition___dispatches_to_correct_branch(self):
        chain = [
            _compare('a', 'b'),
            {
                'type': 'condition', 'variable': 'outcome',
                'equal': [{'type': 'navigate', 'target': 'path_equal'}],
                'left': [{'type': 'navigate', 'target': 'path_left'}],
                'right': [{'type': 'navigate', 'target': 'path_right'}],
            },
        ]
        app = execute_chain(chain, {'a': '7', 'b': '3'})
        self.assertIn('path_left', app.visited_sections)

    def test_clears_section_when_target_changes(self):
        app = execute_chain([_compare('a', 'b')], {'a': '5', 'b': '3'})
        self.assertEqual(1, app.clear_count)

    def test_does_not_clear_section_when_target_already_holds_outcome(self):
        app = execute_chain([_compare('a', 'b')], {'a': '5', 'b': '3', 'outcome': 'left'})
        self.assertEqual(0, app.clear_count)

    def test_boolean_operand_raises(self):
        with self.assertRaises(ValueError):
            execute_chain([_compare(True, 'a')], {'a': '5'})

    def test_unsupported_operand_type_raises(self):
        with self.assertRaises(ValueError):
            execute_chain([_compare({'not': 'a number'}, 'a')], {'a': '5'})


def effect_chain_model():
    return {
        'items': {
            'entry': {'ui': 'stub', 'name': 'entry'},
            'path_equal': {'ui': 'stub', 'name': 'path_equal'},
            'path_left': {'ui': 'stub', 'name': 'path_left'},
            'path_right': {'ui': 'stub', 'name': 'path_right'},
        },
    }


class EffectChainApplication(UiApplication):
    def __init__(self, chain, initial_values):
        self.chain = chain
        self.initial_values = initial_values
        self.ui = None
        self.visited_sections = []
        self.clear_count = 0

    def initialize_ui(self, ui: UiContext) -> UiSectionFactory:
        self.ui = ui
        for key, value in self.initial_values.items():
            ui.set_value(key, value)
        return EffectChainSectionFactory(self)


class RuntimeStub(UiRuntime):
    def initialize_runtime(self, cb):
        cb()

    def update(self) -> None:
        pass

    def interrupt(self) -> None:
        pass

    def resume(self) -> None:
        pass


class EffectChainSectionFactory(UiSectionFactory):
    def __init__(self, app):
        self.app = app

    def create_ui_section(self, _ui_type: str, data: dict, _interpolator: Interpolator) -> UiSection:
        return EffectChainSection(data['name'], self.app)


class EffectChainSection(UiSection):
    def __init__(self, name, app):
        self.name = name
        self.app = app
        self.processed = False

    def process_key(self):
        self.app.visited_sections.append(self.name)
        if self.name != 'entry' or self.processed:
            return EffectChain([{'type': 'navigate', 'target': 'exit_and_run'}])

        self.processed = True
        return EffectChain(self.app.chain)

    def reset(self) -> None:
        pass

    def clear(self) -> None:
        self.app.clear_count += 1
