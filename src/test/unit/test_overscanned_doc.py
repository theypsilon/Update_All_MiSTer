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

from update_all.log_viewer import to_overscanned_doc


class TestToOverscannedDoc(unittest.TestCase):

    # --- No overscan ---

    def test_to_overscanned_doc___with_zero_overscan___returns_doc_unchanged(self):
        doc = [
            'short line\n',
            'this line is exactly twenty chars long!\n',
            'abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOP\n',
        ]
        result = to_overscanned_doc(doc, columns=40, cols_overscan=0)
        self.assertEqual(doc, result)

    # --- Basic padding ---

    def test_to_overscanned_doc___with_short_line___adds_left_padding(self):
        result = to_overscanned_doc(['hello\n'], columns=80, cols_overscan=4)
        self.assertEqual(['    hello\n'], result)

    def test_to_overscanned_doc___with_empty_newline___adds_padding(self):
        result = to_overscanned_doc(['\n'], columns=80, cols_overscan=2)
        self.assertEqual(['  \n'], result)

    def test_to_overscanned_doc___with_line_without_newline___adds_padding(self):
        result = to_overscanned_doc(['hello'], columns=80, cols_overscan=3)
        self.assertEqual(['   hello'], result)

    def test_to_overscanned_doc___with_multiple_lines___pads_all(self):
        doc = ['aaa\n', 'bbb\n', 'ccc\n']
        result = to_overscanned_doc(doc, columns=80, cols_overscan=2)
        self.assertEqual(['  aaa\n', '  bbb\n', '  ccc\n'], result)

    # --- Wrapping ---

    def test_to_overscanned_doc___with_long_line___wraps_to_usable_width(self):
        # columns=20, overscan=2 -> usable=16
        result = to_overscanned_doc(['abcdefghijklmnopqrstuvwxyz\n'], columns=20, cols_overscan=2)
        self.assertEqual(['  abcdefghijklmnop\n', '  qrstuvwxyz\n'], result)

    def test_to_overscanned_doc___with_wrapped_chunks___pads_all_chunks(self):
        # columns=10, overscan=1 -> usable=8
        result = to_overscanned_doc(['1234567890abcdef\n'], columns=10, cols_overscan=1)
        self.assertEqual([' 12345678\n', ' 90abcdef\n'], result)

    def test_to_overscanned_doc___with_line_exactly_usable_width___does_not_wrap(self):
        # columns=20, overscan=2 -> usable=16
        result = to_overscanned_doc(['abcdefghijklmnop\n'], columns=20, cols_overscan=2)
        self.assertEqual(['  abcdefghijklmnop\n'], result)

    def test_to_overscanned_doc___with_line_one_over_usable_width___wraps(self):
        # columns=20, overscan=2 -> usable=16
        result = to_overscanned_doc(['abcdefghijklmnopq\n'], columns=20, cols_overscan=2)
        self.assertEqual(['  abcdefghijklmnop\n', '  q\n'], result)

    # --- Edge cases ---

    def test_to_overscanned_doc___with_empty_doc___returns_empty(self):
        result = to_overscanned_doc([], columns=80, cols_overscan=4)
        self.assertEqual([], result)

    def test_to_overscanned_doc___with_empty_string_entry___adds_padding(self):
        result = to_overscanned_doc([''], columns=80, cols_overscan=2)
        self.assertEqual(['  '], result)

    def test_to_overscanned_doc___with_no_newline_long_line___wraps_without_adding_newlines(self):
        # columns=10, overscan=1 -> usable=8
        result = to_overscanned_doc(['abcdefghij'], columns=10, cols_overscan=1)
        self.assertEqual([' abcdefgh', ' ij'], result)

    def test_to_overscanned_doc___with_overscan_at_half_columns___returns_unchanged(self):
        doc = ['hello\n']
        result = to_overscanned_doc(doc, columns=10, cols_overscan=5)
        self.assertEqual(doc, result)

    def test_to_overscanned_doc___with_mixed_short_and_long_lines___handles_both(self):
        # columns=16, overscan=2 -> usable=12
        doc = ['short\n', 'this is a longer line\n', '\n']
        result = to_overscanned_doc(doc, columns=16, cols_overscan=2)
        self.assertEqual([
            '  short\n',
            '  this is a lo\n',
            '  nger line\n',
            '  \n',
        ], result)


if __name__ == '__main__':
    unittest.main()
