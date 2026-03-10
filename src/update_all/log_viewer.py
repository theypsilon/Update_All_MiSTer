#!/bin/python
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

import os
from typing import Optional, NamedTuple

from update_all.constants import DEFAULT_LOG_VIEWER_THEME
from update_all.file_system import FileSystem
from update_all.logger import apply_overscan_preserving_newlines
from update_all.local_store import LocalStore
from update_all.config import Config
from update_all.other import GenericProvider, ScreenDims
from update_all.retroaccount import RetroAccountService


def clamp(v, lo, hi): return max(lo, min(v, hi))
def clip_range(start: int, length: int, limit: int) -> tuple[int, int]:
    length = clamp(length, 1, limit)
    return clamp(start, 0, limit - length), length

def to_overscanned_doc(doc: list[str], columns: int, cols_overscan: int) -> list[str]:
    if columns - cols_overscan * 2 <= 0:
        return doc
    if len(doc) == 0:
        return []
    result: list[str] = []
    for entry in doc:
        rendered = apply_overscan_preserving_newlines([entry], '', columns, cols_overscan, '')
        result.extend(line + line_end for line, line_end in rendered)
    return result


def create_log_document(file_path: str) -> list[str]:
    if not os.path.exists(file_path):
        return []

    with open(file_path, 'r') as file:
        file_content = file.readlines()

    import re
    ansi_sgr = re.compile(r'\x1b\[[0-9;]*[mK]')

    document = []
    for line in file_content:
        document.append(ansi_sgr.sub('', line))
    return document


class LogViewer:
    def __init__(self, file_system: FileSystem, config_provider: GenericProvider[Config], store_provider: GenericProvider[LocalStore], retroaccount: RetroAccountService):
        self._file_system = file_system
        self._config_provider = config_provider
        self._store_provider = store_provider
        self._retroaccount = retroaccount

    def show(self, doc: list[str], popup_dict: Optional[dict[str, str]] = None, initial_index: int = 0) -> bool:
        store = self._store_provider.get()
        can_use_custom_theme = (
            self._retroaccount.is_update_all_extras_active()
            and store.get_use_settings_screen_theme_in_log_viewer()
        )
        ui_theme = store.get_theme() if can_use_custom_theme else DEFAULT_LOG_VIEWER_THEME
        config = self._config_provider.get()
        view_document(doc, popup_dict or {}, initial_index, ui_theme, config)
        return True


class HudLayout(NamedTuple):
    left: int
    width: int
    top_text_y: int
    top_line_y: int
    bottom_line_y: int
    bottom_text_y: int
    page_top_y: int
    page_rows: int


def calculate_hud_message(screen_dims: ScreenDims) -> str:
    if screen_dims.term_size.cnarrow:
        return '↑↓←→ Nav · Any key Exit'
    return '←↑↓→ Navigate · Any key Exit'


def calculate_hud_layout(screen_dims: ScreenDims) -> HudLayout:
    ts = screen_dims.term_size
    oc = screen_dims.overscan_dim

    left = oc.cols
    width = max(1, ts.columns - oc.cols * 2)
    top_text_y = oc.lines
    top_line_y = min(ts.lines - 1, top_text_y + 1)
    bottom_text_y = max(0, ts.lines - oc.lines - 1)
    bottom_line_y = max(0, bottom_text_y - 1)
    page_top_y = min(ts.lines - 1, top_line_y + 1)
    page_bottom_y = max(page_top_y, bottom_line_y - 1)

    return HudLayout(
        left=left,
        width=width,
        top_text_y=top_text_y,
        top_line_y=top_line_y,
        bottom_line_y=bottom_line_y,
        bottom_text_y=bottom_text_y,
        page_top_y=page_top_y,
        page_rows=max(1, page_bottom_y - page_top_y + 1),
    )


