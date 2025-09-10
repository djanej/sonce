## Sonce Offline News ZIP Generator (HTML)

This folder contains a standalone, offline HTML tool to create news ZIP packages for the website. It runs entirely in your browser (no server needed) and produces a ZIP with the exact folder structure the site expects. You can share this folder as a separate download for editors who prefer a simple, offline workflow.

### What it does
- Lets you enter the news title, date, author, tags, summary, and body
- Optionally attach a hero image and additional images
- Generates a Markdown post with YAML front matter that matches the site spec
- Builds a ZIP that contains:
  - `content/news/YYYY-MM-DD-slug.md`
  - `static/uploads/news/YYYY/MM/...` (hero and any attachments)

### How to use (fully offline)
1. Download or copy this entire folder `generator/html-seperate-news-generator` to your computer
2. Open `index.html` in a modern browser (Chrome, Edge, Firefox, Safari)
3. Fill out the form (Title and Date are required)
4. Optionally select images
5. Click “Create ZIP”
6. A ZIP file will be downloaded by the browser

### Importing to the website
1. Take the generated ZIP file
2. Put it into the website repository’s `incoming/` folder
3. Use one of these options to import:
   - Local scripts at repo root: `run_import_once.*` or `run_watch_incoming.*`
   - Or commit and push the ZIP under `incoming/` on the `main` branch and let CI import it automatically

On import, the files will be moved into their final locations and the index will be rebuilt. See the repo’s `incoming/README.md` for details.

### File format (quick reference)
- Markdown filename: `YYYY-MM-DD-slug.md`
- Images: `/static/uploads/news/YYYY/MM/YYYY-MM-DD-slug-*.ext`
- Front matter fields used by the site (see `NEWS_FORMAT_SPEC.md` for full spec):
  - `title` (required)
  - `date` (required, `YYYY-MM-DD`)
  - `slug` (auto from title if left empty)
  - `author` (optional)
  - `image` (optional hero path)
  - `imageAlt` (recommended if `image` set)
  - `summary` (recommended, ≤ 200 chars)
  - `tags` (optional, array)

### Notes and tips
- Everything runs locally in your browser; no uploads occur
- If you attach images, the ZIP includes them under the correct year/month folder
- If you leave `slug` empty, it is generated from the title
- The body supports Markdown; the preview is optional

### Related docs
- `NEWS_FORMAT_SPEC.md` (repository root)
- `incoming/README.md` (repository root)
- `generator/ZIP_FORMAT.md`

### Troubleshooting
- If a modal overlay appears or blocks interaction, open `emergency-fix.html` (in this folder) and use the emergency controls described there
- If images do not show on the site after import, ensure the `image` path in front matter starts with `/static/uploads/news/` and files exist in `/static/uploads/news/YYYY/MM/`

