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

from update_all.migrations import migration_v7, migration_v8, migration_v9, migration_v10, migration_v11


class TestMigrations(unittest.TestCase):

    def test_migration_v7___adds_manuals_selector(self):
        local_store = {}

        migration_v7(local_store)

        self.assertEqual(False, local_store['ajgowans_manuals_dbs_general_selector'])

    def test_migration_v8___adds_zaparoo_transition_state(self):
        local_store = {}

        migration_v8(local_store)

        self.assertEqual([], local_store['introduced_related_database_ids'])
        self.assertEqual(False, local_store['zaparoo_frontend_default'])

    def test_migration_v9___with_enabled_zaparoo_frontend_default___creates_zaparoo_frontend_active(self):
        local_store = {'zaparoo_frontend_default': True}

        migration_v9(local_store)

        self.assertEqual(True, local_store['zaparoo_frontend_active'])
        self.assertNotIn('zaparoo_frontend_default', local_store)

    def test_migration_v9___with_disabled_zaparoo_frontend_default___removes_zaparoo_frontend_default_without_creating_active(self):
        local_store = {'zaparoo_frontend_default': False}

        migration_v9(local_store)

        self.assertNotIn('zaparoo_frontend_active', local_store)
        self.assertNotIn('zaparoo_frontend_default', local_store)

    def test_migration_v10___with_zaparoo_frontend_active___removes_zaparoo_frontend_active(self):
        local_store = {'zaparoo_frontend_active': True}

        migration_v10(local_store)

        self.assertNotIn('zaparoo_frontend_active', local_store)
        self.assertNotIn('_dirty', local_store)

    def test_migration_v10___without_zaparoo_frontend_active___does_nothing(self):
        local_store = {}

        migration_v10(local_store)

        self.assertNotIn('zaparoo_frontend_active', local_store)
        self.assertNotIn('_dirty', local_store)

    def test_migration_v11___adds_retroaccount_jt_beta_auto_enable_allowed_without_dirtying_store(self):
        local_store = {}

        migration_v11(local_store)

        self.assertEqual(True, local_store['allow_retroaccount_jt_beta_auto_enable'])
        self.assertNotIn('_dirty', local_store)

    def test_migration_v11___sets_retroaccount_jt_beta_auto_enable_allowed(self):
        local_store = {'allow_retroaccount_jt_beta_auto_enable': False}

        migration_v11(local_store)

        self.assertEqual(True, local_store['allow_retroaccount_jt_beta_auto_enable'])
