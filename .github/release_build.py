#!/usr/bin/env python3
# Copyright (c) 2022-2024 José Manuel Barroso Galindo <theypsilon@gmail.com>

import subprocess
import os

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

    print("\nNew dont_download2.sh can be used.")
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write("new_build=yes\n")
else:
    print("Nothing to be updated.")
    subprocess.run(['rm', '-rf', 'build'], check=True)
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write("new_build=no\n")
