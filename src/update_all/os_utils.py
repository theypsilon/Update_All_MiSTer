#!/usr/bin/env python3
# Copyright (c) 2022-2023 José Manuel Barroso Galindo <theypsilon@gmail.com>
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

import subprocess
import time
from abc import ABC
from typing import Optional

from update_all.config import Config
from update_all.other import GenericProvider
from update_all.logger import Logger


class OsUtils(ABC):
    def sync(self) -> None:
        """send sync signal to the OS"""

    def reboot(self) -> None:
        """send reboot signal to the OS"""

    def execute_process(self, launcher, env) -> int:
        """execute launcher process with subprocess and the given env. output gets redirected to stdout"""

    def read_command_output(self, cmd, env) -> [int, str]:
        """executes command with the given env and returns output and success code"""

    def sleep(self, seconds) -> None:
        """waits given seconds"""

    def download(self, url) -> Optional[bytes]:
        """downloads given url and returns content as string"""


class LinuxOsUtils(OsUtils):
    def __init__(self, config_provider: GenericProvider[Config], logger: Logger):
        self._config_provider = config_provider
        self._logger = logger

    def sync(self) -> None:
        subprocess.run(['sync'], shell=False, stderr=subprocess.STDOUT)

    def reboot(self) -> None:
        subprocess.run(['reboot', 'now'], shell=False, stderr=subprocess.STDOUT)

    def execute_process(self, launcher, env) -> int:
        proc = subprocess.run(['python3', launcher], env=env)
        return proc.returncode

    def read_command_output(self, cmd, env) -> [int, str]:
        proc = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return proc.returncode, proc.stdout.decode()

    def sleep(self, seconds) -> None:
        time.sleep(seconds)

    def download(self, url) -> Optional[bytes]:
        curl_ssl = self._config_provider.get().curl_ssl
        curl_command = ["curl", "-s", "-L"]
        if curl_ssl != "":
            curl_command.extend(curl_ssl.split())
        if '--retry' not in curl_ssl:
            curl_command.extend(["--retry", "3"])
        if '--connect-timeout' not in curl_ssl:
            curl_command.extend(["--connect-timeout", "30"])
        if '--max-time' not in curl_ssl:
            curl_command.extend(["--max-time", "300"])
        curl_command.append(url)
        try:
            result = subprocess.check_output(curl_command)
            return result
        except subprocess.CalledProcessError as e:
            connection_error_codes = {
                5: "Couldn't resolve proxy",
                6: "Couldn't resolve host",
                7: "Failed to connect to host",
                28: "Connection timeout",
                35: "SSL connect error",
                52: "Server didn't reply with any data",
                56: "Failure with receiving network data",
            }
            self._logger.debug(e)
            if e.returncode in connection_error_codes:
                self._logger.print(f"Connection error: {connection_error_codes[e.returncode]}")
            else:
                self._logger.print(f"An error occurred, please try again later.")
            return None
