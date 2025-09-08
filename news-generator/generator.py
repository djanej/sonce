#!/usr/bin/env python3
"""
Standalone Sonce News Generator

Creates a Markdown news post compatible with the site, and optionally copies a
hero image into static/uploads/news/YYYY/MM/ with the expected naming.

Run from the repository root:
  python3 news-generator/generator.py --title "My Post" --date 2025-09-05 --image /path/to/hero.jpg

Or interactively:
  python3 news-generator/generator.py --interactive --bundle-zip --verify
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path
import shutil
from typing import List, Optional, Tuple
import subprocess
import zipfile


RE_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
IMAGE_WEB_PATH_RE = re.compile(r"^/static/uploads/news/(\d{4})/(\d{2})/([A-Za-z0-9._-]+)$")


def get_repo_root() -> Path:
	"""Return the repository root (parent of news-generator folder)."""
	script_dir = Path(__file__).resolve().parent
	return script_dir.parent


def slugify(text: str) -> str:
	"""Convert text to a lower-hyphen slug matching [a-z0-9-]+ rules."""
	text_lower = text.strip().lower()
	# Replace non-alphanumeric with hyphens
	text_hyphens = re.sub(r"[^a-z0-9]+", "-", text_lower)
	# Collapse duplicates and trim
	text_single = re.sub(r"-+", "-", text_hyphens).strip("-")
	return text_single or "post"


def validate_date_string(date_string: str) -> dt.date:
	if not RE_DATE.match(date_string):
		raise ValueError("Date must be in YYYY-MM-DD format")
	year, month, day = map(int, date_string.split("-"))
	return dt.date(year, month, day)


def normalize_tags(tags_input: Optional[str], tag_list: Optional[List[str]]) -> List[str]:
	combined: List[str] = []
	if tags_input:
		for part in tags_input.split(","):
			value = part.strip()
			if value:
				combined.append(value)
	if tag_list:
		for value in tag_list:
			value_clean = value.strip()
			if value_clean:
				combined.append(value_clean)
	# Deduplicate preserving order
	seen = set()
	unique_tags: List[str] = []
	for value in combined:
		if value not in seen:
			seen.add(value)
			unique_tags.append(value)
	return unique_tags


def ensure_directory(path: Path) -> None:
	path.mkdir(parents=True, exist_ok=True)


def copy_image_to_uploads(source: Path, uploads_root: Path, date_obj: dt.date, slug_value: str, image_name_hint: str) -> Tuple[str, Path]:
	"""Copy image and return (web_path, local_destination_path)."""
	if not source.exists() or not source.is_file():
		raise FileNotFoundError(f"Image not found: {source}")
	extension = source.suffix.lower()
	if extension not in ALLOWED_IMAGE_EXTENSIONS:
		raise ValueError(f"Unsupported image extension: {extension}. Allowed: {sorted(ALLOWED_IMAGE_EXTENSIONS)}")
	year_str = f"{date_obj.year:04d}"
	month_str = f"{date_obj.month:02d}"
	destination_dir = uploads_root / year_str / month_str
	ensure_directory(destination_dir)
	image_desc = slugify(image_name_hint) or "hero"
	destination_filename = f"{date_obj.isoformat()}-{slug_value}-{image_desc}{extension}"
	destination_path = destination_dir / destination_filename
	shutil.copy2(str(source), str(destination_path))
	# Return absolute web path starting with /static
	web_path = f"/static/uploads/news/{year_str}/{month_str}/{destination_filename}"
	return web_path, destination_path


def yaml_escape(value: str) -> str:
	"""Escape YAML string minimally by quoting if needed."""
	if value == "" or any(ch in value for ch in [":", "-", "#", "\"", "'", "\n"]):
		# Prefer double quotes; escape existing
		escaped = value.replace("\\", "\\\\").replace("\"", "\\\"")
		return f'"{escaped}"'
	return value


def format_frontmatter(
	title: str,
	date_string: str,
	slug_value: str,
	author: Optional[str],
	summary: Optional[str],
	tags: List[str],
	image_path: Optional[str],
	image_alt_text: Optional[str],
	draft_flag: bool,
) -> str:
	lines: List[str] = ["---"]
	lines.append(f"title: {yaml_escape(title)}")
	lines.append(f"date: {date_string}")
	lines.append(f"slug: {yaml_escape(slug_value)}")
	if author:
		lines.append(f"author: {yaml_escape(author)}")
	if summary:
		lines.append(f"summary: {yaml_escape(summary)}")
	if tags:
		tag_items = ", ".join([yaml_escape(t) for t in tags])
		lines.append(f"tags: [{tag_items}]")
	if image_path:
		lines.append(f"image: {yaml_escape(image_path)}")
	if image_alt_text:
		lines.append(f"imageAlt: {yaml_escape(image_alt_text)}")
	lines.append(f"draft: {'true' if draft_flag else 'false'}")
	lines.append("---")
	return "\n".join(lines) + "\n\n"


def read_text_file(file_path: Path) -> str:
	return file_path.read_text(encoding="utf-8")


def verify_generated_post(markdown_path: Path) -> List[str]:
	"""Lightweight checks to ensure compatibility."""
	errors: List[str] = []
	try:
		text = markdown_path.read_text(encoding="utf-8")
	except Exception as exc:  # noqa: BLE001 (explicitly capturing for user-friendly output)
		errors.append(f"Cannot read file: {markdown_path} ({exc})")
		return errors
	if not text.startswith("---\n"):
		errors.append("Front matter must start with '---'")
	if "\ntitle:" not in text:
		errors.append("Missing 'title' in front matter")
	if "\ndate:" not in text:
		errors.append("Missing 'date' in front matter")
	# Validate image path shape if present
	for line in text.splitlines():
		if line.startswith("image:"):
			value = line.split(":", 1)[1].strip().strip('"')
			if value:
				if not IMAGE_WEB_PATH_RE.match(value):
					errors.append("Image path must be like /static/uploads/news/YYYY/MM/filename.ext")
	return errors


def maybe_run_auto_index(repo_root: Path) -> None:
	"""If Node tooling exists, rebuild the index to keep listings fresh."""
	cli = shutil.which("node")
	tool_path = repo_root / "tools" / "news-cli.mjs"
	if cli and tool_path.exists():
		try:
			subprocess.run([cli, str(tool_path), "rebuild-index"], check=True)
			print("🔄 Rebuilt content/news/index.json using tools/news-cli.mjs")
		except Exception as exc:  # noqa: BLE001
			print(f"⚠️  Could not rebuild index automatically: {exc}")
	else:
		print("ℹ️  Skipping index rebuild (Node or tools/news-cli.mjs not found)")


def create_upload_zip(repo_root: Path, markdown_path: Path, local_image_path: Optional[Path], zip_dir: Path) -> Path:
	"""Create a single upload ZIP containing the markdown and optional image at repo-relative paths."""
	ensure_directory(zip_dir)
	timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
	zip_path = zip_dir / f"news-upload-{timestamp}.zip"
	repo_rel_markdown = markdown_path.relative_to(repo_root)
	with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
		zf.write(markdown_path, arcname=str(repo_rel_markdown))
		if local_image_path and local_image_path.exists():
			repo_rel_img = local_image_path.relative_to(repo_root)
			zf.write(local_image_path, arcname=str(repo_rel_img))
	print(f"📦 Created upload bundle: {zip_path.relative_to(repo_root)}")
	return zip_path


def main(argv: Optional[List[str]] = None) -> int:
	parser = argparse.ArgumentParser(description="Generate a Sonce-compatible news post")
	parser.add_argument("--title", help="Post title")
	parser.add_argument("--date", help="Publication date YYYY-MM-DD")
	parser.add_argument("--slug", help="Slug; defaults to slugified title")
	parser.add_argument("--summary", help="Short summary (<= 200 chars)")
	parser.add_argument("--author", help="Author name")
	parser.add_argument("--tags", help="Comma-separated list of tags")
	parser.add_argument("--tag", action="append", help="Repeatable tag option; can be used multiple times")
	parser.add_argument("--image", type=str, help="Path to hero image to copy")
	parser.add_argument("--image-alt", dest="image_alt", help="Alt text for the hero image")
	parser.add_argument("--image-name", default="hero", help="Suffix for the hero image filename (default: hero)")
	parser.add_argument("--body", help="Markdown body content string")
	parser.add_argument("--content-file", help="Path to a .md or .txt file for body content")
	parser.add_argument("--draft", action="store_true", help="Mark post as draft in front matter")
	parser.add_argument("--force", action="store_true", help="Overwrite existing markdown if it exists")
	parser.add_argument("--dry-run", action="store_true", help="Print what would be written without writing files")
	parser.add_argument("--interactive", action="store_true", help="Prompt for missing fields interactively")
	parser.add_argument("--output-dir", default=str(get_repo_root() / "content/news"), help="Output directory for markdown (default: content/news)")
	parser.add_argument("--uploads-dir", default=str(get_repo_root() / "static/uploads/news"), help="Uploads directory for images (default: static/uploads/news)")
	parser.add_argument("--bundle-zip", action="store_true", help="Create a single ZIP containing the markdown and image for easy upload")
	parser.add_argument("--zip-dir", default=str(get_repo_root() / "news-generator/output"), help="Directory to put the upload ZIP (default: news-generator/output)")
	parser.add_argument("--verify", action="store_true", help="Run basic compatibility checks after generation")
	parser.add_argument("--auto-index", action="store_true", help="If available, rebuild index using Node tools/news-cli.mjs")

	args = parser.parse_args(argv)

	repo_root = get_repo_root()
	output_dir = Path(args.output_dir)
	uploads_root = Path(args.uploads_dir)
	zip_dir = Path(args.zip_dir)

	# Collect values, prompt if interactive
	title_value: Optional[str] = args.title
	date_value: Optional[str] = args.date
	slug_value: Optional[str] = args.slug
	summary_value: Optional[str] = args.summary
	author_value: Optional[str] = args.author
	tags_value: List[str] = normalize_tags(args.tags, args.tag)
	image_source_path: Optional[Path] = Path(args.image) if args.image else None
	image_alt_text: Optional[str] = args.image_alt
	image_name_hint: str = args.image_name
	draft_flag: bool = bool(args.draft)

	if args.interactive:
		if not title_value:
			title_value = input("Title: ").strip()
		if not date_value:
			default_date = dt.date.today().isoformat()
			date_input = input(f"Date [YYYY-MM-DD] (default {default_date}): ").strip() or default_date
			date_value = date_input
		if not summary_value:
			summary_value = input("Summary (optional, <=200 chars): ").strip() or None
		if not author_value:
			author_value = input("Author (optional): ").strip() or None
		if not tags_value:
			tags_input = input("Tags (comma-separated, optional): ").strip()
			tags_value = normalize_tags(tags_input, None)
		if image_source_path is None:
			image_path_input = input("Hero image path (optional, press Enter to skip): ").strip()
			if image_path_input:
				image_source_path = Path(image_path_input)
				if not image_alt_text:
					image_alt_text = input("Hero image alt text (optional, default title): ").strip() or None
		if args.body is None and args.content_file is None:
			print("Enter Markdown content. Finish with Ctrl-D (Linux/macOS) or Ctrl-Z+Enter (Windows):")
			try:
				content_lines: List[str] = sys.stdin.read().splitlines()
			except KeyboardInterrupt:
				print("\nCancelled.")
				return 1
			body_content = "\n".join(content_lines).strip()
			if not body_content:
				body_content = "Write your content here.\n"
	else:
		body_content = None

	# Validate and fill defaults
	if not title_value:
		raise SystemExit("--title is required (or use --interactive)")
	if not date_value:
		date_value = dt.date.today().isoformat()
	date_obj = validate_date_string(date_value)
	if not slug_value:
		slug_value = slugify(title_value)
	if not RE_SLUG.match(slug_value):
		raise SystemExit("--slug must match [a-z0-9]+(?:-[a-z0-9]+)*")
	if image_source_path and not image_alt_text:
		image_alt_text = title_value
	if body_content is None:
		if args.content_file:
			body_content = read_text_file(Path(args.content_file))
		else:
			body_content = args.body or "Write your content here.\n"

	# Prepare destinations
	ensure_directory(output_dir)
	markdown_filename = f"{date_value}-{slug_value}.md"
	markdown_path = output_dir / markdown_filename
	if markdown_path.exists() and not args.force:
		raise SystemExit(f"Refusing to overwrite existing file without --force: {markdown_path}")

	# Handle image copy if provided
	image_web_path: Optional[str] = None
	local_image_path: Optional[Path] = None
	if image_source_path is not None:
		image_web_path, local_image_path = copy_image_to_uploads(image_source_path, uploads_root, date_obj, slug_value, image_name_hint)

	frontmatter_text = format_frontmatter(
		title=title_value,
		date_string=date_value,
		slug_value=slug_value,
		author=author_value,
		summary=summary_value,
		tags=tags_value,
		image_path=image_web_path,
		image_alt_text=image_alt_text,
		draft_flag=draft_flag,
	)

	markdown_output = frontmatter_text + body_content.strip() + "\n"

	if args.dry_run:
		print("\nWould write Markdown to:", markdown_path)
		print("\n--- BEGIN MARKDOWN ---\n")
		print(markdown_output)
		print("\n--- END MARKDOWN ---\n")
		return 0

	markdown_path.write_text(markdown_output, encoding="utf-8")
	print(f"✅ Created {markdown_path.relative_to(repo_root)}")
	if image_web_path:
		print(f"🖼️  Copied hero image to {image_web_path}")

	if args.verify:
		errors = verify_generated_post(markdown_path)
		if errors:
			print("❌ Post failed basic verification:")
			for e in errors:
				print(" -", e)
			return 2
		else:
			print("✅ Basic compatibility checks passed")

	if args.auto_index:
		maybe_run_auto_index(repo_root)

	zip_path: Optional[Path] = None
	if args.bundle_zip:
		zip_path = create_upload_zip(repo_root, markdown_path, local_image_path, zip_dir)
		print("\nNEXT STEP: Upload this one file to your server and unzip it in the website folder:")
		print(f"  {zip_path}")
		print("This ZIP places files into content/news/... and static/uploads/news/... automatically.")

	print("Tip: Rebuild index if needed: node tools/news-cli.mjs rebuild-index")
	return 0


if __name__ == "__main__":
	sys.exit(main())