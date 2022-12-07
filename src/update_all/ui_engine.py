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
import abc
from typing import Dict, Callable, Any, Union, Optional, List

from update_all.ui_model_utilities import gather_variable_declarations, expand_type, Key


class UiContext(abc.ABC):
    def get_value(self, key: str) -> str:
        """Gets value for variable on the given key"""

    def set_value(self, key: str, value: Any) -> None:
        """Sets value as string for variable on the given key"""

    def add_custom_effects(self, effects: Dict[str, Callable[[], None]]):
        """Add effects during initialization"""

    def add_custom_formatters(self, formatters: Dict[str, Callable[[str], str]]):
        """Add callable formatters during initialization"""



class UiRuntime(abc.ABC):
    def initialize_runtime(self, cb: Callable[[], None]) -> None:
        """Initializes UI runtime and when ready calls cb"""

    def update(self) -> None:
        """Updates internal UI state according to the latest inputs"""

    def interrupt(self) -> None:
        """Closes the UI temporarily"""

    def resume(self) -> None:
        """Resumes the UI that was previously interrupted"""


class Interpolator(abc.ABC):
    def interpolate(self, text: str) -> str:
        """Interpolates any value inside a string into another string according to the formatters"""


Effect = Dict[str, Any]
class EffectChain:
    def __init__(self, chain: List[Effect]):
        self.chain = chain
ProcessKeyResult = Union[int, EffectChain]


class UiSection(abc.ABC):
    def process_key(self) -> Optional[ProcessKeyResult]:
        """Writes text on window, reads char and returns it"""

    def reset(self) -> None:
        """Resets the UI Section"""

    def clear(self) -> None:
        """Clears the UI Section"""

class UiSectionFactory(abc.ABC):
    def create_ui_section(self, ui_type: str, data: Dict[str, Any], interpolator: Interpolator) -> UiSection:
        """Creates an instance of a UiSection"""


class UiApplication(abc.ABC):
    def initialize_ui(self, ui: UiContext) -> UiSectionFactory:
        """Initializes the theme at the start"""


def execute_ui_engine(entrypoint: str, model: Dict[str, Any], ui_application: UiApplication, ui_runtime: UiRuntime):
    ui = _UiSystem(entrypoint, model, ui_application, ui_runtime)
    ui.execute()


class _UiSystem(UiContext):
    def __init__(self, entrypoint, model, ui_application: UiApplication, ui_runtime: UiRuntime):
        self._entrypoint = entrypoint
        self._model = model
        self._ui_application = ui_application
        self._ui_runtime = ui_runtime
        self._values = {}
        self._custom_effects = {}
        self._custom_formatters = {}
        self._is_initializing = False

    def get_value(self, key: str) -> str:
        return self._values[key]

    def set_value(self, key: str, value: Any) -> None:
        self._values[key] = value

    def execute(self):
        self._values.update({k: v['default'] for k, v in gather_variable_declarations(self._model).items()})

        self._is_initializing = True

        ui_section_factory = self._ui_application.initialize_ui(self)

        self._is_initializing = False

        runtime = _UiMainLoop(self._model, self._entrypoint, self, ui_section_factory, self._ui_runtime)
        runtime.execute()

    def add_custom_effects(self, effects: Dict[str, Callable[[], None]]):
        self._ensure_is_initializing('add_custom_effects')

        self._custom_effects = effects

    def add_custom_formatters(self, formatters: Dict[str, Callable[[str], str]]):
        self._ensure_is_initializing('add_custom_formatters')

        self._custom_formatters = formatters

    def custom_effects(self) -> Dict[str, Callable[[], None]]:
        return self._custom_effects

    def custom_formatters(self) ->  Dict[str, Callable[[str], str]]:
        return self._custom_formatters

    def _ensure_is_initializing(self, topic):
        if self._is_initializing:
            return

        raise Exception(f'{topic} should only be used within the execution of UiApplication.initialize_ui.')


class _UiMainLoop:
    def __init__(self, model, entrypoint, ui_system: _UiSystem, ui_section_factory: UiSectionFactory, ui_runtime: UiRuntime):
        self._model = model
        self._section = entrypoint
        self._items = self._model['items']
        self._section_states = {}
        self._history = []
        self._ui_system = ui_system
        self._ui_section_factory = ui_section_factory
        self._ui_runtime = ui_runtime

    def execute(self):
        self._current_section_state().reset()

        while True:
            new_section = self._current_section_state().process()

            self._ui_runtime.update()

            if new_section is None:
                continue

            if new_section == 'exit_and_run':
                break
            elif new_section == 'abort':
                exit(0)
            elif new_section == 'back':
                if len(self._history) == 0:
                    break
                self._section = self._history.pop()

            elif new_section == 'clear_window':
                self._current_section_state().clear()
                continue
            elif isinstance(new_section, dict):
                self._push_history()
                self._section = '@temporary'
                self._section_states['@temporary'] = self._make_section_state(new_section)
                self._section_states['@temporary'].reset()
            else:
                self._push_history()
                self._section = new_section
                self._current_section_state().reset()

    def _push_history(self):
        if self._section == '@temporary':
            return
        self._history.append(self._section)

    def _current_section_state(self):
        if self._section not in self._section_states:
            self._section_states[self._section] = self._make_section_state(self._items[self._section])
        return self._section_states[self._section]

    def _make_section_state(self, data):
        expand_type(data, self._model.get('base_types', {}))

        for field in ['formatters', 'variables']:
            data[field] = data.get(field, {})
            data[field].update(self._model.get(field, {}))
            for section in self._history:
                data[field].update(self._items[section].get(field, {}))

        data['formatters'].update(self._ui_system.custom_formatters())

        hotkeys = {}
        for hk in data.get('hotkeys', []):
            for key in hk['keys']:
                hotkeys[key] = hk['action']

        interpolator = _Interpolator(data['formatters'], self._ui_system)
        effect_resolver = _EffectResolver(self._ui_system, data, self._ui_system.custom_effects())

        ui_type = data['ui'] if 'ui' in data else None
        if ui_type is None:
            raise ValueError(f'Wrong ui_type: "{data["ui"] if "ui" in data else "`ui` field not found"}"')

        ui_section = self._ui_section_factory.create_ui_section(ui_type, data, interpolator)
        return _UiSectionProcessor(ui_section, effect_resolver, hotkeys)


