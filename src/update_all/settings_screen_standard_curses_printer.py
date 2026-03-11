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
import traceback
from update_all.colors_curses import init_colors, make_color_theme, colors
from update_all.other import ScreenDims, calculate_outer_box
from update_all.settings_screen_printer import SettingsScreenPrinter, ColorThemeManager
from update_all.ui_engine import Interpolator
from update_all.ui_engine_curses_runtime import CursesRuntime
from update_all.retroaccount_ui import DeviceLoginRenderer
from update_all.ui_engine_dialog_application import UiDialogDrawer, UiDialogDrawerFactory
from update_all.ui_model_utilities import Key

_WARNING_LOG = '/tmp/curses_warnings.log'


def _log_warning(msg):
    with open(_WARNING_LOG, 'a') as f:
        f.write(f'WARNING: {msg}\n')
        traceback.print_stack(file=f)


class SettingsScreenStandardCursesPrinter(CursesRuntime, SettingsScreenPrinter):
    def initialize_screen(self, screen_dims: ScreenDims):
        init_colors()
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        layout = _Layout(self, screen_dims)
        return _DrawerFactory(self, layout, screen_dims), layout, CursesDeviceLoginRenderer(self)


class _Layout(ColorThemeManager):
    def __init__(self, runtime: CursesRuntime, screen_dims: ScreenDims):
        self._runtime = runtime
        self._sd = screen_dims
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
        ts = self._sd.term_size
        try:
            box1 = screen.subwin(h, w, y, x)
            box1.erase()
            box1.attron(curses.color_pair(colors.BOX_BACKGROUND_COLOR))
            box1.bkgd(' ', curses.color_pair(colors.BOX_BACKGROUND_COLOR) | curses.A_NORMAL)
            box1.box()

            if has_header:
                screen.hline(y + 2, x + 1, curses.ACS_HLINE | curses.color_pair(colors.HEADER_LINE_COLOR), w - 2)

        except curses.error as _:
            box1 = screen.subwin(ts.lines, ts.columns, 0, 0)
            box1.erase()
            box1.attron(curses.color_pair(colors.BOX_BACKGROUND_COLOR))
            box1.bkgd(' ', curses.color_pair(colors.BOX_BACKGROUND_COLOR) | curses.A_NORMAL)
            box1.box()

    def reset(self) -> None:
        self._painted = False


class _DrawerFactory(UiDialogDrawerFactory):
    def __init__(self, runtime: CursesRuntime, layout: _Layout, screen_dims: ScreenDims):
        self._runtime = runtime
        self._layout = layout
        self._sd = screen_dims

    def create_ui_dialog_drawer(self, interpolator: Interpolator) -> UiDialogDrawer:
        return _Drawer(self._runtime, self._layout, interpolator, self._sd)


