#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GEN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$GEN_DIR/scripts/package_generator.py"
elif command -v python >/dev/null 2>&1; then
  exec python "$GEN_DIR/scripts/package_generator.py"
else
  echo "Python 3 is required to package the generator." >&2
  exit 1
fi

