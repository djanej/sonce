### Sonce News Content Format Specification (for generators)

This document defines the exact file formats, directory layout, and field semantics the website expects for the NEWS section. Follow this spec to generate content that works out-of-the-box without modifying any website UI.

## Directory layout
- content lives under `content/news/`
- images live under `static/uploads/news/YYYY/MM/`

Required structure:
- `content/news/index.json` — metadata index (auto-generated)
- `content/news/YYYY-MM-DD-slug.md` — individual Markdown post files
- `static/uploads/news/YYYY/MM/YYYY-MM-DD-slug-hero.ext` — optional hero image
- `static/uploads/news/YYYY/MM/YYYY-MM-DD-slug-{description}.ext` — optional extra images

Notes:
- `YYYY` is 4-digit year; `MM` is 2-digit month with leading zero.
- Allowed `ext`: .jpg, .jpeg, .png, .gif, .webp, .svg

## Post filename
- format: `YYYY-MM-DD-slug.md`
- date: ISO 8601 calendar date (e.g. `2024-12-01`)
- slug: lowercase, hyphenated, `[a-z0-9-]+`, no leading/trailing hyphen

Examples:
- `2024-12-01-community-event.md`
- `2025-01-15-welcome-post.md`

## Markdown post file format
Each post is a UTF-8 Markdown file with a YAML frontmatter block, followed by Markdown content.

Frontmatter block:
---
title: "Post Title"             # required, string, ≤ 100 chars
date: 2024-12-01                 # required, YYYY-MM-DD
author: "Author Name"           # optional, string
slug: "custom-slug"             # optional, string; defaults to slugified title
image: "/static/uploads/news/2024/12/2024-12-01-slug-hero.jpg"  # optional, hero image URL
imageAlt: "Alt text"            # optional, string
summary: "Short excerpt"        # optional, string, ≤ 200 chars
tags: [news, community]          # optional, array of strings
---

Content block:
- Markdown content begins after the second `---` line.
- You may reference additional images via standard Markdown image syntax using absolute paths under `/static/uploads/news/YYYY/MM/...`.

Validation rules:
- `title` must be non-empty text, trimmed.
- `date` must be a valid date string in `YYYY-MM-DD` (not datetime). Use the publication date.
- `slug` if present must match `[a-z0-9]+(?:-[a-z0-9]+)*`.
- `image` if present must be an absolute path starting with `/static/uploads/news/` and pointing to an image file under the proper year/month folder.
- `tags` must be a YAML array of strings (not a comma string) if you want strict compatibility with readers that parse arrays.

## Images
- Hero image (recommended): `/static/uploads/news/YYYY/MM/YYYY-MM-DD-slug-hero.ext`
- Additional images: `/static/uploads/news/YYYY/MM/YYYY-MM-DD-slug-{description}.ext`
- Recommended hero size: 1200×630px (16:9); max ~5 MB
- Always provide `imageAlt` for accessibility.

## Index file: content/news/index.json
The site reads `/content/news/index.json` for listing and navigation. It should be an array of post objects sorted by date descending. When using the provided tooling, this file is generated automatically; generators that produce it themselves must follow this schema.

Entry object fields:
- id: string — `${date}-${slug}`
- title: string
- date: string — ISO date (`YYYY-MM-DD`), not datetime
- author: string (optional)
- summary: string (optional)
- hero: string (optional) — preferred hero image URL; if omitted, `image` may be used
- image: string (optional) — legacy field, may mirror hero
- imageAlt: string (optional)
- tags: array<string> (optional)
- slug: string — same rules as filename slug
- filename: string — the markdown filename, e.g. `2024-12-01-slug.md`
- path: string — absolute path to the markdown file under `/content/news/...`
- link: string — duplicate of `path` for compatibility
- readingTimeMinutes: integer (optional)
- readingTimeLabel: string (optional) — e.g. `"3 min"`

Minimal valid example (array with one object):
[
  {
    "id": "2024-12-01-welcome-post",
    "title": "Welcome to Sonce News",
    "date": "2024-12-01",
    "author": "Sonce Team",
    "summary": "Welcome to the new Sonce news system.",
    "hero": "/static/uploads/news/2024/12/2024-12-01-welcome-post-hero.jpg",
    "imageAlt": "Welcome hero",
    "tags": ["news", "welcome"],
    "slug": "welcome-post",
    "filename": "2024-12-01-welcome-post.md",
    "path": "/content/news/2024-12-01-welcome-post.md",
    "link": "/content/news/2024-12-01-welcome-post.md",
    "readingTimeMinutes": 3,
    "readingTimeLabel": "3 min"
  }
]

Notes:
- The site accepts either a plain array at root or `{ posts: [...] }`; prefer a plain array.
- For navigation, the site may use either `hero` or `image`; if both exist, it prefers `hero`.
- The post page resolves content from `path`/`link` or falls back to `/content/news/${filename}`.

## Compatibility with site renderers
- Listing page (`/news/`) fetches `/content/news/index.json`, supports filtering by `tags`, searching in `title`, `summary/description/excerpt`, `author`, and sorts by date/title/reading time.
- Post page (`/news/post.html`) fetches the same index, locates the post by `slug` or `path`, loads the markdown via `path`/`link`/`filename`, strips frontmatter, and converts Markdown to HTML.

## Generator guidance
- Always create the markdown file under `content/news/` with the required filename format.
- Always include `title` and `date` in frontmatter.
- Prefer writing `tags` as an array, not as a comma string.
- If you generate the index, ensure field names and shapes match exactly as above.
- If you do not generate `index.json`, you can run: `node tools/news-cli.mjs rebuild-index` to build it from the markdown files.

## Optional: programmatic validation
Posts and the index can be validated by ensuring:
- Filenames match `^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$`
- Frontmatter keys are within the allowed set and required keys are present
- Paths start with `/content/news/` or `/static/uploads/news/` where applicable
- Dates are valid calendar dates in `YYYY-MM-DD`

This spec reflects the current production reader behavior in `news/index.html` and `news/post.html` and the generator scripts in `tools/news-cli.mjs` and `scripts/news-build.mjs`.

