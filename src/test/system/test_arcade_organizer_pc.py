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
import shutil
import subprocess
import tempfile
import unittest

from unittest.mock import MagicMock

from update_all.analogue_pocket.http_gateway import fetch
from update_all.arcade_organizer.arcade_organizer import ArcadeOrganizerService
from update_all.constants import FILE_arcade_database_mad_db_json_zip
from test.logger_tester import NoLogger

DISTRIBUTION_MISTER_REPO = 'https://github.com/MiSTer-devel/Distribution_MiSTer.git'
JTCORES_MISTER_REPO = 'https://github.com/jotego/jtcores_mister.git'
MAD_DB_URL = 'https://raw.githubusercontent.com/MiSTer-devel/ArcadeDatabase_MiSTer/db/mad_db.json.zip'


class _BaseArcadeOrganizerRepoTest:
    """Mixin for tests that download real MRAs from a GitHub repo and run the organizer.

    Subclasses must also inherit from unittest.TestCase and define:
      - REPO_URL: str — git URL to clone
      - TEMP_PREFIX: str — prefix for tempdir
      - MIN_SOURCE_MRAS: int — minimum expected MRA count
      - MIN_ORGANIZED_PATHS: int — minimum expected organized output count
    """

    REPO_URL: str
    TEMP_PREFIX: str
    MIN_SOURCE_MRAS: int
    MIN_ORGANIZED_PATHS: int

    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp(prefix=cls.TEMP_PREFIX)
        cls.base_path = cls.test_dir
        cls.mradir = os.path.join(cls.base_path, '_Arcade')
        cls.orgdir = os.path.join(cls.base_path, '_Arcade', '_Organized')
        cls.work_path = os.path.join(cls.base_path, 'Scripts', '.config', 'arcade-organizer')
        cls.ini_path = os.path.join(cls.base_path, 'update_arcade-organizer.ini')
        cls.mad_db_path = os.path.join(cls.base_path, FILE_arcade_database_mad_db_json_zip)

        os.makedirs(cls.mradir, exist_ok=True)
        os.makedirs(os.path.dirname(cls.mad_db_path), exist_ok=True)

        cls._download_mras()
        cls._download_mad_db()
        cls._create_ini_file()

        cls.ao_service = ArcadeOrganizerService(NoLogger(), MagicMock())

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)

    @classmethod
    def _download_mras(cls):
        """Download _Arcade folder using git sparse checkout."""
        clone_dir = os.path.join(cls.test_dir, '_clone')
        subprocess.run([
            'git', 'clone', '--depth', '1', '--filter=blob:none', '--sparse',
            cls.REPO_URL, clone_dir
        ], check=True, capture_output=True, timeout=120)

        subprocess.run([
            'git', '-C', clone_dir, 'sparse-checkout', 'set', '_Arcade'
        ], check=True, capture_output=True, timeout=120)

        source_arcade = os.path.join(clone_dir, '_Arcade')
        if os.path.isdir(source_arcade):
            for root, dirs, files in os.walk(source_arcade):
                rel_path = os.path.relpath(root, source_arcade)
                dest_path = os.path.join(cls.mradir, rel_path) if rel_path != '.' else cls.mradir
                for dir_name in dirs:
                    if dir_name == '_Organized':
                        continue
                    os.makedirs(os.path.join(dest_path, dir_name), exist_ok=True)
                for file_name in files:
                    if file_name.endswith('.mra'):
                        shutil.copy2(os.path.join(root, file_name), os.path.join(dest_path, file_name))

        shutil.rmtree(clone_dir)

    @classmethod
    def _download_mad_db(cls):
        """Download the real MAD database zip."""
        status, data = fetch(MAD_DB_URL, timeout=60)
        if status != 200:
            raise Exception(f'Failed to download MAD DB: HTTP {status}')
        with open(cls.mad_db_path, 'wb') as f:
            f.write(data)

    @classmethod
    def _create_ini_file(cls):
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
        with open(cls.ini_path, 'w') as f:
            f.write('[DEFAULT]\n')
            for key, value in options.items():
                f.write(f'{key}={value}\n')

    def _get_organized_mra_paths(self):
        mra_paths = set()
        for root, _dirs, files in os.walk(self.orgdir):
            for file in files:
                if file.endswith('.mra'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.orgdir)
                    mra_paths.add(rel_path)
        return mra_paths

    def _count_source_mras(self):
        count = 0
        for root, _dirs, files in os.walk(self.mradir):
            if '_Organized' in root:
                continue
            for f in files:
                if f.endswith('.mra'):
                    count += 1
        return count

    def test_full_repo_build(self):
        """Build organized folders from the full repo _Arcade set."""

        source_mra_count = self._count_source_mras()
        self.assertGreater(source_mra_count, self.MIN_SOURCE_MRAS,
                           f"Expected >{self.MIN_SOURCE_MRAS} MRAs from {self.REPO_URL}, got {source_mra_count}")

        config = self.ao_service.make_arcade_organizer_config(self.ini_path, self.base_path, '')
        success = self.ao_service.run_arcade_organizer_organize_all_mras(config)
        self.assertTrue(success, "Full build should succeed")
        self.assertTrue(os.path.isdir(self.orgdir), "Organized directory should be created")

        paths = self._get_organized_mra_paths()

        self.assertGreater(len(paths), self.MIN_ORGANIZED_PATHS,
                           f"Expected >{self.MIN_ORGANIZED_PATHS} organized paths, got {len(paths)}")

        # Verify all top-level categories exist
        categories_found = set()
        for p in paths:
            top = p.split(os.sep)[0]
            categories_found.add(top)

        expected_categories = {'_1 0-9', '_1 A-E', '_1 F-K', '_1 L-Q', '_1 R-T',
                               '_2 Region', '_3 Collections', '_4 Video & Inputs', '_5 Extra Software'}
        missing_categories = expected_categories - categories_found
        self.assertEqual(set(), missing_categories,
                         f"Missing top-level categories: {missing_categories}")

        # Verify NO_SYMLINKS: spot-check that organized files are copies
        checked = 0
        for rel_path in sorted(paths)[:50]:
            full_path = os.path.join(self.orgdir, rel_path)
            self.assertFalse(os.path.islink(full_path), f"{rel_path} should be a copy, not a symlink")
            checked += 1
        self.assertEqual(50, checked)

        # Verify deep collection subcategories are populated
        collection_dirs = set()
        for p in paths:
            parts = p.split(os.sep)
            if len(parts) >= 3 and parts[0] == '_3 Collections':
                collection_dirs.add(parts[1])

        expected_collection_dirs = {
            '_1 By Platform', '_3 By Year',
            '_4 By Genre', '_5 By Manufacturer', '_6 By Series',
        }
        missing_collections = expected_collection_dirs - collection_dirs
        self.assertEqual(set(), missing_collections,
                         f"Missing collection subdirectories: {missing_collections}")

        # Verify video & inputs subcategories
        video_dirs = set()
        for p in paths:
            parts = p.split(os.sep)
            if len(parts) >= 3 and parts[0] == '_4 Video & Inputs':
                video_dirs.add(parts[1])

        expected_video_dirs = {
            '_1 Resolution', '_2 Rotation', '_3 Move Inputs',
            '_4 Num Buttons', '_6 Players',
        }
        missing_video = expected_video_dirs - video_dirs
        self.assertEqual(set(), missing_video,
                         f"Missing video & inputs subdirectories: {missing_video}")

        # Verify orgdir folders listing works
        folders, success = self.ao_service.run_arcade_organizer_print_orgdir_folders(config)
        self.assertTrue(success, "print_orgdir_folders should succeed")
        self.assertGreater(len(folders), 5, "Should report multiple organized folders")


class TestArcadeOrganizerFullDistribution(_BaseArcadeOrganizerRepoTest, unittest.TestCase):
    """System test using ALL real MRAs from Distribution_MiSTer."""
    REPO_URL = DISTRIBUTION_MISTER_REPO
    TEMP_PREFIX = 'ao_full_dist_test_'
    MIN_SOURCE_MRAS = 1000
    MIN_ORGANIZED_PATHS = 15000


class TestArcadeOrganizerFullJtcores(_BaseArcadeOrganizerRepoTest, unittest.TestCase):
    """System test using ALL real MRAs from jotego/jtcores_mister."""
    REPO_URL = JTCORES_MISTER_REPO
    TEMP_PREFIX = 'ao_full_jtcores_test_'
    MIN_SOURCE_MRAS = 1000
    MIN_ORGANIZED_PATHS = 15000
