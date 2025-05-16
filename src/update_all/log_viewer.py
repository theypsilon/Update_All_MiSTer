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

        def create_document(maxw: int) -> list[str]:
            document = []
            for raw in itertools.dropwhile(lambda ln: ln != "\n", file_content):   # Skips the first debug lines
                no_ansi = strip_ansi(raw)
                nl = '\n' if no_ansi.endswith('\n') else ''
                line = no_ansi.rstrip('\n')

                if len(line) <= maxw:
                    document.append(line + nl)
                else:
                    full_chunks = len(line) // maxw
                    for i in range(full_chunks):
                        chunk = line[i * maxw:(i + 1) * maxw]
                        document.append(chunk + nl)

                    rem = len(line) % maxw
                    if rem:
                        tail = line[-rem:]
                        document.append(tail + nl)
            return document

        def draw_hud(window: curses.window, maxw: int, hud_message: str, hud_percent: str, top: bool=True) -> None:
            if top:
                y_text, y_line = 0, 1
                corner_left, corner_right, tee = curses.ACS_LLCORNER, curses.ACS_LRCORNER, curses.ACS_BTEE
            else:
                y_text, y_line = curses.LINES - 1, curses.LINES - 2
                corner_left, corner_right, tee = curses.ACS_ULCORNER, curses.ACS_URCORNER, curses.ACS_TTEE

            window.addstr(y_text, int(maxw / 2 - len(hud_message) / 2), hud_message, curses.A_NORMAL)
            window.addstr(y_text, maxw - 5, '   %', curses.A_NORMAL)
            window.addstr(y_text, maxw - len(hud_percent) - 1, hud_percent, curses.A_NORMAL)

            for x in (0, maxw - 6, maxw - 1):
                window.vline(y_text, x, curses.ACS_VLINE, 1)

            window.hline(y_line, 0, corner_left, 1)
            window.hline(y_line, 1, curses.ACS_HLINE, maxw - 1)
            window.hline(y_line, maxw - 6, tee, 1)
            window.hline(y_line, maxw - 1, corner_right, 1)

        def loader(screen: curses.window):
            window = screen.subwin(0, 0)
            window.keypad(True)
            curses.cbreak()
            curses.curs_set(0)
            window.nodelay(True)
            window.timeout(50)
            window.clear()
            viewing = True
            hud_size = 2
            index = 0
            maxw = curses.COLS

            document = create_document(maxw)

            frame_start = hud_size
            frame_end = curses.LINES - hud_size * 2

            max_index = len(document) - frame_end
            last_index = None

            while viewing:
                if last_index is None or last_index != index:
                    last_index = index

                    if len(document) > curses.LINES:
                        page = document[len(document) - index - frame_end:len(document) - index]
                    else:
                        page = document

                    for i, line in enumerate(page):
                        window.addstr(i + frame_start, 0, line, curses.A_NORMAL)

                    hud_message = 'Press UP/DOWN LEFT/RIGHT to navigate, and any other button to EXIT'
                    hud_percent = f'{100 - (int(index * 100 / max_index))}%'
                    draw_hud(window, maxw, hud_message, hud_percent, top=True)
                    draw_hud(window, maxw, hud_message, hud_percent, top=False)

                key = window.getch()
                if key == curses.KEY_UP:
                    index += 1
                elif key == curses.KEY_DOWN:
                    index -= 1
                elif key == curses.KEY_LEFT or key == curses.KEY_PPAGE:
                    index += curses.LINES
                elif key == curses.KEY_RIGHT or key == curses.KEY_NPAGE:
                    index -= curses.LINES
                elif key != -1:
                    viewing = False

                if index < 0:
                    index = 0
                elif index > max_index:
                    index = max_index

                curses.doupdate()

        try:
            curses.wrapper(loader)
            return True
        except Exception as e:
            print("Error:")
            print(e)
            return False

def get_cmdline(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            data = f.read()
        parts = data.split(b"\0")
        return [p.decode("utf-8", "ignore") for p in parts if p]
    except Exception:
        return []

if __name__ == "__main__":
    import sys, signal
    parent = os.getppid()
    cmdline = get_cmdline(parent)
    print(f"Parent PID: {parent} | Command line: {cmdline}")

    log_path = sys.argv[1] if len(sys.argv) > 1 else '/media/fat/Scripts/.config/update_all/update_all.log'
    print(f"Log file: {log_path}")
    LogViewer().show(log_path)

    if '/tmp/script' in cmdline:
        os.kill(parent, signal.SIGHUP)
