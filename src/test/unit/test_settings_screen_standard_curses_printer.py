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
from contextlib import contextmanager

import update_all.settings_screen_standard_curses_printer as printer_module
from update_all.other import OverscanDim, TerminalSize
from update_all.settings_screen_standard_curses_printer import Drawer, DrawerPaintLayout, paint_overscan_preview
from update_all.ui_model_utilities import Key


class TestSettingsScreenStandardCursesPrinter(unittest.TestCase):
    def test_action_viewport___at_40_columns___keeps_first_actions_and_marks_more_on_the_right(self):
        viewport = printer_module._calculate_action_viewport(
            _ScreenDims(columns=40, lines=15, overscan_cols=2),
            _actions_with_selected(0),
        )

        self.assertEqual(
            ['<Select>', '<Info>', '<Back>'],
            [action for action, _selected in viewport.actions],
        )
        self.assertFalse(viewport.has_hidden_left)
        self.assertTrue(viewport.has_hidden_right)
        self.assertTrue(viewport.is_scrolling)

    def test_action_viewport___when_last_action_is_selected___scrolls_whole_actions_to_reveal_it(self):
        viewport = printer_module._calculate_action_viewport(
            _ScreenDims(columns=40, lines=15, overscan_cols=2),
            _actions_with_selected(3),
        )

        self.assertEqual(
            ['<Info>', '<Back>', '<Uninstall>'],
            [action for action, _selected in viewport.actions],
        )
        self.assertTrue(viewport.has_hidden_left)
        self.assertFalse(viewport.has_hidden_right)
        self.assertTrue(viewport.actions[-1][1])

    def test_action_viewport___inactive_conditional_action_does_not_create_overflow_or_indicator(self):
        actions = _actions_with_selected(0)
        actions[-1] = (' ' * len('<Uninstall>'), False)

        viewport = printer_module._calculate_action_viewport(
            _ScreenDims(columns=40, lines=15, overscan_cols=2),
            actions,
        )

        self.assertEqual(
            ['<Select>', '<Info>', '<Back>'],
            [action for action, _selected in viewport.actions],
        )
        self.assertFalse(viewport.is_scrolling)
        self.assertFalse(viewport.has_hidden_left)
        self.assertFalse(viewport.has_hidden_right)

    def test_paint___when_actions_overflow___draws_right_indicator_at_overscan_border(self):
        runtime = _RuntimeStub()
        drawer = Drawer(
            runtime,
            _LayoutStub(),
            _InterpolatorStub(),
            _ScreenDims(columns=40, lines=15, overscan_cols=2),
        )
        drawer.start({'header': ''})
        drawer.add_menu_entry('Entry', '', True)
        for action, selected in _actions_with_selected(0):
            drawer.add_action(action[1:-1], selected)

        with _replace(printer_module.curses, 'color_pair', _FunctionStub(0)):
            drawer.paint()

        calls = [call.args for call in runtime.window.addstr.call_args_list]
        self.assertIn((13, 37, '>', printer_module.curses.A_BOLD), calls)
        self.assertNotIn('<Uninstall>', [call[2] for call in calls])

    def test_paint___after_scrolling_to_last_action___draws_left_indicator_and_uninstall(self):
        runtime = _RuntimeStub()
        drawer = Drawer(
            runtime,
            _LayoutStub(),
            _InterpolatorStub(),
            _ScreenDims(columns=40, lines=15, overscan_cols=2),
        )
        drawer.start({'header': ''})
        drawer.add_menu_entry('Entry', '', True)
        for action, selected in _actions_with_selected(3):
            drawer.add_action(action[1:-1], selected)

        with _replace(printer_module.curses, 'color_pair', _FunctionStub(0)):
            drawer.paint()

        calls = [call.args for call in runtime.window.addstr.call_args_list]
        self.assertIn((13, 2, '<', printer_module.curses.A_BOLD), calls)
        self.assertIn('Uninstall', [call[2] for call in calls])

    def test_paint___when_compact_menu_overflows___clears_each_visible_row_before_writing(self):
        runtime = _RuntimeStub()
        layout = _LayoutStub()
        drawer = Drawer(runtime, layout, _InterpolatorStub(), _ScreenDims(columns=80, lines=15))

        drawer.start({'header': ''})
        for i in range(14):
            drawer.add_menu_entry(f'A{i}', '', i == 12)
        drawer.add_action('OK')

        with _replace(printer_module.curses, 'color_pair', _FunctionStub(0)):
            result = drawer.paint()

        self.assertEqual(Key.NONE, result)
        self.assertEqual(14, runtime.window.hline.call_count)
        for y, call in enumerate(runtime.window.hline.call_args_list):
            self.assertEqual((y, 37, ord(' '), 5), call.args)

    def test_clear_content_area___when_header_separator_is_static___keeps_separator_row_untouched(self):
        runtime = _RuntimeStub()
        drawer = Drawer(runtime, _LayoutStub(), _InterpolatorStub(), _ScreenDims(columns=80, lines=40))

        with _replace(printer_module.curses, 'color_pair', _FunctionStub(0)):
            drawer._clear_content_area(DrawerPaintLayout(
            action_gap=4,
            action_y=None,
            has_gap=False,
            layout_reset=False,
            max_length_header=6,
            max_length_option=0,
            menu_entries=[],
            menu_scroll_offset=0,
            offset_actions=10,
            offset_header=10,
            offset_menu=10,
            offset_text_line=10,
            offset_vertical=10,
            skip_header=False,
            text_has_up_scroll=False,
            total_lines=4,
            total_width=6,
            visible_text_lines=[],
            ))

        self.assertEqual([(10, 10, ord(' '), 6), (12, 10, ord(' '), 6), (13, 10, ord(' '), 6)],
                         [call.args for call in runtime.window.hline.call_args_list])

    def test_paint___when_overscan_preview_requested___paints_preview(self):
        runtime = _RuntimeStub()
        layout = _LayoutStub()
        screen_dims = _ScreenDims(columns=80, lines=40, overscan_cols=2, overscan_lines=1)
        drawer = Drawer(runtime, layout, _InterpolatorStub(), screen_dims)

        drawer.start({'header': ''})
        drawer.add_action('OK')
        drawer.show_overscan_preview()

        paint_overscan_preview_spy = _MethodSpy()
        with _replace(printer_module.curses, 'color_pair', _FunctionStub(0)), \
                _replace(printer_module, 'paint_overscan_preview', paint_overscan_preview_spy):
            drawer.paint()

        paint_overscan_preview_spy.assert_called_once_with(runtime.window, screen_dims, 0)

    def test_paint_overscan_preview___draws_screen_edges_outside_overscan(self):
        window = _WindowSpy()

        paint_overscan_preview(window, _ScreenDims(columns=10, lines=6, overscan_cols=2, overscan_lines=1), 7)

        self.assertIn((0, 0, '█' * 10, 7), [call.args for call in window.addstr.call_args_list])
        self.assertIn((5, 0, '█' * 9, 7), [call.args for call in window.addstr.call_args_list])
        self.assertIn((1, 0, '██', 7), [call.args for call in window.addstr.call_args_list])
        self.assertIn((1, 8, '██', 7), [call.args for call in window.addstr.call_args_list])


