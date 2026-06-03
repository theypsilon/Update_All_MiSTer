#!/usr/bin/env python3
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

import sys
import os
import zipfile
from typing import Generic, TypeVar, NamedTuple, Protocol
import shutil
import types

if 'unittest' in sys.modules.keys():
    import inspect
from pathlib import Path


class UnreachableException(Exception):
    pass


_calling_test_only = False


def str_to_bool(val: str):
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return 1
    elif val in ('n', 'no', 'f', 'false', 'off', '0', ''):
        return 0
    else:
        raise ValueError("invalid truth value %r" % (val,))


def any_to_bool(val, default=False):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return bool(str_to_bool(val))
    return default


def any_to_nonfalsy_str(val):
    if not isinstance(val, str):
        return None
    val = val.strip()
    return val if val else None


def current_update_all_archive_path():
    current_path = sys.argv[0]
    if not current_path or not os.path.isfile(current_path):
        return None
    return current_path if zipfile.is_zipfile(current_path) else None


def empty_store_without_base_path():
    return {}


def _current_tty() -> str:
    try:
        return os.ttyname(0)
    except OSError:
        return ''


def _process_parent_pid(pid: int) -> int:
    try:
        with open(f'/proc/{pid}/status', 'r') as f:
            for line in f:
                if line.startswith('PPid:'):
                    return int(line.split()[1])
    except Exception:
        pass
    return 0


def _process_comm(pid: int) -> str:
    try:
        with open(f'/proc/{pid}/comm', 'r') as f:
            return f.read().strip()
    except Exception:
        return ''


def _process_cmdline(pid: int) -> str:
    try:
        with open(f'/proc/{pid}/cmdline', 'rb') as f:
            return f.read().replace(b'\0', b' ').decode(errors='replace').strip()
    except Exception:
        return ''


def _ancestor_process_descriptions(max_depth: int = 16) -> list[tuple[str, str]]:
    result = []
    pid = os.getpid()
    for _ in range(max_depth):
        pid = _process_parent_pid(pid)
        if pid in (0, 1):
            break
        result.append((_process_comm(pid), _process_cmdline(pid)))
    return result


def is_mister_scripts_menu_fb_launch() -> bool:
    if _current_tty() != '/dev/tty2':
        return False

    has_script_wrapper = False
    has_mister_firmware = False
    for comm, cmdline in _ancestor_process_descriptions():
        if '/tmp/script' in cmdline:
            has_script_wrapper = True
        if comm == 'MiSTer' or '/MiSTer' in cmdline:
            has_mister_firmware = True

    return has_script_wrapper and has_mister_firmware


def test_only(func):
    def wrapper(*args, **kwargs):
        if 'unittest' not in sys.modules.keys():
            raise Exception('Function "%s" can only be used during "unittest" runs.' % func.__name__)

        stack = inspect.stack()
        frame = stack[1]
        global _calling_test_only
        if not _calling_test_only and 'test' not in list(Path(frame.filename).parts):
            raise Exception('Function "%s" can only be called directly from a test file.' % func.__name__)

        _calling_test_only = True
        result = func(*args, **kwargs)
        _calling_test_only = False
        return result

    return wrapper


class ClosableValue:
    def __init__(self, value, callback):
        self.value = value
        self._callback = callback

    def close(self):
        self._callback()


TObject = TypeVar('TObject')


class GenericProvider(Generic[TObject]):
    def __init__(self):
        self._object: TObject = None

    def initialize(self, o: TObject) -> None:
        if self._object is not None:
            raise Exception(f"{self.__orig_class__.__args__[0].__name__} must be initialized only once.")
        self._object = o

    def get(self) -> TObject:
        if self._object is None:
            raise Exception(f"{self.__orig_class__.__args__[0].__name__} must be initialized before calling this method.")
        return self._object


class OverscanDim(NamedTuple):
    cols: int = 0
    lines: int = 0

class TerminalSize(NamedTuple):
    columns: int
    lines: int
    lnarrow: bool = False
    cnarrow: bool = False

class ScreenDims(Protocol):
    term_size: TerminalSize
    overscan_dim: OverscanDim

def are_dims_narrow(lines: int, columns: int) -> tuple[int, int]:
    return lines <= 18, columns <= 48

def terminal_size() -> TerminalSize:
    ts = shutil.get_terminal_size()
    lnarrow, cnarrow = are_dims_narrow(ts.lines, ts.columns)
    return TerminalSize(columns=ts.columns, lines=ts.lines,lnarrow=lnarrow, cnarrow=cnarrow)

def calculate_overscan(overscan_label: str, size: TerminalSize) -> OverscanDim:
    if overscan_label == 'maximum':
        overscan_percent = 10.0
    elif overscan_label == 'high':
        overscan_percent = 7.5
    elif overscan_label == 'medium':
        overscan_percent = 5.0
    elif overscan_label == 'small' or overscan_label == 'low':
        overscan_percent = 2.5
    else:
        overscan_percent = 0

    overscan_cols = round(size.columns * overscan_percent / 100)
    overscan_lines = round(size.lines * overscan_percent / 100)
    return OverscanDim(overscan_cols, overscan_lines)


def calculate_outer_box(screen_dims):
    ts = screen_dims.term_size
    oc = screen_dims.overscan_dim
    if oc.cols <= 0 and oc.lines <= 0:
        return None
    return oc.lines - 1, ts.lines - oc.lines, oc.cols - 1, ts.columns - oc.cols
