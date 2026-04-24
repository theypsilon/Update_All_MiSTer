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
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional, Callable, Iterable

from update_all.config import Config
from update_all.constants import FILE_MiSTer_ini
from update_all.file_system import FileSystem
from update_all.logger import Logger
from update_all.os_utils import OsUtils
from update_all.other import GenericProvider, terminal_size, calculate_overscan
from update_all.ui_engine import EffectChain, ProcessKeyResult, UiSection
from update_all.ui_engine_dialog_application import UiDialogDrawer, _NavigationState
from update_all.ui_model_utilities import Key

FIFO_PATH = '/dev/MiSTer_cmd'
_DEFAULT_DIALOG_TIMEOUT_MS = 300
_CONFIRM_TIMEOUT_SECONDS = 5
_DEFAULT_NTSC_VIDEO_MODE = '640,30,60,70,240,4,4,14,12587'
_DEFAULT_PAL_VIDEO_MODE = '640,30,60,70,288,6,4,14,12587'


@dataclass(frozen=True)
class MisterVideoIniState:
    video_mode: Optional[str]
    vga_scaler: bool
    direct_video: bool


class MisterVideoModeService:
    def __init__(self, logger: Logger, file_system: FileSystem, config_provider: GenericProvider[Config], os_utils: OsUtils):
        self._logger = logger
        self._file_system = file_system
        self._config_provider = config_provider
        self._os_utils = os_utils
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
            current_contents = self._file_system.read_file_contents(ini_path) if self._file_system.is_file(ini_path) else ''
            new_contents = save_video_mode_to_contents(current_contents, self._unsaved_kept_mode)
            self._file_system.write_file_contents(ini_path, new_contents)
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


