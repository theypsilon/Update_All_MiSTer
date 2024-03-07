#!/usr/bin/env python3
# Copyright (c) 2022-2024 José Manuel Barroso Galindo <theypsilon@gmail.com>

import subprocess
import os

subprocess.run(['git', 'add', 'dont_download2.sh'], check=True)
subprocess.run(['git', 'commit', '-m', 'BOT: New dont_download2.sh'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(['git', 'fetch', 'origin', 'master'], check=True)

diff_cmd = "git diff master:dont_download2.sh origin/master:dont_download2.sh"
filter_cmd = "grep '^[+-]' | grep -v 'export COMMIT' | grep -v '^\+\+\+' | grep -v '^---'"
changes = int(subprocess.getoutput(f"{diff_cmd} | {filter_cmd} | wc -l"))

if changes >= 1:
    print("There are changes to push.\n")
    subprocess.run(['git', 'push', 'origin', 'master'], check=True)
    print("\nNew dont_download2.sh can be used.")
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write("NEW_RELEASE=yes\n")
else:
    print("Nothing to be updated.")
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write("NEW_RELEASE=no\n")
