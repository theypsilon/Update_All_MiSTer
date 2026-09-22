import stat

from update_all.chip_id_linker.console_system import ConsoleSystem, Debug


DEGAUSS_EXECUTABLES = ('/media/fat/Scripts/.config/degauss/degauss', '/media/fat/Scripts/.degauss/degauss')
DEGAUSS_MAIN_EXECUTABLES = ('/media/fat/MiSTer', '/media/fat/degauss/MiSTer_Degauss', '/media/fat/MiSTer_Degauss')
DEGAUSS_STOP_TIMEOUT_SECONDS = 2.0


class DegaussConsole:
    def __init__(self, system: ConsoleSystem, debug: Debug):
        self._system = system
        self._debug = debug

    def prepare(self) -> bool:
        processes = [process for process in self._system.find_processes(DEGAUSS_EXECUTABLES)
                     if self._system.has_open_device(process, 'tty2', stat.S_IFCHR, '0')
                     and self._system.has_open_device(process, 'fb0', stat.S_IFCHR)]
        confirmed = []
        for process in processes:
            main = self._system.find_ancestor(process, DEGAUSS_MAIN_EXECUTABLES)
            if main is not None and self._system.has_open_device(main, 'MiSTer_cmd', stat.S_IFIFO):
                confirmed.append(process)
        if len(confirmed) != 1:
            if confirmed:
                self._debug('Multiple Degauss console owners found; refusing to select one')
            return False

        process = confirmed[0]
        self._debug(f'Stopping verified Degauss frontend pid {process.pid} before its script wrapper')
        try:
            if not self._system.stop_process(process, DEGAUSS_STOP_TIMEOUT_SECONDS):
                return False
        except ProcessLookupError as e:
            self._debug('Degauss exited before its process descriptor could be opened')
            self._debug(e)
            return False

        self._system.restore_text_console('tty2')
        return True