class _Drawer(UiDialogDrawer):
    def __init__(self, runtime: CursesRuntime, layout: _Layout, interpolator: Interpolator, screen_dims: ScreenDims):
        self._runtime = runtime
        self._layout = layout
        self._interpolator = interpolator
        self._sd = screen_dims
        self._text_lines = []
        self._menu_entries = []
        self._actions = []
        self._effects = {}
        self._header = ''
        self._narrow_selected_info = ''
        self._text_scroll_offset = 0
        self._menu_scroll_offset = 0

    def start(self, data):
        self._text_lines = []
        self._menu_entries = []
        self._actions = []
        self._effects = {}
        self._narrow_selected_info = ''

        new_header = self._interpolator.interpolate(data['header']) if 'header' in data else ''
        if new_header != self._header:
            self._menu_scroll_offset = 0
        self._header = new_header

        self._layout.set_sub_theme(data.get('alert_level', None))

    def add_text_line(self, text):
        interpolated_text = self._interpolator.interpolate(text)
        for line in interpolated_text.split('\n'):
            ts = self._sd.term_size
            oc = self._sd.overscan_dim
            n = ts.columns - max(2, oc.cols * 2)
            for chunk in _word_wrap_line(line, n):
                find_tilda = chunk.find('~')
                find_at = chunk.find('@')
                if find_tilda != -1 or find_at != -1:
                    chunk, effects = parse_effects(chunk)
                    self._effects[chunk] = effects

                self._text_lines.append(chunk)

    def max_text_lines(self) -> int:
        ts = self._sd.term_size
        oc = self._sd.overscan_dim
        overhead = 4  # layout borders (2) + action line (1) + spacing (1)
        if self._header:
            overhead += 2
        available = ts.lines - overhead - oc.lines * 2
        return max(1, available)

    def set_text_scroll(self, offset: int) -> None:
        self._text_scroll_offset = offset

    def total_text_lines(self) -> int:
        return len(self._text_lines)

    def add_menu_entry(self, option, info, is_selected=False):
        ts = self._sd.term_size
        if ts.lnarrow and option == '' and info == '' and not is_selected:
            return  # @resolution: This is to avoid text being cutoff off the screen in tiny resolutions.
        if ts.cnarrow:
            if is_selected and info:
                narrow_info = self._interpolator.interpolate(info)
                if narrow_info.endswith('...'):
                    narrow_info = narrow_info[:-3].rstrip()
                self._narrow_selected_info = narrow_info
            info = ''
        self._menu_entries.append((self._interpolator.interpolate(option), self._interpolator.interpolate(info), is_selected))

    def add_action(self, action, is_selected=False):
        self._actions.append((f'<{self._interpolator.interpolate(action)}>', is_selected))

    def add_inactive_action(self, length: int, is_selected=False):
        self._actions.append((' ' * (length + 2), is_selected))

    def paint(self) -> int:
        ts = self._sd.term_size
        oc = self._sd.overscan_dim

        visible_text_lines = self._text_lines
        text_has_up_scroll = False
        max_tl = self.max_text_lines()
        if max_tl > 0 and len(self._text_lines) > max_tl:
            self._layout.reset()
            end = min(self._text_scroll_offset + max_tl, len(self._text_lines))
            start = self._text_scroll_offset
            visible_text_lines = list(self._text_lines[start:end])
            if start > 0:
                if self._header:
                    text_has_up_scroll = True
                else:
                    visible_text_lines[0] = '--- \u2191 \u2191 \u2191 ---'
            if end < len(self._text_lines):
                visible_text_lines[-1] = '--- \u2193 \u2193 \u2193 ---'

        max_length_header = len(self._header)
        lo = oc.lines
        skip_header = False
        action_y = None

        if ts.cnarrow and self._menu_entries:
            action_y = ts.lines - 1 - lo - 1
            available = action_y - lo
            content_lines = len(visible_text_lines) + len(self._menu_entries)

            all_entries_for_width = self._menu_entries
            if content_lines > available:
                self._layout.reset()
                max_entries = max(1, available - len(visible_text_lines))
                all_entries = list(self._menu_entries)
                total_entries = len(all_entries)
                selected_idx = next((i for i, (_, _, s) in enumerate(all_entries) if s), 0)

                self._menu_scroll_offset = _calculate_menu_scroll(selected_idx, total_entries, max_entries, self._menu_scroll_offset)

                offset = self._menu_scroll_offset
                has_up = offset > 0
                real_count = (max_entries - 1) if has_up else max_entries
                real_end = offset + real_count
                has_down = real_end < total_entries
                if has_down:
                    real_count -= 1
                    real_end = offset + real_count

                visible = []
                if has_up:
                    visible.append(('--- \u2191 \u2191 \u2191 ---', '', False))
                visible.extend(all_entries[offset:real_end])
                if has_down:
                    visible.append(('--- \u2193 \u2193 \u2193 ---', '', False))

                self._menu_entries = visible
                content_lines = len(visible_text_lines) + len(self._menu_entries)

            has_gap = content_lines + 1 <= available
            has_box_top = has_gap and content_lines + 1 + 1 <= available
            has_header = max_length_header > 0 and has_box_top and content_lines + 1 + 1 + 2 <= available

            total_lines = content_lines + 1
            if has_gap:
                total_lines += 1
            if has_header:
                total_lines += 2

            skip_header = not has_header
            min_top = lo + 1 if has_box_top else lo
            offset_vertical = max(min_top, min_top + int((action_y - min_top - total_lines + 1) / 2))
        else:
            text_is_scrolled = visible_text_lines is not self._text_lines
            total_lines = len(visible_text_lines) + len(self._menu_entries) + 1
            if max_length_header > 0:
                total_lines += 2
            has_gap = len(self._actions) > 0 and total_lines < ts.lines and not text_is_scrolled
            if has_gap:
                total_lines += 1
            offset_vertical = int(ts.lines / 2 - total_lines / 2)

        co = oc.cols
        floor = max(1, co)
        offset_header = max(floor, int(ts.columns / 2 - max_length_header / 2))
        max_length_text_line = min(ts.columns - max(2, co * 2), calculate_max_length_text_line(self._text_lines))

        offset_text_line = max(floor, int(ts.columns / 2 - max_length_text_line / 2))

        width_entries = all_entries_for_width if action_y is not None else self._menu_entries
        max_length_option = calculate_max_length_option(width_entries)
        max_length_info =  calculate_max_length_info(width_entries)
        max_menu_entry = max_length_option + 2 + max_length_info

        offset_menu = max(floor, int(ts.columns / 2 - max_menu_entry / 2))

        action_gap = 4
        max_length_actions = sum(len(a) for a, _ in self._actions) + action_gap * max(0, len(self._actions) - 1)
        offset_actions = int(ts.columns / 2 - max_length_actions / 2)

        total_width = max(max(max_menu_entry, max_length_text_line), max(max_length_header, max_length_actions))
        offset_horizontal = min(min(offset_menu, offset_text_line), min(offset_actions, offset_header))

        self._layout.paint_layout(total_lines + 2, total_width + 2, offset_vertical - 1, offset_horizontal - 1, max_length_header > 0 and not skip_header)

        line_index = offset_vertical

        if max_length_header > 0 and not skip_header:
            self._write_line(line_index, offset_header, self._header, curses.A_NORMAL | curses.color_pair(colors.HEADER_COLOR))
            if text_has_up_scroll:
                up_text = '--- \u2191 \u2191 \u2191 ---'
                self._write_line(line_index + 1, offset_text_line, up_text, curses.A_NORMAL | curses.color_pair(colors.COMMON_TEXT_COLOR))
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

        if action_y is not None:
            line_index = action_y
        elif has_gap:
            line_index += 1

        for action, is_selected in self._actions:
            if is_selected:
                self._write_line(line_index, offset_actions, action[0:1], curses.A_BLINK | curses.color_pair(colors.SELECTED_ACTION_BORDER_COLOR))
                self._write_line(line_index, offset_actions + 1, action[1:-1], curses.A_BLINK | curses.color_pair(colors.SELECTED_ACTION_INTERIOR_COLOR))
                self._write_line(line_index, offset_actions + len(action) - 1, action[-1:], curses.A_BLINK | curses.color_pair(colors.SELECTED_ACTION_BORDER_COLOR))
            else:
                self._write_line(line_index, offset_actions, action, curses.A_NORMAL | curses.color_pair(colors.UNSELECTED_ACTION_COLOR))
            offset_actions += len(action) + action_gap

        if ts.cnarrow:
            co = oc.cols
            lo = oc.lines
            mode = curses.A_NORMAL | curses.color_pair(colors.SELECTED_OPTION_INFO_COLOR)
            desc_y = ts.lines - 1 - lo
            for clear_y in range(desc_y, ts.lines):
                self._clear_line(clear_y, 0, ord(' ') | mode, ts.columns)
            if self._narrow_selected_info:
                avail = max(1, ts.columns - co * 2 - 1)  # usable width (skip overscan on both sides, -1 for right edge padding)
                text = self._narrow_selected_info
                if len(text) > avail:
                    return self._marquee_read_key(text, avail, mode)
                x = max(co, (ts.columns - len(text)) // 2)
                self._write_line(desc_y, x, text, mode)

        if _is_selected_overscan_entry(self._menu_entries):
            self._paint_overscan_preview()

        return self._runtime.read_key()

    def _marquee_read_key(self, text, avail, mode):
        ts = self._sd.term_size
        oc = self._sd.overscan_dim
        max_offset = len(text) - avail
        offset = 0
        direction = 1
        pause_ticks = 7  # ~2.1s at 300ms per tick
        wait = pause_ticks
        y = ts.lines - 1 - oc.lines
        win = self._runtime.window
        win.timeout(300)
        try:
            while True:
                co = oc.cols
                visible = text[offset:offset + avail]
                self._clear_line(y, 0, ord(' ') | mode, ts.columns)
                self._write_line(y, co, visible, mode)
                curses.doupdate()
                key = self._runtime.read_key()
                if key != Key.NONE and key != -1:
                    return key
                if wait > 0:
                    wait -= 1
                    continue
                offset += direction
                if offset >= max_offset or offset <= 0:
                    direction = -direction
                    wait = pause_ticks
        finally:
            win.timeout(-1)

    def clear(self) -> None:
        self._layout.reset()

    def _clear_line(self, y, x, ch, n):
        ts = self._sd.term_size
        if y < 0 or y >= ts.lines or x < 0 or x >= ts.columns:
            _log_warning(f'_clear_line out of bounds: y={y} x={x} lines={ts.lines} cols={ts.columns}')
            return
        n = min(n, ts.columns - x)
        if n <= 0:
            return
        self._runtime.window.hline(y, x, ch, n)

    def _write_line(self, y, x, text, mode):
        if not text:
            return
        ts = self._sd.term_size
        oc = self._sd.overscan_dim
        if y < 0 or y >= ts.lines:
            _log_warning(f'_write_line out of bounds: y={y} x={x} text={text!r} lines={ts.lines} cols={ts.columns}')
            return
        left_col = oc.cols  # @resolution: Overscan compensation in narrow resolutions.
        right_col = ts.columns - oc.cols
        if x < left_col:
            _log_warning(f'_write_line x below left bound: y={y} x={x} left_col={left_col} text={text!r}')
            text = text[left_col - x:]
            x = left_col
        if x >= right_col:
            _log_warning(f'_write_line x beyond right bound: y={y} x={x} right_col={right_col} text={text!r}')
            return
        if x + len(text) > right_col:
            _log_warning(f'_write_line text truncated: y={y} x={x} right_col={right_col} text={text!r}')
            text = text[0:(right_col - x)]
        if y == ts.lines - 1 and x + len(text) >= ts.columns:
            text = text[0:(ts.columns - x - 1)]
        if not text:
            return
        self._runtime.window.addstr(y, x, text, mode)

    def _paint_overscan_preview(self) -> None:
        preview_border = calculate_outer_box(self._sd)
        if preview_border is None:
            return
        top, bottom, left, right = preview_border
        ts = self._sd.term_size
        attr = curses.A_NORMAL | curses.color_pair(colors.OVERSCAN_BOX_COLOR)
        win = self._runtime.window
        block = '█'
        try:
            for y in range(0, min(ts.lines, top + 1)):
                width = ts.columns - (1 if y == ts.lines - 1 else 0)
                if width > 0:
                    win.addstr(y, 0, block * width, attr)

            for y in range(max(0, bottom), ts.lines):
                width = ts.columns - (1 if y == ts.lines - 1 else 0)
                if width > 0:
                    win.addstr(y, 0, block * width, attr)

            start_y = max(0, top + 1)
            end_y = min(ts.lines, bottom)
            if start_y < end_y:
                if 0 <= left < ts.columns:
                    left_width = left + 1
                    for y in range(start_y, end_y):
                        width = min(left_width, ts.columns - (1 if y == ts.lines - 1 else 0))
                        if width > 0:
                            win.addstr(y, 0, block * width, attr)
                if 0 <= right < ts.columns:
                    for y in range(start_y, end_y):
                        width = ts.columns - right - (1 if y == ts.lines - 1 else 0)
                        if width > 0:
                            win.addstr(y, right, block * width, attr)
        except curses.error:
            pass


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


def _calculate_menu_scroll(selected_idx, total_entries, max_entries, current_offset):
    offset = current_offset
    if offset == 0:
        if selected_idx + 1 > max_entries - 2 and total_entries > max_entries:
            offset = selected_idx - max_entries + 4
    else:
        end_vis = offset + max_entries - 1
        if end_vis < total_entries:
            last_visible = offset + max_entries - 3
            if selected_idx + 1 > last_visible:
                offset = selected_idx - max_entries + 4
    if offset > 0 and selected_idx - 1 < offset:
        offset = max(0, selected_idx - 1)
    offset = max(0, min(offset, max(0, total_entries - (max_entries - 1))))

    vis_slots = max_entries - (1 if offset > 0 else 0)
    if offset + vis_slots < total_entries:
        vis_slots -= 1  # down indicator takes a slot
    visible_end = offset + vis_slots - 1
    if selected_idx > visible_end:
        offset = min(selected_idx, max(0, total_entries - (max_entries - 1)))
    elif selected_idx < offset:
        offset = max(0, selected_idx)

    return offset


def _is_selected_overscan_entry(menu_entries):
    return any(is_selected and option.endswith('Overscan') for option, _, is_selected in menu_entries)


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
