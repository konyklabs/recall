#!/bin/bash
# The whole check. Green here is the definition of green.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m py_compile bin/recall
python3 -m unittest discover -s tests -v
python3 bin/recall --help >/dev/null
if command -v actionlint >/dev/null 2>&1; then actionlint; else echo "actionlint: not on PATH, skipped"; fi
echo "check: ok"
