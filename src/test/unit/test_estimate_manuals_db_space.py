import io
import json
import unittest
import zipfile

import estimate_manuals_db_space as sut


class TestEstimateManualsDbSpace(unittest.TestCase):
    def test_calculate_clustered_file_bytes___rounds_each_file_up_independently(self):
        self.assertEqual(
            sut.calculate_clustered_file_bytes([1, 128 * 1024, 128 * 1024 + 1], 128 * 1024),
            4 * 128 * 1024,
        )

    def test_load_database_storage_summary___loads_json_zip_and_archive_summary_file_sizes(self):
        database_url = 'https://example.com/db.json.zip'
        summary_url = 'https://example.com/summary.json.zip'
        responses = {
            database_url: (_zip_json({
                'v': 1,
                'files': {
                    'first.bin': {'size': 1},
                    'second.bin': {'size': '10'},
                    'invalid.bin': {'size': -1},
                },
                'archives': {
                    'manuals': {
                        'summary_file': {'url': 'summary.json.zip'},
                    },
                },
            }), database_url),
            summary_url: (_zip_json({
                'files': {
                    'third.bin': {'size': 5},
                    'zero.bin': {'size': 0},
                    'missing.bin': {},
                },
            }), summary_url),
        }

        summary = sut.load_database_storage_summary(database_url, fetcher=lambda url: responses[url])

        self.assertEqual(summary.raw_bytes, 16)
        self.assertEqual(summary.sized_file_count, 4)
        self.assertEqual(summary.unsized_file_count, 2)

    def test_collect_database_file_sizes___supports_legacy_v0_zips(self):
        database = {
            'v': 0,
            'files': {},
            'zips': {
                'legacy': {
                    'kind': 'extract_all_contents',
                    'target_folder_path': '|games',
                    'internal_summary': {
                        'files': {
                            'manual.pdf': {'size': 1234, 'zip_id': 'legacy', 'zip_path': 'manual.pdf'},
                        },
                    },
                },
            },
        }

        file_sizes, unsized_file_count = sut.collect_database_file_sizes(database, 'https://example.com/db.json')

        self.assertEqual(file_sizes, [1234.0])
        self.assertEqual(unsized_file_count, 0)


def _zip_json(payload):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('db.json', json.dumps(payload))
    return buffer.getvalue()
