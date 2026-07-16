#!/usr/bin/env python3
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

# This module is intentionally isolated from the rest of the application.
# It is executed through the special `update_all.pyz --chip-id-linker` command path,
# before normal Update All services are imported. Keep imports limited to the
# standard library or tiny dependency-free helpers; do not import SettingsScreen,
# UpdateAllService, RetroAccount, downloader services, or UI modules here.

import argparse
import fcntl
import hashlib
import mmap
import multiprocessing
import os
import queue
import shlex
import signal
import struct
import subprocess
import sys
import time
from typing import NamedTuple, Optional

from update_all.logger import FileLoggerDecorator
from update_all.other import current_update_all_archive_path


FIFO_PATH = '/dev/MiSTer_cmd'

CHIP_ID_BASE = 0xFF200000
CHIP_ID_REG_SPAN = 0x20
CHIP_ID_HPS_FPGAMGR_BASE = 0xFF706000
CHIP_ID_HPS_RSTMGR_BASE = 0xFFD05000
CHIP_ID_HPS_REG_SPAN = 0x1000
CHIP_ID_FPGAMGR_STAT_OFFSET = 0x00
CHIP_ID_FPGAMGR_GPIO_EXT_PORTA_OFFSET = 0x850
CHIP_ID_RSTMGR_BRG_MOD_RESET_OFFSET = 0x1C
CHIP_ID_FPGAMGR_MODE_MASK = 0x7
CHIP_ID_FPGAMGR_MODE_USERMODE = 0x4
CHIP_ID_FPGAMGR_INITDONE_MASK = 0x4
CHIP_ID_REG_MAGIC = 0x00
CHIP_ID_REG_VERSION = 0x04
CHIP_ID_REG_STATUS = 0x08
CHIP_ID_REG_ID_LO = 0x0C
CHIP_ID_REG_ID_HI = 0x10
CHIP_ID_REG_ID_XOR = 0x14
CHIP_ID_REG_DISPLAY_CONTROL = 0x1C
CHIP_ID_STATUS_READY = 1 << 0
CHIP_ID_STATUS_ERROR = 1 << 1
CHIP_ID_DISPLAY_CONTROL_BLANK = 1 << 0
CHIP_ID_EXPECTED_MAGIC = 0x43484944
CHIP_ID_SUPPORTED_VERSION_MAJOR = 1
CHIP_ID_MAGIC_TIMEOUT_SECONDS = 5.0
CHIP_ID_READY_TIMEOUT_SECONDS = 1.0
CHIP_ID_READS = 8
CHIP_ID_POLL_INTERVAL_SECONDS = 0.001
CHIP_ID_CORE_READY_TIMEOUT_SECONDS = 10.0
CHIP_ID_CORE_READY_POLL_INTERVAL_SECONDS = 0.1
CHIP_ID_FIRMWARE_CORE_RESTART_TIMEOUT_SECONDS = 10.0
CHIP_ID_FIRMWARE_CORE_RESTART_POLL_INTERVAL_SECONDS = 0.05
CHIP_ID_HPS_FPGA_READY_TIMEOUT_SECONDS = 10.0
CHIP_ID_HPS_FPGA_READY_POLL_INTERVAL_SECONDS = 0.05
CHIP_ID_HPS_FPGA_READY_STABLE_SECONDS = 0.2
CHIP_ID_MENU_RESTORE_DELAY_SECONDS = 0.5
CHIP_ID_MENU_CORE_NAME_PATH = '/tmp/CORENAME'
CHIP_ID_MENU_CORE_NAME = 'MENU'
CHIP_ID_MENU_CORE_READY_TIMEOUT_SECONDS = 10.0
CHIP_ID_MENU_CORE_READY_POLL_INTERVAL_SECONDS = 0.1
CHIP_ID_READER_PROCESS_TIMEOUT_SECONDS = 20.0
CHIP_ID_DISPLAY_CONTROL_PROCESS_TIMEOUT_SECONDS = 2.0
CHIP_ID_RELAUNCH_SCRIPT_PATH = '/tmp/script'
CHIP_ID_RELAUNCH_SCRIPT_STARTED_PATH = '/tmp/update_all_chipid_relaunch_started'
CHIP_ID_RELAUNCH_SCRIPT_START_TIMEOUT_SECONDS = 5.0
CHIP_ID_UPDATE_ALL_PYZ_RELATIVE_PATH = '.config/update_all/update_all.pyz'
CHIP_ID_RELAUNCH_RUN_PYZ_PATH = '/tmp/update_all_chipid.pyz'
CHIP_ID_RELAUNCH_ENV_EXCLUDED_NAMES = frozenset(('COMMAND', 'UPDATE_ALL_CHIP_ID_RESULT', 'PWD', 'OLDPWD', 'SHLVL', '_'))
CHIP_ID_F9_CONSOLE_TTY = '1'
CHIP_ID_SCRIPT_CONSOLE_TTY = '3'
CHIP_ID_RELAUNCH_TTY = '7'
CHIP_ID_RELAUNCH_SCRIPT_DRAIN_SECONDS = 2.0
CHIP_ID_RELAUNCH_SCRIPT_TERM_WAIT_SECONDS = 1.0
CHIP_ID_RELAUNCH_SCRIPT_KILL_WAIT_SECONDS = 1.0
CHIP_ID_RELAUNCH_AFTER_SCRIPT_CLEAR_SETTLE_SECONDS = 0.1
CHIP_ID_RELAUNCH_DISPLAY_BLANK_DELAY_SECONDS = 0.25
CHIP_ID_RELAUNCH_CONSOLE_CLOSE_SETTLE_SECONDS = 0.1
CHIP_ID_RELAUNCH_MENU_SETTLE_SECONDS = 0.2
CHIP_ID_CONSOLE_OPEN_TIMEOUT_SECONDS = 5.0
CHIP_ID_CURSOR_BLINK_PATH = '/sys/class/graphics/fbcon/cursor_blink'
CHIP_ID_UINPUT_PATH = '/dev/uinput'
CHIP_ID_UINPUT_DEVICE_NAME = b'Zaparoo'
CHIP_ID_UINPUT_CREATE_DELAY_SECONDS = 0.2
CHIP_ID_UINPUT_KEY_PRESS_DELAY_SECONDS = 0.04
CHIP_ID_KEY_F9 = 67
CHIP_ID_KEY_F12 = 88
CHIP_ID_KEY_MAX = 0x2FF
CHIP_ID_EV_SYN = 0x00
CHIP_ID_EV_KEY = 0x01
CHIP_ID_SYN_REPORT = 0
CHIP_ID_BUS_USB = 0x03
CHIP_ID_UI_DEV_CREATE = 0x5501
CHIP_ID_UI_DEV_DESTROY = 0x5502
CHIP_ID_UI_SET_EVBIT = 0x40045564
CHIP_ID_UI_SET_KEYBIT = 0x40045565

UPDATE_ALL_ENV_COMMAND = 'COMMAND'
UPDATE_ALL_COMMAND_SHOW_CHIP_ID_RESULT = 'SHOW_CHIP_ID_RESULT'
UPDATE_ALL_ENV_CHIP_ID_RESULT = 'UPDATE_ALL_CHIP_ID_RESULT'


class HpsFpgaStatus(NamedTuple):
    fpga_mode: int
    init_done: bool
    bridge_reset: int

    def is_lw_bridge_safe(self) -> bool:
        return (
            self.fpga_mode == CHIP_ID_FPGAMGR_MODE_USERMODE
            and self.init_done
            and self.bridge_reset == 0
        )


def run_chip_id_linker_command(logger: FileLoggerDecorator, argv=None) -> int:
    args = _parse_args(argv)
    _validate_args(args)
    if not args.restore_after_relaunch and not args.blank_display:
        _reset_chip_id_log(args.log)
    logger.set_logfile(args.log, append=True, eager=True)
    linker = ChipIdLinker(logger, args.log)
    _write_worker_startup_marker(args.startup_marker, linker)
    return linker.run(args)


def _parse_args(argv):
    parser = argparse.ArgumentParser(description='Update All FPGA ID linker launcher')
    parser.add_argument('--restore-after-relaunch', action='store_true')
    parser.add_argument('--restore-menu-after-relaunch', action='store_true')
    parser.add_argument('--blank-display', action='store_true')
    parser.add_argument('--extract-only', action='store_true')
    parser.add_argument('--rbf')
    parser.add_argument('--update-all-dir')
    parser.add_argument('--startup-marker')
    parser.add_argument('--log', required=True)
    return parser.parse_args(argv)


