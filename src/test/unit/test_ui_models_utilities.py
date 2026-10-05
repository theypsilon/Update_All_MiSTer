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
import copy
import unittest

from test.ui_model_test_utils import frozen_model
from update_all.settings_screen_model import settings_screen_model
from update_all.ui_model_utilities import gather_variable_declarations, \
    dynamic_convert_string, gather_effects_by_type

_SETTINGS_SCREEN_GROUPS = (None, 'ao_ini', 'db', 'separate_db', 'ua_ini', 'store', 'manuals', 'artwork', 'artwork_style',
                           'artwork_screenshots', 'artwork_titles')


class TestUiModelsUtilities(unittest.TestCase):
    def test_frozen_model___fails_fast_on_any_write(self):
        model = frozen_model({'items': {'menu': {'entries': [{'title': 'a'}]}}})

        with self.assertRaises(TypeError):
            model['items']['menu']['title'] = 'b'
        with self.assertRaises(AttributeError):
            model['items']['menu']['entries'].append({})

    def test_lookups___on_a_frozen_settings_screen_model___match_the_bare_model(self):
        bare, frozen = settings_screen_model(), frozen_model(settings_screen_model())

        for group in _SETTINGS_SCREEN_GROUPS:
            self.assertEqual(
                gather_variable_declarations(bare, group),
                _thawed(gather_variable_declarations(frozen, group)),
                group,
            )
        self.assertEqual(
            gather_effects_by_type(bare, 'mister_ini_add'),
            [_thawed(effect) for effect in gather_effects_by_type(frozen, 'mister_ini_add')],
        )

    def test_lookups___leave_the_bare_settings_screen_model_untouched(self):
        model = settings_screen_model()
        before = copy.deepcopy(model)

        for group in _SETTINGS_SCREEN_GROUPS:
            gather_variable_declarations(model, group)
        gather_effects_by_type(model, 'mister_ini_add')

        self.assertEqual(before, model)

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


def _thawed(node):
    if isinstance(node, tuple):
        return [_thawed(value) for value in node]
    if hasattr(node, 'items'):
        return {key: _thawed(value) for key, value in node.items()}
    return node
