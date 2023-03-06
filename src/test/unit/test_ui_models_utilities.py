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
import unittest

from update_all.ui_model_utilities import gather_variable_declarations, \
    dynamic_convert_string


class TestUiModelsUtilities(unittest.TestCase):
    def test_gather_default_values(self):
        default_values = {k: dynamic_convert_string(v['default']) for k, v in gather_variable_declarations(test_model()).items()}
        expected = {
            "update_all_version": 2,
            "names_region": "US",
            "arcade_offset_downloader": False
        }
        self.assertEqual(expected, default_values)

    def test_list_variables_with_group_x(self):
        expected = {"update_all_version", "arcade_offset_downloader"}
        self.assertEqual(expected, set(gather_variable_declarations(test_model(), 'x')))


def test_model(): return {
    "variables": {
        "update_all_version": {"default": "2", "group": "x"},
    },
    "items": {
        "names_txt_menu": {
            "ui": "dialog_sub_menu",
            "header": "Names TXT Settings",
            "variables": {
                "names_region": {"default": "US", "values": ["US", "EU", "JP"]},
            },
        },
        "misc_menu": {
            "ui": "dialog_sub_menu",
            "header": "Misc | Other Settings",
            "variables": {
                "arcade_offset_downloader": {"default": "false", "group": "x", "values": ["false", "true"]},
            },
        }
    }
}