def _validate_args(args) -> None:
    if args.restore_after_relaunch or args.blank_display:
        return

    missing = []
    if args.rbf is None:
        missing.append('--rbf')
    if not args.extract_only and args.update_all_dir is None:
        missing.append('--update-all-dir')
    if missing:
        raise SystemExit(f'Missing required arguments: {", ".join(missing)}')


class ChipIdLinker:
    def __init__(self, logger: FileLoggerDecorator, log_path: str):
        self._logger = logger
        self.log_path = log_path

    def debug(self, message: str) -> None:
        self._logger.debug(message)

    def run(self, args) -> int:
        if args.restore_after_relaunch:
            _restore_display_after_update_all_relaunch(self, args.restore_menu_after_relaunch)
            return 0

        if args.blank_display:
            _blank_chip_id_core_display(self)
            return 0

        if args.extract_only:
            print(_extract_chip_id_without_relaunch(args.rbf, self))
            return 0

        _run_detached_chip_id_extraction(self, args.rbf, args.update_all_dir)
        return 0


def _extract_chip_id_from_core(rbf_path: str, linker: ChipIdLinker) -> tuple[str, bool]:
    result = 'FAILURE_UNKNOWN'
    chip_id_core_was_loaded = False
    linker.debug('_extract_chip_id_from_core: started')
    try:
        rbf_md5 = _chip_id_rbf_md5(rbf_path, linker)

        _prepare_display_before_chip_id_core_load(linker)
        previous_core_name_mtime_ns = _file_mtime_ns(CHIP_ID_MENU_CORE_NAME_PATH)
        linker.debug('_extract_chip_id_from_core: loading Linker core')
        try:
            _load_chip_id_core(rbf_path, rbf_md5, linker)
        except Exception as e:
            linker.debug(f'_extract_chip_id_from_core: Linker core load failed: {type(e).__name__}: {str(e)}')
            return 'FAILURE_LOAD_CORE_FIFO', chip_id_core_was_loaded
        chip_id_core_was_loaded = True
        linker.debug('_extract_chip_id_from_core: Linker core load command sent')

        restart_result = _wait_for_firmware_core_restart_after_load(previous_core_name_mtime_ns, linker)
        if restart_result is not None:
            linker.debug(f'_extract_chip_id_from_core: final result before bridge read: {restart_result}')
            return restart_result, chip_id_core_was_loaded

        bridge_ready_result = _wait_for_hps_fpga_lw_bridge_ready_after_core_load(linker)
        if bridge_ready_result is not None:
            linker.debug(f'_extract_chip_id_from_core: final result before bridge read: {bridge_ready_result}')
            return bridge_ready_result, chip_id_core_was_loaded

        linker.debug('_extract_chip_id_from_core: reading chip ID from memory')
        result = _read_chip_id_from_memory_after_core_load(linker)
        linker.debug(f'_extract_chip_id_from_core: memory read result: {result}')
        return result, chip_id_core_was_loaded
    except Exception as e:
        result = f'FAILURE_{type(e).__name__.upper()}'
        linker.debug(f'_extract_chip_id_from_core: raised: {type(e).__name__}: {str(e)}')
        return result, chip_id_core_was_loaded


def _combine_chip_id_result_with_restore_result(result: str, restore_result: str) -> str:
    return restore_result if not result.startswith('FAILURE_') else f'{result}_{restore_result}'


def _extract_chip_id_without_relaunch(rbf_path: str, linker: ChipIdLinker) -> str:
    result, chip_id_core_was_loaded = _extract_chip_id_from_core(rbf_path, linker)
    if chip_id_core_was_loaded:
        linker.debug('_extract_chip_id_without_relaunch: restoring menu core')
        restore_result = _restore_menu_after_chip_id(linker)
        if restore_result is not None:
            linker.debug(f'_extract_chip_id_without_relaunch: menu restore result: {restore_result}')
            result = _combine_chip_id_result_with_restore_result(result, restore_result)
            linker.debug(f'_extract_chip_id_without_relaunch: final result after restore failure: {result}')
    return result


def _run_detached_chip_id_extraction(linker: ChipIdLinker, rbf_path: str, update_all_dir: str) -> None:
    linker.debug('_run_detached_chip_id_extraction: started')
    result, chip_id_core_was_loaded = _extract_chip_id_from_core(rbf_path, linker)
    restore_result = None
    if not chip_id_core_was_loaded:
        linker.debug('_run_detached_chip_id_extraction: Linker core was not loaded, relaunching Update All from current menu')
        relaunch_result = _relaunch_update_all_from_scripts_menu(
            linker,
            update_all_dir,
            require_script_start_confirmation=True,
            chip_id_result=result,
        )
        if relaunch_result is not None:
            linker.debug(f'_run_detached_chip_id_extraction: relaunch result without core load: {relaunch_result}')
        return

    linker.debug(f'_run_detached_chip_id_extraction: final result: {result}')

    linker.debug('_run_detached_chip_id_extraction: relaunching Update All directly from Linker core')
    relaunch_result = _relaunch_update_all_from_scripts_menu(
        linker,
        update_all_dir,
        restore_menu_after_relaunch=True,
        require_script_start_confirmation=True,
        chip_id_result=result,
    )
    if relaunch_result is None:
        linker.debug('_run_detached_chip_id_extraction: direct relaunch started')
        return

    linker.debug(
        f'_run_detached_chip_id_extraction: direct relaunch failed, falling back to menu restore: {relaunch_result}'
    )
    linker.debug('_run_detached_chip_id_extraction: restoring menu core')
    restore_result = _restore_menu_after_chip_id(linker)
    if restore_result is not None:
        linker.debug(f'_run_detached_chip_id_extraction: menu restore result: {restore_result}')
        result = _combine_chip_id_result_with_restore_result(result, restore_result)
        linker.debug(f'_run_detached_chip_id_extraction: final result after fallback: {result}')
        return

    linker.debug('_run_detached_chip_id_extraction: menu restore command sent')
    relaunch_result = _relaunch_update_all_from_scripts_menu(
        linker,
        update_all_dir,
        chip_id_result=result,
    )
    if relaunch_result is not None:
        linker.debug(f'_run_detached_chip_id_extraction: fallback relaunch result: {relaunch_result}')


def _chip_id_rbf_md5(rbf_path: str, linker: ChipIdLinker) -> Optional[str]:
    linker.debug(f'_load_chip_id_core: resolved RBF path: {rbf_path}')
    try:
        with open(rbf_path, 'rb') as rbf_file:
            rbf_md5 = hashlib.md5(rbf_file.read()).hexdigest()
        linker.debug(f'_load_chip_id_core: RBF md5: {rbf_md5}')
        return rbf_md5
    except Exception as e:
        linker.debug(f'_load_chip_id_core: could not compute RBF md5: {type(e).__name__}: {str(e)}')
        return None


def _load_chip_id_core(rbf_path: str, rbf_md5: Optional[str], linker: ChipIdLinker) -> None:
    linker.debug(f'_load_chip_id_core: resolved RBF path: {rbf_path}')
    linker.debug(f'_load_chip_id_core: RBF md5: {rbf_md5 or "UNKNOWN"}')
    _load_core(rbf_path, linker)


def _restore_menu_after_chip_id(linker: ChipIdLinker) -> Optional[str]:
    try:
        _load_core('menu.rbf', linker)
        linker.debug(f'_restore_menu_after_chip_id: sleeping {CHIP_ID_MENU_RESTORE_DELAY_SECONDS}s after menu load')
        time.sleep(CHIP_ID_MENU_RESTORE_DELAY_SECONDS)
        menu_ready_result = _wait_for_menu_core_after_restore(linker)
        if menu_ready_result is not None:
            return menu_ready_result
        return None
    except Exception as e:
        linker.debug(f'_restore_menu_after_chip_id: failed: {type(e).__name__}: {str(e)}')
        return 'FAILURE_RESTORE_MENU_FIFO'


def _load_core(rbf_path: str, linker: ChipIdLinker) -> None:
    linker.debug(f'_load_core: opening FIFO {FIFO_PATH} for {rbf_path}')
    fd = os.open(FIFO_PATH, os.O_WRONLY | os.O_NONBLOCK)
    try:
        command = f'load_core {rbf_path}'
        linker.debug(f'_load_core: writing command: {command}')
        os.write(fd, command.encode())
        linker.debug(f'_load_core: command write completed: {command}')
    finally:
        os.close(fd)
        linker.debug(f'_load_core: closed FIFO fd for {rbf_path}')


