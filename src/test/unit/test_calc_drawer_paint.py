import unittest

from update_all.other import OverscanDim, TerminalSize, are_dims_narrow
from update_all.settings_screen_standard_curses_printer import DrawerPaintLayout, calc_drawer_paint


class TestCalcDrawerPaint(unittest.TestCase):

    def test_calc_drawer_paint___when_default_wide_layout___then_returns_base_drawer_paint_layout(self):
        actual = sut()

        expected = drawer_paint_layout()

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_headered_text_scrolls___then_marks_reset_and_keeps_header_scroll_state(self):
        actual = sut(header='Header', text_lines=_lines(40), text_scroll_offset=1)

        expected = drawer_paint_layout(
            layout_reset=True,
            max_length_header=6,
            offset_header=37,
            offset_horizontal=36,
            offset_text_line=36,
            offset_vertical=1,
            text_has_up_scroll=True,
            total_lines=37,
            total_width=7,
            visible_text_lines=_lines(40)[1:34] + ['--- ↓ ↓ ↓ ---'],
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_text_scrolls_without_header___then_uses_inline_scroll_markers(self):
        actual = sut(text_lines=_lines(40), text_scroll_offset=1)

        expected = drawer_paint_layout(
            layout_reset=True,
            offset_horizontal=36,
            offset_text_line=36,
            offset_vertical=1,
            total_lines=37,
            total_width=7,
            visible_text_lines=['--- ↑ ↑ ↑ ---'] + _lines(40)[2:36] + ['--- ↓ ↓ ↓ ---'],
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_text_scroll_starts_at_top___then_only_marks_more_content_below(self):
        actual = sut(text_lines=_lines(40), text_scroll_offset=0)

        expected = drawer_paint_layout(
            layout_reset=True,
            offset_horizontal=36,
            offset_text_line=36,
            offset_vertical=1,
            total_lines=37,
            total_width=7,
            visible_text_lines=_lines(40)[0:35] + ['--- ↓ ↓ ↓ ---'],
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_text_scroll_reaches_bottom_without_header___then_only_marks_more_content_above(self):
        actual = sut(text_lines=_lines(40), text_scroll_offset=4)

        expected = drawer_paint_layout(
            layout_reset=True,
            offset_horizontal=36,
            offset_text_line=36,
            offset_vertical=1,
            total_lines=37,
            total_width=7,
            visible_text_lines=['--- ↑ ↑ ↑ ---'] + _lines(40)[5:40],
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_line_narrow_menu_overflows___then_returns_scrolled_visible_entries_and_updates_scroll_offset(self):
        actual = sut(columns=80, lines=15, menu_entries=_menu_entries(14, 12), actions=[('<OK>', False)])

        expected = drawer_paint_layout(
            action_y=13,
            has_gap=False,
            layout_reset=False,
            max_length_option=3,
            menu_entries=[('--- ↑ ↑ ↑ ---', '', False)] + _menu_entries(14, 12)[2:14],
            menu_scroll_offset=2,
            offset_actions=38,
            offset_horizontal=37,
            offset_menu=37,
            offset_vertical=0,
            skip_header=True,
            total_lines=14,
            total_width=5,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_compact_menu_overflows_from_top___then_shows_only_bottom_scroll_marker(self):
        actual = sut(columns=80, lines=15, menu_entries=_menu_entries(14, 0), actions=ONE_ACTION)

        expected = drawer_paint_layout(
            action_y=13,
            has_gap=False,
            layout_reset=False,
            max_length_option=3,
            menu_entries=OVERFLOW_SHORT_TOP_SELECTED_MENU_ENTRIES,
            menu_scroll_offset=0,
            offset_actions=38,
            offset_horizontal=37,
            offset_menu=37,
            offset_vertical=0,
            skip_header=True,
            total_lines=14,
            total_width=5,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_compact_menu_overflows_to_last_page___then_shows_only_top_scroll_marker(self):
        actual = sut(columns=80, lines=15, menu_entries=_menu_entries(14, 13), actions=ONE_ACTION)

        expected = drawer_paint_layout(
            action_y=13,
            has_gap=False,
            layout_reset=False,
            max_length_option=3,
            menu_entries=OVERFLOW_SHORT_BOTTOM_SELECTED_MENU_ENTRIES,
            menu_scroll_offset=2,
            offset_actions=38,
            offset_horizontal=37,
            offset_menu=37,
            offset_vertical=0,
            skip_header=True,
            total_lines=14,
            total_width=5,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_compact_layout_can_fit_header___then_keeps_header_visible(self):
        actual = sut(columns=40, lines=15, header='Header', menu_entries=FEW_MENU_ENTRIES, actions=ONE_ACTION)

        expected = drawer_paint_layout(
            action_y=13,
            has_gap=True,
            max_length_header=6,
            max_length_option=2,
            menu_entries=FEW_MENU_ENTRIES,
            offset_actions=18,
            offset_header=17,
            offset_horizontal=17,
            offset_menu=18,
            offset_text_line=20,
            offset_vertical=4,
            skip_header=False,
            total_lines=6,
            total_width=6,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_compact_layout_has_gap_but_no_box_top___then_starts_at_overscan_floor(self):
        actual = sut(columns=40, lines=15, menu_entries=NO_BOX_TOP_MENU_ENTRIES, actions=ONE_ACTION)

        expected = drawer_paint_layout(
            action_y=13,
            has_gap=True,
            max_length_option=3,
            menu_entries=NO_BOX_TOP_MENU_ENTRIES,
            offset_actions=18,
            offset_header=20,
            offset_horizontal=17,
            offset_menu=17,
            offset_text_line=20,
            offset_vertical=0,
            skip_header=True,
            total_lines=14,
            total_width=5,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_standard_layout_has_vertical_overscan___then_uses_usable_height_for_offset(self):
        actual = sut(columns=80, lines=15, overscan_lines=2)

        expected = drawer_paint_layout(
            offset_vertical=7,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_narrow_screen_has_no_menu_entries___then_uses_standard_layout_path(self):
        actual = sut(columns=40, lines=15, actions=ONE_ACTION)

        expected = drawer_paint_layout(
            has_gap=True,
            offset_actions=18,
            offset_header=20,
            offset_horizontal=18,
            offset_menu=19,
            offset_text_line=20,
            offset_vertical=6,
            total_lines=2,
            total_width=4,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_actions_exceed_usable_width_with_overscan___then_clamps_action_offset_to_safe_floor(self):
        actual = sut(overscan_cols=4, actions=[('X' * 73, False)])

        expected = drawer_paint_layout(
            has_gap=True,
            offset_actions=4,
            offset_horizontal=4,
            total_lines=2,
            total_width=73,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_multiple_actions_are_present___then_action_gap_contributes_to_centering_and_width(self):
        actual = sut(actions=MULTIPLE_ACTIONS)

        expected = drawer_paint_layout(
            has_gap=True,
            offset_actions=32,
            offset_horizontal=32,
            total_lines=2,
            total_width=16,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_few_entries_on_wide_tall_screen_without_overscan___then_returns_standard_non_overflow_layout(self):
        actual = sut(columns=80, lines=40, menu_entries=FEW_MENU_ENTRIES, actions=ONE_ACTION)

        expected = drawer_paint_layout(
            has_gap=True,
            max_length_option=2,
            menu_entries=FEW_MENU_ENTRIES,
            offset_actions=38,
            offset_horizontal=38,
            offset_menu=38,
            offset_vertical=18,
            total_lines=4,
            total_width=4,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_few_entries_on_wide_tall_screen_with_overscan___then_returns_standard_non_overflow_layout(self):
        actual = sut(columns=80, lines=40, overscan_cols=2, overscan_lines=1, menu_entries=FEW_MENU_ENTRIES, actions=ONE_ACTION)

        expected = drawer_paint_layout(
            has_gap=True,
            max_length_option=2,
            menu_entries=FEW_MENU_ENTRIES,
            offset_actions=38,
            offset_horizontal=38,
            offset_menu=38,
            offset_vertical=18,
            total_lines=4,
            total_width=4,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_few_entries_on_cnarrow_tall_screen_without_overscan___then_returns_standard_non_overflow_layout(self):
        actual = sut(columns=40, lines=40, menu_entries=FEW_MENU_ENTRIES, actions=ONE_ACTION)

        expected = drawer_paint_layout(
            has_gap=True,
            max_length_option=2,
            menu_entries=FEW_MENU_ENTRIES,
            offset_actions=18,
            offset_header=20,
            offset_horizontal=18,
            offset_menu=18,
            offset_text_line=20,
            offset_vertical=18,
            skip_header=False,
            total_lines=4,
            total_width=4,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_few_entries_on_cnarrow_tall_screen_with_overscan___then_returns_standard_non_overflow_layout(self):
        actual = sut(columns=40, lines=40, overscan_cols=2, overscan_lines=1, menu_entries=FEW_MENU_ENTRIES, actions=ONE_ACTION)

        expected = drawer_paint_layout(
            has_gap=True,
            max_length_option=2,
            menu_entries=FEW_MENU_ENTRIES,
            offset_actions=18,
            offset_header=20,
            offset_horizontal=18,
            offset_menu=18,
            offset_text_line=20,
            offset_vertical=18,
            skip_header=False,
            total_lines=4,
            total_width=4,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_few_entries_on_wide_lnarrow_screen_without_overscan___then_returns_compact_non_overflow_layout(self):
        actual = sut(columns=80, lines=15, menu_entries=FEW_MENU_ENTRIES, actions=ONE_ACTION)

        expected = drawer_paint_layout(
            action_y=13,
            has_gap=True,
            max_length_option=2,
            menu_entries=FEW_MENU_ENTRIES,
            offset_actions=38,
            offset_horizontal=38,
            offset_menu=38,
            offset_vertical=5,
            skip_header=True,
            total_lines=4,
            total_width=4,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_few_entries_on_wide_lnarrow_screen_with_overscan___then_returns_compact_non_overflow_layout(self):
        actual = sut(columns=80, lines=15, overscan_cols=2, overscan_lines=1, menu_entries=FEW_MENU_ENTRIES, actions=ONE_ACTION)

        expected = drawer_paint_layout(
            action_y=12,
            has_gap=True,
            max_length_option=2,
            menu_entries=FEW_MENU_ENTRIES,
            offset_actions=38,
            offset_horizontal=38,
            offset_menu=38,
            offset_vertical=5,
            skip_header=True,
            total_lines=4,
            total_width=4,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_few_entries_on_cnarrow_lnarrow_screen_without_overscan___then_returns_compact_non_overflow_layout(self):
        actual = sut(columns=40, lines=15, menu_entries=FEW_MENU_ENTRIES, actions=ONE_ACTION)

        expected = drawer_paint_layout(
            action_y=13,
            has_gap=True,
            max_length_option=2,
            menu_entries=FEW_MENU_ENTRIES,
            offset_actions=18,
            offset_header=20,
            offset_horizontal=18,
            offset_menu=18,
            offset_text_line=20,
            offset_vertical=5,
            skip_header=True,
            total_lines=4,
            total_width=4,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_few_entries_on_cnarrow_lnarrow_screen_with_overscan___then_returns_compact_non_overflow_layout(self):
        actual = sut(columns=40, lines=15, overscan_cols=2, overscan_lines=1, menu_entries=FEW_MENU_ENTRIES, actions=ONE_ACTION)

        expected = drawer_paint_layout(
            action_y=12,
            has_gap=True,
            max_length_option=2,
            menu_entries=FEW_MENU_ENTRIES,
            offset_actions=18,
            offset_header=20,
            offset_horizontal=18,
            offset_menu=18,
            offset_text_line=20,
            offset_vertical=5,
            skip_header=True,
            total_lines=4,
            total_width=4,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_many_entries_on_wide_tall_screen_without_overscan___then_returns_standard_overflow_layout(self):
        actual = sut(columns=80, lines=40, menu_entries=MANY_MENU_ENTRIES, actions=ONE_ACTION)

        expected = drawer_paint_layout(
            has_gap=False,
            max_length_option=3,
            menu_entries=MANY_MENU_ENTRIES,
            offset_actions=38,
            offset_horizontal=37,
            offset_menu=37,
            offset_vertical=0,
            total_lines=41,
            total_width=5,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_many_entries_on_wide_tall_screen_with_overscan___then_returns_standard_overflow_layout(self):
        actual = sut(columns=80, lines=40, overscan_cols=2, overscan_lines=1, menu_entries=MANY_MENU_ENTRIES, actions=ONE_ACTION)

        expected = drawer_paint_layout(
            has_gap=False,
            max_length_option=3,
            menu_entries=MANY_MENU_ENTRIES,
            offset_actions=38,
            offset_horizontal=37,
            offset_menu=37,
            offset_vertical=0,
            total_lines=41,
            total_width=5,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_many_entries_on_cnarrow_tall_screen_without_overscan___then_returns_standard_overflow_layout(self):
        actual = sut(columns=40, lines=40, menu_entries=MANY_MENU_ENTRIES, actions=ONE_ACTION)

        expected = drawer_paint_layout(
            has_gap=False,
            max_length_option=3,
            menu_entries=MANY_MENU_ENTRIES,
            offset_actions=18,
            offset_header=20,
            offset_horizontal=17,
            offset_menu=17,
            offset_text_line=20,
            offset_vertical=0,
            skip_header=False,
            total_lines=41,
            total_width=5,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_many_entries_on_cnarrow_tall_screen_with_overscan___then_returns_standard_overflow_layout(self):
        actual = sut(columns=40, lines=40, overscan_cols=2, overscan_lines=1, menu_entries=MANY_MENU_ENTRIES, actions=ONE_ACTION)

        expected = drawer_paint_layout(
            has_gap=False,
            max_length_option=3,
            menu_entries=MANY_MENU_ENTRIES,
            offset_actions=18,
            offset_header=20,
            offset_horizontal=17,
            offset_menu=17,
            offset_text_line=20,
            offset_vertical=0,
            skip_header=False,
            total_lines=41,
            total_width=5,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_many_entries_on_wide_lnarrow_screen_without_overscan___then_returns_compact_overflow_layout(self):
        actual = sut(columns=80, lines=15, menu_entries=MANY_MENU_ENTRIES, actions=ONE_ACTION)

        expected = drawer_paint_layout(
            action_y=13,
            has_gap=False,
            layout_reset=False,
            max_length_option=3,
            menu_entries=OVERFLOW_SHORT_NO_OVERSCAN_MENU_ENTRIES,
            menu_scroll_offset=27,
            offset_actions=38,
            offset_horizontal=37,
            offset_menu=37,
            offset_vertical=0,
            skip_header=True,
            total_lines=14,
            total_width=5,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_many_entries_on_wide_lnarrow_screen_with_overscan___then_returns_compact_overflow_layout(self):
        actual = sut(columns=80, lines=15, overscan_cols=2, overscan_lines=1, menu_entries=MANY_MENU_ENTRIES, actions=ONE_ACTION)

        expected = drawer_paint_layout(
            action_y=12,
            has_gap=False,
            layout_reset=False,
            max_length_option=3,
            menu_entries=OVERFLOW_SHORT_WITH_OVERSCAN_MENU_ENTRIES,
            menu_scroll_offset=29,
            offset_actions=38,
            offset_horizontal=37,
            offset_menu=37,
            offset_vertical=1,
            skip_header=True,
            total_lines=12,
            total_width=5,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_many_entries_on_cnarrow_lnarrow_screen_without_overscan___then_returns_compact_overflow_layout(self):
        actual = sut(columns=40, lines=15, menu_entries=MANY_MENU_ENTRIES, actions=ONE_ACTION)

        expected = drawer_paint_layout(
            action_y=13,
            has_gap=False,
            layout_reset=False,
            max_length_option=3,
            menu_entries=OVERFLOW_SHORT_NO_OVERSCAN_MENU_ENTRIES,
            menu_scroll_offset=27,
            offset_actions=18,
            offset_header=20,
            offset_horizontal=17,
            offset_menu=17,
            offset_text_line=20,
            offset_vertical=0,
            skip_header=True,
            total_lines=14,
            total_width=5,
        )

        self.assertEqual(expected, actual)

    def test_calc_drawer_paint___when_many_entries_on_cnarrow_lnarrow_screen_with_overscan___then_returns_compact_overflow_layout(self):
        actual = sut(columns=40, lines=15, overscan_cols=2, overscan_lines=1, menu_entries=MANY_MENU_ENTRIES, actions=ONE_ACTION)

        expected = drawer_paint_layout(
            action_y=12,
            has_gap=False,
            layout_reset=False,
            max_length_option=3,
            menu_entries=OVERFLOW_SHORT_WITH_OVERSCAN_MENU_ENTRIES,
            menu_scroll_offset=29,
            offset_actions=18,
            offset_header=20,
            offset_horizontal=17,
            offset_menu=17,
            offset_text_line=20,
            offset_vertical=1,
            skip_header=True,
            total_lines=12,
            total_width=5,
        )

        self.assertEqual(expected, actual)


class _ScreenDims:
    def __init__(self, term_size: TerminalSize, overscan_dim: OverscanDim):
        self.term_size = term_size
        self.overscan_dim = overscan_dim


def sut(columns: int = 80, lines: int = 40, overscan_cols: int = 0,
        overscan_lines: int = 0, text_lines=None, text_scroll_offset: int = 0, header: str = '',
        menu_entries=None, menu_scroll_offset: int = 0, actions=None) -> DrawerPaintLayout:
    lnarrow, cnarrow = are_dims_narrow(lines, columns)
    return calc_drawer_paint(
        _ScreenDims(
            TerminalSize(columns=columns, lines=lines, lnarrow=lnarrow, cnarrow=cnarrow),
            OverscanDim(cols=overscan_cols, lines=overscan_lines),
        ),
        list(text_lines or []),
        text_scroll_offset,
        header,
        list(menu_entries or []),
        menu_scroll_offset,
        list(actions or []),
    )


def drawer_paint_layout(action_gap: int = 4, action_y=None, has_gap: bool = False, layout_reset: bool = False,
                        max_length_header: int = 0, max_length_option: int = 0, menu_entries=None,
                        menu_scroll_offset: int = 0, offset_actions: int = 40, offset_header: int = 40,
                        offset_horizontal=None, offset_menu: int = 39, offset_text_line: int = 40,
                        offset_vertical: int = 19, skip_header: bool = False, text_has_up_scroll: bool = False,
                        total_lines: int = 1, total_width: int = 2, visible_text_lines=None) -> DrawerPaintLayout:
    actual_offset_horizontal = min(offset_menu, offset_text_line, offset_actions, offset_header)
    if offset_horizontal is not None and offset_horizontal != actual_offset_horizontal:
        raise ValueError(f'Expected offset_horizontal {offset_horizontal} does not match derived value {actual_offset_horizontal}')

    return DrawerPaintLayout(
        action_gap=action_gap,
        action_y=action_y,
        has_gap=has_gap,
        layout_reset=layout_reset,
        max_length_header=max_length_header,
        max_length_option=max_length_option,
        menu_entries=list(menu_entries or []),
        menu_scroll_offset=menu_scroll_offset,
        offset_actions=offset_actions,
        offset_header=offset_header,
        offset_menu=offset_menu,
        offset_text_line=offset_text_line,
        offset_vertical=offset_vertical,
        skip_header=skip_header,
        text_has_up_scroll=text_has_up_scroll,
        total_lines=total_lines,
        total_width=total_width,
        visible_text_lines=list(visible_text_lines or []),
    )


def _lines(total: int):
    return [f'line {i}' for i in range(total)]


def _menu_entries(total: int, selected_idx: int):
    return [(f'A{i}', '', i == selected_idx) for i in range(total)]


ONE_ACTION = [('<OK>', False)]
MULTIPLE_ACTIONS = [('<OK>', False), ('<Cancel>', False)]
FEW_MENU_ENTRIES = _menu_entries(2, 1)
MANY_MENU_ENTRIES = _menu_entries(40, 36)
NO_BOX_TOP_MENU_ENTRIES = _menu_entries(12, 11)
OVERFLOW_TALL_NO_OVERSCAN_MENU_ENTRIES = [('--- ↑ ↑ ↑ ---', '', False)] + MANY_MENU_ENTRIES[2:38] + [('--- ↓ ↓ ↓ ---', '', False)]
OVERFLOW_TALL_WITH_OVERSCAN_MENU_ENTRIES = [('--- ↑ ↑ ↑ ---', '', False)] + MANY_MENU_ENTRIES[4:38] + [('--- ↓ ↓ ↓ ---', '', False)]
OVERFLOW_SHORT_NO_OVERSCAN_MENU_ENTRIES = [('--- ↑ ↑ ↑ ---', '', False)] + MANY_MENU_ENTRIES[27:38] + [('--- ↓ ↓ ↓ ---', '', False)]
OVERFLOW_SHORT_WITH_OVERSCAN_MENU_ENTRIES = [('--- ↑ ↑ ↑ ---', '', False)] + MANY_MENU_ENTRIES[29:38] + [('--- ↓ ↓ ↓ ---', '', False)]
OVERFLOW_SHORT_TOP_SELECTED_MENU_ENTRIES = _menu_entries(14, 0)[0:12] + [('--- ↓ ↓ ↓ ---', '', False)]
OVERFLOW_SHORT_BOTTOM_SELECTED_MENU_ENTRIES = [('--- ↑ ↑ ↑ ---', '', False)] + _menu_entries(14, 13)[2:14]


if __name__ == '__main__':
    unittest.main()
