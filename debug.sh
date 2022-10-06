#!/usr/bin/env bash
# Copyright (c) 2021-2022 José Manuel Barroso Galindo <theypsilon@gmail.com>

set -euo pipefail

MISTER_IP=${MISTER_IP:-$(cat "mister.ip" | tr -d '[:space:]')}
MISTER_PW=1
if [ -f mister.pw ] ; then
    MISTER_PW=$(cat "mister.pw" | tr -d '[:space:]')
fi

sshpass -p "${MISTER_PW}" scp -o StrictHostKeyChecking=no dont_download.sh "root@${MISTER_IP}:/media/fat/Scripts/dont_download.sh"

echo "OK"
