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

import os
import subprocess
import platform
import hashlib
from enum import unique, Enum
from functools import cache

from update_all.config import Config
from update_all.logger import Logger
from update_all.other import GenericProvider


@unique
class EncryptionResult(Enum):
    Success = 0
    MissingKey = 1
    MissingInput = 2
    InvalidKey = 3
    ImproperEnvironment = 4
    OtherError = 5


class Encryption:
    def __init__(self, logger: Logger, config_provider: GenericProvider[Config]):
        self._logger = logger
        self._config_provider = config_provider
        self._check_env = True

    def skip_environment_check(self):
        self._check_env = False

    @cache
    def validate_key(self) -> EncryptionResult:
        result = self._common_checks()
        if result != EncryptionResult.Success:
            return result

        try:
            with open(self._config_provider.get().patreon_key_path, 'rb') as key_file:
                fingerprint_result = hashlib.md5(key_file.read()).hexdigest()
        except Exception as e:
            self._print_invalid_patreon_key_message()
            self._logger.debug(f"Encryption: Patreon Key validation failed with error")
            self._logger.debug(e)
            return EncryptionResult.InvalidKey

        if fingerprint_result != _EXPECTED_FINGERPRINT:
            self._print_invalid_patreon_key_message()
            self._logger.debug(f"Encryption: Expected '{_EXPECTED_FINGERPRINT}', got '{fingerprint_result}'.")
            return EncryptionResult.InvalidKey

        return EncryptionResult.Success

    def decrypt_file(self, input_path: str, output_path: str) -> EncryptionResult:
        result = self._common_checks()
        if result != EncryptionResult.Success:
            return result

        if not os.path.isfile(input_path):
            self._logger.debug(f"Encryption: Input file '{input_path}' does not exist.")
            return EncryptionResult.MissingInput

        try:
            subprocess.run([
                'openssl',
                "enc", "-aes-256-cbc", "-d",
                "-in", input_path,
                "-out", output_path,
                "-kfile", self._config_provider.get().patreon_key_path,
                "-nosalt", "-iter", "1"
            ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except subprocess.CalledProcessError as e:
            self._print_invalid_patreon_key_message()
            self._logger.debug(e)
            self._logger.debug(f"Encryption: stderr -> {e.stderr}")
            return EncryptionResult.InvalidKey
        except FileNotFoundError as e:
            self._logger.debug("Encryption: OpenSSL not found in system PATH.")
            self._logger.debug(e)
            return EncryptionResult.OtherError
        except Exception as e:
            self._logger.debug(f"Encryption: Unexpected error running OpenSSL.")
            self._logger.debug(e)
            return EncryptionResult.OtherError

        return EncryptionResult.Success

    @cache
    def _common_checks(self) -> EncryptionResult:
        if self._check_env and (platform.system() != 'Linux' or  not os.path.isfile('/MiSTer.version')):
            self._logger.debug("Encryption: Not running on MiSTer, abort.")
            return EncryptionResult.ImproperEnvironment

        if not os.path.isfile(self._config_provider.get().patreon_key_path):
            self._logger.debug(f"Encryption: Patreon Key file '{self._config_provider.get().patreon_key_path}' does not exist.")
            return EncryptionResult.MissingKey

        if os.path.getsize(self._config_provider.get().patreon_key_path) != 32:
            self._print_invalid_patreon_key_message()
            self._logger.debug(f"Encryption: Patreon Key file '{self._config_provider.get().patreon_key_path}' has invalid size.")
            return EncryptionResult.InvalidKey

        return EncryptionResult.Success

    def _print_invalid_patreon_key_message(self):
        self._logger.print(f"ERROR: Patreon Key validation failed, did you get the latest one?")

_EXPECTED_FINGERPRINT = "d384da73fcfb4a7c5b133b346f5d338e"
