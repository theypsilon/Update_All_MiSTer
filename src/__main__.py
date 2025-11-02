#!/usr/bin/env python3
# Copyright (c) 2022-2024 José Manuel Barroso Galindo <theypsilon@gmail.com>

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
from update_all.constants import DEFAULT_CURL_SSL_OPTIONS, \
    DEFAULT_COMMIT, KENV_CURL_SSL, KENV_COMMIT, KENV_LOCATION_STR, DEFAULT_LOCATION_STR, KENV_DEBUG, \
    DEFAULT_DEBUG, DEFAULT_TRANSITION_SERVICE_ONLY, KENV_TRANSITION_SERVICE_ONLY, KENV_LOCAL_TEST_RUN, \
    DEFAULT_LOCAL_TEST_RUN, KENV_PATREON_KEY_PATH, FILE_patreon_key, KENV_COMMAND, COMMAND_STANDARD, \
    KENV_TIMELINE_SHORT_PATH, FILE_timeline_short, KENV_TIMELINE_PLUS_PATH, FILE_timeline_plus, KENV_HTTP_PROXY, \
    KENV_LC_HTTP_PROXY, KENV_LC_HTTPS_PROXY, KENV_HTTPS_PROXY

try:
    from update_all.main import main
except (ImportError, SyntaxError) as e:
    print(e)
    print('\n')
    print('Warning! Your OS version seems to be older than September 2021!')
    print('Please upgrade your OS before running Update All')
    print('More info at https://github.com/MiSTer-devel/mr-fusion')
    print()
    exit(1)

try:
    from commit import default_commit  # type: ignore[import-not-found]
except ImportError as e:
    default_commit = DEFAULT_COMMIT  # type: ignore[assignment]

if __name__ == '__main__':
    exit_code = main({
        KENV_CURL_SSL: os.getenv(KENV_CURL_SSL, DEFAULT_CURL_SSL_OPTIONS),
        KENV_COMMIT: os.getenv(KENV_COMMIT, default_commit),
        KENV_LOCATION_STR: os.getenv(KENV_LOCATION_STR, DEFAULT_LOCATION_STR),
        KENV_DEBUG: os.getenv(KENV_DEBUG, DEFAULT_DEBUG),
        KENV_TRANSITION_SERVICE_ONLY: os.getenv(KENV_TRANSITION_SERVICE_ONLY, DEFAULT_TRANSITION_SERVICE_ONLY),
        KENV_LOCAL_TEST_RUN: os.getenv(KENV_LOCAL_TEST_RUN, DEFAULT_LOCAL_TEST_RUN),
        KENV_PATREON_KEY_PATH: os.getenv(KENV_PATREON_KEY_PATH, FILE_patreon_key),
        KENV_COMMAND: os.getenv(KENV_COMMAND, COMMAND_STANDARD),
        KENV_TIMELINE_SHORT_PATH: os.getenv(KENV_TIMELINE_SHORT_PATH, FILE_timeline_short),
        KENV_TIMELINE_PLUS_PATH: os.getenv(KENV_TIMELINE_PLUS_PATH, FILE_timeline_plus),
        KENV_HTTP_PROXY: os.getenv(KENV_HTTP_PROXY) or os.getenv(KENV_LC_HTTP_PROXY),
        KENV_HTTPS_PROXY: os.getenv(KENV_HTTPS_PROXY) or os.getenv(KENV_LC_HTTPS_PROXY)
    })

    exit(exit_code)
