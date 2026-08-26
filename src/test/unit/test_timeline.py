#!/usr/bin/env python3

# Copyright (c) 2022-2026 José Manuel Barroso Galindo <theypsilon@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# You can download the latest version of this tool from:
# https://github.com/theypsilon/Update_All_MiSTer

import unittest
from typing import Optional

from update_all.timeline import add_doc_section


class TestAddDocSection(unittest.TestCase):
    def test_add_doc_section___renders_the_title_and_the_separator_before_the_categories(self):
        doc: list[str] = []

        add_doc_section(doc, _section('arcade', ['Pooyan Core']), {}, 4)

        self.assertEqual(['>>> UPDATED TODAY:\n', '----\n', ' [Arcade] Pooyan Core\n', '\n'], doc)

    def test_add_doc_section___with_a_single_system_file___labels_it_system_file(self):
        self.assertEqual([' [System file] MiSTer\n'], _category_lines('system', ['MiSTer']))

    def test_add_doc_section___with_many_system_files___labels_them_system_files(self):
        self.assertEqual([
            ' [System files]\n',
            '  • MiSTer\n',
            '  • Menu Core\n',
        ], _category_lines('system', ['MiSTer', 'Menu Core']))

    def test_add_doc_section___with_a_single_utility_file___labels_it_utility(self):
        self.assertEqual([' [Utility] Update All\n'], _category_lines('utility', ['Update All']))

    def test_add_doc_section___with_many_utility_files___labels_them_utilities(self):
        self.assertEqual([
            ' [Utilities]\n',
            '  • Update All\n',
            '  • Downloader\n',
        ], _category_lines('utility', ['Update All', 'Downloader']))

    def test_add_doc_section___with_many_files_of_a_regular_category___appends_an_s(self):
        self.assertEqual([
            ' [Arcades]\n',
            '  • Pooyan Core\n',
            '  • QBert Core\n',
        ], _category_lines('arcade', ['Pooyan Core', 'QBert Core']))

    def test_add_doc_section___with_a_category_that_is_a_substring_of_system___does_not_label_it_as_a_system_file(self):
        for category, expected in [('sys', ' [Sys] Some File\n'), ('tem', ' [Tem] Some File\n'), ('', ' [] Some File\n')]:
            with self.subTest(category=category):
                self.assertEqual([expected], _category_lines(category, ['Some File']))

    def test_add_doc_section___translates_file_names_with_the_names_dict(self):
        self.assertEqual([' [Arcade] Pooyan\n'], _category_lines('arcade', ['Pooyan Core'], {'Pooyan Core': 'Pooyan'}))

    def test_add_doc_section___without_categories___renders_nothing(self):
        doc: list[str] = []

        add_doc_section(doc, {'title': 'Updated today', 'categories': []}, {}, 4)

        self.assertEqual([], doc)


def _category_lines(category: str, names: list[str], names_dict: Optional[dict] = None) -> list[str]:
    doc: list[str] = []
    add_doc_section(doc, _section(category, names), names_dict or {}, 4)
    return doc[2:-1]


def _section(category: str, names: list[str]) -> dict:
    return {
        'title': 'Updated today',
        'categories': [{
            'category': category,
            'files': [{'name': name, 'type': 'standalone'} for name in names],
        }],
    }


if __name__ == '__main__':
    unittest.main()
