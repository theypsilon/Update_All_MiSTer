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

import configparser
from pathlib import Path


def assertEqualIni(suite, expected, actual):
    expected_ini = testableIni(expected)
    actual_ini = testableIni(actual)
    suite.assertEqual(expected_ini, actual_ini)


def testableIni(ini_str):
    ini_str_path = Path(ini_str)
    ini_content = ini_str
    try:
        if ini_str_path.exists():
            ini_content = ini_str_path.read_text()
    except OSError as _e:
        pass

    return sortIni(ini_content)


def sortIni(ini_content):
    result = ''
    config = configparser.ConfigParser()
    config.read_string(ini_content)

    for section in sorted(config.sections(), key=lambda x: x.lower()):
        result += f'[{section}]\n'
        for key, value in sorted(config[section].items()):
            result += f'{key} = {value}\n'
        result += '\n'

    return result
