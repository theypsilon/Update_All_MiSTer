#!/usr/bin/env bash
# Copyright (c) 2022-2024 José Manuel Barroso Galindo <theypsilon@gmail.com>

set -euo pipefail

UPDATE_ALL_ZIP="update_all_latest.zip"
TEMP_ZIP2="$(mktemp -u).zip"
BIN="/tmp/dont_download.zip"
UUDECODE_CMD=$({ [[ "${MISTER:-false}" == "false" ]] && [[ "$(uname -s)" == "Darwin" ]] ; } && echo "uudecode -p" || echo "uudecode -o -")
EXPORTS="export COMMIT=$(git rev-parse --short HEAD)"

if [[ "${DEBUG:-false}" == "true" ]] ; then
  EXPORTS="${EXPORTS}"$'\n'"export DEBUG=true"
fi

pin_metadata() {
  touch -a -m -t 202108231405 "${1}"
}

cd src

find update_all -type f -iname "*.py" -print0 | while IFS= read -r -d '' file ; do pin_metadata "${file}" ; done
pin_metadata __main__.py
zip -q -0 -D -X -A -r "${UPDATE_ALL_ZIP}" __main__.py update_all -x "*/__pycache__/*"
pin_metadata "${UPDATE_ALL_ZIP}"
echo '#!/usr/bin/env python3' | cat - "${UPDATE_ALL_ZIP}" > "${TEMP_ZIP2}"
pin_metadata "${TEMP_ZIP2}"
mv "${UPDATE_ALL_ZIP}" "/tmp/${UPDATE_ALL_ZIP}"
cd ..

cat <<-EOF
#!/usr/bin/env bash
set -euo pipefail
${EXPORTS}
${UUDECODE_CMD} "\${0}" | xzcat -d -c > "${BIN}"
chmod a+x "${BIN}"
"${BIN}" "\${1:-}"
exit 0
EOF

uuencode - < <(xzcat -z < "${TEMP_ZIP2}")
rm "${TEMP_ZIP2}" > /dev/null 2>&1 || true
