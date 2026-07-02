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
import curses
import mmap
import os
from dataclasses import dataclass
from typing import Optional

from update_all.config import Config
from update_all.constants import FILE_MiSTer_ini
from update_all.file_system import FileSystem
from update_all.logger import Logger
from update_all.mister_ini_repository import MisterIniRepository
from update_all.os_utils import OsUtils
from update_all.other import GenericProvider, terminal_size, calculate_overscan


FIFO_PATH = '/dev/MiSTer_cmd'
_DEFAULT_NTSC_VIDEO_MODE = '640,30,60,70,240,4,4,14,12587'
_DEFAULT_PAL_VIDEO_MODE = '640,30,60,70,288,6,4,14,12587'


@dataclass(frozen=True)
class MisterVideoIniState:
    video_mode: Optional[str]
    vga_scaler: bool
    direct_video: bool


class MisterVideoModeService:
    def __init__(
            self,
            logger: Logger,
            file_system: FileSystem,
            config_provider: GenericProvider[Config],
            os_utils: OsUtils,
            mister_ini_repository: MisterIniRepository,
    ):
        self._logger = logger
        self._file_system = file_system
        self._config_provider = config_provider
        self._os_utils = os_utils
        self._mister_ini_repository = mister_ini_repository
        self._ini_state: Optional[MisterVideoIniState] = None
        self._ini_state_loaded = False
        self._current_mode: Optional[str] = None
        self._current_mode_loaded = False
        self._unsaved_kept_mode: Optional[str] = None
        self._mode_before_unsaved_keeps: Optional[str] = None

    def current_mode(self) -> Optional[str]:
        if self._current_mode_loaded:
            return self._current_mode

        try:
            self._current_mode = self._read_current_mode_from_ini()
        except Exception as e:
            self._logger.debug('MisterVideoModeService: Could not detect the current video mode')
            self._logger.debug(e)
            self._current_mode = None
        self._current_mode_loaded = True
        return self._current_mode

    def current_ini_state(self) -> MisterVideoIniState:
        if self._ini_state_loaded:
            return self._ini_state or MisterVideoIniState(None, False, False)

        try:
            self._ini_state = self._read_ini_state_from_ini()
        except Exception as e:
            self._logger.debug('MisterVideoModeService: Could not detect the current video settings')
            self._logger.debug(e)
            self._ini_state = MisterVideoIniState(None, False, False)
        self._ini_state_loaded = True
        return self._ini_state

    def current_direct_video(self) -> bool:
        return self.current_ini_state().direct_video

    def current_vga_scaler(self) -> bool:
        return self.current_ini_state().vga_scaler

    def apply_mode(self, mode_str: str) -> bool:
        try:
            mode_numbers = parse_mode(mode_str)
            if len(mode_numbers) != 9:
                raise ValueError(f'Video mode should have 9 numbers, got {len(mode_numbers)}: {mode_str}')

            hact, hfp, hs, hbp, vact, vfp, vs, vbp, fpix = mode_numbers
            htotal = hact + hfp + hs + hbp
            if htotal <= 0:
                raise ValueError(f'video_mode_cmd: BLOCKED. htotal={htotal} is invalid.')

            hfreq = fpix * 1000 / htotal
            # Safe hfreq range for 15kHz CRTs based on Switchres arcade_15ex preset.
            # https://github.com/antonioginer/switchres/blob/master/monitor.cpp
            if hfreq < 15625 or hfreq > 16500:
                raise ValueError(f'video_mode_cmd: BLOCKED. hfreq={hfreq:.0f}Hz is outside 15625-16500Hz safe range.')

            if vact <= 0 or min(vfp, vs, vbp) < 0:
                raise ValueError(
                    f'video_mode_cmd: BLOCKED. vertical timing contains invalid values: '
                    f'vact={vact} vfp={vfp} vs={vs} vbp={vbp}.'
                )
        except ValueError as e:
            self._logger.debug('MisterVideoModeService: Invalid video mode')
            self._logger.debug(e)
            return False

        try:
            fd = os.open(FIFO_PATH, os.O_WRONLY | os.O_NONBLOCK)
            try:
                os.write(fd, f'video_mode {mode_str}'.encode())
            finally:
                os.close(fd)
            self._os_utils.sleep(0.1)
            self._refresh_terminal_size()
            self._current_mode = mode_str
            self._current_mode_loaded = True
            return True
        except Exception as e:
            self._logger.debug('MisterVideoModeService: Could not apply video mode')
            self._logger.debug(e)
            return False

    def remember_unsaved_kept_mode(self, mode_str: str, previous_mode: Optional[str] = None) -> None:
        if self._unsaved_kept_mode is None:
            self._mode_before_unsaved_keeps = previous_mode
        self._unsaved_kept_mode = mode_str

    def has_unsaved_kept_mode(self) -> bool:
        return self._unsaved_kept_mode is not None

    def unsaved_kept_mode_filename(self) -> Optional[str]:
        if not self.has_unsaved_kept_mode():
            return None

        try:
            return os.path.basename(self._active_ini_path())
        except Exception as e:
            self._logger.debug('MisterVideoModeService: Could not resolve active ini path for unsaved kept video mode')
            self._logger.debug(e)
            return None

    def save_unsaved_kept_mode_to_active_ini(self) -> bool:
        if self._unsaved_kept_mode is None:
            return True

        try:
            ini_path = self._active_ini_path()
            mode = self._unsaved_kept_mode
            self._mister_ini_repository.remove_mister_ini_key('menu', 'direct_video', path=ini_path)
            self._mister_ini_repository.ensure_mister_ini_keys(
                'menu',
                {
                    'video_mode': mode,
                    'vga_scaler': '1',
                },
                create_if_missing=True,
                path=ini_path,
            )
            self._unsaved_kept_mode = None
            self._mode_before_unsaved_keeps = None
            return True
        except Exception as e:
            self._logger.debug('MisterVideoModeService: Could not save unsaved kept video mode to active ini')
            self._logger.debug(e)
            return False

    def restore_mode_before_unsaved_keeps(self) -> bool:
        if self._unsaved_kept_mode is None:
            return True

        if self._mode_before_unsaved_keeps is None:
            self._unsaved_kept_mode = None
            return True

        restored = self.apply_mode(self._mode_before_unsaved_keeps)
        if restored:
            self._unsaved_kept_mode = None
            self._mode_before_unsaved_keeps = None
        return restored

    def _refresh_terminal_size(self) -> None:
        size = terminal_size()
        try:
            curses.resizeterm(size.lines, size.columns)
        except curses.error:
            pass

        config = self._config_provider.get()
        config.term_size = size
        config.overscan_dim = calculate_overscan(config.overscan, size)

    def _read_ini_state_from_ini(self) -> MisterVideoIniState:
        ini_path = self._active_ini_path()
        if not self._file_system.is_file(ini_path):
            return MisterVideoIniState(None, False, False)
        return read_video_ini_state_from_contents(self._file_system.read_file_contents(ini_path))

    def _read_current_mode_from_ini(self) -> Optional[str]:
        ini_path = self._active_ini_path()
        if not self._file_system.is_file(ini_path):
            return None
        return read_video_mode_from_contents(self._file_system.read_file_contents(ini_path))

    def _active_ini_path(self) -> str:
        config = self._config_provider.get()
        default_ini = os.path.join(config.base_path, FILE_MiSTer_ini)
        active_alt = self._get_active_altcfg_index()
        if active_alt <= 0:
            return default_ini

        root = config.base_path
        found = []
        with os.scandir(root) as it:
            for entry in it:
                name = entry.name
                if name.lower().startswith('mister_') and name.lower().endswith('.ini'):
                    found.append(name)
                    if len(found) == 3:
                        break
        alt_inis = sorted(found, key=str.lower)
        if active_alt <= len(alt_inis):
            return os.path.join(root, alt_inis[active_alt - 1])
        return default_ini

    @staticmethod
    def _get_active_altcfg_index() -> int:
        fd = -1
        memory = None
        try:
            fd = os.open('/dev/mem', os.O_RDONLY | os.O_SYNC)
            memory = mmap.mmap(fd, 0x1000, mmap.MAP_SHARED, mmap.PROT_READ, offset=0x1FFFF000)
            data = memory[0xF04:0xF08]
            if data[0] == 0x34 and data[1] == 0x99 and data[2] == 0xBA:
                return data[3]
        except (OSError, IOError, ValueError):
            pass
        finally:
            if memory is not None:
                memory.close()
            if fd >= 0:
                os.close(fd)
        return 0


