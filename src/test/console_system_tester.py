import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

from test.logger_tester import LoggerSpy
from update_all.chip_id_linker.console_system import ConsoleProcess, ConsoleSystem, KD_GRAPHICS, KD_TEXT


class ConsoleSystemTester(ConsoleSystem):
    def __init__(self, logger=None):
        self.logger = logger or LoggerSpy()
        self.directory = tempfile.TemporaryDirectory()
        self.proc = Path(self.directory.name) / 'proc'
        self.dev = Path(self.directory.name) / 'dev'
        self.proc.mkdir()
        self.dev.mkdir()
        (self.dev / 'tty2').symlink_to('/dev/null')
        (self.dev / 'fb0').symlink_to('/dev/zero')
        os.mkfifo(self.dev / 'MiSTer_cmd')
        self.events = []
        self.discovery_calls = []
        self.files = {}
        self.read_errors = {}
        self.commands = []
        self.on_command = None
        self.ignored_terminations = set()
        self.termination_delay = 0
        self.before_stop = None
        self.stop_error = None
        self.children = []
        self.console_modes = {'tty2': KD_GRAPHICS}
        self._clock = 0
        self._scheduled = []
        self._nonce_count = 0
        super().__init__(self.logger.debug, str(self.proc), str(self.dev))

    def close(self):
        for child in self.children:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=2)
        self.directory.cleanup()

    def add_process(self, pid, executable, start_time='1000', parent_pid=1):
        directory = self.proc / str(pid)
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir()
        (directory / 'fd').mkdir()
        (directory / 'fdinfo').mkdir()
        executable_link = directory / 'exe'
        if executable_link.is_symlink():
            executable_link.unlink()
        os.symlink(executable, executable_link)
        fields = ['S', str(parent_pid)] + ['0'] * 17 + [start_time] + ['0'] * 10
        (directory / 'stat').write_text(f'{pid} (a tricky ) name) ' + ' '.join(fields))
        return ConsoleProcess(pid, start_time, executable.removesuffix(' (deleted)'), parent_pid)

    def attach_device(self, pid, device, fd='3', flags=os.O_RDWR):
        target = self.dev / device
        descriptor = self.proc / str(pid) / 'fd' / fd
        if stat.S_ISFIFO(target.stat().st_mode):
            os.link(target, descriptor)
        else:
            descriptor.symlink_to(target)
        (self.proc / str(pid) / 'fdinfo' / fd).write_text(f'flags:\t{flags:o}\n')

    def remove_process(self, pid):
        directory = self.proc / str(pid)
        shutil.rmtree(directory)
        self.events.append(('exit', pid))

    def read_process(self, pid):
        self.discovery_calls.append(('read_process', pid))
        return super().read_process(pid)

    def find_processes(self, executable_paths):
        self.discovery_calls.append(('find_processes', executable_paths))
        return super().find_processes(executable_paths)

    def stop_process(self, process, timeout):
        if self.stop_error is not None:
            raise self.stop_error
        if self.before_stop is not None:
            self.before_stop(process)
        if not self.is_running(process):
            return False
        pid = process.pid
        self.events.append(('terminate', pid))
        if pid not in self.ignored_terminations:
            if self.termination_delay:
                self.schedule(self.termination_delay, lambda: self.remove_process(pid))
            else:
                self.remove_process(pid)
        deadline = self.monotonic() + timeout
        while self.is_running(process):
            if self.monotonic() >= deadline:
                raise TimeoutError('Frontend process did not exit before timeout')
            self.sleep(0.05)
        return True

    def start_real_child(self, ignore_term=False):
        script = 'import signal, time; '
        if ignore_term:
            script += 'signal.signal(signal.SIGTERM, signal.SIG_IGN); '
        script += 'print("ready", flush=True); time.sleep(30)'
        child = subprocess.Popen([sys.executable, '-c', script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.children.append(child)
        assert child.stdout.readline() == b'ready\n'
        return child

    def restore_text_console(self, tty):
        self.events.append(('text_console', tty))
        self.console_modes[tty] = KD_TEXT

    def read_text(self, path):
        self.discovery_calls.append(('read_text', path))
        if path in self.read_errors:
            raise self.read_errors[path]
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path]

    def read_real_text_in_subprocess(self, path):
        script = '''import sys
from update_all.chip_id_linker.console_system import ConsoleSystem

system = ConsoleSystem(lambda message: None, '/proc', '/dev')
try:
    print(system.read_text(sys.argv[1]), end='')
except OSError:
    sys.exit(3)
'''
        return subprocess.run(
            [sys.executable, '-c', script, str(path)], cwd=Path(__file__).resolve().parents[1],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2,
        )

    def write_command(self, device, command, owner):
        if not self.has_open_device(owner, device, stat.S_IFIFO):
            raise RuntimeError('MiSTer no longer owns the command FIFO')
        path = f'/dev/{device}'
        self.commands.append((path, command))
        self.events.append(('command', command))
        if self.on_command is not None:
            self.on_command(command)

    def nonce(self):
        self._nonce_count += 1
        return f'nonce-{self._nonce_count}'

    def monotonic(self):
        return self._clock

    def schedule(self, seconds, action):
        self._scheduled.append((self._clock + seconds, action))

    def sleep(self, seconds):
        self._clock += seconds
        due = [item for item in self._scheduled if item[0] <= self._clock]
        self._scheduled = [item for item in self._scheduled if item[0] > self._clock]
        for _, action in due:
            action()
