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

import io
import unittest

from update_all.update_output import LtsvUpdateOutput, NoopUpdateOutput


class TestUpdateOutput(unittest.TestCase):
    def test_ltsv_update_output___emits_transition_event(self):
        stream = io.StringIO()
        output = LtsvUpdateOutput(stream)

        output.transition(
            'from_old_db_ids_to_new_db_ids',
            old_db_ids='old-id',
            new_db_ids='new-id'
        )

        self.assertEqual(
            'DLP1\tevent:update_transition'
            '\ttransition:from_old_db_ids_to_new_db_ids'
            '\told_db_ids:old-id'
            '\tnew_db_ids:new-id\n',
            stream.getvalue()
        )

    def test_noop_update_output___accepts_events(self):
        output = NoopUpdateOutput()

        output.transition('transition', db_ids='db')
        output.sync_started()
        output.jtbeta_updated()
        output.credentials_removed('revoked')
        output.sync_finished()


if __name__ == '__main__':
    unittest.main()
