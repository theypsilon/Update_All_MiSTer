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

from update_all.log_viewer import calculate_hud_layout, calculate_hud_message, HudLayout, split_log_text_runs
from update_all.other import TerminalSize, OverscanDim, are_dims_narrow


class _ScreenDims:
    def __init__(self, term_size: TerminalSize, overscan_dim: OverscanDim):
        self.term_size = term_size
        self.overscan_dim = overscan_dim


def _terminal_size(columns: int, lines: int) -> TerminalSize:
    lnarrow, cnarrow = are_dims_narrow(lines, columns)
    return TerminalSize(columns=columns, lines=lines, lnarrow=lnarrow, cnarrow=cnarrow)


class TestLogViewer(unittest.TestCase):
    def test_split_log_text_runs___groups_text_and_symbol_segments(self):
        self.assertEqual(
            [('Hello', True), (' >>> ', False), ('world_123!?', True), (' []', False)],
            split_log_text_runs('Hello >>> world_123!? []'),
        )

    def test_split_log_text_runs___returns_empty_for_empty_text(self):
        self.assertEqual([], split_log_text_runs(''))

    def test_calculate_hud_message___uses_two_width_tiers_based_on_cnarrow(self):
        self.assertEqual(
            '←↑↓→ Navigate · Any other key to EXIT',
            str(calculate_hud_message(_ScreenDims(_terminal_size(columns=80, lines=40), OverscanDim()))),
        )
        self.assertEqual(
            '↑↓←→ Nav · Any key Exit',
            str(calculate_hud_message(_ScreenDims(_terminal_size(columns=40, lines=18), OverscanDim()))),
        )

    def test_calculate_hud_layout___without_overscan___uses_full_screen_bounds(self):
        screen_dims = _ScreenDims(_terminal_size(columns=80, lines=40), OverscanDim(cols=0, lines=0))

        self.assertEqual(
            HudLayout(
                left=0,
                width=80,
                top_text_y=0,
                top_line_y=1,
                bottom_line_y=38,
                bottom_text_y=39,
                page_top_y=2,
                page_rows=36,
            ),
            calculate_hud_layout(screen_dims),
        )

    def test_calculate_hud_layout___with_overscan___uses_usable_area_bounds(self):
        screen_dims = _ScreenDims(_terminal_size(columns=80, lines=40), OverscanDim(cols=4, lines=2))

        self.assertEqual(
            HudLayout(
                left=4,
                width=72,
                top_text_y=2,
                top_line_y=3,
                bottom_line_y=36,
                bottom_text_y=37,
                page_top_y=4,
                page_rows=32,
            ),
            calculate_hud_layout(screen_dims),
        )
