#!/usr/bin/env python3
# Copyright (c) 2022-2024 José Manuel Barroso Galindo <theypsilon@gmail.com>

import subprocess
import os
import time
import json
import hashlib

def hash_file(path: str) -> str:
    with open(path, "rb") as f:
        file_hash = hashlib.md5()
        chunk = f.read(8192)
        while chunk:
            file_hash.update(chunk)
            chunk = f.read(8192)
        return file_hash.hexdigest()

subprocess.run(['git', 'add', 'dont_download2.sh'], check=True)
subprocess.run(['git', 'commit', '-m', 'BOT: New dont_download2.sh'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(['git', 'fetch', 'origin', 'master'], check=True)
subprocess.run(['cp', 'dont_download2.sh', '/tmp/dont_download2.sh'], check=True)

diff_cmd = "git diff master:dont_download2.sh origin/master:dont_download2.sh"
filter_cmd = "grep '^[+-]' | grep -v 'export COMMIT' | grep -v '^\+\+\+' | grep -v '^---'"
changes = subprocess.getoutput(f"{diff_cmd} | {filter_cmd} | wc -l")

if int(changes) >= 1:
    print("There are changes to push:")
    print(changes)
    print()

    subprocess.run(['git', 'checkout', '--orphan', 'db'], check=True)
    subprocess.run(['git', 'rm', '-rf', '.'], check=False)
    subprocess.run(['git', 'add', 'dont_download2.sh'], check=True)
    subprocess.run(['git', 'commit', '-m', '-'], check=True)

    commit_id = subprocess.getoutput("git rev-parse HEAD")

    db = {
        "db_id": 'update_all_mister',
        "files": {
            'Scripts/.config/update_all/update_all_latest.zip': {
                'size': os.path.getsize('/tmp/dont_download2.sh'),
                'hash': hash_file('/tmp/dont_download2.sh'),
                'url': f'https://raw.githubusercontent.com/theypsilon/Update_All_MiSTer/{commit_id}/dont_download2.sh',
                'tags': ['updatealllatest', 'updateall']
            }
        },
        "folders": {'Scripts': {}, 'Scripts/.config': {}, 'Scripts/.config/update_all': {}},
        "timestamp":  int(time.time())
    }

    with open('update_all_db.json', 'w') as json_file:
        json.dump(db, json_file, indent=4)

    subprocess.run(['git', 'add', 'update_all_db.json'], check=True)
    subprocess.run(['git', 'commit', '-m', '-'], check=True)
    subprocess.run(['git', 'push', 'origin', 'master'], check=True)
    subprocess.run(['git', 'push', '--force', 'origin', 'db'], check=True)

    print("\nNew dont_download2.sh can be used.")
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write("NEW_RELEASE=yes\n")
else:
    print("Nothing to be updated.")
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write("NEW_RELEASE=no\n")

