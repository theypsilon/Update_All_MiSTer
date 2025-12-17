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
import abc

class ColorConfiguration:
    FIRST_OPTION_KEY_UNSELECTED_COLOR = 0
    FIRST_OPTION_KEY_SELECTED_COLOR = 0
    WINDOW_BACKGROUND_COLOR = 0
    SELECTED_OPTION_INFO_COLOR = 0
    SELECTED_ACTION_BORDER_COLOR = 0
    HEADER_COLOR = 0
    OPTION_UNSELECTED_COLOR = 0
    SYMBOL_TILDE_COLOR = 0
    SELECTED_ACTION_INTERIOR_COLOR = 0
    SELECTED_OPTION_TEXT_COLOR = 0
    SYMBOL_AT_COLOR = 0
    BOX_BACKGROUND_COLOR = 0
    HEADER_LINE_COLOR = 0
    COMMON_TEXT_COLOR = 0
    UNSELECTED_ACTION_COLOR = 0


colors = ColorConfiguration()

white = curses.COLOR_WHITE
red = curses.COLOR_RED
blue = curses.COLOR_BLUE
cyan = curses.COLOR_CYAN
black = curses.COLOR_BLACK
yellow = curses.COLOR_YELLOW
green = curses.COLOR_GREEN
magenta = curses.COLOR_MAGENTA

color_pair = {}

def init_colors():
    if len(color_pair) > 0:
        return

    curses.start_color()

    all_colors = [white, red, blue, cyan, black, yellow, green, magenta]

    i = 1
    for color_left in all_colors:
        color_pair[color_left] = {}
        for color_right in all_colors:
            color_pair[color_left][color_right] = i
            curses.init_pair(i, color_left, color_right)
            i += 1


class ColorTheme(abc.ABC):
    def standard(self): pass
    def black(self): pass
    def red(self): pass
    def viewer(self): pass


def make_color_theme(theme: str) -> ColorTheme:
    if theme == 'Cyan Night': return CyanNightColorTheme()
    elif theme == 'Japan': return Custom3ColorTheme(white, red, white)
    elif theme == 'Aquamarine': return AquamarineColorTheme()
    elif theme == 'Clean Wall': return CleanWallColorTheme()
    else: return BlueInstallerColorTheme()