class MisterVideoModeMenu(UiSection):
    def __init__(self, drawer: UiDialogDrawer, service: MisterVideoModeService, data: Dict[str, Any], monotonic: Callable[[], float] = time.monotonic):
        self._drawer = drawer
        self._service = service
        self._data = data
        self._modes = _video_modes_from_data(data)
        self._text_lines = _text_lines_from_data(data, [''])
        self._back_entry_index = len(self._modes)
        self._monotonic = monotonic
        self._menu_state = _NavigationState(self._back_entry_index + 1, 2)
        self._menu_state.reset_position(self._selected_index(self._service.current_mode()))

    def process_key(self) -> Optional[ProcessKeyResult]:
        initial_mode = self._service.current_mode()
        current_mode = initial_mode

        while True:
            key = self._paint_menu(current_mode)
            if key == Key.UP:
                self._menu_state.navigate_up()
            elif key == Key.DOWN:
                self._menu_state.navigate_down()
            elif key == Key.LEFT:
                self._menu_state.navigate_left()
            elif key == Key.RIGHT:
                self._menu_state.navigate_right()
            elif key == 27:
                if current_mode == initial_mode:
                    return self._back_effect()

                if initial_mode is not None:
                    self._service.apply_mode(initial_mode)
                    current_mode = initial_mode
                    self._menu_state.reset_position(self._selected_index(current_mode))
                    self._show_message(
                        self._data.get('header', 'Video Mode'),
                        ['Initial video mode restored.'],
                    )
                else:
                    return self._back_effect()
            elif key == Key.ENTER:
                if self._menu_state.lateral_position() == 1 or self._menu_state.position() == self._back_entry_index:
                    return self._back_effect()

                selected_mode = self._modes[self._menu_state.position()][1]
                if selected_mode == current_mode:
                    self._show_message(
                        self._data.get('header', 'Video Mode'),
                        ['The selected video mode is already active.'],
                    )
                    continue

                previous_mode = current_mode
                if not self._service.apply_mode(selected_mode):
                    self._show_message(
                        self._data.get('header', 'Video Mode'),
                        ['Could not apply the selected video mode.'],
                    )
                    current_mode = self._service.current_mode()
                    self._menu_state.reset_position(self._selected_index(current_mode))
                    continue

                if self._confirm_keep_mode(selected_mode, previous_mode):
                    current_mode = selected_mode
                    self._service.remember_unsaved_kept_mode(selected_mode, previous_mode)
                else:
                    current_mode = self._service.current_mode()
                self._menu_state.reset_position(self._selected_index(current_mode))

    def reset(self) -> None:
        self._menu_state.reset_lateral_position()
        self._menu_state.reset_position(self._selected_index(self._service.current_mode()))

    def clear(self) -> None:
        self._drawer.clear()

    def _paint_menu(self, current_mode: Optional[str]) -> int:
        header = self._data.get('header', 'Video Mode')
        self._drawer.start({'header': header})
        self._drawer.add_text_line(f'Current: {_mode_label(current_mode, self._modes)}')
        for text_line in self._text_lines:
            self._drawer.add_text_line(text_line)

        for index, (title, mode_value) in enumerate(self._modes):
            info = 'Active' if mode_value == current_mode else ''
            self._drawer.add_menu_entry(title, info, index == self._menu_state.position())
        self._drawer.add_menu_entry('Back', '', self._menu_state.position() == self._back_entry_index)

        self._drawer.add_action('Select', self._menu_state.lateral_position() == 0)
        self._drawer.add_action('Back', self._menu_state.lateral_position() == 1)
        self._drawer.show_overscan_preview()
        return self._drawer.paint()

    def _confirm_keep_mode(self, candidate_mode: str, previous_mode: Optional[str]) -> bool:
        state = _NavigationState(0, 2)
        state.reset_lateral_position(1)
        try:
            deadline = self._monotonic() + _CONFIRM_TIMEOUT_SECONDS
            while True:
                now = self._monotonic()
                remaining_seconds = deadline - now
                remaining = max(0, int(remaining_seconds + 0.999))
                if remaining <= 0:
                    if previous_mode is not None:
                        self._service.apply_mode(previous_mode)
                    return False

                self._drawer.clear()
                self._drawer.start({'header': 'Keep This Video Mode?'})
                self._drawer.add_text_line(f'{_mode_label(candidate_mode, self._modes)} is active.')
                self._drawer.add_text_line(f'It will revert in {remaining} seconds unless you keep it.')
                self._drawer.add_action('Keep', state.lateral_position() == 0)
                self._drawer.add_action('Revert', state.lateral_position() == 1)
                self._drawer.show_overscan_preview()
                self._drawer.set_key_timeout(_countdown_timeout_ms(remaining_seconds, remaining))

                key = self._drawer.paint()
                if key == Key.LEFT:
                    state.navigate_left()
                elif key == Key.RIGHT:
                    state.navigate_right()
                elif key == Key.ENTER:
                    if state.lateral_position() == 0:
                        return True
                    if previous_mode is not None:
                        self._service.apply_mode(previous_mode)
                    return False
                elif key == 27:
                    if previous_mode is not None:
                        self._service.apply_mode(previous_mode)
                    return False
        finally:
            self._drawer.set_key_timeout(_DEFAULT_DIALOG_TIMEOUT_MS)

    def _show_message(self, header: str, text_lines: list[str]) -> None:
        self._drawer.set_key_timeout(-1)
        try:
            while True:
                self._drawer.clear()
                self._drawer.start({'header': header})
                for line in text_lines:
                    self._drawer.add_text_line(line)
                self._drawer.add_action('Ok', True)
                key = self._drawer.paint()
                if key == Key.ENTER or key == 27:
                    return
        finally:
            self._drawer.set_key_timeout(_DEFAULT_DIALOG_TIMEOUT_MS)

    def _back_effect(self) -> EffectChain:
        return EffectChain(self._data.get('effects', [{'type': 'navigate', 'target': 'back'}]))

    def _selected_index(self, current_mode: Optional[str]) -> int:
        for index, (_, mode_value) in enumerate(self._modes):
            if mode_value == current_mode:
                return index
        return 0


