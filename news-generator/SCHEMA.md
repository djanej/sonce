# Plain-language schema for Sonce News posts

These fields go in the YAML front matter at the top of each Markdown file.

Required by the site
- title: Text, ≤ 100 characters
- date: ISO date `YYYY-MM-DD` (e.g. `2025-09-05`)

Recommended for best compatibility
- slug: Lowercase hyphenated ID (defaults to slugified title), `[a-z0-9-]+`
- summary: Short excerpt, ≤ 200 characters
- author: The author name
- tags: A list of words, for example `[news, update]`
- image: Absolute path to the hero image under `/static/uploads/news/YYYY/MM/...`
- imageAlt: Short alt text for the hero image
- draft: `true` or `false` (useful during editing; the site may ignore it)

Image placement rules
- Images live under `static/uploads/news/YYYY/MM/`
- Hero image name convention: `YYYY-MM-DD-slug-hero.ext`
- Allowed extensions: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.svg`

Example front matter
```yaml
---
title: "Community Update"
date: 2025-09-05
slug: "community-update"
author: "Sonce Team"
summary: "Short summary here."
tags: [news, update]
image: "/static/uploads/news/2025/09/2025-09-05-community-update-hero.jpg"
imageAlt: "Community update hero"
draft: false
---
```

Filename format
- `YYYY-MM-DD-slug.md` (e.g. `2025-09-05-community-update.md`)

Content placement
- Save posts to `content/news/`
- The site’s listing page reads `content/news/index.json` (you can rebuild it via `node tools/news-cli.mjs rebuild-index` if needed)