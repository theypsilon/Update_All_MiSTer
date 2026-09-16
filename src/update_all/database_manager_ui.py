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

from update_all.database_manager_service import DatabaseManagerService, InstalledDb
from update_all.logger import Logger
from update_all.ui_engine import EffectChain, ProcessKeyResult, UiRuntime, UiSection
from update_all.ui_engine_dialog_application import UiDialogDrawer, _NavigationState
from update_all.ui_model_utilities import Key
from update_all.uninstall_db_ui import UninstallDbMenu

_UPDATE_ONLY = 'Update Only'
_UNINSTALL = 'Uninstall'
_BACK = 'Back'
# Longest unbreakable string the Settings Screen model shows today: the Names_MiSTer GitHub URL in the Names TXT menu.
_MAX_UNBREAKABLE_LINE_WIDTH = 49
# Longest entry description the Settings Screen model shows today, in the Names TXT menu.
_MAX_LIST_DESCRIPTION_WIDTH = 46
_MAX_LIST_ROW_WIDTH = 80
_LIST_COLUMN_GAP = 2  # What the standard printer leaves between the entry and its info
_INDENT = '  '
_ELLIPSIS = '...'


class DatabaseManagerMenu(UiSection):
    def __init__(
            self,
            drawer: UiDialogDrawer,
            database_manager_service: DatabaseManagerService,
            ui_runtime: UiRuntime,
            logger: Logger,
            on_uninstalled: Callable[[str], None],
            text_width: int,
            data: Dict[str, Any],
    ):
        self._drawer = drawer
        self._service = database_manager_service
        self._ui_runtime = ui_runtime
        self._logger = logger
        self._on_uninstalled = on_uninstalled
        self._line_width = min(_MAX_UNBREAKABLE_LINE_WIDTH, text_width) if text_width > 0 else _MAX_UNBREAKABLE_LINE_WIDTH
        self._data = data
        self._dbs: list[InstalledDb] = []
        self._menu_state = _NavigationState(1, 2)

    def process_key(self) -> Optional[ProcessKeyResult]:
        dbs = self._service.list_installed_dbs()
        if dbs is None:
            self._show_message(self._header(), ['Could not list the installed databases.', 'Check the output for details.'])
            return self._back_effect()

        self._dbs = list(dbs)
        self._menu_state = _NavigationState(len(self._dbs) + 1, 2)
        while True:
            if not self._dbs:
                self._show_message(self._header(), ['There are no databases to manage.'])
                return self._back_effect()

            key = self._paint_list()
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
                if self._database_screen(db):
                    self._on_uninstalled(db.db_id)
                    self._dbs.remove(db)
                    self._menu_state = _NavigationState(len(self._dbs) + 1, 2)
                    self._menu_state.reset_position(min(self._menu_state.position(), len(self._dbs)))

    def reset(self) -> None:
        self._menu_state.reset_lateral_position()

    def clear(self) -> None:
        self._drawer.clear()

    def _paint_list(self) -> int:
        self._drawer.start({'header': self._header()})
        for line in self._data.get('text', []):
            self._drawer.add_text_line(line)
        infos = [_shortened(db.description, _MAX_LIST_DESCRIPTION_WIDTH, at_word=True) for db in self._dbs]
        info_width = max(len(info) for info in infos)
        option_width = _MAX_LIST_ROW_WIDTH - (_LIST_COLUMN_GAP + info_width if info_width else 0)
        for index, (db, info) in enumerate(zip(self._dbs, infos)):
            option = _shortened(f'{index + 1} {db.title}', option_width, at_word=False)
            self._drawer.add_menu_entry(option, info, index == self._menu_state.position())
        self._drawer.add_menu_entry(_BACK, '', self._menu_state.position() == len(self._dbs))
        self._drawer.add_action('Select', self._menu_state.lateral_position() == 0)
        self._drawer.add_action(_BACK, self._menu_state.lateral_position() == 1)
        return self._drawer.paint()

    def _database_screen(self, db: InstalledDb) -> bool:
        """Returns True when the database got uninstalled."""
        actions = ([_UPDATE_ONLY] if db.configured else []) + [_UNINSTALL, _BACK]
        lines = _database_lines(db, self._line_width)
        state = _NavigationState(0, len(actions))
        state.reset_lateral_position(len(actions) - 1)
        text_scroll = 0
        while True:
            self._drawer.start({'header': self._header()})
            for line in lines:
                self._drawer.add_text_line(line)
            self._drawer.set_text_scroll(text_scroll)
            for index, action in enumerate(actions):
                self._drawer.add_action(action, index == state.lateral_position())

            key = self._drawer.paint()
            if key in (Key.UP, Key.DOWN):
                text_scroll = self._scrolled(text_scroll, key)
            elif key == Key.LEFT:
                state.navigate_left()
            elif key == Key.RIGHT:
                state.navigate_right()
            elif key == 27:
                return False
            elif key == Key.ENTER:
                action = actions[state.lateral_position()]
                if action == _BACK:
                    return False
                if action == _UNINSTALL:
                    if self._confirm_uninstall(db) and self._uninstall(db):
                        return True
                elif self._confirm_update(db):
                    self._update(db)

    def _confirm_update(self, db: InstalledDb) -> bool:
        return self._confirm(f'Update {db.title}?', [
            'This will run the MiSTer Downloader only for the database:',
            f'[{db.db_id}]',
            ' ',
            'No other database will be updated.',
            'Do you want to continue?',
        ])

    def _confirm_uninstall(self, db: InstalledDb) -> bool:
        return self._confirm(f'Uninstall {db.title}?', [
            'This will uninstall the database:',
            f'[{db.db_id}]',
            ' ',
            'All its files will be deleted from your system.',
            'Do you really want to uninstall it?',
        ])

    def _confirm(self, header: str, lines: list[str]) -> bool:
        state = _NavigationState(0, 2)
        state.reset_lateral_position(1)
        text_scroll = 0
        while True:
            self._drawer.start({'header': header})
            for line in lines:
                self._drawer.add_text_line(line)
            self._drawer.set_text_scroll(text_scroll)
            self._drawer.add_action('Yes', state.lateral_position() == 0)
            self._drawer.add_action('No', state.lateral_position() == 1)

            key = self._drawer.paint()
            if key in (Key.UP, Key.DOWN):
                text_scroll = self._scrolled(text_scroll, key)
            elif key == Key.LEFT:
                state.navigate_left()
            elif key == Key.RIGHT:
                state.navigate_right()
            elif key == Key.ENTER:
                return state.lateral_position() == 0
            elif key == 27:
                return False

    def _update(self, db: InstalledDb) -> None:
        self._ui_runtime.interrupt()
        try:
            self._logger.print()
            self._logger.print(f'Updating {db.title}...')
            self._logger.print()
            return_code = self._service.update(db.db_id)
        finally:
            self._ui_runtime.resume()

        if return_code == 0:
            self._show_message('Database Updated', [f'The database {db.title}', 'has been updated successfully.'])
        else:
            self._show_message('Update Failed', [f'The database {db.title} could not be updated', f'(error code {return_code}). Check the output for details.'])

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

    def _show_message(self, header: str, lines: list[str]) -> None:
        text_scroll = 0
        while True:
            self._drawer.start({'header': header})
            for line in lines:
                self._drawer.add_text_line(line)
            self._drawer.set_text_scroll(text_scroll)
            self._drawer.add_action('Ok', True)
            key = self._drawer.paint()
            if key in (Key.UP, Key.DOWN):
                text_scroll = self._scrolled(text_scroll, key)
            elif key == Key.ENTER or key == 27:
                return

    def _scrolled(self, text_scroll: int, key) -> int:
        if key == Key.UP:
            return max(0, text_scroll - 1)
        max_lines = self._drawer.max_text_lines()
        if max_lines <= 0:
            return text_scroll
        return min(text_scroll + 1, max(0, self._drawer.total_text_lines() - max_lines))

    def _header(self) -> str:
        return self._data.get('header', 'Database Manager')

    def _back_effect(self) -> EffectChain:
        return EffectChain(self._data.get('effects', [{'type': 'navigate', 'target': 'back'}]))


