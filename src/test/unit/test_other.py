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

import unittest

from update_all.other import any_to_bool, any_to_nonfalsy_str, calculate_overscan, OverscanDim, TerminalSize


class TestOther(unittest.TestCase):
    def test_any_to_bool(self):
        cases = [
            (True, False, True),
            (False, False, False),
            ('true', False, True),
            ('false', False, False),
            (None, False, False),
            (None, True, True),
        ]
        for value, default, expected in cases:
            with self.subTest(value=value, default=default, expected=expected):
                self.assertEqual(expected, any_to_bool(value, default=default))

    def test_any_to_nonfalsy_str(self):
        cases = [
            ('abc', 'abc'),
            ('  abc  ', 'abc'),
            ('', None),
            ('   ', None),
            (None, None),
        ]
        for value, expected in cases:
            with self.subTest(value=value, expected=expected):
                self.assertEqual(expected, any_to_nonfalsy_str(value))

    def test_calculate_overscan(self):
        def _size(columns=100, lines=50):
            return TerminalSize(columns=columns, lines=lines)

        cases = [
            ('maximum',   _size(),         OverscanDim(cols=10, lines=5)),
            ('high',    _size(),         OverscanDim(cols=8, lines=4)),
            ('medium', _size(),         OverscanDim(cols=5, lines=2)),
            ('small',  _size(),         OverscanDim(cols=2, lines=1)),
            ('none',   _size(),         OverscanDim(cols=0, lines=0)),
            ('banana', _size(80, 24),   OverscanDim(cols=0, lines=0)),
            ('none',   _size(40, 18),   OverscanDim(cols=0, lines=0)),
            ('small',  _size(40, 18),   OverscanDim(cols=1, lines=0)),
            ('medium', _size(40, 18),   OverscanDim(cols=2, lines=1)),
            ('high',    _size(40, 18),   OverscanDim(cols=3, lines=1)),
            ('maximum',   _size(40, 18),   OverscanDim(cols=4, lines=2)),
        ]
        for label, size, expected in cases:
            with self.subTest(label=label, size=size):
                self.assertEqual(str(expected), str(calculate_overscan(label, size)))
