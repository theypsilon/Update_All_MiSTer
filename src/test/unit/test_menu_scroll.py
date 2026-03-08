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

from update_all.settings_screen_standard_curses_printer import _calculate_menu_scroll


class TestCalculateMenuScroll(unittest.TestCase):

    # --- Basic: no scrolling needed ---

    def test_selected_at_top_with_all_entries_visible_returns_zero(self):
        result = _calculate_menu_scroll(selected_idx=0, total_entries=5, max_entries=5, current_offset=0)
        self.assertEqual(0, result)

    def test_selected_at_bottom_with_all_entries_visible_returns_zero(self):
        result = _calculate_menu_scroll(selected_idx=4, total_entries=5, max_entries=5, current_offset=0)
        self.assertEqual(0, result)

    def test_fewer_entries_than_max_returns_zero(self):
        result = _calculate_menu_scroll(selected_idx=2, total_entries=3, max_entries=10, current_offset=0)
        self.assertEqual(0, result)

    # --- Scrolling down from offset 0 ---

    def test_scrolling_down_triggers_when_buffer_exceeded(self):
        # 10 entries, 5 visible. Selecting index 3 should trigger scroll (buffer at max_entries - 2 = 3)
        result = _calculate_menu_scroll(selected_idx=3, total_entries=10, max_entries=5, current_offset=0)
        self.assertGreater(result, 0)

    def test_no_scroll_when_within_buffer_from_top(self):
        # 10 entries, 5 visible. Selecting index 1 is within buffer.
        result = _calculate_menu_scroll(selected_idx=1, total_entries=10, max_entries=5, current_offset=0)
        self.assertEqual(0, result)

    # --- Scrolling up ---

    def test_scrolling_up_from_nonzero_offset(self):
        # Offset 5, selecting index 5 means selected - 1 < offset, should scroll up
        result = _calculate_menu_scroll(selected_idx=5, total_entries=15, max_entries=5, current_offset=5)
        self.assertLess(result, 5)

    def test_scrolling_up_to_top(self):
        result = _calculate_menu_scroll(selected_idx=0, total_entries=10, max_entries=5, current_offset=3)
        self.assertEqual(0, result)

    def test_scrolling_up_with_buffer(self):
        # Selecting index 3 with offset 4 means selected - 1 = 2 < 4, should scroll to show buffer above
        result = _calculate_menu_scroll(selected_idx=3, total_entries=15, max_entries=5, current_offset=4)
        self.assertLessEqual(result, 2)

    # --- Selected always visible ---

    def test_selected_entry_is_always_within_visible_range(self):
        for total in range(4, 20):
            for max_e in range(3, min(total, 10)):
                for sel in range(total):
                    for cur_off in range(total):
                        offset = _calculate_menu_scroll(sel, total, max_e, cur_off)
                        has_up = offset > 0
                        real_count = (max_e - 1) if has_up else max_e
                        real_end = offset + real_count
                        has_down = real_end < total
                        if has_down:
                            real_count -= 1
                            real_end = offset + real_count
                        self.assertGreaterEqual(sel, offset,
                            f'selected {sel} before offset {offset} (total={total}, max={max_e}, cur={cur_off})')
                        self.assertLess(sel, real_end,
                            f'selected {sel} >= real_end {real_end} (total={total}, max={max_e}, cur={cur_off})')

    # --- Offset never negative or beyond bounds ---

    def test_offset_never_negative(self):
        for sel in range(10):
            result = _calculate_menu_scroll(sel, total_entries=10, max_entries=5, current_offset=0)
            self.assertGreaterEqual(result, 0)

    def test_offset_never_exceeds_max_scroll(self):
        for sel in range(10):
            result = _calculate_menu_scroll(sel, total_entries=10, max_entries=5, current_offset=9)
            max_offset = 10 - (5 - 1)  # total - (max - 1)
            self.assertLessEqual(result, max_offset)

    # --- Sequential navigation (simulating cursor movement) ---

    def test_sequential_down_navigation(self):
        total, max_e = 12, 5
        offset = 0
        for sel in range(total):
            offset = _calculate_menu_scroll(sel, total, max_e, offset)
            self.assertGreaterEqual(offset, 0)
            self._assert_selected_visible(sel, total, max_e, offset)

    def test_sequential_up_navigation(self):
        total, max_e = 12, 5
        offset = _calculate_menu_scroll(total - 1, total, max_e, 0)
        for sel in range(total - 1, -1, -1):
            offset = _calculate_menu_scroll(sel, total, max_e, offset)
            self.assertGreaterEqual(offset, 0)
            self._assert_selected_visible(sel, total, max_e, offset)

    def test_down_then_up_returns_smoothly(self):
        total, max_e = 12, 5
        offset = 0
        # Navigate down to middle
        for sel in range(7):
            offset = _calculate_menu_scroll(sel, total, max_e, offset)
        # Navigate back up
        for sel in range(6, -1, -1):
            offset = _calculate_menu_scroll(sel, total, max_e, offset)
            self._assert_selected_visible(sel, total, max_e, offset)

    # --- Buffer behavior ---

    def test_downward_buffer_shows_next_entry(self):
        total, max_e = 12, 6
        offset = 0
        for sel in range(total):
            offset = _calculate_menu_scroll(sel, total, max_e, offset)
            has_up = offset > 0
            real_count = (max_e - 1) if has_up else max_e
            real_end = offset + real_count
            has_down = real_end < total
            if has_down:
                real_end = offset + real_count - 1
            # When not at the last visible entry before the down indicator,
            # the entry after selected should also be visible
            if has_down and sel < real_end - 1:
                self.assertLess(sel + 1, real_end,
                    f'next entry after selected {sel} not visible (offset={offset}, real_end={real_end})')

    def test_upward_buffer_shows_previous_entry(self):
        total, max_e = 12, 6
        # Start from bottom
        offset = _calculate_menu_scroll(total - 1, total, max_e, 0)
        for sel in range(total - 1, -1, -1):
            offset = _calculate_menu_scroll(sel, total, max_e, offset)
            has_up = offset > 0
            # When scrolled and not at the first visible entry after the up indicator,
            # the entry before selected should also be visible
            if has_up and sel > offset:
                self.assertGreater(sel - 1, offset - 1,
                    f'previous entry before selected {sel} not visible (offset={offset})')

    # --- Edge cases ---

    def test_single_entry(self):
        result = _calculate_menu_scroll(selected_idx=0, total_entries=1, max_entries=5, current_offset=0)
        self.assertEqual(0, result)

    def test_max_entries_equals_one(self):
        result = _calculate_menu_scroll(selected_idx=3, total_entries=5, max_entries=1, current_offset=0)
        self.assertGreaterEqual(result, 0)

    def test_selected_at_last_entry(self):
        result = _calculate_menu_scroll(selected_idx=9, total_entries=10, max_entries=5, current_offset=0)
        self.assertGreaterEqual(result, 0)
        self._assert_selected_visible(9, 10, 5, result)

    def _assert_selected_visible(self, sel, total, max_e, offset):
        has_up = offset > 0
        real_count = (max_e - 1) if has_up else max_e
        real_end = offset + real_count
        has_down = real_end < total
        if has_down:
            real_count -= 1
            real_end = offset + real_count
        self.assertGreaterEqual(sel, offset,
            f'selected {sel} before offset {offset}')
        self.assertLess(sel, real_end,
            f'selected {sel} >= real_end {real_end}')


if __name__ == '__main__':
    unittest.main()
