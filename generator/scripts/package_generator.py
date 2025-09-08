#!/usr/bin/env python3
import os
import sys
import zipfile
from pathlib import Path


EXCLUDE_DIRS = {"output", "dist", ".git", "__pycache__"}
EXCLUDE_FILES = {".DS_Store",}


def should_include(path: Path, gen_root: Path) -> bool:
    rel = path.relative_to(gen_root)
    parts = set(rel.parts)
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return False
    if path.name in EXCLUDE_FILES:
        return False
    return True


def main() -> int:
    gen_root = Path(__file__).resolve().parents[1]
    dist_dir = gen_root / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dist_dir / "news-generator.zip"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for base, dirs, files in os.walk(gen_root):
            base_path = Path(base)
            # Prune excluded dirs from walk
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for fname in files:
                fpath = base_path / fname
                if not should_include(fpath, gen_root):
                    continue
                arcname = f"generator/{fpath.relative_to(gen_root).as_posix()}"
                zf.write(fpath, arcname)

    print(f"Created: {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

