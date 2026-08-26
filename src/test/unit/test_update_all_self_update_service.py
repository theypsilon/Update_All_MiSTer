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
import json
import unittest

from test.fake_filesystem import FileSystemFactory
from test.fetcher_stub import FetcherStub
from test.file_system_tester_state import FileSystemState
from test.logger_tester import LoggerSpy
from test.update_all_self_update_service_tester import UpdateAllSelfUpdateServiceTester
from update_all.cli_output_formatting import bold
from update_all.config import Config
from update_all.constants import BACKGROUND_JOBS_SOFT_TIMEOUT, FILE_settings_screen_model_json_zip, \
    FILE_update_all_self_update_downloader_log, FILE_update_all_self_update_resume, FILE_update_all_pyz
from update_all.other import GenericProvider
from update_all.update_all_self_update_service import UpdateAllResumePoint


class TestUpdateAllSelfUpdateService(unittest.TestCase):
    def test_check___when_file_changed___requires_update_from_single_non_retrying_fetch(self):
        sut, _state, fetcher, _downloader = _tester(
            files=_self_update_files('old-pyz', 'old-model'),
            response=(200, _update_all_db('new-pyz', 'new-model')),
        )

        result = _run_check(sut)

        self.assertTrue(result)
        self.assertEqual([0], fetcher.retries)
        self.assertEqual(BACKGROUND_JOBS_SOFT_TIMEOUT, fetcher.calls[0][4])

    def test_check___with_update_all_mister_url_override___fetches_overridden_url(self):
        override = 'http://127.0.0.1:8765/update_all_db.json'
        sut, _state, fetcher, _downloader = _tester(
            config=Config(update_all_mister_db_url=override),
            files=_self_update_files('old-pyz', 'old-model'),
            response=(200, _update_all_db('new-pyz', 'new-model')),
        )

        _run_check(sut)

        self.assertEqual(override, fetcher.calls[0][0])

    def test_can_check_for_update___when_file_missing___does_not_fetch(self):
        sut, _state, fetcher, _downloader = _tester(
            files={FILE_update_all_pyz: {'hash': 'pyz'}},
        )

        result = _run_check(sut)

        self.assertFalse(result)
        self.assertEqual([], fetcher.calls)

    def test_try_update_before_settings_and_prepare_restart___runs_downloader_and_records_settings_resume(self):
        downloader = _DownloaderServiceStub()
        logger = LoggerSpy()
        sut, state, _fetcher, _downloader = _tester(
            files=_self_update_files('old-pyz', 'old-model'),
            downloader=downloader,
            logger=logger,
        )

        result = sut.try_update_before_settings_and_prepare_restart()

        self.assertTrue(result)
        self.assertEqual([
            (
                '/media/fat/downloader.ini',
                ['--run-only', 'update_all_mister'],
                '/media/fat/' + FILE_update_all_self_update_downloader_log.lower(),
                False,
            ),
        ], downloader.command_calls)
        self.assertEqual('settings_screen', state.files[FILE_update_all_self_update_resume]['content'])
        self.assertEqual([
            '',
            bold('A NEW VERSION OF UPDATE ALL IS AVAILABLE!'),
            '',
            'Installing it now.',
            'The update process will continue automatically...',
            '',
        ], logger.print_lines)

    def test_try_prepare_restart_after_downloader___records_resume_without_running_downloader(self):
        downloader = _DownloaderServiceStub()
        sut, state, _fetcher, _downloader = _tester(
            files=_self_update_files('old-pyz', 'old-model'),
            downloader=downloader,
        )

        result = sut.try_prepare_restart_after_downloader()

        self.assertTrue(result)
        self.assertEqual([], downloader.command_calls)
        self.assertEqual('after_downloader', state.files[FILE_update_all_self_update_resume]['content'])

    def test_try_prepare_restart_after_downloader___when_marker_cannot_be_written___does_not_restart(self):
        sut, state, _fetcher, _downloader = _tester()

        def cannot_write(_path, _content):
            raise OSError('unwritable')

        sut._file_system.write_file_contents = cannot_write

        self.assertFalse(sut.try_prepare_restart_after_downloader())
        self.assertNotIn(FILE_update_all_self_update_resume, state.files)

    def test_take_resume_point___accepts_known_markers_and_always_removes_them(self):
        cases = (
            ('settings_screen', UpdateAllResumePoint.SETTINGS_SCREEN),
            ('after_downloader', UpdateAllResumePoint.AFTER_DOWNLOADER),
        )

        for resume_point, expected_result in cases:
            with self.subTest(resume_point=resume_point):
                sut, state, _fetcher, _downloader = _tester(files={
                    FILE_update_all_self_update_resume: {'content': resume_point},
                })

                result = sut.take_resume_point()

                self.assertEqual(expected_result, result)
                self.assertNotIn(FILE_update_all_self_update_resume, state.files)

    def test_take_resume_point___with_unknown_marker___returns_none_and_removes_it(self):
        for resume_point in ('downloader', 'unknown'):
            with self.subTest(resume_point=resume_point):
                sut, state, _fetcher, _downloader = _tester(files={
                    FILE_update_all_self_update_resume: {'content': resume_point},
                })

                self.assertIsNone(sut.take_resume_point())
                self.assertNotIn(FILE_update_all_self_update_resume, state.files)

    def test_take_resume_point___without_marker___returns_none(self):
        sut, _state, _fetcher, _downloader = _tester()

        self.assertIsNone(sut.take_resume_point())

    def test_take_resume_point___when_marker_cannot_be_inspected___returns_none(self):
        sut, state, _fetcher, _downloader = _tester(files={
            FILE_update_all_self_update_resume: {'content': 'after_downloader'},
        })

        def cannot_inspect(_path):
            raise OSError('inaccessible')

        sut._file_system.is_file = cannot_inspect

        self.assertIsNone(sut.take_resume_point())
        self.assertNotIn(FILE_update_all_self_update_resume, state.files)

    def test_take_resume_point___when_known_marker_cannot_be_removed___returns_none(self):
        for removal_error in (False, OSError('unremovable')):
            with self.subTest(removal_error=removal_error):
                sut, state, _fetcher, _downloader = _tester(files={
                    FILE_update_all_self_update_resume: {'content': 'after_downloader'},
                })

                def cannot_remove(_path, verbose=True):
                    del verbose
                    if removal_error:
                        raise removal_error
                    return False

                sut._file_system.unlink = cannot_remove

                self.assertIsNone(sut.take_resume_point())
                self.assertIn(FILE_update_all_self_update_resume, state.files)


