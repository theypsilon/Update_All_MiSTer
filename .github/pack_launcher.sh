#!/usr/bin/env bash
# Copyright (c) 2022-2024 José Manuel Barroso Galindo <theypsilon@gmail.com>

set -euo pipefail

zip "update_all.zip" update_all.sh

release_tag="$(date +"%Y-%m-%d_%H-%M-%S")"
gh release download --pattern "update_all.pyz update_all.pyz.sha256"
gh release create "$release_tag"
gh release upload "$release_tag" "update_all.zip" "update_all.pyz" "update_all.pyz.sha256" --clobber
