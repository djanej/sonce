#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GEN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="$GEN_DIR/dist"
ZIP_PATH="$DIST_DIR/news-generator.zip"

mkdir -p "$DIST_DIR"

TMP_DIR="$(mktemp -d)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

# Copy selected generator files
rsync -a --exclude 'output/' --exclude 'dist/' --exclude '__pycache__/' --exclude '*.pyc' \
  --exclude '.DS_Store' --exclude '.git/' --exclude '.gitignore' \
  "$GEN_DIR/" "$TMP_DIR/generator/"

cd "$TMP_DIR"

if command -v zip >/dev/null 2>&1; then
  zip -r "$ZIP_PATH" generator
else
  # Fallback to Python zipfile
  python3 - <<'PY'
import os, zipfile, sys
root = 'generator'
zip_path = sys.argv[1]
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for base, _, files in os.walk(root):
        for f in files:
            p = os.path.join(base, f)
            zf.write(p, arcname=p)
print('Wrote', zip_path)
PY
  "$ZIP_PATH"
fi

echo "Created: $ZIP_PATH"

