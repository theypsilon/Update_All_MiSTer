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


class _DownloadOsUtils(SpyOsUtils):
    def __init__(self, content):
        super().__init__()
        self._content = content

    def download(self, url):
        self.calls_to_download.append(url)
        return self._content
