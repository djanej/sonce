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

def warning(msg: str):
    print(f"[incoming] ⚠️  {msg}")

def error(msg: str):
    print(f"[incoming] ❌ {msg}")

def success(msg: str):
    print(f"[incoming] ✅ {msg}")


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


def validate_markdown_content(text: str, filename: str) -> list:
    """Validate markdown content for quality issues."""
    warnings = []
    
    # Extract frontmatter
    fm_match = re.match(r'^---\n([\s\S]*?)\n---', text)
    if not fm_match:
        warnings.append("Missing frontmatter")
        return warnings
    
    frontmatter = fm_match.group(1)
    body = text[fm_match.end():].strip()
    
    # Check title
    title_match = re.search(r'^title:\s*["\']?(.+?)["\']?$', frontmatter, re.MULTILINE)
    if title_match:
        title = title_match.group(1).strip()
        if len(title) < 3:
            warnings.append("Title too short")
        if re.match(r'^(test|asdf|lorem|example)', title, re.IGNORECASE):
            warnings.append("Title appears to be test content")
        # Check for gibberish
        if re.match(r'^[a-z]{15,}$', title.replace(' ', ''), re.IGNORECASE):
            warnings.append("Title appears to be random characters")
    
    # Check body content
    if not body or len(body.strip()) < 10:
        warnings.append("Content body is too short or missing")
    else:
        word_count = len(body.split())
        if word_count < 50:
            warnings.append(f"Content is very short ({word_count} words)")
        if re.match(r'^(test|lorem ipsum|placeholder)', body[:100], re.IGNORECASE):
            warnings.append("Content appears to be placeholder text")
    
    # Check for broken markdown
    if re.search(r'\[([^\]]*?)\]\(\s*\)', body):
        warnings.append("Found broken markdown links")
    if re.search(r'!\[([^\]]*?)\]\(\s*\)', body):
        warnings.append("Found broken markdown images")
    
    return warnings

def import_zip(zip_path: Path) -> bool:
    info(f"Importing {zip_path.name}")
    work_dir = zip_path.with_suffix('.unpacked')
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    # Unzip
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Check for suspicious files
            for name in zf.namelist():
                if name.startswith('/') or '..' in name:
                    error(f"Security warning: suspicious path in zip: {name}")
                    return False
            zf.extractall(work_dir)
    except zipfile.BadZipFile:
        error(f"Skipping (bad zip): {zip_path.name}")
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
            warning(f"Markdown filename not matching date-slug format: {md.name}")
        
        # Read and validate content
        text = md.read_text(encoding='utf-8')
        validation_warnings = validate_markdown_content(text, md.name)
        if validation_warnings:
            warning(f"Content quality issues in {md.name}:")
            for w in validation_warnings:
                warning(f"  - {w}")
        
        # Fix paths and write
        dest_md = ROOT / rel_md
        dest_md.parent.mkdir(parents=True, exist_ok=True)
        fixed = fix_paths_in_text(text)
        dest_md.write_text(fixed, encoding='utf-8')
        moved_files.append(dest_md)

    # Rebuild index and commit locally
    rebuild_index()
    git_commit(f"Import news from {zip_path.name}")

    success(f"Imported {zip_path.name} - {len(md_files)} post(s), {len(uploads_inside)} image(s)")
    
    # Clean up temp directory
    if work_dir.exists():
        shutil.rmtree(work_dir)
    
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

