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

from test.retroaccount_gateway_tester import RetroAccountGatewayTester
from update_all.retroaccount_gateway import SessionResult


class TestRetroAccountGateway(unittest.TestCase):
    def test_mister_sync___when_server_returns_401___returns_revoked_session(self):
        sut = RetroAccountGatewayTester(status=401)

        result, response = sut.mister_sync('device-1', 'refresh-1', None, None)

        self.assertEqual(SessionResult.REVOKED, result)
        self.assertEqual(401, response)
        self.assertEqual(1, len(sut.fetcher.calls))

    def test_mister_sync___when_server_returns_403___returns_error_session(self):
        sut = RetroAccountGatewayTester(status=403)

        result, response = sut.mister_sync('device-1', 'refresh-1', None, None)

        self.assertEqual(SessionResult.ERROR, result)
        self.assertEqual(403, response)
        self.assertEqual(1, len(sut.fetcher.calls))

    def test_mister_sync___posts_refresh_and_device_headers_to_current_sync_endpoint(self):
        sut = RetroAccountGatewayTester(status=401)

        sut.mister_sync('device-1', 'refresh-1', 'patreon-md5', 'jtbeta-md5')

        self.assertEqual([(
            'https://retroaccount.test/api/mister/sync',
            'POST',
            {
                'update_all_patreon_key_fingerprint': 'patreon-md5',
                'jtbeta_fingerprint': 'jtbeta-md5',
            },
            {'x-refresh-token': 'refresh-1', 'x-device-id': 'device-1'},
            10,
        )], sut.fetcher.calls)

    def test_put_device_hardware_id___puts_device_auth_and_hardware_id_to_current_endpoint(self):
        sut = RetroAccountGatewayTester(status=200, body=b'{"status":"attached"}')

        result = sut.put_device_hardware_id('device-1', 'refresh-1', '0123456789abcdef')

        self.assertEqual(200, result)
        self.assertEqual([(
            'https://retroaccount.test/api/mister/device/hardware-id',
            'PUT',
            {
                'hardware_id_type': 'misterfpga.fpgaid',
                'hardware_id': '0123456789abcdef',
            },
            {'x-refresh-token': 'refresh-1', 'x-device-id': 'device-1'},
            10,
        )], sut.fetcher.calls)
