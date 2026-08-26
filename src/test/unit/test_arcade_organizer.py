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
import os
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

import update_all.arcade_organizer.arcade_organizer as arcade_organizer_module
from test.fetcher_stub import FetcherStub
from test.logger_tester import NoLogger
from update_all.arcade_organizer.arcade_organizer import ArcadeOrganizerService, Infrastructure


class TestArcadeOrganizerInfrastructure(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix='ao_unit_')
        ini_path = os.path.join(self.test_dir, 'Scripts', 'update_arcade-organizer.ini')
        os.makedirs(os.path.dirname(ini_path), exist_ok=True)
        with open(ini_path, 'w') as f:
            f.write('[DEFAULT]\n')

        service = ArcadeOrganizerService(NoLogger(), FetcherStub())
        config = service.make_arcade_organizer_config(ini_path, self.test_dir, '')
        self.config = config
        self.infra = Infrastructure(config, NoLogger(), FetcherStub())

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    def test_read_mra_fields___closes_file_handle_after_parsing(self):
        fixture = Path('test/fixtures/arcade_organizer/mra/pacman.mra')
        seen = {}

        class _Elem:
            def __init__(self, tag, text):
                self.tag = tag
                self.text = text

        def fake_iterparse(file_obj, events):
            self.assertEqual(("start",), events)
            self.assertFalse(file_obj.closed)
            seen['file_obj'] = file_obj
            return iter([
                ("start", _Elem("setname", "pacman")),
                ("start", _Elem("rbf", "PacMan")),
            ])

        with _replace(arcade_organizer_module.ET, 'iterparse', fake_iterparse):
            fields = self.infra.read_mra_fields(fixture, ['setname', 'rbf'])

        self.assertEqual({'setname': 'pacman', 'rbf': 'PacMan'}, fields)
        self.assertTrue(seen['file_obj'].closed)

    def test_handle_orgdir_outside_mra_folder___with_missing_orgdir_parent___creates_cores_link(self):
        self.config['ORGDIR'] = os.path.join(self.test_dir, '_Arcade Organized')
        mra_cores = Path(self.config['MRADIR']) / 'cores'
        mra_cores.mkdir(parents=True)

        self.infra.handle_orgdir_outside_mra_folder()

        org_cores = Path(self.config['ORGDIR']) / 'cores'
        self.assertTrue(org_cores.is_symlink())
        self.assertEqual(str(mra_cores.absolute()), os.readlink(org_cores))
        self.assertEqual([], self.infra.errors())

    def test_handle_orgdir_outside_mra_folder___without_mra_cores___does_nothing(self):
        self.config['ORGDIR'] = os.path.join(self.test_dir, '_Arcade Organized')

        self.infra.handle_orgdir_outside_mra_folder()

        self.assertFalse(Path(self.config['ORGDIR']).exists())
        self.assertEqual([], self.infra.errors())


@contextmanager
def _replace(target, attribute, replacement):
    original = getattr(target, attribute)
    setattr(target, attribute, replacement)
    try:
        yield replacement
    finally:
        setattr(target, attribute, original)
