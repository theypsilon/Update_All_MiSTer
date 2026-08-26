#!/usr/bin/env python3
import io
import json
import math
import urllib.request
import zipfile
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin

from update_all.databases import ajgowans_manualsdbs


CLUSTER_SIZE_OPTIONS = [4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288, 1048576]


@dataclass(frozen=True)
class StorageSummary:
    raw_bytes: int
    sized_file_count: int
    unsized_file_count: int


OUTPUT_JSON_PATH = 'estimate_manuals_db_space.json'


def main():
    result = estimate_all_manuals_report()
    output = json.dumps(result, indent=2)
    print(output)
    with open(OUTPUT_JSON_PATH, 'w') as f:
        f.write(output)
    print(f'\nSaved to {OUTPUT_JSON_PATH}')


def estimate_all_manuals_report(fetcher=None):
    if fetcher is None:
        fetcher = _fetch_url_bytes

    all_file_sizes = []
    databases_report = []

    for database in ajgowans_manualsdbs():
        loaded_database, final_url = load_jsonish_url(database.db_url, fetcher=fetcher)
        file_sizes, unsized_file_count = collect_database_file_sizes(loaded_database, final_url, fetcher=fetcher)
        all_file_sizes.extend(file_sizes)
        sized_count = len(file_sizes)
        databases_report.append({
            'db_id': database.db_id,
            'title': database.title,
            'url': database.db_url,
            'file_count': sized_count + unsized_file_count,
            'sized_file_count': sized_count,
            'unsized_file_count': unsized_file_count,
            'raw_bytes': int(sum(file_sizes)),
            'cluster_estimates': cluster_estimates(file_sizes),
        })

    return {
        'databases': databases_report,
        'total': {
            'file_count': sum(d['file_count'] for d in databases_report),
            'sized_file_count': sum(d['sized_file_count'] for d in databases_report),
            'unsized_file_count': sum(d['unsized_file_count'] for d in databases_report),
            'raw_bytes': sum(d['raw_bytes'] for d in databases_report),
            'cluster_estimates': cluster_estimates(all_file_sizes),
        },
    }


def estimate_all_manuals_db_space(fetcher=None) -> StorageSummary:
    if fetcher is None:
        fetcher = _fetch_url_bytes

    raw_bytes = 0
    sized_file_count = 0
    unsized_file_count = 0

    for database in ajgowans_manualsdbs():
        database_summary = load_database_storage_summary(database.db_url, fetcher=fetcher)
        raw_bytes += database_summary.raw_bytes
        sized_file_count += database_summary.sized_file_count
        unsized_file_count += database_summary.unsized_file_count

    return StorageSummary(
        raw_bytes=raw_bytes,
        sized_file_count=sized_file_count,
        unsized_file_count=unsized_file_count,
    )


def load_database_storage_summary(url: str, fetcher=None) -> StorageSummary:
    if fetcher is None:
        fetcher = _fetch_url_bytes

    database, final_url = load_jsonish_url(url, fetcher=fetcher)
    file_sizes, unsized_file_count = collect_database_file_sizes(database, final_url, fetcher=fetcher)

    return StorageSummary(
        raw_bytes=int(sum(file_sizes)),
        sized_file_count=len(file_sizes),
        unsized_file_count=unsized_file_count,
    )


def cluster_estimates(file_sizes):
    return [
        {
            'cluster_size_bytes': cluster_size_bytes,
            'cluster_size_gb': _bytes_to_gb(cluster_size_bytes),
            'estimated_bytes': (estimated := calculate_clustered_file_bytes(file_sizes, cluster_size_bytes)),
            'estimated_gb': _bytes_to_gb(estimated),
        }
        for cluster_size_bytes in CLUSTER_SIZE_OPTIONS
    ]


def _bytes_to_gb(b: int) -> str:
    return f'{b / 1_073_741_824:.2f} GB'


def estimate_all_manuals_cluster_sizes(fetcher=None):
    if fetcher is None:
        fetcher = _fetch_url_bytes

    file_sizes = []
    for database in ajgowans_manualsdbs():
        loaded_database, final_url = load_jsonish_url(database.db_url, fetcher=fetcher)
        database_file_sizes, _ = collect_database_file_sizes(loaded_database, final_url, fetcher=fetcher)
        file_sizes.extend(database_file_sizes)

    return cluster_estimates(file_sizes)


def calculate_clustered_file_bytes(file_sizes: list[float], cluster_size_bytes: int) -> int:
    if cluster_size_bytes <= 0:
        return 0

    clustered_total = 0
    for size in file_sizes:
        if not math.isfinite(size) or size <= 0:
            continue
        clustered_total += math.ceil(size / cluster_size_bytes) * cluster_size_bytes
    return clustered_total


def collect_database_file_sizes(database, source_url: str, fetcher=None):
    if fetcher is None:
        fetcher = _fetch_url_bytes

    file_sizes = []
    unsized_file_count = 0

    for file_record in _as_dict(database.get('files')).values():
        size = _normalize_record_size(_as_dict(file_record).get('size'))
        if size is None:
            unsized_file_count += 1
        else:
            file_sizes.append(size)

    version = database.get('v') if isinstance(database.get('v'), int) else 0
    archives = derive_inspectable_archives(database, version)
    for archive in archives.values():
        archive_record = _as_dict(archive)

        summary = None
        if isinstance(archive_record.get('summary_inline'), dict):
            summary = archive_record['summary_inline']
        elif isinstance(archive_record.get('summary_file'), dict):
            summary_url = str(archive_record['summary_file'].get('url', '')).strip()
            if summary_url:
                summary, _ = load_jsonish_url(urljoin(source_url, summary_url), fetcher=fetcher)
                if archive_record.get('__legacyZip'):
                    summary = convert_legacy_zip_summary(
                        zip_id='archive',
                        summary=summary,
                        archive_path_kind=_get_string(archive_record.get('path')),
                        extract_mode=_get_string(archive_record.get('extract')),
                    )

        if not isinstance(summary, dict):
            continue

        for file_record in _as_dict(summary.get('files')).values():
            size = _normalize_record_size(_as_dict(file_record).get('size'))
            if size is None:
                unsized_file_count += 1
            else:
                file_sizes.append(size)

    return file_sizes, unsized_file_count


