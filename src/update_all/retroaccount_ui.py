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
import abc
import threading
import time
from typing import Dict, Any, Optional, Union, List, Protocol

from update_all.retroaccount_qr import generate_qr_lines
from update_all.ui_engine import EffectChain, ProcessKeyResult, UiSection
from update_all.ui_engine_dialog_application import UiDialogDrawer, _NavigationState
from update_all.ui_model_utilities import Key

_POLL_TIMEOUT_SECONDS = 600  # 10 minutes
_POLL_INTERVAL = 5


class RetroAccountClient(Protocol):
    @property
    def server_url(self) -> str: ...
    def request_device_code(self) -> Optional[dict]: ...
    def get_existing_device_id(self) -> Optional[str]: ...
    def poll_for_token(self, device_code: str, device_id: Optional[str] = None) -> Optional[dict]: ...
    def save_login_credentials(self, credentials: dict) -> bool: ...

class DeviceLoginRenderer(abc.ABC):
    @abc.abstractmethod
    def render_requesting(self, header: str) -> None:
        """Show 'Requesting device code...' screen"""

    @abc.abstractmethod
    def render_poll_screen(self, header: str, user_code: str, verification_uri: str,
                           qr_lines: List[str], dots: str, remaining: int) -> None:
        """Show the QR/code + countdown polling screen"""

    @abc.abstractmethod
    def render_cancel_dialog(self, header: str, user_code: str,
                             options: List[str], selected: int) -> None:
        """Show cancel confirmation dialog (non-blocking)"""

    @abc.abstractmethod
    def set_key_timeout(self, timeout_ms: int) -> None:
        """Set timeout for next read_key. -1 = blocking."""

    @abc.abstractmethod
    def read_key(self) -> Union[Key, int]:
        """Read a key. Returns Key enum or raw int. -1 on timeout."""

    @abc.abstractmethod
    def flush_input(self) -> None:
        """Flush stale keyboard input."""


