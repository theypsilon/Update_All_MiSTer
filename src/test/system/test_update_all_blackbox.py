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

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import zipapp
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from update_all.constants import BACKGROUND_JOBS_SOFT_TIMEOUT, FILE_downloader_run_signal, FILE_settings_screen_model_json_zip, \
    FILE_update_all_self_update_downloader_log, FILE_update_all_self_update_resume, FILE_update_all_log, \
    FILE_update_all_print_tmp_log, FILE_update_all_pyz


_SOURCE_ROOT = Path(__file__).resolve().parents[2]
_REPOSITORY_ROOT = _SOURCE_ROOT.parent
_LAUNCHER = _REPOSITORY_ROOT / 'update_all.sh'
_FAKE_DOWNLOADER_FIXTURE = Path(__file__).resolve().parent / 'fixtures/mock_downloader.py'
_CURRENT_MODEL = b'blackbox-current-settings-model'
_UPDATED_MODEL = b'blackbox-updated-settings-model'
_GLOBAL_TEMP_FILES = (
    Path(FILE_downloader_run_signal),
    Path(FILE_update_all_self_update_resume),
    Path(FILE_update_all_print_tmp_log),
    Path('/tmp/ua_downloader_bin'),
    Path('/tmp/ua_downloader_latest.zip'),
    Path('/tmp/ua_downloader_dd.pyz'),
    Path('/tmp/update_all.sh'),
    Path('/tmp/update_all.pyz'),
)


class _Route:
    def __init__(self, body: bytes = b'', status: int = 200, delay: float = 0):
        self.body = body
        self.status = status
        self.delay = delay


class _MockRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._handle()

    def do_POST(self):
        self._handle()

    def _handle(self):
        body_size = int(self.headers.get('Content-Length', '0'))
        request_body = self.rfile.read(body_size) if body_size else b''
        path = urlsplit(self.path).path
        owner = self.server.owner
        owner.record_request(self.command, path, request_body)
        route = owner.routes.get((self.command, path), _Route(status=404))
        if route.delay:
            time.sleep(route.delay)

        try:
            self.send_response(route.status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(route.body)))
            self.end_headers()
            self.wfile.write(route.body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, _format, *_args):
        pass


class _MockServer:
    def __init__(self, routes):
        self.routes = routes
        self.requests = []
        self._lock = threading.Lock()
        self._server = ThreadingHTTPServer(('127.0.0.1', 0), _MockRequestHandler)
        self._server.daemon_threads = True
        self._server.owner = self
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, _type, _value, _traceback):
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)

    @property
    def base_url(self):
        host, port = self._server.server_address
        return f'http://{host}:{port}'

    def url(self, path):
        return self.base_url + path

    def record_request(self, method, path, body):
        with self._lock:
            self.requests.append({
                'body': body,
                'method': method,
                'path': path,
                'timestamp': time.time(),
            })

    def requests_for(self, path, method=None):
        with self._lock:
            return [
                request
                for request in self.requests
                if request['path'] == path and (method is None or request['method'] == method)
            ]


