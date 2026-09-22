import array
import fcntl
import os
import select
import signal
import stat
import time
import uuid
from typing import Callable, NamedTuple, Optional


Debug = Callable[[object], None]
KDGETMODE = 0x4B3B
KDSETMODE = 0x4B3A
KD_TEXT = 0
KD_GRAPHICS = 1


class ConsoleProcess(NamedTuple):
    pid: int
    start_time: str
    executable: str
    parent_pid: int


class ConsoleSystem:
    def __init__(self, debug: Debug, proc_path: str, dev_path: str):
        self._debug = debug
        self._proc_path = proc_path
        self._dev_path = dev_path

    def read_process(self, pid: int) -> Optional[ConsoleProcess]:
        try:
            executable = os.readlink(f'{self._proc_path}/{pid}/exe').removesuffix(' (deleted)')
            with open(f'{self._proc_path}/{pid}/stat') as stat_file:
                # comm is parenthesized and can itself contain spaces or parentheses.
                description = stat_file.read()
                fields = description.rpartition(')')[2].split()
            if int(description.partition('(')[0]) != pid or fields[0] in ('Z', 'X') \
                    or int(fields[19]) <= 0 or int(fields[1]) < 0:
                return None
            return ConsoleProcess(pid, fields[19], executable, int(fields[1]))
        except (FileNotFoundError, ProcessLookupError):
            # Kernel threads have no executable.
            return None
        except (OSError, UnicodeError, IndexError, ValueError) as e:
            self._debug(f'Could not inspect console process {pid}')
            self._debug(e)
            return None

    def is_running(self, process: ConsoleProcess) -> bool:
        return self.read_process(process.pid) == process

    def find_processes(self, executable_paths: tuple[str, ...]) -> list[ConsoleProcess]:
        try:
            entries = os.listdir(self._proc_path)
        except OSError as e:
            self._debug('Could not scan for frontend console processes')
            self._debug(e)
            return []
        processes = []
        for entry in entries:
            if not entry.isascii() or not entry.isdecimal():
                continue
            process = self.read_process(int(entry))
            if process is not None and process.executable in executable_paths:
                processes.append(process)
        return processes

    def find_ancestor(self, process: ConsoleProcess, executable_paths: tuple[str, ...]) -> Optional[ConsoleProcess]:
        visited = {process.pid}
        for _ in range(32):
            if not self.is_running(process) or process.parent_pid <= 1 or process.parent_pid in visited:
                return None
            parent = self.read_process(process.parent_pid)
            if parent is None or int(parent.start_time) > int(process.start_time):
                return None
            if parent.executable in executable_paths:
                return parent
            visited.add(parent.pid)
            process = parent
        return None

    def has_open_device(self, process: ConsoleProcess, device: str, file_type: int, fd: Optional[str] = None) -> bool:
        try:
            target = os.stat(f'{self._dev_path}/{device}')
            if stat.S_IFMT(target.st_mode) != file_type:
                return False
            return self._has_open_file(process, target, fd)
        except (OSError, ValueError, UnicodeError, IndexError) as e:
            self._debug(f'Could not verify {device} ownership for process {process.pid}')
            self._debug(e)
            return False

    def _has_open_file(self, process: ConsoleProcess, target, fd: Optional[str]) -> bool:
        if not self.is_running(process):
            return False
        directory = f'{self._proc_path}/{process.pid}/fd'
        descriptors = [fd] if fd is not None else os.listdir(directory)
        for descriptor in descriptors:
            try:
                opened = os.stat(f'{directory}/{descriptor}')
                if (opened.st_dev, opened.st_ino) != (target.st_dev, target.st_ino):
                    continue
                with open(f'{self._proc_path}/{process.pid}/fdinfo/{descriptor}') as info:
                    flags = next(int(line.split()[1], 8) for line in info if line.startswith('flags:'))
                if flags & os.O_PATH or (flags & os.O_ACCMODE) == os.O_WRONLY:
                    continue
                current = os.stat(f'{directory}/{descriptor}')
                if (current.st_dev, current.st_ino) != (target.st_dev, target.st_ino):
                    continue
                return self.is_running(process)
            except (FileNotFoundError, ProcessLookupError):
                continue
            except StopIteration:
                continue
        return False

    def stop_process(self, process: ConsoleProcess, timeout: float) -> bool:
        # Never fall back to kill(pid): a recycled PID could name another process.
        descriptor = os.pidfd_open(process.pid)
        try:
            if not self.is_running(process):
                return False
            signal.pidfd_send_signal(descriptor, signal.SIGTERM)
            waiter = select.poll()
            waiter.register(descriptor, select.POLLIN)
            events = waiter.poll(int(timeout * 1000))
            if not events:
                raise TimeoutError('Frontend process did not exit before timeout')
            if not (events[0][1] & select.POLLIN):
                raise RuntimeError('Could not confirm frontend process exit')
            return True
        except ProcessLookupError:
            return False
        finally:
            os.close(descriptor)

    def restore_text_console(self, tty: str) -> None:
        # stty does not change KD_GRAPHICS. Only reset after the frontend exits.
        fd = os.open(f'{self._dev_path}/{tty}', os.O_RDWR | os.O_NONBLOCK)
        try:
            mode = array.array('i', [0])
            fcntl.ioctl(fd, KDGETMODE, mode)
            self._debug(f'{tty} console mode after frontend shutdown: {mode[0]}')
            if mode[0] == KD_GRAPHICS:
                fcntl.ioctl(fd, KDSETMODE, KD_TEXT)
                self._debug(f'Restored {tty} to text mode')
        finally:
            os.close(fd)

    def read_text(self, path: str) -> str:
        with os.fdopen(os.open(path, os.O_RDONLY | os.O_NONBLOCK)) as source:
            if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                raise OSError('Console state is not a regular file')
            return source.read(256)

    def write_command(self, device: str, command: str, owner: ConsoleProcess) -> None:
        fd = os.open(f'{self._dev_path}/{device}', os.O_WRONLY | os.O_NONBLOCK)
        try:
            target = os.fstat(fd)
            if not stat.S_ISFIFO(target.st_mode) or not self._has_open_file(owner, target, None):
                raise RuntimeError('MiSTer no longer owns the command FIFO')
            os.write(fd, command.encode())
        finally:
            os.close(fd)

    def nonce(self) -> str:
        return uuid.uuid4().hex

    def monotonic(self) -> float:
        return time.monotonic()

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)
