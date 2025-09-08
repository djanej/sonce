#!/usr/bin/env python3

import os
import re
import sys
import zipfile
import shutil
import unicodedata
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


APP_TITLE = "Sonce News Generator (Draft Only)"
OUTPUT_ROOT = Path(__file__).parent / "output"


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


def copy_image_to_uploads(src_path: Path, dest_dir: Path, dest_filename: str) -> Path:
    ensure_dir(dest_dir)
    ext = src_path.suffix.lower()
    target = dest_dir / f"{dest_filename}{ext}"
    # Avoid overwriting by adding numeric suffix if needed
    counter = 2
    while target.exists():
        target = dest_dir / f"{dest_filename}-{counter}{ext}"
        counter += 1
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


class NewsGeneratorApp:
    def __init__(self, master: tk.Tk):
        self.master = master
        master.title(APP_TITLE)

        # State
        self.hero_image_path: Path | None = None
        self.additional_images: list[Path] = []
        self.last_generated_paths: list[Path] = []

        # Variables
        self.var_title = tk.StringVar()
        self.var_date = tk.StringVar(value=today_date_str())
        self.var_datetime = tk.StringVar(value=now_iso_local())
        self.var_author = tk.StringVar()
        self.var_slug = tk.StringVar()
        self.var_tags = tk.StringVar()
        self.var_draft = tk.BooleanVar(value=True)
        self.var_image_alt = tk.StringVar()

        # Layout
        container = ttk.Frame(master, padding=12)
        container.grid(row=0, column=0, sticky="nsew")
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)

        # Form grid
        row = 0
        ttk.Label(container, text="Title").grid(row=row, column=0, sticky="w")
        e_title = ttk.Entry(container, textvariable=self.var_title, width=60)
        e_title.grid(row=row, column=1, columnspan=3, sticky="ew", padx=(8,0))
        e_title.bind("<KeyRelease>", self._on_title_change)
        row += 1

        ttk.Label(container, text="Date (YYYY-MM-DD)").grid(row=row, column=0, sticky="w")
        ttk.Entry(container, textvariable=self.var_date, width=20).grid(row=row, column=1, sticky="w", padx=(8,0))
        ttk.Button(container, text="Today", command=lambda: self.var_date.set(today_date_str())).grid(row=row, column=2, sticky="w", padx=(8,0))
        row += 1

        ttk.Label(container, text="Datetime (ISO 8601)").grid(row=row, column=0, sticky="w")
        ttk.Entry(container, textvariable=self.var_datetime, width=40).grid(row=row, column=1, sticky="w", padx=(8,0))
        ttk.Button(container, text="Now", command=lambda: self.var_datetime.set(now_iso_local())).grid(row=row, column=2, sticky="w", padx=(8,0))
        row += 1

        ttk.Label(container, text="Author").grid(row=row, column=0, sticky="w")
        ttk.Entry(container, textvariable=self.var_author, width=40).grid(row=row, column=1, columnspan=2, sticky="ew", padx=(8,0))
        row += 1

        ttk.Label(container, text="Slug").grid(row=row, column=0, sticky="w")
        ttk.Entry(container, textvariable=self.var_slug, width=40).grid(row=row, column=1, sticky="w", padx=(8,0))
        ttk.Button(container, text="Regenerate", command=self._regen_slug).grid(row=row, column=2, sticky="w", padx=(8,0))
        row += 1

        ttk.Label(container, text="Summary (short)").grid(row=row, column=0, sticky="nw")
        self.txt_summary = tk.Text(container, width=60, height=4)
        self.txt_summary.grid(row=row, column=1, columnspan=3, sticky="ew", padx=(8,0))
        row += 1

        ttk.Label(container, text="Tags (comma-separated)").grid(row=row, column=0, sticky="w")
        ttk.Entry(container, textvariable=self.var_tags, width=60).grid(row=row, column=1, columnspan=3, sticky="ew", padx=(8,0))
        row += 1

        ttk.Checkbutton(container, text="Draft (recommended)", variable=self.var_draft).grid(row=row, column=0, sticky="w")
        row += 1

        # Images
        ttk.Label(container, text="Hero image (optional)").grid(row=row, column=0, sticky="w")
        self.lbl_hero = ttk.Label(container, text="None selected")
        self.lbl_hero.grid(row=row, column=1, columnspan=2, sticky="w", padx=(8,0))
        ttk.Button(container, text="Choose…", command=self.choose_hero).grid(row=row, column=3, sticky="w")
        row += 1

        ttk.Label(container, text="Image alt text").grid(row=row, column=0, sticky="w")
        ttk.Entry(container, textvariable=self.var_image_alt, width=60).grid(row=row, column=1, columnspan=3, sticky="ew", padx=(8,0))
        row += 1

        ttk.Label(container, text="Additional images (optional)").grid(row=row, column=0, sticky="nw")
        self.lst_images = tk.Listbox(container, height=4, width=50)
        self.lst_images.grid(row=row, column=1, columnspan=2, sticky="ew", padx=(8,0))
        btns = ttk.Frame(container)
        btns.grid(row=row, column=3, sticky="n")
        ttk.Button(btns, text="Add…", command=self.add_images).grid(row=0, column=0, sticky="ew", pady=2)
        ttk.Button(btns, text="Remove", command=self.remove_selected_image).grid(row=1, column=0, sticky="ew", pady=2)
        row += 1

        # Body content (optional)
        ttk.Label(container, text="Body (optional)").grid(row=row, column=0, sticky="nw")
        self.txt_body = tk.Text(container, width=60, height=12)
        self.txt_body.grid(row=row, column=1, columnspan=3, sticky="ew", padx=(8,0))
        row += 1

        # Actions
        actions = ttk.Frame(container)
        actions.grid(row=row, column=0, columnspan=4, sticky="ew", pady=(8,0))
        ttk.Button(actions, text="Generate Draft", command=self.generate_draft).grid(row=0, column=0, padx=(0,8))
        ttk.Button(actions, text="Create ZIP for Editor", command=self.create_zip).grid(row=0, column=1, padx=(0,8))
        ttk.Button(actions, text="Reset Form", command=self.reset_form).grid(row=0, column=2)

        # Status
        row += 1
        self.var_status = tk.StringVar(value="Ready.")
        ttk.Label(container, textvariable=self.var_status).grid(row=row, column=0, columnspan=4, sticky="w", pady=(8,0))

        # Resize weights
        for c in range(4):
            container.columnconfigure(c, weight=1 if c in (1,2) else 0)

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
            copied = copy_image_to_uploads(self.hero_image_path, uploads_dir, hero_base)
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
            copied = copy_image_to_uploads(add_path, uploads_dir, add_base)
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

        self.var_status.set(f"ZIP created: {zip_path}")
        messagebox.showinfo("ZIP ready", f"ZIP created at:\n{zip_path}\n\nSend this ZIP to the editor.")

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
        self.last_generated_paths = []
        self.var_status.set("Ready.")


def main():
    root = tk.Tk()
    # Better default minimum size
    root.minsize(800, 700)
    NewsGeneratorApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()

