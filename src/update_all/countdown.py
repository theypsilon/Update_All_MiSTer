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
import math
import os
import sys
import time
from abc import ABC, abstractmethod
from enum import unique, IntEnum, auto
from multiprocessing import Process, Value

from update_all.cli_output_formatting import bold
from update_all.logger import Logger


@unique
class CountdownOutcome(IntEnum):
    CONTINUE = auto()
    SETTINGS_SCREEN = auto()


class Countdown(ABC):
    @abstractmethod
    def execute_count(self, n) -> CountdownOutcome:
        """Runs a countdown for 'n' seconds, and returns the outcome"""


class CountdownImpl(Countdown):
    def __init__(self, logger: Logger):
        self._logger = logger

    def execute_count(self, count) -> CountdownOutcome:
        os_specifics = make_os_specifics()
        os_specifics.initialize()

        char = Value('i', 0)
        ends = Value('i', 0)

        child_process = Process(target=read_characters, args=(char, ends, os_specifics.context()), daemon=True)

        self._logger.print()
        self._logger.print(f" {bold('*')}Press <{bold('UP')}>, To enter the SETTINGS.")
        self._logger.print(f" {bold('*')}Press <{bold('DOWN')}>, To continue now.")
        self._logger.print()
        result = CountdownOutcome.CONTINUE

        try:
            child_process.start()

            begin = time.monotonic()
            end = begin + float(count)
            now = begin
            latest_seconds = -1
            while now < end:
                seconds = math.floor(end - now) + 1
                if seconds != latest_seconds:
                    dots = '.' * (count - seconds + 1)
                    print(f'\033[2K\rStarting in {seconds} seconds.{dots}', end='', flush=True)
                    latest_seconds = seconds

                char_value = chr(char.value)
                if char_value == 'A':
                    result = CountdownOutcome.SETTINGS_SCREEN
                    break
                elif char_value == 'B':
                    break

                time.sleep(1.0 / 120.0)
                now = time.monotonic()

        finally:
            ends.value = 1
            time.sleep(1.0 / 60.0)

            child_process.terminate()
            time.sleep(1.0 / 60.0)

            child_process.close()
            os_specifics.finalize()

        return result


def read_characters(char, ends, context):
    with context:
        while ends.value == 0:
            char.value = ord(_getch())
            time.sleep(1.0 / 120.0)


def make_getch():
    try:
        return _GetchWindows()
    except ImportError:
        return _GetchUnix()


class _GetchUnix:
    def __init__(self):
        import sys, tty, termios

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()


_getch = make_getch()


def make_os_specifics():
    try:
        return _OsSpecificsWindows()
    except ImportError:
        return _OsSpecificsLinux()


class _OsSpecificsLinux:
    def __init__(self):
        import tty, sys, termios
        self._oldtty = None
        self._fdstdin = sys.stdin.fileno()

    def initialize(self):
        import termios, sys
        self._oldtty = termios.tcgetattr(sys.stdin)

    def finalize(self):
        import termios, sys
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._oldtty)

    def context(self):
        return _LinuxContext(self._fdstdin)


class _LinuxContext(object):
    def __init__(self, fdstdin):
        self.fdstdin = fdstdin

    def __enter__(self):
        self.fin = os.fdopen(self.fdstdin)
        sys.stdin = self.fin
        return self

    def __exit__(self, ty, value, traceback):
        self.fin.close()


class _OsSpecificsWindows:
    def __init__(self):
        import msvcrt

    def initialize(self):
        pass

    def finalize(self):
        pass

    def context(self):
        return _WindowsContext()


class _WindowsContext(object):
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, ty, value, traceback):
        pass
