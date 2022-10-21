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
from update_all.ui_engine_dialog_application import UiDialogDrawer, UiDialogDrawerFactory

COLOR_PAIR_RED_OVER_BLUE = 1
COLOR_PAIR_WHITE_OVER_BLUE = 2
COLOR_PAIR_CYAN_OVER_BLUE = 3
COLOR_PAIR_RED_OVER_WHITE = 4
COLOR_PAIR_BLUE_OVER_WHITE = 5
COLOR_PAIR_CYAN_OVER_WHITE = 6
COLOR_PAIR_BLACK_OVER_WHITE = 7
COLOR_PAIR_CYAN_OVER_BLACK = 8
COLOR_PAIR_WHITE_OVER_BLACK = 9
COLOR_PAIR_RED_OVER_BLACK = 10
COLOR_PAIR_YELLOW_OVER_BLACK = 11
COLOR_PAIR_GREEN_OVER_BLACK = 12
COLOR_PAIR_MAGENTA_OVER_BLACK = 13
COLOR_PAIR_RED_OVER_CYAN = 14
COLOR_PAIR_BLACK_OVER_CYAN = 15
COLOR_PAIR_WHITE_OVER_CYAN = 16
COLOR_PAIR_BLACK_OVER_YELLOW = 17
COLOR_PAIR_BLACK_OVER_RED = 18
COLOR_PAIR_WHITE_OVER_RED = 19


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
    COMMON_TEXT_COLOR = 0
    UNSELECTED_ACTION_COLOR = 0


colors = ColorConfiguration()


class SettingsScreenStandardPrinter(SettingsScreenPrinter):
    def initialize_screen(self, screen: curses.window) -> Tuple[UiDialogDrawerFactory, SettingsScreenThemeManager]:
        curses.start_color()

        color_white = curses.COLOR_WHITE
        color_red = curses.COLOR_RED
        color_blue = curses.COLOR_BLUE
        color_cyan = curses.COLOR_CYAN
        color_black = curses.COLOR_BLACK
        color_yellow = curses.COLOR_YELLOW
        color_green = curses.COLOR_GREEN
        color_magenta = curses.COLOR_MAGENTA

        curses.init_pair(COLOR_PAIR_RED_OVER_WHITE, color_red, color_white)
        curses.init_pair(COLOR_PAIR_RED_OVER_BLUE, color_red, color_blue)
        curses.init_pair(COLOR_PAIR_WHITE_OVER_BLUE, color_white, color_blue)
        curses.init_pair(COLOR_PAIR_BLUE_OVER_WHITE, color_blue, color_white)
        curses.init_pair(COLOR_PAIR_CYAN_OVER_BLUE, color_cyan, color_blue)
        curses.init_pair(COLOR_PAIR_CYAN_OVER_WHITE, color_cyan, color_white)
        curses.init_pair(COLOR_PAIR_BLACK_OVER_WHITE, color_black, color_white)
        curses.init_pair(COLOR_PAIR_CYAN_OVER_BLACK, color_cyan, color_black)
        curses.init_pair(COLOR_PAIR_WHITE_OVER_BLACK, color_white, color_black)
        curses.init_pair(COLOR_PAIR_RED_OVER_BLACK, color_red, color_black)
        curses.init_pair(COLOR_PAIR_YELLOW_OVER_BLACK, color_yellow, color_black)
        curses.init_pair(COLOR_PAIR_GREEN_OVER_BLACK, color_green, color_black)
        curses.init_pair(COLOR_PAIR_MAGENTA_OVER_BLACK, color_magenta, color_black)
        curses.init_pair(COLOR_PAIR_RED_OVER_CYAN, color_red, color_cyan)
        curses.init_pair(COLOR_PAIR_BLACK_OVER_CYAN, color_black, color_cyan)
        curses.init_pair(COLOR_PAIR_WHITE_OVER_CYAN, color_white, color_cyan)
        curses.init_pair(COLOR_PAIR_BLACK_OVER_YELLOW, color_black, color_yellow)
        curses.init_pair(COLOR_PAIR_BLACK_OVER_RED, color_black, color_red)
        curses.init_pair(COLOR_PAIR_WHITE_OVER_RED, color_white, color_red)

        window = screen.subwin(0, 0)
        window.keypad(True)
        layout = _Layout(window)
        return _DrawerFactory(window, layout), layout