def _is_firmware_fifo_available(linker: ChipIdLinker) -> bool:
    linker.debug(f'_is_firmware_fifo_available: probing FIFO {FIFO_PATH}')
    try:
        fd = os.open(FIFO_PATH, os.O_WRONLY | os.O_NONBLOCK)
        os.close(fd)
        linker.debug('_is_firmware_fifo_available: FIFO has a reader')
        return True
    except OSError as e:
        linker.debug(f'_is_firmware_fifo_available: FIFO unavailable: {type(e).__name__}: {str(e)}')
        return False


def _wait_for_firmware_core_restart_after_load(previous_core_name_mtime_ns: Optional[int], linker: ChipIdLinker) -> Optional[str]:
    deadline = time.monotonic() + CHIP_ID_FIRMWARE_CORE_RESTART_TIMEOUT_SECONDS
    last_core_name_mtime_ns = previous_core_name_mtime_ns
    linker.debug(
        '_wait_for_firmware_core_restart_after_load: '
        f'waiting up to {CHIP_ID_FIRMWARE_CORE_RESTART_TIMEOUT_SECONDS}s for {CHIP_ID_MENU_CORE_NAME_PATH} rewrite; '
        f'previous_mtime_ns={previous_core_name_mtime_ns}'
    )

    while True:
        core_name_mtime_ns = _file_mtime_ns(CHIP_ID_MENU_CORE_NAME_PATH)
        if core_name_mtime_ns != last_core_name_mtime_ns:
            linker.debug(
                '_wait_for_firmware_core_restart_after_load: '
                f'{CHIP_ID_MENU_CORE_NAME_PATH} mtime changed from {last_core_name_mtime_ns} to {core_name_mtime_ns}'
            )
            last_core_name_mtime_ns = core_name_mtime_ns

        if core_name_mtime_ns is not None and core_name_mtime_ns != previous_core_name_mtime_ns:
            linker.debug('_wait_for_firmware_core_restart_after_load: firmware core restart observed')
            return None

        if time.monotonic() >= deadline:
            linker.debug(
                '_wait_for_firmware_core_restart_after_load: timed out waiting for firmware core restart marker'
            )
            return 'FAILURE_FIRMWARE_CORE_RESTART_TIMEOUT'

        time.sleep(CHIP_ID_FIRMWARE_CORE_RESTART_POLL_INTERVAL_SECONDS)


def _wait_for_hps_fpga_lw_bridge_ready_after_core_load(linker: ChipIdLinker) -> Optional[str]:
    deadline = time.monotonic() + CHIP_ID_HPS_FPGA_READY_TIMEOUT_SECONDS
    stable_since = None
    last_status = None
    linker.debug(
        '_wait_for_hps_fpga_lw_bridge_ready_after_core_load: '
        f'waiting up to {CHIP_ID_HPS_FPGA_READY_TIMEOUT_SECONDS}s for FPGA user mode and released HPS bridges'
    )

    while True:
        try:
            status = _read_hps_fpga_status()
        except Exception as e:
            linker.debug(
                '_wait_for_hps_fpga_lw_bridge_ready_after_core_load: '
                f'failed to read HPS FPGA status: {type(e).__name__}: {str(e)}'
            )
            return 'FAILURE_HPS_FPGA_STATUS_READ'

        if status != last_status:
            linker.debug(f'_wait_for_hps_fpga_lw_bridge_ready_after_core_load: status {status}')
            last_status = status

        now = time.monotonic()
        if status.is_lw_bridge_safe():
            if stable_since is None:
                stable_since = now
                linker.debug('_wait_for_hps_fpga_lw_bridge_ready_after_core_load: bridge-safe status observed')
            elif now - stable_since >= CHIP_ID_HPS_FPGA_READY_STABLE_SECONDS:
                linker.debug(
                    '_wait_for_hps_fpga_lw_bridge_ready_after_core_load: '
                    f'bridge-safe status stable for {CHIP_ID_HPS_FPGA_READY_STABLE_SECONDS}s'
                )
                return None
        else:
            stable_since = None

        if now >= deadline:
            linker.debug(
                '_wait_for_hps_fpga_lw_bridge_ready_after_core_load: '
                f'timed out with status {status}'
            )
            return 'FAILURE_HPS_FPGA_LW_BRIDGE_NOT_READY'

        time.sleep(CHIP_ID_HPS_FPGA_READY_POLL_INTERVAL_SECONDS)


def _read_hps_fpga_status() -> HpsFpgaStatus:
    fd = -1
    fpgamgr = None
    rstmgr = None
    try:
        fd = os.open('/dev/mem', os.O_RDONLY | os.O_SYNC)
        fpgamgr = mmap.mmap(fd, CHIP_ID_HPS_REG_SPAN, mmap.MAP_SHARED, mmap.PROT_READ, offset=CHIP_ID_HPS_FPGAMGR_BASE)
        rstmgr = mmap.mmap(fd, CHIP_ID_HPS_REG_SPAN, mmap.MAP_SHARED, mmap.PROT_READ, offset=CHIP_ID_HPS_RSTMGR_BASE)

        fpgamgr_stat = _read_chip_id_reg(fpgamgr, 0, CHIP_ID_FPGAMGR_STAT_OFFSET)
        fpgamgr_gpio_ext_porta = _read_chip_id_reg(fpgamgr, 0, CHIP_ID_FPGAMGR_GPIO_EXT_PORTA_OFFSET)
        bridge_reset = _read_chip_id_reg(rstmgr, 0, CHIP_ID_RSTMGR_BRG_MOD_RESET_OFFSET)
        return HpsFpgaStatus(
            fpga_mode=fpgamgr_stat & CHIP_ID_FPGAMGR_MODE_MASK,
            init_done=bool(fpgamgr_gpio_ext_porta & CHIP_ID_FPGAMGR_INITDONE_MASK),
            bridge_reset=bridge_reset,
        )
    finally:
        if rstmgr is not None:
            rstmgr.close()
        if fpgamgr is not None:
            fpgamgr.close()
        if fd >= 0:
            os.close(fd)


def _file_mtime_ns(path: str) -> Optional[int]:
    try:
        return os.stat(path).st_mtime_ns
    except OSError:
        return None


def _read_chip_id_from_memory_after_core_load(linker: ChipIdLinker) -> str:
    deadline = time.monotonic() + CHIP_ID_CORE_READY_TIMEOUT_SECONDS
    last_result = 'FAILURE_CORE_NOT_READY'
    attempt = 1

    linker.debug(
        f'_read_chip_id_from_memory_after_core_load: waiting up to {CHIP_ID_CORE_READY_TIMEOUT_SECONDS}s for Linker core readiness'
    )
    while True:
        linker.debug(f'_read_chip_id_from_memory_after_core_load: attempt {attempt}')
        result = _read_chip_id_from_memory(linker)
        if not _is_transient_chip_id_read_failure(result):
            return result

        last_result = result
        if time.monotonic() >= deadline:
            linker.debug(f'_read_chip_id_from_memory_after_core_load: timeout with last result {last_result}')
            return last_result

        bridge_ready_result = _wait_for_hps_fpga_lw_bridge_ready_after_core_load(linker)
        if bridge_ready_result is not None:
            return bridge_ready_result

        if not _is_firmware_fifo_available(linker):
            linker.debug('_read_chip_id_from_memory_after_core_load: firmware FIFO disappeared while waiting')
            return 'FAILURE_FIRMWARE_EXITED_AFTER_LOAD'

        time.sleep(CHIP_ID_CORE_READY_POLL_INTERVAL_SECONDS)
        attempt += 1


def _is_transient_chip_id_read_failure(result: str) -> bool:
    return result == 'FAILURE_MEM_SIGBUS'


def _blank_chip_id_core_display(linker: ChipIdLinker) -> None:
    linker.debug('_blank_chip_id_core_display: requesting black display')
    result = _write_chip_id_display_control(CHIP_ID_DISPLAY_CONTROL_BLANK, linker)
    if result is not None:
        linker.debug(f'_blank_chip_id_core_display: failed without blocking relaunch: {result}')


