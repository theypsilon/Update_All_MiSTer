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
import datetime
import tempfile
import sys
import time
from abc import ABC, abstractmethod


class Logger(ABC):
    @abstractmethod
    def configure(self, _config):
        """makes logs more verbose"""

    @abstractmethod
    def print(self, *args, sep='', end='\n', file=sys.stdout, flush=True):
        """print always"""

    @abstractmethod
    def debug(self, *args, sep='', end='\n', flush=True):
        """print only to debug target"""

    @abstractmethod
    def bench(self, label):
        """print only to debug target"""

    def finalize(self):
        """to be called at the very end, should not call any method after this one"""


class PrintLogger(Logger):
    def __init__(self):
        self._verbose_mode = False
        self._start_time = None

    def set_local_repository(self, local_repository):
        pass

    def configure(self, config):
        if config.verbose:
            self._verbose_mode = True
            self._start_time = config.start_time

    def print(self, *args, sep='', end='\n', file=sys.stdout, flush=True):
        self._do_print(*args, sep=sep, end=end, file=file, flush=flush)

    def debug(self, *args, sep='', end='\n', flush=True):
        if self._verbose_mode:
            self._do_print(*args, sep=sep, end=end, file=sys.stdout, flush=flush)

    def bench(self, label):
        if self._start_time is not None:
            self._do_print('%s| %s' % (str(datetime.timedelta(seconds=time.time() - self._start_time))[0:-4], label), sep='', end='\n', file=sys.stdout, flush=True)

    def finalize(self):
        pass

    @staticmethod
    def _do_print(*args, sep, end, file, flush):
        try:
            print(*args, sep=sep, end=end, file=file, flush=flush)
        except UnicodeEncodeError:
            pack = []
            for a in args:
                pack.append(a.encode('utf8', 'surrogateescape'))
            print(*pack, sep=sep, end=end, file=file, flush=flush)
        except BaseException as error:
            print('An unknown exception occurred during logging: %s' % str(error))


class FileLoggerDecorator(Logger):
    def __init__(self, decorated_logger, local_repository_provider):
        self._decorated_logger = decorated_logger
        self._logfile = tempfile.NamedTemporaryFile('w', delete=False)
        self._local_repository_provider = local_repository_provider

    def configure(self, config):
        self._decorated_logger.configure(config)

    def finalize(self):
        self._decorated_logger.finalize()
        if self._logfile is None:
            return

        self._logfile.close()
        self._local_repository_provider.get().save_log_from_tmp(self._logfile.name)
        self._logfile = None

    def print(self, *args, sep='', end='\n', file=sys.stdout, flush=True):
        self._decorated_logger.print(*args, sep=sep, end=end, file=file, flush=flush)
        self._do_print_in_file(*args, sep=sep, end=end, flush=flush)

    def debug(self, *args, sep='', end='\n', flush=True):
        self._decorated_logger.debug(*args, sep=sep, end=end, flush=flush)
        self._do_print_in_file(*args, sep=sep, end=end, flush=flush)

    def bench(self, label):
        self._decorated_logger.bench(label)

    def _do_print_in_file(self, *args, sep, end, flush):
        if self._logfile is not None:
            print(*args, sep=sep, end=end, file=self._logfile, flush=flush)


class DebugOnlyLoggerDecorator(Logger):
    def __init__(self, decorated_logger):
        self._decorated_logger = decorated_logger

    def configure(self, config):
        self._decorated_logger.configure(config)

    def print(self, *args, sep='', end='\n', file=sys.stdout, flush=True):
        """Calls debug instead of print"""
        self._decorated_logger.debug(*args, sep=sep, end=end, flush=flush)

    def debug(self, *args, sep='', end='\n', flush=True):
        self._decorated_logger.debug(*args, sep=sep, end=end, flush=flush)

    def bench(self, label):
        self._decorated_logger.bench(label)

    def finalize(self):
        self._decorated_logger.finalize()
