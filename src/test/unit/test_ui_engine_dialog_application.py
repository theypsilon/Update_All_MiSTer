# Copyright (c) 2022-2026 José Manuel Barroso Galindo <theypsilon@gmail.com>

import unittest

from update_all.ui_engine import EffectChain, Interpolator
from update_all.ui_engine_dialog_application import DialogSectionFactory, UiDialogDrawer, UiDialogDrawerFactory
from update_all.ui_model_utilities import Key


class TestUiEngineDialogApplication(unittest.TestCase):
    def test_menu___renders_auto_numbered_entries(self):
        drawer = _Drawer([Key.NONE])
        section = _menu_section(drawer, [
            _entry('# Alpha', 'alpha'),
            _entry('# Beta', 'beta'),
            {},
            _entry('# Gamma', 'gamma'),
        ])

        section.process_key()

        self.assertEqual([
            ('1 Alpha', '', True),
            ('2 Beta', '', False),
            ('', '', False),
            ('3 Gamma', '', False),
        ], drawer.menu_entries)

    def test_menu___auto_numbering_ignores_entries_without_marker_and_separators(self):
        drawer = _Drawer([Key.NONE])
        section = _menu_section(drawer, [
            _entry(' Select None', 'select_none'),
            {},
            _entry('# 3DO', '3do'),
            _entry('# Arcadia 2001', 'arcadia2001'),
        ])

        section.process_key()

        self.assertEqual([
            (' Select None', '', True),
            ('', '', False),
            ('1 3DO', '', False),
            ('2 Arcadia 2001', '', False),
        ], drawer.menu_entries)

    def test_menu___number_key_selects_auto_numbered_entry(self):
        drawer = _Drawer([ord('3'), Key.ENTER])
        section = _menu_section(drawer, [
            _entry('# Alpha', 'alpha'),
            _entry('# Beta', 'beta'),
            _entry('# Gamma', 'gamma'),
        ])

        section.process_key()
        result = section.process_key()

        self.assertIsInstance(result, EffectChain)
        self.assertEqual([{'type': 'navigate', 'target': 'gamma'}], result.chain)

    def test_menu___hotkey_collision_selects_first_match_before_later_matches(self):
        drawer = _Drawer([ord('1'), Key.ENTER])
        section = _menu_section(drawer, [_entry(f'# Item {index}', f'item_{index}') for index in range(1, 12)])

        section.process_key()
        result = section.process_key()

        self.assertIsInstance(result, EffectChain)
        self.assertEqual([{'type': 'navigate', 'target': 'item_1'}], result.chain)

    def test_menu___repeating_hotkey_collision_cycles_through_matches(self):
        drawer = _Drawer([ord('1'), ord('1'), ord('1'), Key.ENTER])
        section = _menu_section(drawer, [_entry(f'# Item {index}', f'item_{index}') for index in range(1, 12)])

        section.process_key()
        section.process_key()
        section.process_key()
        result = section.process_key()

        self.assertIsInstance(result, EffectChain)
        self.assertEqual([{'type': 'navigate', 'target': 'item_11'}], result.chain)

    def test_menu___when_another_entry_activates_the_action___hole_keeps_the_layout(self):
        drawer = _Drawer([Key.NONE])
        section = _two_entry_new_action_section(drawer, 'true')

        section.process_key()

        self.assertEqual([('Select', True, True), (3, False, False), ('Back', True, False)], drawer.rendered_actions)

    def test_menu___when_no_entry_activates_the_action___there_is_no_hole(self):
        drawer = _Drawer([Key.NONE])
        section = _two_entry_new_action_section(drawer, 'false')

        section.process_key()

        self.assertEqual([('Select', True, True), ('Back', True, False)], drawer.rendered_actions)

    def test_menu___hole_is_skipped_by_lateral_navigation(self):
        drawer = _Drawer([Key.RIGHT, Key.ENTER])
        section = _two_entry_new_action_section(drawer, 'true')

        section.process_key()
        result = section.process_key()

        self.assertIsInstance(result, EffectChain)
        self.assertEqual([{'type': 'navigate', 'target': 'back'}], result.chain)

    def test_menu___conditional_action_is_shown_when_its_variable_is_true(self):
        drawer = _Drawer([Key.NONE])
        section = _conditional_menu_section(drawer, 'true')

        section.process_key()

        self.assertIn(('New', True, False), drawer.rendered_actions)

    def test_menu___conditional_action_button_is_derived_from_the_entries_layout(self):
        drawer = _Drawer([Key.NONE])
        data = {
            'ui': 'menu',
            'header': 'Menu',
            'entries': [{
                'title': '# Alpha',
                'description': '',
                'actions': {
                    'ok': [{'type': 'navigate', 'target': 'alpha'}],
                    'uninstall': {'if': 'alpha_db_installed', 'chain': [{'type': 'rotate_variable', 'target': 'alpha_db'}]},
                },
            }],
            'actions': [
                {'title': 'Select', 'type': 'symbol', 'symbol': 'ok'},
                {'title': 'Back', 'type': 'fixed', 'fixed': [{'type': 'navigate', 'target': 'back'}]},
            ],
        }
        section = DialogSectionFactory(_DrawerFactory(drawer)).create_ui_section(
            'menu', data, _ValuesInterpolator({'alpha_db_installed': 'true'}))

        section.process_key()

        # The row does not declare the "uninstall" symbol; the engine appends it
        # because an entry carries the conditional action.
        self.assertEqual(
            [('Select', True, True), ('Back', True, False), ('Uninstall', True, False)],
            drawer.rendered_actions,
        )

    def test_menu___derived_uninstall_stays_after_back_and_runs_after_navigating_right(self):
        drawer = _Drawer([Key.RIGHT, Key.RIGHT, Key.RIGHT, Key.ENTER])
        data = {
            'ui': 'menu',
            'header': 'Menu',
            'entries': [{
                'title': '# Alpha',
                'description': '',
                'actions': {
                    'ok': [{'type': 'navigate', 'target': 'select'}],
                    'info': [{'type': 'navigate', 'target': 'info'}],
                    'uninstall': {
                        'if': 'alpha_db_installed',
                        'chain': [{'type': 'navigate', 'target': 'uninstall'}],
                    },
                },
            }],
            'actions': [
                {'title': 'Select', 'type': 'symbol', 'symbol': 'ok'},
                {'title': 'Info', 'type': 'symbol', 'symbol': 'info'},
                {'title': 'Back', 'type': 'fixed', 'fixed': [{'type': 'navigate', 'target': 'back'}]},
            ],
        }
        section = DialogSectionFactory(_DrawerFactory(drawer)).create_ui_section(
            'menu', data, _ValuesInterpolator({'alpha_db_installed': 'true'}))

        section.process_key()
        section.process_key()
        section.process_key()
        result = section.process_key()

        self.assertEqual(
            ['Select', 'Info', 'Back', 'Uninstall'],
            [action[0] for action in drawer.rendered_actions],
        )
        self.assertTrue(drawer.rendered_actions[-1][2])
        self.assertIsInstance(result, EffectChain)
        self.assertEqual([{'type': 'navigate', 'target': 'uninstall'}], result.chain)

    def test_menu___derived_snake_case_action_uses_title_case_label(self):
        drawer = _Drawer([Key.NONE])
        data = {
            'ui': 'menu',
            'header': 'Menu',
            'entries': [{
                'title': '# Select All',
                'description': '',
                'actions': {
                    'ok': [],
                    'uninstall_all': {
                        'if': 'manuals_installed',
                        'chain': [{'type': 'navigate', 'target': 'back'}],
                    },
                },
            }],
            'actions': [
                {'title': 'Select', 'type': 'symbol', 'symbol': 'ok'},
                {'title': 'Back', 'type': 'fixed', 'fixed': [{'type': 'navigate', 'target': 'back'}]},
            ],
        }
        section = DialogSectionFactory(_DrawerFactory(drawer)).create_ui_section(
            'menu', data, _ValuesInterpolator({'manuals_installed': 'true'}))

        section.process_key()

        self.assertEqual(
            [('Select', True, True), ('Back', True, False), ('Uninstall All', True, False)],
            drawer.rendered_actions,
        )

    def test_menu___derived_action_button_is_not_rendered_when_no_entry_activates_it(self):
        drawer = _Drawer([Key.NONE])
        data = {
            'ui': 'menu',
            'header': 'Menu',
            'entries': [{
                'title': '# Alpha',
                'description': '',
                'actions': {
                    'ok': [{'type': 'navigate', 'target': 'alpha'}],
                    'uninstall': {'if': 'alpha_db_installed', 'chain': [{'type': 'rotate_variable', 'target': 'alpha_db'}]},
                },
            }],
            'actions': [
                {'title': 'Select', 'type': 'symbol', 'symbol': 'ok'},
                {'title': 'Back', 'type': 'fixed', 'fixed': [{'type': 'navigate', 'target': 'back'}]},
            ],
        }
        section = DialogSectionFactory(_DrawerFactory(drawer)).create_ui_section(
            'menu', data, _ValuesInterpolator({'alpha_db_installed': 'false'}))

        section.process_key()

        self.assertEqual([('Select', True, True), ('Back', True, False)], drawer.rendered_actions)

    def test_menu___conditional_action_is_hidden_when_its_variable_is_false(self):
        drawer = _Drawer([Key.NONE])
        section = _conditional_menu_section(drawer, 'false')

        section.process_key()

        self.assertNotIn('New', [action[0] for action in drawer.rendered_actions])
        self.assertEqual(['Select', 'Back'], [action[0] for action in drawer.rendered_actions])

    def test_menu___conditional_action_runs_its_target_chain_when_selected(self):
        drawer = _Drawer([Key.RIGHT, Key.ENTER])
        section = _conditional_menu_section(drawer, 'true')

        section.process_key()
        result = section.process_key()

        self.assertIsInstance(result, EffectChain)
        self.assertEqual(
            [{'type': 'rotate_variable', 'target': 'example_db'}],
            result.chain,
        )

    def test_menu___malformed_conditional_action_raises_a_clear_error(self):
        drawer = _Drawer([Key.NONE])
        data = {
            'ui': 'menu',
            'header': 'Menu',
            'entries': [_entry('# Alpha', 'alpha')],
            'actions': [
                {'title': 'Select', 'type': 'symbol', 'symbol': 'ok'},
                {'title': 'New', 'type': 'symbol', 'symbol': 'new'},
            ],
        }
        data['entries'][0]['actions']['new'] = {'type': 'rotate_variable', 'target': 'example_db'}
        section = DialogSectionFactory(_DrawerFactory(drawer)).create_ui_section('menu', data, _IdentityInterpolator())

        with self.assertRaises(ValueError) as ctx:
            section.process_key()

        self.assertIn('Conditional action "new"', str(ctx.exception))

    def test_menu___hidden_action_is_skipped_by_lateral_navigation(self):
        drawer = _Drawer([Key.RIGHT, Key.ENTER])
        section = _conditional_menu_section(drawer, 'false')

        section.process_key()
        result = section.process_key()

        self.assertIsInstance(result, EffectChain)
        self.assertEqual([{'type': 'navigate', 'target': 'back'}], result.chain)

    def test_menu___when_selected_action_turns_into_an_inactive_hole___cursor_snaps_to_first_action(self):
        # Other entries keep the 'new' slot in the row, so it stays visible as a
        # hole for the current entry once its condition flips to false (mirrors
        # uninstalling a db while other installed dbs remain in the menu).
        values = {'alpha_installed': 'true', 'beta_installed': 'true'}
        drawer = _Drawer([Key.RIGHT, Key.NONE, Key.NONE])
        data = {
            'ui': 'menu',
            'header': 'Menu',
            'entries': [
                {'title': '# Alpha', 'description': '', 'actions': {
                    'ok': [{'type': 'navigate', 'target': 'alpha'}],
                    'new': {'if': 'alpha_installed', 'chain': [{'type': 'navigate', 'target': 'back'}]},
                }},
                {'title': '# Beta', 'description': '', 'actions': {
                    'ok': [{'type': 'navigate', 'target': 'beta'}],
                    'new': {'if': 'beta_installed', 'chain': [{'type': 'navigate', 'target': 'back'}]},
                }},
            ],
            'actions': [
                {'title': 'Select', 'type': 'symbol', 'symbol': 'ok'},
                {'title': 'New', 'type': 'symbol', 'symbol': 'new'},
            ],
        }
        section = DialogSectionFactory(_DrawerFactory(drawer)).create_ui_section(
            'menu', data, _ValuesInterpolator(values))

        section.process_key()  # renders with cursor on 'Select', then consumes RIGHT
        section.process_key()  # renders with cursor now on the (active) 'New' action
        self.assertEqual(('New', True, True), drawer.rendered_actions[1])

        values['alpha_installed'] = 'false'  # Alpha's 'new' action turns inactive
        section.process_key()  # re-render with the stale cursor on the now-inactive slot

        self.assertEqual(('Select', True, True), drawer.rendered_actions[0])
        self.assertEqual(False, drawer.rendered_actions[1][2])  # the hole is no longer selected