class MisterVideoAdjustMenu(UiSection):
    def __init__(self, drawer: UiDialogDrawer, service: MisterVideoModeService, data: Dict[str, Any]):
        self._drawer = drawer
        self._service = service
        self._data = data
        self._text_lines = _text_lines_from_data(data, [''])

    def process_key(self) -> Optional[ProcessKeyResult]:
        original_mode = self._service.current_mode()
        if original_mode is None:
            self._show_message(self._data.get('header', 'Adjust'), ['No active video mode could be detected.'])
            return self._back_effect()

        try:
            parts = parse_mode(original_mode)
        except ValueError:
            self._show_message(self._data.get('header', 'Adjust'), ['The current video mode could not be adjusted.'])
            return self._back_effect()

        while True:
            key = self._paint_adjust_screen(parts)
            if key == Key.LEFT:
                parts = self._try_shift(parts, 1, 3)
            elif key == Key.RIGHT:
                parts = self._try_shift(parts, 3, 1)
            elif key == Key.UP:
                parts = self._try_shift(parts, 5, 7)
            elif key == Key.DOWN:
                parts = self._try_shift(parts, 7, 5)
            elif key in (27, 8, 127, curses.KEY_BACKSPACE, 263):
                if format_mode(parts) == original_mode:
                    return self._back_effect()
                if self._service.apply_mode(original_mode):
                    parts = parse_mode(original_mode)
                self._show_message(self._data.get('header', 'Adjust'), ['Original position restored.'])
            elif key == Key.ENTER:
                candidate_mode = format_mode(parts)
                if candidate_mode != original_mode:
                    if self._confirm_keep_adjusted_mode(candidate_mode, original_mode):
                        self._service.remember_unsaved_kept_mode(candidate_mode, original_mode)
                return self._back_effect()

    def reset(self) -> None:
        pass

    def clear(self) -> None:
        self._drawer.clear()

    def _paint_adjust_screen(self, parts: list[int]) -> int:
        header = self._data.get('header', 'Adjust')
        self._drawer.start({'header': header})
        for text_line in self._text_lines:
            self._drawer.add_text_line(text_line)
        self._drawer.add_text_line(' ')
        self._drawer.add_text_line(f'hfp={parts[1]}  hs={parts[2]}  hbp={parts[3]}')
        self._drawer.add_text_line(f'vfp={parts[5]}  vs={parts[6]}  vbp={parts[7]}')
        self._drawer.add_action('Done', True)
        self._drawer.show_overscan_preview()
        return self._drawer.paint()

    def _try_shift(self, parts: list[int], increment_index: int, decrement_index: int) -> list[int]:
        if parts[decrement_index] <= 0:
            return parts

        candidate = list(parts)
        candidate[increment_index] += 1
        candidate[decrement_index] -= 1
        candidate_mode = format_mode(candidate)
        if self._service.apply_mode(candidate_mode):
            return candidate
        return parts

    def _confirm_keep_adjusted_mode(self, candidate_mode: str, original_mode: str) -> bool:
        state = _NavigationState(0, 2)
        state.reset_lateral_position(1)
        self._drawer.set_key_timeout(-1)
        try:
            while True:
                self._drawer.clear()
                self._drawer.start({'header': 'Keep This Adjustment?'})
                self._drawer.add_text_line('The adjusted position is active.')
                self._drawer.add_action('Keep', state.lateral_position() == 0)
                self._drawer.add_action('Revert', state.lateral_position() == 1)
                self._drawer.show_overscan_preview()

                key = self._drawer.paint()
                if key == Key.LEFT:
                    state.navigate_left()
                elif key == Key.RIGHT:
                    state.navigate_right()
                elif key == Key.ENTER:
                    if state.lateral_position() == 0:
                        return True
                    self._service.apply_mode(original_mode)
                    return False
                elif key == 27:
                    self._service.apply_mode(original_mode)
                    return False
        finally:
            self._drawer.set_key_timeout(_DEFAULT_DIALOG_TIMEOUT_MS)

    def _show_message(self, header: str, text_lines: list[str]) -> None:
        self._drawer.set_key_timeout(-1)
        try:
            while True:
                self._drawer.clear()
                self._drawer.start({'header': header})
                for line in text_lines:
                    self._drawer.add_text_line(line)
                self._drawer.add_action('Ok', True)
                key = self._drawer.paint()
                if key == Key.ENTER or key == 27:
                    return
        finally:
            self._drawer.set_key_timeout(_DEFAULT_DIALOG_TIMEOUT_MS)

    def _back_effect(self) -> EffectChain:
        return EffectChain(self._data.get('effects', [{'type': 'navigate', 'target': 'back'}]))


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


