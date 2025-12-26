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
import unittest
import zipfile
from pathlib import Path

from update_all.arcade_organizer.arcade_organizer import ArcadeOrganizerService
from test.logger_tester import NoLogger


class TestArcadeOrganizerIntegration(unittest.TestCase):
    """Integration tests for Arcade Organizer with all options enabled."""

    def setUp(self):
        """Set up test environment with temp directory and fixtures."""
        # Create temp directory for all test operations
        self.test_dir = tempfile.mkdtemp(prefix='ao_test_')
        self.base_path = self.test_dir

        # Set up directory structure
        self.mradir = os.path.join(self.base_path, '_Arcade')
        self.orgdir = os.path.join(self.base_path, '_Arcade', '_Organized')
        self.work_path = os.path.join(self.base_path, 'Scripts', '.config', 'arcade-organizer')
        self.ini_path = os.path.join(self.base_path, 'Scripts', 'update_arcade-organizer.ini')

        # Create required directories
        os.makedirs(self.mradir, exist_ok=True)
        os.makedirs(self.work_path, exist_ok=True)
        os.makedirs(os.path.dirname(self.ini_path), exist_ok=True)

        # Copy MRA fixtures to MRADIR
        fixtures_dir = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'arcade_organizer', 'mra')
        self._copy_fixtures(fixtures_dir, self.mradir)

        # Create MAD database zip
        self._create_mad_database_zip()

        # Create cores directory with some dummy cores
        self._create_cores_directory()

        # Initialize arcade organizer service
        self.ao_service = ArcadeOrganizerService(NoLogger())

    def tearDown(self):
        """Clean up temp directory after test."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _copy_fixtures(self, source_dir, dest_dir):
        """Recursively copy MRA fixtures to test MRADIR."""
        for root, dirs, files in os.walk(source_dir):
            # Calculate relative path from source_dir
            rel_path = os.path.relpath(root, source_dir)
            dest_path = os.path.join(dest_dir, rel_path) if rel_path != '.' else dest_dir

            # Create directories
            for dir_name in dirs:
                os.makedirs(os.path.join(dest_path, dir_name), exist_ok=True)

            # Copy files
            for file_name in files:
                if file_name.endswith('.mra'):
                    src_file = os.path.join(root, file_name)
                    dst_file = os.path.join(dest_path, file_name)
                    shutil.copy2(src_file, dst_file)

    def _create_mad_database_zip(self):
        """Create zipped MAD database from fixture."""
        mad_db_fixture = os.path.join(
            os.path.dirname(__file__), '..', 'fixtures', 'arcade_organizer', 'mad_db.json'
        )

        # Read the JSON fixture
        with open(mad_db_fixture, 'r') as f:
            mad_db_data = f.read()

        # Create zip file in work path
        zip_path = os.path.join(self.work_path, 'data.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr('mad_db.json', mad_db_data)

    def _create_cores_directory(self):
        """Create cores directory with dummy core files."""
        cores_dir = os.path.join(self.mradir, 'cores')
        os.makedirs(cores_dir, exist_ok=True)

        # Create dummy core files
        core_names = [
            'PacMan_20201225.rbf',
            'DonkeyKong_20210101.rbf',
            'Galaga_20201215.rbf',
            'Capcom1942_20210201.rbf',
            'OutRun_20210301.rbf',
            'Frogger_20201220.rbf',
            'StreetFighter2_20210401.rbf',
            'Raiden_20210315.rbf',
            'BurgerTime_20201230.rbf'
        ]

        for core_name in core_names:
            core_path = os.path.join(cores_dir, core_name)
            Path(core_path).touch()

    def _create_ini_file(self, **options):
        """Create INI file with specified options."""
        with open(self.ini_path, 'w') as f:
            f.write('[DEFAULT]\n')
            for key, value in options.items():
                if isinstance(value, bool):
                    f.write(f'{key}={str(value).lower()}\n')
                else:
                    f.write(f'{key}={value}\n')

    def test_organize___with_all_options_enabled___creates_complete_structure(self):
        """Test arcade organizer with all options enabled (happy path)."""
        self._create_ini_file(
            SKIPALTS=False,
            VERBOSE=False,
            AZ_DIR=True,
            NO_SYMLINKS=False,
            REGION_MAIN='World',
            REGION_OTHERS=2,  # EVERYWHERE
            RESOLUTION_15KHZ=True,
            RESOLUTION_24KHZ=True,
            RESOLUTION_31KHZ=True,
            ROTATION_0=True,
            ROTATION_90=True,
            ROTATION_180=True,
            ROTATION_270=True,
            FLIP=True,
            PREPEND_YEAR=False,
            DECADES_DIR=True,
            BOOTLEG=2,  # EVERYWHERE
            HOMEBREW=2,  # EVERYWHERE
            ROTATION_DIR=True,
            RESOLUTION_DIR=True,
            REGION_DIR=True,
            YEAR_DIR=True,
            NUM_BUTTONS_DIR=True,
            MOVE_INPUTS_DIR=True,
            PLAYERS_DIR=True,
            CORE_DIR=True,
            MANUFACTURER_DIR=True,
            CATEGORY_DIR=True,
            SERIES_DIR=True,
            PLATFORM_DIR=True,
            SPECIAL_CONTROLS_DIR=True,
            NUM_MONITORS_DIR=True
        )

        config = self.ao_service.make_arcade_organizer_config(
            self.ini_path,
            self.base_path,
            ''
        )

        success = self.ao_service.run_arcade_organizer_organize_all_mras(config)
        self.assertTrue(success, "Arcade organizer should complete successfully")
        self.assertTrue(os.path.exists(self.orgdir), "Organized directory should exist")

        actual_paths = self._get_organized_mra_paths()

        # With all options enabled, each MRA gets placed in many directories
        self.assertGreater(len(actual_paths), 100, "Should have many organized MRA paths with all options enabled")

        # Verify key paths exist (sampling from different organization categories)
        required_paths = {
            # Alphabetic
            '_1 0-9/1942.mra',
            '_1 A-E/burgertime.mra',
            '_1 A-E/dkong.mra',
            '_1 F-K/frogger.mra',
            '_1 L-Q/pacman.mra',
            '_1 R-T/sf2.mra',
            # Region
            '_2 Region/_World/pacman.mra',
            '_2 Region/_USA/dkong.mra',
            # Category
            '_3 Collections/_4 By Genre/_Maze/pacman.mra',
            '_3 Collections/_4 By Genre/_Fighter/sf2.mra',
            # Year
            '_3 Collections/_3 By Year/_1980/pacman.mra',
            '_3 Collections/_3 By Year/_The 1980s/pacman.mra',
            # Rotation
            '_4 Video & Inputs/_2 Rotation/_Horizontal/sf2.mra',
            '_4 Video & Inputs/_2 Rotation/_Vertical (CW)/pacman.mra',
            # Resolution
            '_4 Video & Inputs/_1 Resolution/_15kHz/pacman.mra',
            '_4 Video & Inputs/_1 Resolution/_31kHz/outrun.mra',
        }

        missing_paths = required_paths - actual_paths
        self.assertEqual(set(), missing_paths, f"Required paths should exist. Missing: {missing_paths}")

        # Verify at least the first required path is a symlink (NO_SYMLINKS is False)
        first_required_path = next(iter(sorted(required_paths)))
        full_path = os.path.join(self.orgdir, first_required_path)
        self.assertTrue(os.path.islink(full_path), f"{first_required_path} should be a symlink")

    def test_organize___with_bootleg_filter___excludes_bootleg_games(self):
        """Test that bootleg filter works correctly."""
        self._create_ini_file(
            SKIPALTS=True,
            AZ_DIR=True,
            BOOTLEG=0,  # DEACTIVATED - skip bootlegs
            REGION_MAIN='World'
        )

        config = self.ao_service.make_arcade_organizer_config(
            self.ini_path,
            self.base_path,
            ''
        )

        success = self.ao_service.run_arcade_organizer_organize_all_mras(config)
        self.assertTrue(success)

        # pacmanbl.mra should be excluded everywhere when bootleg filter is active
        expected_paths = {
            '_1 0-9/1942.mra',
            '_1 F-K/frogger.mra',
            '_1 F-K/galaga.mra',
            '_1 L-Q/outrun.mra',
            '_1 L-Q/pacman.mra',
            '_1 R-T/sf2.mra',
            '_2 Region/_Japan/raiden.mra',
            '_2 Region/_USA/burgertime.mra',
            '_2 Region/_USA/dkong.mra',
            '_2 Region/_USA/mspacman.mra',
            '_2 Region/_World/1942.mra',
            '_2 Region/_World/frogger.mra',
            '_2 Region/_World/galaga.mra',
            '_2 Region/_World/outrun.mra',
            '_2 Region/_World/pacman.mra',
            '_2 Region/_World/sf2.mra',
            '_3 Collections/_1 By Platform/_CPS1/sf2.mra',
            '_3 Collections/_1 By Platform/_Capcom Z80/1942.mra',
            '_3 Collections/_1 By Platform/_Konami Scramble/frogger.mra',
            '_3 Collections/_1 By Platform/_Namco Galaga/galaga.mra',
            '_3 Collections/_1 By Platform/_Namco Pac-Man/pacman.mra',
            '_3 Collections/_1 By Platform/_Sega Out Run/outrun.mra',
            '_3 Collections/_2 By MiSTer Core/_Capcom1942/1942.mra',
            '_3 Collections/_2 By MiSTer Core/_Frogger/frogger.mra',
            '_3 Collections/_2 By MiSTer Core/_Galaga/galaga.mra',
            '_3 Collections/_2 By MiSTer Core/_OutRun/outrun.mra',
            '_3 Collections/_2 By MiSTer Core/_PacMan/pacman.mra',
            '_3 Collections/_2 By MiSTer Core/_StreetFighter2/sf2.mra',
            '_3 Collections/_3 By Year/_1980/pacman.mra',
            '_3 Collections/_3 By Year/_1981/frogger.mra',
            '_3 Collections/_3 By Year/_1981/galaga.mra',
            '_3 Collections/_3 By Year/_1984/1942.mra',
            '_3 Collections/_3 By Year/_1986/outrun.mra',
            '_3 Collections/_3 By Year/_1991/sf2.mra',
            '_3 Collections/_3 By Year/_The 1980s/1942.mra',
            '_3 Collections/_3 By Year/_The 1980s/frogger.mra',
            '_3 Collections/_3 By Year/_The 1980s/galaga.mra',
            '_3 Collections/_3 By Year/_The 1980s/outrun.mra',
            '_3 Collections/_3 By Year/_The 1980s/pacman.mra',
            '_3 Collections/_3 By Year/_The 1990s/sf2.mra',
            '_3 Collections/_4 By Genre/_Action/frogger.mra',
            '_3 Collections/_4 By Genre/_Driving/outrun.mra',
            '_3 Collections/_4 By Genre/_Fighter/sf2.mra',
            '_3 Collections/_4 By Genre/_Maze/pacman.mra',
            '_3 Collections/_4 By Genre/_Racing/outrun.mra',
            "_3 Collections/_4 By Genre/_Shoot 'em Up/1942.mra",
            "_3 Collections/_4 By Genre/_Shoot 'em Up/galaga.mra",
            '_3 Collections/_4 By Genre/_Versus/sf2.mra',
            '_3 Collections/_4 By Genre/_Vertical/1942.mra',
            '_3 Collections/_4 By Genre/_Vertical/galaga.mra',
            '_3 Collections/_5 By Manufacturer/_Capcom/1942.mra',
            '_3 Collections/_5 By Manufacturer/_Capcom/sf2.mra',
            '_3 Collections/_5 By Manufacturer/_Konami/frogger.mra',
            '_3 Collections/_5 By Manufacturer/_Namco/galaga.mra',
            '_3 Collections/_5 By Manufacturer/_Namco/pacman.mra',
            '_3 Collections/_5 By Manufacturer/_Sega/outrun.mra',
            '_3 Collections/_6 By Series/_1942/1942.mra',
            '_3 Collections/_6 By Series/_Galaxian/galaga.mra',
            '_3 Collections/_6 By Series/_Out Run/outrun.mra',
            '_3 Collections/_6 By Series/_Pac-Man/pacman.mra',
            '_3 Collections/_6 By Series/_Street Fighter/sf2.mra',
            '_4 Video & Inputs/_1 Resolution/_15kHz/1942.mra',
            '_4 Video & Inputs/_1 Resolution/_15kHz/frogger.mra',
            '_4 Video & Inputs/_1 Resolution/_15kHz/galaga.mra',
            '_4 Video & Inputs/_1 Resolution/_15kHz/pacman.mra',
            '_4 Video & Inputs/_1 Resolution/_15kHz/sf2.mra',
            '_4 Video & Inputs/_1 Resolution/_31kHz/outrun.mra',
            '_4 Video & Inputs/_2 Rotation/_Horizontal/outrun.mra',
            '_4 Video & Inputs/_2 Rotation/_Horizontal/sf2.mra',
            '_4 Video & Inputs/_2 Rotation/_Vertical (CCW)/1942.mra',
            '_4 Video & Inputs/_2 Rotation/_Vertical (CCW)/galaga.mra',
            '_4 Video & Inputs/_2 Rotation/_Vertical (CW)/frogger.mra',
            '_4 Video & Inputs/_2 Rotation/_Vertical (CW)/pacman.mra',
            '_4 Video & Inputs/_3 Move Inputs/_2-way Joystick/galaga.mra',
            '_4 Video & Inputs/_3 Move Inputs/_4-way Joystick/frogger.mra',
            '_4 Video & Inputs/_3 Move Inputs/_4-way Joystick/pacman.mra',
            '_4 Video & Inputs/_3 Move Inputs/_8-way Joystick/1942.mra',
            '_4 Video & Inputs/_3 Move Inputs/_8-way Joystick/sf2.mra',
            '_4 Video & Inputs/_3 Move Inputs/_Steering Wheel/outrun.mra',
            '_4 Video & Inputs/_4 Num Buttons/_0/frogger.mra',
            '_4 Video & Inputs/_4 Num Buttons/_0/pacman.mra',
            '_4 Video & Inputs/_4 Num Buttons/_1/galaga.mra',
            '_4 Video & Inputs/_4 Num Buttons/_2/1942.mra',
            '_4 Video & Inputs/_4 Num Buttons/_2/outrun.mra',
            '_4 Video & Inputs/_4 Num Buttons/_6/sf2.mra',
            '_4 Video & Inputs/_5 Special Inputs/_Pedal/outrun.mra',
            '_4 Video & Inputs/_5 Special Inputs/_Steering/outrun.mra',
            '_4 Video & Inputs/_6 Players/_1/outrun.mra',
            '_4 Video & Inputs/_6 Players/_2/1942.mra',
            '_4 Video & Inputs/_6 Players/_2/frogger.mra',
            '_4 Video & Inputs/_6 Players/_2/galaga.mra',
            '_4 Video & Inputs/_6 Players/_2/pacman.mra',
            '_4 Video & Inputs/_6 Players/_2/sf2.mra',
            '_4 Video & Inputs/_7 Cocktail/frogger.mra',
            '_4 Video & Inputs/_8 Num Monitors/_1/1942.mra',
            '_4 Video & Inputs/_8 Num Monitors/_1/frogger.mra',
            '_4 Video & Inputs/_8 Num Monitors/_1/galaga.mra',
            '_4 Video & Inputs/_8 Num Monitors/_1/outrun.mra',
            '_4 Video & Inputs/_8 Num Monitors/_1/pacman.mra',
            '_4 Video & Inputs/_8 Num Monitors/_1/sf2.mra',
        }

        actual_paths = self._get_organized_mra_paths()
        self.assertEqual(expected_paths, actual_paths, "Bootleg games should be filtered out")

    def test_organize___with_region_filter___includes_only_matching_region(self):
        """Test that region filter works correctly."""
        self._create_ini_file(
            SKIPALTS=False,
            AZ_DIR=True,
            REGION_MAIN='USA',
            REGION_OTHERS=0  # DEACTIVATED - only show USA region
        )

        config = self.ao_service.make_arcade_organizer_config(
            self.ini_path,
            self.base_path,
            ''
        )

        success = self.ao_service.run_arcade_organizer_organize_all_mras(config)
        self.assertTrue(success)

        # Only USA region games (DK, BurgerTime, Ms. Pac-Man) + bootleg in Extra Software
        expected_paths = {
            '_1 A-E/burgertime.mra',
            '_1 A-E/dkong.mra',
            '_1 L-Q/mspacman.mra',
            '_2 Region/_USA/burgertime.mra',
            '_2 Region/_USA/dkong.mra',
            '_2 Region/_USA/mspacman.mra',
            '_3 Collections/_1 By Platform/_Data East Burger Time/burgertime.mra',
            '_3 Collections/_1 By Platform/_Namco Pac-Man/mspacman.mra',
            '_3 Collections/_1 By Platform/_Nintendo/dkong.mra',
            '_3 Collections/_2 By MiSTer Core/_BurgerTime/burgertime.mra',
            '_3 Collections/_2 By MiSTer Core/_DonkeyKong/dkong.mra',
            '_3 Collections/_2 By MiSTer Core/_PacMan/mspacman.mra',
            '_3 Collections/_3 By Year/_1981/dkong.mra',
            '_3 Collections/_3 By Year/_1981/mspacman.mra',
            '_3 Collections/_3 By Year/_1982/burgertime.mra',
            '_3 Collections/_3 By Year/_The 1980s/burgertime.mra',
            '_3 Collections/_3 By Year/_The 1980s/dkong.mra',
            '_3 Collections/_3 By Year/_The 1980s/mspacman.mra',
            '_3 Collections/_4 By Genre/_Climb/burgertime.mra',
            '_3 Collections/_4 By Genre/_Climb/dkong.mra',
            '_3 Collections/_4 By Genre/_Maze/mspacman.mra',
            '_3 Collections/_4 By Genre/_Platform/burgertime.mra',
            '_3 Collections/_4 By Genre/_Platform/dkong.mra',
            '_3 Collections/_5 By Manufacturer/_Data East/burgertime.mra',
            '_3 Collections/_5 By Manufacturer/_Namco/mspacman.mra',
            '_3 Collections/_5 By Manufacturer/_Nintendo/dkong.mra',
            '_3 Collections/_6 By Series/_Donkey Kong/dkong.mra',
            '_3 Collections/_6 By Series/_Pac-Man/mspacman.mra',
            '_4 Video & Inputs/_1 Resolution/_15kHz/burgertime.mra',
            '_4 Video & Inputs/_1 Resolution/_15kHz/dkong.mra',
            '_4 Video & Inputs/_1 Resolution/_15kHz/mspacman.mra',
            '_4 Video & Inputs/_2 Rotation/_Vertical (CW)/burgertime.mra',
            '_4 Video & Inputs/_2 Rotation/_Vertical (CW)/dkong.mra',
            '_4 Video & Inputs/_2 Rotation/_Vertical (CW)/mspacman.mra',
            '_4 Video & Inputs/_3 Move Inputs/_4-way Joystick/burgertime.mra',
            '_4 Video & Inputs/_3 Move Inputs/_4-way Joystick/dkong.mra',
            '_4 Video & Inputs/_3 Move Inputs/_4-way Joystick/mspacman.mra',
            '_4 Video & Inputs/_4 Num Buttons/_0/burgertime.mra',
            '_4 Video & Inputs/_4 Num Buttons/_0/mspacman.mra',
            '_4 Video & Inputs/_4 Num Buttons/_1/dkong.mra',
            '_4 Video & Inputs/_6 Players/_2/burgertime.mra',
            '_4 Video & Inputs/_6 Players/_2/dkong.mra',
            '_4 Video & Inputs/_6 Players/_2/mspacman.mra',
            '_4 Video & Inputs/_8 Num Monitors/_1/burgertime.mra',
            '_4 Video & Inputs/_8 Num Monitors/_1/dkong.mra',
            '_4 Video & Inputs/_8 Num Monitors/_1/mspacman.mra',
            '_5 Extra Software/_1 Bootleg/pacmanbl.mra',
        }

        actual_paths = self._get_organized_mra_paths()
        self.assertEqual(expected_paths, actual_paths, "Only USA region games should be organized")

    def test_print_orgdir_folders___after_organizing___returns_top_level_directories(self):
        """Test that print_orgdir_folders returns correct list."""
        self._create_ini_file(
            AZ_DIR=True,
            CATEGORY_DIR=True
        )

        config = self.ao_service.make_arcade_organizer_config(
            self.ini_path,
            self.base_path,
            ''
        )

        success = self.ao_service.run_arcade_organizer_organize_all_mras(config)
        self.assertTrue(success)

        folders, success = self.ao_service.run_arcade_organizer_print_orgdir_folders(config)
        self.assertTrue(success)

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

        self.assertEqual(expected_folders, set(folders), "Folder list should match expected directories")

    def test_organize___with_no_symlinks_option___creates_file_copies(self):
        """Test that NO_SYMLINKS option creates copies instead of symlinks."""
        self._create_ini_file(
            SKIPALTS=False,
            AZ_DIR=True,
            NO_SYMLINKS=True,
            REGION_MAIN='World'
        )

        config = self.ao_service.make_arcade_organizer_config(
            self.ini_path,
            self.base_path,
            ''
        )

        success = self.ao_service.run_arcade_organizer_organize_all_mras(config)
        self.assertTrue(success)

        expected_paths = {
            '_1 0-9/1942.mra',
            '_1 F-K/frogger.mra',
            '_1 F-K/galaga.mra',
            '_1 L-Q/outrun.mra',
            '_1 L-Q/pacman.mra',
            '_1 R-T/sf2.mra',
            '_2 Region/_Japan/raiden.mra',
            '_2 Region/_USA/burgertime.mra',
            '_2 Region/_USA/dkong.mra',
            '_2 Region/_USA/mspacman.mra',
            '_2 Region/_World/1942.mra',
            '_2 Region/_World/frogger.mra',
            '_2 Region/_World/galaga.mra',
            '_2 Region/_World/outrun.mra',
            '_2 Region/_World/pacman.mra',
            '_2 Region/_World/sf2.mra',
            '_3 Collections/_1 By Platform/_CPS1/sf2.mra',
            '_3 Collections/_1 By Platform/_Capcom Z80/1942.mra',
            '_3 Collections/_1 By Platform/_Konami Scramble/frogger.mra',
            '_3 Collections/_1 By Platform/_Namco Galaga/galaga.mra',
            '_3 Collections/_1 By Platform/_Namco Pac-Man/pacman.mra',
            '_3 Collections/_1 By Platform/_Sega Out Run/outrun.mra',
            '_3 Collections/_2 By MiSTer Core/_Capcom1942/1942.mra',
            '_3 Collections/_2 By MiSTer Core/_Frogger/frogger.mra',
            '_3 Collections/_2 By MiSTer Core/_Galaga/galaga.mra',
            '_3 Collections/_2 By MiSTer Core/_OutRun/outrun.mra',
            '_3 Collections/_2 By MiSTer Core/_PacMan/pacman.mra',
            '_3 Collections/_2 By MiSTer Core/_StreetFighter2/sf2.mra',
            '_3 Collections/_3 By Year/_1980/pacman.mra',
            '_3 Collections/_3 By Year/_1981/frogger.mra',
            '_3 Collections/_3 By Year/_1981/galaga.mra',
            '_3 Collections/_3 By Year/_1984/1942.mra',
            '_3 Collections/_3 By Year/_1986/outrun.mra',
            '_3 Collections/_3 By Year/_1991/sf2.mra',
            '_3 Collections/_3 By Year/_The 1980s/1942.mra',
            '_3 Collections/_3 By Year/_The 1980s/frogger.mra',
            '_3 Collections/_3 By Year/_The 1980s/galaga.mra',
            '_3 Collections/_3 By Year/_The 1980s/outrun.mra',
            '_3 Collections/_3 By Year/_The 1980s/pacman.mra',
            '_3 Collections/_3 By Year/_The 1990s/sf2.mra',
            '_3 Collections/_4 By Genre/_Action/frogger.mra',
            '_3 Collections/_4 By Genre/_Driving/outrun.mra',
            '_3 Collections/_4 By Genre/_Fighter/sf2.mra',
            '_3 Collections/_4 By Genre/_Maze/pacman.mra',
            '_3 Collections/_4 By Genre/_Racing/outrun.mra',
            "_3 Collections/_4 By Genre/_Shoot 'em Up/1942.mra",
            "_3 Collections/_4 By Genre/_Shoot 'em Up/galaga.mra",
            '_3 Collections/_4 By Genre/_Versus/sf2.mra',
            '_3 Collections/_4 By Genre/_Vertical/1942.mra',
            '_3 Collections/_4 By Genre/_Vertical/galaga.mra',
            '_3 Collections/_5 By Manufacturer/_Capcom/1942.mra',
            '_3 Collections/_5 By Manufacturer/_Capcom/sf2.mra',
            '_3 Collections/_5 By Manufacturer/_Konami/frogger.mra',
            '_3 Collections/_5 By Manufacturer/_Namco/galaga.mra',
            '_3 Collections/_5 By Manufacturer/_Namco/pacman.mra',
            '_3 Collections/_5 By Manufacturer/_Sega/outrun.mra',
            '_3 Collections/_6 By Series/_1942/1942.mra',
            '_3 Collections/_6 By Series/_Galaxian/galaga.mra',
            '_3 Collections/_6 By Series/_Out Run/outrun.mra',
            '_3 Collections/_6 By Series/_Pac-Man/pacman.mra',
            '_3 Collections/_6 By Series/_Street Fighter/sf2.mra',
            '_4 Video & Inputs/_1 Resolution/_15kHz/1942.mra',
            '_4 Video & Inputs/_1 Resolution/_15kHz/frogger.mra',
            '_4 Video & Inputs/_1 Resolution/_15kHz/galaga.mra',
            '_4 Video & Inputs/_1 Resolution/_15kHz/pacman.mra',
            '_4 Video & Inputs/_1 Resolution/_15kHz/sf2.mra',
            '_4 Video & Inputs/_1 Resolution/_31kHz/outrun.mra',
            '_4 Video & Inputs/_2 Rotation/_Horizontal/outrun.mra',
            '_4 Video & Inputs/_2 Rotation/_Horizontal/sf2.mra',
            '_4 Video & Inputs/_2 Rotation/_Vertical (CCW)/1942.mra',
            '_4 Video & Inputs/_2 Rotation/_Vertical (CCW)/galaga.mra',
            '_4 Video & Inputs/_2 Rotation/_Vertical (CW)/frogger.mra',
            '_4 Video & Inputs/_2 Rotation/_Vertical (CW)/pacman.mra',
            '_4 Video & Inputs/_3 Move Inputs/_2-way Joystick/galaga.mra',
            '_4 Video & Inputs/_3 Move Inputs/_4-way Joystick/frogger.mra',
            '_4 Video & Inputs/_3 Move Inputs/_4-way Joystick/pacman.mra',
            '_4 Video & Inputs/_3 Move Inputs/_8-way Joystick/1942.mra',
            '_4 Video & Inputs/_3 Move Inputs/_8-way Joystick/sf2.mra',
            '_4 Video & Inputs/_3 Move Inputs/_Steering Wheel/outrun.mra',
            '_4 Video & Inputs/_4 Num Buttons/_0/frogger.mra',
            '_4 Video & Inputs/_4 Num Buttons/_0/pacman.mra',
            '_4 Video & Inputs/_4 Num Buttons/_1/galaga.mra',
            '_4 Video & Inputs/_4 Num Buttons/_2/1942.mra',
            '_4 Video & Inputs/_4 Num Buttons/_2/outrun.mra',
            '_4 Video & Inputs/_4 Num Buttons/_6/sf2.mra',
            '_4 Video & Inputs/_5 Special Inputs/_Pedal/outrun.mra',
            '_4 Video & Inputs/_5 Special Inputs/_Steering/outrun.mra',
            '_4 Video & Inputs/_6 Players/_1/outrun.mra',
            '_4 Video & Inputs/_6 Players/_2/1942.mra',
            '_4 Video & Inputs/_6 Players/_2/frogger.mra',
            '_4 Video & Inputs/_6 Players/_2/galaga.mra',
            '_4 Video & Inputs/_6 Players/_2/pacman.mra',
            '_4 Video & Inputs/_6 Players/_2/sf2.mra',
            '_4 Video & Inputs/_7 Cocktail/frogger.mra',
            '_4 Video & Inputs/_8 Num Monitors/_1/1942.mra',
            '_4 Video & Inputs/_8 Num Monitors/_1/frogger.mra',
            '_4 Video & Inputs/_8 Num Monitors/_1/galaga.mra',
            '_4 Video & Inputs/_8 Num Monitors/_1/outrun.mra',
            '_4 Video & Inputs/_8 Num Monitors/_1/pacman.mra',
            '_4 Video & Inputs/_8 Num Monitors/_1/sf2.mra',
            '_5 Extra Software/_1 Bootleg/pacmanbl.mra',
        }

        actual_paths = self._get_organized_mra_paths()
        self.assertEqual(expected_paths, actual_paths, "All games should be organized with copies")

        for rel_path in actual_paths:
            full_path = os.path.join(self.orgdir, rel_path)
            self.assertTrue(
                os.path.isfile(full_path) and not os.path.islink(full_path),
                f"{rel_path} should be a regular file, not a symlink"
            )

    def test_organize___on_incremental_run___produces_identical_structure(self):
        """Test that incremental runs work correctly."""
        self._create_ini_file(
            SKIPALTS=False,
            AZ_DIR=True,
            CATEGORY_DIR=True
        )

        config = self.ao_service.make_arcade_organizer_config(
            self.ini_path,
            self.base_path,
            ''
        )

        success1 = self.ao_service.run_arcade_organizer_organize_all_mras(config)
        self.assertTrue(success1)

        paths_after_first_run = self._get_organized_mra_paths()

        success2 = self.ao_service.run_arcade_organizer_organize_all_mras(config)
        self.assertTrue(success2)

        paths_after_second_run = self._get_organized_mra_paths()

        self.assertEqual(
            paths_after_first_run,
            paths_after_second_run,
            "Incremental run should produce identical organization"
        )

    def _get_organized_mra_paths(self):
        """Get set of all MRA file paths relative to orgdir."""
        mra_paths = set()
        for root, dirs, files in os.walk(self.orgdir):
            for file in files:
                if file.endswith('.mra'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.orgdir)
                    mra_paths.add(rel_path)
        return mra_paths
