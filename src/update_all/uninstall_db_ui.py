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

from typing import Any, Callable, Dict, Optional

from update_all.logger import Logger
from update_all.ui_engine import EffectChain, ProcessKeyResult, UiSection, UiRuntime
from update_all.ui_engine_dialog_application import UiDialogDrawer
from update_all.ui_model_utilities import Key
from update_all.uninstall_db_service import UninstallDbService

_EXIT_UNINSTALL_EXTERNALS_UNVERIFIED = 22
_EXIT_UNINSTALL_DRIVE_DISCONNECTED = 23
_RECOVERABLE_EXIT_CODES = {
    _EXIT_UNINSTALL_EXTERNALS_UNVERIFIED,
    _EXIT_UNINSTALL_DRIVE_DISCONNECTED,
}

_RETRY = 'retry'
_LOCAL_ONLY = 'local_only'


class UninstallDbMenu(UiSection):
    def __init__(
            self,
            drawer: UiDialogDrawer,
            uninstall_db_service: UninstallDbService,
            ui_runtime: UiRuntime,
            logger: Logger,
            on_failed_bulk_uninstall: Callable[[tuple[str, ...]], None],
            data: Dict[str, Any],
    ):
        self._drawer = drawer
        self._service = uninstall_db_service
        self._ui_runtime = ui_runtime
        self._logger = logger
        self._on_failed_bulk_uninstall = on_failed_bulk_uninstall
        self._db_ids = list(data['db_ids'])
        self._title = data['title']
        self._on_success = data.get('on_success', [{'type': 'navigate', 'target': 'back'}])
        self._on_failure = data.get('on_failure', [{'type': 'navigate', 'target': 'back'}])

    def process_key(self) -> Optional[ProcessKeyResult]:
        force = False
        while True:
            return_code = self._run_uninstall(force)
            if return_code == 0:
                self._paint('Database Uninstalled', [
                    f'The database {self._title}',
                    'has been uninstalled successfully.',
                ], wait_for_confirmation=True)
                return EffectChain(self._on_success)

            if len(self._db_ids) > 1:
                self._on_failed_bulk_uninstall(tuple(self._db_ids))

            if return_code not in _RECOVERABLE_EXIT_CODES:
                self._paint('Uninstall Failed', [
                    f'The database {self._title} could not be uninstalled',
                    f'(error code {return_code}). Check the output for details.',
                ], wait_for_confirmation=True)
                return EffectChain(self._on_failure)

            recovery = self._paint_recovery_options(return_code)
            if recovery is None:
                return EffectChain(self._on_failure)
            force = recovery == _LOCAL_ONLY

    def _run_uninstall(self, force: bool) -> int:
        self._ui_runtime.interrupt()
        try:
            self._logger.print()
            self._logger.print(f'Uninstalling {self._title}...')
            self._logger.print()
            return self._service.uninstall(self._db_ids, force=force)
        finally:
            self._ui_runtime.resume()

    def reset(self) -> None:
        pass

    def clear(self) -> None:
        self._drawer.clear()

    def _paint(self, header: str, lines, wait_for_confirmation: bool = False) -> None:
        self._drawer.start({'header': header})
        for line in lines:
            self._drawer.add_text_line(line)

        if not wait_for_confirmation:
            self._drawer.paint()
            return

        self._drawer.add_action('Ok', True)
        while True:
            key = self._drawer.paint()
            if key == Key.ENTER or key == 27:
                return

    def _paint_recovery_options(self, return_code: int) -> Optional[str]:
        if return_code == _EXIT_UNINSTALL_EXTERNALS_UNVERIFIED:
            header = 'External Drive Not Connected'
            lines = [
                'A drive with database files is not connected.',
                'Local Only can finish now. Delete any files left on that',
                'drive manually later.',
                'Or reconnect the drive and Retry.',
            ]
        else:
            header = 'External Drive Disconnected'
            lines = [
                'An external drive suddenly disconnected during uninstall.',
                'Local Only can finish now. Delete any files left on that',
                'drive manually later.',
                'Or reconnect the drive and Retry.',
            ]

        actions = [
            ('Retry', _RETRY),
            ('Local Only', _LOCAL_ONLY),
        ]
        selected = len(actions) - 1
        text_scroll = 0
        while True:
            self._drawer.start({'header': header})
            for line in lines:
                self._drawer.add_text_line(line)
            self._drawer.set_text_scroll(text_scroll)
            for index, (title, _value) in enumerate(actions):
                self._drawer.add_action(title, index == selected)

            key = self._drawer.paint()
            if key == Key.UP:
                text_scroll = max(0, text_scroll - 1)
            elif key == Key.DOWN:
                max_lines = self._drawer.max_text_lines()
                total_lines = self._drawer.total_text_lines()
                if max_lines > 0:
                    text_scroll = min(text_scroll + 1, max(0, total_lines - max_lines))
            elif key == Key.LEFT:
                selected = max(0, selected - 1)
            elif key == Key.RIGHT:
                selected = min(len(actions) - 1, selected + 1)
            elif key == Key.ENTER:
                return actions[selected][1]
            elif key == 27:
                return None
