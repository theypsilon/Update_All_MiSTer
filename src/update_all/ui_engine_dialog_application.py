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
import curses
from typing import Dict, Any, Optional, List

from update_all.ui_engine import EffectChain, ProcessKeyResult, UiSection, Interpolator, UiSectionFactory


class UiDialogDrawer(abc.ABC):
    def start(self, data):
        """"Start of screen"""

    def add_text_line(self, text):
        """"Adds text line"""

    def add_menu_entry(self, option, info, is_selected=False):
        """"Adds menu entry"""

    def add_action(self, action, is_selected=False):
        """"Adds action"""

    def add_inactive_action(self, length: int, is_selected=False):
        """"Adds action"""

    def paint(self) -> int:
        """"Paints all screen UI and returns char"""

    def clear(self) -> None:
        """Clears all the screen"""


class UiDialogDrawerFactory(abc.ABC):
    def create_ui_dialog_drawer(self, interpolator: Interpolator) -> UiDialogDrawer:
        """Creates instances of DialogDrawer"""


class _NavigationState:
    def __init__(self, vertical_limit, horizontal_limit):
        self._position = 0
        self._lateral_position = 0
        self._vertical_limit = vertical_limit
        self._horizontal_limit = horizontal_limit

    def position(self):
        return self._position

    def lateral_position(self):
        return self._lateral_position

    def navigate_up(self):
        self._position -= 1
        if self._position < 0:
            self._position = 0

    def navigate_down(self):
        self._position += 1
        if self._position >= self._vertical_limit:
            self._position = self._vertical_limit - 1

    def navigate_left(self):
        self._lateral_position -= 1
        if self._lateral_position < 0:
            self._lateral_position = 0

    def navigate_right(self):
        self._lateral_position += 1
        if self._lateral_position >= self._horizontal_limit:
            self._lateral_position = self._horizontal_limit - 1

    def reset_lateral_position(self, value=None):
        self._lateral_position = value or 0

    def reset_position(self, value=None):
        self._position = value or 0


class _Message(UiSection):
    def __init__(self, drawer: UiDialogDrawer, data: Dict[str, Any]):
        self._drawer = drawer
        self._data = data

    def process_key(self) -> Optional[ProcessKeyResult]:
        self._drawer.start(self._data)

        for index, text_line in enumerate(self._data['text']):
            self._drawer.add_text_line(text_line)

        self._drawer.add_action(self._data.get('action_name', 'Ok'), is_selected=True)

        key = self._drawer.paint()
        if key in [curses.KEY_ENTER, ord("\n")]:
            return EffectChain(self._data['effects'])

        return key

    def reset(self) -> None:
        pass

    def clear(self) -> None:
        self._drawer.clear()


class _Confirm(UiSection):
    def __init__(self, drawer: UiDialogDrawer, data: Dict[str, Any], state: _NavigationState):
        self._drawer = drawer
        self._data = data
        self._state = state

    def process_key(self) -> Optional[ProcessKeyResult]:
        self._drawer.start(self._data)

        for index, text_line in enumerate(self._data['text']):
            self._drawer.add_text_line(text_line)

        for index, action in enumerate(self._data['actions']):
            self._drawer.add_action(action['title'], index == self._state.lateral_position())

        key = self._drawer.paint()
        if key == curses.KEY_LEFT:
            self._state.navigate_left()
        elif key == curses.KEY_RIGHT:
            self._state.navigate_right()
        elif key in [curses.KEY_ENTER, ord("\n")]:
            return _make_action_effect_chain(self._data, self._state)

        return key

    def reset(self) -> None:
        self._state.reset_lateral_position()
        if 'preselected_action' not in self._data:
            return

        preselected_action = self._data['preselected_action']
        for index, action in enumerate(self._data['actions']):
            if action['title'] == preselected_action:
                self._state.reset_lateral_position(index)

    def clear(self) -> None:
        self._drawer.clear()