def derive_inspectable_archives(database, version):
    explicit_archives = _as_dict(database.get('archives'))
    if version != 0:
        return explicit_archives

    legacy_zips = _as_dict(database.get('zips'))
    derived_archives = {
        zip_id: convert_legacy_zip_to_archive(zip_id, zip_record)
        for zip_id, zip_record in legacy_zips.items()
        if isinstance(zip_record, dict)
    }

    result = dict(derived_archives)
    result.update(explicit_archives)
    return result


def convert_legacy_zip_to_archive(zip_id, zip_record):
    legacy_zip = _as_dict(zip_record)
    archive = {
        '__legacyZip': True,
        'format': _get_string(legacy_zip.get('format')) or 'zip',
        'extract': _legacy_zip_extract_mode(_get_string(legacy_zip.get('kind'))),
        'description': _get_string(legacy_zip.get('description')) or zip_id,
        'target_folder': _normalized_legacy_target_folder(legacy_zip),
        'archive_file': _as_dict(legacy_zip.get('contents_file')),
        'base_files_url': _get_string(legacy_zip.get('base_files_url')) or None,
        'path': _legacy_archive_path(legacy_zip),
    }

    if isinstance(legacy_zip.get('internal_summary'), dict):
        archive['summary_inline'] = convert_legacy_zip_summary(
            zip_id=zip_id,
            summary=legacy_zip['internal_summary'],
            archive_path_kind=_get_string(archive.get('path')),
            extract_mode=_get_string(archive.get('extract')),
        )
    elif isinstance(legacy_zip.get('summary_file'), dict):
        archive['summary_file'] = dict(legacy_zip['summary_file'])

    return archive


def convert_legacy_zip_summary(zip_id, summary, archive_path_kind: str, extract_mode: str):
    del zip_id
    summary_record = _as_dict(summary)
    files = _as_dict(summary_record.get('files'))
    folders = _as_dict(summary_record.get('folders'))
    should_force_pext = extract_mode == 'all' and archive_path_kind == 'pext'
    should_remove_pext = extract_mode == 'all' and archive_path_kind != 'pext'

    return {
        **summary_record,
        'files': {
            path: _convert_legacy_summary_entry(file_record, should_force_pext, should_remove_pext)
            for path, file_record in files.items()
        },
        'folders': {
            path: _convert_legacy_summary_entry(folder_record, should_force_pext, should_remove_pext)
            for path, folder_record in folders.items()
        },
    }


def load_jsonish_url(url: str, fetcher=None):
    if fetcher is None:
        fetcher = _fetch_url_bytes

    content, final_url = fetcher(url)
    return decode_jsonish(content, final_url.split('/')[-1] or url), final_url


def decode_jsonish(content: bytes, source_name: str):
    lower_source_name = source_name.lower()
    if lower_source_name.endswith('.zip') or _looks_like_zip(content):
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            file_names = [name for name in archive.namelist() if not name.endswith('/')]
            if not file_names:
                raise ValueError(f'ZIP archive {source_name} does not contain any files.')
            json_name = next((name for name in file_names if name.lower().endswith('.json')), file_names[0])
            with archive.open(json_name) as entry:
                return json.load(entry)

    return json.loads(content.decode())


def _convert_legacy_summary_entry(entry, should_force_pext: bool, should_remove_pext: bool):
    converted = dict(_as_dict(entry))
    if 'zip_id' in converted:
        converted['arc_id'] = converted.pop('zip_id')
    if 'zip_path' in converted:
        converted['arc_at'] = converted.pop('zip_path')

    if should_force_pext:
        converted['path'] = 'pext'
    elif should_remove_pext and converted.get('path') == 'pext':
        del converted['path']

    return converted


def _fetch_url_bytes(url: str):
    with urllib.request.urlopen(url) as response:
        return response.read(), response.geturl()


def _normalize_record_size(value):
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(numeric_value) or numeric_value < 0:
        return None
    return numeric_value


def _looks_like_zip(content: bytes) -> bool:
    return len(content) >= 4 and content[:2] == b'PK'


def _legacy_zip_extract_mode(kind: str) -> str:
    return {
        'extract_all_contents': 'all',
        'extract_single_files': 'selective',
    }.get(kind, kind)


def _normalized_legacy_target_folder(legacy_zip) -> Optional[str]:
    target_folder_path = _get_string(legacy_zip.get('target_folder_path'))
    if target_folder_path.startswith('|'):
        return target_folder_path[1:] or None
    return target_folder_path or None


def _legacy_archive_path(legacy_zip):
    target_folder_path = _get_string(legacy_zip.get('target_folder_path'))
    explicit_path = _get_string(legacy_zip.get('path'))
    if explicit_path:
        return explicit_path
    if target_folder_path.startswith('|'):
        return 'pext'
    return None


def _as_dict(value):
    return value if isinstance(value, dict) else {}


def _get_string(value) -> str:
    return value if isinstance(value, str) else ''
if __name__ == '__main__':
    main()
