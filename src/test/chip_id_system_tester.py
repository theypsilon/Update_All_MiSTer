import mmap
import os
import queue
import signal
import struct
import subprocess
from pathlib import Path
from types import SimpleNamespace

from update_all.chip_id_linker.chip_id_system import ChipIdSystem
from update_all.chip_id_linker.chip_id_linker import (
    CHIP_ID_BASE, CHIP_ID_HPS_FPGAMGR_BASE, CHIP_ID_HPS_RSTMGR_BASE,
    CHIP_ID_FPGAMGR_GPIO_EXT_PORTA_OFFSET, CHIP_ID_RSTMGR_BRG_MOD_RESET_OFFSET,
    CHIP_ID_MENU_CORE_NAME_PATH, CHIP_ID_RELAUNCH_SCRIPT_STARTED_PATH,
    CHIP_ID_RESULT_HANDOFF_PATH, CHIP_ID_UI_DEV_CREATE, CHIP_ID_UI_DEV_DESTROY,
    CHIP_ID_EV_KEY, CHIP_ID_KEY_F9,
)


class ChipIdSystemTester(ChipIdSystem):
    def __init__(self, root, logger, environment=None):
        super().__init__(dict(os.environ) if environment is None else environment)
        self.root = Path(root)
        self.logger = logger
        self.events = []
        self.opened_devices = []
        self.closed_devices = []
        self.descriptors = {}
        self.core_commands = []
        self.failed_core_loads = set()
        self.firmware_restarts = True
        self.menu_restores = True
        self.open_errors = {}
        self.map_errors = {}
        self.memory_maps = []
        self.process_exitcodes = []
        self.isolated_processes = []
        self.run_calls = []
        self.popen_calls = []
        self.popen_error = None
        self.relaunch_processes = []
        self.relaunch_start_delay = 0.05
        self.visible_processes = {}
        self.ignored_signals = set()
        self.signals = []
        self.printed_results = []
        self.sleeps = []
        self._clock = 0.0
        self._scheduled = []
        self.f9_count = 0
        self.f9_console_after = 1
        self.archive_path = None
        self.handoffs_at_keyboard_open = []
        self.worker_marker_path = None
        self.log_path = None
        self.observations_at_load = []
        self.hard_exit_on_load = None
        self.append_external_log_on_load = False
        for path, content in {
            '/dev/MiSTer_cmd': b'', '/dev/uinput': b'', '/dev/fb0': b'',
            '/dev/tty1': b'', '/dev/tty2': b'', '/dev/tty3': b'', '/dev/tty7': b'',
            '/sys/class/graphics/fbcon/cursor_blink': b'1\n',
            '/sys/devices/virtual/tty/tty0/active': b'tty1\n',
            '/proc/bus/input/devices': b'Zaparoo\n', CHIP_ID_MENU_CORE_NAME_PATH: b'MENU\n',
        }.items():
            target = self.path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        self.path('/dev/mem').write_bytes(bytes(3 * 4096))
        self.set_chip_id_memory()
        self.set_hps_status()

    def path(self, path):
        path = Path(path)
        if path.is_relative_to(self.root):
            return path
        return self.root / 'linux' / str(path).lstrip('/')

    def read_text(self, path):
        return self.path(path).read_text()

    def open_file(self, path, *args, **kwargs):
        if str(path) in self.open_errors:
            raise self.open_errors[str(path)]
        return self.path(path).open(*args, **kwargs)

    def exists(self, path):
        return self.path(path).exists()

    def stat(self, path):
        return self.path(path).stat()

    def remove(self, path):
        self.events.append(('remove', str(path)))
        self.path(path).unlink()

    def makedirs(self, path, exist_ok=False):
        self.path(path).mkdir(parents=True, exist_ok=exist_ok)

    def replace(self, source, destination):
        self.path(source).replace(self.path(destination))

    def chmod(self, path, mode):
        self.path(path).chmod(mode)

    def open_device(self, path, flags):
        self.opened_devices.append((path, flags))
        if path in self.open_errors:
            raise self.open_errors[path]
        if path == '/dev/uinput':
            handoff = self.path(CHIP_ID_RESULT_HANDOFF_PATH)
            self.handoffs_at_keyboard_open.append(handoff.read_text() if handoff.exists() else None)
        fd = os.open(self.path(path), flags)
        self.descriptors[fd] = path
        return fd

    def close(self, fd):
        self.closed_devices.append(self.descriptors.pop(fd))
        os.close(fd)

    def write(self, fd, data):
        path = self.descriptors[fd]
        if path == '/dev/MiSTer_cmd':
            command = data.decode()
            self.core_commands.append(command)
            self.events.append(('core_command', command))
            self.observations_at_load.append({
                'marker': self.exists(self.worker_marker_path) if self.worker_marker_path else False,
                'log': Path(self.log_path).read_text() if self.log_path and Path(self.log_path).exists() else '',
            })
            if self.hard_exit_on_load is not None:
                self.logger.debug('worker log before hard exit')
                os._exit(self.hard_exit_on_load)
            if self.append_external_log_on_load:
                with open(self.log_path, 'a') as log:
                    log.write('relaunch_script: started\n')
            core = command.removeprefix('load_core ')
            if core in self.failed_core_loads:
                raise OSError('firmware rejected core load')
            if core == 'menu.rbf':
                if self.menu_restores:
                    self.rewrite_core_name('MENU')
            elif self.firmware_restarts:
                self.rewrite_core_name('LINKER')
        elif path == '/dev/uinput' and len(data) == struct.calcsize('llHHi'):
            _, _, event_type, code, value = struct.unpack('llHHi', data)
            if event_type == CHIP_ID_EV_KEY:
                self.events.append(('key', code, value))
                if code == CHIP_ID_KEY_F9 and value == 0:
                    self.f9_count += 1
                    if self.f9_console_after is not None and self.f9_count >= self.f9_console_after:
                        self.path('/sys/devices/virtual/tty/tty0/active').write_text('tty1\n')
        elif path.startswith('/dev/tty'):
            self.events.append(('reset', path))
        return os.write(fd, data)

    def ioctl(self, fd, request, value=0):
        if request == CHIP_ID_UI_DEV_CREATE:
            self.events.append(('keyboard_created', self.descriptors[fd]))
        elif request == CHIP_ID_UI_DEV_DESTROY:
            self.events.append(('keyboard_destroyed', self.descriptors[fd]))
        return 0

    def mmap(self, fd, length, flags, prot, offset=0):
        self.memory_maps.append(offset)
        if offset in self.map_errors:
            raise self.map_errors[offset]
        offsets = {CHIP_ID_BASE: 0, CHIP_ID_HPS_FPGAMGR_BASE: 4096, CHIP_ID_HPS_RSTMGR_BASE: 8192}
        return mmap.mmap(fd, length, flags, prot, offset=offsets[offset])

    def set_chip_id_memory(self, id_hi=0x01234567, id_lo=0x89abcdef, version=0x00010000,
                           status=1, id_xor=None, magic=0x43484944):
        if id_xor is None:
            id_xor = id_lo ^ id_hi ^ 0x43484944
        memory = bytearray(0x20)
        struct.pack_into('<7I', memory, 0, magic, version, status, id_lo, id_hi, id_xor, 0)
        with self.path('/dev/mem').open('r+b') as file:
            file.write(memory)
        return memory

    def set_hps_status(self, fpga_mode=4, init_done=True, bridge_reset=0):
        with self.path('/dev/mem').open('r+b') as file:
            for offset, value in ((4096, fpga_mode),
                                  (4096 + CHIP_ID_FPGAMGR_GPIO_EXT_PORTA_OFFSET, 4 if init_done else 0),
                                  (8192 + CHIP_ID_RSTMGR_BRG_MOD_RESET_OFFSET, bridge_reset)):
                file.seek(offset)
                file.write(struct.pack('<I', value))

    def rewrite_core_name(self, name):
        path = self.path(CHIP_ID_MENU_CORE_NAME_PATH)
        previous = path.stat().st_mtime_ns
        path.write_text(name + '\n')
        os.utime(path, ns=(previous + 100, previous + 100))

    def run(self, args, **kwargs):
        self.run_calls.append((args, kwargs))
        if args == ['ps', 'ax']:
            self.events.append(('ps',))
            return SimpleNamespace(returncode=0, stdout='\n'.join(self.visible_processes.values()))
        if args == ['stty', 'sane']:
            return SimpleNamespace(returncode=0)
        if args[0] == 'chvt':
            self.events.append(('chvt', args[1]))
            self.path('/sys/devices/virtual/tty/tty0/active').write_text(f'tty{args[1]}\n')
            return SimpleNamespace(returncode=0)
        raise AssertionError(f'Unexpected external command: {args}')

    def popen(self, args):
        self.popen_calls.append(args)
        if self.popen_error is not None:
            raise self.popen_error
        process = ChipIdProcessTester(pid=456 + len(self.relaunch_processes))
        self.relaunch_processes.append(process)
        if self.relaunch_start_delay is not None:
            self.schedule(self.relaunch_start_delay,
                          lambda: self.path(CHIP_ID_RELAUNCH_SCRIPT_STARTED_PATH).write_text(str(process.pid)))
        return process

    def kill(self, pid, sig):
        self.signals.append((pid, sig))
        if (pid, sig) not in self.ignored_signals:
            del self.visible_processes[pid]

    def get_context(self, method):
        assert method == 'fork'
        return _ForkContextTester(self)

    def monotonic(self):
        return self._clock

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        end = round(self._clock + seconds, 9)
        while self._scheduled and self._scheduled[0][0] <= end:
            instant, action = self._scheduled.pop(0)
            self._clock = instant
            action()
        self._clock = end

    def schedule(self, delay, action):
        self._scheduled.append((round(self._clock + delay, 9), action))
        self._scheduled.sort(key=lambda item: item[0])

    def print_result(self, result):
        self.printed_results.append(result)

    def current_archive_path(self):
        return self.archive_path

    def close_remaining_descriptors(self):
        for fd in list(self.descriptors):
            self.close(fd)


class ChipIdProcessTester:
    def __init__(self, pid=456, returncode=None):
        self.pid = pid
        self.returncode = returncode
        self.terminated = False
        self.killed = False
        self.ignore_termination = False

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True
        if not self.ignore_termination:
            self.returncode = -signal.SIGTERM

    def kill(self):
        self.killed = True
        self.returncode = -signal.SIGKILL

    def wait(self, timeout):
        if self.returncode is None:
            raise subprocess.TimeoutExpired('agetty', timeout)
        return self.returncode


class _ForkContextTester:
    Queue = staticmethod(queue.Queue)

    def __init__(self, system):
        self.system = system

    def Process(self, target, args):
        process = _IsolatedProcessTester(self.system, target, args)
        self.system.isolated_processes.append(process)
        return process


class _IsolatedProcessTester:
    def __init__(self, system, target, args):
        self.system = system
        self.target = target
        self.args = args
        self.exitcode = None

    def start(self):
        forced_exit = self.system.process_exitcodes.pop(0) if self.system.process_exitcodes else None
        if forced_exit is not None:
            self.exitcode = forced_exit
            return
        self.target(*self.args)
        self.exitcode = 0

    def join(self, _timeout):
        pass

    def is_alive(self):
        return False