def _write_chip_id_display_control(value: int, linker: ChipIdLinker) -> Optional[str]:
    linker.debug('_write_chip_id_display_control: starting isolated writer process')
    ctx = multiprocessing.get_context('fork')
    result_queue = ctx.Queue()
    process = ctx.Process(target=_write_chip_id_display_control_process, args=(result_queue, value, linker))
    process.start()
    process.join(CHIP_ID_DISPLAY_CONTROL_PROCESS_TIMEOUT_SECONDS)

    if process.is_alive():
        linker.debug('_write_chip_id_display_control: writer process timed out')
        process.terminate()
        process.join(1)
        return 'FAILURE_DISPLAY_CONTROL_TIMEOUT'

    if process.exitcode == 0:
        try:
            result = result_queue.get_nowait()
            if result is None:
                linker.debug('_write_chip_id_display_control: writer process completed')
            else:
                linker.debug(f'_write_chip_id_display_control: writer process returned {result}')
            return result
        except queue.Empty:
            linker.debug('_write_chip_id_display_control: writer process exited without result')
            return 'FAILURE_DISPLAY_CONTROL_NO_RESULT'

    if process.exitcode == -signal.SIGBUS:
        linker.debug('_write_chip_id_display_control: writer process died with SIGBUS')
        return 'FAILURE_DISPLAY_CONTROL_SIGBUS'

    if process.exitcode is not None and process.exitcode < 0:
        signal_number = -process.exitcode
        linker.debug(f'_write_chip_id_display_control: writer process died with signal {signal_number}')
        return f'FAILURE_DISPLAY_CONTROL_SIGNAL_{signal_number}'

    linker.debug(f'_write_chip_id_display_control: writer process exited with code {process.exitcode}')
    return f'FAILURE_DISPLAY_CONTROL_EXIT_{process.exitcode}'


def _write_chip_id_display_control_process(result_queue, value: int, linker: ChipIdLinker) -> None:
    result_queue.put(_write_chip_id_display_control_direct(value, linker))


def _write_chip_id_display_control_direct(value: int, linker: ChipIdLinker) -> Optional[str]:
    fd = -1
    memory = None
    try:
        linker.debug(f'_write_chip_id_display_control_direct: opening /dev/mem at base 0x{CHIP_ID_BASE:08x}')
        fd = os.open('/dev/mem', os.O_RDWR | os.O_SYNC)
        memory = mmap.mmap(
            fd,
            CHIP_ID_REG_SPAN,
            mmap.MAP_SHARED,
            mmap.PROT_READ | mmap.PROT_WRITE,
            offset=CHIP_ID_BASE
        )
        linker.debug(f'_write_chip_id_display_control_direct: mapped {CHIP_ID_REG_SPAN} bytes')
        return _write_chip_id_display_control_to_registers(memory, 0, value, linker)
    except OSError as e:
        linker.debug(f'_write_chip_id_display_control_direct: OSError: errno={e.errno}, message={str(e)}')
        return f'FAILURE_DISPLAY_CONTROL_MEM_{e.errno or "ERROR"}'
    except ValueError as e:
        linker.debug(f'_write_chip_id_display_control_direct: ValueError while mapping: {str(e)}')
        return 'FAILURE_DISPLAY_CONTROL_MEM_MAP'
    finally:
        if memory is not None:
            memory.close()
            linker.debug('_write_chip_id_display_control_direct: closed memory map')
        if fd >= 0:
            os.close(fd)
            linker.debug('_write_chip_id_display_control_direct: closed /dev/mem fd')


def _write_chip_id_display_control_to_registers(memory, map_delta: int, value: int, linker: ChipIdLinker) -> Optional[str]:
    magic = _read_chip_id_reg(memory, map_delta, CHIP_ID_REG_MAGIC)
    if magic != CHIP_ID_EXPECTED_MAGIC:
        linker.debug(f'_write_chip_id_display_control_to_registers: bad MAGIC 0x{magic:08x}')
        return f'FAILURE_DISPLAY_CONTROL_BAD_MAGIC_{magic:08x}'

    struct.pack_into('<I', memory, map_delta + CHIP_ID_REG_DISPLAY_CONTROL, value)
    linker.debug(f'_write_chip_id_display_control_to_registers: wrote 0x{value:08x}')
    return None


def _read_chip_id_from_memory(linker: ChipIdLinker) -> str:
    linker.debug('_read_chip_id_from_memory: starting isolated reader process')
    ctx = multiprocessing.get_context('fork')
    result_queue = ctx.Queue()
    process = ctx.Process(target=_read_chip_id_from_memory_process, args=(result_queue, linker))
    process.start()
    process.join(CHIP_ID_READER_PROCESS_TIMEOUT_SECONDS)

    if process.is_alive():
        linker.debug('_read_chip_id_from_memory: reader process timed out')
        process.terminate()
        process.join(1)
        return 'FAILURE_MEM_READER_TIMEOUT'

    if process.exitcode == 0:
        try:
            result = result_queue.get_nowait()
            linker.debug(f'_read_chip_id_from_memory: reader process returned {result}')
            return result
        except queue.Empty:
            linker.debug('_read_chip_id_from_memory: reader process exited without result')
            return 'FAILURE_MEM_READER_NO_RESULT'

    if process.exitcode == -signal.SIGBUS:
        linker.debug('_read_chip_id_from_memory: reader process died with SIGBUS')
        return 'FAILURE_MEM_SIGBUS'

    if process.exitcode is not None and process.exitcode < 0:
        signal_number = -process.exitcode
        linker.debug(f'_read_chip_id_from_memory: reader process died with signal {signal_number}')
        return f'FAILURE_MEM_SIGNAL_{signal_number}'

    linker.debug(f'_read_chip_id_from_memory: reader process exited with code {process.exitcode}')
    return f'FAILURE_MEM_READER_EXIT_{process.exitcode}'


def _read_chip_id_from_memory_process(result_queue, linker: ChipIdLinker) -> None:
    result_queue.put(_read_chip_id_from_memory_direct(linker))


def _read_chip_id_from_memory_direct(linker: ChipIdLinker) -> str:
    fd = -1
    memory = None
    try:
        linker.debug(f'_read_chip_id_from_memory_direct: opening /dev/mem at base 0x{CHIP_ID_BASE:08x}')
        fd = os.open('/dev/mem', os.O_RDONLY | os.O_SYNC)
        memory = mmap.mmap(fd, CHIP_ID_REG_SPAN, mmap.MAP_SHARED, mmap.PROT_READ, offset=CHIP_ID_BASE)
        linker.debug(f'_read_chip_id_from_memory_direct: mapped {CHIP_ID_REG_SPAN} bytes')
        return _read_chip_id_from_registers(memory, 0, linker)
    except OSError as e:
        linker.debug(f'_read_chip_id_from_memory_direct: OSError: errno={e.errno}, message={str(e)}')
        return f'FAILURE_MEM_{e.errno or "ERROR"}'
    except ValueError as e:
        linker.debug(f'_read_chip_id_from_memory_direct: ValueError while mapping: {str(e)}')
        return 'FAILURE_MEM_MAP'
    finally:
        if memory is not None:
            memory.close()
            linker.debug('_read_chip_id_from_memory_direct: closed memory map')
        if fd >= 0:
            os.close(fd)
            linker.debug('_read_chip_id_from_memory_direct: closed /dev/mem fd')


def _read_chip_id_from_registers(memory, map_delta: int, linker: ChipIdLinker) -> str:
    linker.debug('_read_chip_id_from_registers: waiting for MAGIC')
    magic = _wait_for_chip_id_magic(memory, map_delta, linker)
    if magic != CHIP_ID_EXPECTED_MAGIC:
        linker.debug(f'_read_chip_id_from_registers: bad MAGIC 0x{magic:08x}')
        return f'FAILURE_BAD_MAGIC_{magic:08x}'

    version = _read_chip_id_reg(memory, map_delta, CHIP_ID_REG_VERSION)
    linker.debug(f'_read_chip_id_from_registers: VERSION 0x{version:08x}')
    if (version >> 16) != CHIP_ID_SUPPORTED_VERSION_MAJOR:
        linker.debug(f'_read_chip_id_from_registers: unsupported VERSION 0x{version:08x}')
        return f'FAILURE_UNSUPPORTED_VERSION_{version:08x}'

    linker.debug('_read_chip_id_from_registers: waiting for READY')
    ready_error = _wait_for_chip_id_ready(memory, map_delta, linker)
    if ready_error is not None:
        linker.debug(f'_read_chip_id_from_registers: READY wait failed: {ready_error}')
        return ready_error

    linker.debug('_read_chip_id_from_registers: validating repeated reads')
    return _validate_chip_id_reads(memory, map_delta, linker)


def _wait_for_chip_id_magic(memory, map_delta: int, linker: ChipIdLinker) -> int:
    deadline = time.monotonic() + CHIP_ID_MAGIC_TIMEOUT_SECONDS
    magic = 0

    while True:
        magic = _read_chip_id_reg(memory, map_delta, CHIP_ID_REG_MAGIC)
        if magic == CHIP_ID_EXPECTED_MAGIC or time.monotonic() >= deadline:
            linker.debug(f'_wait_for_chip_id_magic: returning MAGIC 0x{magic:08x}')
            return magic
        time.sleep(0.05)