class DeviceLogin(UiSection):
    def __init__(self, drawer: UiDialogDrawer, renderer: DeviceLoginRenderer, retroaccount: RetroAccountClient, data: Dict[str, Any]):
        self._drawer = drawer
        self._renderer = renderer
        self._retroaccount = retroaccount
        self._data = data

    def process_key(self) -> Optional[ProcessKeyResult]:
        try:
            return self._run_login_flow()
        finally:
            self._drawer.clear()
            self._renderer.flush_input()

    def _run_login_flow(self) -> Optional[ProcessKeyResult]:
        code_response = self._request_code_with_retry()
        if code_response is None:
            return EffectChain(self._data.get('failure_effects', [{"type": "navigate", "target": "back"}]))

        while True:
            result = self._poll_loop(code_response)
            if result == '_new_code':
                code_response = self._request_code_with_retry()
                if code_response is None:
                    return EffectChain(self._data.get('failure_effects', [{"type": "navigate", "target": "back"}]))
                continue
            return result

    def _request_code_with_retry(self):
        header = self._data.get('header', 'Device Login')
        while True:
            self._renderer.render_requesting(header)
            result = self._retroaccount.request_device_code()
            if result is not None:
                return result

            result = self._show_drawer_dialog(
                "Connection Failed",
                ["Could not reach the server."],
                ["Retry", "Exit"]
            )
            if result != 0:
                return None

    def _poll_loop(self, code_response) -> ProcessKeyResult:
        device_code = code_response["device_code"]
        user_code = code_response["user_code"]
        poll_device_id = code_response.get("device_id") or self._retroaccount.get_existing_device_id()
        base_url = self._retroaccount.server_url.rstrip('/')
        verification_uri = code_response.get("verification_uri", f"{base_url}/code?c={user_code}")
        qr_lines = generate_qr_lines(verification_uri)
        timeout = min(code_response.get("expires_in", _POLL_TIMEOUT_SECONDS), _POLL_TIMEOUT_SECONDS)
        start_time = time.time()
        dots = ""
        last_dots_time = 0
        header = self._data.get('header', 'Device Login')

        poller = _BackgroundPoller(self._retroaccount, device_code, poll_device_id)
        self._renderer.set_key_timeout(50)

        while True:
            remaining = int(timeout - (time.time() - start_time))
            if remaining <= 0:
                break

            now = time.time()
            if now - last_dots_time >= 1.0:
                last_dots_time = now
                dots = "." * ((len(dots) + 1) % 4)

            self._renderer.render_poll_screen(header, user_code, verification_uri, qr_lines, dots, remaining)

            token_resp = poller.get_result()
            if token_resp:
                if token_resp.get("status") == "unauthorized":
                    return EffectChain(self._data.get('failure_effects', [{"type": "navigate", "target": "back"}]))
                return self._handle_success(token_resp, code_response)

            key = self._renderer.read_key()
            if key == Key.ENTER or key == 27:
                if remaining <= 120:
                    break

                cancel_result = self._show_cancel_dialog(poller, user_code, code_response)
                if cancel_result is not None:
                    return cancel_result

        return self._show_timeout_dialog(user_code)

    def _show_cancel_dialog(self, poller: '_BackgroundPoller', user_code, code_response):
        self._drawer.clear()
        self._renderer.set_key_timeout(50)

        selected = 0
        options = ["Resume", "Exit"]
        header = self._data.get('header', 'Device Login')

        while True:
            token_resp = poller.get_result()
            if token_resp:
                if token_resp.get("status") == "unauthorized":
                    return EffectChain(self._data.get('failure_effects', [{"type": "navigate", "target": "back"}]))
                return self._handle_success(token_resp, code_response)

            self._renderer.render_cancel_dialog(header, user_code, options, selected)

            key = self._renderer.read_key()
            if key == Key.LEFT:
                selected = max(0, selected - 1)
            elif key == Key.RIGHT:
                selected = min(len(options) - 1, selected + 1)
            elif key == 27:
                return EffectChain(self._data.get('failure_effects', [{"type": "navigate", "target": "back"}]))
            elif key == Key.ENTER:
                if selected == 0:
                    return None  # Resume
                else:
                    return EffectChain(self._data.get('failure_effects', [{"type": "navigate", "target": "back"}]))

    def _show_timeout_dialog(self, user_code) -> ProcessKeyResult:
        result = self._show_drawer_dialog(
            "Code Expired",
            [
                f"The code {user_code} is no longer valid.",
                " ",
                "To link this device, you'll need a new code",
                "to enter on your phone or computer.",
            ],
            ["New Code", "Exit"]
        )
        if result == 0:
            return '_new_code'
        return EffectChain(self._data.get('failure_effects', [{"type": "navigate", "target": "back"}]))

    def _handle_success(self, token_resp, code_response) -> ProcessKeyResult:
        credentials = token_resp.get("credentials", token_resp)
        if isinstance(credentials, dict):
            if "device_id" not in credentials:
                credentials["device_id"] = token_resp.get("device_id", code_response.get("device_code", ""))

        saved = self._retroaccount.save_login_credentials(credentials)
        if saved:
            self._show_drawer_dialog(
                "Verified!",
                ["Device successfully authenticated"],
                ["Ok"]
            )
            return EffectChain(self._data.get('success_effects', [{"type": "navigate", "target": "back"}]))
        else:
            self._show_drawer_dialog(
                "Login Failed",
                ["Could not store the login credentials in the device. Make sure your storage can be written."],
                ["Ok"]
            )
            return EffectChain(self._data.get('failure_effects', [{"type": "navigate", "target": "back"}]))

    def _show_drawer_dialog(self, header_text, text_lines, options) -> int:
        self._drawer.clear()
        dialog_data = {
            'header': f"{header_text}",
            'text': text_lines,
            'actions': [{"title": o} for o in options],
        }

        if len(options) == 1:
            self._drawer.start(dialog_data)
            for line in text_lines:
                self._drawer.add_text_line(line)
            self._drawer.add_action(options[0], is_selected=True)
            while True:
                key = self._drawer.paint()
                if key == Key.ENTER:
                    return 0

        state = _NavigationState(0, len(options))
        self._drawer.start(dialog_data)
        for line in text_lines:
            self._drawer.add_text_line(line)
        for i, option in enumerate(options):
            self._drawer.add_action(option, i == state.lateral_position())

        while True:
            key = self._drawer.paint()
            if key == Key.LEFT:
                state.navigate_left()
            elif key == Key.RIGHT:
                state.navigate_right()
            elif key == 27:
                return len(options) - 1
            elif key == Key.ENTER:
                return state.lateral_position()

            self._drawer.clear()
            self._drawer.start(dialog_data)
            for line in text_lines:
                self._drawer.add_text_line(line)
            for i, option in enumerate(options):
                self._drawer.add_action(option, i == state.lateral_position())

    def reset(self) -> None:
        pass

    def clear(self) -> None:
        self._drawer.clear()


class _BackgroundPoller:
    def __init__(self, retroaccount: RetroAccountClient, device_code, device_id):
        self._retroaccount = retroaccount
        self._device_code = device_code
        self._device_id = device_id
        self._result = None
        self._lock = threading.Lock()
        self._polling = False
        self._last_poll = 0
        self._start_poll()

    def _start_poll(self):
        with self._lock:
            if self._polling:
                return
            self._polling = True
            self._last_poll = time.time()
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self):
        result = self._retroaccount.poll_for_token(self._device_code, device_id=self._device_id)

        with self._lock:
            self._result = result
            self._polling = False

    def get_result(self):
        with self._lock:
            result = self._result
            self._result = None
            polling = self._polling
        if not polling and result is None and time.time() - self._last_poll >= _POLL_INTERVAL:
            self._start_poll()
        return result
