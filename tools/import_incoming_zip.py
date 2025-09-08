#!/usr/bin/env python3
import os
import re
import sys
import json
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
import subprocess


ROOT = Path(__file__).resolve().parents[1]
INCOMING_DIR = ROOT / 'incoming'
CONTENT_DIR = ROOT / 'content' / 'news'
UPLOADS_ROOT = ROOT / 'static' / 'uploads' / 'news'

MD_EXT_RE = re.compile(r"\.md$", re.IGNORECASE)
DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(?:[a-z0-9]+(?:-[a-z0-9]+)*)\.md$")


def info(msg: str):
    print(f"[incoming] {msg}")


def fix_paths_in_text(text: str) -> str:
    # Normalize any site-relative paths under content->static conventions
    # Front matter image lines: image: /static/uploads/news/YYYY/MM/...
    # Convert inline image markdown if it mistakenly used relative paths like images/... to absolute under static
    text = re.sub(r"(image:\s*)(['\"]?)(?!/static/uploads/news/)([^\n'\"]+)(['\"]?)",
                  lambda m: f"{m.group(1)}\"/static/uploads/news/{m.group(3).lstrip('/')}\"",
                  text)
    # Inline markdown images ![alt](path) -> if path starts with static/uploads/news keep, if content/... or images/... -> rewrite to /static/uploads/news/... best-effort
    def repl_markdown(m):
        alt = m.group(1)
        path = m.group(2)
        if path.startswith('/static/uploads/news/'):
            return m.group(0)
        path = path.lstrip('/')
        return f"![{alt}](/{'static/uploads/news/' + path})"
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", repl_markdown, text)
    return text


def rebuild_index() -> None:
    try:
        subprocess.run(['node', str(ROOT / 'tools' / 'validate-news.mjs')], check=False)
    except Exception:
        # Non-fatal; index may not rebuild if node not present
        pass


def git_commit(message: str) -> None:
    try:
        subprocess.run(['git', '-C', str(ROOT), 'add', 'content/news', 'static/uploads/news'], check=False)
        subprocess.run(['git', '-C', str(ROOT), 'commit', '-m', message], check=False)
    except Exception:
        # Non-fatal if git not available
        pass


def import_zip(zip_path: Path) -> bool:
    info(f"Importing {zip_path.name}")
    work_dir = zip_path.with_suffix('.unpacked')
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    # Unzip
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(work_dir)
    except zipfile.BadZipFile:
        info(f"Skipping (bad zip): {zip_path.name}")
        return False

    # Locate markdown under content/news/
    md_files = list(work_dir.rglob('content/news/*.md'))
    if not md_files:
        info("No content/news/*.md found in ZIP; skipping")
        return False

    # Move images if present
    # Expect images under static/uploads/news/YYYY/MM/**
    moved_files = []
    uploads_inside = list(work_dir.rglob('static/uploads/news/*/*/*'))
    for p in uploads_inside:
        if p.is_file():
            rel = p.relative_to(work_dir)
            dest = ROOT / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
            moved_files.append(dest)

    # Process markdown(s)
    for md in md_files:
        rel_md = md.relative_to(work_dir)
        if not DATE_RE.search(md.name):
            info(f"Warning: markdown filename not matching date-slug format: {md.name}")
        dest_md = ROOT / rel_md
        dest_md.parent.mkdir(parents=True, exist_ok=True)
        text = md.read_text(encoding='utf-8')
        fixed = fix_paths_in_text(text)
        dest_md.write_text(fixed, encoding='utf-8')
        moved_files.append(dest_md)

    # Rebuild index and commit locally
    rebuild_index()
    git_commit(f"Import news from {zip_path.name}")

    info(f"Imported {zip_path.name}")
    return True


def import_all_incoming() -> int:
    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    zip_files = sorted([p for p in INCOMING_DIR.iterdir() if p.is_file() and p.suffix.lower() == '.zip'])
    if not zip_files:
        info("No ZIP files found in incoming/")
        return 0
    imported = 0
    for zp in zip_files:
        ok = import_zip(zp)
        if ok:
            imported += 1
            # Optionally move processed ZIP to archive
            processed_dir = INCOMING_DIR / 'processed'
            processed_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(zp), processed_dir / zp.name)
    return imported


def main() -> int:
    count = import_all_incoming()
    info(f"Done. Imported {count} ZIP(s).")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