def _wait_for_chip_id_ready(memory, map_delta: int, linker: ChipIdLinker) -> Optional[str]:
    deadline = time.monotonic() + CHIP_ID_READY_TIMEOUT_SECONDS
    status = 0

    while True:
        status = _read_chip_id_reg(memory, map_delta, CHIP_ID_REG_STATUS)
        if status & CHIP_ID_STATUS_ERROR:
            linker.debug(f'_wait_for_chip_id_ready: ERROR status 0x{status:08x}')
            return f'FAILURE_CORE_ERROR_BEFORE_READY_{status:08x}'
        if status & CHIP_ID_STATUS_READY:
            linker.debug(f'_wait_for_chip_id_ready: READY status 0x{status:08x}')
            return None
        if time.monotonic() >= deadline:
            linker.debug(f'_wait_for_chip_id_ready: timeout with status 0x{status:08x}')
            return f'FAILURE_READY_TIMEOUT_{status:08x}'
        time.sleep(CHIP_ID_POLL_INTERVAL_SECONDS)


def _validate_chip_id_reads(memory, map_delta: int, linker: ChipIdLinker) -> str:
    previous = None

    for index in range(CHIP_ID_READS):
        status = _read_chip_id_reg(memory, map_delta, CHIP_ID_REG_STATUS)
        if status & CHIP_ID_STATUS_ERROR:
            linker.debug(f'_validate_chip_id_reads: read {index}: ERROR status 0x{status:08x}')
            return f'FAILURE_CORE_ERROR_DURING_READBACK_{status:08x}'
        if not (status & CHIP_ID_STATUS_READY):
            linker.debug(f'_validate_chip_id_reads: read {index}: READY deasserted, status 0x{status:08x}')
            return f'FAILURE_READY_DEASSERTED_{status:08x}'

        id_lo = _read_chip_id_reg(memory, map_delta, CHIP_ID_REG_ID_LO)
        id_hi = _read_chip_id_reg(memory, map_delta, CHIP_ID_REG_ID_HI)
        id_xor = _read_chip_id_reg(memory, map_delta, CHIP_ID_REG_ID_XOR)
        expected_xor = id_lo ^ id_hi ^ CHIP_ID_EXPECTED_MAGIC
        linker.debug(
        f'_validate_chip_id_reads: read {index}: hi=0x{id_hi:08x}, lo=0x{id_lo:08x}, xor=0x{id_xor:08x}, expected_xor=0x{expected_xor:08x}'
        )

        if id_xor != expected_xor:
            linker.debug(f'_validate_chip_id_reads: read {index}: ID_XOR mismatch')
            return f'FAILURE_ID_XOR_MISMATCH_{id_xor:08x}_{expected_xor:08x}'
        if (id_hi == 0 and id_lo == 0) or (id_hi == 0xFFFFFFFF and id_lo == 0xFFFFFFFF):
            linker.debug(f'_validate_chip_id_reads: read {index}: invalid chip ID')
            return f'FAILURE_INVALID_CHIP_ID_{id_hi:08x}{id_lo:08x}'

        current = (id_hi, id_lo)
        if previous is not None and current != previous:
            linker.debug(f'_validate_chip_id_reads: read {index}: inconsistent read')
            return 'FAILURE_INCONSISTENT_READS'
        previous = current

    id_hi, id_lo = previous
    linker.debug(f'_validate_chip_id_reads: stable chip ID {id_hi:08x}{id_lo:08x}')
    return f'{id_hi:08x}{id_lo:08x}'


def _read_chip_id_reg(memory, map_delta: int, offset: int) -> int:
    return struct.unpack_from('<I', memory, map_delta + offset)[0]


def _relaunch_update_all_from_scripts_menu(
    linker: ChipIdLinker,
    update_all_dir: str,
    restore_menu_after_relaunch: bool = False,
    require_script_start_confirmation: bool = False,
    chip_id_result: str = '',
) -> Optional[str]:
    try:
        clear_result = _clear_visible_script_processes(linker)
        if clear_result is not None:
            return clear_result

        start_marker_path = CHIP_ID_RELAUNCH_SCRIPT_STARTED_PATH if require_script_start_confirmation else None
        if start_marker_path is not None:
            clear_marker_result = _clear_relaunch_script_start_marker(start_marker_path, linker)
            if clear_marker_result is not None:
                return clear_marker_result

        linker.debug(
            f'_relaunch_update_all_from_scripts_menu: sleeping {CHIP_ID_RELAUNCH_AFTER_SCRIPT_CLEAR_SETTLE_SECONDS}s after stale script cleanup'
        )
        time.sleep(CHIP_ID_RELAUNCH_AFTER_SCRIPT_CLEAR_SETTLE_SECONDS)
        linker.debug(f'_relaunch_update_all_from_scripts_menu: Update All dir: {update_all_dir}')
        _reset_script_tty(linker)
        _open_script_console(linker)
        _switch_to_relaunch_tty(linker)
        _write_update_all_relaunch_script(
            linker,
            CHIP_ID_RELAUNCH_SCRIPT_PATH,
            update_all_dir,
            restore_menu_after_relaunch,
            start_marker_path,
            chip_id_result,
        )
        process = subprocess.Popen([
            'setsid',
            '/sbin/agetty',
            '-a',
            'root',
            '-l',
            CHIP_ID_RELAUNCH_SCRIPT_PATH,
            '--nohostname',
            '-L',
            f'tty{CHIP_ID_RELAUNCH_TTY}',
            'linux',
        ])
        linker.debug(f'_relaunch_update_all_from_scripts_menu: started agetty pid {process.pid}')
        if start_marker_path is not None:
            start_result = _wait_for_relaunch_script_start(process, start_marker_path, linker)
            if start_result is not None:
                _terminate_relaunch_process(process, linker)
                return start_result
        return None
    except Exception as e:
        linker.debug(f'_relaunch_update_all_from_scripts_menu: failed: {type(e).__name__}: {str(e)}')
        return f'FAILURE_RELAUNCH_{type(e).__name__.upper()}'


def _clear_relaunch_script_start_marker(marker_path: str, linker: ChipIdLinker) -> Optional[str]:
    try:
        os.remove(marker_path)
        linker.debug(f'_clear_relaunch_script_start_marker: removed stale marker {marker_path}')
        return None
    except FileNotFoundError:
        linker.debug(f'_clear_relaunch_script_start_marker: no stale marker at {marker_path}')
        return None
    except Exception as e:
        linker.debug(f'_clear_relaunch_script_start_marker: failed: {type(e).__name__}: {str(e)}')
        return 'FAILURE_RELAUNCH_MARKER_CLEAR'


def _wait_for_relaunch_script_start(process, marker_path: str, linker: ChipIdLinker) -> Optional[str]:
    deadline = time.monotonic() + CHIP_ID_RELAUNCH_SCRIPT_START_TIMEOUT_SECONDS
    linker.debug(
        f'_wait_for_relaunch_script_start: waiting up to {CHIP_ID_RELAUNCH_SCRIPT_START_TIMEOUT_SECONDS}s for {marker_path}'
    )
    while True:
        if os.path.exists(marker_path):
            linker.debug(f'_wait_for_relaunch_script_start: marker found at {marker_path}')
            return None

        returncode = process.poll()
        if returncode is not None:
            linker.debug(f'_wait_for_relaunch_script_start: agetty exited before marker with {returncode}')
            return f'FAILURE_RELAUNCH_PROCESS_EXIT_{returncode}'

        if time.monotonic() >= deadline:
            linker.debug('_wait_for_relaunch_script_start: timed out waiting for script start marker')
            return 'FAILURE_RELAUNCH_SCRIPT_START_TIMEOUT'

        time.sleep(0.05)


