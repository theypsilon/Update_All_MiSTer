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
from update_all.databases import ALL_DB_IDS, COIN_OP_COLLECTION_RELEASES
from update_all.ini_repository import IniRepository
from update_all.other import GenericProvider


class CoinOpCollectionService:
    def __init__(
            self,
            config_provider: GenericProvider[Config],
            ini_repository: IniRepository,
    ):
        self._config_provider = config_provider
        self._ini_repository = ini_repository

    def follow_retroaccount_benefit(self, releases: str) -> None:
        config = self._config_provider.get()
        if not config.coin_op_collection_releases_auto:
            return

        if releases not in COIN_OP_COLLECTION_RELEASES or ALL_DB_IDS['COIN_OP_COLLECTION'] not in config.databases:
            return

        if config.coin_op_collection_releases == releases:
            return

        config.coin_op_collection_releases = releases
        self._ini_repository.write_downloader_ini(config)