class BlueInstallerColorTheme(ColorTheme):
    def viewer(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[white][black]
        colors.BOX_BACKGROUND_COLOR = color_pair[white][black]
        colors.HEADER_LINE_COLOR = color_pair[white][black]
        colors.HEADER_COLOR = color_pair[white][black]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[black][white]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[black][white]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[black][white]

        colors.OPTION_UNSELECTED_COLOR = color_pair[white][black]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[white][black]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[black][white]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[black][white]

        colors.UNSELECTED_ACTION_COLOR = color_pair[white][black]

        colors.SYMBOL_TILDE_COLOR = color_pair[yellow][black]
        colors.SYMBOL_AT_COLOR = color_pair[white][black]
        colors.COMMON_TEXT_COLOR = color_pair[white][black]

    def standard(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[white][blue]
        colors.BOX_BACKGROUND_COLOR = color_pair[black][white]
        colors.HEADER_LINE_COLOR = color_pair[black][white]
        colors.HEADER_COLOR = color_pair[blue][white]

        colors.SELECTED_OPTION_INFO_COLOR = color_pair[white][blue]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[cyan][blue]
        colors.OPTION_UNSELECTED_COLOR = color_pair[blue][white]

        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[red][white]
        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[red][blue]

        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[white][blue]
        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[cyan][blue]
        colors.UNSELECTED_ACTION_COLOR = color_pair[black][white]

        colors.SYMBOL_AT_COLOR = color_pair[red][white]
        colors.SYMBOL_TILDE_COLOR = color_pair[blue][white]
        colors.COMMON_TEXT_COLOR = color_pair[black][white]

    def black(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[white][black]
        colors.BOX_BACKGROUND_COLOR = color_pair[black][white]
        colors.HEADER_LINE_COLOR = color_pair[black][white]
        colors.HEADER_COLOR = color_pair[black][white]

        colors.SELECTED_OPTION_INFO_COLOR = color_pair[white][black]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[cyan][blue]
        colors.OPTION_UNSELECTED_COLOR = color_pair[blue][white]

        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[red][white]
        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[red][blue]

        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[white][black]
        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[white][black]
        colors.UNSELECTED_ACTION_COLOR = color_pair[black][white]

        colors.SYMBOL_AT_COLOR = color_pair[cyan][white]
        colors.SYMBOL_TILDE_COLOR = color_pair[blue][white]
        colors.COMMON_TEXT_COLOR = color_pair[black][white]

    def red(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[white][red]
        colors.BOX_BACKGROUND_COLOR = color_pair[black][white]
        colors.HEADER_LINE_COLOR = color_pair[black][white]
        colors.HEADER_COLOR = color_pair[red][white]

        colors.SELECTED_OPTION_INFO_COLOR = color_pair[white][red]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[white][red]
        colors.OPTION_UNSELECTED_COLOR = color_pair[black][white]

        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[red][white]
        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[white][red]

        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[white][red]
        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[white][red]
        colors.UNSELECTED_ACTION_COLOR = color_pair[red][white]

        colors.SYMBOL_AT_COLOR = color_pair[red][white]
        colors.SYMBOL_TILDE_COLOR = color_pair[blue][white]
        colors.COMMON_TEXT_COLOR = color_pair[black][white]


class CyanNightColorTheme(ColorTheme):
    def viewer(self):
        self.standard()

    def standard(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[cyan][black]
        colors.BOX_BACKGROUND_COLOR = color_pair[cyan][black]
        colors.HEADER_LINE_COLOR = color_pair[cyan][black]
        colors.HEADER_COLOR = color_pair[cyan][black]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[black][cyan]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[black][cyan]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[black][cyan]

        colors.OPTION_UNSELECTED_COLOR = color_pair[cyan][black]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[white][black]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[black][cyan]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[black][cyan]

        colors.UNSELECTED_ACTION_COLOR = color_pair[cyan][black]

        colors.SYMBOL_TILDE_COLOR = color_pair[yellow][black]
        colors.SYMBOL_AT_COLOR = color_pair[white][black]
        colors.COMMON_TEXT_COLOR = color_pair[cyan][black]

    def black(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[yellow][black]
        colors.BOX_BACKGROUND_COLOR = color_pair[yellow][black]
        colors.HEADER_LINE_COLOR = color_pair[yellow][black]
        colors.HEADER_COLOR = color_pair[yellow][black]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[black][yellow]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[black][yellow]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[black][yellow]

        colors.OPTION_UNSELECTED_COLOR = color_pair[yellow][black]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[white][black]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[black][yellow]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[black][yellow]

        colors.UNSELECTED_ACTION_COLOR = color_pair[yellow][black]

        colors.SYMBOL_TILDE_COLOR = color_pair[cyan][black]
        colors.SYMBOL_AT_COLOR = color_pair[white][black]
        colors.COMMON_TEXT_COLOR = color_pair[yellow][black]

    def red(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[red][black]
        colors.BOX_BACKGROUND_COLOR = color_pair[red][black]
        colors.HEADER_LINE_COLOR = color_pair[red][black]
        colors.HEADER_COLOR = color_pair[red][black]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[black][red]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[black][red]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[black][red]

        colors.OPTION_UNSELECTED_COLOR = color_pair[red][black]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[white][black]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[black][red]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[black][red]

        colors.UNSELECTED_ACTION_COLOR = color_pair[red][black]

        colors.SYMBOL_TILDE_COLOR = color_pair[cyan][black]
        colors.SYMBOL_AT_COLOR = color_pair[white][black]
        colors.COMMON_TEXT_COLOR = color_pair[red][black]


class AquamarineColorTheme(ColorTheme):
    def viewer(self):
        self.standard()

    def standard(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[black][cyan]
        colors.BOX_BACKGROUND_COLOR = color_pair[black][cyan]
        colors.HEADER_LINE_COLOR = color_pair[cyan][cyan]
        colors.HEADER_COLOR = color_pair[black][cyan]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[black][cyan]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[cyan][black]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[cyan][black]

        colors.OPTION_UNSELECTED_COLOR = color_pair[black][cyan]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[cyan][black]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[cyan][black]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[cyan][black]

        colors.UNSELECTED_ACTION_COLOR = color_pair[black][cyan]

        colors.SYMBOL_TILDE_COLOR = color_pair[blue][cyan]
        colors.SYMBOL_AT_COLOR = color_pair[magenta][cyan]
        colors.COMMON_TEXT_COLOR = color_pair[black][cyan]

    def black(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[red][cyan]
        colors.BOX_BACKGROUND_COLOR = color_pair[red][cyan]
        colors.HEADER_LINE_COLOR = color_pair[red][cyan]
        colors.HEADER_COLOR = color_pair[red][cyan]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[cyan][red]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[cyan][red]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[cyan][red]

        colors.OPTION_UNSELECTED_COLOR = color_pair[red][cyan]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[cyan][red]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[cyan][red]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[cyan][red]

        colors.UNSELECTED_ACTION_COLOR = color_pair[red][cyan]

        colors.SYMBOL_TILDE_COLOR = color_pair[blue][cyan]
        colors.SYMBOL_AT_COLOR = color_pair[magenta][cyan]
        colors.COMMON_TEXT_COLOR = color_pair[red][cyan]

    def red(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[cyan][red]
        colors.BOX_BACKGROUND_COLOR = color_pair[cyan][red]
        colors.HEADER_LINE_COLOR = color_pair[cyan][red]
        colors.HEADER_COLOR = color_pair[cyan][red]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[red][cyan]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[red][cyan]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[red][cyan]

        colors.OPTION_UNSELECTED_COLOR = color_pair[cyan][red]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[red][cyan]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[red][cyan]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[red][cyan]

        colors.UNSELECTED_ACTION_COLOR = color_pair[cyan][red]

        colors.SYMBOL_TILDE_COLOR = color_pair[green][red]
        colors.SYMBOL_AT_COLOR = color_pair[yellow][red]
        colors.COMMON_TEXT_COLOR = color_pair[cyan][red]


class CleanWallColorTheme(ColorTheme):
    def viewer(self):
        self.standard()

    def standard(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[white][white]
        colors.BOX_BACKGROUND_COLOR = color_pair[white][white]
        colors.HEADER_LINE_COLOR = color_pair[black][white]
        colors.HEADER_COLOR = color_pair[black][white]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[white][black]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[white][black]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[white][black]

        colors.OPTION_UNSELECTED_COLOR = color_pair[black][white]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[black][white]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[white][black]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[white][black]

        colors.UNSELECTED_ACTION_COLOR = color_pair[black][white]

        colors.SYMBOL_TILDE_COLOR = color_pair[blue][white]
        colors.SYMBOL_AT_COLOR = color_pair[magenta][white]
        colors.COMMON_TEXT_COLOR = color_pair[black][white]

    def black(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[black][black]
        colors.BOX_BACKGROUND_COLOR = color_pair[white][white]
        colors.HEADER_LINE_COLOR = color_pair[black][white]
        colors.HEADER_COLOR = color_pair[black][white]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[white][black]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[white][black]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[white][black]

        colors.OPTION_UNSELECTED_COLOR = color_pair[black][white]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[black][white]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[white][black]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[white][black]

        colors.UNSELECTED_ACTION_COLOR = color_pair[black][white]

        colors.SYMBOL_TILDE_COLOR = color_pair[blue][white]
        colors.SYMBOL_AT_COLOR = color_pair[magenta][white]
        colors.COMMON_TEXT_COLOR = color_pair[black][white]

    def red(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[red][red]
        colors.BOX_BACKGROUND_COLOR = color_pair[white][white]
        colors.HEADER_LINE_COLOR = color_pair[black][white]
        colors.HEADER_COLOR = color_pair[black][white]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[white][black]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[white][black]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[white][black]

        colors.OPTION_UNSELECTED_COLOR = color_pair[black][white]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[black][white]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[white][black]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[white][black]

        colors.UNSELECTED_ACTION_COLOR = color_pair[black][white]

        colors.SYMBOL_TILDE_COLOR = color_pair[blue][white]
        colors.SYMBOL_AT_COLOR = color_pair[magenta][white]
        colors.COMMON_TEXT_COLOR = color_pair[black][white]


class Custom3ColorTheme(ColorTheme):
    def __init__(self, background, box, text):
        self._background = background
        self._box = box
        self._text = text

    def viewer(self):
        self.standard()

    def standard(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[self._box][self._background]
        colors.BOX_BACKGROUND_COLOR = color_pair[self._box][self._box]
        colors.HEADER_LINE_COLOR = color_pair[self._box][self._box]
        colors.HEADER_COLOR = color_pair[self._text][self._box]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[self._text][self._box]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[self._box][self._text]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[self._box][self._text]

        colors.OPTION_UNSELECTED_COLOR = color_pair[self._text][self._box]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[self._text][self._box]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[self._box][self._text]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[self._text][self._box]

        colors.UNSELECTED_ACTION_COLOR = color_pair[self._text][self._box]

        colors.SYMBOL_TILDE_COLOR = color_pair[blue if self._box is not blue else black][self._box]
        colors.SYMBOL_AT_COLOR = color_pair[red if self._box is not red else black][self._box]
        colors.COMMON_TEXT_COLOR = color_pair[self._text][self._box]

    def black(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[black][black]
        colors.BOX_BACKGROUND_COLOR = color_pair[black][black]
        colors.HEADER_LINE_COLOR = color_pair[black][black]
        colors.HEADER_COLOR = color_pair[white][black]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[white][black]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[black][white]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[black][white]

        colors.OPTION_UNSELECTED_COLOR = color_pair[white][black]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[white][black]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[black][white]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[white][black]

        colors.UNSELECTED_ACTION_COLOR = color_pair[white][black]

        colors.SYMBOL_TILDE_COLOR = color_pair[cyan][black]
        colors.SYMBOL_AT_COLOR = color_pair[red][black]
        colors.COMMON_TEXT_COLOR = color_pair[white][black]

    def red(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[black][black]
        colors.BOX_BACKGROUND_COLOR = color_pair[black][black]
        colors.HEADER_LINE_COLOR = color_pair[black][black]
        colors.HEADER_COLOR = color_pair[red][black]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[red][black]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[black][red]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[black][red]

        colors.OPTION_UNSELECTED_COLOR = color_pair[red][black]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[red][black]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[black][red]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[red][black]

        colors.UNSELECTED_ACTION_COLOR = color_pair[red][black]

        colors.SYMBOL_TILDE_COLOR = color_pair[cyan][black]
        colors.SYMBOL_AT_COLOR = color_pair[red][black]
        colors.COMMON_TEXT_COLOR = color_pair[red][black]
