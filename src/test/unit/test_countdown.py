#!/usr/bin/env python3

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

from update_all.countdown import _countdown_left_padding, _countdown_status_line
from update_all.logger import FileLoggerDecorator, PrintLogger
from update_all.other import GenericProvider


class TestCountdown(unittest.TestCase):
    def test_countdown_status_line___adds_clear_carriage_return_and_left_padding(self):
        self.assertEqual('\033[2K\r  Starting in 15 seconds.', _countdown_status_line('Starting in 15 seconds.', 2))

    def test_countdown_left_padding___unwraps_decorated_print_logger(self):
        inner_logger = PrintLogger()
        inner_logger._overscan = 4
        logger = FileLoggerDecorator(inner_logger, GenericProvider())

        self.assertEqual(4, _countdown_left_padding(logger))
