#!/bin/python
# Copyright (c) 2022-2024 José Manuel Barroso Galindo <theypsilon@gmail.com>

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

def clamp(v, lo, hi): return max(lo, min(v, hi))
def clip_range(start: int, length: int, limit: int) -> tuple[int, int]:
    length = clamp(length, 1, limit)
    return clamp(start, 0, limit - length), length

class LogViewer:
    def show(self, file_path: str) -> bool:
        if not os.path.exists(file_path):
            return False

        import curses, re, itertools

        with open(file_path, 'r') as file:
            file_content = file.readlines()

        ansi_sgr = re.compile(r'\x1b\[[0-9;]*[mK]')

        def strip_ansi(line: str) -> str:
            return ansi_sgr.sub('', line)

        def create_document(max_cols: int) -> list[str]:
            document = []
            for raw in itertools.dropwhile(lambda ln: ln != "\n", file_content):   # Skips the first debug lines
                no_ansi = strip_ansi(raw)
                nl = '\n' if no_ansi.endswith('\n') else ''
                line = no_ansi.rstrip('\n')

                if len(line) <= max_cols:
                    document.append(line + nl)
                else:
                    full_chunks = len(line) // max_cols
                    for i in range(full_chunks):
                        chunk = line[i * max_cols:(i + 1) * max_cols]
                        document.append(chunk + nl)

                    rem = len(line) % max_cols
                    if rem:
                        tail = line[-rem:]
                        document.append(tail + nl)
            return document

        class ViewerGui:
            def __init__(self, window: curses.window, max_cols: int, max_lines: int, document: list[str]):
                self.window = window
                self.mcols = max_cols
                self.mlines = max_lines
                self.document = document
                hud_size = 2
                self.frame_start = hud_size
                self.frame_end = max_lines - hud_size * 2
                self.mindex = len(document) - self.frame_end

            def addstr(self, y: int, x: int, text: str, attr: int):
                x, length = clip_range(x, len(text), self.mcols - 1)
                self.window.addstr(clamp(y, 0, self.mlines - 1), x, text[:length], attr)

            def vline(self, y: int, x: int, attr: int, length: int):
                y, length = clip_range(y, length, self.mlines)
                self.window.vline(y, clamp(x, 0, self.mcols - 1), attr, length)

            def hline(self, y: int, x: int, attr: int, length: int):
                x, length = clip_range(x, length, self.mcols)
                self.window.hline(clamp(y, 0, self.mlines - 1), x, attr, length)

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
                index = 0
                last_index = None
                viewing = True

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

        def loader(screen: curses.window):
            window = screen.subwin(0, 0)
            window.keypad(True)
            curses.cbreak()
            curses.curs_set(0)
            window.nodelay(True)
            window.timeout(50)
            window.clear()

            ViewerGui(window, curses.COLS, curses.LINES, create_document(curses.COLS)).loop()

        curses.wrapper(loader)
        return True

if __name__ == "__main__":
    import sys, curses
    log_path = sys.argv[1] if len(sys.argv) > 1 else '/media/fat/Scripts/.config/update_all/update_all.log'
    try:
        success = LogViewer().show(log_path)
    except curses.error as e:
        success = False
        print('Your current terminal could not open a UI. Is it configured correctly?')

    if not success:
        print("Failed to display the log file: " + log_path)
        sys.exit(1)
