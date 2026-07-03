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

from update_all.config import Config
from update_all.databases import ALL_DB_IDS
from update_all.ini_repository import IniRepository
from update_all.local_store import LocalStore
from update_all.other import GenericProvider


class JtcoresService:
    def __init__(
            self,
            config_provider: GenericProvider[Config],
            store_provider: GenericProvider[LocalStore],
            ini_repository: IniRepository,
    ):
        self._config_provider = config_provider
        self._store_provider = store_provider
        self._ini_repository = ini_repository

    def enable_private_beta_cores_from_retroaccount_if_allowed(self) -> None:
        config = self._config_provider.get()
        store = self._store_provider.get()
        if not store.get_allow_retroaccount_jt_beta_auto_enable():
            return

        if config.download_beta_cores or ALL_DB_IDS['JTCORES'] not in config.databases:
            return

        config.download_beta_cores = True
        self._ini_repository.write_downloader_ini(config)
