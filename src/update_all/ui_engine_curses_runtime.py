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
from typing import Callable, Union

from update_all.ui_engine import UiRuntime
from update_all.ui_model_utilities import Key


class CursesRuntime(UiRuntime):
    _screen: curses.window

    @property
    def screen(self) -> curses.window:
        if self._screen is None:
            raise RuntimeError("CursesRuntime has not been initialised")

        return self._screen

    def initialize_runtime(self, cb: Callable[[], None]) -> None:
        def loader(screen):
            self._screen = screen
            cb()

        curses.wrapper(loader)

    def update(self) -> None:
        curses.doupdate()

    def interrupt(self) -> None:
        curses.endwin()

    def resume(self) -> None:
        curses.initscr()


def read_key(window: curses.window) -> Union[Key, int]:
    key = window.getch()
    if key == curses.KEY_UP:
        return Key.UP
    elif key == curses.KEY_DOWN:
        return Key.DOWN
    elif key == curses.KEY_LEFT:
        return Key.LEFT
    elif key == curses.KEY_RIGHT:
        return Key.RIGHT
    elif key in [curses.KEY_ENTER, ord("\n"), ord(" ")]:
        return Key.ENTER

    return key
