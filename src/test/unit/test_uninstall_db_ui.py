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

from test.logger_tester import NoLogger
from update_all.ui_engine import EffectChain, UiRuntime
from update_all.ui_engine_dialog_application import UiDialogDrawer
from update_all.ui_model_utilities import Key
from update_all.uninstall_db_ui import UninstallDbMenu

FOLLOW_UP = [
    {'type': 'set_variable', 'target': 'MultiDatabases/duke3d', 'value': 'false'},
    {'type': 'set_variable', 'target': 'MultiDatabases/duke3d_installed', 'value': 'false'},
]


class TestUninstallDbMenu(unittest.TestCase):
    def test_process_key___on_success___shows_progress_then_success_and_runs_the_follow_up_effects(self):
        events = []
        section = UninstallDbMenu(
            _Drawer(events, [Key.NONE, Key.ENTER]),
            _ServiceStub(events, 0),
            _RuntimeStub(events),
            NoLogger(),
            lambda db_ids: events.append(('reconcile', db_ids)),
            {
                'db_ids': ['MultiDatabases/duke3d', 'MultiDatabases/mister-quake'],
                'title': 'MiSTer ports',
                'on_success': FOLLOW_UP,
            },
        )

        result = section.process_key()

        self.assertIsInstance(result, EffectChain)
        self.assertEqual(FOLLOW_UP, result.chain)
        self.assertEqual([
            ('interrupt', None),
            ('uninstall', ['MultiDatabases/duke3d', 'MultiDatabases/mister-quake'], False),
            ('resume', None),
            ('paint', 'Database Uninstalled'),
        ], _summary(events))

    def test_process_key___on_failure___shows_the_error_and_navigates_back(self):
        events = []
        section = UninstallDbMenu(
            _Drawer(events, [Key.NONE, Key.ENTER]),
            _ServiceStub(events, 1),
            _RuntimeStub(events),
            NoLogger(),
            lambda db_ids: events.append(('reconcile', db_ids)),
            {
                'db_ids': ['MultiDatabases/duke3d', 'MultiDatabases/mister-quake'],
                'title': 'MiSTer ports',
                'on_success': FOLLOW_UP,
            },
        )

        result = section.process_key()

        self.assertIsInstance(result, EffectChain)
        self.assertEqual([{'type': 'navigate', 'target': 'back'}], result.chain)
        self.assertEqual([
            ('interrupt', None),
            ('uninstall', ['MultiDatabases/duke3d', 'MultiDatabases/mister-quake'], False),
            ('resume', None),
            ('reconcile', ('MultiDatabases/duke3d', 'MultiDatabases/mister-quake')),
            ('paint', 'Uninstall Failed'),
        ], _summary(events))
        self.assertIn('error code 1', _text(events))

    def test_process_key___exit_22_then_retry___retries_without_force(self):
        events = []
        section = UninstallDbMenu(
            _Drawer(events, [Key.LEFT, Key.ENTER, Key.ENTER]),
            _ServiceStub(events, [22, 0]),
            _RuntimeStub(events),
            NoLogger(),
            lambda db_ids: events.append(('reconcile', db_ids)),
            {
                'db_ids': ['MultiDatabases/duke3d'],
                'title': 'Duke Nukem 3D',
                'on_success': FOLLOW_UP,
            },
        )

        result = section.process_key()

        self.assertEqual(FOLLOW_UP, result.chain)
        self.assertEqual([
            ('uninstall', ['MultiDatabases/duke3d'], False),
            ('uninstall', ['MultiDatabases/duke3d'], False),
        ], _uninstall_events(events))
        self.assertIn(('paint', 'External Drive Not Connected'), events)
        self.assertIn(('paint', 'Database Uninstalled'), events)

    def test_process_key___exit_22_then_local_only___retries_with_force(self):
        events = []
        section = UninstallDbMenu(
            _Drawer(events, [Key.ENTER, Key.ENTER]),
            _ServiceStub(events, [22, 0]),
            _RuntimeStub(events),
            NoLogger(),
            lambda db_ids: events.append(('reconcile', db_ids)),
            {
                'db_ids': ['MultiDatabases/duke3d'],
                'title': 'Duke Nukem 3D',
                'on_success': FOLLOW_UP,
            },
        )

        result = section.process_key()

        self.assertEqual(FOLLOW_UP, result.chain)
        self.assertEqual([
            ('uninstall', ['MultiDatabases/duke3d'], False),
            ('uninstall', ['MultiDatabases/duke3d'], True),
        ], _uninstall_events(events))
        self.assertIn(('action', 'Local Only', True), events)

    def test_process_key___exit_23_then_escape___explains_the_disconnect_and_does_not_retry(self):
        events = []
        section = UninstallDbMenu(
            _Drawer(events, [27]),
            _ServiceStub(events, 23),
            _RuntimeStub(events),
            NoLogger(),
            lambda db_ids: events.append(('reconcile', db_ids)),
            {
                'db_ids': ['MultiDatabases/duke3d'],
                'title': 'Duke Nukem 3D',
                'on_success': FOLLOW_UP,
            },
        )

        result = section.process_key()

        self.assertEqual([{'type': 'navigate', 'target': 'back'}], result.chain)
        self.assertEqual([
            ('uninstall', ['MultiDatabases/duke3d'], False),
        ], _uninstall_events(events))
        self.assertIn(('paint', 'External Drive Disconnected'), events)
        self.assertIn(
            'suddenly disconnected during uninstall',
            _text(events),
        )
        self.assertEqual(
            ['Retry', 'Local Only'],
            [event[1] for event in events if event[0] == 'action'],
        )
        self.assertFalse(any(event[0] == 'reconcile' for event in events))

    def test_process_key___exit_23_then_local_only___retries_with_force(self):
        events = []
        section = UninstallDbMenu(
            _Drawer(events, [Key.ENTER, Key.ENTER]),
            _ServiceStub(events, [23, 0]),
            _RuntimeStub(events),
            NoLogger(),
            lambda db_ids: events.append(('reconcile', db_ids)),
            {
                'db_ids': ['MultiDatabases/duke3d'],
                'title': 'Duke Nukem 3D',
                'on_success': FOLLOW_UP,
            },
        )

        result = section.process_key()

        self.assertEqual(FOLLOW_UP, result.chain)
        self.assertEqual([
            ('uninstall', ['MultiDatabases/duke3d'], False),
            ('uninstall', ['MultiDatabases/duke3d'], True),
        ], _uninstall_events(events))

    def test_process_key___failed_bulk_uninstall___requests_reconciliation_before_showing_failure(self):
        events = []
        db_ids = ('MultiDatabases/duke3d', 'MultiDatabases/mister-quake')
        section = UninstallDbMenu(
            _Drawer(events, [Key.ENTER]),
            _ServiceStub(events, 1),
            _RuntimeStub(events),
            NoLogger(),
            lambda db_ids: events.append(('reconcile', db_ids)),
            {
                'db_ids': list(db_ids),
                'title': 'MiSTer ports',
            },
        )

        result = section.process_key()

        self.assertEqual([{'type': 'navigate', 'target': 'back'}], result.chain)
        self.assertLess(events.index(('reconcile', db_ids)), events.index(('paint', 'Uninstall Failed')))

    def test_process_key___recoverable_failure_then_escape___keeps_partial_reconciliation(self):
        events = []
        db_ids = ('ajgowans/manualsdb-3do', 'ajgowans/manualsdb-megadrive')
        section = UninstallDbMenu(
            _Drawer(events, [27]),
            _ServiceStub(events, 22),
            _RuntimeStub(events),
            NoLogger(),
            lambda db_ids: events.append(('reconcile', db_ids)),
            {
                'db_ids': list(db_ids),
                'title': 'All Manuals Databases',
            },
        )

        result = section.process_key()

        self.assertEqual([{'type': 'navigate', 'target': 'back'}], result.chain)
        self.assertIn(('reconcile', db_ids), events)
        self.assertEqual(1, len(_uninstall_events(events)))