def view_document(document: list[str], popup_dict: dict[int, list[str]], initial_index: int, theme: Optional[str], screen_dims: ScreenDims) -> None:
    import curses
    from update_all.colors_curses import init_colors, make_color_theme, colors

    class ViewerGui:
        def __init__(self, window: curses.window, max_cols: int, max_lines: int, document: list[str],
                     initial_index: int, hud_layout: HudLayout):
            self.window = window
            self.mcols = max_cols
            self.mlines = max_lines
            self.document = document
            self.initial_index = initial_index
            self._hud_layout = hud_layout
            self.frame_start = hud_layout.page_top_y
            self.frame_end = hud_layout.page_rows
            self.mindex = max(1, len(document) - self.frame_end)

            hud_message = calculate_hud_message(screen_dims)
            text_area = hud_layout.width - 7
            hud_x = hud_layout.left + 1 + max(0, (text_area - len(hud_message)) // 2)
            dot_idx = hud_message.find('·')
            self._hud_parts = (hud_message[:dot_idx], hud_x, dot_idx, hud_message[dot_idx + 1:]) if dot_idx != -1 else (
            hud_message, hud_x, -1, '')

        def addstr(self, y: int, x: int, text: str, attr: int):
            x, length = clip_range(x, len(text), self.mcols - 1)
            self.window.addstr(clamp(y, 0, self.mlines - 1), x, text[:length],
                               attr | curses.color_pair(colors.LOG_VIEWER_TEXT_COLOR))

        def addstr_symbol(self, y: int, x: int, text: str):
            x, length = clip_range(x, len(text), self.mcols - 1)
            self.window.addstr(clamp(y, 0, self.mlines - 1), x, text[:length],
                               curses.color_pair(colors.LOG_VIEWER_SYMBOL_COLOR))

        def addstr_log(self, y: int, x: int, text: str):
            x, length = clip_range(x, len(text), self.mcols)
            y = clamp(y, 0, self.mlines - 1)
            text_attr = curses.color_pair(colors.LOG_VIEWER_TEXT_COLOR)
            symbol_attr = curses.color_pair(colors.LOG_VIEWER_SYMBOL_COLOR)
            win = self.window
            for i, c in enumerate(text[:length]):
                if ('a' <= c <= 'z') or ('A' <= c <= 'Z') or ('0' <= c <= '9') or c in ",.'!?_&":
                    win.addstr(y, x + i, c, text_attr)
                else:
                    win.addstr(y, x + i, c, symbol_attr)

        def vline(self, y: int, x: int, attr: int, length: int):
            y, length = clip_range(y, length, self.mlines)
            self.window.vline(y, clamp(x, 0, self.mcols - 1), attr | curses.color_pair(colors.LOG_VIEWER_TEXT_COLOR),
                              length)

        def hline(self, y: int, x: int, attr: int, length: int):
            x, length = clip_range(x, length, self.mcols)
            self.window.hline(clamp(y, 0, self.mlines - 1), x, attr | curses.color_pair(colors.LOG_VIEWER_TEXT_COLOR),
                              length)

        def draw_hud(self, hud_percent: str, top: bool = True) -> None:
            hl = self._hud_layout
            if top:
                y_text, y_line = hl.top_text_y, hl.top_line_y
                corner_left, corner_right, tee = curses.ACS_LLCORNER, curses.ACS_LRCORNER, curses.ACS_BTEE
            else:
                y_text, y_line = hl.bottom_text_y, hl.bottom_line_y
                corner_left, corner_right, tee = curses.ACS_ULCORNER, curses.ACS_URCORNER, curses.ACS_TTEE

            hud_attr = curses.color_pair(colors.LOG_VIEWER_HUD_TEXT_COLOR)
            if top:
                for y in range(y_text):
                    self.window.hline(y, hl.left, ord(' ') | hud_attr, hl.width)
            else:
                for y in range(y_text + 1, self.mlines):
                    self.window.hline(y, hl.left, ord(' ') | hud_attr, hl.width)
            self.window.hline(clamp(y_text, 0, self.mlines - 1), hl.left, ord(' ') | hud_attr, hl.width)
            self.window.hline(clamp(y_line, 0, self.mlines - 1), hl.left, ord(' ') | hud_attr, hl.width)

            before, hud_x, dot_idx, after = self._hud_parts
            hud_text_attr = curses.color_pair(colors.LOG_VIEWER_HUD_TEXT_COLOR)
            hud_dot_attr = curses.color_pair(colors.LOG_VIEWER_HUD_SYMBOL_COLOR)
            if dot_idx == -1:
                x, length = clip_range(hud_x, len(before), self.mcols - 1)
                self.window.addstr(clamp(y_text, 0, self.mlines - 1), x, before[:length], curses.A_NORMAL | hud_text_attr)
            else:
                x, length = clip_range(hud_x, len(before), self.mcols - 1)
                self.window.addstr(clamp(y_text, 0, self.mlines - 1), x, before[:length], curses.A_NORMAL | hud_text_attr)
                x, length = clip_range(hud_x + dot_idx, 1, self.mcols - 1)
                self.window.addstr(clamp(y_text, 0, self.mlines - 1), x, '·'[:length], hud_dot_attr)
                x, length = clip_range(hud_x + dot_idx + 1, len(after), self.mcols - 1)
                self.window.addstr(clamp(y_text, 0, self.mlines - 1), x, after[:length], curses.A_NORMAL | hud_text_attr)
            x, length = clip_range(hl.left + hl.width - 5, len('   %'), self.mcols - 1)
            self.window.addstr(clamp(y_text, 0, self.mlines - 1), x, '   %'[:length], curses.A_NORMAL | hud_text_attr)
            x, length = clip_range(hl.left + hl.width - len(hud_percent) - 1, len(hud_percent), self.mcols - 1)
            self.window.addstr(clamp(y_text, 0, self.mlines - 1), x, hud_percent[:length], curses.A_NORMAL | hud_text_attr)

            vertical_line_start = 0 if top else y_text
            vertical_line_length = y_text + 1 if top else self.mlines - y_text
            for x in (hl.left, hl.left + hl.width - 6, hl.left + hl.width - 1):
                y, length = clip_range(vertical_line_start, vertical_line_length, self.mlines)
                self.window.vline(y, clamp(x, 0, self.mcols - 1), curses.ACS_VLINE | curses.color_pair(colors.LOG_VIEWER_HUD_LINES_COLOR), length)

            border_attr = curses.color_pair(colors.LOG_VIEWER_HUD_BORDER_COLOR)
            lines_attr = curses.color_pair(colors.LOG_VIEWER_HUD_LINES_COLOR)
            x, length = clip_range(hl.left, 1, self.mcols)
            self.window.hline(clamp(y_line, 0, self.mlines - 1), x, corner_left | lines_attr, length)
            x, length = clip_range(hl.left + 1, hl.width - 1, self.mcols)
            self.window.hline(clamp(y_line, 0, self.mlines - 1), x, curses.ACS_HLINE | border_attr, length)
            x, length = clip_range(hl.left + hl.width - 6, 1, self.mcols)
            self.window.hline(clamp(y_line, 0, self.mlines - 1), x, tee | lines_attr, length)
            x, length = clip_range(hl.left + hl.width - 1, 1, self.mcols)
            self.window.hline(clamp(y_line, 0, self.mlines - 1), x, corner_right | lines_attr, length)

        def loop(self):
            index = self.initial_index
            last_index = None
            viewing = True

            self.window.bkgd(' ', curses.color_pair(colors.LOG_VIEWER_BACKGROUND_COLOR))

            while viewing:
                if last_index is None or last_index != index:
                    last_index = index

                    if len(self.document) > self.frame_end:
                        page = self.document[len(self.document) - index - self.frame_end:len(self.document) - index]
                    else:
                        page = self.document

                    bg = curses.color_pair(colors.LOG_VIEWER_BACKGROUND_COLOR)
                    for i in range(self.frame_end):
                        y = i + self.frame_start
                        self.window.hline(y, 0, ord(' ') | bg, self.mcols)
                    for i, line in enumerate(page[:self.frame_end]):
                        y = i + self.frame_start
                        self.addstr_log(y, 0, line)

                    hud_percent = f'{100 - (int(index * 100 / self.mindex))}%'
                    self.draw_hud(hud_percent, top=True)
                    self.draw_hud(hud_percent, top=False)

                key = self.window.getch()
                if key == curses.KEY_UP:
                    index += 1
                elif key == curses.KEY_DOWN:
                    index -= 1
                elif key == curses.KEY_LEFT or key == curses.KEY_PPAGE:
                    index += self.mlines
                elif key == curses.KEY_RIGHT or key == curses.KEY_NPAGE:
                    index -= self.mlines
                elif key != -1:
                    viewing = False

                if index < 0:
                    index = 0
                elif index > self.mindex:
                    index = self.mindex

                curses.doupdate()

    def loader(screen: curses.window):
        init_colors()
        make_color_theme(theme).viewer()

        window = screen.subwin(0, 0)
        window.bkgd(' ', curses.color_pair(colors.LOG_VIEWER_BACKGROUND_COLOR))
        window.keypad(True)
        curses.cbreak()
        curses.curs_set(0)
        window.nodelay(True)
        window.timeout(50)
        window.clear()

        ts = screen_dims.term_size

        hud_layout = calculate_hud_layout(screen_dims)

        ViewerGui(
            window,
            ts.columns,
            ts.lines,
            document,
            initial_index,
            hud_layout
        ).loop()

    curses.wrapper(loader)