class DialogSectionFactory(UiSectionFactory):
    def __init__(self, dialog_drawer_factory: UiDialogDrawerFactory):
        self._dialog_drawer_factory = dialog_drawer_factory

    def create_ui_section(self, ui_type: str, data: Dict[str, Any], interpolator: Interpolator) -> UiSection:
        state = _NavigationState(self._count_entries(data), len(data.get('actions', {})))
        drawer = self._dialog_drawer_factory.create_ui_dialog_drawer(interpolator)
        if ui_type == 'menu':
            return _Menu(drawer, data, state)
        elif ui_type == 'confirm':
            return _Confirm(drawer, data, state)
        elif ui_type == 'message':
            if 'effects' not in data:
                data['effects'] = [{"type": "navigate", "target": "back"}]
            return _Message(drawer, data)
        else:
            raise ValueError(f'Not implemented ui_type: {ui_type}')

    @staticmethod
    def _count_entries(data: Dict[str, Any]) -> int:
        count = 0
        for entry in data.get('entries', []):
            if len(entry) == 0:
                continue
            count += 1
        return count


class _Menu(UiSection):
    def __init__(self, drawer: UiDialogDrawer, data: Dict[str, Any], state: _NavigationState):
        self._drawer = drawer
        self._data = data
        self._state = state
        self._hotkeys = {}
        self._separators = {}
        entries = []
        for entry in self._data['entries']:
            target_index = len(entries)
            if len(entry) == 0:
                self._separators[target_index] = self._separators.get(target_index, 0)
                self._separators[target_index] += 1
                continue

            first_letter = ord(entry['title'][0:1].lower())
            self._hotkeys[first_letter] = target_index
            entries.append(entry)

        self._data['entries'] = entries
        if curses.LINES <= 15: # This is to avoid text being cutoff off the screen in tiny resolutions.
            self._separators = {}

    def process_key(self) -> Optional[ProcessKeyResult]:
        self._drawer.start(self._data)

        any_text = False
        for index, text_line in enumerate(self._data.get('text', [])):
            self._drawer.add_text_line(text_line)
            any_text = True

        if any_text:
            self._drawer.add_text_line(' ')

        entry_index = 0
        for index, entry in enumerate(self._data['entries']):
            for _ in range(self._separators.get(index, 0)):
                self._drawer.add_menu_entry(' ', '', False)

            self._drawer.add_menu_entry(entry['title'], entry.get('description', ''), entry_index == self._state.position())
            entry_index += 1

        for index, action in enumerate(self._data['actions']):
            title = action['title']
            is_selected = index == self._state.lateral_position()
            if action['type'] == 'symbol' and action['symbol'] not in self._data['entries'][self._state.position()]['actions']:
                self._drawer.add_inactive_action(len(title), is_selected)
            else:
                self._drawer.add_action(title, is_selected)

        key = self._drawer.paint()
        if key == curses.KEY_UP:
            self._state.navigate_up()
        elif key == curses.KEY_DOWN:
            self._state.navigate_down()
        elif key == curses.KEY_LEFT:
            self._state.navigate_left()
        elif key == curses.KEY_RIGHT:
            self._state.navigate_right()
        elif key in [curses.KEY_ENTER, ord("\n")]:
            return _make_action_effect_chain(self._data, self._state)
        elif key in self._hotkeys:
            self._state.reset_position(self._hotkeys[key])

        return key

    def reset(self) -> None:
        self._state.reset_lateral_position()

    def clear(self) -> None:
        self._drawer.clear()


def _make_action_effect_chain(data: Dict[str, Any], state: _NavigationState) -> Optional[EffectChain]:
    props = data['actions'][state.lateral_position()]
    if props['type'] == 'symbol':
        selection = data['entries'][state.position()]
        if 'actions' not in selection:
            raise ValueError('Selection does not contain nested actions that can be linked to symbol.')

        symbol = props['symbol']
        if symbol not in selection['actions']:
            return None

        return EffectChain(selection['actions'][symbol])
    elif props['type'] == 'fixed':
        return EffectChain(props['fixed'])
    else:
        raise Exception(f"Action type '{props['type']}' not valid.")