def _terminate_relaunch_process(process, linker: ChipIdLinker) -> None:
    try:
        if process.poll() is not None:
            linker.debug(f'_terminate_relaunch_process: process already exited with {process.returncode}')
            return
    except Exception as e:
        linker.debug(f'_terminate_relaunch_process: poll failed: {type(e).__name__}: {str(e)}')

    try:
        linker.debug(f'_terminate_relaunch_process: terminating pid {process.pid}')
        process.terminate()
        process.wait(CHIP_ID_RELAUNCH_SCRIPT_TERM_WAIT_SECONDS)
        linker.debug('_terminate_relaunch_process: process terminated')
        return
    except subprocess.TimeoutExpired:
        linker.debug('_terminate_relaunch_process: terminate timed out, killing process')
    except ProcessLookupError:
        linker.debug('_terminate_relaunch_process: process already gone')
        return
    except Exception as e:
        linker.debug(f'_terminate_relaunch_process: terminate failed: {type(e).__name__}: {str(e)}')

    try:
        process.kill()
        process.wait(CHIP_ID_RELAUNCH_SCRIPT_KILL_WAIT_SECONDS)
        linker.debug('_terminate_relaunch_process: process killed')
    except Exception as e:
        linker.debug(f'_terminate_relaunch_process: kill failed: {type(e).__name__}: {str(e)}')


def _open_script_console(linker: ChipIdLinker) -> None:
    linker.debug('_open_script_console: started')
    keyboard_fd = _create_uinput_keyboard(linker)
    try:
        try:
            _switch_to_open_console_tty(linker)
        except Exception as e:
            linker.debug(f'_open_script_console: initial chvt failed: {type(e).__name__}: {str(e)}')

        deadline = time.monotonic() + CHIP_ID_CONSOLE_OPEN_TIMEOUT_SECONDS
        backoff = 0.05
        while time.monotonic() < deadline:
            linker.debug('_open_script_console: requesting framebuffer console')
            _press_f9_for_console(keyboard_fd, linker)
            time.sleep(backoff)

            tty = _active_tty(linker)
            linker.debug(f'_open_script_console: active tty after F9 is {tty}')
            if tty == f'tty{CHIP_ID_F9_CONSOLE_TTY}':
                linker.debug('_open_script_console: F9 console confirmed')
                _wait_for_framebuffer_ready(max(0, deadline - time.monotonic()), linker)
                if CHIP_ID_SCRIPT_CONSOLE_TTY != CHIP_ID_F9_CONSOLE_TTY:
                    try:
                        _switch_to_open_console_tty(linker)
                    except Exception as e:
                        linker.debug(f'_open_script_console: target chvt failed: {type(e).__name__}: {str(e)}')
                if _is_tty_console_ready(CHIP_ID_SCRIPT_CONSOLE_TTY, linker):
                    linker.debug('_open_script_console: script console ready')
                    return

            backoff = min(backoff * 1.5, 0.5)
    finally:
        _destroy_uinput_keyboard(keyboard_fd, linker)

    tty = _active_tty(linker)
    raise TimeoutError(f'timeout waiting for script console on tty{CHIP_ID_SCRIPT_CONSOLE_TTY}; current tty is {tty}')


def _is_script_console_ready(linker: ChipIdLinker) -> bool:
    return _is_tty_console_ready(CHIP_ID_RELAUNCH_TTY, linker)


def _is_tty_console_ready(tty_id: str, linker: ChipIdLinker) -> bool:
    tty = _active_tty(linker)
    framebuffer_ready = os.path.exists('/dev/fb0') and os.path.exists('/sys/class/graphics/fbcon/cursor_blink')
    ready = tty == f'tty{tty_id}' and framebuffer_ready
    linker.debug(f'_is_tty_console_ready: target=tty{tty_id}, tty={tty}, framebuffer_ready={framebuffer_ready}, ready={ready}')
    return ready


def _wait_for_framebuffer_ready(timeout_seconds: float, linker: ChipIdLinker) -> None:
    deadline = time.monotonic() + timeout_seconds
    while True:
        framebuffer_ready = os.path.exists('/dev/fb0') and os.path.exists('/sys/class/graphics/fbcon/cursor_blink')
        if framebuffer_ready:
            linker.debug('_wait_for_framebuffer_ready: framebuffer ready')
            return
        if time.monotonic() >= deadline:
            raise TimeoutError('timeout waiting for framebuffer readiness')
        time.sleep(0.05)


def _active_tty(linker: ChipIdLinker) -> str:
    try:
        with open('/sys/devices/virtual/tty/tty0/active') as active_tty_file:
            return active_tty_file.read().strip()
    except Exception as e:
        linker.debug(f'_active_tty: failed: {type(e).__name__}: {str(e)}')
        return ''


def _wait_for_menu_core_after_restore(linker: ChipIdLinker) -> Optional[str]:
    deadline = time.monotonic() + CHIP_ID_MENU_CORE_READY_TIMEOUT_SECONDS
    last_core_name = ''
    linker.debug(f'_wait_for_menu_core_after_restore: waiting for {CHIP_ID_MENU_CORE_NAME_PATH}={CHIP_ID_MENU_CORE_NAME}')
    while True:
        last_core_name = _active_core_name(linker)
        if last_core_name == CHIP_ID_MENU_CORE_NAME:
            linker.debug('_wait_for_menu_core_after_restore: menu core is active')
            return None

        if time.monotonic() >= deadline:
            linker.debug(f'_wait_for_menu_core_after_restore: timeout with active core {last_core_name or "UNKNOWN"}')
            return f'FAILURE_RESTORE_MENU_CORE_TIMEOUT_{last_core_name or "UNKNOWN"}'

        time.sleep(CHIP_ID_MENU_CORE_READY_POLL_INTERVAL_SECONDS)


def _active_core_name(linker: ChipIdLinker) -> str:
    try:
        with open(CHIP_ID_MENU_CORE_NAME_PATH) as core_name_file:
            core_name = core_name_file.read().strip()
        linker.debug(f'_active_core_name: {core_name}')
        return core_name
    except Exception as e:
        linker.debug(f'_active_core_name: failed: {type(e).__name__}: {str(e)}')
        return ''


def _prepare_display_before_chip_id_core_load(linker: ChipIdLinker) -> None:
    linker.debug('_prepare_display_before_chip_id_core_load: started')
    for tty_id in (CHIP_ID_RELAUNCH_TTY, CHIP_ID_SCRIPT_CONSOLE_TTY, CHIP_ID_F9_CONSOLE_TTY):
        _reset_tty(tty_id, '_prepare_display_before_chip_id_core_load', linker)


def _create_uinput_keyboard(linker: ChipIdLinker) -> int:
    linker.debug(f'_create_uinput_keyboard: opening {CHIP_ID_UINPUT_PATH}')
    fd = os.open(CHIP_ID_UINPUT_PATH, os.O_WRONLY | os.O_NONBLOCK)
    created = False
    try:
        fcntl.ioctl(fd, CHIP_ID_UI_SET_EVBIT, CHIP_ID_EV_KEY)
        for key_code in range(CHIP_ID_KEY_MAX + 1):
            fcntl.ioctl(fd, CHIP_ID_UI_SET_KEYBIT, key_code)
        linker.debug(f'_create_uinput_keyboard: registered EV_KEY and keys 0..{CHIP_ID_KEY_MAX}')

        user_device = struct.pack(
            '80sHHHHI',
            CHIP_ID_UINPUT_DEVICE_NAME,
            CHIP_ID_BUS_USB,
            0x4711,
            0x0815,
            1,
            0,
        ) + bytes(64 * 4 * 4)
        os.write(fd, user_device)
        fcntl.ioctl(fd, CHIP_ID_UI_DEV_CREATE)
        created = True
        linker.debug(f'_create_uinput_keyboard: created virtual keyboard, sleeping {CHIP_ID_UINPUT_CREATE_DELAY_SECONDS}s')
        time.sleep(CHIP_ID_UINPUT_CREATE_DELAY_SECONDS)
        _log_uinput_keyboard_presence(linker)
        return fd
    except Exception:
        if created:
            try:
                fcntl.ioctl(fd, CHIP_ID_UI_DEV_DESTROY)
            except Exception:
                pass
        os.close(fd)
        raise


def _log_uinput_keyboard_presence(linker: ChipIdLinker) -> None:
    try:
        device_name = CHIP_ID_UINPUT_DEVICE_NAME.decode()
        with open('/proc/bus/input/devices') as devices_file:
            present = device_name in devices_file.read()
        linker.debug(f'_create_uinput_keyboard: /proc/bus/input/devices contains {device_name}: {present}')
    except Exception as e:
        linker.debug(f'_create_uinput_keyboard: input device presence check failed: {type(e).__name__}: {str(e)}')


def _destroy_uinput_keyboard(fd: int, linker: ChipIdLinker) -> None:
    try:
        fcntl.ioctl(fd, CHIP_ID_UI_DEV_DESTROY)
        linker.debug('_destroy_uinput_keyboard: destroyed virtual keyboard')
    except Exception as e:
        linker.debug(f'_destroy_uinput_keyboard: destroy failed: {type(e).__name__}: {str(e)}')
    try:
        os.close(fd)
        linker.debug('_destroy_uinput_keyboard: closed virtual keyboard fd')
    except Exception as e:
        linker.debug(f'_destroy_uinput_keyboard: close failed: {type(e).__name__}: {str(e)}')