def read_video_mode_from_contents(contents: str) -> Optional[str]:
    sections = _read_video_ini_sections(contents)
    if sections.get('direct_video', '0') == '1':
        if sections.get('menu_pal', '0') == '1':
            return _DEFAULT_PAL_VIDEO_MODE
        return _DEFAULT_NTSC_VIDEO_MODE

    current_mode = sections.get('video_mode')
    if current_mode and ',' in current_mode:
        return current_mode
    return None


def read_video_ini_state_from_contents(contents: str) -> MisterVideoIniState:
    sections = _read_video_ini_sections(contents)
    current_mode = sections.get('video_mode')
    if current_mode and ',' not in current_mode:
        current_mode = None

    return MisterVideoIniState(
        current_mode,
        vga_scaler=sections.get('vga_scaler', '0') == '1',
        direct_video=sections.get('direct_video', '0') == '1',
    )


def _read_video_ini_sections(contents: str) -> dict[str, str]:
    merged = {'mister': {}, 'menu': {}}
    current_section = None

    for raw_line in contents.splitlines():
        line = _ini_parse_line(raw_line)
        if not line:
            continue

        section = _ini_get_section(line)
        if section is not None:
            current_section = section if section in merged else None
            continue

        if current_section is None:
            continue

        variable = _ini_get_var(line)
        if variable is None:
            continue

        key, value = variable
        if key in ('video_mode', 'direct_video', 'vga_scaler', 'menu_pal'):
            merged[current_section][key] = value

    return {**merged['mister'], **merged['menu']}


def parse_mode(mode_str: str) -> list[int]:
    return [int(part) for part in mode_str.split(',')]


def _ini_parse_line(raw: str) -> str:
    line = raw.lstrip(' \t')
    comment_index = line.find(';')
    if comment_index >= 0:
        line = line[:comment_index]
    return line.rstrip(' \t\r\n')


def _ini_get_section(line: str) -> Optional[str]:
    if not line.startswith('['):
        return None

    end = line.find(']')
    if end <= 1:
        return None

    return line[1:end].lower()


def _ini_get_var(line: str) -> Optional[tuple[str, str]]:
    for index, character in enumerate(line):
        if character in ('=', ' ', '\t'):
            key = line[:index].lower()
            value = line[index + 1:].lstrip('= \t')
            return key, value
    return None
