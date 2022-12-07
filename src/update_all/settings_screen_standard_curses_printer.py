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
from typing import Tuple

from update_all.settings_screen_printer import SettingsScreenPrinter, SettingsScreenThemeManager
from update_all.ui_engine import Interpolator
from update_all.ui_engine_curses_runtime import CursesRuntime
from update_all.ui_engine_dialog_application import UiDialogDrawer, UiDialogDrawerFactory


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


class SettingsScreenStandardCursesPrinter(CursesRuntime, SettingsScreenPrinter):
    def initialize_screen(self) -> Tuple[UiDialogDrawerFactory, SettingsScreenThemeManager]:
        curses.start_color()

        all_colors = [white, red, blue, cyan, black, yellow, green, magenta]

        i = 1
        for color_left in all_colors:
            color_pair[color_left] = {}
            for color_right in all_colors:
                color_pair[color_left][color_right] = i
                curses.init_pair(i, color_left, color_right)
                i += 1

        layout = _Layout(self)
        return _DrawerFactory(self, layout), layout


class ColorTheme(abc.ABC):
    def standard(self): pass
    def black(self): pass
    def red(self): pass


class BlueInstallerColorTheme(ColorTheme):
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


class _Layout(SettingsScreenThemeManager):
    def __init__(self, runtime: CursesRuntime):
        self._runtime = runtime
        self._painted = False
        self._box_id = None
        self._current_theme = None
        self._current_sub_theme = None

    def set_theme(self, new_theme) -> None:
        if new_theme == self._current_theme:
            return

        self._current_theme = new_theme
        self._apply_theme()

    def set_sub_theme(self, new_sub_theme) -> None:
        if new_sub_theme == self._current_sub_theme:
            return

        self._current_sub_theme = new_sub_theme
        self._apply_theme()

    def _apply_theme(self) -> None:
        self._painted = False
        color_theme = self._get_color_theme()
        if self._current_sub_theme == 'black':
            color_theme.black()
        elif self._current_sub_theme == 'red':
            color_theme.red()
        else:
            color_theme.standard()

    def _get_color_theme(self) -> ColorTheme:
        if self._current_theme == 'Cyan Night': return CyanNightColorTheme()
        elif self._current_theme == 'Japan': return Custom3ColorTheme(white, red, white)
        elif self._current_theme == 'Aquamarine': return AquamarineColorTheme()
        elif self._current_theme == 'Clean Wall': return CleanWallColorTheme()
        else:
            return BlueInstallerColorTheme()

    def paint_layout(self, h: int, w: int, y: int, x: int, has_header: bool) -> None:
        box_id = f'{h}_{w}_{y}_{x}_{str(has_header)}'
        if self._painted and box_id == self._box_id:
            return

        self._painted = True
        self._box_id = box_id
        self._runtime.window.clear()
        self._runtime.window.bkgd(' ', curses.color_pair(colors.WINDOW_BACKGROUND_COLOR))
        if box_id == self._box_id:
            self._paint_box(h, w, y, x, has_header)

    def _paint_box(self, h: int, w: int, y: int, x: int, has_header: bool) -> None:
        screen = curses.initscr()
        if curses.LINES <= 15:  # @resolution: This is to move the texts a bit up in tiny resolutions.
            y -= 1
        try:
            box1 = screen.subwin(h, w, y, x)
            box1.clear()
            box1.attron(curses.color_pair(colors.BOX_BACKGROUND_COLOR))
            box1.bkgd(' ', curses.color_pair(colors.BOX_BACKGROUND_COLOR) | curses.A_NORMAL)
            box1.box()

            if has_header:
                screen.hline(y + 2, x + 1, curses.ACS_HLINE | curses.color_pair(colors.HEADER_LINE_COLOR), w - 2)

        except curses.error as _:
            box1 = screen.subwin(curses.LINES, curses.COLS, 0, 0)
            box1.clear()
            box1.attron(curses.color_pair(colors.BOX_BACKGROUND_COLOR))
            box1.bkgd(' ', curses.color_pair(colors.BOX_BACKGROUND_COLOR) | curses.A_NORMAL)
            box1.box()

    def reset(self) -> None:
        self._painted = False


