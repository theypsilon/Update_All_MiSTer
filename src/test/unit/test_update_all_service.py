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

from update_all.config import Config
from update_all.other import TerminalSize, OverscanDim
from update_all.update_all_service import calculate_supporter_shoutout, calculate_outro_summary, calculate_success_summary, calculate_reading_sections_summary


class TestUpdateAllService(unittest.TestCase):
    def test_calculate_supporter_shoutout___selects_tier_from_usable_width(self):
        supporter_name = 'Patron TesterXX'

        cases = [
            (
                Config(term_size=TerminalSize(columns=120, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                "Today's shoutout is for Patron TesterXX! - Join us at patreon.com/theypsilon",
            ),
            (
                Config(term_size=TerminalSize(columns=70, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                'Shoutout to Patron TesterXX! patreon.com/theypsilon',
            ),
            (
                Config(term_size=TerminalSize(columns=45, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                'Thanks Patron TesterXX! patreon.com/theypsilon',
            ),
        ]

        for config, expected in cases:
            with self.subTest(config=config, expected=expected):
                self.assertEqual(expected, calculate_supporter_shoutout(config, supporter_name))

    def test_calculate_outro_summary___selects_tier_from_usable_width(self):
        timestamp = '2026-03-10 19:34:04'
        run_time = '00:01.17'
        cases = [
            (
                Config(commit='unknown', term_size=TerminalSize(columns=120, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                'Update All 2.5 (unk) by theypsilon. Run time: 00:01.17s at 2026-03-10 19:34:04',
            ),
            (
                Config(commit='unknown', term_size=TerminalSize(columns=80, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                'Update All 2.5 by theypsilon 00:01.17s 2026-03-10 19:34:04',
            ),
            (
                Config(commit='unknown', term_size=TerminalSize(columns=56, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                'Update All 2.5: 00:01.17s 2026-03-10 19:34:04',
            ),
            (
                Config(commit='unknown', term_size=TerminalSize(columns=28, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                'Update All 2.5: 00:01.17s',
            ),
        ]

        for config, expected in cases:
            with self.subTest(config=config, expected=expected):
                self.assertEqual(expected, calculate_outro_summary(config, run_time, timestamp))

    def test_calculate_success_summary___selects_tier_from_usable_width(self):
        log_path = 'Scripts/.config/update_all/update_all.log'
        cases = [
            (
                Config(term_size=TerminalSize(columns=120, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                'Success! More details at: Scripts/.config/update_all/update_all.log',
            ),
            (
                Config(term_size=TerminalSize(columns=64, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                'Success! Log: Scripts/.config/update_all/update_all.log',
            ),
            (
                Config(term_size=TerminalSize(columns=28, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                'Success! Log saved.',
            ),
        ]

        for config, expected in cases:
            with self.subTest(config=config, expected=expected):
                self.assertEqual(expected, calculate_success_summary(config, log_path))

    def test_calculate_reading_sections_summary___omits_message_when_it_does_not_fit(self):
        downloader_ini_path = '/home/jose/workspace/Update_All_MiSTer/.local_drv/downloader.ini'
        cases = [
            (
                Config(term_size=TerminalSize(columns=120, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                f'Reading sections from {downloader_ini_path}',
            ),
            (
                Config(term_size=TerminalSize(columns=56, lines=40), overscan_dim=OverscanDim(cols=2, lines=0)),
                None,
            ),
        ]

        for config, expected in cases:
            with self.subTest(config=config, expected=expected):
                self.assertEqual(expected, calculate_reading_sections_summary(config, downloader_ini_path))
