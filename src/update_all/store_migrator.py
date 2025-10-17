# Copyright (c) 2022-2024 José Manuel Barroso Galindo <theypsilon@gmail.com>

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

from typing import Callable
from update_all.config import Config
from update_all.logger import Logger


Migration = Callable[[dict[str, str]], None]

class StoreMigrator:
    def __init__(self, migration_list: list[Migration], logger: Logger):
        self._migrations = migration_list
        self._logger = logger

    def migrate(self, local_store):
        self._logger.bench('Migration start.')

        current_version = local_store.get('migration_version', 0)
        if current_version >= len(self._migrations):
            self._logger.bench('Migration not necessary, early return.')
            return

        for i in range(current_version, len(self._migrations), 1):
            self._logger.debug('Running migration version %s.' % (i + 1))
            self._migrations[i](local_store)

        local_store['migration_version'] = self.latest_migration_version()

        self._logger.bench('Migration done.')

    def latest_migration_version(self) -> int:
        return len(self._migrations)


def make_new_local_store(store_migrator):
    default_config = Config()
    return {
        'migration_version': store_migrator.latest_migration_version(),
        'theme': 'Blue Installer',
        'countdown_time': default_config.countdown_time,
        'log_viewer': default_config.log_viewer,
        'autoreboot': default_config.autoreboot,
        'download_beta_cores': default_config.download_beta_cores,
        'names_region': default_config.names_region,
        'names_char_code': default_config.names_char_code,
        'names_sort_code': default_config.names_sort_code,
        'introduced_arcade_names_txt': False,
        'pocket_firmware_update': default_config.pocket_firmware_update,
        'pocket_backup': default_config.pocket_backup,
        'timeline_after_logs': default_config.timeline_after_logs,
    }


class WrongMigrationException(Exception):
    pass
