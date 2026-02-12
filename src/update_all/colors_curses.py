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
    LINK_COLOR = 0
    DEVICE_LOGIN_BACKGROUND_COLOR = 0
    DEVICE_LOGIN_TEXT_COLOR = 0
    DEVICE_LOGIN_TEXT_EXTRA_ATTR = 0
    DEVICE_LOGIN_HEADER_COLOR = 0
    DEVICE_LOGIN_LINK_COLOR = 0
    DEVICE_LOGIN_LINK_EXTRA_ATTR = 0
    LOG_VIEWER_BACKGROUND_COLOR = 0
    LOG_VIEWER_TEXT_COLOR = 0
    LOG_VIEWER_SYMBOL_COLOR = 0


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
    elif theme == 'Bloody Amber': return BloodyAmberColorTheme()
    elif theme == 'Mainframe': return MainframeColorTheme()
    elif theme == 'Aurora': return AuroraColorTheme()
    elif theme == 'Neon Noir': return NeonNoirColorTheme()
    elif theme == 'Mono': return MonoColorTheme()
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
        colors.LINK_COLOR = color_pair[cyan][black]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_LINK_EXTRA_ATTR = curses.A_DIM
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[blue][blue]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[white][blue]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[cyan][blue]

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
        colors.LINK_COLOR = color_pair[blue][white]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_LINK_EXTRA_ATTR = curses.A_DIM
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[blue][blue]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[white][blue]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[cyan][blue]

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
        colors.LINK_COLOR = color_pair[blue][white]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_LINK_EXTRA_ATTR = curses.A_DIM
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[black][black]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[white][black]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[white][black]

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
        colors.LINK_COLOR = color_pair[blue][white]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_LINK_EXTRA_ATTR = curses.A_DIM
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[black][black]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[white][black]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[white][black]


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
        colors.LINK_COLOR = color_pair[green][black]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[cyan][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[cyan][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[cyan][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[white][black]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[black][black]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[cyan][black]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[white][black]

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
        colors.LINK_COLOR = color_pair[green][black]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[yellow][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[yellow][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[yellow][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[white][black]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[black][black]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[yellow][black]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[white][black]

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
        colors.LINK_COLOR = color_pair[cyan][black]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[red][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[red][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[red][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[white][black]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[black][black]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[red][black]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[white][black]


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
        colors.LINK_COLOR = color_pair[blue][cyan]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[black][cyan]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[black][cyan]
        colors.DEVICE_LOGIN_TEXT_EXTRA_ATTR = curses.A_DIM
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[black][cyan]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[black][cyan]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[cyan][cyan]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[black][cyan]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[white][cyan]

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
        colors.LINK_COLOR = color_pair[blue][cyan]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[red][cyan]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[red][cyan]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[red][cyan]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[blue][cyan]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[cyan][cyan]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[red][cyan]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[white][cyan]

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
        colors.LINK_COLOR = color_pair[yellow][red]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[cyan][red]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[cyan][red]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[cyan][red]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[yellow][red]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[red][red]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[cyan][red]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[white][red]


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
        colors.LINK_COLOR = color_pair[blue][white]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[white][white]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[black][white]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[black][white]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[black][white]
        colors.DEVICE_LOGIN_LINK_EXTRA_ATTR = curses.A_DIM
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[white][white]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[black][white]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[black][white]

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
        colors.LINK_COLOR = color_pair[blue][white]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[black][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[blue][black]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[black][black]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[white][black]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[white][black]

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
        colors.LINK_COLOR = color_pair[blue][white]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[red][red]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[white][red]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[white][red]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[cyan][red]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[red][red]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[white][red]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[white][red]


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

        colors.SYMBOL_TILDE_COLOR = color_pair[black if self._box is not black else blue][self._box]
        colors.SYMBOL_AT_COLOR = color_pair[red if self._box is not red else black][self._box]
        colors.COMMON_TEXT_COLOR = color_pair[self._text][self._box]
        colors.LINK_COLOR = color_pair[cyan if self._box is not cyan else blue][self._box]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[self._box][self._background]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[self._box][self._background]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[self._box][self._background]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[black][self._background]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[self._background][self._background]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[self._box][self._background]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[black][self._background]

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
        colors.LINK_COLOR = color_pair[cyan][black]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[black][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[cyan][black]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[black][black]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[white][black]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[white][black]

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
        colors.LINK_COLOR = color_pair[cyan][black]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[black][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[red][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[red][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[cyan][black]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[black][black]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[red][black]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[white][black]


class BloodyAmberColorTheme(ColorTheme):
    def viewer(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[yellow][black]
        colors.BOX_BACKGROUND_COLOR = color_pair[yellow][black]
        colors.HEADER_LINE_COLOR = color_pair[yellow][black]
        colors.HEADER_COLOR = color_pair[yellow][black]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[black][yellow]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[black][yellow]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[black][yellow]

        colors.OPTION_UNSELECTED_COLOR = color_pair[yellow][black]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[yellow][black]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[black][yellow]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[black][yellow]

        colors.UNSELECTED_ACTION_COLOR = color_pair[yellow][black]

        colors.SYMBOL_TILDE_COLOR = color_pair[red][black]
        colors.SYMBOL_AT_COLOR = color_pair[red][black]
        colors.COMMON_TEXT_COLOR = color_pair[yellow][black]
        colors.LINK_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[yellow][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[yellow][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[yellow][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[white][black]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[yellow][yellow]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[black][yellow]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[red][yellow]

    def standard(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[yellow][black]
        colors.BOX_BACKGROUND_COLOR = color_pair[yellow][yellow]
        colors.HEADER_LINE_COLOR = color_pair[yellow][yellow]
        colors.HEADER_COLOR = color_pair[red][yellow]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[red][black]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[yellow][black]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[yellow][black]

        colors.OPTION_UNSELECTED_COLOR = color_pair[black][yellow]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[red][yellow]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[yellow][black]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[yellow][black]

        colors.UNSELECTED_ACTION_COLOR = color_pair[black][yellow]

        colors.SYMBOL_TILDE_COLOR = color_pair[blue][yellow]
        colors.SYMBOL_AT_COLOR = color_pair[red][yellow]
        colors.COMMON_TEXT_COLOR = color_pair[black][yellow]
        colors.LINK_COLOR = color_pair[blue][yellow]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[yellow][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[yellow][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[green][black]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[black][black]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[yellow][black]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[green][black]

    def black(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[red][black]
        colors.BOX_BACKGROUND_COLOR = color_pair[yellow][yellow]
        colors.HEADER_LINE_COLOR = color_pair[yellow][yellow]
        colors.HEADER_COLOR = color_pair[red][yellow]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[yellow][red]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[yellow][red]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[yellow][red]

        colors.OPTION_UNSELECTED_COLOR = color_pair[red][yellow]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[black][yellow]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[yellow][red]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[yellow][red]

        colors.UNSELECTED_ACTION_COLOR = color_pair[red][yellow]

        colors.SYMBOL_TILDE_COLOR = color_pair[black][yellow]
        colors.SYMBOL_AT_COLOR = color_pair[black][yellow]
        colors.COMMON_TEXT_COLOR = color_pair[red][yellow]
        colors.LINK_COLOR = color_pair[black][yellow]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[red][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[red][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[red][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[yellow][black]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[yellow][yellow]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[red][yellow]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[black][yellow]

    def red(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[red][black]
        colors.BOX_BACKGROUND_COLOR = color_pair[red][red]
        colors.HEADER_LINE_COLOR = color_pair[red][red]
        colors.HEADER_COLOR = color_pair[yellow][red]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[yellow][black]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[red][black]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[red][black]

        colors.OPTION_UNSELECTED_COLOR = color_pair[black][red]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[yellow][red]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[red][black]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[red][black]

        colors.UNSELECTED_ACTION_COLOR = color_pair[black][red]

        colors.SYMBOL_TILDE_COLOR = color_pair[yellow][red]
        colors.SYMBOL_AT_COLOR = color_pair[white][red]
        colors.COMMON_TEXT_COLOR = color_pair[black][red]
        colors.LINK_COLOR = color_pair[yellow][red]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[red][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[red][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[red][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[yellow][black]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[yellow][yellow]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[red][yellow]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[black][yellow]


class MainframeColorTheme(ColorTheme):
    def viewer(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[green][black]
        colors.BOX_BACKGROUND_COLOR = color_pair[green][black]
        colors.HEADER_LINE_COLOR = color_pair[green][black]
        colors.HEADER_COLOR = color_pair[green][black]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[black][green]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[black][green]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[black][green]

        colors.OPTION_UNSELECTED_COLOR = color_pair[green][black]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[green][black]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[black][green]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[black][green]

        colors.UNSELECTED_ACTION_COLOR = color_pair[green][black]

        colors.SYMBOL_TILDE_COLOR = color_pair[cyan][black]
        colors.SYMBOL_AT_COLOR = color_pair[yellow][black]
        colors.COMMON_TEXT_COLOR = color_pair[green][black]
        colors.LINK_COLOR = color_pair[cyan][black]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[green][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[green][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[green][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[cyan][black]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[black][black]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[green][black]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[cyan][black]

    def standard(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[black][black]
        colors.BOX_BACKGROUND_COLOR = color_pair[black][black]
        colors.HEADER_LINE_COLOR = color_pair[black][black]
        colors.HEADER_COLOR = color_pair[green][black]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[black][green]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[black][green]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[black][green]

        colors.OPTION_UNSELECTED_COLOR = color_pair[green][black]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[green][black]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[black][green]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[black][green]

        colors.UNSELECTED_ACTION_COLOR = color_pair[green][black]

        colors.SYMBOL_TILDE_COLOR = color_pair[cyan][black]
        colors.SYMBOL_AT_COLOR = color_pair[yellow][black]
        colors.COMMON_TEXT_COLOR = color_pair[green][black]
        colors.LINK_COLOR = color_pair[cyan][black]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[green][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[green][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[green][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[cyan][black]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[black][black]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[green][black]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[cyan][black]

    def black(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[green][black]
        colors.BOX_BACKGROUND_COLOR = color_pair[green][black]
        colors.HEADER_LINE_COLOR = color_pair[green][black]
        colors.HEADER_COLOR = color_pair[green][black]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[black][green]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[black][green]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[black][green]

        colors.OPTION_UNSELECTED_COLOR = color_pair[green][black]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[white][black]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[black][green]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[black][green]

        colors.UNSELECTED_ACTION_COLOR = color_pair[green][black]

        colors.SYMBOL_TILDE_COLOR = color_pair[cyan][black]
        colors.SYMBOL_AT_COLOR = color_pair[yellow][black]
        colors.COMMON_TEXT_COLOR = color_pair[green][black]
        colors.LINK_COLOR = color_pair[cyan][black]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[green][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[green][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[green][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[cyan][black]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[black][black]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[green][black]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[cyan][black]

    def red(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[red][black]
        colors.BOX_BACKGROUND_COLOR = color_pair[red][black]
        colors.HEADER_LINE_COLOR = color_pair[red][black]
        colors.HEADER_COLOR = color_pair[red][black]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[black][red]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[black][red]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[black][red]

        colors.OPTION_UNSELECTED_COLOR = color_pair[red][black]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[green][black]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[black][red]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[black][red]

        colors.UNSELECTED_ACTION_COLOR = color_pair[red][black]

        colors.SYMBOL_TILDE_COLOR = color_pair[green][black]
        colors.SYMBOL_AT_COLOR = color_pair[yellow][black]
        colors.COMMON_TEXT_COLOR = color_pair[red][black]
        colors.LINK_COLOR = color_pair[green][black]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[red][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[red][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[red][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[green][black]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[black][black]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[red][black]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[green][black]


class AuroraColorTheme(ColorTheme):
    def viewer(self):
        self.standard()

    def standard(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[yellow][blue]
        colors.BOX_BACKGROUND_COLOR = color_pair[yellow][blue]
        colors.HEADER_LINE_COLOR = color_pair[yellow][blue]
        colors.HEADER_COLOR = color_pair[white][blue]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[white][yellow]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[blue][yellow]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[blue][yellow]

        colors.OPTION_UNSELECTED_COLOR = color_pair[yellow][blue]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[white][blue]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[blue][yellow]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[blue][yellow]

        colors.UNSELECTED_ACTION_COLOR = color_pair[yellow][blue]

        colors.SYMBOL_TILDE_COLOR = color_pair[cyan][blue]
        colors.SYMBOL_AT_COLOR = color_pair[green][blue]
        colors.COMMON_TEXT_COLOR = color_pair[yellow][blue]
        colors.LINK_COLOR = color_pair[cyan][blue]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[yellow][blue]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[yellow][blue]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[white][blue]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[cyan][blue]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[blue][blue]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[yellow][blue]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[cyan][blue]

    def black(self):
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

        colors.SYMBOL_TILDE_COLOR = color_pair[blue][black]
        colors.SYMBOL_AT_COLOR = color_pair[yellow][black]
        colors.COMMON_TEXT_COLOR = color_pair[cyan][black]
        colors.LINK_COLOR = color_pair[blue][black]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[cyan][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[cyan][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[cyan][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[blue][black]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[black][black]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[cyan][black]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[blue][black]

    def red(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[red][blue]
        colors.BOX_BACKGROUND_COLOR = color_pair[red][blue]
        colors.HEADER_LINE_COLOR = color_pair[red][blue]
        colors.HEADER_COLOR = color_pair[red][blue]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[blue][red]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[blue][red]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[blue][red]

        colors.OPTION_UNSELECTED_COLOR = color_pair[red][blue]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[white][blue]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[blue][red]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[blue][red]

        colors.UNSELECTED_ACTION_COLOR = color_pair[red][blue]

        colors.SYMBOL_TILDE_COLOR = color_pair[cyan][blue]
        colors.SYMBOL_AT_COLOR = color_pair[yellow][blue]
        colors.COMMON_TEXT_COLOR = color_pair[red][blue]
        colors.LINK_COLOR = color_pair[cyan][blue]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[red][blue]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[red][blue]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[red][blue]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[cyan][blue]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[blue][blue]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[red][blue]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[cyan][blue]


class NeonNoirColorTheme(ColorTheme):
    def viewer(self):
        self.standard()

    def standard(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[black][black]
        colors.BOX_BACKGROUND_COLOR = color_pair[black][black]
        colors.HEADER_LINE_COLOR = color_pair[magenta][black]
        colors.HEADER_COLOR = color_pair[white][black]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[black][magenta]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[black][magenta]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[black][magenta]

        colors.OPTION_UNSELECTED_COLOR = color_pair[magenta][black]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[cyan][black]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[black][magenta]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[cyan][black]

        colors.UNSELECTED_ACTION_COLOR = color_pair[magenta][black]

        colors.SYMBOL_TILDE_COLOR = color_pair[cyan][black]
        colors.SYMBOL_AT_COLOR = color_pair[white][black]
        colors.COMMON_TEXT_COLOR = color_pair[magenta][black]
        colors.LINK_COLOR = color_pair[green][black]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[magenta][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[magenta][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[cyan][black]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[black][black]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[magenta][black]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[cyan][black]

    def black(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[yellow][black]
        colors.BOX_BACKGROUND_COLOR = color_pair[yellow][black]
        colors.HEADER_LINE_COLOR = color_pair[yellow][black]
        colors.HEADER_COLOR = color_pair[yellow][black]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[black][yellow]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[black][yellow]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[black][yellow]

        colors.OPTION_UNSELECTED_COLOR = color_pair[yellow][black]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[magenta][black]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[black][yellow]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[black][yellow]

        colors.UNSELECTED_ACTION_COLOR = color_pair[yellow][black]

        colors.SYMBOL_TILDE_COLOR = color_pair[magenta][black]
        colors.SYMBOL_AT_COLOR = color_pair[white][black]
        colors.COMMON_TEXT_COLOR = color_pair[yellow][black]
        colors.LINK_COLOR = color_pair[magenta][black]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[yellow][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[yellow][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[yellow][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[magenta][black]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[black][black]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[yellow][black]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[magenta][black]

    def red(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[red][black]
        colors.BOX_BACKGROUND_COLOR = color_pair[red][black]
        colors.HEADER_LINE_COLOR = color_pair[red][black]
        colors.HEADER_COLOR = color_pair[red][black]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[black][red]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[black][red]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[black][red]

        colors.OPTION_UNSELECTED_COLOR = color_pair[red][black]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[magenta][black]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[black][red]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[black][red]

        colors.UNSELECTED_ACTION_COLOR = color_pair[red][black]

        colors.SYMBOL_TILDE_COLOR = color_pair[magenta][black]
        colors.SYMBOL_AT_COLOR = color_pair[yellow][black]
        colors.COMMON_TEXT_COLOR = color_pair[red][black]
        colors.LINK_COLOR = color_pair[magenta][black]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[red][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[red][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[red][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[magenta][black]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[black][black]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[red][black]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[magenta][black]


class MonoColorTheme(ColorTheme):
    def viewer(self):
        self.standard()

    def standard(self):
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

        colors.SYMBOL_TILDE_COLOR = color_pair[white][black]
        colors.SYMBOL_AT_COLOR = color_pair[white][black]
        colors.COMMON_TEXT_COLOR = color_pair[white][black]
        colors.LINK_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[white][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[white][black]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[black][black]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[white][black]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[white][black]

    def black(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[yellow][black]
        colors.BOX_BACKGROUND_COLOR = color_pair[yellow][black]
        colors.HEADER_LINE_COLOR = color_pair[yellow][black]
        colors.HEADER_COLOR = color_pair[yellow][black]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[black][yellow]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[black][yellow]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[black][yellow]

        colors.OPTION_UNSELECTED_COLOR = color_pair[yellow][black]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[yellow][black]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[black][yellow]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[black][yellow]

        colors.UNSELECTED_ACTION_COLOR = color_pair[yellow][black]

        colors.SYMBOL_TILDE_COLOR = color_pair[yellow][black]
        colors.SYMBOL_AT_COLOR = color_pair[yellow][black]
        colors.COMMON_TEXT_COLOR = color_pair[yellow][black]
        colors.LINK_COLOR = color_pair[yellow][black]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[yellow][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[yellow][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[yellow][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[yellow][black]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[black][black]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[yellow][black]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[yellow][black]

    def red(self):
        colors.WINDOW_BACKGROUND_COLOR = color_pair[red][black]
        colors.BOX_BACKGROUND_COLOR = color_pair[red][black]
        colors.HEADER_LINE_COLOR = color_pair[red][black]
        colors.HEADER_COLOR = color_pair[red][black]

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = color_pair[black][red]
        colors.SELECTED_OPTION_INFO_COLOR = color_pair[black][red]
        colors.SELECTED_OPTION_TEXT_COLOR = color_pair[black][red]

        colors.OPTION_UNSELECTED_COLOR = color_pair[red][black]
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = color_pair[red][black]

        colors.SELECTED_ACTION_INTERIOR_COLOR = color_pair[black][red]
        colors.SELECTED_ACTION_BORDER_COLOR = color_pair[black][red]

        colors.UNSELECTED_ACTION_COLOR = color_pair[red][black]

        colors.SYMBOL_TILDE_COLOR = color_pair[red][black]
        colors.SYMBOL_AT_COLOR = color_pair[red][black]
        colors.COMMON_TEXT_COLOR = color_pair[red][black]
        colors.LINK_COLOR = color_pair[red][black]
        colors.DEVICE_LOGIN_BACKGROUND_COLOR = color_pair[red][black]
        colors.DEVICE_LOGIN_TEXT_COLOR = color_pair[red][black]
        colors.DEVICE_LOGIN_HEADER_COLOR = color_pair[red][black]
        colors.DEVICE_LOGIN_LINK_COLOR = color_pair[red][black]
        colors.LOG_VIEWER_BACKGROUND_COLOR = color_pair[black][black]
        colors.LOG_VIEWER_TEXT_COLOR = color_pair[red][black]
        colors.LOG_VIEWER_SYMBOL_COLOR = color_pair[red][black]
