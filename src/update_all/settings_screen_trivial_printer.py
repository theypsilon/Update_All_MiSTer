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
import curses
from typing import Tuple

from update_all.settings_screen_printer import SettingsScreenPrinter, SettingsScreenThemeManager
from update_all.ui_engine import Interpolator
from update_all.ui_engine_dialog_application import UiDialogDrawerFactory, UiDialogDrawer


class SettingsScreenTrivialPrinter(SettingsScreenPrinter, SettingsScreenThemeManager):
    def initialize_screen(self, screen: curses.window) -> Tuple[UiDialogDrawerFactory, SettingsScreenThemeManager]:
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)

        window = screen.subwin(0, 0)
        window.keypad(True)
        window.clear()
        window.bkgd(' ', curses.color_pair(1) | curses.A_BOLD)

        return _DrawerFactory(window), self

    def set_theme(self, new_theme):
        pass


class _DrawerFactory(UiDialogDrawerFactory):
    def __init__(self, window: curses.window):
        self._window = window

    def create_ui_dialog_drawer(self, interpolator: Interpolator) -> UiDialogDrawer:
        return _Drawer(self._window, interpolator)


class _Drawer(UiDialogDrawer):
    def __init__(self, window, interpolator: Interpolator):
        self._window = window
        self._interpolator = interpolator
        self._index_vertical = 0
        self._index_horizontal = 0

    def start(self, data):
        self._window.clear()
        self._index_vertical = 0
        self._index_horizontal = 0
        if 'header' in data:
            self._window.addstr(0, 1, self._interpolator.interpolate(data['header']), curses.A_NORMAL)
            self._index_vertical += 1

    def add_text_line(self, text):
        self._window.addstr(self._index_vertical, 1, self._interpolator.interpolate(text), curses.A_NORMAL)
        self._index_vertical += 1

    def add_menu_entry(self, option, info, is_selected=False):
        mode = curses.A_REVERSE if is_selected else curses.A_NORMAL
        self._window.addstr(self._index_vertical, 1, self._interpolator.interpolate(option), mode)
        self._window.addstr(self._index_vertical, 30, self._interpolator.interpolate(info), mode)
        self._index_vertical += 1

    def add_action(self, action, is_selected=False):
        mode = curses.A_REVERSE if is_selected else curses.A_NORMAL
        self._window.addstr(self._index_vertical, 1 + 30 * self._index_horizontal, self._interpolator.interpolate(action), mode)
        self._index_horizontal += 1

    def paint(self) -> int:
        return self._window.getch()

    def clear(self) -> None:
        pass
