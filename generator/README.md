### Sonce News Generator (Offline, Draft-Only)

This folder contains a small, offline tool that creates draft news files compatible with the website. It does not publish or push anything. It simply produces files you can hand to an editor.

## What you get
- A simple app to type in a news title, date, summary, author, tags, and pick images
- It generates one Markdown file and, if you added images, copies/renames them into the correct folder structure
- It can also create a ZIP that an editor can drop into the website repository
- All drafts are clearly marked with `draft: true` in the front matter

## Quick start (no command line)
1. Download the generator-only ZIP (or this `generator/` folder) and unzip it anywhere on your computer.
2. Open the folder named `generator`.
3. Double‑click one of these:
   - On Windows: `run_windows.bat`
   - On Mac or Linux: `run_mac_linux.sh` (you may need to right‑click > Open)
4. Fill in the form and click “Generate Draft”.
5. The draft will be saved into `generator/output/` as:
   - `content/news/YYYY-MM-DD-slug.md` (your news file)
   - `static/uploads/news/YYYY/MM/...` (renamed images if you selected them)
6. Optionally click “Create ZIP for Editor” to produce one ZIP containing both the Markdown and image files in the exact structure the website expects.

Note: The tool works fully offline. If your computer does not have Python installed, install it once from `python.org` and then double‑click the run file again.

## What to send to the editor
- If you used “Create ZIP for Editor”: send the ZIP file found in `generator/output/` (for example: `news-draft-2025-01-15-welcome-post.zip`). The editor can unzip it into the website repository root and commit.
- If you did not create a ZIP: send both of these from `generator/output/`:
  - `content/news/YYYY-MM-DD-slug.md`
  - the entire folder `static/uploads/news/YYYY/MM/` that contains your images

## What the editor does (for reference)
- Place the Markdown file under the website repo at `content/news/`.
- Place the images under `static/uploads/news/YYYY/MM/`.
- Optionally run validation: `node tools/validate-news.mjs` (not required for you).
- Publish only after review. Drafts are not published automatically.

## Format (simple schema)
All fields are entered in the app. The generated Markdown file has a YAML front matter block:

Required fields:
- title: text
- date: calendar date in `YYYY-MM-DD`

Recommended fields:
- slug: lowercase, web‑friendly, dashes between words (auto‑generated from title)
- summary: short preview text (up to ~200 chars)
- author: text
- tags: list of words (you can type comma‑separated; the generator writes a proper list)
- image: an absolute path like `/static/uploads/news/YYYY/MM/YYYY-MM-DD-slug-hero.jpg` if you chose an image
- draft: true (always set for safety)
- datetime: full ISO 8601 timestamp with timezone (extra info retained for humans)

Notes:
- The website expects `date` as `YYYY-MM-DD`. The generator also records `datetime` (full ISO) for your reference.
- Images are renamed so the first image becomes `YYYY-MM-DD-slug-hero.ext` and any additional images become `YYYY-MM-DD-slug-{description}.ext`.

## Examples
See `generator/examples/` for two ready‑to‑drop drafts.

## Packaging a download ZIP (for maintainers)
- From the repository root or from this folder, run the packaging script:
  - Linux/Mac: `generator/scripts/package-generator-zip.sh`
- This creates `generator/dist/news-generator.zip` containing only the generator and documentation.

## Safety and privacy
- No sign‑in or internet is required.
- The generator never commits, pushes, or publishes anything.
- No deploy keys or credentials are included.

