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
    MIRROR_ANDI_BR, MIRROR_MYSTICAL_REALM_ORG, chipster6502_artworkdbs, \
    chipster6502_artwork_style_from_db_url
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

    def test_nblood___uses_multidatabases_publication(self):
        db = all_dbs('').NBLOOD

        self.assertEqual('MultiDatabases/nblood', db.db_id)
        self.assertEqual(
            'https://raw.githubusercontent.com/theypsilon/MultiDatabases_MiSTer/db/nblood/db.json',
            db.db_url,
        )
        self.assertEqual('NBlood', db.title)

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

    def test_chipster6502_artworkdbs___contains_every_published_box2d_database_with_derived_url(self):
        groups_by_system = {
            '3do': 'misc',
            'atari5200': 'atari',
            'atari7800': 'atari',
            'amigacd32': 'misc',
            'arcade': 'arcade',
            'atari2600': 'atari',
            'atarilynx': 'atari',
            'cd-i': 'misc',
            'coleco': 'misc',
            'fds': 'nintendo-consoles',
            'gameboy': 'nintendo-handhelds',
            'gba': 'nintendo-handhelds',
            'gbc': 'nintendo-handhelds',
            'gamegear': 'sega',
            'genesis': 'sega',
            'intellivision': 'misc',
            'jaguar': 'atari',
            'megacd': 'sega',
            'n64': 'nintendo-consoles',
            'neogeo': 'snk',
            'nes': 'nintendo-consoles',
            'neogeo-cd': 'snk',
            'neogeopocket': 'snk',
            'neogeopocket-color': 'snk',
            'odyssey2': 'misc',
            'psx': 'sony',
            's32x': 'sega',
            'sg-1000': 'sega',
            'sms': 'sega',
            'snes': 'nintendo-consoles',
            'satellaview': 'nintendo-consoles',
            'saturn': 'sega',
            'supergrafx': 'nec',
            'tgfx16': 'nec',
            'tgfx16-cd': 'nec',
            'vectrex': 'misc',
            'virtualboy': 'nintendo-consoles',
            'wonderswan': 'misc',
            'wonderswancolor': 'misc',
        }
        artwork_dbs = {db.db_id: db for db in chipster6502_artworkdbs()}

        self.assertEqual(39, len(artwork_dbs))
        self.assertEqual(
            {f'chipster6502/artworkdb-{system}' for system in groups_by_system},
            set(artwork_dbs),
        )
        for system, group in groups_by_system.items():
            db = artwork_dbs[f'chipster6502/artworkdb-{system}']
            self.assertEqual(
                f'https://raw.githubusercontent.com/chipster6502/artworkdb-{group}/db/{system}_box2d.json.zip',
                db.db_url,
            )
            self.assertTrue(db.title.endswith(' Artwork'))

    def test_candidate_databases___uses_each_configured_artwork_style_identifier_in_the_url(self):
        config = Config(artwork_default_style='mixrbv2')
        config.set_artwork_db_style('chipster6502/artworkdb-nes', 'box3d')
        candidates = {db.db_id: db for _variable, db in candidate_databases(config)}

        self.assertEqual(
            'https://raw.githubusercontent.com/chipster6502/artworkdb-nintendo-consoles/db/nes_box3d.json.zip',
            candidates['chipster6502/artworkdb-nes'].db_url,
        )
        self.assertEqual(
            'https://raw.githubusercontent.com/chipster6502/artworkdb-nintendo-consoles/db/snes_mixrbv2.json.zip',
            candidates['chipster6502/artworkdb-snes'].db_url,
        )

    def test_candidate_databases___applies_artwork_style_after_andi_mirror_wrapping(self):
        config = Config(mirror=MIRROR_ANDI_BR)
        config.set_artwork_db_style('chipster6502/artworkdb-nes', 'box3d')
        candidates = {db.db_id: db for _variable, db in candidate_databases(config)}

        self.assertEqual(
            'https://mister.cc.cd/https://raw.githubusercontent.com/chipster6502/'
            'artworkdb-nintendo-consoles/db/nes_box3d.json.zip',
            candidates['chipster6502/artworkdb-nes'].db_url,
        )

    def test_chipster6502_artwork_style_from_db_url___recognizes_identifiers_and_defaults_to_box2d(self):
        base = 'https://example.test/nes_{}.json.zip'

        self.assertEqual('box2d', chipster6502_artwork_style_from_db_url(base.format('box2d')))
        self.assertEqual('box3d', chipster6502_artwork_style_from_db_url(base.format('box3d')))
        self.assertEqual('mixrbv2', chipster6502_artwork_style_from_db_url(base.format('mixrbv2')))
        self.assertEqual('box2d', chipster6502_artwork_style_from_db_url(base.format('unknown')))

def candidate_dbs(): return candidate_databases(Config())
def names_locale_by_db_url(db_url: str) -> tuple[str, str, str]: return all_dbs('').names_locale_by_db_url(db_url)
