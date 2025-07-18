#!/usr/bin/env python3
# Copyright (c) 2022-2025 José Manuel Barroso Galindo <theypsilon@gmail.com>

import copy
import subprocess
import os
import hashlib
import json
import time
import zipfile
from pathlib import Path
from typing import TypedDict
import requests


def save_json(obj, path_str):
    with open(path_str, 'w') as json_file:
        json.dump(obj, json_file, indent=4)

class FirmwareInfo(TypedDict):
    url: str
    version: str
    file: str
    md5: str
    size: float

def generate_pocket_firmware_details() -> FirmwareInfo:
    details_url = 'https://www.analogue.co/support/pocket/firmware/latest/details'
    details = requests.get(details_url).json()
    print('pocket_firmware_details:', json.dumps(details, indent=4))
    print()

    assert isinstance(details['download_url'], str) and len(details['download_url']) > 0, 'download_url is not a string'
    assert details['download_url'].startswith('https://') and details['download_url'].endswith('.bin'), 'download_url is not a valid URL'
    assert isinstance(details['version'], str) and len(details['version']) > 0, 'version is not a string'
    assert isinstance(details['file_size'], str) and len(details['file_size']) > 0, 'file_size is not a string'
    assert isinstance(details['md5'], str) and len(details['md5']) == 32, 'md5 is not a string or is not 32 chars long'

    def parse_size(size_str: str) -> float:
        assert size_str.endswith('MB'), 'size is not in MB'
        result = float(size_str[:-2])
        assert result > 0, 'size is not a positive number'
        assert result < 1000, 'size is too big'
        return result

    firmware_info: FirmwareInfo = {
        'url': details['download_url'],
        'version': details['version'],
        'file': Path(details['download_url']).name,
        'md5': details['md5'].lower(),
        'size': parse_size(details['file_size'])
    }
    return firmware_info

def nested_match(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        if a.keys() != b.keys():
            return False
        return all(nested_match(a[k], b[k]) for k in a)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        return all(nested_match(x, y) for x, y in zip(a, b))
    else:
        return a == b

def set_new_db(new_db: str) -> None:
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write(f"new_db={new_db}\n")

def hash_file(path: str) -> str:
    with open(path, "rb") as f:
        file_hash = hashlib.md5()
        chunk = f.read(8192)
        while chunk:
            file_hash.update(chunk)
            chunk = f.read(8192)
        return file_hash.hexdigest()

subprocess.run(['git', 'fetch', 'origin'], check=True)
try:
    subprocess.run(['git', 'checkout', 'origin/db',  '--', 'update_all_db.json'], check=True)
    with open('update_all_db.json', 'r') as json_file:
        old_db = json.load(json_file)
except Exception as e:
    print(e)
    old_db = {
        "db_id": 'update_all_mister',
        "files": {},
        "folders": {},
        "timestamp":  0
    }

for description in old_db['files'].values():
    if 'url' in description:
        description.pop('url')

subprocess.run(['git', 'checkout', '--orphan', 'db'], check=True)
subprocess.run(['git', 'reset'], check=True)
subprocess.run(['git', 'add', '.gitattributes'], check=True)
subprocess.run(['git', 'commit', '-m', '-'], check=True)

new_db = copy.deepcopy(old_db)

subprocess.run(["gh", "release", "download", "-p", "update_all.pyz", "-p", "update_all.pyz.sha256"], check=True)
hashsum = subprocess.run(['sha256sum', 'update_all.pyz'], check=True, capture_output=True, text=True).stdout.strip().split()[0]
with open('update_all.pyz.sha256', 'r') as f:
    expected_hashsum = f.read().strip().split()[0]

if hashsum != expected_hashsum:
    print(f'hash missmatch: {hashsum} != {expected_hashsum}')
    exit(1)

def fetch_file(path: str, url: str) -> None:
    response = requests.get(url)
    response.raise_for_status()
    with open(path, 'wb') as res_file:
        res_file.write(response.content)

fetch_file('mad_db.json.zip', 'https://raw.githubusercontent.com/MiSTer-devel/ArcadeDatabase_MiSTer/refs/heads/db/mad_db.json.zip')

with zipfile.ZipFile('mad_db.json.zip') as z:
    bad_file = z.testzip()
    if bad_file is not None:
        raise Exception('Zip is wrong:', bad_file)

fetch_file('update_all_latest_log.sh', 'https://raw.githubusercontent.com/theypsilon/Update_All_MiSTer/refs/heads/master/src/update_all/log_viewer.py')

save_json(generate_pocket_firmware_details(), 'pocket_firmware_details.json')

subprocess.run(['zip', 'update_all.zip', 'update_all.sh'], check=True)

subprocess.run(['git', 'add', 'update_all.pyz', 'update_all.pyz.sha256', 'update_all.sh', 'update_all_latest_log.sh', 'update_all.zip', 'mad_db.json.zip', 'pocket_firmware_details.json'], check=True)
subprocess.run(['git', 'commit', '-m', '-'], check=True)

new_db['files'] = {
    'Scripts/.config/update_all/update_all.pyz': {
        'size': os.path.getsize('update_all.pyz'),
        'hash': hash_file('update_all.pyz'),
    },
    'Scripts/.config/update_all/mad_db.json.zip': {
        'size': os.path.getsize('mad_db.json.zip'),
        'hash': hash_file('mad_db.json.zip'),
    },
    'Scripts/.config/update_all/pocket_firmware_details.json': {
        'size': os.path.getsize('pocket_firmware_details.json'),
        'hash': hash_file('pocket_firmware_details.json'),
    },
    'Scripts/update_all.sh': {
        'size': os.path.getsize('update_all.sh'),
        'hash': hash_file('update_all.sh'),
    },
    'Scripts/update_all_latest_log.sh': {
        'size': os.path.getsize('update_all_latest_log.sh'),
        'hash': hash_file('update_all_latest_log.sh'),
        'tags': [0],
    }
}
new_db['tag_dictionary'] = {
    'updatealllatestlog': 0
}
if 'tags_dictionary' in new_db:
    new_db.pop('tags_dictionary')
new_db['folders'] = {}
for file_path in new_db['files']:
    for parent in Path(file_path).parents:
        parent_str = str(parent)
        if parent_str == '.': continue
        new_db['folders'][parent_str] = {}

for file_path, desc in new_db['files'].items():
    if desc['size'] <= 0:
        print(f"File {file_path} has size {desc['size']}.")
        set_new_db('no')
        exit(1)
    if len(desc['hash']) != 32:
        print(f"File {file_path} has hash {desc['hash']}.")
        set_new_db('no')
        exit(1)

print('Candidate db:')
print(json.dumps(new_db, indent=4))
print()

if nested_match(old_db, new_db):
    print("Nothing to be updated.")
    set_new_db('no')
    exit(0)

print("There are changes to push.")

commit_id = subprocess.getoutput("git rev-parse HEAD")

for k, v in new_db['files'].items():
    file_name = Path(k).name
    v['url'] = f'https://raw.githubusercontent.com/theypsilon/Update_All_MiSTer/{commit_id}/{file_name}'

new_db['timestamp'] = int(time.time())
save_json(new_db, 'update_all_db.json')

print('New db:')
print(json.dumps(new_db, indent=4))
print('Old db:')
print(json.dumps(old_db, indent=4))
print()

subprocess.run(['git', 'add', 'update_all_db.json'], check=True)
subprocess.run(['git', 'commit', '-m', '-'], check=True)

set_new_db('yes')
