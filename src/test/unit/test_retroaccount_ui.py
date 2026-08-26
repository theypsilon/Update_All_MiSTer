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

from update_all.retroaccount_ui import DeviceLogin
from update_all.ui_model_utilities import Key


class TestDeviceLogin(unittest.TestCase):
    def test_show_timeout_dialog___uses_blocking_input_and_restores_default_timeout(self):
        drawer = _DrawerStub([Key.ENTER])
        renderer = _RendererStub()
        sut = DeviceLogin(drawer, renderer, _RetroAccountStub(), {})

        result = sut._show_timeout_dialog('ABCD-1234')

        self.assertEqual('_new_code', result)
        self.assertEqual([-1, 300], renderer.timeout_calls)
        self.assertEqual(1, drawer.paint_calls)


class _DrawerStub:
    def __init__(self, keys):
        self._keys = list(keys)
        self.paint_calls = 0

    def clear(self):
        pass

    def start(self, data):
        pass

    def add_text_line(self, text):
        pass

    def add_action(self, action, is_selected=False):
        pass

    def paint(self):
        self.paint_calls += 1
        return self._keys.pop(0)


class _RendererStub:
    def __init__(self):
        self.timeout_calls = []

    def render_requesting(self, header):
        pass

    def render_poll_screen(self, header, user_code, verification_uri, qr_lines, dots, remaining):
        pass

    def render_cancel_dialog(self, header, user_code, options, selected):
        pass

    def set_key_timeout(self, timeout_ms):
        self.timeout_calls.append(timeout_ms)

    def read_key(self):
        return Key.NONE

    def flush_input(self):
        pass


class _RetroAccountStub:
    @property
    def server_url(self):
        return 'https://example.com'

    def request_device_code(self):
        return None

    def get_existing_device_id(self):
        return None

    def poll_for_token(self, device_code, device_id=None):
        return None

    def save_login_credentials(self, credentials):
        return True
