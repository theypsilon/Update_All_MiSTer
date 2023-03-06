#!/usr/bin/env python3
# Copyright (c) 2022-2023 José Manuel Barroso Galindo <theypsilon@gmail.com>

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

if 'unittest' in sys.modules.keys():
    import inspect
from pathlib import Path


class UnreachableException(Exception):
    pass


_calling_test_only = False


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
    _object: TObject

    def __init__(self):
        self._object = None

    def initialize(self, o: TObject) -> None:
        if self._object is not None:
            raise Exception(f"{self.__orig_class__.__args__[0].__name__} must be initialized only once.")
        self._object = o

    def get(self) -> TObject:
        if self._object is None:
            raise Exception(f"{self.__orig_class__.__args__[0].__name__} must be initialized before calling this method.")
        return self._object


class Checker:
    def __init__(self, file_system):
        self._file_system = file_system

    @cached_property
    def available_code(self) -> int:
        path = ''.join([chr(ord(c) - i - 3) for i, c in enumerate(_parameters[0])])
        if not self._file_system.is_file(path):
            return -1

        file_size = os.path.getsize(self._file_system.download_target_path(path))
        if file_size != _parameters[1]:
            return 0

        file_md5 = hashlib.md5(self._file_system.read_file_binary(path)).hexdigest()
        if file_md5 != _parameters[2]:
            return 1

        return 2


_parameters = ['Vgwow||9|qoupsCx', 16384, "00e9f6acaec74650ddd38a14334ebaef"]
