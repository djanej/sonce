#!/usr/bin/env python3

import os
import re
import sys
import zipfile
import shutil
import unicodedata
import subprocess
import json
from datetime import datetime
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except Exception as e:
    print("This tool requires Python with Tkinter installed.\n"
          "On Windows and macOS, Tkinter is included with the standard installer.\n"
          "On Linux, install the Tkinter package via your package manager (e.g., python3-tk).\n")
    raise


APP_TITLE = "Sonce News Maker (Simple)"
OUTPUT_ROOT = Path(__file__).parent / "output"
PREFS_PATH = OUTPUT_ROOT / "prefs.json"


def to_slug(value: str) -> str:
    text = str(value or "").strip().lower()
    # Remove diacritics
    text = unicodedata.normalize('NFD', text)
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
    # Replace non-alphanumeric with hyphens
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"(^-|-$)", "", text)
    return text


def today_date_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def now_iso_local() -> str:
    return datetime.now().astimezone().isoformat(timespec='seconds')


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def copy_image_to_uploads(src_path: Path, dest_dir: Path, dest_filename: str, optimize: bool = False) -> Path:
    ensure_dir(dest_dir)
    ext = src_path.suffix.lower()
    target = dest_dir / f"{dest_filename}{ext}"
    # Avoid overwriting by adding numeric suffix if needed
    counter = 2
    while target.exists():
        target = dest_dir / f"{dest_filename}-{counter}{ext}"
        counter += 1
    if optimize:
        try:
            from PIL import Image  # type: ignore
            with Image.open(src_path) as im:
                save_kwargs = {}
                if ext in (".jpg", ".jpeg"):
                    # convert to RGB if needed
                    if im.mode in ("RGBA", "P"):
                        im = im.convert("RGB")
                    save_kwargs = {"quality": 85, "optimize": True, "progressive": True}
                elif ext == ".png":
                    save_kwargs = {"optimize": True}
                # Avoid very large metadata blocks
                im.save(target, **save_kwargs)
        except Exception:
            shutil.copy2(src_path, target)
    else:
        shutil.copy2(src_path, target)
    return target


def yaml_escape(text: str) -> str:
    if text is None:
        return ""
    s = str(text)
    # Quote if contains special characters
    if re.search(r'[":#\[\],]', s) or s.strip() != s or ' ' in s:
        # escape quotes
        s = s.replace('"', '\\"')
        return f'"{s}"'
    return s


