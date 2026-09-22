from test.console_system_tester import ConsoleSystemTester
from update_all.chip_id_linker.zaparoo_console import ZaparooConsole, ZAPAROO_CONSOLE_STATE_PATH


class ZaparooConsoleTester(ZaparooConsole):
    def __init__(self, system=None, on_acquire=None):
        self.system = system or ConsoleSystemTester()
        self.process = None
        self.acquire_status = 'acquired'
        self.acquire_error = None
        self.release_status = 'released'
        self.acknowledge_acquire = True
        self.acknowledge_release = True
        self.ack_delay = 0
        self.lease_nonce = None
        self.on_acquire = on_acquire
        self.system.on_command = self._receive_command
        super().__init__(self.system, self.system.logger.debug)

    def enable(self):
        self.process = self.system.add_process(123, '/media/fat/zaparoo/MiSTer_Zaparoo')
        self.system.attach_device(self.process.pid, 'MiSTer_cmd')
        self.publish('ready', '-')

    def publish(self, status, nonce, pid=123):
        self.system.files[ZAPAROO_CONSOLE_STATE_PATH] = f'1 {pid} {status} {nonce}\n'

    def _receive_command(self, command):
        _, action, nonce, *arguments = command.split()
        if action == 'acquire':
            status = self.acquire_status
            if status == 'acquired':
                self.lease_nonce = nonce
                if self.on_acquire is not None:
                    self.on_acquire(arguments[0])
            if self.acquire_error is not None:
                raise self.acquire_error
            if not self.acknowledge_acquire:
                return
        else:
            status = self.release_status if self.lease_nonce == nonce else 'failed'
            if status == 'released':
                self.lease_nonce = None
            if not self.acknowledge_release:
                return
        if self.ack_delay:
            self.system.schedule(self.ack_delay, lambda: self.publish(status, nonce))
        else:
            self.publish(status, nonce)

    def close(self):
        self.system.close()
