#!/usr/bin/env python3
import json
import os
import shutil
import sys
import time
from pathlib import Path


def copy_atomically(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + '.mock-downloader.tmp')
    shutil.copyfile(source, temporary)
    os.replace(temporary, target)


args = sys.argv[1:]
run_only = len(args) >= 2 and args[0] == '--run-only'
mode = 'run-only' if run_only else 'standard'
logfile = os.environ.get('LOGFILE')

try:
    Path('/tmp/downloader_run_signal').unlink()
except FileNotFoundError:
    pass

call = {
    'args': args,
    'default_db_id': os.environ.get('DEFAULT_DB_ID'),
    'downloader_ini_path': os.environ.get('DOWNLOADER_INI_PATH'),
    'logfile': logfile,
    'mode': mode,
    'timestamp': time.time(),
    'update_linux': os.environ.get('UPDATE_LINUX'),
}
with open(os.environ['MOCK_DOWNLOADER_CALLS_PATH'], 'a') as calls:
    calls.write(json.dumps(call, sort_keys=True) + '\n')

print('MOCK_DOWNLOADER mode=' + mode + ' args=' + json.dumps(args), flush=True)
if logfile is not None:
    log_path = Path(logfile)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text('MOCK_DOWNLOADER mode=' + mode + '\n')

exit_code = int(os.environ.get('MOCK_RUN_ONLY_EXIT_CODE' if run_only else 'MOCK_STANDARD_EXIT_CODE', '0'))
if exit_code == 0 and os.environ.get('MOCK_INSTALL_FILES', 'true').lower() == 'true':
    root = Path(os.environ['LOCATION_STR'])
    copy_atomically(
        Path(os.environ['MOCK_UPDATE_ALL_PYZ_SOURCE']),
        root / 'Scripts/.config/update_all/update_all.pyz',
    )
    copy_atomically(
        Path(os.environ['MOCK_SETTINGS_MODEL_SOURCE']),
        root / 'Scripts/.config/update_all/settings_screen_model.json.zip',
    )

raise SystemExit(exit_code)
