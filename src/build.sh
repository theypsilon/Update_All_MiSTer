#!/usr/bin/env bash
# Copyright (c) 2021-2025 José Manuel Barroso Galindo <theypsilon@gmail.com>

set -euo pipefail

rm -rf build || true
mkdir -p build/src

cp src/__main__.py build/src/__main__.py
cp -r src/update_all/ build/src/update_all
if [[ "${SKIP_COMMIT:-false}" != "true" ]] ; then
  echo "default_commit = '$(git rev-parse --short HEAD)'" > "build/src/commit.py"
fi

if [[ "${SKIP_REMOVALS:-false}" != "true" ]] ; then
  find build/src -type f -name '*.py' -exec perl -i -0pe 's/"""(.*?)"""/""/sg; s/^\s*#.*\n//mg; s/^\s*\n//mg' {} +
fi
#if which strip-hints > /dev/null ; then
#  find build/src -type f -name '*.py' -exec strip-hints --inplace {} \; 2> /dev/null
#fi
find build/src -type f ! -name '*.py' -exec rm -f {} +
find build/src -exec touch -t 202108231405 {} +

export SOURCE_DATE_EPOCH=0
python -m zipapp build/src -o build/update_all.pyz -p "/usr/bin/env python3"

cat <<-EOF
#!/usr/bin/env bash
set -euo pipefail
export DEBUG="\${DEBUG:-false}"
tail -n +8 "\${0}" | xzcat -d -c > "/tmp/update_all.pyz"
chmod a+x "/tmp/update_all.pyz"
"/tmp/update_all.pyz" "\${1:-}"
exit 0
EOF

xzcat -z < build/update_all.pyz
