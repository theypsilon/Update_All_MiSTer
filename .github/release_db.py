#!/usr/bin/env python3
# Copyright (c) 2022-2025 José Manuel Barroso Galindo <theypsilon@gmail.com>

import copy
import subprocess
import os
import hashlib
import json
import time
from pathlib import Path

no_check = 'no_check'

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
        return a == b or a == no_check or b == no_check

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

new_db = copy.deepcopy(old_db)

update_all_pyz = Path('build/update_all.pyz')
if update_all_pyz.exists():
    update_all_pyz.replace('update_all.pyz')
else:
    subprocess.run(['git', 'checkout', 'origin/db', '--', 'update_all.pyz'], check=True)

new_db['files'] = {
    'Scripts/.config/update_all/update_all.pyz': {
        'size': os.path.getsize('update_all.pyz'),
        'hash': hash_file('update_all.pyz'),
        'url': no_check
    },
    'Scripts/update_all.sh': {
        'size': os.path.getsize('update_all.sh'),
        'hash': hash_file('update_all.sh'),
        'url': no_check
    }
}
new_db['folders'] = {
    'Scripts': {},
    'Scripts/.config': {},
    'Scripts/.config/update_all': {},
}

for file_path, desc in new_db['files'].items():
    if desc['size'] <= 0:
        print(f"File {file_path} has size {desc['size']}.")
        set_new_db('no')
        exit(1)
    if len(desc['hash']) != 32:
        print(f"File {file_path} has hash {desc['hash']}.")
        set_new_db('no')
        exit(1)

if nested_match(old_db, new_db):
    print("Nothing to be updated.")
    set_new_db('no')
    exit(0)

print("There are changes to push.")
print('old_db', old_db)
print('new_db', new_db)

subprocess.run(['git', 'checkout', '--orphan', 'db'], check=True)
subprocess.run(['git', 'reset'], check=True)
subprocess.run('sha256sum update_all.pyz > update_all.pyz.sha256', shell=True, check=True)
subprocess.run(['git', 'add', 'update_all.pyz', 'update_all.pyz.sha256', 'update_all.sh'], check=True)
subprocess.run(['git', 'commit', '-m', '-'], check=True)
commit_id = subprocess.getoutput("git rev-parse HEAD")

new_db['files']['Scripts/.config/update_all/update_all.pyz']['url'] = f'https://raw.githubusercontent.com/theypsilon/Update_All_MiSTer/{commit_id}/update_all.pyz'
new_db['files']['Scripts/update_all.sh']['url'] = f'https://raw.githubusercontent.com/theypsilon/Update_All_MiSTer/{commit_id}/update_all.sh'

new_db['timestamp'] = int(time.time())
with open('update_all_db.json', 'w') as json_file:
    json.dump(new_db, json_file, indent=4)

subprocess.run(['git', 'add', 'update_all_db.json'], check=True)
subprocess.run(['git', 'commit', '-m', '-'], check=True)
subprocess.run(['git', 'push', '--force', 'origin', 'db'], check=True)

set_new_db('yes')