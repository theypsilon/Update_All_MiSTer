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

from test.fake_filesystem import FileSystemFactory
from test.logger_tester import NoLogger
from update_all.file_system import FileSystem
from update_all.logger import Logger
from update_all.zaparoo_service import ZaparooService


class ZaparooServiceTester(ZaparooService):
    def __init__(
            self,
            file_system: FileSystem = None,
            files=None,
            logger: Logger = None,
    ):
        self.file_system = file_system or FileSystemFactory.from_state(files=files or {}).create_for_system_scope()
        self.logger = logger or NoLogger()
        super().__init__(
            self.file_system,
            self.logger,
        )
