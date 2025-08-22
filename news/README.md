# News System Overview

This document explains what was improved, how the News section works now, and how to integrate external generators (e.g., Sonce News Generator) without breaking compatibility. This file is documentation only and does not affect runtime.

## What changed / improvements
- Pagination on the news list with URL state (`?page=` and `?size=`)
- Tag-based filtering with URL state (`?tag=`)
- Auto-excerpt generation when not provided (first paragraph, cleanly truncated)
- Responsive layout and consistent styling (tag pills, pagination buttons)
- Hardened error handling (missing images, empty/malformed data)
- Added `news/post.html` detail page
- Added pre-render pipeline to convert Markdown to HTML + `index.json`

## Files and directories
- `news/index.html` — News listing page (pagination, filtering, auto-excerpts)
- `news/post.html` — Single post page (loads metadata from `index.json` and HTML by slug)
- `news/news.css` — Shared News styles
- `content/news/` — Generated output (do not edit manually unless you generate externally)
  - `content/news/index.json` — Posts index used by both pages
  - `content/news/<slug>.html` — Pre-rendered HTML per post
- `content/news-src/` — Place Markdown sources here (for the Node pre-render)
- `scripts/news-build.mjs` — Pre-render script (Markdown -> HTML + JSON)
- `package.json` — Contains `build:news` script and deps

## Data contract (expected shape)
Both `news/index.html` and `news/post.html` load `GET /content/news/index.json`. The loader is tolerant and supports 2 shapes:
- Array: `[{ ...post }, ...]`  (preferred)
- Object: `{ posts: [{ ...post }, ...] }`

Each post object should have:
- `slug` (string) — unique, URL-safe identifier; used to fetch `/content/news/<slug>.html`
- `title` (string)
- `date` (string, ISO or parseable)
- `author` (string, optional)
- `hero` (string, optional) — image URL; hidden if image fails to load
- `tags` (string[] preferred; a comma-separated string is also accepted and normalized)
- `excerpt` (string, optional) — if missing, an excerpt is auto-generated client-side

Sorting: listing sorts by `date` descending.

Detail page requires: `content/news/<slug>.html` exists for each post.

## URL parameters (listing page)
- `?page=1` — 1-based current page
- `?size=12` — page size (default 12; UI lets user change)
- `?tag=novice` — filter to posts that include this tag

All three parameters sync with the UI. Clearing filters resets state.

## Pre-render pipeline (optional but recommended)
If you want to author in Markdown and pre-render:
1. Put `.md` files in `content/news-src/`
2. Run `npm run build:news`
3. The script outputs:
   - `content/news/index.json`
   - `content/news/<slug>.html` for each post

Requirements:
- Node 18+
- Install deps once: `npm install`
- Then: `npm run build:news`

### Markdown frontmatter schema
The pre-render reads YAML frontmatter via `gray-matter`:
```yaml
---
title: "Primer objave"
date: 2025-02-01
author: "Sonce Team"
hero: "/images/primer.jpg"
# Can be array or comma-separated string
# tags: ["novice", "pravna pomoč"]
tags: "novice, pravna pomoč"
# Optional; if omitted, an excerpt is generated automatically
excerpt: "Kratek povzetek objave."
slug: "primer-objave" # optional; auto-generated from title otherwise
---

Vsebina objave v Markdownu...
```

The script produces:
- `content/news/<slug>.html` — HTML from Markdown
- Adds a record in `content/news/index.json` with `{ slug, title, date, author, hero, tags[], excerpt }`

## Integrating an external generator (Sonce News Generator)
You have two options:

- Option A: Generate Markdown
  - Emit `.md` files into `content/news-src/` with frontmatter above
  - Run `npm run build:news` to produce JSON + HTML

- Option B: Generate final assets directly (skip Node step)
  - Emit `content/news/index.json` as an array of post objects (see Data contract)
  - Emit `content/news/<slug>.html` (one per post)
  - Make sure `slug` values match between `index.json` and the HTML filenames

Either option will be fully compatible with the News pages.

## Example `index.json` entry
```json
{
  "slug": "primer-objave",
  "title": "Primer objave",
  "date": "2025-02-01T00:00:00.000Z",
  "author": "Sonce Team",
  "hero": "/images/primer.jpg",
  "tags": ["novice", "pravna pomoč"],
  "excerpt": "Kratek povzetek objave."
}
```

## Behavior & fallbacks
- If `index.json` is missing/invalid: shows a friendly error message
- If `index.json` is empty: shows "Ni objav za prikaz."
- If hero image fails: it is hidden gracefully
- If `excerpt` missing: first paragraph is auto-used and cleanly truncated

## Notes on styling & responsiveness
- Tag pills and pagination are styled in `news/news.css`
- Listing uses a responsive grid; detail page uses a centered column
- Provide hero images with safe aspect ratio (16:9 preferred) for best results

## Changelog snapshot
- Added `news/post.html`
- Enhanced `news/index.html`: pagination, filters, auto-excerpts, URL sync, errors
- Updated `news/news.css`: tag pills, pagination buttons, mobile paddings
- Added pre-render: `scripts/news-build.mjs`, `package.json` deps and script
- Seeded `content/news/index.json` as `[]`