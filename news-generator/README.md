# News Generator (Standalone)

A simple, standalone Python tool to create Sonce-compatible news posts without touching the website code. It writes Markdown posts into `/content/news/` and copies images into `/static/uploads/news/YYYY/MM/` using the exact paths the site expects.

- Output: one Markdown file per post, named `YYYY-MM-DD-slug.md`
- Images: copied to `/static/uploads/news/YYYY/MM/` and referenced via absolute paths like `/static/uploads/news/2025/09/2025-09-05-my-post-hero.jpg`
- No site code changes required

See `SCHEMA.md` for the required front matter fields and examples.

## Easiest steps (for your father)

Do this once:
- Download the repository as a ZIP
- Unzip it and open the folder

Every time you want to publish news:
1) Put your photo somewhere on your computer (optional)
2) Open the folder in File Explorer / Finder
3) Double-click the start script:
   - Windows: `news-generator/start-windows.cmd`
   - macOS: `news-generator/start-mac.command` (you may need to allow it once in System Settings)
   - Linux: `news-generator/start-linux.sh`
4) Answer the questions (title, date, summary, author, tags). If you picked a photo, paste its path (or drag it into the terminal if supported)
5) Done! The tool creates:
   - One Markdown file in `content/news/`
   - If you chose a photo, it copies it to `static/uploads/news/YYYY/MM/`
6) The tool also creates a ZIP file in `news-generator/output/` that contains both files ready for upload. Upload that single ZIP to your server and unzip it into the website folder.

If the site uses an index, rebuild it (optional):
```bash
node tools/news-cli.mjs rebuild-index
```

## Command line (optional)
Interactive with ZIP and checks:
```bash
python3 news-generator/generator.py --interactive --bundle-zip --verify --auto-index
```

One-shot:
```bash
python3 news-generator/generator.py \
  --title "Community Update" \
  --date 2025-09-05 \
  --summary "Short summary here." \
  --author "Sonce Team" \
  --tags "news,update" \
  --image /path/to/hero.jpg \
  --bundle-zip --verify --auto-index
```

Where files go:
- Markdown: `content/news/2025-09-05-community-update.md`
- Image: `static/uploads/news/2025/09/2025-09-05-community-update-hero.jpg`
- Upload bundle: `news-generator/output/news-upload-*.zip`

## Troubleshooting (common issues)
- Wrong folder: run the tool from the repo root so `content/` and `static/` exist
- Wrong field names: front matter keys must match `SCHEMA.md` (`title`, `date`, `slug`, `summary`, `author`, `tags`, `image`, `imageAlt`, `draft`)
- Date format: must be `YYYY-MM-DD`
- Image paths: must start with `/static/uploads/news/YYYY/MM/...`
- Slug rules: lowercase, hyphen-separated (`[a-z0-9-]+`), no spaces
- Index missing/old: run `node tools/news-cli.mjs rebuild-index`

## Samples
See `news-generator/samples/` for two example posts generated with this tool. You can compare them to files in `content/news/`.