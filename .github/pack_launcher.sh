#!/usr/bin/env bash
# Copyright (c) 2022 José Manuel Barroso Galindo <theypsilon@gmail.com>

set -euo pipefail

if ! gh release list | grep -q "latest" ; then
    gh release create "latest" || true
    sleep 15s
fi

zip "update_all.zip" update_all.sh
gh release upload "latest" "update_all.zip" --clobber
