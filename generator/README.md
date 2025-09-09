### Sonce News Maker (Simple, Offline)

This folder contains a tiny offline app that creates draft news files compatible with the website. It does not publish or push anything. It simply produces files you can send or copy into the website.

## What you get
- A simple app to type in a news title, date, summary, author, tags, and pick images
- Generates one Markdown file and, if you added images, copies/renames them into the correct folder structure
- Can also create a ZIP that an editor can drop into the website repository
- All drafts are clearly marked with `draft: true` in the front matter
- Dark mode and large text options for accessibility (View menu)
- Live counters (title 0/100, summary 0/200) and reading-time estimate
- Inline preview of the generated Markdown (Preview button)
- Image preview for the hero image (if Pillow is installed)
- Quick insert of image Markdown into the body (Insert hero / Insert selected)
- Save/Load draft to JSON (File menu) and persistent preferences (author, theme)

## Quick start (no command line)
1. Download the generator-only ZIP (or this `generator/` folder) and unzip it anywhere on your computer.
2. Open the folder named `generator`.
3. Double‑click one of these:
   - On Windows: `run_windows.bat`
   - On Mac or Linux: `run_mac_linux.sh` (you may need to right‑click > Open)
4. Fill in the form and click “Generate Draft”. Tooltips explain each field. Use View → Dark mode / Large text as needed.
5. The draft will be saved into `generator/output/` as:
   - `content/news/YYYY-MM-DD-slug.md` (your news file)
   - `static/uploads/news/YYYY/MM/...` (renamed images if you selected them)
6. Click “Create ZIP” to produce one ZIP containing both the Markdown and image files in the exact structure the website expects.
7. Click “Copy ZIP to incoming…” and choose your website folder (or its `incoming/` folder). The file will be copied there.

Note: The tool works fully offline. If your computer does not have Python installed, install it once from `python.org` and then double‑click the run file again.

## What to send to the editor
- If you used “Create ZIP”: use the “Copy ZIP to incoming…” button, or send the ZIP file found in `generator/output/` (e.g. `news-draft-2025-01-15-welcome-post.zip`). The editor can copy it into the website repo under `incoming/`.
- If you did not create a ZIP: send both of these from `generator/output/`:
  - `content/news/YYYY-MM-DD-slug.md`
  - the entire folder `static/uploads/news/YYYY/MM/` that contains your images

## What happens next (automatic)
- If you push the ZIP to GitHub on the `main` branch under `incoming/`, an automation imports it and moves files into the correct places.
- Locally, you can also run `run_watch_incoming.*` from the repository root to import ZIPs you drop into `incoming/`.
- Drafts are not published automatically; they remain drafts until reviewed.

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

## ZIP file format (what the app creates)
- The ZIP contains two top-level folders when applicable:
  - `content/news/` with your `YYYY-MM-DD-slug.md`
  - `static/uploads/news/YYYY/MM/` with your renamed images
- Details are in `generator/ZIP_FORMAT.md`.

The app also runs a quick preflight validation on the ZIP (checks filename format and folder structure). When copying to your repository’s `incoming/` folder, if `tools/validate_incoming_zip.py` is present, it is invoked for an extra validation note.

## For Dad: three simple steps
1. Type the title, click Today, optionally pick an image, and click Generate Draft.
2. Click Create ZIP.
3. Click Copy ZIP to incoming… and pick the website folder. Done.

## Safety and privacy
- No sign‑in or internet is required.
- The generator never commits, pushes, or publishes anything.
- No deploy keys or credentials are included.

