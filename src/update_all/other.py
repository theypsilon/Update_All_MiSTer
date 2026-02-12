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

import hashlib
import os
import sys
from functools import cached_property
from typing import Generic, TypeVar
import shutil
import types

if 'unittest' in sys.modules.keys():
    import inspect
from pathlib import Path


class UnreachableException(Exception):
    pass


_calling_test_only = False


def strtobool(val: str):
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return 1
    elif val in ('n', 'no', 'f', 'false', 'off', '0', ''):
        return 0
    else:
        raise ValueError("invalid truth value %r" % (val,))


def empty_store_without_base_path():
    return {}


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



_terminal_size = None
def terminal_size():
    global _terminal_size
    if _terminal_size is None:
        size = shutil.get_terminal_size()
        columns = size.columns if size.columns != 40 else 39
        _terminal_size = types.SimpleNamespace(columns=columns, lines=size.lines)
    return _terminal_size