class _DrawerFactory(UiDialogDrawerFactory):
    def __init__(self, runtime: CursesRuntime, layout: _Layout):
        self._runtime = runtime
        self._layout = layout

    def create_ui_dialog_drawer(self, interpolator: Interpolator) -> UiDialogDrawer:
        return _Drawer(self._runtime, self._layout, interpolator)


class _Drawer(UiDialogDrawer):
    def __init__(self, runtime: CursesRuntime, layout: _Layout, interpolator: Interpolator):
        self._runtime = runtime
        self._layout = layout
        self._interpolator = interpolator
        self._text_lines = []
        self._menu_entries = []
        self._actions = []
        self._effects = {}
        self._header = ''

    def start(self, data):
        self._text_lines = []
        self._menu_entries = []
        self._actions = []
        self._effects = {}

        self._header = ''
        if 'header' in data:
            self._header = self._interpolator.interpolate(data['header'])

        self._layout.set_sub_theme(data.get('alert_level', None))

    def add_text_line(self, text):
        interpolated_text = self._interpolator.interpolate(text)
        for line in interpolated_text.split('\n'):
            n = curses.COLS - 2
            for chunk in [line[i:i + n] for i in range(0, len(line), n)]:
                find_tilda = chunk.find('~')
                find_at = chunk.find('@')
                if find_tilda != -1 or find_at != -1:
                    chunk, effects = parse_effects(chunk)
                    self._effects[chunk] = effects

                self._text_lines.append(chunk)

    def add_menu_entry(self, option, info, is_selected=False):
        if curses.LINES <= 15 and option == '' and info == '' and not is_selected:
            return  # @resolution: This is to avoid text being cutoff off the screen in tiny resolutions.
        self._menu_entries.append((self._interpolator.interpolate(option), self._interpolator.interpolate(info), is_selected))

    def add_action(self, action, is_selected=False):
        self._actions.append((f'<{self._interpolator.interpolate(action)}>', is_selected))

    def add_inactive_action(self, length: int, is_selected=False):
        self._actions.append((' ' * (length + 2), is_selected))

    def paint(self) -> int:
        total_lines = len(self._text_lines) + len(self._menu_entries) + 1
        max_length_header = len(self._header)
        if max_length_header > 0:
            total_lines += 2

        if len(self._actions) > 0 and total_lines < curses.COLS:
            total_lines += 1

        offset_vertical = int(curses.LINES / 2 - total_lines / 2)

        offset_header = max(1, int(curses.COLS / 2 - max_length_header / 2))
        max_length_text_line = min(curses.COLS - 2, calculate_max_length_text_line(self._text_lines))

        offset_text_line = max(1, int(curses.COLS / 2 - max_length_text_line / 2))

        max_length_option = calculate_max_length_option(self._menu_entries)
        max_length_info =  calculate_max_length_info(self._menu_entries)
        max_menu_entry = max_length_option + 2 + max_length_info

        offset_menu = max(1, int(curses.COLS / 2 - max_menu_entry / 2))

        action_width = calculate_max_length_actions(self._actions) + 6
        max_length_actions = action_width * len(self._actions)
        offset_actions = int(curses.COLS / 2 - max_length_actions / 2)

        total_width = max(max(max_menu_entry, max_length_text_line), max(max_length_header, max_length_actions))
        offset_horizontal = min(min(offset_menu, offset_text_line), min(offset_actions, offset_header))

        self._layout.paint_layout(total_lines + 2, total_width + 2, offset_vertical - 1, offset_horizontal - 1, max_length_header> 0)

        line_index = offset_vertical

        if max_length_header > 0:
            self._write_line(line_index, offset_header, self._header, curses.A_NORMAL | curses.color_pair(colors.HEADER_COLOR))
            line_index += 2

        for line in self._text_lines:
            if line in self._effects:
                for mode, start, end in self._effects[line]:
                    self._write_line(line_index, offset_text_line + start, line[start:end], mode)

            else:
                self._write_line(line_index, offset_text_line, line, curses.A_NORMAL | curses.color_pair(colors.COMMON_TEXT_COLOR))
            line_index += 1

        for option, info, is_selected in self._menu_entries:
            if is_selected:
                mode = curses.A_NORMAL | curses.color_pair(colors.FIRST_OPTION_KEY_SELECTED_COLOR)
            else:
                mode = curses.A_NORMAL | curses.color_pair(colors.FIRST_OPTION_KEY_UNSELECTED_COLOR)

            self._write_line(line_index, offset_menu, option[0:1], mode)

            if is_selected:
                mode = curses.A_NORMAL | curses.color_pair(colors.SELECTED_OPTION_TEXT_COLOR)
            else:
                mode = curses.A_NORMAL | curses.color_pair(colors.OPTION_UNSELECTED_COLOR)

            self._write_line(line_index, offset_menu + 1, option[1:], mode)

            if is_selected:
                mode = curses.A_NORMAL | curses.color_pair(colors.SELECTED_OPTION_INFO_COLOR)
            else:
                mode = curses.A_NORMAL | curses.color_pair(colors.COMMON_TEXT_COLOR)
            self._write_line(line_index, offset_menu + max_length_option + 2, info, mode)
            line_index += 1

        if len(self._actions) > 0 and total_lines < curses.COLS:
            line_index += 1

        for action, is_selected in self._actions:
            if is_selected:
                self._write_line(line_index, offset_actions, action[0:1], curses.A_BLINK | curses.color_pair(colors.SELECTED_ACTION_BORDER_COLOR))
                self._write_line(line_index, offset_actions + 1, action[1:-1], curses.A_BLINK | curses.color_pair(colors.SELECTED_ACTION_INTERIOR_COLOR))
                self._write_line(line_index, offset_actions + len(action) - 1, action[-1:], curses.A_BLINK | curses.color_pair(colors.SELECTED_ACTION_BORDER_COLOR))
            else:
                self._write_line(line_index, offset_actions, action, curses.A_NORMAL | curses.color_pair(colors.UNSELECTED_ACTION_COLOR))
            offset_actions += action_width

        return self._runtime.read_key()

    def clear(self) -> None:
        self._layout.reset()

    def _write_line(self, y, x, text, mode):
        if curses.LINES <= 15:  #  @resolution: This is to move the texts a bit up in tiny resolutions.
            y -= 1
        if y < 0 or y >= curses.LINES:
            return
        if x < 0:
            text = text[-x:]
            x = 0
        if x + len(text) >= curses.COLS:
            text = text[0:(curses.COLS - x - 1)]
        self._runtime.window.addstr(y, x, text, mode)


