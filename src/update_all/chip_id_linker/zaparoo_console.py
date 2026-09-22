import re
import stat
from typing import NamedTuple, Optional

from update_all.chip_id_linker.console_system import ConsoleProcess, ConsoleSystem, Debug


ZAPAROO_CONSOLE_STATE_PATH = '/tmp/zaparoo_console_state'
ZAPAROO_COMMAND_DEVICE = 'MiSTer_cmd'
ZAPAROO_MAIN_EXECUTABLES = ('/media/fat/zaparoo/MiSTer_Zaparoo', '/media/fat/MiSTer_Zaparoo')
ZAPAROO_CONSOLE_TIMEOUT_SECONDS = 5.0


class ConsoleState(NamedTuple):
    pid: int
    status: str
    nonce: str


class ZaparooConsoleUnavailable(RuntimeError):
    """Main refused the request without granting a console lease."""


def _read_state(system: ConsoleSystem, debug: Debug) -> Optional[ConsoleState]:
    try:
        fields = system.read_text(ZAPAROO_CONSOLE_STATE_PATH).split()
    except FileNotFoundError:
        return None
    except (OSError, UnicodeError) as e:
        debug('Could not read Zaparoo console state')
        debug(e)
        return None
    if len(fields) != 4 or fields[0] != '1' or re.fullmatch(r'[0-9]+', fields[1]) is None:
        debug(f'Ignoring unsupported Zaparoo console state: {fields!r}')
        return None
    if int(fields[1]) <= 1 or fields[2] not in ('ready', 'acquired', 'released', 'busy', 'failed'):
        debug(f'Ignoring invalid Zaparoo console state: {fields!r}')
        return None
    return ConsoleState(int(fields[1]), fields[2], fields[3])


class ZaparooConsole:
    def __init__(self, system: ConsoleSystem, debug: Debug):
        self._system = system
        self._debug = debug

    def detect(self) -> Optional['ZaparooConsoleLease']:
        state = _read_state(self._system, self._debug)
        if state is None:
            return None
        process = self._system.read_process(state.pid)
        if process is None or process.executable not in ZAPAROO_MAIN_EXECUTABLES \
                or not self._system.has_open_device(process, ZAPAROO_COMMAND_DEVICE, stat.S_IFIFO):
            self._debug('Ignoring Zaparoo console state without a matching live Main process')
            return None
        return ZaparooConsoleLease(process, self._system.nonce(), self._system, self._debug)

    def restore(self, token: str) -> None:
        if re.fullmatch(r'[0-9]+:[0-9]+:[a-zA-Z0-9-]{1,64}', token) is None:
            raise ValueError('Invalid Zaparoo console restore token')
        pid, start_time, nonce = token.split(':')
        process = self._system.read_process(int(pid))
        if process is None or process.start_time != start_time or process.executable not in ZAPAROO_MAIN_EXECUTABLES \
                or not self._system.has_open_device(process, ZAPAROO_COMMAND_DEVICE, stat.S_IFIFO):
            self._debug('Zaparoo Main changed before console restoration')
            return
        ZaparooConsoleLease(process, nonce, self._system, self._debug).release()


class ZaparooConsoleLease:
    def __init__(self, process: ConsoleProcess, nonce: str, system: ConsoleSystem, debug: Debug):
        self._process = process
        self._nonce = nonce
        self._system = system
        self._debug = debug

    def restore_token(self) -> str:
        return f'{self._process.pid}:{self._process.start_time}:{self._nonce}'

    def acquire(self, tty: str) -> None:
        if not tty.isdigit() or not 1 <= int(tty) <= 63:
            raise ValueError('Invalid console VT')
        self._command(f'acquire {self._nonce} {tty}')
        self._wait_for('acquired')

    def release(self) -> None:
        if not self._system.is_running(self._process):
            self._debug('Zaparoo Main changed; its previous console lease no longer applies')
            return
        state = _read_state(self._system, self._debug)
        if state is not None and state.pid == self._process.pid and state.nonce == self._nonce \
                and state.status in ('released', 'busy', 'failed'):
            return
        self._command(f'release {self._nonce}')
        self._wait_for('released')

    def _command(self, command: str) -> None:
        if not self._system.is_running(self._process):
            raise RuntimeError('Zaparoo Main changed during the console handoff')
        self._debug(f'Zaparoo console request: {command}')
        self._system.write_command(ZAPAROO_COMMAND_DEVICE, f'zaparoo_console {command}\n', self._process)

    def _wait_for(self, expected: str) -> None:
        deadline = self._system.monotonic() + ZAPAROO_CONSOLE_TIMEOUT_SECONDS
        while True:
            if not self._system.is_running(self._process):
                raise RuntimeError('Zaparoo Main changed while waiting for the console')
            state = _read_state(self._system, self._debug)
            if state is not None and state.pid == self._process.pid and state.nonce == self._nonce:
                if state.status == expected:
                    self._debug(f'Zaparoo console acknowledged: {expected}')
                    return
                if state.status == 'failed':
                    raise ZaparooConsoleUnavailable(f'Zaparoo console request {expected}: failed')
                if state.status == 'busy':
                    raise RuntimeError(f'Zaparoo console request {expected}: {state.status}')
            if self._system.monotonic() >= deadline:
                raise TimeoutError(f'Zaparoo console did not acknowledge {expected}')
            self._system.sleep(0.05)