def _database_lines(db: InstalledDb, width: int) -> list[str]:
    chunk_width = max(1, width - len(_INDENT))
    lines = [db.title]
    if db.db_id != db.title:
        lines.append(f'db_id: {db.db_id}')
    if db.description:
        if len(db.description) <= width:
            lines.append(db.description)
        else:
            lines.extend(_INDENT + chunk for chunk in _wrap_words(db.description, chunk_width))
    if db.db_url:
        url_line = f'db_url: {db.db_url}'
        if len(url_line) <= width:
            lines.append(url_line)
        else:
            lines.append('db_url:')
            lines.extend(_INDENT + db.db_url[i:i + chunk_width] for i in range(0, len(db.db_url), chunk_width))
    return lines


def _shortened(text: str, width: int, at_word: bool) -> str:
    if len(text) <= width:
        return text
    cut = text[:width - len(_ELLIPSIS)]
    if at_word and cut.rfind(' ') > 0:
        cut = cut[:cut.rfind(' ')]
    return cut.rstrip() + _ELLIPSIS


def _wrap_words(text: str, width: int) -> list[str]:
    lines: list[str] = []
    current = ''
    for word in text.split():
        while len(word) > width:
            if current:
                lines.append(current)
                current = ''
            lines.append(word[:width])
            word = word[width:]
        candidate = word if not current else f'{current} {word}'
        if len(candidate) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
