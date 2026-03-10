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
from io import StringIO
from unittest.mock import patch

from update_all.logger import apply_overscan_to_text, PrintLogger


class TestApplyOverscanToText(unittest.TestCase):

    # --- Basic padding ---

    def test_apply_overscan_to_text___with_short_text___adds_left_padding(self):
        result = apply_overscan_to_text(['hello'], '', columns=40, overscan=2)
        self.assertEqual(['  hello'], result)

    def test_apply_overscan_to_text___with_overscan_4___adds_4_spaces(self):
        result = apply_overscan_to_text(['hi'], '', columns=40, overscan=4)
        self.assertEqual(['    hi'], result)

    # --- Args joining ---

    def test_apply_overscan_to_text___with_multiple_args_empty_sep___concatenates(self):
        result = apply_overscan_to_text(['ab', 'cd'], '', columns=40, overscan=2)
        self.assertEqual(['  abcd'], result)

    def test_apply_overscan_to_text___with_multiple_args_and_sep___joins_with_sep(self):
        result = apply_overscan_to_text(['ab', 'cd'], ', ', columns=40, overscan=2)
        self.assertEqual(['  ab, cd'], result)

    def test_apply_overscan_to_text___with_non_string_args___converts_to_string(self):
        result = apply_overscan_to_text([42, True], ' ', columns=40, overscan=2)
        self.assertEqual(['  42 True'], result)

    # --- Word wrapping ---

    def test_apply_overscan_to_text___with_words_fitting_usable___no_wrap(self):
        # columns=20, overscan=2 -> usable=16
        result = apply_overscan_to_text(['hello world'], '', columns=20, overscan=2)
        self.assertEqual(['  hello world'], result)

    def test_apply_overscan_to_text___with_words_exceeding_usable___wraps_at_word_boundary(self):
        # columns=20, overscan=2 -> usable=16
        result = apply_overscan_to_text(['hello beautiful world'], '', columns=20, overscan=2)
        self.assertEqual(['  hello beautiful', '  world'], result)

    def test_apply_overscan_to_text___with_multiple_words_wrapping___wraps_at_boundaries(self):
        # columns=20, overscan=3 -> usable=14
        result = apply_overscan_to_text(['The quick brown fox jumps over'], '', columns=20, overscan=3)
        self.assertEqual(['   The quick', '   brown fox', '   jumps over'], result)

    def test_apply_overscan_to_text___with_word_longer_than_usable___breaks_word(self):
        # columns=10, overscan=1 -> usable=8
        result = apply_overscan_to_text(['abcdefghijklmno'], '', columns=10, overscan=1)
        self.assertEqual([' abcdefgh', ' ijklmno'], result)

    def test_apply_overscan_to_text___with_exact_usable_width_text___no_wrap(self):
        # columns=20, overscan=2 -> usable=16
        result = apply_overscan_to_text(['abcdefghijklmnop'], '', columns=20, overscan=2)
        self.assertEqual(['  abcdefghijklmnop'], result)

    def test_apply_overscan_to_text___with_one_char_over_usable_no_spaces___breaks(self):
        # columns=20, overscan=2 -> usable=16
        result = apply_overscan_to_text(['abcdefghijklmnopq'], '', columns=20, overscan=2)
        self.assertEqual(['  abcdefghijklmnop', '  q'], result)

    # --- Empty text ---

    def test_apply_overscan_to_text___with_empty_args___returns_padded_empty(self):
        result = apply_overscan_to_text([], '', columns=40, overscan=2)
        self.assertEqual(['  '], result)

    def test_apply_overscan_to_text___with_empty_string_arg___returns_padded_empty(self):
        result = apply_overscan_to_text([''], '', columns=40, overscan=2)
        self.assertEqual(['  '], result)

    # --- All lines fit within columns ---

    def test_apply_overscan_to_text___all_output_lines_fit_within_columns(self):
        # columns=20, overscan=3 -> usable=14
        text = 'The quick brown fox jumps over'
        result = apply_overscan_to_text([text], '', columns=20, overscan=3)
        for line in result:
            self.assertLessEqual(len(line), 20, f'Line too wide: {line!r} ({len(line)} > 20)')

    def test_apply_overscan_to_text___all_lines_start_with_padding(self):
        # columns=10, overscan=2 -> usable=6
        result = apply_overscan_to_text(['abcdefghijklmno'], '', columns=10, overscan=2)
        for line in result:
            self.assertTrue(line.startswith('  '), f'Line missing padding: {line!r}')

    # --- Realistic terminal sizes ---

    def test_apply_overscan_to_text___with_40_col_terminal_small_overscan___wraps_at_word(self):
        # columns=39, overscan=2 -> usable=35
        text = 'The All-in-One Updater for MiSTer FPGA!!'  # 40 chars
        result = apply_overscan_to_text([text], '', columns=39, overscan=2)
        self.assertEqual(2, len(result))
        self.assertEqual('  The All-in-One Updater for MiSTer', result[0])
        self.assertEqual('  FPGA!!', result[1])

    def test_apply_overscan_to_text___with_40_col_terminal_medium_overscan___wraps_at_word(self):
        # columns=39, overscan=4 -> usable=31
        text = 'The All-in-One Updater for MiSTer'  # 34 chars
        result = apply_overscan_to_text([text], '', columns=39, overscan=4)
        self.assertEqual(2, len(result))
        self.assertEqual('    The All-in-One Updater for', result[0])
        self.assertEqual('    MiSTer', result[1])

    def test_apply_overscan_to_text___with_short_text_on_wide_terminal___single_line(self):
        result = apply_overscan_to_text(['hello world'], '', columns=80, overscan=2)
        self.assertEqual(['  hello world'], result)

    # --- Separator line patterns (no spaces, breaks by chars) ---

    def test_apply_overscan_to_text___with_separator_dashes___breaks_by_chars(self):
        # columns=20, overscan=2 -> usable=16
        text = '-' * 20
        result = apply_overscan_to_text([text], '', columns=20, overscan=2)
        self.assertEqual(['  ' + '-' * 16, '  ' + '-' * 4], result)

    def test_apply_overscan_to_text___with_separator_fitting_usable___no_wrap(self):
        # columns=20, overscan=2 -> usable=16
        text = '#' * 16
        result = apply_overscan_to_text([text], '', columns=20, overscan=2)
        self.assertEqual(['  ' + '#' * 16], result)

    # --- Hyphenated words ---

    def test_apply_overscan_to_text___with_hyphenated_word___does_not_break_at_hyphen(self):
        # columns=20, overscan=2 -> usable=16
        # "The All-in-One" is 14 chars, fits. "Tool" pushes to 19, wraps at word boundary.
        result = apply_overscan_to_text(['The All-in-One Tool'], '', columns=20, overscan=2)
        self.assertEqual(['  The All-in-One', '  Tool'], result)

    def test_apply_overscan_to_text___with_hyphenated_word_fitting___stays_on_one_line(self):
        # columns=20, overscan=2 -> usable=16
        result = apply_overscan_to_text(['All-in-One'], '', columns=20, overscan=2)
        self.assertEqual(['  All-in-One'], result)

    # --- Mixed content ---

    def test_apply_overscan_to_text___with_sentence_exactly_at_word_boundary___no_trailing_empty_line(self):
        # columns=20, overscan=2 -> usable=16
        result = apply_overscan_to_text(['hello world test'], '', columns=20, overscan=2)
        self.assertEqual(['  hello world test'], result)

    def test_apply_overscan_to_text___with_multiple_spaces___preserves_during_wrap(self):
        # columns=16, overscan=2 -> usable=12
        result = apply_overscan_to_text(['aaa bbb ccc ddd eee'], '', columns=16, overscan=2)
        self.assertEqual(['  aaa bbb ccc', '  ddd eee'], result)

    def test_print_logger___with_embedded_newlines___preserves_line_breaks_before_overscan(self):
        logger = PrintLogger()
        logger._overscan = 2
        logger._columns = 20

        with patch('sys.stdout', new_callable=StringIO) as stdout:
            logger.print('START!\nSECTION: jtcores', end='')

        self.assertEqual('  START!\n  SECTION: jtcores', stdout.getvalue())

    def test_print_logger___with_wrapped_text_and_embedded_newlines___preserves_both_wraps_and_line_breaks(self):
        logger = PrintLogger()
        logger._overscan = 2
        logger._columns = 20

        with patch('sys.stdout', new_callable=StringIO) as stdout:
            logger.print('abcdefghijklmnopq\nx', end='')

        self.assertEqual('  abcdefghijklmnop\n  q\n  x', stdout.getvalue())

    def test_print_logger___when_chunk_ends_with_newline___next_chunk_does_not_get_extra_padding(self):
        logger = PrintLogger()
        logger._overscan = 2
        logger._columns = 20

        with patch('sys.stdout', new_callable=StringIO) as stdout:
            logger.print('START!\n', end='')
            logger.print('SECTION: jtcores', end='')

        self.assertEqual('  START!\n  SECTION: jtcores', stdout.getvalue())


if __name__ == '__main__':
    unittest.main()
