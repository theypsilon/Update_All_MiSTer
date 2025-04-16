#!/usr/bin/env python3
# Copyright (c) 2022-2025 José Manuel Barroso Galindo <theypsilon@gmail.com>

import subprocess
import os
import time
import datetime

subprocess.run(['git', 'add', 'dont_download2.sh', 'latest.id'], check=True)
subprocess.run(['git', 'commit', '-m', 'BOT: New dont_download2.sh'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(['git', 'fetch', 'origin', 'master'], check=True)

def file_has_changed(branch_a, branch_b, file_path):
    def get_blob(branch):
        try:
            result = subprocess.run(
                ["git", "rev-parse", f"{branch}:{file_path}"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    blob_a = get_blob(branch_a)
    blob_b = get_blob(branch_b)

    return blob_a != blob_b or (blob_a is None) != (blob_b is None)

if file_has_changed("master", "origin/master", "latest.id"):
    print("There are changes to push.")

    subprocess.run(['git', 'push', 'origin', 'master'], check=True)

    subprocess.run('cd build; sha256sum update_all.pyz > update_all.pyz.sha256', shell=True, check=True)
    subprocess.run(['zip', 'build/update_all.zip', 'update_all.sh'], check=True)

    release_tag = datetime.datetime.now().strftime("UpdateAll_%Y-%m-%d_%H.%M.%S")
    print('Creating release', release_tag)
    subprocess.run(['gh', 'release', 'create', release_tag], check=True)
    subprocess.run(['gh', 'release', 'upload', release_tag, 'build/update_all.pyz', 'build/update_all.pyz.sha256', 'build/update_all.zip', '--clobber'], check=True)

    print("\nNew dont_download2.sh can be used.")
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write("new_build=yes\n")
else:
    print("Nothing to be updated.")
    subprocess.run(['rm', '-rf', 'build'], check=True)
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write("new_build=no\n")
