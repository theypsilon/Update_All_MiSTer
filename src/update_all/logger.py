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
import os
import tempfile
import sys
import time
import traceback
from abc import ABC, abstractmethod
from io import TextIOWrapper
from typing import Optional

from update_all.constants import FILE_update_all_print_tmp_log


class Logger(ABC):
    @abstractmethod
    def configure(self, _config):
        """makes logs more verbose"""

    @abstractmethod
    def print(self, *args, sep='', end='\n', flush=True):
        """print always"""

    @abstractmethod
    def debug(self, *args, sep='', end='\n', flush=True):
        """print only to debug target"""

    @abstractmethod
    def bench(self, label):
        """print only to debug target"""

    def finalize(self):
        """to be called at the very end, should not call any method after this one"""

_print_tmp_log_file: Optional[TextIOWrapper] = None
def open_print_tmp_log_file():
    if os.path.exists(FILE_update_all_print_tmp_log):
        os.remove(FILE_update_all_print_tmp_log)
    global _print_tmp_log_file
    _print_tmp_log_file = open(FILE_update_all_print_tmp_log, 'w')

def close_print_tmp_log_file():
    global _print_tmp_log_file
    if _print_tmp_log_file is not None:
        _print_tmp_log_file.close()
        _print_tmp_log_file = None

def apply_overscan_to_text(args, sep: str, columns: int, overscan: int) -> list[str]:
    import textwrap
    text = sep.join(str(a) for a in args)
    pad = ' ' * overscan
    usable = columns - overscan * 2
    if not text:
        return [pad]
    if len(text) <= usable:
        return [pad + text]
    lines = textwrap.wrap(text, width=usable, break_long_words=True, break_on_hyphens=False)
    return [pad + line for line in lines]


def apply_overscan_preserving_newlines(args, sep: str, columns: int, overscan: int, end: str) -> list[tuple[str, str]]:
    text = sep.join(str(a) for a in args)
    rendered_lines: list[tuple[str, str]] = []

    if text == '':
        return [(line, end) for line in apply_overscan_to_text([''], '', columns, overscan)]

    chunks = text.splitlines(keepends=True)
    if len(chunks) == 0:
        chunks = [text]

    for chunk_index, chunk in enumerate(chunks):
        has_newline = chunk.endswith('\n')
        chunk_text = chunk[:-1] if has_newline else chunk
        chunk_lines = apply_overscan_to_text([chunk_text], '', columns, overscan)
        is_last_chunk = chunk_index == len(chunks) - 1
        chunk_end = '\n' if has_newline else end if is_last_chunk else ''

        for line_index, line in enumerate(chunk_lines):
            line_end = chunk_end if line_index == len(chunk_lines) - 1 else '\n'
            rendered_lines.append((line, line_end))

    return rendered_lines


class PrintLogger(Logger):
    def __init__(self):
        self._verbose_mode = False
        self._start_time = None
        self._overscan = 0
        self._columns = 0

    def set_local_repository(self, local_repository):
        pass

    def configure(self, config):
        if config.verbose:
            self._verbose_mode = True
            self._start_time = config.start_time
        self._overscan = config.overscan_dim.cols
        self._columns = config.term_size.columns
        open_print_tmp_log_file()

    def print(self, *args, sep='', end='\n', flush=True):
        if self._overscan == 0:
            self._do_print(*args, sep=sep, end=end, file=sys.stdout, flush=flush)
        else:
            for line, line_end in apply_overscan_preserving_newlines(args, sep, self._columns, self._overscan, end):
                self._do_print(line, sep='', end=line_end, file=sys.stdout, flush=flush)
        if _print_tmp_log_file is not None:
            self._do_print(*args, sep=sep, end=end, file=_print_tmp_log_file, flush=flush)

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

    def print(self, *args, sep='', end='\n', flush=True):
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
        try:
            self._local_repository_provider.get().save_log_from_tmp(self._logfile.name)
        except:
            pass
        self._logfile = None

    def print(self, *args, sep='', end='\n', flush=True):
        self._decorated_logger.print(*args, sep=sep, end=end, flush=flush)
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

    def print(self, *args, sep='', end='\n', flush=True):
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

    def print(self, *args, sep='', end='\n', flush=True):
        self._decorated_logger.print(*args, sep=sep, end=end, flush=flush)
        self.prints.append(args[0])

    def debug(self, *args, sep='', end='\n', flush=True):
        self._decorated_logger.debug(*args, sep=sep, end=end, flush=flush)
        self.debugs.append(args[0])


class PostPrintCallbackLoggerDecorator(TrivialLoggerDecorator):
    def __init__(self, decorated_logger, post_print_cb):
        super().__init__(decorated_logger)
        self._post_print_cb = post_print_cb

    def print(self, *args, sep='', end='\n', flush=True):
        self._post_print_cb(args[0])
