#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
  exec python3 news_generator.py
elif command -v python >/dev/null 2>&1; then
  exec python news_generator.py
else
  echo "Python 3 is required. Please install it from python.org and try again." >&2
  exit 1
fi