class _UiSectionProcessor:
    def __init__(self, ui_section: UiSection, effect_resolver, hotkeys):
        self._ui_section = ui_section
        self._effect_resolver = effect_resolver
        self._hotkeys = hotkeys

    def process(self):
        key_result = self._ui_section.process_key()

        if key_result is None:
            return None
        elif isinstance(key_result, EffectChain):
            return self._effect_resolver.resolve_effect_chain(key_result.chain)
        elif isinstance(key_result, Key):
            pass
        elif key_result in self._hotkeys:
            return self._effect_resolver.resolve_effect_chain(self._hotkeys[key_result])
        elif self._chr(key_result) in self._hotkeys:
            return self._effect_resolver.resolve_effect_chain(self._hotkeys[self._chr(key_result)])
        elif not isinstance(key_result, int):
            raise TypeError(f'Result with type {str(type(key_result))} can not be processed by the effect resolver')

    @staticmethod
    def _chr(key_result):
        try:
            return chr(key_result)
        except ValueError:
            return 1000000

    def reset(self):
        self._ui_section.reset()

    def clear(self):
        self._ui_section.clear()


class _Interpolator(Interpolator):
    def __init__(self, formatters: Dict[str, Union[Dict[str, str], Callable[[str], str]]], ui: UiContext):
        self._formatters = formatters
        self._ui = ui

    def interpolate(self, text):
        reading_state = 0
        reading_value = ''
        reading_modifier = ''
        reading_arguments = []
        reading_current_argument = ''
        values = dict()

        for character in text:
            if reading_state == 0:
                if character == '{':
                    reading_state = 1
                    reading_value = ''

            elif reading_state == 1:
                if character == '}':
                    reading_state = 0
                    values[reading_value] = self._call_formatter(reading_value, reading_value) if reading_value in self._formatters else self._ui.get_value(reading_value)
                elif character == ':':
                    reading_state = 2
                    reading_modifier = ''
                else:
                    reading_value += character

            elif reading_state == 2:
                if character == '=':
                    reading_arguments = []
                    reading_current_argument = ''
                    reading_state = 3
                elif character == '}':
                    reading_state = 0
                    values[reading_value + ':' + reading_modifier] = self._call_formatter(reading_modifier, reading_value)
                else:
                    reading_modifier += character

            elif reading_state == 3:
                if character == '}':
                    reading_arguments.append(reading_current_argument)
                    reading_state = 0
                    values[reading_value + ':' + reading_modifier + '=' + ','.join(reading_arguments)] = self._call_formatter(reading_modifier, reading_value, reading_arguments)
                elif character == ',':
                    reading_arguments.append(reading_current_argument)
                    reading_current_argument = ''
                else:
                    reading_current_argument += character

            else:
                raise NotImplementedError(reading_state)

        for var_name, var_value in values.items():
            text = text.replace("{" + var_name + "}", str(var_value))

        return text

    def _call_formatter(self, reading_modifier: str, reading_value: str, reading_arguments: List[str] = None) -> str:
        if reading_modifier not in self._formatters:
            raise ValueError(f'Formatter "{reading_modifier}" called for value "{reading_value}" does not exit.')

        formatter = self._formatters[reading_modifier]
        try:
            variable_value = self._ui.get_value(reading_value)
            if callable(formatter):
                result = formatter(variable_value)
            else:
                result = formatter[variable_value] if variable_value in formatter else variable_value

            if reading_arguments is None:
                return result
            else:
                return result.format(*reading_arguments)

        except Exception as e:
            raise ValueError(reading_value, reading_modifier, formatter, e)


class _EffectResolver:
    def __init__(self, ui, data, additional_effects: Dict[str, Callable[[Effect], None]]):
        self._ui = ui
        self._data = data
        self._additional_effects = additional_effects

    def resolve_effect_chain(self, chain: List[Effect]):
        result = None
        for effect in chain:
            if 'ui' in effect:
                return effect
            elif 'type' not in effect:
                raise ValueError('Effects should either have property `ui` or property `type`.')
            elif effect['type'] == 'condition':
                variable = effect['variable']
                return self.resolve_effect_chain(effect[self._ui.get_value(variable)])
            elif effect['type'] == 'navigate':
                return effect['target']
            elif effect['type'] == 'rotate_variable':
                target_variable = effect['target']
                possible_values = self._data['variables'][target_variable]['values']

                cur_index = 0
                for index, var_value in enumerate(possible_values):
                    if var_value == self._ui.get_value(target_variable):
                        cur_index = index
                        break

                cur_index += 1
                if cur_index >= len(possible_values):
                    cur_index = 0

                if possible_values[cur_index] != self._ui.get_value(target_variable):
                    self._ui.set_value(target_variable, possible_values[cur_index])
                    result = 'clear_window'
            elif effect['type'] in self._additional_effects:
                self._additional_effects[effect['type']](effect)
            else:
                raise NotImplementedError(f'Wrong effect type :"{effect["type"]}"')

        return result
