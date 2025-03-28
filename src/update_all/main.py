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

import traceback
import sys
from update_all.local_repository import LocalRepository
from update_all.logger import FileLoggerDecorator, PrintLogger
from update_all.other import GenericProvider
from update_all.update_all_service import UpdateAllServiceFactory, UpdateAllServicePass


def main(env):
    local_repository_provider = GenericProvider[LocalRepository]()
    logger = FileLoggerDecorator(PrintLogger(), local_repository_provider)
    # noinspection PyBroadException
    try:
        exit_code = execute_update_all(
            UpdateAllServiceFactory(logger, local_repository_provider=local_repository_provider),
            env
        )
    except KeyboardInterrupt as _:
        logger.print('\nExecution aborted by the user.')
        return 1
    except Exception as _:
        logger.print(traceback.format_exc())
        exit_code = 1

    logger.finalize()
    return exit_code


def execute_update_all(factory, env):
    return factory.create(env).full_run(pass_parameter(sys.argv))

def pass_parameter(args: list[str]) -> UpdateAllServicePass:
    if len(args) > 1 and args[1] == '--continue':
        return UpdateAllServicePass.Continue
    elif len(args) > 1 and args[1] == '--no-continue':
        return UpdateAllServicePass.NewRunNonStop
    else:
        return UpdateAllServicePass.NewRun
