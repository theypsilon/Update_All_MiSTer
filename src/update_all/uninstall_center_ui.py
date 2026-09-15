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
from update_all.ui_engine import EffectChain, ProcessKeyResult, UiRuntime, UiSection
from update_all.ui_engine_dialog_application import UiDialogDrawer, _NavigationState
from update_all.ui_model_utilities import Key
from update_all.uninstall_db_service import UninstallDbService, InstalledDb
from update_all.uninstall_db_ui import UninstallDbMenu


class UninstallCenterMenu(UiSection):
    def __init__(
            self,
            drawer: UiDialogDrawer,
            uninstall_db_service: UninstallDbService,
            ui_runtime: UiRuntime,
            logger: Logger,
            on_uninstalled: Callable[[str], None],
            data: Dict[str, Any],
    ):
        self._drawer = drawer
        self._service = uninstall_db_service
        self._ui_runtime = ui_runtime
        self._logger = logger
        self._on_uninstalled = on_uninstalled
        self._data = data
        self._dbs: list[InstalledDb] = []
        self._menu_state = _NavigationState(1, 2)

    def process_key(self) -> Optional[ProcessKeyResult]:
        dbs = self._service.list_installed_dbs()
        if dbs is None:
            self._show_message(['Could not list the installed databases.', 'Check the output for details.'])
            return self._back_effect()

        self._dbs = list(dbs)
        self._menu_state = _NavigationState(len(self._dbs) + 1, 2)
        while True:
            if not self._dbs:
                self._show_message(['There are no databases to uninstall.'])
                return self._back_effect()

            key = self._paint_menu()
            if key == Key.UP:
                self._menu_state.navigate_up()
            elif key == Key.DOWN:
                self._menu_state.navigate_down()
            elif key == Key.LEFT:
                self._menu_state.navigate_left()
            elif key == Key.RIGHT:
                self._menu_state.navigate_right()
            elif key == 27:
                return self._back_effect()
            elif key == Key.ENTER:
                if self._menu_state.lateral_position() == 1 or self._menu_state.position() == len(self._dbs):
                    return self._back_effect()

                db = self._dbs[self._menu_state.position()]
                if self._confirm_uninstall(db) and self._uninstall(db):
                    self._on_uninstalled(db.db_id)
                    self._dbs.remove(db)
                    self._menu_state = _NavigationState(len(self._dbs) + 1, 2)
                    self._menu_state.reset_position(min(self._menu_state.position(), len(self._dbs)))

    def reset(self) -> None:
        self._menu_state.reset_lateral_position()

    def clear(self) -> None:
        self._drawer.clear()

    def _paint_menu(self) -> int:
        self._drawer.start({'header': self._data.get('header', 'Uninstall Center')})
        for line in self._data.get('text', []):
            self._drawer.add_text_line(line)
        for index, db in enumerate(self._dbs):
            self._drawer.add_menu_entry(f'{index + 1} {db.title}', db.description, index == self._menu_state.position())
        self._drawer.add_menu_entry('Back', '', self._menu_state.position() == len(self._dbs))
        self._drawer.add_action('Uninstall', self._menu_state.lateral_position() == 0)
        self._drawer.add_action('Back', self._menu_state.lateral_position() == 1)
        return self._drawer.paint()

    def _confirm_uninstall(self, db: InstalledDb) -> bool:
        state = _NavigationState(0, 2)
        state.reset_lateral_position(1)
        while True:
            self._drawer.start({'header': f'Uninstall {db.title}?'})
            for line in (
                    'This will uninstall the database:',
                    f'[{db.db_id}]',
                    ' ',
                    'All its contents will be deleted from your system.',
                    'Do you really want to uninstall it?',
            ):
                self._drawer.add_text_line(line)
            self._drawer.add_action('Yes', state.lateral_position() == 0)
            self._drawer.add_action('No', state.lateral_position() == 1)

            key = self._drawer.paint()
            if key == Key.LEFT:
                state.navigate_left()
            elif key == Key.RIGHT:
                state.navigate_right()
            elif key == Key.ENTER:
                return state.lateral_position() == 0
            elif key == 27:
                return False

    def _uninstall(self, db: InstalledDb) -> bool:
        success_effects: list = []
        result = UninstallDbMenu(
            self._drawer,
            self._service,
            self._ui_runtime,
            self._logger,
            lambda _db_ids: None,
            {'db_ids': [db.db_id], 'title': db.title, 'on_success': success_effects, 'on_failure': []},
        ).process_key()
        return isinstance(result, EffectChain) and result.chain is success_effects

    def _show_message(self, lines: list[str]) -> None:
        while True:
            self._drawer.start({'header': self._data.get('header', 'Uninstall Center')})
            for line in lines:
                self._drawer.add_text_line(line)
            self._drawer.add_action('Ok', True)
            key = self._drawer.paint()
            if key == Key.ENTER or key == 27:
                return

    def _back_effect(self) -> EffectChain:
        return EffectChain(self._data.get('effects', [{'type': 'navigate', 'target': 'back'}]))
