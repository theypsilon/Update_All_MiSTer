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


class TestUiEngineNavigation(unittest.TestCase):
    def test_execute_ui_engine___with_initial_history___back_returns_to_seeded_parent(self):
        events = []
        model = {
            'items': {
                'parent': {'ui': 'stub', 'name': 'parent', 'effects': [{'type': 'navigate', 'target': 'exit_and_run'}]},
                'child': {'ui': 'stub', 'name': 'child', 'effects': [{'type': 'navigate', 'target': 'back'}]},
            },
        }

        execute_ui_engine('child', model, _Application(events), _Runtime(), initial_history=['parent'])

        self.assertEqual(['child', 'parent'], events)

    def test_execute_ui_engine___set_variable_with_undeclared_variable___sets_it_directly(self):
        events = []
        model = {
            'items': {
                'main': {'ui': 'stub', 'name': 'main', 'effects': [
                    {'type': 'set_variable', 'target': 'undeclared_var', 'value': 'hello'},
                    {'type': 'navigate', 'target': 'exit_and_run'},
                ]},
            },
        }

        app = _Application(events)
        execute_ui_engine('main', model, app, _Runtime())

        self.assertEqual('hello', app.ui.get_value('undeclared_var'))


class _Application(UiApplication):
    def __init__(self, events):
        self._events = events
        self.ui = None

    def initialize_ui(self, ui: UiContext) -> UiSectionFactory:
        self.ui = ui
        return _SectionFactory(self._events)


class _Runtime(UiRuntime):
    def initialize_runtime(self, cb):
        cb()

    def update(self) -> None:
        pass

    def interrupt(self) -> None:
        pass

    def resume(self) -> None:
        pass


class _SectionFactory(UiSectionFactory):
    def __init__(self, events):
        self._events = events

    def create_ui_section(self, _ui_type: str, data: dict, _interpolator: Interpolator) -> UiSection:
        return _Section(data, self._events)


class _Section(UiSection):
    def __init__(self, data, events):
        self._data = data
        self._events = events

    def process_key(self):
        self._events.append(self._data['name'])
        return EffectChain(self._data['effects'])

    def reset(self) -> None:
        pass

    def clear(self) -> None:
        pass