def format_mode(parts: list[int]) -> str:
    return ','.join(str(part) for part in parts)


def _countdown_timeout_ms(remaining_seconds: float, displayed_remaining: int) -> int:
    seconds_until_next_display_value = remaining_seconds - (displayed_remaining - 1)
    return max(1, min(1000, int(seconds_until_next_display_value * 1000)))


def save_video_mode_to_contents(contents: str, mode_str: str) -> str:
    new_lines = []
    current_section = None
    menu_section_found = False
    video_mode_written = False
    vga_scaler_written = False

    for raw_line in contents.splitlines():
        line = _ini_parse_line(raw_line)
        section = _ini_get_section(line) if line else None
        if section is not None:
            if current_section == 'menu' and not video_mode_written:
                new_lines.append(f'video_mode={mode_str}')
                video_mode_written = True
            if current_section == 'menu' and not vga_scaler_written:
                new_lines.append('vga_scaler=1')
                vga_scaler_written = True

            current_section = section
            if current_section == 'menu':
                menu_section_found = True

            new_lines.append(raw_line)
            continue

        if current_section == 'menu':
            variable = _ini_get_var(line) if line else None
            if variable is not None:
                if variable[0] == 'video_mode':
                    if not video_mode_written:
                        new_lines.append(f'video_mode={mode_str}')
                        video_mode_written = True
                    continue
                if variable[0] == 'vga_scaler':
                    if not vga_scaler_written:
                        new_lines.append('vga_scaler=1')
                        vga_scaler_written = True
                    continue
                if variable[0] == 'direct_video':
                    continue

        new_lines.append(raw_line)

    if current_section == 'menu' and not video_mode_written:
        new_lines.append(f'video_mode={mode_str}')
        video_mode_written = True
    if current_section == 'menu' and not vga_scaler_written:
        new_lines.append('vga_scaler=1')
        vga_scaler_written = True

    if not menu_section_found:
        if new_lines:
            new_lines.append('')
        new_lines.append('[menu]')
        new_lines.append(f'video_mode={mode_str}')
        new_lines.append('vga_scaler=1')

    return '\n'.join(new_lines).rstrip() + '\n'


def _video_modes_from_data(data: Dict[str, Any]) -> list[tuple[str, str]]:
    raw_modes = data.get('resolutions', [])
    modes = [_parse_video_mode(raw_mode) for raw_mode in raw_modes]
    if not modes:
        raise ValueError('mister_video_mode requires at least one video mode.')
    return modes


def _text_lines_from_data(data: Dict[str, Any], default_text_lines: list[str]) -> list[str]:
    raw_text = data.get('text', default_text_lines)
    if isinstance(raw_text, str):
        return [raw_text]
    if isinstance(raw_text, Iterable):
        return [str(text_line) for text_line in raw_text]
    raise ValueError(f'Invalid video mode text definition: {raw_text}')


def _parse_video_mode(raw_mode: Any) -> tuple[str, str]:
    if isinstance(raw_mode, dict):
        name = raw_mode.get('name')
        video_mode = raw_mode.get('video_mode')
    elif isinstance(raw_mode, Iterable) and not isinstance(raw_mode, str):
        name, video_mode = raw_mode
    else:
        raise ValueError(f'Invalid video mode definition: {raw_mode}')

    if name is None or video_mode is None:
        raise ValueError(f'Invalid video mode definition: {raw_mode}')

    return str(name), str(video_mode)


def _mode_label(mode_str: Optional[str], modes: list[tuple[str, str]] = None) -> str:
    if mode_str is None:
        return 'Unknown'

    modes = [] if modes is None else modes
    for label, value in modes:
        if value == mode_str:
            return label.partition(' ')[2] or label

    try:
        parts = parse_mode(mode_str)
        return f'{parts[0]}x{parts[4]}'
    except ValueError:
        return mode_str


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
