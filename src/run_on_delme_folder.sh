#!/usr/bin/env bash

set -euo pipefail

MAJOR_PYTHON_VERSION="$(python --version | awk '{print $2}' | cut -c 3)"
if [[ "${MAJOR_PYTHON_VERSION}" != "9" ]] ; then
  echo "Need Python 3.9!"
  if [ ! -d .venv ] ; then
    python3.9 -m venv .venv
  fi
  source .venv/bin/activate
  echo "Python 3.9 OK"
  echo
fi

TMP_FILE="$(mktemp)"

echo "Building..."
./src/build.sh > "${TMP_FILE}"

chmod +x "${TMP_FILE}"

export CURL_SSL=""
export LOCATION_STR="$(pwd)"
export DEBUG="${DEBUG:-true}"

echo "Running..."
echo "LOCATION_STR=${LOCATION_STR}"

"${TMP_FILE}"