def _tester(files=None, response=(200, b''), downloader=None, config=None, logger=None):
    config_provider = GenericProvider[Config]()
    config_provider.initialize(config or Config())
    state = FileSystemState(files=files)
    file_system = FileSystemFactory(
        state=state,
        config_provider=config_provider,
    ).create_for_system_scope()
    fetcher = _RecordingFetcherStub(response=response, config_provider=config_provider)
    downloader = downloader or _DownloaderServiceStub()
    return UpdateAllSelfUpdateServiceTester(
        config_provider=config_provider,
        logger=logger,
        file_system=file_system,
        downloader_service=downloader,
        fetcher=fetcher,
    ), state, fetcher, downloader


def _run_check(sut):
    if not sut.can_check_for_update():
        return False
    return sut.is_update_needed(
        sut.fetch_expected_hashes(),
        sut.hash_installed_files(),
    )


def _self_update_files(pyz_hash: str, model_hash: str) -> dict[str, dict[str, str]]:
    return {
        FILE_update_all_pyz: {'hash': pyz_hash},
        FILE_settings_screen_model_json_zip: {'hash': model_hash},
    }


def _update_all_db(pyz_hash: str, model_hash: str) -> bytes:
    return json.dumps({
        'db_id': 'update_all_mister',
        'files': {
            FILE_update_all_pyz: {'hash': pyz_hash},
            FILE_settings_screen_model_json_zip: {'hash': model_hash},
        },
    }).encode()


class _RecordingFetcherStub(FetcherStub):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.retries = []

    def fetch(self, url, method=None, body=None, headers=None, timeout=None, retry=3):
        self.retries.append(retry)
        return super().fetch(url, method, body, headers, timeout, retry)


class _DownloaderServiceStub:
    def __init__(self):
        self.command_calls = []

    def execute_downloader_command(self, _config, downloader_ini_path, args, logfile, quiet=False):
        self.command_calls.append((downloader_ini_path, args, logfile, quiet))
        return 0
