#!/usr/bin/env bash
# Copyright (c) 2022-2023 José Manuel Barroso Galindo <theypsilon@gmail.com>

set -euo pipefail

echo "Type checks:"
python3 -m mypy src
echo

cd src
echo "Unit Tests:"
python3 -m unittest discover -s test/unit
echo
echo "Integration Tests:"
python3 -m unittest discover -s test/integration
echo
echo "SystemTests:"
python3 -m unittest discover -s test/system
echo
echo "Done"