def _two_entry_new_action_section(drawer, new_enabled):
    data = {
        'ui': 'menu',
        'header': 'Menu',
        'entries': [
            {
                'title': '# Alpha',
                'description': '',
                'actions': {'ok': [{'type': 'navigate', 'target': 'alpha'}]},
            },
            {
                'title': '# Beta',
                'description': '',
                'actions': {
                    'ok': [{'type': 'navigate', 'target': 'beta'}],
                    'new': {'if': 'beta_new_enabled', 'chain': [{'type': 'rotate_variable', 'target': 'beta'}]},
                },
            },
        ],
        'actions': [
            {'title': 'Select', 'type': 'symbol', 'symbol': 'ok'},
            {'title': 'New', 'type': 'symbol', 'symbol': 'new'},
            {'title': 'Back', 'type': 'fixed', 'fixed': [{'type': 'navigate', 'target': 'back'}]},
        ],
    }
    return DialogSectionFactory(_DrawerFactory(drawer)).create_ui_section(
        'menu', data, _ValuesInterpolator({'beta_new_enabled': new_enabled}))


def _conditional_menu_section(drawer, installed):
    data = {
        'ui': 'menu',
        'header': 'Menu',
        'entries': [{
            'title': '# Example Database',
            'description': '',
            'actions': {
                'ok': [{'type': 'rotate_variable', 'target': 'example_db'}],
                'new': {'if': 'example_db_installed', 'chain': [{'type': 'rotate_variable', 'target': 'example_db'}]},
            },
        }],
        'actions': [
            {'title': 'Select', 'type': 'symbol', 'symbol': 'ok'},
            {'title': 'New', 'type': 'symbol', 'symbol': 'new'},
            {'title': 'Back', 'type': 'fixed', 'fixed': [{'type': 'navigate', 'target': 'back'}]},
        ],
    }
    return DialogSectionFactory(_DrawerFactory(drawer)).create_ui_section(
        'menu', data, _ValuesInterpolator({'example_db_installed': installed}))


