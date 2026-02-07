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

import json
import os
import shutil
import tempfile
import time
import unittest
import zipfile
from pathlib import Path

from update_all.arcade_organizer.arcade_organizer import ArcadeOrganizerService
from update_all.constants import FILE_arcade_database_mad_db_json_zip
from test.logger_tester import NoLogger


class TestArcadeOrganizerPCIntegration(unittest.TestCase):
    """Integration test simulating PC setup following PC_ARCADE_ORGANIZER.md.

    Configuration:
      - NO_SYMLINKS=true (copies instead of symlinks)
      - Local MAD_DB file (avoids network downloads)
      - Custom base_path under temp directory
      - ARCADE_ORGANIZER_WORK_PATH under temp directory
    """

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix='ao_pc_test_')
        self.base_path = self.test_dir

        self.mradir = os.path.join(self.base_path, '_Arcade')
        self.orgdir = os.path.join(self.base_path, '_Arcade', '_Organized')
        self.work_path = os.path.join(self.base_path, 'Scripts', '.config', 'arcade-organizer')
        self.ini_path = os.path.join(self.base_path, 'update_arcade-organizer.ini')
        self.mad_db_path = os.path.join(self.base_path, FILE_arcade_database_mad_db_json_zip)

        os.makedirs(self.mradir, exist_ok=True)
        os.makedirs(os.path.dirname(self.mad_db_path), exist_ok=True)
        # work_path is NOT pre-created — the organizer creates it itself

        self._copy_mra_fixtures()
        self._create_cores_directory()
        self._create_local_mad_db_zip()
        self._create_ini_file()

        self.ao_service = ArcadeOrganizerService(NoLogger())

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _copy_mra_fixtures(self):
        fixtures_dir = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'arcade_organizer', 'mra')
        for root, dirs, files in os.walk(fixtures_dir):
            rel_path = os.path.relpath(root, fixtures_dir)
            dest_path = os.path.join(self.mradir, rel_path) if rel_path != '.' else self.mradir
            for dir_name in dirs:
                os.makedirs(os.path.join(dest_path, dir_name), exist_ok=True)
            for file_name in files:
                if file_name.endswith('.mra'):
                    shutil.copy2(os.path.join(root, file_name), os.path.join(dest_path, file_name))

    def _create_cores_directory(self):
        cores_dir = os.path.join(self.mradir, 'cores')
        os.makedirs(cores_dir, exist_ok=True)
        for name in ['PacMan_20201225.rbf', 'DonkeyKong_20210101.rbf', 'Galaga_20201215.rbf',
                      'Capcom1942_20210201.rbf', 'OutRun_20210301.rbf', 'Frogger_20201220.rbf',
                      'StreetFighter2_20210401.rbf', 'Raiden_20210315.rbf', 'BurgerTime_20201230.rbf']:
            Path(os.path.join(cores_dir, name)).touch()

    def _create_local_mad_db_zip(self):
        """Create MAD_DB zip at the default local path (not in work_path cache).

        This forces the organizer to go through the full flow:
        copy local file -> tmp_data.zip -> compare with cached -> cache -> read via zipfile
        """
        mad_db_fixture = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'arcade_organizer', 'mad_db.json')
        with open(mad_db_fixture, 'r') as f:
            mad_db_data = f.read()

        with zipfile.ZipFile(self.mad_db_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr('mad_db.json', mad_db_data)

    def _create_ini_file(self, **overrides):
        options = dict(
            NO_SYMLINKS='true',
            SKIPALTS='false',
            AZ_DIR='true',
            REGION_MAIN='DEV PREFERRED',
            REGION_OTHERS=2,
            RESOLUTION_15KHZ='true',
            RESOLUTION_24KHZ='true',
            RESOLUTION_31KHZ='true',
            ROTATION_0='true',
            ROTATION_90='true',
            ROTATION_180='true',
            ROTATION_270='true',
            FLIP='true',
            PREPEND_YEAR='false',
            DECADES_DIR='true',
            BOOTLEG=2,
            HOMEBREW=2,
            ROTATION_DIR='true',
            RESOLUTION_DIR='true',
            REGION_DIR='true',
            YEAR_DIR='true',
            NUM_BUTTONS_DIR='true',
            MOVE_INPUTS_DIR='true',
            PLAYERS_DIR='true',
            CORE_DIR='true',
            MANUFACTURER_DIR='true',
            CATEGORY_DIR='true',
            SERIES_DIR='true',
            PLATFORM_DIR='true',
            SPECIAL_CONTROLS_DIR='true',
            NUM_MONITORS_DIR='true',
        )
        options.update(overrides)
        with open(self.ini_path, 'w') as f:
            f.write('[DEFAULT]\n')
            for key, value in options.items():
                f.write(f'{key}={value}\n')

    def _make_config(self):
        return self.ao_service.make_arcade_organizer_config(self.ini_path, self.base_path, '')

    def _get_organized_mra_paths(self):
        mra_paths = set()
        for root, _dirs, files in os.walk(self.orgdir):
            for file in files:
                if file.endswith('.mra'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.orgdir)
                    mra_paths.add(rel_path)
        return mra_paths

    def _add_mra_file(self, name, setname, rbf):
        """Add a new MRA file to the arcade directory."""
        mra_content = f'<misterromdescription>\n<setname>{setname}</setname>\n<rbf>{rbf}</rbf>\n</misterromdescription>'
        mra_path = os.path.join(self.mradir, name)
        with open(mra_path, 'w') as f:
            f.write(mra_content)

    def _update_mad_db_with(self, extra_entries):
        """Update the local MAD_DB zip with additional entries."""
        mad_db_fixture = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'arcade_organizer', 'mad_db.json')
        with open(mad_db_fixture, 'r') as f:
            mad_db = json.loads(f.read())

        mad_db.update(extra_entries)

        with zipfile.ZipFile(self.mad_db_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr('mad_db.json', json.dumps(mad_db))

    def test_complete_pc_flow(self):
        """Full realistic PC flow: fresh build, verify, incremental, add content, rebuild."""

        config = self._make_config()

        # === Phase 1: Full build from scratch ===

        self.assertFalse(os.path.exists(self.work_path), "Work path should not exist before first run")

        success = self.ao_service.run_arcade_organizer_organize_all_mras(config)
        self.assertTrue(success, "First full build should succeed")
        self.assertTrue(os.path.isdir(self.orgdir), "Organized directory should be created")
        self.assertTrue(os.path.isdir(self.work_path), "Work path should be created by organizer")

        paths_full_build = self._get_organized_mra_paths()

        # Verify substantial output — all options enabled with 11 MRAs produces many organized entries
        self.assertGreater(len(paths_full_build), 80, f"Expected many organized paths, got {len(paths_full_build)}")

        # Spot-check key categories exist
        categories_found = set()
        for p in paths_full_build:
            top = p.split(os.sep)[0]
            categories_found.add(top)

        expected_categories = {'_1 0-9', '_1 A-E', '_1 F-K', '_1 L-Q', '_1 R-T',
                               '_2 Region', '_3 Collections', '_4 Video & Inputs', '_5 Extra Software'}
        self.assertEqual(expected_categories, categories_found, "All top-level categories should be present")

        # Verify NO_SYMLINKS: all files should be regular copies, not symlinks
        for rel_path in paths_full_build:
            full_path = os.path.join(self.orgdir, rel_path)
            self.assertTrue(os.path.isfile(full_path), f"{rel_path} should exist as a file")
            self.assertFalse(os.path.islink(full_path), f"{rel_path} should be a copy, not a symlink")

        # Verify specific entries from different organization axes
        required_paths = {
            '_1 L-Q/pacman.mra',
            '_2 Region/_World/pacman.mra',
            '_3 Collections/_3 By Year/_1980/pacman.mra',
            '_3 Collections/_3 By Year/_The 1980s/pacman.mra',
            '_3 Collections/_4 By Genre/_Maze/pacman.mra',
            '_3 Collections/_5 By Manufacturer/_Namco/pacman.mra',
            '_3 Collections/_6 By Series/_Pac-Man/pacman.mra',
            '_4 Video & Inputs/_1 Resolution/_15kHz/pacman.mra',
            '_4 Video & Inputs/_2 Rotation/_Vertical (CW)/pacman.mra',
            '_4 Video & Inputs/_3 Move Inputs/_4-way Joystick/pacman.mra',
            '_4 Video & Inputs/_4 Num Buttons/_0/pacman.mra',
            '_4 Video & Inputs/_6 Players/_2/pacman.mra',
            '_5 Extra Software/_1 Bootleg/pacmanbl.mra',
            '_4 Video & Inputs/_1 Resolution/_31kHz/outrun.mra',
            '_4 Video & Inputs/_5 Special Inputs/_Steering/outrun.mra',
            '_4 Video & Inputs/_7 Cocktail/frogger.mra',
            '_3 Collections/_4 By Genre/_Fighter/sf2.mra',
        }
        missing = required_paths - paths_full_build
        self.assertEqual(set(), missing, f"Missing required paths: {missing}")

        # Verify cached database was created by the flow
        cached_data_zip = os.path.join(self.work_path, 'data.zip')
        self.assertTrue(os.path.isfile(cached_data_zip), "Cached data.zip should exist after first run")

        # Verify last_run file was written
        last_run = os.path.join(self.work_path, 'last_run')
        self.assertTrue(os.path.isfile(last_run), "last_run file should exist after first run")

        # === Phase 2: Incremental build (no changes) ===

        success = self.ao_service.run_arcade_organizer_organize_all_mras(config)
        self.assertTrue(success, "Incremental build should succeed")

        paths_incremental = self._get_organized_mra_paths()
        self.assertEqual(paths_full_build, paths_incremental, "Incremental build should produce identical results")

        # === Phase 3: Add new content and rebuild ===

        self._add_mra_file('centipede.mra', 'centiped', 'Centipede')
        self._update_mad_db_with({
            'centiped': {
                'file': 'centipede.mra',
                'rotation': 270,
                'flip': False,
                'resolution': '15kHz',
                'region': 'World',
                'homebrew': False,
                'bootleg': False,
                'year': 1981,
                'manufacturer': ['Atari'],
                'platform': ['Atari Centipede'],
                'category': ["Shoot 'em Up"],
                'series': ['Centipede'],
                'players': '2',
                'move_inputs': ['Trackball'],
                'special_controls': ['Trackball'],
                'num_buttons': 1,
                'num_monitors': 1,
                'cocktail': 'yes',
            }
        })

        # Touch the new file to ensure it's newer than last_run
        time.sleep(0.1)
        Path(os.path.join(self.mradir, 'centipede.mra')).touch()

        config = self._make_config()
        success = self.ao_service.run_arcade_organizer_organize_all_mras(config)
        self.assertTrue(success, "Rebuild after adding content should succeed")

        paths_after_add = self._get_organized_mra_paths()

        # New MRA should appear in organized output
        new_paths = paths_after_add - paths_incremental
        centipede_paths = {p for p in new_paths if 'centipede.mra' in p}
        self.assertGreater(len(centipede_paths), 0, "Centipede should appear in organized output after adding")

        expected_centipede = {
            '_1 A-E/centipede.mra',
            '_2 Region/_World/centipede.mra',
            '_3 Collections/_1 By Platform/_Atari Centipede/centipede.mra',
            '_3 Collections/_3 By Year/_1981/centipede.mra',
            '_3 Collections/_3 By Year/_The 1980s/centipede.mra',
            "_3 Collections/_4 By Genre/_Shoot 'em Up/centipede.mra",
            '_3 Collections/_5 By Manufacturer/_Atari/centipede.mra',
            '_3 Collections/_6 By Series/_Centipede/centipede.mra',
            '_4 Video & Inputs/_1 Resolution/_15kHz/centipede.mra',
            '_4 Video & Inputs/_2 Rotation/_Vertical (CCW)/centipede.mra',
            '_4 Video & Inputs/_3 Move Inputs/_Trackball/centipede.mra',
            '_4 Video & Inputs/_4 Num Buttons/_1/centipede.mra',
            '_4 Video & Inputs/_5 Special Inputs/_Trackball/centipede.mra',
            '_4 Video & Inputs/_6 Players/_2/centipede.mra',
            '_4 Video & Inputs/_7 Cocktail/centipede.mra',
            '_4 Video & Inputs/_8 Num Monitors/_1/centipede.mra',
        }
        missing_centipede = expected_centipede - paths_after_add
        self.assertEqual(set(), missing_centipede, f"Missing centipede paths: {missing_centipede}")

        # All centipede files should be copies, not symlinks
        for rel_path in expected_centipede:
            full_path = os.path.join(self.orgdir, rel_path)
            self.assertFalse(os.path.islink(full_path), f"{rel_path} should be a copy after incremental add")

        # === Phase 4: Verify orgdir folders listing ===

        folders, success = self.ao_service.run_arcade_organizer_print_orgdir_folders(config)
        self.assertTrue(success, "print_orgdir_folders should succeed")
        self.assertGreater(len(folders), 5, "Should report multiple organized folders")

        expected_folders = {
            os.path.join(self.orgdir, '_1 0-9'),
            os.path.join(self.orgdir, '_1 A-E'),
            os.path.join(self.orgdir, '_1 F-K'),
            os.path.join(self.orgdir, '_1 L-Q'),
            os.path.join(self.orgdir, '_1 R-T'),
            os.path.join(self.orgdir, '_2 Region'),
            os.path.join(self.orgdir, '_3 Collections'),
            os.path.join(self.orgdir, '_4 Video & Inputs'),
            os.path.join(self.orgdir, '_5 Extra Software'),
        }
        self.assertTrue(expected_folders.issubset(set(folders)), "Top-level organized folders should be listed")

