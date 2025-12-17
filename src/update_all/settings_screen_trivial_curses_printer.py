# Copyright (c) 2022-2025 José Manuel Barroso Galindo <theypsilon@gmail.com>

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
import curses
from typing import Tuple, Union

from update_all.settings_screen_printer import SettingsScreenPrinter, ColorThemeManager
from update_all.ui_engine import Interpolator
from update_all.ui_engine_curses_runtime import CursesRuntime
from update_all.ui_engine_dialog_application import UiDialogDrawerFactory, UiDialogDrawer
from update_all.ui_model_utilities import Key


class SettingsScreenTrivialCursesPrinter(CursesRuntime, SettingsScreenPrinter, ColorThemeManager, UiDialogDrawerFactory, UiDialogDrawer):
    _interpolator: Interpolator
    _index_horizontal = 0
    _index_vertical = 0

    def initialize_screen(self) -> Tuple[UiDialogDrawerFactory, ColorThemeManager]:
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)

        self.window.clear()
        self.window.bkgd(' ', curses.color_pair(1) | curses.A_BOLD)

        return self, self

    def set_theme(self, new_theme):
        pass

    def create_ui_dialog_drawer(self, interpolator: Interpolator) -> UiDialogDrawer:
        self._interpolator = interpolator
        self._index_vertical = 0
        self._index_horizontal = 0
        return self

    def start(self, data):
        self.window.clear()
        self._index_vertical = 0
        self._index_horizontal = 0
        if 'header' in data:
            self.window.addstr(0, 1, self._interpolator.interpolate(data['header']), curses.A_NORMAL)
            self._index_vertical += 1

    def add_text_line(self, text):
        self.window.addstr(self._index_vertical, 1, self._interpolator.interpolate(text), curses.A_NORMAL)
        self._index_vertical += 1

    def add_menu_entry(self, option, info, is_selected=False):
        mode = curses.A_REVERSE if is_selected else curses.A_NORMAL
        self.window.addstr(self._index_vertical, 1, self._interpolator.interpolate(option), mode)
        self.window.addstr(self._index_vertical, 30, self._interpolator.interpolate(info), mode)
        self._index_vertical += 1

    def add_action(self, action, is_selected=False):
        mode = curses.A_REVERSE if is_selected else curses.A_NORMAL
        self.window.addstr(self._index_vertical, 1 + 30 * self._index_horizontal, self._interpolator.interpolate(action), mode)
        self._index_horizontal += 1

    def add_inactive_action(self, length: int, is_selected=False):
        self._index_horizontal += 1

    def paint(self) -> Union[Key, int]:
        return self.read_key()

    def clear(self) -> None:
        pass