class ColorTheme(abc.ABC):
    def standard(self): pass
    def black(self): pass
    def red(self): pass


class BlueInstallerColorTheme(ColorTheme):
    def standard(self):
        colors.WINDOW_BACKGROUND_COLOR = COLOR_PAIR_WHITE_OVER_BLUE
        colors.BOX_BACKGROUND_COLOR = COLOR_PAIR_BLACK_OVER_WHITE
        colors.HEADER_COLOR = COLOR_PAIR_BLUE_OVER_WHITE

        colors.SELECTED_OPTION_INFO_COLOR = COLOR_PAIR_WHITE_OVER_BLUE
        colors.SELECTED_OPTION_TEXT_COLOR = COLOR_PAIR_CYAN_OVER_BLUE
        colors.OPTION_UNSELECTED_COLOR = COLOR_PAIR_BLUE_OVER_WHITE

        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = COLOR_PAIR_RED_OVER_WHITE
        colors.FIRST_OPTION_KEY_SELECTED_COLOR = COLOR_PAIR_RED_OVER_BLUE

        colors.SELECTED_ACTION_BORDER_COLOR = COLOR_PAIR_WHITE_OVER_BLUE
        colors.SELECTED_ACTION_INTERIOR_COLOR = COLOR_PAIR_CYAN_OVER_BLUE
        colors.UNSELECTED_ACTION_COLOR = COLOR_PAIR_BLACK_OVER_WHITE

        colors.SYMBOL_AT_COLOR = COLOR_PAIR_CYAN_OVER_WHITE
        colors.SYMBOL_TILDE_COLOR = COLOR_PAIR_BLUE_OVER_WHITE
        colors.COMMON_TEXT_COLOR = COLOR_PAIR_BLACK_OVER_WHITE

    def black(self):
        colors.WINDOW_BACKGROUND_COLOR = COLOR_PAIR_WHITE_OVER_BLACK
        colors.BOX_BACKGROUND_COLOR = COLOR_PAIR_BLACK_OVER_WHITE
        colors.HEADER_COLOR = COLOR_PAIR_BLACK_OVER_WHITE

        colors.SELECTED_OPTION_INFO_COLOR = COLOR_PAIR_WHITE_OVER_BLACK
        colors.SELECTED_OPTION_TEXT_COLOR = COLOR_PAIR_CYAN_OVER_BLUE
        colors.OPTION_UNSELECTED_COLOR = COLOR_PAIR_BLUE_OVER_WHITE

        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = COLOR_PAIR_RED_OVER_WHITE
        colors.FIRST_OPTION_KEY_SELECTED_COLOR = COLOR_PAIR_RED_OVER_BLUE

        colors.SELECTED_ACTION_BORDER_COLOR = COLOR_PAIR_WHITE_OVER_BLACK
        colors.SELECTED_ACTION_INTERIOR_COLOR = COLOR_PAIR_WHITE_OVER_BLACK
        colors.UNSELECTED_ACTION_COLOR = COLOR_PAIR_BLACK_OVER_WHITE

        colors.SYMBOL_AT_COLOR = COLOR_PAIR_CYAN_OVER_WHITE
        colors.SYMBOL_TILDE_COLOR = COLOR_PAIR_BLUE_OVER_WHITE
        colors.COMMON_TEXT_COLOR = COLOR_PAIR_BLACK_OVER_WHITE

    def red(self):
        colors.WINDOW_BACKGROUND_COLOR = COLOR_PAIR_WHITE_OVER_RED
        colors.BOX_BACKGROUND_COLOR = COLOR_PAIR_BLACK_OVER_WHITE
        colors.HEADER_COLOR = COLOR_PAIR_RED_OVER_WHITE

        colors.SELECTED_OPTION_INFO_COLOR = COLOR_PAIR_WHITE_OVER_RED
        colors.SELECTED_OPTION_TEXT_COLOR = COLOR_PAIR_WHITE_OVER_RED
        colors.OPTION_UNSELECTED_COLOR = COLOR_PAIR_BLACK_OVER_WHITE

        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = COLOR_PAIR_RED_OVER_WHITE
        colors.FIRST_OPTION_KEY_SELECTED_COLOR = COLOR_PAIR_WHITE_OVER_RED

        colors.SELECTED_ACTION_BORDER_COLOR = COLOR_PAIR_WHITE_OVER_RED
        colors.SELECTED_ACTION_INTERIOR_COLOR = COLOR_PAIR_WHITE_OVER_RED
        colors.UNSELECTED_ACTION_COLOR = COLOR_PAIR_RED_OVER_WHITE

        colors.SYMBOL_AT_COLOR = COLOR_PAIR_RED_OVER_WHITE
        colors.SYMBOL_TILDE_COLOR = COLOR_PAIR_BLUE_OVER_WHITE
        colors.COMMON_TEXT_COLOR = COLOR_PAIR_BLACK_OVER_WHITE


