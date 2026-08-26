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


def execute_chain(chain, values=None, variables=None):
    app = EffectChainApplication(chain, values or {})
    execute_ui_engine('entry', effect_chain_model(variables), app, RuntimeStub())
    return app


def _condition(variable, **branches):
    return {'type': 'condition', 'variable': variable, **branches}


def _navigate(target):
    return [{'type': 'navigate', 'target': target}]


_MIRROR_VARIABLES = {'mirror': {'default': 'off', 'values': ['off', 'andi_br']}}


class TestConditionAction(unittest.TestCase):
    def test_condition___with_declared_value___dispatches_to_its_branch(self):
        app = execute_chain(
            [_condition('mirror', off=_navigate('path_a'), andi_br=_navigate('path_b'))],
            values={'mirror': 'andi_br'},
            variables=_MIRROR_VARIABLES,
        )

        self.assertIn('path_b', app.visited_sections)

    def test_condition___with_undeclared_value___dispatches_to_branch_of_first_declared_value(self):
        app = execute_chain(
            [_condition('mirror', off=_navigate('path_a'), andi_br=_navigate('path_b'))],
            values={'mirror': ''},
            variables=_MIRROR_VARIABLES,
        )

        self.assertIn('path_a', app.visited_sections)

    def test_condition___with_undeclared_value___does_not_change_the_variable(self):
        app = execute_chain(
            [_condition('mirror', off=_navigate('path_a'), andi_br=_navigate('path_b'))],
            values={'mirror': 'mysticalrealm'},
            variables=_MIRROR_VARIABLES,
        )

        self.assertEqual('mysticalrealm', app.ui.get_value('mirror'))

    def test_condition___with_declared_value_but_no_branch_for_it___raises(self):
        with self.assertRaises(ValueError):
            execute_chain(
                [_condition('mirror', off=_navigate('path_a'))],
                values={'mirror': 'andi_br'},
                variables=_MIRROR_VARIABLES,
            )

    def test_condition___with_undeclared_value_and_no_branch_for_the_first_declared_value___raises(self):
        with self.assertRaises(ValueError):
            execute_chain(
                [_condition('mirror', andi_br=_navigate('path_b'))],
                values={'mirror': ''},
                variables=_MIRROR_VARIABLES,
            )

    def test_condition___on_variable_without_declared_values___raises_when_there_is_no_branch(self):
        with self.assertRaises(ValueError):
            execute_chain(
                [_condition('outcome', equal=_navigate('path_a'), left=_navigate('path_b'))],
                values={'outcome': 'right'},
            )


def effect_chain_model(variables=None):
    return {
        'variables': variables or {},
        'items': {
            'entry': {'ui': 'stub', 'name': 'entry'},
            'path_a': {'ui': 'stub', 'name': 'path_a'},
            'path_b': {'ui': 'stub', 'name': 'path_b'},
        },
    }


class EffectChainApplication(UiApplication):
    def __init__(self, chain, initial_values):
        self.chain = chain
        self.initial_values = initial_values
        self.ui = None
        self.visited_sections = []

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
        pass
