#!/usr/bin/env bash
# Copyright (c) 2022-2024 José Manuel Barroso Galindo <theypsilon@gmail.com>

set -euo pipefail

zip "update_all.zip" update_all.sh

gh release download --pattern "update_all.pyz update_all.pyz.sha256"
gh release upload "$(date +"%Y-%m-%d_%H-%M-%S")" "update_all.zip" "update_all.pyz" "update_all.pyz.sha256" --clobber