class TestUpdateAllBlackBox(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._artifacts_temp = tempfile.TemporaryDirectory(prefix='update_all_blackbox_artifacts_')
        cls._artifacts = Path(cls._artifacts_temp.name)
        app_source = cls._artifacts / 'app'
        app_source.mkdir()
        shutil.copy2(_SOURCE_ROOT / '__main__.py', app_source / '__main__.py')
        shutil.copytree(
            _SOURCE_ROOT / 'update_all',
            app_source / 'update_all',
            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'),
        )

        cls._current_archive = cls._artifacts / 'update_all_current.pyz'
        cls._updated_archive = cls._artifacts / 'update_all_updated.pyz'
        cls._create_archive(app_source, cls._current_archive, 'blackbox-current')
        cls._create_archive(app_source, cls._updated_archive, 'blackbox-updated')

        cls._current_model_source = cls._artifacts / 'settings_model_current.zip'
        cls._current_model_source.write_bytes(_CURRENT_MODEL)
        cls._updated_model_source = cls._artifacts / 'settings_model_updated.zip'
        cls._updated_model_source.write_bytes(_UPDATED_MODEL)

        cls._fake_downloader = cls._artifacts / 'mock_downloader.py'
        shutil.copy2(_FAKE_DOWNLOADER_FIXTURE, cls._fake_downloader)
        cls._fake_downloader.chmod(0o755)

    @classmethod
    def tearDownClass(cls):
        cls._artifacts_temp.cleanup()

    @classmethod
    def _create_archive(cls, app_source, target, commit):
        (app_source / 'commit.py').write_text(f"default_commit = '{commit}'\n")
        zipapp.create_archive(app_source, target, interpreter='/usr/bin/env python3')
        target.chmod(0o755)

    def setUp(self):
        self._clean_global_temp_files()
        self._installation_temp = tempfile.TemporaryDirectory(prefix='update_all_blackbox_install_')
        self.installation = Path(self._installation_temp.name)
        self.update_all_dir = self.installation / 'Scripts/.config/update_all'
        self.update_all_dir.mkdir(parents=True)
        shutil.copyfile(self._current_archive, self.installation / FILE_update_all_pyz)
        (self.installation / FILE_settings_screen_model_json_zip).write_bytes(_CURRENT_MODEL)
        shutil.copyfile(
            _SOURCE_ROOT / 'test/fixtures/downloader_ini/default_downloader.ini',
            self.installation / 'downloader.ini',
        )
        (self.installation / 'downloader').mkdir()
        retroaccount_dir = self.installation / 'Scripts/.config/retroaccount'
        retroaccount_dir.mkdir(parents=True)
        (retroaccount_dir / 'user.json').write_text(json.dumps({
            'device_id': 'blackbox-device',
            'refresh_token': 'blackbox-refresh-token',
        }))
        self.calls_path = self.installation / 'mock_downloader_calls.jsonl'

    def tearDown(self):
        self._installation_temp.cleanup()
        self._clean_global_temp_files()

    def test_matching_hashes_run_standard_downloader_once_without_restart(self):
        manifest = self._manifest(self._current_archive, self._current_model_source)
        with self._server(manifest) as server:
            result = self._run(server, downloader_source='path')

        self._assert_successful_standard_flow(result, ['standard'])
        self.assertEqual(1, len(server.requests_for('/update_all.json', 'GET')))
        self.assertEqual(0, len(server.requests_for('/downloader.pyz', 'GET')))
        self.assertEqual(1, len(server.requests_for('/api/mister/sync', 'POST')))
        self.assertLessEqual(
            server.requests_for('/api/mister/sync', 'POST')[0]['timestamp'],
            self._calls()[0]['timestamp'],
        )
        self.assertIn('Sequence:', result.stdout)
        self.assertNotIn('Early Update All check found a changed', result.stdout)
        self.assertIn('Update All flow started: pass=NewRun.', self._log_contents())
        self._assert_messages_in_output_and_log(
            result,
            'Update All flow command: STANDARD.',
            'Update All flow destination: downloader.',
        )

    def test_downloader_url_override_runs_server_downloader(self):
        manifest = self._manifest(self._current_archive, self._current_model_source)
        with self._server(manifest) as server:
            result = self._run(server, downloader_source='url')

        self._assert_successful_standard_flow(result, ['standard'])
        self.assertEqual(1, len(server.requests_for('/downloader.pyz', 'GET')))

    def test_standard_downloader_failure_is_reported_after_the_normal_tail(self):
        manifest = self._manifest(self._current_archive, self._current_model_source)
        with self._server(manifest) as server:
            result = self._run(server, standard_exit_code=9)

        self.assertEqual(1, result.returncode, result.stdout)
        self.assertEqual(['standard'], [call['mode'] for call in self._calls()])
        self.assertIn('There were some errors in the Updaters.', result.stdout)
        self.assertIn(' - Scripts/.config/downloader/downloader.log', result.stdout)
        self.assertIn('Update All failed!', result.stdout)
        self.assertIn('There were some errors in the Updaters.', self._log_contents())
        self._assert_messages_in_output_and_log(
            result,
            'Standard Downloader failed: return_code=9.',
            'Update All flow finished: exit_code=10.',
        )
        self.assertFalse(Path('/tmp/ua_downloader_bin').exists())

    def test_revoked_retroaccount_session_does_not_interrupt_standard_update(self):
        manifest = self._manifest(self._current_archive, self._current_model_source)
        with self._server(manifest, retroaccount_status=401) as server:
            result = self._run(server)

        self._assert_successful_standard_flow(result, ['standard'])
        self.assertEqual(1, len(server.requests_for('/api/mister/sync', 'POST')))
        self.assertIn('RetroAccountService: User session revoked', result.stdout)
        self.assertFalse((self.installation / 'Scripts/.config/retroaccount/user.json').exists())

    def test_changed_update_all_before_settings_runs_only_targeted_downloader_and_records_settings_resume(self):
        manifest = self._manifest(self._updated_archive, self._updated_model_source)
        with self._server(manifest) as server:
            result = self._run(
                server,
                non_interactive=False,
                settings_model_source=self._updated_model_source,
                stdin_bytes=b'A',
                update_all_source=self._updated_archive,
                use_launcher=False,
            )

        self.assertEqual(2, result.returncode, result.stdout)
        self.assertEqual(['run-only'], [call['mode'] for call in self._calls()])
        self.assertEqual(
            str(self.installation / FILE_update_all_self_update_downloader_log),
            self._calls()[0]['logfile'],
        )
        self.assertEqual(
            'MOCK_DOWNLOADER mode=run-only\n',
            (self.installation / FILE_update_all_self_update_downloader_log).read_text(),
        )
        self.assertEqual('settings_screen', Path(FILE_update_all_self_update_resume).read_text())
        self.assertIn('A NEW VERSION OF UPDATE ALL IS AVAILABLE!', result.stdout)
        self.assertIn('Early Update All update completed; restart destination: settings-screen.', result.stdout)
        self.assertNotIn('MOCK_DOWNLOADER mode=standard', result.stdout)

    def test_changed_update_all_runs_standard_downloader_then_restarts_after_it(self):
        manifest = self._manifest(self._updated_archive, self._current_model_source)
        with self._server(manifest) as server:
            result = self._run(
                server,
                update_all_source=self._updated_archive,
                settings_model_source=self._current_model_source,
            )

        self._assert_successful_standard_flow(result, ['standard'])
        self.assertEqual(self._md5(self._updated_archive), self._md5(self.installation / FILE_update_all_pyz))
        self.assertEqual(1, len(server.requests_for('/update_all.json', 'GET')))
        self.assertEqual(2, len(server.requests_for('/api/mister/sync', 'POST')))
        self.assertIn(f'Early Update All check found a changed {FILE_update_all_pyz}', result.stdout)
        self.assertIn('Update All was updated by the standard Downloader; restart destination: after-downloader.', result.stdout)
        self.assertIn('Update All flow finished: exit_code=2.', result.stdout)
        log_contents = self._log_contents()
        self.assertIn('Update All flow started: pass=NewRun.', log_contents)
        self.assertIn('Update All flow finished: exit_code=2.', log_contents)
        self.assertIn('Update All flow started: pass=Continue.', log_contents)
        self.assertIn('Update All flow destination: after-downloader.', result.stdout)
        self.assertIn('blackbox-updated', result.stdout)
        self.assertFalse(Path(FILE_update_all_self_update_resume).exists())

    def test_changed_settings_model_runs_standard_downloader_then_restarts_after_it(self):
        manifest = self._manifest(self._current_archive, self._updated_model_source)
        with self._server(manifest) as server:
            result = self._run(
                server,
                update_all_source=self._current_archive,
                settings_model_source=self._updated_model_source,
            )

        self._assert_successful_standard_flow(result, ['standard'])
        self.assertEqual(self._md5(self._updated_model_source), self._md5(self.installation / FILE_settings_screen_model_json_zip))
        self.assertEqual(1, len(server.requests_for('/update_all.json', 'GET')))
        self.assertIn(f'Early Update All check found a changed {FILE_settings_screen_model_json_zip}', result.stdout)
        self.assertIn('Update All was updated by the standard Downloader; restart destination: after-downloader.', result.stdout)

    def test_failed_standard_downloader_does_not_prepare_post_downloader_restart(self):
        manifest = self._manifest(self._updated_archive, self._updated_model_source)
        with self._server(manifest) as server:
            result = self._run(server, standard_exit_code=7)

        self.assertEqual(1, result.returncode, result.stdout)
        self.assertEqual(['standard'], [call['mode'] for call in self._calls()])
        self.assertEqual(self._md5(self._current_archive), self._md5(self.installation / FILE_update_all_pyz))
        self.assertEqual(1, len(server.requests_for('/update_all.json', 'GET')))
        self.assertIn('Standard Downloader failed: return_code=7.', result.stdout)
        self.assertNotIn('restart destination: after-downloader.', result.stdout)
        self.assertFalse(Path(FILE_update_all_self_update_resume).exists())

    def test_successful_standard_update_is_not_rechecked_before_post_downloader_restart(self):
        manifest = self._manifest(self._updated_archive, self._updated_model_source)
        with self._server(manifest) as server:
            result = self._run(server, install_files=False)

        self._assert_successful_standard_flow(result, ['standard'])
        self.assertEqual(self._md5(self._current_archive), self._md5(self.installation / FILE_update_all_pyz))
        self.assertEqual(self._md5(self._current_model_source), self._md5(self.installation / FILE_settings_screen_model_json_zip))
        self.assertIn('Update All was updated by the standard Downloader; restart destination: after-downloader.', result.stdout)

    def test_manifest_http_failure_is_not_retried_and_continues_standard_flow(self):
        with self._server(b'', manifest_status=503) as server:
            result = self._run(server)

        self._assert_successful_standard_flow(result, ['standard'])
        self.assertEqual(1, len(server.requests_for('/update_all.json', 'GET')))
        self.assertIn('Could not check whether Update All needs an update.', result.stdout)
        self.assertIn('HTTP 503', result.stdout)

    def test_invalid_manifest_is_not_retried_and_continues_standard_flow(self):
        with self._server(b'not-json') as server:
            result = self._run(server)

        self._assert_successful_standard_flow(result, ['standard'])
        self.assertEqual(1, len(server.requests_for('/update_all.json', 'GET')))
        self.assertIn('Could not check whether Update All needs an update.', result.stdout)

    def test_missing_settings_model_skips_manifest_fetch_and_runs_standard_flow(self):
        (self.installation / FILE_settings_screen_model_json_zip).unlink()
        manifest = self._manifest(self._updated_archive, self._updated_model_source)
        with self._server(manifest) as server:
            result = self._run(server)

        self._assert_successful_standard_flow(result, ['standard'])
        self.assertEqual(0, len(server.requests_for('/update_all.json', 'GET')))
        self.assertNotIn('A NEW VERSION OF UPDATE ALL IS AVAILABLE!', result.stdout)
        self._assert_messages_in_output_and_log(
            result,
            'Early Update All check skipped.',
        )

    def test_missing_update_all_archive_skips_manifest_fetch_and_runs_standard_flow(self):
        (self.installation / FILE_update_all_pyz).unlink()
        manifest = self._manifest(self._updated_archive, self._updated_model_source)
        with self._server(manifest) as server:
            result = self._run(server, use_launcher=False)

        self._assert_successful_standard_flow(result, ['standard'])
        self.assertEqual(0, len(server.requests_for('/update_all.json', 'GET')))
        self._assert_messages_in_output_and_log(
            result,
            'Early Update All check skipped.',
        )

    def test_manifest_timeout_waits_once_then_continues_standard_flow(self):
        manifest = self._manifest(self._updated_archive, self._updated_model_source)
        manifest_delay = BACKGROUND_JOBS_SOFT_TIMEOUT + 3
        with self._server(manifest, manifest_delay=manifest_delay) as server:
            result = self._run(server, timeout=20)

        self._assert_successful_standard_flow(result, ['standard'])
        manifest_request = server.requests_for('/update_all.json', 'GET')
        self.assertEqual(1, len(manifest_request))
        standard_call = self._calls()[0]
        self.assertLess(
            standard_call['timestamp'] - manifest_request[0]['timestamp'],
            manifest_delay,
        )
        self.assertIn('Update All update check timed out; continuing with the normal update flow.', result.stdout)

    def test_non_default_entrypoint_skips_early_check(self):
        manifest = self._manifest(self._updated_archive, self._updated_model_source)
        with self._server(manifest) as server:
            result = self._run(server, args=['--no-continue'])

        self._assert_successful_standard_flow(result, ['standard'])
        self.assertEqual(0, len(server.requests_for('/update_all.json', 'GET')))
        self.assertIn('Update All flow started: pass=NewRunNonStop.', self._log_contents())
        self._assert_messages_in_output_and_log(
            result,
            'Update All flow command: STANDARD.',
            'Update All flow destination: downloader.',
        )

    def test_continue_without_resume_marker_defaults_to_standard_downloader(self):
        manifest = self._manifest(self._updated_archive, self._updated_model_source)
        with self._server(manifest) as server:
            result = self._run(server, args=['--continue'], use_launcher=False)

        self._assert_successful_standard_flow(result, ['standard'])
        self.assertEqual(0, len(server.requests_for('/update_all.json', 'GET')))
        self.assertIn('Update All flow started: pass=Continue.', self._log_contents())
        self._assert_messages_in_output_and_log(
            result,
            'Update All flow destination: downloader.',
        )

    def test_non_interactive_continue_skips_recorded_settings_screen(self):
        Path(FILE_update_all_self_update_resume).write_text('settings_screen')
        manifest = self._manifest(self._updated_archive, self._updated_model_source)
        with self._server(manifest) as server:
            result = self._run(server, args=['--continue'], use_launcher=False)

        self._assert_successful_standard_flow(result, ['standard'])
        self.assertIn('Skipping Settings Screen in non-interactive mode.', result.stdout)
        self.assertIn('Skipping Settings Screen in non-interactive mode.', self._log_contents())
        self._assert_messages_in_output_and_log(
            result,
            'Update All flow destination: settings-screen.',
        )
        self.assertFalse(Path(FILE_update_all_self_update_resume).exists())

    def test_unknown_resume_marker_defaults_to_standard_downloader_and_is_removed(self):
        Path(FILE_update_all_self_update_resume).write_text('unknown')
        manifest = self._manifest(self._updated_archive, self._updated_model_source)
        with self._server(manifest) as server:
            result = self._run(server, args=['--continue'], use_launcher=False)

        self._assert_successful_standard_flow(result, ['standard'])
        self.assertIn('Ignoring unknown early Update All resume point: unknown', result.stdout)
        self._assert_messages_in_output_and_log(
            result,
            'Update All flow destination: downloader.',
        )
        self.assertFalse(Path(FILE_update_all_self_update_resume).exists())

    def test_skip_downloader_logs_both_early_check_and_standard_downloader_skip(self):
        manifest = self._manifest(self._updated_archive, self._updated_model_source)
        with self._server(manifest) as server:
            result = self._run(server, skip_downloader=True)

        self.assertEqual(0, result.returncode, result.stdout)
        self.assertEqual([], self._calls())
        self.assertEqual(0, len(server.requests_for('/update_all.json', 'GET')))
        self.assertIn('Update All flow started: pass=NewRun.', self._log_contents())
        self._assert_messages_in_output_and_log(
            result,
            'Update All flow command: STANDARD.',
            'Early Update All check skipped.',
            'Update All flow destination: downloader.',
            'Standard Downloader skipped.',
            'Update All flow finished: exit_code=0.',
        )

    def test_retroaccount_sync_pass_logs_entry_and_completion_without_downloader(self):
        manifest = self._manifest(self._current_archive, self._current_model_source)
        with self._server(manifest) as server:
            result = self._run(server, args=['--retroaccount-sync'], use_launcher=False)

        self.assertEqual(0, result.returncode, result.stdout)
        self.assertEqual([], self._calls())
        self.assertEqual(0, len(server.requests_for('/update_all.json', 'GET')))
        self.assertEqual(1, len(server.requests_for('/api/mister/sync', 'POST')))
        self.assertIn('Update All flow started: pass=RetroAccountSync.', self._log_contents())
        self._assert_messages_in_output_and_log(
            result,
            'Update All flow finished: exit_code=0.',
        )

    def test_environment_requested_early_exit_logs_service_exit_code(self):
        manifest = self._manifest(self._current_archive, self._current_model_source)
        with self._server(manifest) as server:
            result = self._run(server, transition_service_only=True, use_launcher=False)

        self.assertEqual(1, result.returncode, result.stdout)
        self.assertEqual([], self._calls())
        self.assertEqual(0, len(server.requests_for('/update_all.json', 'GET')))
        self.assertIn('Update All flow started: pass=NewRun.', self._log_contents())
        self._assert_messages_in_output_and_log(
            result,
            'Update All flow command: STANDARD.',
            'Update All flow finished: exit_code=1.',
        )

    def _server(self, manifest_body, manifest_status=200, manifest_delay=0, retroaccount_status=200):
        routes = {
            ('GET', '/update_all.json'): _Route(manifest_body, manifest_status, manifest_delay),
            ('GET', '/downloader.pyz'): _Route(_FAKE_DOWNLOADER_FIXTURE.read_bytes()),
            ('POST', '/api/mister/sync'): _Route(json.dumps({
                'benefits': {
                    'jtbeta_access': False,
                    'update_all_extras': False,
                },
            }).encode(), retroaccount_status),
        }
        return _MockServer(routes)

    def _run(
            self,
            server,
            args=None,
            downloader_source='path',
            install_files=True,
            non_interactive=True,
            run_only_exit_code=0,
            settings_model_source=None,
            skip_downloader=False,
            standard_exit_code=0,
            stdin_bytes=None,
            timeout=15,
            transition_service_only=False,
            update_all_source=None,
            use_launcher=True,
    ):
        env = os.environ.copy()
        env.update({
            'CURL_SSL': '--insecure',
            'DEBUG': 'true',
            'HTTP_PROXY': '',
            'HTTPS_PROXY': '',
            'LOCATION_STR': str(self.installation),
            'MOCK_DOWNLOADER_CALLS_PATH': str(self.calls_path),
            'MOCK_INSTALL_FILES': str(install_files).lower(),
            'MOCK_RUN_ONLY_EXIT_CODE': str(run_only_exit_code),
            'MOCK_SETTINGS_MODEL_SOURCE': str(settings_model_source or self._current_model_source),
            'MOCK_STANDARD_EXIT_CODE': str(standard_exit_code),
            'MOCK_UPDATE_ALL_PYZ_SOURCE': str(update_all_source or self._current_archive),
            'NO_PROXY': '127.0.0.1,localhost',
            'RETROACCOUNT_DOMAIN': server.base_url,
            'SKIP_DOWNLOADER': str(skip_downloader).lower(),
            'TRANSITION_SERVICE_ONLY': str(transition_service_only).lower(),
            'UPDATE_ALL_DOWNLOADER_PATH': str(self._fake_downloader) if downloader_source == 'path' else '',
            'UPDATE_ALL_DOWNLOADER_PYTHON_COMPATIBLE_PATH': sys.executable if downloader_source == 'path' else '',
            'UPDATE_ALL_DOWNLOADER_URL': server.url('/downloader.pyz'),
            'UPDATE_ALL_MISTER_DB_URL': server.url('/update_all.json'),
            'UPDATE_ALL_NON_INTERACTIVE': str(non_interactive).lower(),
            'http_proxy': '',
            'https_proxy': '',
        })
        env.pop('TEST_ROUTINE', None)
        command = [_LAUNCHER if use_launcher else self._current_archive, *(args or [])]
        master_fd = None
        slave_fd = None
        input_thread = None
        input_stop = None
        if stdin_bytes is not None:
            master_fd, slave_fd = os.openpty()
            input_stop = threading.Event()

            def write_stdin():
                while not input_stop.wait(0.25):
                    try:
                        os.write(master_fd, stdin_bytes)
                    except OSError:
                        return

            input_thread = threading.Thread(target=write_stdin, daemon=True)
            input_thread.start()
        try:
            process = subprocess.run(
                [str(part) for part in command],
                cwd=self.installation,
                env=env,
                stdin=slave_fd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as e:
            output = e.stdout.decode() if isinstance(e.stdout, bytes) else e.stdout or ''
            self.fail(f'Update All process timed out after {timeout}s.\n{output}')
        finally:
            if input_stop is not None:
                input_stop.set()
            if slave_fd is not None:
                os.close(slave_fd)
            if master_fd is not None:
                os.close(master_fd)
            if input_thread is not None:
                input_thread.join(timeout=1)
        return process

    def _assert_successful_standard_flow(self, result, expected_modes):
        self.assertEqual(0, result.returncode, result.stdout)
        calls = self._calls()
        self.assertEqual(expected_modes, [call['mode'] for call in calls], result.stdout)
        self.assertEqual(1, sum(call['mode'] == 'standard' for call in calls))
        standard_call = next(call for call in calls if call['mode'] == 'standard')
        self.assertEqual(str(self.installation / 'downloader.ini'), standard_call['downloader_ini_path'])
        self.assertIsNone(standard_call['logfile'])
        self.assertEqual('false', standard_call['update_linux'])
        self.assertIsNone(standard_call['default_db_id'])
        self.assertIn('Running MiSTer Downloader', result.stdout)
        self.assertIn('MOCK_DOWNLOADER mode=standard', result.stdout)
        if 'run-only' in expected_modes:
            self.assertIn('A NEW VERSION OF UPDATE ALL IS AVAILABLE!', result.stdout)
            self.assertIn('Installing it now.', result.stdout)
            self.assertIn('The update process will continue automatically...', result.stdout)
            self.assertIn('MOCK_DOWNLOADER mode=run-only', result.stdout)
        else:
            self.assertNotIn('A NEW VERSION OF UPDATE ALL IS AVAILABLE!', result.stdout)
            self.assertNotIn('Installing it now.', result.stdout)
            self.assertNotIn('The update process will continue automatically...', result.stdout)
            self.assertNotIn('MOCK_DOWNLOADER mode=run-only', result.stdout)
        self.assertIn('Success! More details at:', result.stdout)
        self.assertIn('Skipping interactive log viewer and timeline in non-interactive mode.', result.stdout)
        self.assertNotIn('Press <UP>', result.stdout)
        self.assertFalse(Path('/tmp/ua_downloader_bin').exists())

        log_contents = self._log_contents()
        if 'Update All flow destination: after-downloader.' in log_contents:
            self.assertIn('Update All flow started: pass=Continue.', log_contents)
        else:
            self.assertIn('MOCK_DOWNLOADER mode=standard', log_contents)
        self.assertIn('Success! More details at:', log_contents)
        self.assertIn('Skipping interactive log viewer and timeline in non-interactive mode.', log_contents)
        self.assertIn('Update All flow started:', log_contents)
        self.assertIn('Update All flow destination:', log_contents)
        self.assertIn('Update All flow finished: exit_code=0.', log_contents)

        self.assertIn('Update All flow destination:', result.stdout)
        self.assertIn('Update All flow finished: exit_code=0.', result.stdout)

    def _calls(self):
        if not self.calls_path.exists():
            return []
        return [
            json.loads(line)
            for line in self.calls_path.read_text().splitlines()
            if line.strip()
        ]

    def _log_contents(self):
        log_path = self.installation / FILE_update_all_log
        self.assertTrue(log_path.is_file(), f'Expected Update All log at {log_path}')
        return log_path.read_text()

    def _assert_messages_in_output_and_log(self, result, *messages):
        log_contents = self._log_contents()
        for message in messages:
            self.assertIn(message, result.stdout)
            self.assertIn(message, log_contents)

    @classmethod
    def _manifest(cls, update_all_source, settings_model_source):
        return json.dumps({
            'db_id': 'update_all_mister',
            'files': {
                FILE_settings_screen_model_json_zip: {
                    'hash': cls._md5(settings_model_source),
                },
                FILE_update_all_pyz: {
                    'hash': cls._md5(update_all_source),
                },
            },
        }).encode()

    @staticmethod
    def _md5(path):
        digest = hashlib.md5()
        with open(path, 'rb') as source:
            while chunk := source.read(8192):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _clean_global_temp_files():
        for path in _GLOBAL_TEMP_FILES:
            try:
                path.unlink()
            except FileNotFoundError:
                pass


if __name__ == '__main__':
    unittest.main()
