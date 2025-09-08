### News Generator (independent tool)

This small tool creates news posts for the site by writing files into the website folders. It stays separate from the website code, so you can download and run just this folder.

- Output post: `content/news/YYYY-MM-DD-slug.md`
- Output images (optional): `static/uploads/news/YYYY/MM/`
- Updates: `content/news/index.json`

It’s designed for very simple use.

## Quick start

1) Download the repository as ZIP and unzip. Open the `news-generator` folder.
2) Install (first time only):
   - Windows: double‑click `install.bat`
   - Mac/Linux: run `install.sh`
3) Run the tool:
   - Windows: double‑click `run.bat`
   - Mac/Linux: run `run.sh`
4) Answer the questions. The tool prints the files it created.
5) Upload those files to the website repository in the same folders.

Tip: If you skip the image, you only upload one file (the `.md`).

## Plain-language schema (front‑matter)

Required fields are marked.

- title (required): Headline text.
- date (required): `YYYY-MM-DD` (e.g. `2025-01-15`).
- slug (optional): Lowercase-with-hyphens. Auto‑generated from title.
- summary (recommended): Short 1–2 sentence description.
- author (optional)
- tags (optional): list like `[news, obvestilo]`.
- image (optional): `/static/uploads/news/YYYY/MM/...` (auto‑set if you choose an image).
- imageAlt (optional): Short description for the image.
- draft (optional): `true` or `false`.

Example the generator writes:

```
---
title: "Primer objave"
date: 2025-01-15
slug: "primer-objave"
author: "Sonce Team"
summary: "Kratek opis vsebine."
tags: [sonce, pomembno]
image: "/static/uploads/news/2025/01/2025-01-15-primer-objave-hero.jpg"
imageAlt: "Primer objave"
draft: false
---
```

## Where files go

- Posts: `content/news/YYYY-MM-DD-slug.md`
- Images: `static/uploads/news/YYYY/MM/YYYY-MM-DD-slug-hero.jpg`
- Index: `content/news/index.json`

## Download options

- Repo ZIP (simplest). Use only `news-generator`.
- Git clone, then `cd news-generator`.
- Release ZIP (if provided).

## How to publish (step‑by‑step)

1) Run `run.bat` or `run.sh`.
2) Enter title; the tool fills other fields.
3) Optionally pick an image when asked.
4) Upload the created `.md` (and the image if any).
5) Visit `/news/` to check the post.

## Troubleshooting

- Folder: Post must be in `content/news/`; image in `static/uploads/news/YYYY/MM/`.
- Fields: Use only title, date, slug, summary, author, tags, image, imageAlt, draft.
- Date format: Must be `YYYY-MM-DD`.
- Image path: Must start with `/static/uploads/news/` and match year/month.
- Slug: Lowercase with hyphens only.
- Index: If list looks wrong, run the tool again to refresh `index.json`.

## Advanced (optional)

- Rebuild index only: `python3 news_generator.py rebuild-index`
- Custom site root: `python3 news_generator.py --site-root /path/to/site`

The generator never changes website templates.

