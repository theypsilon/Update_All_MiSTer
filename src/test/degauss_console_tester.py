from test.console_system_tester import ConsoleSystemTester
from update_all.chip_id_linker.degauss_console import DegaussConsole


class DegaussConsoleTester(DegaussConsole):
    def __init__(self, system=None):
        self.system = system or ConsoleSystemTester()
        self.main = None
        super().__init__(self.system, self.system.logger.debug)

    def start_frontend(self, pid=456, old_location=False):
        if self.main is None:
            self.main = self.system.add_process(124, '/media/fat/degauss/MiSTer_Degauss')
            self.system.attach_device(self.main.pid, 'MiSTer_cmd')
        wrapper = self.system.add_process(pid + 10000, '/bin/bash', parent_pid=self.main.pid)
        path = '/media/fat/Scripts/.degauss/degauss' if old_location else '/media/fat/Scripts/.config/degauss/degauss'
        frontend = self.system.add_process(pid, path, parent_pid=wrapper.pid)
        self.system.attach_device(pid, 'tty2', '0')
        self.system.attach_device(pid, 'fb0')
        return frontend

    def close(self):
        self.system.close()
