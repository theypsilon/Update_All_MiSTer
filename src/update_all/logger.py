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
import datetime
import tempfile
import sys
import time
import traceback
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
            self._do_print(*_transform_debug_args(args), sep=sep, end=end, file=sys.stdout, flush=flush)

    def bench(self, label):
        if self._start_time is not None:
            self._do_print('%s| %s' % (str(datetime.timedelta(seconds=time.monotonic() - self._start_time))[0:-4], label), sep='', end='\n', file=sys.stdout, flush=True)

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


class TrivialLoggerDecorator(Logger):
    def __init__(self, decorated_logger):
        self._decorated_logger = decorated_logger

    def configure(self, config):
        self._decorated_logger.configure(config)

    def print(self, *args, sep='', end='\n', file=sys.stdout, flush=True):
        self._decorated_logger.print(*args, sep=sep, end=end, flush=flush)

    def debug(self, *args, sep='', end='\n', flush=True):
        self._decorated_logger.debug(*args, sep=sep, end=end, flush=flush)

    def bench(self, label):
        self._decorated_logger.bench(label)

    def finalize(self):
        self._decorated_logger.finalize()


class FileLoggerDecorator(TrivialLoggerDecorator):
    def __init__(self, decorated_logger, local_repository_provider):
        super().__init__(decorated_logger)
        self._logfile = tempfile.NamedTemporaryFile('w', delete=False)
        self._local_repository_provider = local_repository_provider

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
        transformed = _transform_debug_args(args)
        self._decorated_logger.debug(*transformed, sep=sep, end=end, flush=flush)
        self._do_print_in_file(*transformed, sep=sep, end=end, flush=flush)

    def _do_print_in_file(self, *args, sep, end, flush):
        if self._logfile is not None:
            print(*args, sep=sep, end=end, file=self._logfile, flush=flush)


class DebugOnlyLoggerDecorator(TrivialLoggerDecorator):
    def __init__(self, decorated_logger):
        super().__init__(decorated_logger)

    def print(self, *args, sep='', end='\n', file=sys.stdout, flush=True):
        """Calls debug instead of print"""
        self._decorated_logger.debug(*args, sep=sep, end=end, flush=flush)


def _transform_debug_args(args):
    exception_msgs = []
    rest_args = []
    interp_count = 0
    interp_main = ''
    interp_subs = []
    for a in args:
        if isinstance(a, Exception):
            exception_msgs.append(_format_ex(a))
            continue

        if interp_count > 1:
            interp_subs.append(str(a))
            interp_count -= 1
        elif interp_count == 1:
            try:
                rest_args.append(interp_main % (*interp_subs, str(a)))
            except Exception as e:
                exception_msgs.append(_format_ex(e))
                rest_args.extend([interp_main, *interp_subs, str(a)])
            interp_subs = []
            interp_count = 0
            interp_main = ''
        elif isinstance(a, str) and (interp_count := a.count('%s')) > 0:
            interp_main = a
        else:
            rest_args.append(str(a))
    return [*rest_args, *exception_msgs]


def _format_ex(e: BaseException) -> str:
    exception_msg = ''.join(traceback.TracebackException.from_exception(e).format())
    padding = ' ' * 4
    while e.__cause__ is not None:
        e = e.__cause__
        exception_msg += padding + 'CAUSE: ' + padding.join(traceback.TracebackException.from_exception(e).format())
        padding += ' ' * 4
    return exception_msg


class CollectorLoggerDecorator(TrivialLoggerDecorator):
    def __init__(self, decorated_logger):
        super().__init__(decorated_logger)
        self.prints = []
        self.debugs = []

    def print(self, *args, sep='', end='\n', file=sys.stdout, flush=True):
        self._decorated_logger.print(*args, sep=sep, end=end, flush=flush)
        self.prints.append(args[0])

    def debug(self, *args, sep='', end='\n', flush=True):
        self._decorated_logger.debug(*args, sep=sep, end=end, flush=flush)
        self.debugs.append(args[0])


class PostPrintCallbackLoggerDecorator(TrivialLoggerDecorator):
    def __init__(self, decorated_logger, post_print_cb):
        super().__init__(decorated_logger)
        self._post_print_cb = post_print_cb

    def print(self, *args, sep='', end='\n', file=sys.stdout, flush=True):
        self._post_print_cb(args[0])
