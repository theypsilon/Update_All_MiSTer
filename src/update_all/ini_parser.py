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

import distutils
import distutils.util


class IniParser:
    def __init__(self, ini_args):
        self._ini_args = {k.lower(): v for k, v in ini_args.items()}

    def get_string(self, key, default):
        result = self._ini_args.get(key, default)
        if result is None:
            return None
        return self._ini_args.get(key, default).strip('"\' ')

    def get_bool(self, key, default):
        return bool(distutils.util.strtobool(self.get_string(key, 'true' if default else 'false')))

    def get_int(self, key, default):
        result = self.get_string(key, None)
        if result is None:
            return default

        return to_int(result, default)

    def has(self, key):
        return self._ini_args.get(key) is not None


def to_int(n, default):
    try:
        return int(n)
    except ValueError as _:
        if isinstance(default, Exception):
            raise default
        return default
