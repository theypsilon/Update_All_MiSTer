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
