### ZIP format produced by the News Maker

The generator creates a ZIP that mirrors the website's expected folder layout. Unzipping at the repository root places files into the right locations.

Contents:
- `content/news/YYYY-MM-DD-slug.md` — the post markdown with YAML front matter
- `static/uploads/news/YYYY/MM/...` — renamed images (hero and additional)

Notes:
- Only files under `content/` and `static/` are included.
- Filenames are safe, lowercase, and include the date and slug.
- If no images are selected, only the markdown file is included.

Related spec: see `NEWS_FORMAT_SPEC.md` at the repository root.