def _summary(events):
    return [event for event in events if event[0] not in ('text', 'action')]


def _uninstall_events(events):
    return [event for event in events if event[0] == 'uninstall']


def _text(events):
    return ' '.join(event[1] for event in events if event[0] == 'text')


class _ServiceStub:
    def __init__(self, events, return_codes):
        self._events = events
        self._return_codes = list(return_codes) if isinstance(return_codes, list) else [return_codes]

    def uninstall(self, db_ids, force=False):
        self._events.append(('uninstall', db_ids, force))
        return self._return_codes.pop(0)


class _RuntimeStub(UiRuntime):
    def __init__(self, events):
        self._events = events

    def interrupt(self) -> None:
        self._events.append(('interrupt', None))

    def resume(self) -> None:
        self._events.append(('resume', None))


class _Drawer(UiDialogDrawer):
    def __init__(self, events, keys):
        self._events = events
        self._keys = list(keys)

    def start(self, data):
        self._events.append(('paint', data['header']))

    def add_text_line(self, text):
        self._events.append(('text', text))

    def add_menu_entry(self, _option, _info, _is_selected=False):
        pass

    def add_action(self, action, is_selected=False):
        self._events.append(('action', action, is_selected))

    def add_inactive_action(self, _length, _is_selected=False):
        pass

    def show_overscan_preview(self) -> None:
        pass

    def paint(self):
        return self._keys.pop(0) if self._keys else Key.NONE

    def clear(self) -> None:
        pass

    def set_key_timeout(self, _timeout_ms: int) -> None:
        pass