@contextmanager
def _replace(target, attribute, replacement):
    original = getattr(target, attribute)
    setattr(target, attribute, replacement)
    try:
        yield replacement
    finally:
        setattr(target, attribute, original)


class _FunctionStub:
    def __init__(self, return_value):
        self._return_value = return_value

    def __call__(self, *_args):
        return self._return_value


class _RuntimeStub:
    def __init__(self):
        self.window = _WindowSpy()

    def read_key(self):
        return Key.NONE


class _LayoutStub:
    def set_sub_theme(self, _alert_level):
        pass

    def reset(self):
        pass

    def paint_layout(self, *_args):
        pass


class _Call:
    def __init__(self, args):
        self.args = args


class _MethodSpy:
    def __init__(self):
        self.call_args_list = []

    @property
    def call_count(self):
        return len(self.call_args_list)

    def __call__(self, *args):
        self.call_args_list.append(_Call(args))

    def assert_called_once_with(self, *args):
        calls = [call.args for call in self.call_args_list]
        if calls != [args]:
            raise AssertionError(f'Expected one call with {args}, got {calls}')


class _WindowSpy:
    def __init__(self):
        self.hline = _MethodSpy()
        self.addstr = _MethodSpy()
        self.timeout = _MethodSpy()


class _InterpolatorStub:
    def interpolate(self, text: str) -> str:
        return text


class _ScreenDims:
    def __init__(self, columns: int, lines: int, overscan_cols: int = 0, overscan_lines: int = 0):
        self.term_size = TerminalSize(columns=columns, lines=lines, lnarrow=lines <= 18, cnarrow=columns <= 48)
        self.overscan_dim = OverscanDim(cols=overscan_cols, lines=overscan_lines)


def _actions_with_selected(selected_index: int):
    return [
        (action, index == selected_index)
        for index, action in enumerate(('<Select>', '<Info>', '<Back>', '<Uninstall>'))
    ]
