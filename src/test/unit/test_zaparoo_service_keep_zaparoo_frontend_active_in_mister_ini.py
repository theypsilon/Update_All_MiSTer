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
import os
import unittest

from update_all.zaparoo_service import keep_zaparoo_frontend_active_in_mister_ini


MISTER_INI_FIXTURES_DIR = os.path.join(
    os.path.dirname(__file__), '..', 'fixtures', 'zaparoo_mister_ini'
)


def _read_mister_ini_fixture(scenario: str, kind: str) -> str:
    path = os.path.join(MISTER_INI_FIXTURES_DIR, f'{scenario}.{kind}.ini')
    with open(path, 'r') as f:
        return f.read()


class TestZaparooServiceKeepZaparooFrontendActiveInMisterIni(unittest.TestCase):
    """Narrow unit tests for keep_zaparoo_frontend_active_in_mister_ini.

    Each scenario has matching fixtures under
    ``src/test/fixtures/zaparoo_mister_ini/`` named
    ``<scenario>.input.ini`` (what the function receives) and
    ``<scenario>.expected.ini`` (what the function must return).
    """

    def _assert_transform(self, scenario: str) -> None:
        input_contents = _read_mister_ini_fixture(scenario, 'input')
        expected_contents = _read_mister_ini_fixture(scenario, 'expected')
        self.assertEqual(
            expected_contents,
            keep_zaparoo_frontend_active_in_mister_ini(input_contents),
        )

    def test_when_input_is_empty___creates_mister_section_with_main(self):
        self._assert_transform('empty_file')

    def test_when_file_has_no_mister_section___prepends_mister_section_with_main(self):
        self._assert_transform('file_without_mister_section')

    def test_when_mister_section_has_no_main___inserts_main_at_end_of_section(self):
        self._assert_transform('mister_section_without_main')

    def test_when_mister_section_at_end_lacks_trailing_newline___appends_main_with_newlines(self):
        self._assert_transform('mister_section_at_end_without_trailing_newline')

    def test_when_mister_section_has_different_main___replaces_main_value(self):
        self._assert_transform('mister_section_with_different_main')

    def test_when_mister_section_already_has_correct_main___returns_contents_unchanged(self):
        self._assert_transform('mister_section_with_correct_main')

    def test_when_mister_section_has_correct_main_with_different_casing___returns_contents_unchanged(self):
        self._assert_transform('mister_section_with_correct_main_uppercase')

    def test_when_correct_main_has_extra_whitespace_around_equals___returns_contents_unchanged(self):
        # The firmware's INI parser (Main_MiSTer/cfg.cpp, ini_parse_var) skips any
        # run of spaces/tabs and '=' around the value, so "main   =   zaparoo/MiSTer_Zaparoo"
        # is read identically to "main=zaparoo/MiSTer_Zaparoo". The frontend is already
        # active, so we must leave the user's spacing untouched rather than rewrite it.
        self._assert_transform('mister_section_with_correct_main_extra_spaces')

    def test_when_correct_main_has_inline_comment___returns_contents_unchanged(self):
        self._assert_transform('mister_section_with_main_inline_comment')

    def test_when_input_is_realistic_mister_ini_with_other_sections___only_replaces_main_inside_mister_section(self):
        self._assert_transform('realistic_mister_ini_with_comments_and_other_sections')