class CyanNightColorTheme(ColorTheme):
    def standard(self):
        colors.WINDOW_BACKGROUND_COLOR = COLOR_PAIR_CYAN_OVER_BLACK
        colors.BOX_BACKGROUND_COLOR = COLOR_PAIR_CYAN_OVER_BLACK
        colors.HEADER_COLOR = COLOR_PAIR_CYAN_OVER_BLACK

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = COLOR_PAIR_BLACK_OVER_CYAN
        colors.SELECTED_OPTION_INFO_COLOR = COLOR_PAIR_BLACK_OVER_CYAN
        colors.SELECTED_OPTION_TEXT_COLOR = COLOR_PAIR_BLACK_OVER_CYAN

        colors.OPTION_UNSELECTED_COLOR = COLOR_PAIR_CYAN_OVER_BLACK
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = COLOR_PAIR_WHITE_OVER_BLACK

        colors.SELECTED_ACTION_INTERIOR_COLOR = COLOR_PAIR_BLACK_OVER_CYAN
        colors.SELECTED_ACTION_BORDER_COLOR = COLOR_PAIR_BLACK_OVER_CYAN

        colors.UNSELECTED_ACTION_COLOR = COLOR_PAIR_CYAN_OVER_BLACK

        colors.SYMBOL_TILDE_COLOR = COLOR_PAIR_YELLOW_OVER_BLACK
        colors.SYMBOL_AT_COLOR = COLOR_PAIR_WHITE_OVER_BLACK
        colors.COMMON_TEXT_COLOR = COLOR_PAIR_CYAN_OVER_BLACK

    def black(self):
        colors.WINDOW_BACKGROUND_COLOR = COLOR_PAIR_YELLOW_OVER_BLACK
        colors.BOX_BACKGROUND_COLOR = COLOR_PAIR_YELLOW_OVER_BLACK
        colors.HEADER_COLOR = COLOR_PAIR_YELLOW_OVER_BLACK

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = COLOR_PAIR_BLACK_OVER_YELLOW
        colors.SELECTED_OPTION_INFO_COLOR = COLOR_PAIR_BLACK_OVER_YELLOW
        colors.SELECTED_OPTION_TEXT_COLOR = COLOR_PAIR_BLACK_OVER_YELLOW

        colors.OPTION_UNSELECTED_COLOR = COLOR_PAIR_YELLOW_OVER_BLACK
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = COLOR_PAIR_WHITE_OVER_BLACK

        colors.SELECTED_ACTION_INTERIOR_COLOR = COLOR_PAIR_BLACK_OVER_YELLOW
        colors.SELECTED_ACTION_BORDER_COLOR = COLOR_PAIR_BLACK_OVER_YELLOW

        colors.UNSELECTED_ACTION_COLOR = COLOR_PAIR_YELLOW_OVER_BLACK

        colors.SYMBOL_TILDE_COLOR = COLOR_PAIR_CYAN_OVER_BLACK
        colors.SYMBOL_AT_COLOR = COLOR_PAIR_WHITE_OVER_BLACK
        colors.COMMON_TEXT_COLOR = COLOR_PAIR_YELLOW_OVER_BLACK

    def red(self):
        colors.WINDOW_BACKGROUND_COLOR = COLOR_PAIR_RED_OVER_BLACK
        colors.BOX_BACKGROUND_COLOR = COLOR_PAIR_RED_OVER_BLACK
        colors.HEADER_COLOR = COLOR_PAIR_RED_OVER_BLACK

        colors.FIRST_OPTION_KEY_SELECTED_COLOR = COLOR_PAIR_BLACK_OVER_RED
        colors.SELECTED_OPTION_INFO_COLOR = COLOR_PAIR_BLACK_OVER_RED
        colors.SELECTED_OPTION_TEXT_COLOR = COLOR_PAIR_BLACK_OVER_RED

        colors.OPTION_UNSELECTED_COLOR = COLOR_PAIR_RED_OVER_BLACK
        colors.FIRST_OPTION_KEY_UNSELECTED_COLOR = COLOR_PAIR_WHITE_OVER_BLACK

        colors.SELECTED_ACTION_INTERIOR_COLOR = COLOR_PAIR_BLACK_OVER_RED
        colors.SELECTED_ACTION_BORDER_COLOR = COLOR_PAIR_BLACK_OVER_RED

        colors.UNSELECTED_ACTION_COLOR = COLOR_PAIR_RED_OVER_BLACK

        colors.SYMBOL_TILDE_COLOR = COLOR_PAIR_CYAN_OVER_BLACK
        colors.SYMBOL_AT_COLOR = COLOR_PAIR_WHITE_OVER_BLACK
        colors.COMMON_TEXT_COLOR = COLOR_PAIR_RED_OVER_BLACK


