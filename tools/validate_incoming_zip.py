#!/usr/bin/env python3
import sys
import re
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INCOMING_DIR = ROOT / 'incoming'

MD_NAME_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")


def validate_zip(zip_path: Path) -> tuple[bool, list[str]]:
    problems: list[str] = []
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            names = [i.filename for i in zf.infolist() if not i.is_dir()]
    except zipfile.BadZipFile:
        return False, [f"Bad ZIP file: {zip_path.name}"]

    md_files = [n for n in names if n.startswith('content/news/') and n.lower().endswith('.md')]
    if not md_files:
        problems.append('Missing content/news/*.md')
    else:
        for n in md_files:
            fname = Path(n).name
            if not MD_NAME_RE.match(fname):
                problems.append(f"Markdown filename must be YYYY-MM-DD-slug.md: {fname}")

    img_files = [n for n in names if n.startswith('static/uploads/news/')]
    for n in img_files:
        parts = Path(n).parts
        # Expect: static/uploads/news/YYYY/MM/filename
        if len(parts) < 6:
            problems.append(f"Image path should be static/uploads/news/YYYY/MM/…: {n}")
            continue
        yyyy, mm = parts[3], parts[4]
        if not (len(yyyy) == 4 and yyyy.isdigit()):
            problems.append(f"Year folder must be 4 digits: {n}")
        if not (len(mm) == 2 and mm.isdigit() and 1 <= int(mm) <= 12):
            problems.append(f"Month folder must be 01..12: {n}")

    return len(problems) == 0, problems


def main() -> int:
    args = sys.argv[1:]
    targets: list[Path] = []
    if args and args[0] not in ('--all', '-a'):
        targets = [Path(args[0])]
    else:
        INCOMING_DIR.mkdir(parents=True, exist_ok=True)
        targets = sorted(INCOMING_DIR.glob('*.zip'))

    if not targets:
        print('[validate] No ZIP files found to validate.')
        return 0

    any_errors = False
    for zp in targets:
        ok, problems = validate_zip(zp)
        if ok:
            print(f"[validate] ✔ {zp.name} OK")
        else:
            any_errors = True
            print(f"[validate] ✖ {zp.name}")
            for p in problems:
                print(f"  - {p}")

    return 1 if any_errors else 0


if __name__ == '__main__':
    raise SystemExit(main())

