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
import hashlib
import json
import unittest
import zipfile
from io import BytesIO
from typing import Optional

from test.fake_filesystem import FileSystemFactory
from test.file_system_tester_state import FileSystemState
from test.logger_tester import LoggerSpy, NoLogger
from test.spy_os_utils import SpyOsUtils
from test.update_all_service_tester import IniRepositoryTester
from update_all.config import Config
from update_all.constants import DOWNLOADER_LATEST_ZIP_PATH, DOWNLOADER_URL, FILE_downloader_run_signal
from update_all.databases import MIRROR_ANDI_BR, all_dbs
from update_all.downloader_service import DownloaderService
from update_all.ini_parser import IniParser


_INJECTED_DOWNLOADER_PATH = 'fixtures/fake_downloader'
_INJECTED_PYTHON_COMPATIBLE_PATH = 'fixtures/python3.9'
_INJECTED_DOWNLOADER_TEMP_PATH = '/tmp/ua_downloader_bin'


class TestDownloaderService(unittest.TestCase):
    def test_execute_downloader_command___with_injected_path___copies_and_executes_injected_downloader(self):
        config = Config(
            downloader_path=_INJECTED_DOWNLOADER_PATH,
            downloader_python_compatible_path=_INJECTED_PYTHON_COMPATIBLE_PATH,
        )
        service, file_system, os_utils, fetcher = _service(
            config,
            files={
                _INJECTED_DOWNLOADER_PATH: {'content': '#!/bin/sh\n'},
                _INJECTED_PYTHON_COMPATIBLE_PATH: {'content': ''},
            },
        )
        os_utils.execute_process_action = lambda: file_system.unlink(FILE_downloader_run_signal, verbose=False)

        result = service.execute_downloader_command(
            config,
            '/media/fat/downloader.ini',
            ['--run-only', 'update_all_mister'],
            '/media/fat/Scripts/.config/update_all/self_update_downloader.log',
            quiet=True,
        )

        self.assertEqual(0, result)
        self.assertEqual([], fetcher.calls)
        self.assertEqual([_INJECTED_DOWNLOADER_TEMP_PATH], os_utils.calls_to_make_executable)
        self.assertEqual(1, len(os_utils.calls_to_execute_process))
        launcher, env, quiet, args = os_utils.calls_to_execute_process[0]
        self.assertEqual(_INJECTED_DOWNLOADER_TEMP_PATH, launcher)
        self.assertEqual(
            '/media/fat/Scripts/.config/update_all/self_update_downloader.log',
            env['LOGFILE'],
        )
        self.assertTrue(quiet)
        self.assertEqual(['--run-only', 'update_all_mister'], args)
        self.assertTrue(file_system.is_file(_INJECTED_DOWNLOADER_PATH))

        service.cleanup_temp_launchers()

        self.assertTrue(file_system.is_file(_INJECTED_DOWNLOADER_PATH))
        self.assertFalse(file_system.is_file(_INJECTED_DOWNLOADER_TEMP_PATH))

    def test_execute_downloader___when_injected_path_fails___uses_existing_fallback_chain(self):
        url = 'http://127.0.0.1:8765/downloader.pyz'
        config = Config(
            downloader_path=_INJECTED_DOWNLOADER_PATH,
            downloader_url=url,
            downloader_python_compatible_path=_INJECTED_PYTHON_COMPATIBLE_PATH,
        )
        service, file_system, os_utils, fetcher = _service(config, files={
            _INJECTED_DOWNLOADER_PATH: {'content': '#!/bin/sh\n'},
            _INJECTED_PYTHON_COMPATIBLE_PATH: {'content': ''},
            DOWNLOADER_LATEST_ZIP_PATH: {'content': 'zipapp'},
        })
        call_count = 0

        def complete_second_downloader():
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                file_system.unlink(FILE_downloader_run_signal, verbose=False)

        os_utils.execute_process_action = complete_second_downloader

        result = service.execute_downloader(
            config,
            '/media/fat/downloader.ini',
            skip_linux_update=False,
            logfile=None,
            default_db=None,
        )

        self.assertEqual(0, result)
        self.assertEqual([], fetcher.calls)
        self.assertEqual(
            [_INJECTED_DOWNLOADER_TEMP_PATH, '/tmp/ua_downloader_latest.zip'],
            [call[0] for call in os_utils.calls_to_execute_process],
        )

    def test_execute_downloader___when_local_launchers_fail___uses_fetched_launcher(self):
        url = 'http://127.0.0.1:8765/downloader.pyz'
        config = Config(
            downloader_path=_INJECTED_DOWNLOADER_PATH,
            downloader_url=url,
            downloader_python_compatible_path=_INJECTED_PYTHON_COMPATIBLE_PATH,
        )
        service, _file_system, os_utils, fetcher = _service(config, files={
            _INJECTED_DOWNLOADER_PATH: {'content': '#!/bin/sh\n'},
            _INJECTED_PYTHON_COMPATIBLE_PATH: {'content': ''},
            DOWNLOADER_LATEST_ZIP_PATH: {'content': 'zipapp'},
        })

        result = service.execute_downloader(
            config,
            '/media/fat/downloader.ini',
            skip_linux_update=False,
            logfile=None,
            default_db=None,
        )

        self.assertEqual(0, result)
        self.assertEqual([(url, 0)], fetcher.calls)
        self.assertEqual(
            [
                _INJECTED_DOWNLOADER_TEMP_PATH,
                '/tmp/ua_downloader_latest.zip',
                '/tmp/ua_downloader_dd.pyz',
            ],
            [call[0] for call in os_utils.calls_to_execute_process],
        )

    def test_execute_downloader___without_local_candidate___uses_injected_fallback_url(self):
        url = 'http://127.0.0.1:8765/downloader.pyz'
        config = Config(downloader_url=url)
        logger = LoggerSpy()
        service, _file_system, os_utils, fetcher = _service(config, logger=logger)

        result = service.execute_downloader(
            config,
            '/media/fat/downloader.ini',
            skip_linux_update=False,
            logfile=None,
            default_db=None,
        )

        self.assertEqual(0, result)
        self.assertEqual([(url, 0)], fetcher.calls)
        self.assertEqual(
            ['/tmp/ua_downloader_dd.pyz'],
            [call[0] for call in os_utils.calls_to_execute_process],
        )
        self.assertIn(f'Using configured Downloader bootstrap URL: {url}', logger.debug_lines)

    def test_execute_downloader___without_local_candidate___uses_selected_mirrored_distribution_db(self):
        selected_db_url = 'https://configured-mirror.example/distribution.json.zip'
        config = Config(mirror=MIRROR_ANDI_BR)
        downloader_url = 'https://mirror.example/downloader_latest.zip'
        downloader = b'selected mirror downloader'
        logger = LoggerSpy()
        service, _file_system, os_utils, fetcher = _service(
            config,
            files=_distribution_files(selected_db_url),
            logger=logger,
        )
        _fetch_responses(fetcher, {
            selected_db_url: _database_zip(
                downloader_url,
                downloader,
                base_files_url='https://base.example/',
            ),
            downloader_url: downloader,
        })

        result = service.execute_downloader(
            config,
            '/media/fat/downloader.ini',
            skip_linux_update=False,
            logfile=None,
            default_db=None,
        )

        self.assertEqual(0, result)
        self.assertEqual([(selected_db_url, 3), (downloader_url, 1)], fetcher.calls)
        self.assertEqual([
            'Preparing Downloader launcher attempt 1/3',
            f'Trying configured Distribution database for Downloader bootstrap: {selected_db_url}',
            f'Distribution database resolved Downloader bootstrap file: {downloader_url}',
            'Downloader bootstrap integrity validated',
            'Downloader launcher finished with exit code 0',
        ], logger.debug_lines)

    def test_execute_downloader___when_file_url_is_missing___derives_it_from_base_files_url(self):
        selected_db_url = 'https://configured-mirror.example/distribution.json.zip'
        base_files_url = 'https://raw.example/distribution/'
        downloader_url = base_files_url + DOWNLOADER_LATEST_ZIP_PATH
        downloader = b'base files URL downloader'
        config = Config()
        service, _file_system, os_utils, fetcher = _service(
            config,
            files=_distribution_files(selected_db_url),
        )
        _fetch_responses(fetcher, {
            selected_db_url: _database_zip(
                None,
                downloader,
                base_files_url=base_files_url,
            ),
            downloader_url: downloader,
        })

        result = service.execute_downloader(
            config,
            '/media/fat/downloader.ini',
            skip_linux_update=False,
            logfile=None,
            default_db=None,
        )

        self.assertEqual(0, result)
        self.assertEqual([(selected_db_url, 3), (downloader_url, 1)], fetcher.calls)
        self.assertEqual(
            ['/tmp/ua_downloader_dd.pyz'],
            [call[0] for call in os_utils.calls_to_execute_process],
        )

    def test_execute_downloader___when_selected_distribution_db_fails___uses_official_distribution_db(self):
        selected_db_url = 'https://configured.example/distribution.json.zip'
        config = Config()
        db_defs = all_dbs(config.mirror)
        official_db_url = db_defs.MISTER_DEVEL_DISTRIBUTION_MISTER.db_url
        downloader_url = 'https://distribution.example/downloader_latest.zip'
        downloader = b'official distribution downloader'
        service, _file_system, os_utils, fetcher = _service(config, files=_distribution_files(selected_db_url))
        _fetch_responses(fetcher, {
            selected_db_url: None,
            official_db_url: _database_zip(downloader_url, downloader),
            downloader_url: downloader,
        })

        result = service.execute_downloader(
            config,
            '/media/fat/downloader.ini',
            skip_linux_update=False,
            logfile=None,
            default_db=None,
        )

        self.assertEqual(0, result)
        self.assertEqual(
            [(selected_db_url, 3), (official_db_url, 3), (downloader_url, 1)],
            fetcher.calls,
        )

    def test_execute_downloader___rejects_distribution_download_with_wrong_hash_or_size(self):
        for invalid_field in ('hash', 'size'):
            with self.subTest(invalid_field=invalid_field):
                selected_db_url = 'https://configured.example/distribution.json.zip'
                config = Config()
                db_defs = all_dbs(config.mirror)
                official_db_url = db_defs.MISTER_DEVEL_DISTRIBUTION_MISTER.db_url
                selected_downloader_url = 'https://selected.example/downloader_latest.zip'
                official_downloader_url = 'https://official.example/downloader_latest.zip'
                selected_downloader = b'invalid selected downloader'
                official_downloader = b'valid official downloader'
                expected_hash = hashlib.md5(b'different contents').hexdigest() if invalid_field == 'hash' else None
                expected_size = len(selected_downloader) + 1 if invalid_field == 'size' else None
                service, _file_system, os_utils, fetcher = _service(config, files=_distribution_files(selected_db_url))
                _fetch_responses(fetcher, {
                    selected_db_url: _database_zip(
                        selected_downloader_url,
                        selected_downloader,
                        expected_hash=expected_hash,
                        expected_size=expected_size,
                    ),
                    selected_downloader_url: selected_downloader,
                    official_db_url: _database_zip(official_downloader_url, official_downloader),
                    official_downloader_url: official_downloader,
                })

                result = service.execute_downloader(
                    config,
                    '/media/fat/downloader.ini',
                    skip_linux_update=False,
                    logfile=None,
                    default_db=None,
                )

                self.assertEqual(0, result)
                self.assertEqual(
                    [
                        (selected_db_url, 3),
                        (selected_downloader_url, 1),
                        (official_db_url, 3),
                        (official_downloader_url, 1),
                    ],
                    fetcher.calls,
                )

    def test_execute_downloader___when_distribution_db_bootstrap_fails___uses_raw_fallback_once(self):
        config = Config()
        official_db_url = all_dbs(config.mirror).MISTER_DEVEL_DISTRIBUTION_MISTER.db_url
        logger = LoggerSpy()
        service, _file_system, os_utils, fetcher = _service(config, logger=logger)
        _fetch_responses(fetcher, {
            official_db_url: b'{}',
            DOWNLOADER_URL: b'raw fallback downloader',
        })

        result = service.execute_downloader(
            config,
            '/media/fat/downloader.ini',
            skip_linux_update=False,
            logfile=None,
            default_db=None,
        )

        self.assertEqual(0, result)
        self.assertEqual([(official_db_url, 3), (DOWNLOADER_URL, 3)], fetcher.calls)
        self.assertIn(f'Falling back to direct Downloader bootstrap: {DOWNLOADER_URL}', logger.debug_lines)

    def test_execute_downloader___when_fetcher_raises___returns_failure(self):
        url = 'https://configured.example/downloader.pyz'
        config = Config(downloader_url=url)
        service, _file_system, _os_utils, fetcher = _service(config)
        _fetch_responses(fetcher, {url: RuntimeError('fetch failed')})

        result = service.execute_downloader(
            config,
            '/media/fat/downloader.ini',
            skip_linux_update=False,
            logfile=None,
            default_db=None,
        )

        self.assertEqual(1, result)
        self.assertEqual([(url, 0)], fetcher.calls)