def _press_f9_for_console(fd: int, linker: ChipIdLinker) -> None:
    _press_key(fd, CHIP_ID_KEY_F9, '_press_f9_for_console', linker)


def _press_f12_for_menu(fd: int, linker: ChipIdLinker) -> None:
    _press_key(fd, CHIP_ID_KEY_F12, '_press_f12_for_menu', linker)


def _press_key(fd: int, key_code: int, log_label: str, linker: ChipIdLinker) -> None:
    _set_key(fd, key_code, 1)
    time.sleep(CHIP_ID_UINPUT_KEY_PRESS_DELAY_SECONDS)
    _set_key(fd, key_code, 0)
    linker.debug(f'{log_label}: key down/up sent')


def _set_key(fd: int, key_code: int, value: int) -> None:
    _send_uinput_event(fd, CHIP_ID_EV_KEY, key_code, value)
    _send_uinput_event(fd, CHIP_ID_EV_SYN, CHIP_ID_SYN_REPORT, 0)


def _send_uinput_event(fd: int, event_type: int, code: int, value: int) -> None:
    os.write(fd, struct.pack('llHHi', 0, 0, event_type, code, value))


def _clear_visible_script_processes(linker: ChipIdLinker) -> Optional[str]:
    linker.debug('_clear_visible_script_processes: started')
    if _wait_for_no_visible_script_processes(CHIP_ID_RELAUNCH_SCRIPT_DRAIN_SECONDS, linker):
        return None

    processes = _visible_script_processes(linker)
    if not processes:
        return None

    linker.debug(f'_clear_visible_script_processes: terminating {len(processes)} stale /tmp/script process(es)')
    _signal_visible_script_processes(processes, signal.SIGTERM, linker)
    if _wait_for_no_visible_script_processes(CHIP_ID_RELAUNCH_SCRIPT_TERM_WAIT_SECONDS, linker):
        return None

    processes = _visible_script_processes(linker)
    linker.debug(f'_clear_visible_script_processes: killing {len(processes)} stale /tmp/script process(es)')
    _signal_visible_script_processes(processes, signal.SIGKILL, linker)
    if _wait_for_no_visible_script_processes(CHIP_ID_RELAUNCH_SCRIPT_KILL_WAIT_SECONDS, linker):
        return None

    processes = _visible_script_processes(linker)
    for pid, line in processes:
        linker.debug(f'_clear_visible_script_processes: still active pid={pid}: {line}')
    return 'FAILURE_RELAUNCH_SCRIPT_ACTIVE'


def _wait_for_no_visible_script_processes(timeout_seconds: float, linker: ChipIdLinker) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while True:
        processes = _visible_script_processes(linker)
        if not processes:
            linker.debug('_wait_for_no_visible_script_processes: no active /tmp/script process')
            return True

        if time.monotonic() >= deadline:
            linker.debug(f'_wait_for_no_visible_script_processes: timeout with {len(processes)} active /tmp/script process(es)')
            return False

        time.sleep(0.1)


def _signal_visible_script_processes(processes, sig: int, linker: ChipIdLinker) -> None:
    for pid, line in processes:
        try:
            linker.debug(f'_signal_visible_script_processes: sending signal {sig} to pid={pid}: {line}')
            os.kill(pid, sig)
        except ProcessLookupError:
            linker.debug(f'_signal_visible_script_processes: pid={pid} already exited')
        except Exception as e:
            linker.debug(f'_signal_visible_script_processes: failed for pid={pid}: {type(e).__name__}: {str(e)}')


def _reset_script_tty(linker: ChipIdLinker) -> None:
    _reset_tty(CHIP_ID_RELAUNCH_TTY, '_reset_script_tty', linker)


def _reset_tty(tty_id: str, log_label: str, linker: ChipIdLinker) -> None:
    tty_path = f'/dev/tty{tty_id}'
    linker.debug(f'{log_label}: resetting {tty_path}')
    fd = -1
    try:
        fd = os.open(tty_path, os.O_RDWR | os.O_NONBLOCK)
        with os.fdopen(os.dup(fd), 'rb', buffering=0) as tty:
            process = subprocess.run(
                ['stty', 'sane'],
                stdin=tty,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                timeout=2,
                check=False,
            )
        linker.debug(f'{log_label}: stty sane exited with {process.returncode} for {tty_path}')
    except Exception as e:
        linker.debug(f'{log_label}: stty sane failed for {tty_path}: {type(e).__name__}: {str(e)}')

    try:
        if fd < 0:
            fd = os.open(tty_path, os.O_RDWR | os.O_NONBLOCK)
        os.write(fd, b'\x1bc\x1b[2J\x1b[H\x1b[?25h')
        linker.debug(f'{log_label}: terminal reset sequence written to {tty_path}')
    except Exception as e:
        linker.debug(f'{log_label}: terminal reset sequence failed for {tty_path}: {type(e).__name__}: {str(e)}')
    finally:
        if fd >= 0:
            try:
                os.close(fd)
            except Exception:
                pass