class _Tooltip:
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tipwindow: tk.Toplevel | None = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _event=None):
        if self.tipwindow is not None:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "9"), padx=6, pady=3)
        label.pack(ipadx=1)

    def hide(self, _event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw is not None:
            tw.destroy()


class NewsGeneratorApp:
    def __init__(self, master: tk.Tk):
        self.master = master
        master.title(APP_TITLE)

        # State
        self.hero_image_path: Path | None = None
        self.additional_images: list[Path] = []
        self.last_generated_paths: list[Path] = []
        self.last_zip_path: Path | None = None
        self._hero_photo = None  # keep ref for Tk image

        # Variables
        self.var_title = tk.StringVar()
        self.var_date = tk.StringVar(value=today_date_str())
        self.var_datetime = tk.StringVar(value=now_iso_local())
        self.var_author = tk.StringVar()
        self.var_slug = tk.StringVar()
        self.var_tags = tk.StringVar()
        self.var_draft = tk.BooleanVar(value=True)
        self.var_image_alt = tk.StringVar()
        self.var_dark_mode = tk.BooleanVar(value=False)
        self.var_large_text = tk.BooleanVar(value=False)
        self.var_simple_mode = tk.BooleanVar(value=True)
        self.var_optimize_images = tk.BooleanVar(value=True)
        self.var_remember_incoming = tk.BooleanVar(value=True)
        self._last_incoming_dir: Path | None = None

        # Load preferences
        self._load_preferences()

        # Layout
        container = ttk.Frame(master, padding=12)
        container.grid(row=0, column=0, sticky="nsew")
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)

        # Form grid
        row = 0
        ttk.Label(container, text="Title (headline)").grid(row=row, column=0, sticky="w")
        e_title = ttk.Entry(container, textvariable=self.var_title, width=60)
        e_title.grid(row=row, column=1, columnspan=3, sticky="ew", padx=(8,0))
        e_title.bind("<KeyRelease>", self._on_title_change)
        self._add_tooltip(e_title, "Write the big headline for your news.")
        # Title counter
        self.lbl_title_count = ttk.Label(container, text="0/100")
        self.lbl_title_count.grid(row=row, column=3, sticky="e")
        row += 1

        ttk.Label(container, text="Date (YYYY-MM-DD)").grid(row=row, column=0, sticky="w")
        entry_date = ttk.Entry(container, textvariable=self.var_date, width=20)
        entry_date.grid(row=row, column=1, sticky="w", padx=(8,0))
        self._add_tooltip(entry_date, "Publication date. Click Today if unsure.")
        ttk.Button(container, text="Today", command=lambda: self.var_date.set(today_date_str())).grid(row=row, column=2, sticky="w", padx=(8,0))
        row += 1

        ttk.Label(container, text="Exact time (optional)").grid(row=row, column=0, sticky="w")
        entry_dt = ttk.Entry(container, textvariable=self.var_datetime, width=40)
        entry_dt.grid(row=row, column=1, sticky="w", padx=(8,0))
        self._add_tooltip(entry_dt, "Exact time with timezone. You can leave this as-is or click Now.")
        ttk.Button(container, text="Now", command=lambda: self.var_datetime.set(now_iso_local())).grid(row=row, column=2, sticky="w", padx=(8,0))
        row += 1

        ttk.Label(container, text="Author (optional)").grid(row=row, column=0, sticky="w")
        entry_author = ttk.Entry(container, textvariable=self.var_author, width=40)
        entry_author.grid(row=row, column=1, columnspan=2, sticky="ew", padx=(8,0))
        self._add_tooltip(entry_author, "Who wrote this? You can leave it empty.")
        row += 1

        ttk.Label(container, text="Web address name (slug)").grid(row=row, column=0, sticky="w")
        entry_slug = ttk.Entry(container, textvariable=self.var_slug, width=40)
        entry_slug.grid(row=row, column=1, sticky="w", padx=(8,0))
        self._add_tooltip(entry_slug, "Short web-friendly name. Letters, numbers, and dashes only.")
        ttk.Button(container, text="Regenerate", command=self._regen_slug).grid(row=row, column=2, sticky="w", padx=(8,0))
        row += 1

        ttk.Label(container, text="Summary (one or two sentences)").grid(row=row, column=0, sticky="nw")
        self.txt_summary = tk.Text(container, width=60, height=4)
        self.txt_summary.grid(row=row, column=1, columnspan=3, sticky="ew", padx=(8,0))
        self._add_tooltip(self.txt_summary, "A short preview. Keep it simple—one or two sentences.")
        # Summary counter
        self.lbl_summary_count = ttk.Label(container, text="0/200")
        self.lbl_summary_count.grid(row=row, column=3, sticky="se")
        row += 1

        ttk.Label(container, text="Tags (optional, comma-separated)").grid(row=row, column=0, sticky="w")
        entry_tags = ttk.Entry(container, textvariable=self.var_tags, width=60)
        entry_tags.grid(row=row, column=1, columnspan=3, sticky="ew", padx=(8,0))
        self._add_tooltip(entry_tags, "Words that describe the news, e.g. news, community.")
        row += 1

        ttk.Checkbutton(container, text="Keep as Draft (recommended)", variable=self.var_draft).grid(row=row, column=0, sticky="w")
        row += 1

        # Images
        ttk.Label(container, text="Hero image (optional)").grid(row=row, column=0, sticky="w")
        self.lbl_hero = ttk.Label(container, text="None selected")
        self.lbl_hero.grid(row=row, column=1, sticky="w", padx=(8,0))
        ttk.Button(container, text="Choose…", command=self.choose_hero).grid(row=row, column=2, sticky="w")
        # Small preview area
        self.lbl_hero_preview = ttk.Label(container, text="")
        self.lbl_hero_preview.grid(row=row, column=3, sticky="e")
        self._add_tooltip(self.lbl_hero, "Main picture shown with the news. Optional but recommended.")
        row += 1

        ttk.Label(container, text="Image description (alt text)").grid(row=row, column=0, sticky="w")
        entry_alt = ttk.Entry(container, textvariable=self.var_image_alt, width=60)
        entry_alt.grid(row=row, column=1, columnspan=3, sticky="ew", padx=(8,0))
        self._add_tooltip(entry_alt, "A short description of the image for accessibility.")
        row += 1

        ttk.Label(container, text="Additional images (optional)").grid(row=row, column=0, sticky="nw")
        self.lst_images = tk.Listbox(container, height=4, width=50)
        self.lst_images.grid(row=row, column=1, columnspan=2, sticky="ew", padx=(8,0))
        btns = ttk.Frame(container)
        btns.grid(row=row, column=3, sticky="n")
        ttk.Button(btns, text="Add…", command=self.add_images).grid(row=0, column=0, sticky="ew", pady=2)
        ttk.Button(btns, text="Remove", command=self.remove_selected_image).grid(row=1, column=0, sticky="ew", pady=2)
        ttk.Button(btns, text="Insert hero", command=self.insert_hero_image_markdown).grid(row=2, column=0, sticky="ew", pady=2)
        ttk.Button(btns, text="Insert selected", command=self.insert_selected_image_markdown).grid(row=3, column=0, sticky="ew", pady=2)
        row += 1

        # Body content (optional)
        ttk.Label(container, text="Body (optional)").grid(row=row, column=0, sticky="nw")
        self.txt_body = tk.Text(container, width=60, height=12)
        self.txt_body.grid(row=row, column=1, columnspan=3, sticky="ew", padx=(8,0))
        self._add_tooltip(self.txt_body, "The full text of your news. You can leave it empty.")
        # Reading time
        self.lbl_reading_time = ttk.Label(container, text="Reading: 0 min")
        self.lbl_reading_time.grid(row=row, column=3, sticky="ne")
        row += 1

        # Actions
        actions = ttk.Frame(container)
        actions.grid(row=row, column=0, columnspan=4, sticky="ew", pady=(8,0))
        # Simple mode one-click
        self.btn_one_click = ttk.Button(actions, text="Send to Website (One Click)", command=self.one_click_send)
        self.btn_one_click.grid(row=0, column=0, padx=(0,8))
        self._add_tooltip(self.btn_one_click, "Generate draft, create ZIP, and copy to incoming in one go.")

        btn_gen = ttk.Button(actions, text="Generate Draft", command=self.generate_draft)
        btn_gen.grid(row=0, column=1, padx=(0,8))
        self._add_tooltip(btn_gen, "Create the files on your computer (no publishing).")

        btn_zip = ttk.Button(actions, text="Create ZIP", command=self.create_zip)
        btn_zip.grid(row=0, column=2, padx=(0,8))
        self._add_tooltip(btn_zip, "Packs the draft and images into one ZIP.")

        ttk.Button(actions, text="Preview", command=self.show_preview).grid(row=0, column=3, padx=(0,8))
        ttk.Button(actions, text="Open Output Folder", command=self.open_output_folder).grid(row=0, column=4, padx=(0,8))
        ttk.Button(actions, text="Copy ZIP to incoming…", command=self.copy_zip_to_incoming).grid(row=0, column=5, padx=(0,8))
        ttk.Button(actions, text="Reset Form", command=self.reset_form).grid(row=0, column=6, padx=(0,8))
        ttk.Button(actions, text="How it works", command=self.show_help).grid(row=0, column=7)

        # Status
        row += 1
        self.var_status = tk.StringVar(value="Ready.")
        ttk.Label(container, textvariable=self.var_status).grid(row=row, column=0, columnspan=4, sticky="w", pady=(8,0))

        # Resize weights
        for c in range(4):
            container.columnconfigure(c, weight=1 if c in (1,2) else 0)

        # Menubar
        self._build_menubar()

        # Bind updates
        e_title.bind("<KeyRelease>", self._on_any_change)
        self.txt_summary.bind("<KeyRelease>", self._on_any_change)
        self.txt_body.bind("<KeyRelease>", self._on_any_change)

        # Apply theme from prefs
        self.apply_theme()

    def _on_title_change(self, _event=None):
        if not self.var_slug.get().strip():
            self.var_slug.set(to_slug(self.var_title.get()))

    def _regen_slug(self):
        self.var_slug.set(to_slug(self.var_title.get()))

    def choose_hero(self):
        path = filedialog.askopenfilename(title="Choose hero image",
                                          filetypes=[("Images", ".jpg .jpeg .png .gif .webp .svg"), ("All files", "*.*")])
        if path:
            self.hero_image_path = Path(path)
            self.lbl_hero.config(text=str(self.hero_image_path.name))
            self._update_hero_preview()

    def add_images(self):
        paths = filedialog.askopenfilenames(title="Choose additional images",
                                            filetypes=[("Images", ".jpg .jpeg .png .gif .webp .svg"), ("All files", "*.*")])
        for p in paths:
            pth = Path(p)
            if pth not in self.additional_images:
                self.additional_images.append(pth)
                self.lst_images.insert(tk.END, pth.name)

    def remove_selected_image(self):
        sel = list(self.lst_images.curselection())
        sel.reverse()
        for idx in sel:
            path = self.additional_images[idx]
            del self.additional_images[idx]
            self.lst_images.delete(idx)

    def _validate_inputs(self) -> tuple[bool, str]:
        title = self.var_title.get().strip()
        if not title:
            return False, "Title is required."
        if len(title) > 100:
            return False, "Title must be at most 100 characters."
        date_str = self.var_date.get().strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            return False, "Date must be in YYYY-MM-DD format."
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            return False, "Date is not a valid calendar date."
        slug = to_slug(self.var_slug.get() or self.var_title.get())
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", slug):
            return False, "Slug must be lowercase letters/numbers with hyphens."
        # Summary length
        summary = self.txt_summary.get("1.0", tk.END).strip().replace("\n", " ")
        if len(summary) > 200:
            return False, "Summary should be 200 characters or less."
        # If hero selected, require alt
        if self.hero_image_path and not self.var_image_alt.get().strip():
            return False, "Please provide image description (alt text) for the hero image."
        return True, ""

    def generate_draft(self):
        ok, msg = self._validate_inputs()
        if not ok:
            messagebox.showerror("Invalid input", msg)
            return

        # Collect data
        title = self.var_title.get().strip()
        date_str = self.var_date.get().strip()
        dt_iso = self.var_datetime.get().strip() or now_iso_local()
        author = self.var_author.get().strip()
        slug = to_slug(self.var_slug.get() or title)
        summary = self.txt_summary.get("1.0", tk.END).strip().replace("\n", " ")
        tags_raw = [t.strip() for t in self.var_tags.get().split(',') if t.strip()]
        tags = tags_raw
        draft = bool(self.var_draft.get())
        image_alt = self.var_image_alt.get().strip() or title
        body = self.txt_body.get("1.0", tk.END).rstrip()

        year, month = date_str.split('-')[0], date_str.split('-')[1]

        # Prepare output dirs
        content_dir = OUTPUT_ROOT / "content" / "news"
        uploads_dir = OUTPUT_ROOT / "static" / "uploads" / "news" / year / month
        ensure_dir(content_dir)
        ensure_dir(uploads_dir)

        # Copy images
        image_url = ""
        written_paths: list[Path] = []
        if self.hero_image_path:
            hero_base = f"{date_str}-{slug}-hero"
            copied = copy_image_to_uploads(self.hero_image_path, uploads_dir, hero_base, optimize=bool(self.var_optimize_images.get()))
            # Compute absolute web path
            image_url = "/" + "/".join(copied.relative_to(OUTPUT_ROOT).parts)
            image_url = image_url.replace("\\", "/")
            written_paths.append(copied)

        # Additional images
        for add_path in self.additional_images:
            base_name = add_path.stem
            desc = to_slug(base_name)
            if not desc or desc == "hero":
                desc = "image"
            add_base = f"{date_str}-{slug}-{desc}"
            copied = copy_image_to_uploads(add_path, uploads_dir, add_base, optimize=bool(self.var_optimize_images.get()))
            written_paths.append(copied)

        # Build frontmatter (compatible with site spec; date as YYYY-MM-DD)
        fm_lines = [
            "---",
            f"title: {yaml_escape(title)}",
            f"date: {date_str}",
            f"slug: {yaml_escape(slug)}",
        ]
        if author:
            fm_lines.append(f"author: {yaml_escape(author)}")
        if summary:
            # Trim to ~200 characters to align with site expectations
            short = summary[:200].rstrip()
            fm_lines.append(f"summary: {yaml_escape(short)}")
        if image_url:
            fm_lines.append(f"image: {yaml_escape(image_url)}")
        if image_alt:
            fm_lines.append(f"imageAlt: {yaml_escape(image_alt)}")
        if tags:
            # YAML inline list: [tag1, tag2]
            tags_escaped = ", ".join(yaml_escape(t) for t in tags)
            fm_lines.append(f"tags: [{tags_escaped}]")
        # Always write draft flag for safety
        fm_lines.append(f"draft: {'true' if draft else 'false'}")
        # Keep the full datetime for human reference; site ignores unknown fields
        if dt_iso:
            fm_lines.append(f"datetime: {yaml_escape(dt_iso)}")
        fm_lines.append("---")

        # Markdown body
        if not body.strip():
            body = "Write your content here."

        content = "\n".join(fm_lines) + "\n\n" + body + "\n"

        # Filename and write
        filename = f"{date_str}-{slug}.md"
        md_path = content_dir / filename
        if md_path.exists():
            if not messagebox.askyesno("Overwrite?", f"{md_path.name} already exists. Overwrite?"):
                self.var_status.set("Cancelled: not overwriting existing file.")
                return
        md_path.write_text(content, encoding='utf-8')
        written_paths.append(md_path)

        # Save last generated set (relative to OUTPUT_ROOT)
        rel_written = [p.relative_to(OUTPUT_ROOT) for p in written_paths]
        self.last_generated_paths = rel_written

        self.var_status.set(f"Draft generated: {md_path}")
        messagebox.showinfo("Success", f"Draft created at:\n{md_path}\n\nImages (if any) were copied under:\n{uploads_dir}")

    def create_zip(self):
        if not self.last_generated_paths:
            messagebox.showwarning("Nothing to zip", "Generate a draft first.")
            return

        # Try to find the markdown file in the last set to name the zip
        md_rel = None
        for p in self.last_generated_paths:
            if p.as_posix().endswith('.md'):
                md_rel = p
                break
        if md_rel is None:
            messagebox.showerror("Error", "Could not locate the markdown file to name the ZIP.")
            return

        slug_part = md_rel.name[:-3]
        zip_name = f"news-draft-{slug_part}.zip"
        dist_dir = OUTPUT_ROOT
        ensure_dir(dist_dir)
        zip_path = dist_dir / zip_name

        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            for rel in self.last_generated_paths:
                abs_path = OUTPUT_ROOT / rel
                if abs_path.is_file():
                    # Keep content/ and static/ folder roots inside the archive
                    zf.write(abs_path, arcname=str(rel))

        self.last_zip_path = zip_path
        # Preflight validate ZIP
        problems: list[str] = []
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                if zf.testzip() is not None:
                    problems.append("ZIP contains a corrupted file.")
                names = [i.filename for i in zf.infolist() if not i.is_dir()]
                md_files = [n for n in names if n.startswith('content/news/') and n.lower().endswith('.md')]
                if not md_files:
                    problems.append('Missing content/news/*.md')
                else:
                    md_names = [os.path.basename(n) for n in md_files]
                    for fname in md_names:
                        if not re.match(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$", fname):
                            problems.append(f"Markdown filename must be YYYY-MM-DD-slug.md: {fname}")
                for n in names:
                    if n.startswith('static/uploads/news/'):
                        parts = Path(n).parts
                        if len(parts) < 6:
                            problems.append(f"Image path should be static/uploads/news/YYYY/MM/…: {n}")
        except Exception as e:
            problems.append(f"Could not open ZIP: {e}")

        if problems:
            self.var_status.set(f"ZIP created with warnings: {zip_path}")
            messagebox.showwarning("ZIP created with warnings", "\n".join([f"ZIP: {zip_path}"] + problems))
        else:
            self.var_status.set(f"ZIP created: {zip_path}")
            messagebox.showinfo("ZIP ready", f"ZIP created at:\n{zip_path}\n\nYou can now copy it into your website folder's incoming/ directory.")

    def open_output_folder(self):
        ensure_dir(OUTPUT_ROOT)
        try:
            if sys.platform == 'win32':
                os.startfile(str(OUTPUT_ROOT))  # type: ignore[attr-defined]
            elif sys.platform == 'darwin':
                subprocess.run(['open', str(OUTPUT_ROOT)], check=False)
            else:
                subprocess.run(['xdg-open', str(OUTPUT_ROOT)], check=False)
        except Exception as e:
            messagebox.showerror("Cannot open folder", f"Please open this folder manually:\n{OUTPUT_ROOT}\n\nError: {e}")

    def copy_zip_to_incoming(self):
        if not self.last_zip_path or not self.last_zip_path.exists():
            # Try to find a recent ZIP in OUTPUT_ROOT
            candidates = sorted(OUTPUT_ROOT.glob('news-draft-*.zip'), key=lambda p: p.stat().st_mtime, reverse=True)
            if candidates:
                self.last_zip_path = candidates[0]
            else:
                messagebox.showwarning("No ZIP found", "Please click 'Create ZIP' first.")
                return

        messagebox.showinfo(
            "Choose website folder",
            "Select your website folder. If you click on the 'incoming' folder itself, that's okay too."
        )
        initialdir = None
        if self.var_remember_incoming.get() and self._last_incoming_dir and self._last_incoming_dir.exists():
            initialdir = str(self._last_incoming_dir)
        selected = filedialog.askdirectory(title="Select your website folder (or incoming)", initialdir=initialdir if initialdir else None)
        if not selected:
            return
        target = Path(selected)
        incoming_dir = target if target.name.lower() == 'incoming' else (target / 'incoming')
        try:
            incoming_dir.mkdir(parents=True, exist_ok=True)
            dest = incoming_dir / self.last_zip_path.name
            shutil.copy2(self.last_zip_path, dest)
            self.var_status.set(f"Copied ZIP to: {dest}")
            if self.var_remember_incoming.get():
                self._last_incoming_dir = incoming_dir
                self._save_preferences()
            # If validator exists, try to run it for extra confidence
            validator = (target if target.name.lower() != 'incoming' else target.parent) / 'tools' / 'validate_incoming_zip.py'
            if validator.exists():
                try:
                    completed = subprocess.run([sys.executable, str(validator), str(dest)], capture_output=True, text=True, check=False)
                    out = completed.stdout.strip()
                    err = completed.stderr.strip()
                    msg = out or ''
                    if err:
                        msg += ("\n" if msg else "") + f"stderr:\n{err}"
                    messagebox.showinfo("Validation", msg if msg else "Validation script finished.")
                except Exception as e:
                    messagebox.showwarning("Validation error", f"Could not run validator script:\n{e}")
            messagebox.showinfo("Copied", f"ZIP copied to:\n{dest}\n\nCommit and push this to GitHub (main). The site will import it automatically.")
        except Exception as e:
            messagebox.showerror("Copy failed", f"Could not copy to incoming/:\n{e}")

    def show_help(self):
        steps = (
            "1) Title: Write the headline.\n"
            "2) Date: Click Today (or choose the publication date).\n"
            "3) Optional: Choose a hero image and write a short description.\n"
            "4) Click Generate Draft.\n"
            "5) Click Create ZIP.\n"
            "6) Click Copy ZIP to incoming… and pick your website folder.\n\n"
            "After you push to GitHub (main), the site automatically places files in the right folders."
        )
        messagebox.showinfo("How it works", steps)

    # Simple tooltip helper
    def _add_tooltip(self, widget, text: str):
        tip = _Tooltip(widget, text)
        return tip

    def reset_form(self):
        self.var_title.set("")
        self.var_date.set(today_date_str())
        self.var_datetime.set(now_iso_local())
        self.var_author.set("")
        self.var_slug.set("")
        self.var_tags.set("")
        self.var_draft.set(True)
        self.var_image_alt.set("")
        self.txt_summary.delete("1.0", tk.END)
        self.txt_body.delete("1.0", tk.END)
        self.hero_image_path = None
        self.additional_images.clear()
        self.lst_images.delete(0, tk.END)
        self.lbl_hero.config(text="None selected")
        self.lbl_hero_preview.config(text="", image='')
        self.last_generated_paths = []
        self.var_status.set("Ready.")

    # ---------- New helpers ----------
    def _build_menubar(self):
        menubar = tk.Menu(self.master)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="New", command=self.reset_form)
        filemenu.add_command(label="Save draft…", command=self.save_draft)
        filemenu.add_command(label="Load draft…", command=self.load_draft)
        filemenu.add_separator()
        filemenu.add_command(label="Quit", command=self.master.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        viewmenu = tk.Menu(menubar, tearoff=0)
        viewmenu.add_checkbutton(label="Simple mode (Dad)", onvalue=True, offvalue=False, variable=self.var_simple_mode, command=self.apply_simple_mode)
        viewmenu.add_checkbutton(label="Dark mode", onvalue=True, offvalue=False, variable=self.var_dark_mode, command=self.apply_theme)
        viewmenu.add_checkbutton(label="Large text", onvalue=True, offvalue=False, variable=self.var_large_text, command=self.apply_theme)
        viewmenu.add_checkbutton(label="Optimize images (smaller files)", onvalue=True, offvalue=False, variable=self.var_optimize_images)
        viewmenu.add_checkbutton(label="Remember incoming folder", onvalue=True, offvalue=False, variable=self.var_remember_incoming)
        menubar.add_cascade(label="View", menu=viewmenu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="How it works", command=self.show_help)
        menubar.add_cascade(label="Help", menu=helpmenu)
        self.master.config(menu=menubar)

    def _on_any_change(self, _event=None):
        # Update counters and derived labels
        title_len = len(self.var_title.get())
        self.lbl_title_count.config(text=f"{title_len}/100", foreground=("#b00020" if title_len > 100 else ""))
        summary = self.txt_summary.get("1.0", tk.END).strip().replace("\n", " ")
        self.lbl_summary_count.config(text=f"{len(summary)}/200", foreground=("#b00020" if len(summary) > 200 else ""))
        # Reading time
        body = self.txt_body.get("1.0", tk.END)
        words = len([w for w in re.split(r"\s+", body) if w])
        minutes = max(0, (words + 199) // 200)
        self.lbl_reading_time.config(text=f"Reading: {minutes} min")

    def _update_hero_preview(self):
        # Try to show a small preview using Tk's PhotoImage for PNG/GIF, else skip
        try:
            from PIL import Image, ImageTk  # type: ignore
        except Exception:
            # Fallback: show filename only
            self.lbl_hero_preview.config(text="(preview unavailable)")
            self.lbl_hero_preview.configure(image='')
            self._hero_photo = None
            return
        try:
            im = Image.open(self.hero_image_path)  # type: ignore[arg-type]
            im.thumbnail((96, 96))
            self._hero_photo = ImageTk.PhotoImage(im)
            self.lbl_hero_preview.configure(image=self._hero_photo)
            self.lbl_hero_preview.config(text="")
        except Exception:
            self.lbl_hero_preview.config(text="(preview unavailable)")
            self.lbl_hero_preview.configure(image='')
            self._hero_photo = None

    def _compute_image_web_path(self, date_str: str, slug: str, description: str) -> str:
        year, month = date_str.split('-')[0], date_str.split('-')[1]
        safe_desc = to_slug(description) or 'image'
        return f"/static/uploads/news/{year}/{month}/{date_str}-{slug}-{safe_desc}"

    def insert_hero_image_markdown(self):
        title = self.var_title.get().strip()
        date_str = self.var_date.get().strip()
        slug = to_slug(self.var_slug.get() or title)
        if not (title and re.match(r"^\d{4}-\d{2}-\d{2}$", date_str) and slug):
            messagebox.showwarning("Missing info", "Please fill Title and Date first.")
            return
        base = self._compute_image_web_path(date_str, slug, 'hero')
        # Try to detect extension from selected hero, else leave without ext
        ext = (self.hero_image_path.suffix if self.hero_image_path else '')
        path = base + (ext if ext else '')
        alt = self.var_image_alt.get().strip() or title
        self._insert_into_body(f"![{alt}]({path})\n\n")

    def insert_selected_image_markdown(self):
        sel = self.lst_images.curselection()
        if not sel:
            messagebox.showwarning("No image selected", "Select an additional image first.")
            return
        idx = sel[0]
        add_path = self.additional_images[idx]
        title = self.var_title.get().strip()
        date_str = self.var_date.get().strip()
        slug = to_slug(self.var_slug.get() or title)
        if not (title and re.match(r"^\d{4}-\d{2}-\d{2}$", date_str) and slug):
            messagebox.showwarning("Missing info", "Please fill Title and Date first.")
            return
        desc = to_slug(add_path.stem) or 'image'
        base = self._compute_image_web_path(date_str, slug, desc)
        ext = add_path.suffix
        path = base + ext
        alt = desc.replace('-', ' ')
        self._insert_into_body(f"![{alt}]({path})\n\n")

    def _insert_into_body(self, text: str):
        try:
            self.txt_body.insert(tk.INSERT, text)
            self.txt_body.focus_set()
        except Exception:
            pass

    def show_preview(self):
        # Build content preview
        ok, msg = self._validate_inputs()
        if not ok:
            if not messagebox.askyesno("Preview with warnings?", f"{msg}\n\nContinue to preview anyway?"):
                return
        title = self.var_title.get().strip()
        date_str = self.var_date.get().strip()
        dt_iso = self.var_datetime.get().strip() or now_iso_local()
        author = self.var_author.get().strip()
        slug = to_slug(self.var_slug.get() or title)
        summary = self.txt_summary.get("1.0", tk.END).strip().replace("\n", " ")
        tags = [t.strip() for t in self.var_tags.get().split(',') if t.strip()]
        draft = bool(self.var_draft.get())
        image_url = ""
        if self.hero_image_path:
            year, month = date_str.split('-')[0], date_str.split('-')[1]
            image_url = f"/static/uploads/news/{year}/{month}/{date_str}-{slug}-hero{self.hero_image_path.suffix.lower()}"
        fm_lines = [
            "---",
            f"title: {yaml_escape(title)}",
            f"date: {date_str}",
            f"slug: {yaml_escape(slug)}",
        ]
        if author:
            fm_lines.append(f"author: {yaml_escape(author)}")
        if summary:
            fm_lines.append(f"summary: {yaml_escape(summary[:200].rstrip())}")
        if image_url:
            fm_lines.append(f"image: {yaml_escape(image_url)}")
        if self.var_image_alt.get().strip():
            fm_lines.append(f"imageAlt: {yaml_escape(self.var_image_alt.get().strip())}")
        if tags:
            fm_lines.append(f"tags: [{', '.join(yaml_escape(t) for t in tags)}]")
        fm_lines.append(f"draft: {'true' if draft else 'false'}")
        fm_lines.append(f"datetime: {yaml_escape(dt_iso)}")
        fm_lines.append("---")
        body = self.txt_body.get("1.0", tk.END).rstrip() or "Write your content here."
        content = "\n".join(fm_lines) + "\n\n" + body + "\n"
        # Show in toplevel
        top = tk.Toplevel(self.master)
        top.title("Preview")
        top.geometry("800x600")
        txt = tk.Text(top, wrap="word")
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", content)
        txt.config(state="disabled")

    def apply_theme(self):
        # Lightweight theming without extra deps
        try:
            style = ttk.Style(self.master)
            theme = 'clam'
            if sys.platform == 'win32':
                theme = 'xpnative'
            elif sys.platform == 'darwin':
                theme = 'aqua'
            try:
                style.theme_use(theme)
            except Exception:
                pass
            # Font sizing
            base_font = ("TkDefaultFont", 12 if self.var_large_text.get() else 10)
            self.master.option_add("*Font", base_font)
            # Dark mode tweaks (best-effort)
            if self.var_dark_mode.get():
                bg = "#1e1e1e"
                fg = "#f2f2f2"
                style.configure('.', background=bg, foreground=fg)
                style.configure('TEntry', fieldbackground="#2a2a2a", foreground=fg)
                style.map('TButton', foreground=[('active', fg)], background=[('active', '#333')])
                try:
                    self.master.configure(background=bg)
                except Exception:
                    pass
            else:
                # Reset to defaults
                style.configure('.', background=None, foreground=None)
            # Persist preferences
            self._save_preferences()
        except Exception:
            pass

    def apply_simple_mode(self):
        # In simple mode, highlight one-click action
        try:
            if self.var_simple_mode.get():
                self.btn_one_click.configure(style='Accent.TButton')
            else:
                self.btn_one_click.configure(style='TButton')
            self._save_preferences()
        except Exception:
            pass

    def _load_preferences(self):
        try:
            ensure_dir(OUTPUT_ROOT)
            if PREFS_PATH.exists():
                data = json.loads(PREFS_PATH.read_text(encoding='utf-8'))
                self.var_author.set(str(data.get('defaultAuthor', '')))
                self.var_dark_mode.set(bool(data.get('darkMode', False)))
                self.var_large_text.set(bool(data.get('largeText', False)))
                self.var_simple_mode.set(bool(data.get('simpleMode', True)))
                self.var_optimize_images.set(bool(data.get('optimizeImages', True)))
                self.var_remember_incoming.set(bool(data.get('rememberIncoming', True)))
                last_incoming = data.get('lastIncomingDir', '')
                self._last_incoming_dir = Path(last_incoming) if last_incoming else None
        except Exception:
            pass

    def _save_preferences(self):
        try:
            ensure_dir(OUTPUT_ROOT)
            data = {
                'defaultAuthor': self.var_author.get().strip(),
                'darkMode': bool(self.var_dark_mode.get()),
                'largeText': bool(self.var_large_text.get()),
                'simpleMode': bool(self.var_simple_mode.get()),
                'optimizeImages': bool(self.var_optimize_images.get()),
                'rememberIncoming': bool(self.var_remember_incoming.get()),
                'lastIncomingDir': str(self._last_incoming_dir) if self._last_incoming_dir else '',
            }
            PREFS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception:
            pass

    def one_click_send(self):
        # One step: validate inputs, generate draft, zip, ask folder (or reuse), copy
        ok, msg = self._validate_inputs()
        if not ok:
            messagebox.showerror("Invalid input", msg)
            return
        self.generate_draft()
        self.create_zip()
        # Reuse last incoming if remembered
        if self.var_remember_incoming.get() and self._last_incoming_dir and self._last_incoming_dir.exists():
            try:
                dest = self._last_incoming_dir / (self.last_zip_path.name if self.last_zip_path else "")
                if self.last_zip_path and self.last_zip_path.exists():
                    shutil.copy2(self.last_zip_path, dest)
                    self.var_status.set(f"Copied ZIP to: {dest}")
                    messagebox.showinfo("Copied", f"ZIP copied to:\n{dest}\n\nCommit and push this to GitHub (main). The site will import it automatically.")
                    return
            except Exception:
                # Fall back to normal flow
                pass
        # Otherwise, ask
        self.copy_zip_to_incoming()

    def save_draft(self):
        ensure_dir(OUTPUT_ROOT)
        drafts_dir = OUTPUT_ROOT / 'drafts'
        ensure_dir(drafts_dir)
        default_name = f"{self.var_date.get()}-{to_slug(self.var_slug.get() or self.var_title.get() or 'draft')}.json"
        path = filedialog.asksaveasfilename(title="Save draft", defaultextension=".json", initialdir=str(drafts_dir), initialfile=default_name, filetypes=[("JSON", ".json")])
        if not path:
            return
        data = {
            'title': self.var_title.get(),
            'date': self.var_date.get(),
            'datetime': self.var_datetime.get(),
            'author': self.var_author.get(),
            'slug': self.var_slug.get(),
            'summary': self.txt_summary.get("1.0", tk.END),
            'tags': self.var_tags.get(),
            'draft': bool(self.var_draft.get()),
            'imageAlt': self.var_image_alt.get(),
            'body': self.txt_body.get("1.0", tk.END),
            'hero': str(self.hero_image_path) if self.hero_image_path else '',
            'additional': [str(p) for p in self.additional_images],
        }
        try:
            Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            self.var_status.set(f"Draft saved: {path}")
        except Exception as e:
            messagebox.showerror("Save failed", str(e))

    def load_draft(self):
        path = filedialog.askopenfilename(title="Load draft", filetypes=[("JSON", ".json"), ("All files", "*.*")])
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding='utf-8'))
            self.var_title.set(data.get('title', ''))
            self.var_date.set(data.get('date', today_date_str()))
            self.var_datetime.set(data.get('datetime', now_iso_local()))
            self.var_author.set(data.get('author', ''))
            self.var_slug.set(data.get('slug', ''))
            self.txt_summary.delete("1.0", tk.END)
            self.txt_summary.insert("1.0", data.get('summary', ''))
            self.var_tags.set(data.get('tags', ''))
            self.var_draft.set(bool(data.get('draft', True)))
            self.var_image_alt.set(data.get('imageAlt', ''))
            self.txt_body.delete("1.0", tk.END)
            self.txt_body.insert("1.0", data.get('body', ''))
            hero = data.get('hero', '')
            self.hero_image_path = Path(hero) if hero else None
            self.lbl_hero.config(text=str(self.hero_image_path.name) if self.hero_image_path else "None selected")
            self._update_hero_preview()
            self.additional_images = [Path(p) for p in data.get('additional', [])]
            self.lst_images.delete(0, tk.END)
            for p in self.additional_images:
                self.lst_images.insert(tk.END, p.name)
            self._on_any_change()
            self.var_status.set(f"Draft loaded: {path}")
        except Exception as e:
            messagebox.showerror("Load failed", str(e))


def main():
    root = tk.Tk()
    # Better default minimum size
    root.minsize(800, 700)
    NewsGeneratorApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()


