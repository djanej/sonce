# News Generator (Standalone)

A simple, standalone Python tool to create Sonce-compatible news posts without touching the website code. It writes Markdown posts into `/content/news/` and copies images into `/static/uploads/news/YYYY/MM/` using the exact paths the site expects.

- Output: one Markdown file per post, named `YYYY-MM-DD-slug.md`
- Images: copied to `/static/uploads/news/YYYY/MM/` and referenced via absolute paths like `/static/uploads/news/2025/09/2025-09-05-my-post-hero.jpg`
- No site code changes required

See `SCHEMA.md` for the required front matter fields and examples.

## Quick start

1) Download just the generator (choose one):
- ZIP of the whole repo: download, then keep only the `news-generator/` folder
- Release ZIP: download `news-generator.zip` from Releases (if provided)
- Git: `git clone` the repo and use the `news-generator/` folder

2) Requirements:
- Python 3.8+ installed
- Run from the repository root so it can write to `content/` and `static/`

3) Create a post (interactive):
```bash
python3 news-generator/generator.py
```

Create a post (one-shot command):
```bash
python3 news-generator/generator.py \
  --title "Community Update" \
  --date 2025-09-05 \
  --summary "Short summary here." \
  --author "Sonce Team" \
  --tags "news,update" \
  --image /path/to/hero.jpg
```

Where files go:
- Markdown: `content/news/2025-09-05-community-update.md`
- Image: `static/uploads/news/2025/09/2025-09-05-community-update-hero.jpg`

Rebuild the news index (optional if your site auto-builds it):
```bash
node tools/news-cli.mjs rebuild-index
```

## For your father (simple steps)
- Download the repository ZIP and open it
- Open the folder, keep only `news-generator/` if you want
- Put your image file somewhere on your computer
- Open Terminal in the repository folder
- Run: `python3 news-generator/generator.py` and follow prompts
- The tool creates one Markdown file in `content/news/`. Upload this file to the server
- If you included an image, it is copied into `static/uploads/news/YYYY/MM/`; upload that folder too

## Troubleshooting (common issues)
- Wrong folder: run the tool from the repo root so `content/` and `static/` exist
- Wrong field names: front matter keys must match `SCHEMA.md` (`title`, `date`, `slug`, `summary`, `author`, `tags`, `image`, `imageAlt`, `draft`)
- Date format: must be `YYYY-MM-DD`
- Image paths: must start with `/static/uploads/news/YYYY/MM/...`
- Slug rules: lowercase, hyphen-separated (`[a-z0-9-]+`), no spaces
- Index missing/old: run `node tools/news-cli.mjs rebuild-index`

## Samples
See `news-generator/samples/` for two example posts generated with this tool. You can compare them to files in `content/news/`.