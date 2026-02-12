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
from typing import Tuple

from update_all.colors_curses import init_colors, make_color_theme, colors
from update_all.settings_screen_printer import SettingsScreenPrinter, ColorThemeManager
from update_all.ui_engine import Interpolator
from update_all.ui_engine_curses_runtime import CursesRuntime
from update_all.retroaccount_ui import DeviceLoginRenderer
from update_all.ui_engine_dialog_application import UiDialogDrawer, UiDialogDrawerFactory
from update_all.ui_model_utilities import Key


class SettingsScreenStandardCursesPrinter(CursesRuntime, SettingsScreenPrinter):
    def initialize_screen(self):
        init_colors()
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        layout = _Layout(self)
        return _DrawerFactory(self, layout), layout, CursesDeviceLoginRenderer(self)


class _Layout(ColorThemeManager):
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
        color_theme = make_color_theme(self._current_theme)
        if self._current_sub_theme == 'black':
            color_theme.black()
        elif self._current_sub_theme == 'red':
            color_theme.red()
        else:
            color_theme.standard()

    def paint_layout(self, h: int, w: int, y: int, x: int, has_header: bool) -> None:
        box_id = f'{h}_{w}_{y}_{x}_{str(has_header)}'
        if self._painted and box_id == self._box_id:
            return

        self._painted = True
        self._box_id = box_id
        self._runtime.window.erase()
        self._runtime.window.bkgd(' ', curses.color_pair(colors.WINDOW_BACKGROUND_COLOR))
        if box_id == self._box_id:
            self._paint_box(h, w, y, x, has_header)

    def _paint_box(self, h: int, w: int, y: int, x: int, has_header: bool) -> None:
        screen = curses.initscr()
        if curses.LINES <= 15:  # @resolution: This is to move the texts a bit up in tiny resolutions.
            y -= 1
        try:
            box1 = screen.subwin(h, w, y, x)
            box1.erase()
            box1.attron(curses.color_pair(colors.BOX_BACKGROUND_COLOR))
            box1.bkgd(' ', curses.color_pair(colors.BOX_BACKGROUND_COLOR) | curses.A_NORMAL)
            box1.box()

            if has_header:
                screen.hline(y + 2, x + 1, curses.ACS_HLINE | curses.color_pair(colors.HEADER_LINE_COLOR), w - 2)

        except curses.error as _:
            box1 = screen.subwin(curses.LINES, curses.COLS, 0, 0)
            box1.erase()
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
        self._narrow_selected_info = ''
        self._scroll_offset = 0

    def start(self, data):
        self._text_lines = []
        self._menu_entries = []
        self._actions = []
        self._effects = {}
        self._narrow_selected_info = ''
        self._scroll_offset = 0

        self._header = ''
        if 'header' in data:
            self._header = self._interpolator.interpolate(data['header'])

        self._layout.set_sub_theme(data.get('alert_level', None))

    def add_text_line(self, text):
        interpolated_text = self._interpolator.interpolate(text)
        for line in interpolated_text.split('\n'):
            n = curses.COLS - 2
            for chunk in _word_wrap_line(line, n):
                find_tilda = chunk.find('~')
                find_at = chunk.find('@')
                if find_tilda != -1 or find_at != -1:
                    chunk, effects = parse_effects(chunk)
                    self._effects[chunk] = effects

                self._text_lines.append(chunk)

    def max_text_lines(self) -> int:
        overhead = 4  # layout borders (2) + action line (1) + spacing (1)
        if self._header:
            overhead += 2
        available = curses.LINES - overhead
        return max(1, available)

    def set_text_scroll(self, offset: int) -> None:
        self._scroll_offset = offset

    def total_text_lines(self) -> int:
        return len(self._text_lines)

    def add_menu_entry(self, option, info, is_selected=False):
        if curses.LINES <= 15 and option == '' and info == '' and not is_selected:
            return  # @resolution: This is to avoid text being cutoff off the screen in tiny resolutions.
        if curses.COLS <= 40:
            if is_selected and info:
                self._narrow_selected_info = self._interpolator.interpolate(info)
            info = ''
        self._menu_entries.append((self._interpolator.interpolate(option), self._interpolator.interpolate(info), is_selected))

    def add_action(self, action, is_selected=False):
        self._actions.append((f'<{self._interpolator.interpolate(action)}>', is_selected))

    def add_inactive_action(self, length: int, is_selected=False):
        self._actions.append((' ' * (length + 2), is_selected))

    def paint(self) -> int:
        visible_text_lines = self._text_lines
        max_tl = self.max_text_lines()
        if max_tl > 0 and len(self._text_lines) > max_tl:
            self._layout.reset()
            end = min(self._scroll_offset + max_tl, len(self._text_lines))
            start = self._scroll_offset
            visible_text_lines = list(self._text_lines[start:end])
            if start > 0:
                visible_text_lines[0] = '--- ↑ ↑ ↑ ---'
            if end < len(self._text_lines):
                visible_text_lines[-1] = '--- ↓ ↓ ↓ ---'

        total_lines = len(visible_text_lines) + len(self._menu_entries) + 1
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

        action_gap = 4
        max_length_actions = sum(len(a) for a, _ in self._actions) + action_gap * max(0, len(self._actions) - 1)
        offset_actions = int(curses.COLS / 2 - max_length_actions / 2)

        total_width = max(max(max_menu_entry, max_length_text_line), max(max_length_header, max_length_actions))
        offset_horizontal = min(min(offset_menu, offset_text_line), min(offset_actions, offset_header))

        self._layout.paint_layout(total_lines + 2, total_width + 2, offset_vertical - 1, offset_horizontal - 1, max_length_header> 0)

        line_index = offset_vertical

        if max_length_header > 0:
            self._write_line(line_index, offset_header, self._header, curses.A_NORMAL | curses.color_pair(colors.HEADER_COLOR))
            line_index += 2

        for line in visible_text_lines:
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
            offset_actions += len(action) + action_gap

        if curses.COLS <= 40:
            mode = curses.A_NORMAL | curses.color_pair(colors.SELECTED_OPTION_INFO_COLOR)
            self._runtime.window.hline(curses.LINES - 1, 0, ord(' ') | mode, curses.COLS)
            if self._narrow_selected_info:
                text = self._narrow_selected_info[:curses.COLS - 1]
                x = max(0, (curses.COLS - len(text)) // 2)
                self._runtime.window.addstr(curses.LINES - 1, x, text, mode)

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
        if x >= curses.COLS:
            return
        if x + len(text) >= curses.COLS:
            text = text[0:(curses.COLS - x - 1)]
        self._runtime.window.addstr(y, x, text, mode)

class CursesDeviceLoginRenderer(DeviceLoginRenderer):
    def __init__(self, runtime: CursesRuntime):
        self._runtime = runtime

    def render_requesting(self, header: str) -> None:
        win = self._runtime.window
        win.erase()
        win.bkgd(' ', curses.color_pair(colors.DEVICE_LOGIN_BACKGROUND_COLOR))
        h, w = win.getmaxyx()
        self._draw_centered(win, 1, w, f"═══ {header} ═══", curses.A_BOLD | curses.color_pair(colors.DEVICE_LOGIN_HEADER_COLOR))
        text_attr = curses.color_pair(colors.DEVICE_LOGIN_TEXT_COLOR) | colors.DEVICE_LOGIN_TEXT_EXTRA_ATTR
        self._draw_centered(win, 3, w, "Requesting device code...", text_attr)
        win.refresh()

    def render_poll_screen(self, header: str, user_code: str, verification_uri: str,
                           qr_lines: list, dots: str, remaining: int) -> None:
        win = self._runtime.window
        win.erase()
        win.bkgd(' ', curses.color_pair(colors.DEVICE_LOGIN_BACKGROUND_COLOR))
        h, w = win.getmaxyx()
        header_attr = curses.A_BOLD | curses.color_pair(colors.DEVICE_LOGIN_HEADER_COLOR)
        text_attr = curses.color_pair(colors.DEVICE_LOGIN_TEXT_COLOR) | colors.DEVICE_LOGIN_TEXT_EXTRA_ATTR
        bold_attr = curses.A_BOLD | curses.color_pair(colors.DEVICE_LOGIN_TEXT_COLOR)
        link_attr = curses.color_pair(colors.DEVICE_LOGIN_LINK_COLOR) | colors.DEVICE_LOGIN_LINK_EXTRA_ATTR
        highlight_attr = curses.A_REVERSE | curses.A_BOLD | curses.color_pair(colors.DEVICE_LOGIN_TEXT_COLOR)

        self._draw_centered(win, 1, w, f"═══ {header} ═══", header_attr)

        qr_fits = qr_lines and w >= len(qr_lines[0]) + 4 and h >= len(qr_lines) + 12
        url_complete = qr_fits and len(f"at {verification_uri}") < w
        display_uri = verification_uri if url_complete else \
            verification_uri.split('?')[0].removeprefix('https://').removeprefix('http://')
        code_action = "authorize" if url_complete else "enter"

        if qr_fits:
            self._draw_centered(win, 3, w, "Scan QR to link this device", text_attr)
            for i, line in enumerate(qr_lines):
                if 5 + i < h - 6:
                    self._draw_centered(win, 5 + i, w, line, text_attr)
            row = 5 + len(qr_lines) + 2
            self._draw_centered(win, row, w, f"or {code_action} the code:", text_attr)
            self._draw_centered(win, row + 2, w, f"   {user_code}   ", highlight_attr)
            self._draw_centered(win, row + 4, w, f"at {display_uri}", link_attr)
        else:
            self._draw_centered(win, 3, w, "On your phone, visit:", bold_attr)
            self._draw_centered(win, 5, w, display_uri, curses.A_UNDERLINE | link_attr)
            self._draw_centered(win, 7, w, f"And {code_action} the code:", text_attr)
            self._draw_centered(win, 9, w, f"  {user_code}  ", highlight_attr)

        time_label = f"({remaining:>3d}s remaining)" if url_complete else f"{remaining:>3d}s"
        self._draw_centered(win, h - 3, w, f"Waiting for verification{dots:<3s} {time_label}", text_attr)
        self._draw_centered(win, h - 2, w, "[ Cancel ]", bold_attr)
        win.refresh()

    def render_cancel_dialog(self, header: str, user_code: str,
                             options: list, selected: int) -> None:
        win = self._runtime.window
        win.erase()
        win.bkgd(' ', curses.color_pair(colors.DEVICE_LOGIN_BACKGROUND_COLOR))
        h, w = win.getmaxyx()
        header_attr = curses.A_BOLD | curses.color_pair(colors.DEVICE_LOGIN_HEADER_COLOR)
        text_attr = curses.color_pair(colors.DEVICE_LOGIN_TEXT_COLOR) | colors.DEVICE_LOGIN_TEXT_EXTRA_ATTR
        bold_attr = curses.A_BOLD | curses.color_pair(colors.DEVICE_LOGIN_TEXT_COLOR)
        link_attr = curses.color_pair(colors.DEVICE_LOGIN_LINK_COLOR) | colors.DEVICE_LOGIN_LINK_EXTRA_ATTR
        hint = "← → to select, Enter to confirm"

        self._draw_centered(win, 1, w, f"═══ {header} ═══", header_attr)
        self._draw_centered(win, 3, w, "Cancel Login?", bold_attr)
        self._draw_centered(win, 5, w, f"The code {user_code} is still valid.", link_attr)

        labels = [f"[ {o} ]" if i == selected else f"  {o}  " for i, o in enumerate(options)]
        full = "    ".join(labels)
        opt_row = 8
        x = (w - len(full)) // 2
        if x < 0:
            x = 0
        try:
            win.addstr(opt_row, x, full, bold_attr)
            sel_x = x + sum(len(labels[j]) + 4 for j in range(selected))
            win.addstr(opt_row, sel_x, labels[selected], curses.A_REVERSE | bold_attr)
        except curses.error:
            pass
        self._draw_centered(win, h - 2, w, hint, bold_attr)
        win.refresh()

    def set_key_timeout(self, timeout_ms: int) -> None:
        self._runtime.window.timeout(timeout_ms)

    def read_key(self):
        key = self._runtime.window.getch()
        if key == curses.KEY_LEFT:
            return Key.LEFT
        elif key == curses.KEY_RIGHT:
            return Key.RIGHT
        elif key in (curses.KEY_ENTER, ord('\n'), ord('\r')):
            return Key.ENTER
        return key

    def flush_input(self) -> None:
        curses.flushinp()

    @staticmethod
    def _draw_centered(win, row, width, text, attr=0):
        x = max(0, (width - len(text)) // 2)
        try:
            win.addstr(row, x, text, attr)
        except curses.error:
            pass


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


def _word_wrap_line(line, max_width):
    if len(line) <= max_width:
        return [line]
    result = []
    while len(line) > max_width:
        break_pos = line.rfind(' ', 0, max_width + 1)
        if break_pos <= 0:
            result.append(line[:max_width])
            line = line[max_width:]
        else:
            result.append(line[:break_pos])
            line = line[break_pos + 1:]
    if line:
        result.append(line)
    return result
