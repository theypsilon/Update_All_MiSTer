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

from test.retroachievements_service_tester import RetroAchievementsServiceTester
from test.spy_os_utils import SpyOsUtils
from update_all.constants import FILE_MiSTer_ini
from update_all.retroachievements_service import RETROACHIEVEMENTS_CFG_PATH, RETROACHIEVEMENTS_CFG_URL


class TestRetroAchievementsService(unittest.TestCase):
    def test_prepare_enable___with_valid_password___enables_without_installing_cfg(self):
        cfg_contents = 'username=user\npassword=secret\n'
        os_utils = _DownloadOsUtils(b'username=\npassword=\n')
        sut = RetroAchievementsServiceTester(
            files={RETROACHIEVEMENTS_CFG_PATH: {'content': cfg_contents}},
            os_utils=os_utils,
        )

        self.assertEqual('ok', sut.prepare_enable())

        self.assertEqual([], os_utils.calls_to_download)
        self.assertEqual(cfg_contents, sut.file_system.read_file_contents(RETROACHIEVEMENTS_CFG_PATH))

    def test_prepare_enable___with_missing_cfg___installs_cfg(self):
        os_utils = _DownloadOsUtils(b'username=\npassword=\n')
        sut = RetroAchievementsServiceTester(os_utils=os_utils)

        self.assertEqual('installed', sut.prepare_enable())

        self.assertEqual([RETROACHIEVEMENTS_CFG_URL], os_utils.calls_to_download)
        self.assertEqual('username=\npassword=\n', sut.file_system.read_file_contents(RETROACHIEVEMENTS_CFG_PATH))

    def test_prepare_enable___with_missing_password_field___installs_cfg(self):
        os_utils = _DownloadOsUtils(b'username=\npassword=\n')
        sut = RetroAchievementsServiceTester(
            files={RETROACHIEVEMENTS_CFG_PATH: {'content': 'username=user\nshow_progress_popups=1\n'}},
            os_utils=os_utils,
        )

        self.assertEqual('installed', sut.prepare_enable())

        self.assertEqual([RETROACHIEVEMENTS_CFG_URL], os_utils.calls_to_download)
        self.assertEqual('username=\npassword=\n', sut.file_system.read_file_contents(RETROACHIEVEMENTS_CFG_PATH))

    def test_prepare_enable___with_empty_password___reminds_user_without_installing_cfg(self):
        cfg_contents = 'username=user\npassword=\nshow_progress_popups=1\n'
        os_utils = _DownloadOsUtils(b'username=\npassword=\n')
        sut = RetroAchievementsServiceTester(
            files={RETROACHIEVEMENTS_CFG_PATH: {'content': cfg_contents}},
            os_utils=os_utils,
        )

        self.assertEqual('missing_credentials', sut.prepare_enable())

        self.assertEqual([], os_utils.calls_to_download)
        self.assertEqual(cfg_contents, sut.file_system.read_file_contents(RETROACHIEVEMENTS_CFG_PATH))

    def test_set_mister_ini_active_true___adds_ra_mister_ini_block_at_end(self):
        mister_ini = '[mister]\nfoo=bar\n\n[menu]\nvideo_mode=8\n'
        sut = RetroAchievementsServiceTester(files={
            FILE_MiSTer_ini: {'content': mister_ini},
        })

        sut.set_mister_ini_active(True)

        self.assertEqual(
            '[mister]\nfoo=bar\n\n[menu]\nvideo_mode=8\n\n[RA_*]\nmain=MiSTer_RA\n',
            sut.file_system.read_file_contents(FILE_MiSTer_ini),
        )

    def test_set_mister_ini_active_true___without_mister_ini___creates_ra_mister_ini_block(self):
        sut = RetroAchievementsServiceTester()

        sut.set_mister_ini_active(True)

        self.assertEqual('[RA_*]\nmain=MiSTer_RA\n', sut.file_system.read_file_contents(FILE_MiSTer_ini))

    def test_set_mister_ini_active_true___with_existing_ra_block___does_not_rewrite_mister_ini(self):
        mister_ini = '[mister]\nfoo=bar\n\n[RA_*]\nmain=MiSTer_RA\n'
        sut = RetroAchievementsServiceTester(files={
            FILE_MiSTer_ini: {'content': mister_ini},
        })

        sut.set_mister_ini_active(True)

        mister_ini_writes = [
            record for record in sut.file_system.write_records
            if record['scope'] == 'write_file_contents'
            and record['data'][0] == '/media/fat/.mister.ini.new'
        ]
        self.assertEqual([], mister_ini_writes)
        self.assertEqual(mister_ini, sut.file_system.read_file_contents(FILE_MiSTer_ini))

    def test_would_change_mister_ini_active_true___when_mister_ini_is_missing___returns_true_without_writing(self):
        sut = RetroAchievementsServiceTester()

        self.assertTrue(sut.would_change_mister_ini_active(True))

        self.assertFalse(sut.file_system.is_file(FILE_MiSTer_ini))

    def test_would_change_mister_ini_active_true___when_ra_block_exists___returns_false(self):
        sut = RetroAchievementsServiceTester(files={
            FILE_MiSTer_ini: {'content': '[RA_*]\nmain=MiSTer_RA\n'},
        })

        self.assertFalse(sut.would_change_mister_ini_active(True))

    def test_would_change_mister_ini_active_false___when_ra_block_exists___returns_true_without_writing(self):
        original = '[mister]\nfoo=bar\n\n[RA_*]\nmain=MiSTer_RA\n'
        sut = RetroAchievementsServiceTester(files={
            FILE_MiSTer_ini: {'content': original},
        })

        self.assertTrue(sut.would_change_mister_ini_active(False))

        self.assertEqual(original, sut.file_system.read_file_contents(FILE_MiSTer_ini))

    def test_would_change_mister_ini_active_false___when_ra_block_is_absent___returns_false(self):
        sut = RetroAchievementsServiceTester(files={
            FILE_MiSTer_ini: {'content': '[mister]\nfoo=bar\n'},
        })

        self.assertFalse(sut.would_change_mister_ini_active(False))

    def test_set_mister_ini_active_false___removes_ra_mister_ini_block(self):
        sut = RetroAchievementsServiceTester(files={
            FILE_MiSTer_ini: {'content': '[mister]\nfoo=bar\n\n[RA_*]\nmain=MiSTer_RA\n'},
        })

        sut.set_mister_ini_active(False)

        self.assertEqual('[mister]\nfoo=bar\n', sut.file_system.read_file_contents(FILE_MiSTer_ini))

    def test_set_mister_ini_active_false___without_mister_ini___does_not_fail(self):
        sut = RetroAchievementsServiceTester()

        sut.set_mister_ini_active(False)

        self.assertFalse(sut.file_system.is_file(FILE_MiSTer_ini))


class _DownloadOsUtils(SpyOsUtils):
    def __init__(self, content):
        super().__init__()
        self._content = content

    def download(self, url):
        self.calls_to_download.append(url)
        return self._content