def _service(config: Config, files=None, logger=None):
    state = FileSystemState(config=config, files=files)
    file_system = FileSystemFactory(state=state).create_for_system_scope()
    os_utils = SpyOsUtils()
    ini_repository = IniRepositoryTester(file_system=file_system, os_utils=os_utils)
    ini_repository.resolve_all_database_sections({
        db_id: IniParser(section)
        for db_id, section in ini_repository.get_downloader_ini(cached=False).items()
    })
    fetcher = _FetcherStub()
    return (
        DownloaderService(logger or NoLogger(), file_system, os_utils, ini_repository, fetcher),
        file_system,
        os_utils,
        fetcher,
    )


def _fetch_responses(fetcher, responses: dict[str, object]) -> None:
    fetcher.responses = responses


class _FetcherStub:
    def __init__(self):
        self.calls: list[tuple[str, int]] = []
        self.responses: dict[str, object] = {}

    def fetch(self, url, method=None, body=None, headers=None, timeout=None, retry=3):
        self.calls.append((url, retry))
        if url not in self.responses:
            return 200, b''

        response = self.responses[url]
        if isinstance(response, Exception):
            raise response
        if response is None:
            return 503, b''
        return 200, response


def _distribution_files(db_url: str) -> dict[str, dict[str, str]]:
    return {
        '/media/fat/downloader.ini': {
            'content': f'[distribution_mister]\ndb_url = {db_url}\n',
        },
    }


def _database_zip(
        downloader_url: Optional[str],
        downloader: bytes,
        expected_hash: Optional[str] = None,
        expected_size: Optional[int] = None,
        base_files_url: Optional[str] = None,
) -> bytes:
    file_description = {
        'hash': expected_hash or hashlib.md5(downloader).hexdigest(),
        'size': len(downloader) if expected_size is None else expected_size,
    }
    if downloader_url is not None:
        file_description['url'] = downloader_url
    database = {
        'files': {
            DOWNLOADER_LATEST_ZIP_PATH: file_description,
        },
    }
    if base_files_url is not None:
        database['base_files_url'] = base_files_url
    result = BytesIO()
    with zipfile.ZipFile(result, 'w', compression=zipfile.ZIP_DEFLATED) as db_zip:
        db_zip.writestr('db.json', json.dumps(database))
    return result.getvalue()


if __name__ == '__main__':
    unittest.main()
