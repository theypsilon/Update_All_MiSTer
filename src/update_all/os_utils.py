#!/usr/bin/env python3
# Copyright (c) 2022-2025 José Manuel Barroso Galindo <theypsilon@gmail.com>
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
try:
    import select
    import fcntl
except ImportError:
    pass
import os
from abc import ABC
from typing import Optional, Tuple

from update_all.analogue_pocket.http_gateway import fetch
from update_all.config import Config
from update_all.other import GenericProvider
from update_all.logger import Logger
import ssl


class OsUtils(ABC):
    def sync(self) -> None:
        """send sync signal to the OS"""

    def reboot(self) -> None:
        """send reboot signal to the OS"""

    def execute_process(self, launcher, env, quiet: bool = False) -> int:
        """execute launcher process with subprocess and the given env. output gets redirected to stdout"""

    def read_command_output(self, cmd, env) -> [int, str]:
        """executes command with the given env and returns output and success code"""

    def sleep(self, seconds) -> None:
        """waits given seconds"""

    def download(self, url) -> Optional[bytes]:
        """downloads given url and returns content as string"""

    def make_executable(self, file_path: str) -> None:
        """makes the given file executable"""


class LinuxOsUtils(OsUtils):
    def __init__(self, config_provider: GenericProvider[Config], logger: Logger):
        self._config_provider = config_provider
        self._logger = logger

    def sync(self) -> None:
        subprocess.run(['sync'], shell=False, stderr=subprocess.STDOUT)

    def reboot(self) -> None:
        subprocess.run(['reboot', 'now'], shell=False, stderr=subprocess.STDOUT)

    def make_executable(self, file_path: str) -> None:
        subprocess.run(['chmod', '+x', file_path], check=True, stderr=subprocess.STDOUT)

    def execute_process(self, launcher, env, quiet: bool = False) -> int:
        try:
            env = {**os.environ.copy(), **env, 'PYTHONUNBUFFERED': '1'}
            self._logger.debug('Executing launcher', launcher, ' with env: ', env, ' quiet=', quiet)

            proc = subprocess.Popen(
                [launcher],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                bufsize=1,
                text=True
            )

            for pipe in (proc.stdout, proc.stderr):
                fd = pipe.fileno()
                flags = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

            while True:
                exit_code = proc.poll()
                if exit_code is not None:
                    break

                rlist, _, _ = select.select([proc.stdout, proc.stderr], [], [], 0.25)
                for pipe in rlist:
                    try:
                        output = pipe.read(4096)
                        if output:
                            if quiet: output = '.'
                            self._logger.print(output, end='', flush=True)
                    except BlockingIOError:
                        continue

            for pipe in [proc.stdout, proc.stderr]:
                for line in pipe.readlines():
                    if quiet: line = '.'
                    self._logger.print(line, end='', flush=True)

            return proc.returncode
        except Exception as e:
            self._logger.print(f"ERROR: Launcher {launcher} failed!")
            self._logger.debug(e)
            return -1

    def read_command_output(self, cmd, env) -> [int, str]:
        proc = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return proc.returncode, proc.stdout.decode()

    def sleep(self, seconds) -> None:
        time.sleep(seconds)

    def download(self, url) -> Optional[bytes]:
        ssl_ctx, ssl_err = context_from_curl_ssl(self._config_provider.get().curl_ssl)
        if ssl_err is not None:
            self._logger.debug(ssl_err)
            self._logger.print('WARNING! Ignoring SSL parameters...')
            return None

        try:
            status, data = fetch(url, ssl_ctx=ssl_ctx, timeout=180, config=self._config_provider.get().http_config)
            if status != 200:
                self._logger.print(f'ERROR! Bad http status!: {status}')
                return None

            return data
        except Exception as e:
            self._logger.debug(e)
            self._logger.print(f"An error occurred, please try again later.")
            return None


def context_from_curl_ssl(curl_ssl) -> Tuple[ssl.SSLContext, Optional[Exception]]:
    try:
        context = ssl.create_default_context()

        if curl_ssl.startswith('--cacert '):
            cacert_file = curl_ssl[len('--cacert '):]
            context.load_verify_locations(cacert_file)
        elif curl_ssl == '--insecure':
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        return context, None
    except Exception as e:
        return ssl.create_default_context(), e
