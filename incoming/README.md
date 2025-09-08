### Incoming ZIPs (Editor Workflow)

Drop generator ZIP files into this `incoming/` folder to import them into the website.

What happens on import:
- The ZIP is unzipped into a temporary folder
- The news Markdown file is moved to `content/news/`
- Images are moved to `static/uploads/news/YYYY/MM/`
- Image paths in the Markdown front matter and body are fixed to absolute `/static/uploads/news/...`
- The news index is rebuilt
- A local git commit is created (no push)

How to use (no command line):
1. Save the ZIP from the News Generator
2. Copy the ZIP into `incoming/`
3. Double‑click one of these at the repository root:
   - Windows: `run_watch_incoming.bat` (keeps watching) or `run_import_once.bat`
   - Mac/Linux: `run_watch_incoming.sh` (keeps watching) or `run_import_once.sh`

GitHub automation:
- When a ZIP under `incoming/` is pushed to the `main` branch, GitHub Actions automatically runs the importer and commits the moved files.
- You will see a commit with the message `ci: import incoming zips` after the automation finishes.

Troubleshooting:
- If nothing happens, ensure the script window stays open (watch mode) or run the one‑time import again
- If the ZIP has no `content/news/*.md`, the importer will skip it
- If git is not installed or this is not a git repo, the import will work but no commit will be made
- If images don’t show on the site, confirm the front matter `image:` begins with `/static/uploads/news/` and the files exist under `static/uploads/news/YYYY/MM/`

