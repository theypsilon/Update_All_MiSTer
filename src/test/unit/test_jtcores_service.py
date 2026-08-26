# Copyright (c) 2022-2026 José Manuel Barroso Galindo <theypsilon@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# You can download the latest version of this tool from:
# https://github.com/theypsilon/Update_All_MiSTer
import unittest

from test.update_all_service_tester import default_databases, local_store
from update_all.config import Config
from update_all.databases import ALL_DB_IDS
from update_all.jtcores_service import JtcoresService
from update_all.local_store import LocalStore
from update_all.other import GenericProvider


class TestJtcoresService(unittest.TestCase):
    def test_enable_private_beta_cores_from_retroaccount_if_allowed___when_allowed_and_jtcores_enabled___enables_and_writes_downloader_ini(self):
        sut, config, _store, ini_repository = tester()

        sut.enable_private_beta_cores_from_retroaccount_if_allowed()

        self.assertTrue(config.download_beta_cores)
        self.assertEqual([True], ini_repository.write_calls)

    def test_enable_private_beta_cores_from_retroaccount_if_allowed___when_user_chose_private_releases_themselves___does_nothing(self):
        store = local_store()
        store.set_allow_retroaccount_jt_beta_auto_enable(False)
        store.mark_as_cleaned()
        sut, config, _store, ini_repository = tester(store=store)

        sut.enable_private_beta_cores_from_retroaccount_if_allowed()

        self.assertFalse(config.download_beta_cores)
        self.assertEqual([], ini_repository.write_calls)

    def test_enable_private_beta_cores_from_retroaccount_if_allowed___when_jtcores_disabled___does_nothing(self):
        sut, config, _store, ini_repository = tester(config=Config(databases={ALL_DB_IDS['UPDATE_ALL_MISTER']}))

        sut.enable_private_beta_cores_from_retroaccount_if_allowed()

        self.assertFalse(config.download_beta_cores)
        self.assertEqual([], ini_repository.write_calls)

    def test_enable_private_beta_cores_from_retroaccount_if_allowed___when_private_releases_already_enabled___does_not_write_downloader_ini(self):
        sut, config, _store, ini_repository = tester(config=Config(databases=default_databases(), download_beta_cores=True))

        sut.enable_private_beta_cores_from_retroaccount_if_allowed()

        self.assertTrue(config.download_beta_cores)
        self.assertEqual([], ini_repository.write_calls)


def tester(config: Config = None, store: LocalStore = None):
    config = config or Config(databases=default_databases(), download_beta_cores=False)
    store = store or local_store()
    config_provider = GenericProvider[Config]()
    config_provider.initialize(config)
    store_provider = GenericProvider[LocalStore]()
    store_provider.initialize(store)
    ini_repository = _IniRepositoryStub()
    return JtcoresService(config_provider, store_provider, ini_repository), config, store, ini_repository


class _IniRepositoryStub:
    def __init__(self):
        self.write_calls = []

    def write_downloader_ini(self, config: Config):
        self.write_calls.append(config.download_beta_cores)