def parse_effects(chunk):
    state = 0
    last = 0
    effects = []
    cursor = 0
    while cursor < len(chunk):
        char = chunk[cursor:cursor + 1]
        if state == 0:
            if char == '~':
                state = 1
                chunk = chunk[0:cursor] + chunk[cursor + 1:]
                effects.append((curses.color_pair(colors.COMMON_TEXT_COLOR) | curses.A_NORMAL, last, cursor))
                last = cursor
                continue
            elif char == '@':
                state = 2
                chunk = chunk[0:cursor] + chunk[cursor + 1:]
                effects.append((curses.color_pair(colors.COMMON_TEXT_COLOR) | curses.A_NORMAL, last, cursor))
                last = cursor
                continue

        elif state == 1:
            if char == '~':
                state = 0
                chunk = chunk[0:cursor] + chunk[cursor + 1:]
                effects.append((curses.color_pair(colors.SYMBOL_TILDE_COLOR) | curses.A_UNDERLINE, last, cursor))
                last = cursor
                continue

        elif state == 2:
            if char == '@':
                state = 0
                chunk = chunk[0:cursor] + chunk[cursor + 1:]
                effects.append((curses.color_pair(colors.SYMBOL_AT_COLOR) | curses.A_BOLD, last, cursor))
                last = cursor
                continue

        else:
            raise ValueError(f'State "{state}" not supported!')

        cursor += 1

    effects.append((curses.color_pair(colors.COMMON_TEXT_COLOR) | curses.A_NORMAL, last, len(chunk)))
    return chunk, effects


def calculate_max_length_actions(actions):
    max_length = 0
    for action, _ in actions:
        length = len(action)
        if length > max_length:
            max_length = length
    return max_length

def calculate_max_length_option(menu_entries):
    max_length = 0
    for option, _, _ in menu_entries:
        length = len(option)
        if length > max_length:
            max_length = length
    return max_length


def calculate_max_length_info(menu_entries):
    max_length = 0
    for _, info, _ in menu_entries:
        length = len(info)
        if length > max_length:
            max_length = length
    return max_length


def calculate_max_length_text_line(lines):
    max_length = 0
    for line in lines:
        length = len(line)
        if length > max_length:
            max_length = length
    return max_length
