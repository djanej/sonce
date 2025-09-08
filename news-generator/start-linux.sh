#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 news-generator/generator.py --interactive --bundle-zip --verify --auto-index | cat