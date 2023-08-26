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
from typing import Dict, Union, List


class LocalStore:
    def __init__(self, props: Dict[str, Union[str, int, bool]]):
        self._props = props
        self._dirty = set()
        if '_dirty' in self._props:
            if self._props['_dirty']:
                self._dirty.add('constructed dirty')
            self._props.pop('_dirty')

    def set_theme(self, theme: str) -> None: self.generic_set('theme', theme)
    def get_theme(self) -> str: return self._props['theme']
    def set_wait_time_for_reading(self, wait_time_for_reading: int) -> None: self.generic_set('wait_time_for_reading', wait_time_for_reading)
    def get_wait_time_for_reading(self) -> int: return self._props['wait_time_for_reading']
    def set_countdown_time(self, countdown_time: int) -> None: self.generic_set('countdown_time', countdown_time)
    def get_countdown_time(self) -> int: return self._props['countdown_time']
    def set_autoreboot(self, autoreboot: bool) -> None: self.generic_set('autoreboot', autoreboot)
    def get_autoreboot(self) -> bool: return self._props['autoreboot']
    def set_download_beta_cores(self, download_beta_cores: bool) -> None: self.generic_set('download_beta_cores', download_beta_cores)
    def get_download_beta_cores(self) -> bool: return self._props['download_beta_cores']
    def set_names_region(self, names_region: str) -> None: self.generic_set('names_region', names_region)
    def get_names_region(self) -> str: return self._props['names_region']
    def set_names_char_code(self, names_char_code: str) -> None: self.generic_set('names_char_code', names_char_code)
    def get_names_char_code(self) -> str: return self._props['names_char_code']
    def set_names_sort_code(self, names_sort_code: str) -> None: self.generic_set('names_sort_code', names_sort_code)
    def get_names_sort_code(self) -> str: return self._props['names_sort_code']
    def set_introduced_arcade_names_txt(self, introduced_arcade_names_txt: bool) -> None: self.generic_set('introduced_arcade_names_txt', introduced_arcade_names_txt)
    def get_introduced_arcade_names_txt(self) -> bool: return self._props['introduced_arcade_names_txt']

    def unwrap_props(self):
        return self._props

    def needs_save(self) -> bool:
        return len(self._dirty) > 0

    def changed_fields(self) -> List[str]:
        return list(self._dirty)

    def mark_as_cleaned(self) -> None:
        self._dirty = set()

    def generic_set(self, field, value) -> None:
        if value == self._props[field]: return
        self._props[field] = value
        self._dirty.add(field)

    def has_field(self, field):
        return field in self._props