class _Layout(SettingsScreenThemeManager):
    def __init__(self, window: curses.window):
        self._window = window
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
        if self._current_theme == 'Cyan Night':
            return CyanNightColorTheme()
        else:
            return BlueInstallerColorTheme()

    def paint_layout(self, h: int, w: int, y: int, x: int, has_header: bool) -> None:
        box_id = f'{h}_{w}_{y}_{x}_{str(has_header)}'
        if self._painted and box_id == self._box_id:
            return

        self._painted = True
        self._box_id = box_id
        self._window.clear()
        self._window.bkgd(' ', curses.color_pair(colors.WINDOW_BACKGROUND_COLOR))
        if box_id == self._box_id:
            self._paint_box(h, w, y, x, has_header)

    def _paint_box(self, h: int, w: int, y: int, x: int, has_header: bool) -> None:
        screen = curses.initscr()
        try:
            box1 = screen.subwin(h, w, y, x)
            box1.clear()
            box1.attron(curses.color_pair(colors.BOX_BACKGROUND_COLOR))
            box1.bkgd(' ', curses.color_pair(colors.BOX_BACKGROUND_COLOR) | curses.A_NORMAL)
            box1.box()

            if has_header:
                screen.hline(y + 2, x + 1, curses.ACS_HLINE | curses.color_pair(colors.BOX_BACKGROUND_COLOR), w - 2)

        except curses.error as _:
            box1 = screen.subwin(curses.LINES, curses.COLS, 0, 0)
            box1.clear()
            box1.attron(curses.color_pair(colors.BOX_BACKGROUND_COLOR))
            box1.bkgd(' ', curses.color_pair(colors.BOX_BACKGROUND_COLOR) | curses.A_NORMAL)
            box1.box()

    def reset(self) -> None:
        self._painted = False


class _DrawerFactory(UiDialogDrawerFactory):
    def __init__(self, window: curses.window, layout: _Layout):
        self._window = window
        self._layout = layout

    def create_ui_dialog_drawer(self, interpolator: Interpolator) -> UiDialogDrawer:
        return _Drawer(self._window, self._layout, interpolator)


class _Drawer(UiDialogDrawer):
    def __init__(self, window, layout: _Layout, interpolator: Interpolator):
        self._window = window
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

        return self._window.getch()

    def clear(self) -> None:
        self._layout.reset()

    def _write_line(self, y, x, text, mode):
        if x + len(text) > curses.COLS:
            text = text[0:(curses.COLS - x)]
        try:
            self._window.addstr(y, x, text, mode)
        except curses.error as e:
            print(f'y: {str(y)}')
            print(f'x: {str(x)}')
            print(f'lines: {str(curses.LINES)}')
            print(f'cols: {str(curses.COLS)}')
            print('please report this error to theypsilon and share Scripts/.config/update_all/update_all.log with him')
            raise e


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