def _visible_script_processes(linker: ChipIdLinker):
    try:
        process = subprocess.run(
            ['ps', 'ax'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=2,
        )
        processes = []
        current_pid = os.getpid()
        for line in process.stdout.splitlines():
            if '/tmp/script' not in line:
                continue
            parts = line.split(None, 1)
            if not parts:
                continue
            try:
                pid = int(parts[0])
            except ValueError:
                continue
            if pid == current_pid:
                continue
            processes.append((pid, line.strip()))
        linker.debug(f'_visible_script_processes: found {len(processes)} /tmp/script process(es)')
        for pid, line in processes:
            linker.debug(f'_visible_script_processes: pid={pid}: {line}')
        return processes
    except Exception as e:
        linker.debug(f'_visible_script_processes: failed: {type(e).__name__}: {str(e)}')
        return []


def _switch_to_open_console_tty(linker: ChipIdLinker) -> None:
    _switch_to_tty(CHIP_ID_SCRIPT_CONSOLE_TTY, '_switch_to_open_console_tty', linker)


def _switch_to_relaunch_tty(linker: ChipIdLinker) -> None:
    _switch_to_tty(CHIP_ID_RELAUNCH_TTY, '_switch_to_relaunch_tty', linker)


def _switch_to_tty(tty_id: str, log_label: str, linker: ChipIdLinker) -> None:
    linker.debug(f'{log_label}: chvt {tty_id}')
    subprocess.run(['chvt', tty_id], check=True, timeout=2)
    linker.debug(f'{log_label}: chvt {tty_id} completed')


def _restore_display_after_update_all_relaunch(linker: ChipIdLinker, restore_menu_after_relaunch: bool = False) -> Optional[str]:
    linker.debug('_restore_display_after_update_all_relaunch: started')
    keyboard_fd = None
    try:
        keyboard_fd = _create_uinput_keyboard(linker)
        _press_f12_for_menu(keyboard_fd, linker)
        linker.debug(
            f'_restore_display_after_update_all_relaunch: sleeping {CHIP_ID_RELAUNCH_CONSOLE_CLOSE_SETTLE_SECONDS}s after F12'
        )
        time.sleep(CHIP_ID_RELAUNCH_CONSOLE_CLOSE_SETTLE_SECONDS)
    except Exception as e:
        linker.debug(
            f'_restore_display_after_update_all_relaunch: F12 restore failed: {type(e).__name__}: {str(e)}'
        )
    finally:
        if keyboard_fd is not None:
            _destroy_uinput_keyboard(keyboard_fd, linker)

    for tty_id in (CHIP_ID_F9_CONSOLE_TTY, CHIP_ID_RELAUNCH_TTY):
        _reset_tty(tty_id, '_restore_display_after_update_all_relaunch', linker)
    _restore_cursor_blink(linker)

    if restore_menu_after_relaunch:
        restore_result = _restore_menu_after_chip_id(linker)
        if restore_result is not None:
            linker.debug(f'_restore_display_after_update_all_relaunch: menu restore result: {restore_result}')
            return restore_result

    linker.debug(
        f'_restore_display_after_update_all_relaunch: sleeping {CHIP_ID_RELAUNCH_MENU_SETTLE_SECONDS}s after display restore'
    )
    time.sleep(CHIP_ID_RELAUNCH_MENU_SETTLE_SECONDS)
    linker.debug('_restore_display_after_update_all_relaunch: completed')
    return None


def _restore_cursor_blink(linker: ChipIdLinker) -> None:
    try:
        with open(CHIP_ID_CURSOR_BLINK_PATH, 'w') as cursor_blink:
            cursor_blink.write('1\n')
        linker.debug(f'_restore_cursor_blink: wrote {CHIP_ID_CURSOR_BLINK_PATH}')
    except Exception as e:
        linker.debug(f'_restore_cursor_blink: failed: {type(e).__name__}: {str(e)}')


def _write_update_all_relaunch_script(
    linker: ChipIdLinker,
    script_path: str,
    update_all_dir: str,
    restore_menu_after_relaunch: bool = False,
    start_marker_path: Optional[str] = None,
    chip_id_result: str = '',
) -> None:
    update_all_pyz_path = _update_all_pyz_path(update_all_dir)
    python_executable = sys.executable or '/usr/bin/python3'
    linker.debug(f'_write_update_all_relaunch_script: writing {script_path}')
    shell_log_path = shlex.quote(linker.log_path)
    forwarded_environment = _shell_export_forwarded_environment()
    start_marker_command = ''
    if start_marker_path is not None:
        shell_start_marker_path = shlex.quote(start_marker_path)
        start_marker_command = f'''mark_update_all_relaunch_started() {{
  if printf "%s\\n" "$$" > {shell_start_marker_path} 2>/dev/null; then
    log_update_all_relaunch "started marker written {shell_start_marker_path}"
  else
    log_update_all_relaunch "started marker write failed {shell_start_marker_path}"
  fi
}}
mark_update_all_relaunch_started
'''
    restore_command = (
        f'{shlex.quote(python_executable)} {shlex.quote(update_all_pyz_path)} '
        f'--chip-id-linker '
        f'--restore-after-relaunch'
        f'{" --restore-menu-after-relaunch" if restore_menu_after_relaunch else ""}'
        f' --log {shell_log_path}'
    )
    launcher = f'''#!/bin/bash
{forwarded_environment}
export LC_ALL="${{LC_ALL:-en_US.UTF-8}}"
export HOME="${{HOME:-/root}}"
export LESSKEY="${{LESSKEY:-/media/fat/linux/lesskey}}"
export {UPDATE_ALL_ENV_COMMAND}={UPDATE_ALL_COMMAND_SHOW_CHIP_ID_RESULT}
export {UPDATE_ALL_ENV_CHIP_ID_RESULT}={shlex.quote(chip_id_result)}
UPDATE_ALL_DIR={shlex.quote(update_all_dir)}
UPDATE_ALL_PYZ={shlex.quote(update_all_pyz_path)}
UPDATE_ALL_RUN_PYZ={shlex.quote(CHIP_ID_RELAUNCH_RUN_PYZ_PATH)}
UPDATE_ALL_PYTHON={shlex.quote(python_executable)}
CHIP_ID_DISPLAY_BLANK_SCHEDULED=0
RESTORE_UPDATE_ALL_DISPLAY_DONE=0
log_update_all_relaunch() {{
  printf "%s relaunch_script: %s\\n" "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> {shell_log_path} 2>/dev/null || true
}}
{start_marker_command}reset_update_all_tty() {{
  stty sane 2>/dev/null || true
  stty echo icanon isig iexten opost onlcr 2>/dev/null || true
  printf '\\033[?25h'
}}
prepare_update_all_tty() {{
  reset_update_all_tty
  printf '\\033c\\033[?25h'
}}
restore_update_all_display() {{
  if [ "$RESTORE_UPDATE_ALL_DISPLAY_DONE" = "1" ]; then
    return
  fi
  RESTORE_UPDATE_ALL_DISPLAY_DONE=1
  reset_update_all_tty
  log_update_all_relaunch "restoring MiSTer display"
  {restore_command} >> {shell_log_path} 2>&1 || log_update_all_relaunch "display restore command failed with $?"
}}
copy_update_all_pyz() {{
  cp "$UPDATE_ALL_PYZ" "$UPDATE_ALL_RUN_PYZ" || return 126
  chmod +x "$UPDATE_ALL_RUN_PYZ" 2>/dev/null || true
  return 0
}}
schedule_chip_id_display_blank() {{
  if [ "$CHIP_ID_DISPLAY_BLANK_SCHEDULED" = "1" ]; then
    return
  fi
  CHIP_ID_DISPLAY_BLANK_SCHEDULED=1
  (
    sleep {CHIP_ID_RELAUNCH_DISPLAY_BLANK_DELAY_SECONDS}
    log_update_all_relaunch "blanking Linker display"
    "$UPDATE_ALL_PYTHON" "$UPDATE_ALL_PYZ" --chip-id-linker --blank-display --log {shell_log_path} >> {shell_log_path} 2>&1 || log_update_all_relaunch "Linker display blank failed with $?"
  ) &
}}
run_update_all_pyz() {{
  copy_update_all_pyz || return $?

  log_update_all_relaunch "running pyz $UPDATE_ALL_RUN_PYZ"
  schedule_chip_id_display_blank
  "$UPDATE_ALL_PYTHON" "$UPDATE_ALL_RUN_PYZ"
  local pyz_status=$?
  if [ "$pyz_status" -eq 2 ]; then
    log_update_all_relaunch "pyz requested continue"
    copy_update_all_pyz || return $?
    schedule_chip_id_display_blank
    "$UPDATE_ALL_PYTHON" "$UPDATE_ALL_RUN_PYZ" --continue
    pyz_status=$?
  fi
  return "$pyz_status"
}}
trap restore_update_all_display EXIT INT TERM HUP
log_update_all_relaunch "started tty=$(tty 2>/dev/null || echo unknown) args=$*"
prepare_update_all_tty
cd "$UPDATE_ALL_DIR"
run_update_all_pyz
EXITSTATUS=$?
log_update_all_relaunch "Update All exited with $EXITSTATUS"
restore_update_all_display
exit $EXITSTATUS
'''
    with open(script_path, 'w') as launcher_file:
        launcher_file.write(launcher)
        launcher_file.flush()
        os.fsync(launcher_file.fileno())
    os.chmod(script_path, 0o750)
    linker.debug(f'_write_update_all_relaunch_script: wrote {script_path}')


def _update_all_pyz_path(update_all_dir: str) -> str:
    running_archive_path = current_update_all_archive_path()
    if running_archive_path is not None:
        return running_archive_path

    return os.path.join(update_all_dir, CHIP_ID_UPDATE_ALL_PYZ_RELATIVE_PATH)


def _shell_export_forwarded_environment() -> str:
    lines = []
    for name, value in sorted(os.environ.items()):
        if not _should_forward_relaunch_environment_name(name):
            continue
        lines.append(f'export {name}={shlex.quote(value)}')
    return '\n'.join(lines)


def _should_forward_relaunch_environment_name(name: str) -> bool:
    if name in CHIP_ID_RELAUNCH_ENV_EXCLUDED_NAMES:
        return False
    if name.startswith('BASH_FUNC_'):
        return False
    return _is_valid_shell_environment_name(name)


def _is_valid_shell_environment_name(name: str) -> bool:
    if not name:
        return False

    first = name[0]
    if not (first == '_' or 'A' <= first <= 'Z' or 'a' <= first <= 'z'):
        return False

    for char in name[1:]:
        if not (char == '_' or '0' <= char <= '9' or 'A' <= char <= 'Z' or 'a' <= char <= 'z'):
            return False

    return True


def _reset_chip_id_log(log_path: str) -> None:
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    try:
        os.remove(log_path)
    except FileNotFoundError:
        pass


def _write_worker_startup_marker(marker_path: Optional[str], linker: ChipIdLinker) -> None:
    if marker_path is None:
        return

    temporary_marker_path = f'{marker_path}.{os.getpid()}.tmp'
    try:
        marker_dir = os.path.dirname(marker_path)
        if marker_dir:
            os.makedirs(marker_dir, exist_ok=True)
        with open(temporary_marker_path, 'w') as marker_file:
            marker_file.write(f'{os.getpid()}\n')
            marker_file.flush()
            os.fsync(marker_file.fileno())
        os.replace(temporary_marker_path, marker_path)
        linker.debug(f'_write_worker_startup_marker: wrote {marker_path}')
    except Exception as e:
        linker.debug('Could not write chip-ID worker startup marker')
        linker.debug(e)
        try:
            os.remove(temporary_marker_path)
        except FileNotFoundError:
            pass
        raise
