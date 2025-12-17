# Copyright (c) 2022-2025 José Manuel Barroso Galindo <theypsilon@gmail.com>

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

from update_all.config import Config
from update_all.databases import all_dbs_list
from update_all.ini_repository import candidate_databases


class TestDatabases(unittest.TestCase):

    def test_candidate_databases_are_as_many_as_different_db_ids_in_all_dbs(self) -> None:
        self.assertEqual(len(all_db_ids()), len(candidate_dbs()))

    def test_candidate_database_ids_are_identical_to_the_different_db_ids_in_all_dbs(self) -> None:
        self.assertSetEqual(all_db_ids(), {db.db_id for k, db in candidate_dbs()})


def candidate_dbs(): return candidate_databases(Config())
def all_db_ids(): return {v.db_id for v in all_dbs_list()}
