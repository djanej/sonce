#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
  exec python3 tools/import_incoming_zip.py
elif command -v python >/dev/null 2>&1; then
  exec python tools/import_incoming_zip.py
else
  echo "Python 3 is required to run the importer." >&2
  exit 1
fi

