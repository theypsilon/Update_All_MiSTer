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

from update_all.local_store import LocalStore


class TestLocalStore(unittest.TestCase):

    def test_generic_set___when_field_is_missing___adds_field_and_marks_store_dirty(self):
        store = LocalStore({})

        store.generic_set('some_field', False)

        self.assertEqual(False, store.unwrap_props()['some_field'])
        self.assertEqual(['some_field'], store.changed_fields())

    def test_set_allow_retroaccount_jt_beta_auto_enable___updates_field_and_marks_store_dirty(self):
        store = LocalStore({'allow_retroaccount_jt_beta_auto_enable': True})

        store.set_allow_retroaccount_jt_beta_auto_enable(False)

        self.assertEqual(False, store.get_allow_retroaccount_jt_beta_auto_enable())
        self.assertEqual(['allow_retroaccount_jt_beta_auto_enable'], store.changed_fields())
