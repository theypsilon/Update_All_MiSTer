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
import unittest

from update_all.config import Config
from update_all.databases import all_dbs, all_mirrors, ids_sequence, ALL_DB_IDS, AllDBs, AllDBsAndiBr, Database, \
    MIRROR_ANDI_BR, MIRROR_MYSTICAL_REALM_ORG
from update_all.ini_repository import candidate_databases


class TestDatabases(unittest.TestCase):

    def test_candidate_databases_are_as_many_as_different_db_ids_in_all_dbs(self) -> None:
        self.assertEqual(len(ids_sequence()), len(candidate_dbs()))

    def test_candidate_database_ids_are_identical_to_the_different_db_ids_in_all_dbs(self) -> None:
        self.assertSetEqual(set(ids_sequence()), {db.db_id for k, db in candidate_dbs()})

    def test_names_locale_by_db_url___on_wrong_db_url___returns_names_char18_common_jp_locale(self):
        self.assertEqual(names_locale_by_db_url(all_dbs('').NAMES_CHAR18_COMMON_JP_TXT.db_url), names_locale_by_db_url('wrong'))

    def test_names_locale_by_db_url___on_names_char18_common_jp_db_url___returns_proper_region_value(self):
        self.assertEqual('JP', names_locale_by_db_url(all_dbs('').NAMES_CHAR18_COMMON_JP_TXT.db_url)[0])

    def test_all_mirrors___includes_mystical_realm_and_andi_br(self):
        self.assertEqual(
            (MIRROR_MYSTICAL_REALM_ORG, MIRROR_ANDI_BR),
            all_mirrors(),
        )

    def test_all_dbs___with_andi_br_mirror___prepends_proxy_to_every_database_url(self):
        original_dbs = AllDBs()
        mirrored_dbs = all_dbs(MIRROR_ANDI_BR)

        self.assertIsInstance(mirrored_dbs, AllDBsAndiBr)
        for name, original_db in original_dbs.__dict__.items():
            if not isinstance(original_db, Database):
                continue

            with self.subTest(database=name):
                mirrored_db = getattr(mirrored_dbs, name)
                self.assertEqual(original_db.db_id, mirrored_db.db_id)
                self.assertEqual(original_db.title, mirrored_db.title)
                self.assertEqual(
                    'https://mister.cc.cd/' + original_db.db_url,
                    mirrored_db.db_url,
                )

def candidate_dbs(): return candidate_databases(Config())
def names_locale_by_db_url(db_url: str) -> tuple[str, str, str]: return all_dbs('').names_locale_by_db_url(db_url)
