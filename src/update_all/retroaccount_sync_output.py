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

import sys
from typing import Optional, Protocol, TextIO, Union


class RetroAccountSyncOutput(Protocol):
    def jtbeta_updated(self) -> None: pass
    def credentials_removed(self, reason: str) -> None: pass


class NoopRetroAccountSyncOutput(RetroAccountSyncOutput):
    def jtbeta_updated(self) -> None: pass
    def credentials_removed(self, reason: str) -> None: pass


class LtsvRetroAccountSyncOutput(RetroAccountSyncOutput):
    def __init__(self, stream: Optional[TextIO] = None) -> None:
        self._stream = sys.stdout if stream is None else stream

    def jtbeta_updated(self) -> None:
        self._emit('retroaccount_jtbeta_updated')

    def credentials_removed(self, reason: str) -> None:
        self._emit('retroaccount_credentials_removed', reason=reason)

    def _emit(self, event: str, **fields: Union[str, int]) -> None:
        line = ['DLP1', f'event:{_sanitize(event)}']
        for key, value in fields.items():
            line.append(f'{_sanitize(key)}:{_sanitize(str(value))}')
        print('\t'.join(line), file=self._stream, flush=True)


def _sanitize(value: str) -> str:
    return value.replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')
