#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "Watching incoming/ for ZIP files. Press Ctrl+C to stop."

while true; do
  if command -v python3 >/dev/null 2>&1; then
    python3 tools/import_incoming_zip.py || true
  elif command -v python >/dev/null 2>&1; then
    python tools/import_incoming_zip.py || true
  else
    echo "Python 3 is required to run the importer." >&2
    exit 1
  fi
  sleep 5
done

