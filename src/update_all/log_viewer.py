#!/bin/python
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

import os
from typing import Optional

from update_all.colors_curses import init_colors, make_color_theme, colors
from update_all.constants import FILE_update_all_log
from update_all.encryption import Encryption, EncryptionResult
from update_all.file_system import FileSystem
from update_all.local_store import LocalStore
from update_all.other import GenericProvider


def clamp(v, lo, hi): return max(lo, min(v, hi))
def clip_range(start: int, length: int, limit: int) -> tuple[int, int]:
    length = clamp(length, 1, limit)
    return clamp(start, 0, limit - length), length

def create_log_document(file_path: str) -> list[str]:
    if not os.path.exists(file_path):
        return []

    with open(file_path, 'r') as file:
        file_content = file.readlines()

    import re, itertools
    ansi_sgr = re.compile(r'\x1b\[[0-9;]*[mK]')

    document = []
    for line in itertools.dropwhile(lambda ln: ln != "\n", file_content):  # Skips the first debug lines
        document.append(ansi_sgr.sub('', line))
    return document


class LogViewer:
    def __init__(self, file_system: FileSystem, store_provider: GenericProvider[LocalStore], encryption: Encryption):
        self._file_system = file_system
        self._store_provider = store_provider
        self._encryption = encryption

    def show(self, doc: list[str], popup_dict: Optional[dict[str, str]] = None, initial_index: int = 0) -> bool:
        view_document(doc, popup_dict or {}, initial_index, self._store_provider.get().get_theme() if self._encryption.validate_key() == EncryptionResult.Success else None)
        return True

    def load_log_document(self) -> list[str]:
        return create_log_document(self._file_system.resolve(FILE_update_all_log))


def adjust_document(document: list[str], max_cols: int) -> list[str]:
    new_doc = []
    for line in document:
        nl = '\n' if line.endswith('\n') else ''
        line = line.rstrip('\n')

        if len(line) <= max_cols:
            new_doc.append(line + nl)
        else:
            full_chunks = len(line) // max_cols
            for i in range(full_chunks):
                chunk = line[i * max_cols:(i + 1) * max_cols]
                new_doc.append(chunk + nl)

            rem = len(line) % max_cols
            if rem:
                tail = line[-rem:]
                new_doc.append(tail + nl)

    return new_doc


def adjust_popup_dict(popup_dict: dict[int, list[str]], max_cols: int) -> dict[int, list[str]]:
    new_dict = {}
    for key, lines in popup_dict.items():
        new_dict[key] = adjust_document(lines, max_cols)
    return new_dict


import curses


def view_document(document: list[str], popup_dict: dict[int, list[str]], initial_index: int, theme: Optional[str]) -> None:
    def loader(screen: curses.window):
        if theme is not None and theme != 'none':
            init_colors()
            make_color_theme(theme).viewer()

        window = screen.subwin(0, 0)
        window.keypad(True)
        curses.cbreak()
        curses.curs_set(0)
        window.nodelay(True)
        window.timeout(50)
        window.clear()

        ViewerGui(
            window,
            curses.COLS,
            curses.LINES,
            adjust_document(document, curses.COLS),
            initial_index,
            adjust_popup_dict(popup_dict, curses.COLS)
        ).loop()

    curses.wrapper(loader)


class ViewerGui:
    def __init__(self, window: 'curses.window', max_cols: int, max_lines: int, document: list[str], initial_index: int, popup_dict: dict[int, list[str]]):
        self.window = window
        self.mcols = max_cols
        self.mlines = max_lines
        self.document = document
        self.initial_index = initial_index
        hud_size = 2
        self.frame_start = hud_size
        self.frame_end = max_lines - hud_size * 2
        self.mindex = len(document) - self.frame_end

    def addstr(self, y: int, x: int, text: str, attr: int):
        x, length = clip_range(x, len(text), self.mcols - 1)
        self.window.addstr(clamp(y, 0, self.mlines - 1), x, text[:length], attr | curses.color_pair(colors.COMMON_TEXT_COLOR))

    def vline(self, y: int, x: int, attr: int, length: int):
        y, length = clip_range(y, length, self.mlines)
        self.window.vline(y, clamp(x, 0, self.mcols - 1), attr | curses.color_pair(colors.COMMON_TEXT_COLOR), length)

    def hline(self, y: int, x: int, attr: int, length: int):
        x, length = clip_range(x, length, self.mcols)
        self.window.hline(clamp(y, 0, self.mlines - 1), x, attr | curses.color_pair(colors.COMMON_TEXT_COLOR), length)

    def draw_hud(self, hud_message: str, hud_percent: str, top: bool=True) -> None:
        if top:
            y_text, y_line = 0, 1
            corner_left, corner_right, tee = curses.ACS_LLCORNER, curses.ACS_LRCORNER, curses.ACS_BTEE
        else:
            y_text, y_line = self.mlines - 1, self.mlines - 2
            corner_left, corner_right, tee = curses.ACS_ULCORNER, curses.ACS_URCORNER, curses.ACS_TTEE

        self.addstr(y_text, int(self.mcols / 2 - len(hud_message) / 2), hud_message, curses.A_NORMAL)
        self.addstr(y_text, self.mcols - 5, '   %', curses.A_NORMAL)
        self.addstr(y_text, self.mcols - len(hud_percent) - 1, hud_percent, curses.A_NORMAL)

        for x in (0, self.mcols - 6, self.mcols - 1):
            self.vline(y_text, x, curses.ACS_VLINE, 1)

        self.hline(y_line, 0, corner_left, 1)
        self.hline(y_line, 1, curses.ACS_HLINE, self.mcols - 1)
        self.hline(y_line, self.mcols - 6, tee, 1)
        self.hline(y_line, self.mcols - 1, corner_right, 1)

    def loop(self):
        index = self.initial_index
        last_index = None
        viewing = True

        self.window.bkgd(' ', curses.color_pair(colors.BOX_BACKGROUND_COLOR))

        while viewing:
            if last_index is None or last_index != index:
                last_index = index

                if len(self.document) > self.mlines:
                    page = self.document[len(self.document) - index - self.frame_end:len(self.document) - index]
                else:
                    page = self.document

                for i, line in enumerate(page):
                    self.addstr(i + self.frame_start, 0, line, curses.A_NORMAL)

                hud_message = 'Press UP/DOWN LEFT/RIGHT to navigate, and any other button to EXIT'
                hud_percent = f'{100 - (int(index * 100 / self.mindex))}%'
                self.draw_hud(hud_message, hud_percent, top=True)
                self.draw_hud(hud_message, hud_percent, top=False)

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
