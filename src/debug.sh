#!/usr/bin/env bash
# Copyright (c) 2022-2024 José Manuel Barroso Galindo <theypsilon@gmail.com>

set -euo pipefail

MISTER_IP=${MISTER_IP:-$(cat "mister.ip" | tr -d '[:space:]')}
MISTER_PW=1
if [ -f mister.pw ] ; then
    MISTER_PW=$(cat "mister.pw" | tr -d '[:space:]')
fi

TEMP_SCRIPT="$(mktemp)"

DEBUG=true MISTER=true ./src/build.sh > "${TEMP_SCRIPT}"
chmod +x "${TEMP_SCRIPT}"

if [ -f dont_download.ini ] ; then
  sshpass -p "${MISTER_PW}" scp -o StrictHostKeyChecking=no dont_download.ini "root@${MISTER_IP}:/media/fat/Scripts/update_all.ini"
fi
sshpass -p "${MISTER_PW}" scp -o StrictHostKeyChecking=no "${TEMP_SCRIPT}" "root@${MISTER_IP}:/media/fat/update_all.sh"
sshpass -p "${MISTER_PW}" scp -o StrictHostKeyChecking=no "${TEMP_SCRIPT}" "root@${MISTER_IP}:/media/fat/Scripts/ua2.sh"
sshpass -p "${MISTER_PW}" scp -o StrictHostKeyChecking=no update_all.sh "root@${MISTER_IP}:/media/fat/Scripts/update_all.sh"
rm "${TEMP_SCRIPT}"

if [[ "${1:-}" == 'run' ]] ; then
  sshpass -p "${MISTER_PW}" ssh -o StrictHostKeyChecking=no "root@${MISTER_IP}" "/media/fat/update_all.sh ${2:-}"
else
  echo "OK"
fi