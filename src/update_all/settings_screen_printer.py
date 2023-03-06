# Copyright (c) 2022-2023 José Manuel Barroso Galindo <theypsilon@gmail.com>

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
import abc
from typing import Tuple

from update_all.ui_engine_dialog_application import UiDialogDrawerFactory


class SettingsScreenThemeManager(abc.ABC):
    def set_theme(self, new_theme: str) -> None:
        """"Sets the theme for all drawers created or to be created"""


class SettingsScreenPrinter(abc.ABC):
    def initialize_screen(self) -> Tuple[UiDialogDrawerFactory, SettingsScreenThemeManager]:
        """Creates instances of DialogDrawerFactory"""
