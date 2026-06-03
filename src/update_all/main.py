#!/usr/bin/env python3
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

import traceback
import sys
import locale
import os

from update_all.config import EnvDict
from update_all.constants import DEFAULT_CURL_SSL_OPTIONS, \
    KENV_CURL_SSL, KENV_COMMIT, KENV_LOCATION_STR, DEFAULT_LOCATION_STR, KENV_DEBUG, \
    DEFAULT_DEBUG, DEFAULT_TRANSITION_SERVICE_ONLY, KENV_TRANSITION_SERVICE_ONLY, KENV_SKIP_DOWNLOADER, \
    DEFAULT_SKIP_DOWNLOADER, KENV_PATREON_KEY_PATH, FILE_patreon_key, KENV_COMMAND, COMMAND_STANDARD, \
    KENV_TIMELINE_SHORT_PATH, FILE_timeline_short, KENV_TIMELINE_PLUS_PATH, FILE_timeline_plus, KENV_HTTP_PROXY, \
    KENV_LC_HTTP_PROXY, KENV_LC_HTTPS_PROXY, KENV_HTTPS_PROXY, KENV_MIRROR_ID, KENV_UPDATE_ALL_CHIP_ID_RESULT, \
    KENV_RETROACCOUNT_DOMAIN, DOMAIN_default_retroaccount, MEDIA_FAT, FILE_update_all_log

from update_all.logger import FileLoggerDecorator, PrintLogger
from update_all.other import GenericProvider


def main(env, args=None):
    locale.setlocale(locale.LC_CTYPE, "")
    local_repository_provider = GenericProvider()
    logger = FileLoggerDecorator(PrintLogger(), initial_logfile_path())
    # noinspection PyBroadException
    try:
        exit_code = execute_update_all(logger, local_repository_provider, env, args=args)
    except KeyboardInterrupt as _:
        logger.print('\nExecution aborted by the user.')
        return 1
    except Exception as _:
        logger.print(traceback.format_exc())
        exit_code = 1
    finally:
        logger.finalize()

    return exit_code


def initial_logfile_path():
    media_fat_logfile_dir = os.path.join(MEDIA_FAT, os.path.dirname(FILE_update_all_log))
    media_fat_logfile_path = os.path.join(MEDIA_FAT, FILE_update_all_log)
    return media_fat_logfile_path if os.path.isdir(media_fat_logfile_dir) else os.path.basename(FILE_update_all_log)


def execute_update_all(logger: FileLoggerDecorator, local_repository_provider, env, args=None):
    args = sys.argv if args is None else args
    if len(args) > 1 and args[1] == '--chip-id-linker':
        from update_all.chip_id_linker import run_chip_id_linker_command
        return run_chip_id_linker_command(logger, args[2:])

    from update_all.update_all_service import UpdateAllServiceFactory, UpdateAllServicePass
    if len(args) > 1 and args[1] == '--continue':
        full_run_param = UpdateAllServicePass.Continue
    elif len(args) > 1 and args[1] == '--no-continue':
        full_run_param = UpdateAllServicePass.NewRunNonStop
    else:
        full_run_param = UpdateAllServicePass.NewRun

    factory = UpdateAllServiceFactory(logger, local_repository_provider=local_repository_provider)
    return factory.create(env).full_run(full_run_param)


def read_env(default_commit: str, real_start_time: float) -> EnvDict:
    return {
        KENV_CURL_SSL: os.getenv(KENV_CURL_SSL, DEFAULT_CURL_SSL_OPTIONS),
        KENV_COMMIT: os.getenv(KENV_COMMIT, default_commit),
        KENV_LOCATION_STR: os.getenv(KENV_LOCATION_STR, DEFAULT_LOCATION_STR),
        KENV_DEBUG: os.getenv(KENV_DEBUG, DEFAULT_DEBUG),
        KENV_TRANSITION_SERVICE_ONLY: os.getenv(KENV_TRANSITION_SERVICE_ONLY, DEFAULT_TRANSITION_SERVICE_ONLY),
        KENV_SKIP_DOWNLOADER: os.getenv(KENV_SKIP_DOWNLOADER, DEFAULT_SKIP_DOWNLOADER),
        KENV_PATREON_KEY_PATH: os.getenv(KENV_PATREON_KEY_PATH, FILE_patreon_key),
        KENV_COMMAND: os.getenv(KENV_COMMAND, COMMAND_STANDARD),
        KENV_UPDATE_ALL_CHIP_ID_RESULT: os.getenv(KENV_UPDATE_ALL_CHIP_ID_RESULT, ''),
        KENV_TIMELINE_SHORT_PATH: os.getenv(KENV_TIMELINE_SHORT_PATH, FILE_timeline_short),
        KENV_TIMELINE_PLUS_PATH: os.getenv(KENV_TIMELINE_PLUS_PATH, FILE_timeline_plus),
        KENV_HTTP_PROXY: os.getenv(KENV_HTTP_PROXY) or os.getenv(KENV_LC_HTTP_PROXY),
        KENV_HTTPS_PROXY: os.getenv(KENV_HTTPS_PROXY) or os.getenv(KENV_LC_HTTPS_PROXY),
        KENV_MIRROR_ID: os.getenv(KENV_MIRROR_ID, ''),
        KENV_RETROACCOUNT_DOMAIN: os.getenv(KENV_RETROACCOUNT_DOMAIN, DOMAIN_default_retroaccount),
        'real_start_time': real_start_time
    }
