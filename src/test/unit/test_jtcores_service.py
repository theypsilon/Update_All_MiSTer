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

from test.update_all_service_tester import default_databases
from update_all.config import Config
from update_all.databases import ALL_DB_IDS
from update_all.jtcores_service import JtcoresService
from update_all.other import GenericProvider


class TestJtcoresService(unittest.TestCase):
    def test_follow_retroaccount_benefit___when_auto_and_benefit_active___enables_private_releases_and_writes_downloader_ini(self):
        sut, config, ini_repository = tester()

        sut.follow_retroaccount_benefit(True)

        self.assertTrue(config.download_beta_cores)
        self.assertEqual([True], ini_repository.write_calls)

    def test_follow_retroaccount_benefit___when_auto_and_benefit_inactive___disables_private_releases_and_writes_downloader_ini(self):
        sut, config, ini_repository = tester(config=Config(databases=default_databases(), download_beta_cores=True))

        sut.follow_retroaccount_benefit(False)

        self.assertFalse(config.download_beta_cores)
        self.assertEqual([True], ini_repository.write_calls)

    def test_follow_retroaccount_benefit___when_private_releases_already_match___does_not_write_downloader_ini(self):
        sut, config, ini_repository = tester(config=Config(databases=default_databases(), download_beta_cores=True))

        sut.follow_retroaccount_benefit(True)

        self.assertTrue(config.download_beta_cores)
        self.assertEqual([], ini_repository.write_calls)

    def test_follow_retroaccount_benefit___when_user_chose_private_releases_manually___does_nothing(self):
        sut, config, ini_repository = tester(config=Config(databases=default_databases(), jtcores_private_releases_auto=False))

        sut.follow_retroaccount_benefit(True)

        self.assertFalse(config.download_beta_cores)
        self.assertEqual([], ini_repository.write_calls)

    def test_follow_retroaccount_benefit___when_jtcores_disabled___does_nothing(self):
        sut, config, ini_repository = tester(config=Config(databases={ALL_DB_IDS['UPDATE_ALL_MISTER']}))

        sut.follow_retroaccount_benefit(True)

        self.assertFalse(config.download_beta_cores)
        self.assertEqual([], ini_repository.write_calls)


def tester(config: Config = None):
    config = config or Config(databases=default_databases(), download_beta_cores=False)
    config_provider = GenericProvider[Config]()
    config_provider.initialize(config)
    ini_repository = _IniRepositoryStub()
    return JtcoresService(config_provider, ini_repository), config, ini_repository


class _IniRepositoryStub:
    def __init__(self):
        self.write_calls = []

    def write_downloader_ini(self, config: Config):
        self.write_calls.append(True)