def _menu_section(drawer, entries):
    data = {
        'ui': 'menu',
        'header': 'Menu',
        'entries': entries,
        'actions': [{'title': 'Select', 'type': 'symbol', 'symbol': 'ok'}],
    }
    return DialogSectionFactory(_DrawerFactory(drawer)).create_ui_section('menu', data, _IdentityInterpolator())


def _entry(title, target):
    return {
        'title': title,
        'description': '',
        'actions': {'ok': [{'type': 'navigate', 'target': target}]},
    }


class _IdentityInterpolator(Interpolator):
    def interpolate(self, text):
        return text

    def get_value(self, key):
        return ''


class _ValuesInterpolator(Interpolator):
    def __init__(self, values):
        self._values = values

    def interpolate(self, text):
        return text

    def get_value(self, key):
        return self._values.get(key, '')


class _DrawerFactory(UiDialogDrawerFactory):
    def __init__(self, drawer):
        self._drawer = drawer

    def create_ui_dialog_drawer(self, _interpolator):
        return self._drawer


class _Drawer(UiDialogDrawer):
    def __init__(self, keys):
        self._keys = list(keys)
        self.menu_entries = []
        self.rendered_actions = []

    def start(self, _data):
        self.menu_entries = []
        self.rendered_actions = []

    def add_text_line(self, _text):
        pass

    def add_menu_entry(self, option, info, is_selected=False):
        self.menu_entries.append((option, info, is_selected))

    def add_action(self, action, is_selected=False):
        self.rendered_actions.append((action, True, is_selected))

    def add_inactive_action(self, length, is_selected=False):
        self.rendered_actions.append((length, False, is_selected))

    def show_overscan_preview(self) -> None:
        pass

    def paint(self):
        return self._keys.pop(0) if self._keys else Key.NONE

    def clear(self) -> None:
        pass

    def set_key_timeout(self, _timeout_ms: int) -> None:
        pass
