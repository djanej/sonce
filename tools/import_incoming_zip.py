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
    """Normalize image paths in frontmatter and markdown.

    - Frontmatter: image: "/static/uploads/news/YYYY/MM/....ext"
      * Trim whitespace and quotes; ensure single /static/uploads/news/ prefix
    - Markdown inline images: ![alt](path)
      * Leave http(s):, blob:, data: untouched
      * If already absolute under /static/uploads/news/, leave as-is
      * If relative (e.g., images/foo.jpg or content/news/...), rewrite to /static/uploads/news/<relative>
    """

    def normalize_hero_path(raw: str) -> str:
        val = (raw or '').strip().strip('"\'')
        # Collapse accidental double prefixes and internal whitespace
        val = re.sub(r"\s+", " ", val)
        # If it already contains the uploads root, reduce duplicates and remove spaces
        if '/static/uploads/news/' in val:
            # Remove any accidental spaces around the slash and collapse duplicate segments
            val = val.replace(' /static/uploads/news/', '/static/uploads/news/')
            val = val.replace('/static/uploads/news/ ', '/static/uploads/news/')
            # If duplicated twice, reduce to one occurrence
            val = re.sub(r"(?:/static/uploads/news/)+", "/static/uploads/news/", val)
            # Ensure it starts with a slash
            if not val.startswith('/'):
                val = '/' + val
            return val
        # Not absolute: prepend uploads root
        val = val.lstrip('/')
        return f"/static/uploads/news/{val}"

    # Front matter image: lines starting with image:
    def repl_frontmatter(m):
        prefix = m.group(1)
        value = m.group(2)
        normalized = normalize_hero_path(value)
        return f"{prefix}\"{normalized}\""

    text = re.sub(r"^(image:\s*)([^\n]+)$", repl_frontmatter, text, flags=re.MULTILINE)

    # Inline markdown images
    def repl_markdown(m):
        alt = m.group(1)
        path = (m.group(2) or '').strip()
        # Leave external or blob/data URLs as-is
        if re.match(r"^(?:https?:|blob:|data:)", path):
            return m.group(0)
        # Already absolute under uploads
        if path.startswith('/static/uploads/news/'):
            # Normalize duplicate segments just in case
            fixed = re.sub(r"(?:/static/uploads/news/)+", "/static/uploads/news/", path)
            return f"![{alt}]({fixed})"
        # Rewrite relative to uploads root
        fixed = f"/static/uploads/news/{path.lstrip('/')}"
        return f"![{alt}]({fixed})"

    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", repl_markdown, text)
    return text


def ensure_hero_in_frontmatter(md_text: str) -> str:
    """If frontmatter has image under uploads but no hero field, add hero equal to image for site UI convenience."""
    try:
        fm_match = re.match(r"^---\n([\s\S]*?)\n---\n", md_text)
        if not fm_match:
            return md_text
        fm = fm_match.group(1)
        # Extract image: line
        img_match = re.search(r"^image:\s*\"?([^\n\"]+)\"?\s*$", fm, flags=re.MULTILINE)
        if not img_match:
            return md_text
        image_val = img_match.group(1).strip()
        if '/static/uploads/news/' not in image_val:
            return md_text
        # If hero: exists, skip
        if re.search(r"^hero:\s*", fm, flags=re.MULTILINE):
            return md_text
        # Insert hero: after image: line
        start, end = fm_match.span(0)
        lines = fm.split('\n')
        new_lines = []
        inserted = False
        for line in lines:
            new_lines.append(line)
            if not inserted and line.strip().startswith('image:'):
                new_lines.append(f"hero: \"{image_val}\"")
                inserted = True
        new_fm = '\n'.join(new_lines)
        return md_text.replace(fm, new_fm, 1)
    except Exception:
        return md_text


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
        fixed = ensure_hero_in_frontmatter(fixed)
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

