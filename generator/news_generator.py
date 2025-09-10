#!/usr/bin/env python3

import os
import re
import sys
import json
import zipfile
import shutil
import unicodedata
import subprocess
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except Exception as e:
    print("This tool requires Python with Tkinter installed.\n"
          "On Windows and macOS, Tkinter is included with the standard installer.\n"
          "On Linux, install the Tkinter package via your package manager (e.g., python3-tk).\n")
    raise


APP_TITLE = "Sonce News Maker (Advanced)"
OUTPUT_ROOT = Path(__file__).parent / "output"
SETTINGS_FILE = Path(__file__).parent / "settings_advanced.json"
MAX_IMAGE_SIZE_MB = 10  # Maximum image size in MB
SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}


def to_slug(value: str) -> str:
    """Convert text to URL-safe slug."""
    text = str(value or "").strip().lower()
    # Remove diacritics
    text = unicodedata.normalize('NFD', text)
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
    # Replace non-alphanumeric with hyphens
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"(^-|-$)", "", text)
    return text


def today_date_str() -> str:
    """Get today's date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")


def now_iso_local() -> str:
    """Get current datetime in ISO format with timezone."""
    return datetime.now().astimezone().isoformat(timespec='seconds')


def ensure_dir(path: Path) -> None:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


def get_file_size_mb(path: Path) -> float:
    """Get file size in megabytes."""
    return path.stat().st_size / (1024 * 1024)


def validate_image(path: Path) -> tuple[bool, str]:
    """Validate image file."""
    if not path.exists():
        return False, "File does not exist"
    
    if path.suffix.lower() not in SUPPORTED_IMAGE_FORMATS:
        return False, f"Unsupported format. Supported: {', '.join(SUPPORTED_IMAGE_FORMATS)}"
    
    size_mb = get_file_size_mb(path)
    if size_mb > MAX_IMAGE_SIZE_MB:
        return False, f"File too large ({size_mb:.1f}MB). Maximum: {MAX_IMAGE_SIZE_MB}MB"
    
    return True, ""


def copy_image_to_uploads(src_path: Path, dest_dir: Path, dest_filename: str) -> Path:
    """Copy image to uploads directory with unique name."""
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
    """Escape text for YAML frontmatter."""
    if text is None:
        return ""
    s = str(text)
    # Quote if contains special characters
    if re.search(r'[":>#\[\],{}|]', s) or s.strip() != s or '\n' in s:
        # escape quotes and backslashes
        s = s.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{s}"'
    return s


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations."""
    # Remove path separators and other dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove control characters
    filename = ''.join(ch for ch in filename if ord(ch) >= 32)
    return filename[:255]  # Limit length


class _Tooltip:
    """Tooltip widget for help text."""
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tipwindow: Optional[tk.Toplevel] = None
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
        self.hero_image_path: Optional[Path] = None
        self.additional_images: List[Path] = []
        self.last_generated_paths: List[Path] = []
        self.last_zip_path: Optional[Path] = None
        self.settings = self.load_settings()
        self.is_generating = False

        # Variables
        self.var_title = tk.StringVar()
        self.var_date = tk.StringVar(value=today_date_str())
        self.var_datetime = tk.StringVar(value=now_iso_local())
        self.var_author = tk.StringVar(value=self.settings.get('default_author', ''))
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
        ttk.Label(container, text="Title (headline)*").grid(row=row, column=0, sticky="w")
        e_title = ttk.Entry(container, textvariable=self.var_title, width=60)
        e_title.grid(row=row, column=1, columnspan=3, sticky="ew", padx=(8,0))
        e_title.bind("<KeyRelease>", self._on_title_change)
        self._add_tooltip(e_title, "Write the big headline for your news.")
        row += 1

        ttk.Label(container, text="Date (YYYY-MM-DD)*").grid(row=row, column=0, sticky="w")
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

        ttk.Label(container, text="Web address name (slug)*").grid(row=row, column=0, sticky="w")
        entry_slug = ttk.Entry(container, textvariable=self.var_slug, width=40)
        entry_slug.grid(row=row, column=1, sticky="w", padx=(8,0))
        self._add_tooltip(entry_slug, "Short web-friendly name. Letters, numbers, and dashes only.")
        ttk.Button(container, text="Regenerate", command=self._regen_slug).grid(row=row, column=2, sticky="w", padx=(8,0))
        row += 1

        ttk.Label(container, text="Summary (1-2 sentences)*").grid(row=row, column=0, sticky="nw")
        self.txt_summary = tk.Text(container, width=60, height=4)
        self.txt_summary.grid(row=row, column=1, columnspan=3, sticky="ew", padx=(8,0))
        self._add_tooltip(self.txt_summary, "A short preview. Keep it simple—one or two sentences.")
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
        self.lbl_hero.grid(row=row, column=1, columnspan=2, sticky="w", padx=(8,0))
        ttk.Button(container, text="Choose…", command=self.choose_hero).grid(row=row, column=3, sticky="w")
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
        row += 1

        # Body content (optional)
        ttk.Label(container, text="Body (optional)").grid(row=row, column=0, sticky="nw")
        self.txt_body = tk.Text(container, width=60, height=12)
        self.txt_body.grid(row=row, column=1, columnspan=3, sticky="ew", padx=(8,0))
        self._add_tooltip(self.txt_body, "The full text of your news. You can leave it empty.")
        row += 1

        # Actions
        actions = ttk.Frame(container)
        actions.grid(row=row, column=0, columnspan=4, sticky="ew", pady=(8,0))
        self.btn_gen = ttk.Button(actions, text="Generate Draft", command=self.generate_draft)
        self.btn_gen.grid(row=0, column=0, padx=(0,8))
        self._add_tooltip(self.btn_gen, "Create the files on your computer (no publishing).")

        self.btn_zip = ttk.Button(actions, text="Create ZIP", command=self.create_zip)
        self.btn_zip.grid(row=0, column=1, padx=(0,8))
        self._add_tooltip(self.btn_zip, "Packs the draft and images into one ZIP.")

        ttk.Button(actions, text="Open Output Folder", command=self.open_output_folder).grid(row=0, column=2, padx=(0,8))
        ttk.Button(actions, text="Copy ZIP to incoming…", command=self.copy_zip_to_incoming).grid(row=0, column=3, padx=(0,8))
        ttk.Button(actions, text="Reset Form", command=self.reset_form).grid(row=0, column=4, padx=(0,8))
        ttk.Button(actions, text="How it works", command=self.show_help).grid(row=0, column=5)

        # Status
        row += 1
        self.var_status = tk.StringVar(value="Ready.")
        self.status_label = ttk.Label(container, textvariable=self.var_status)
        self.status_label.grid(row=row, column=0, columnspan=4, sticky="w", pady=(8,0))
        
        # Progress label
        self.progress_label = ttk.Label(container, text="", foreground='#666')
        self.progress_label.grid(row=row, column=4, sticky="e", pady=(8,0))

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
                                          filetypes=[("Images", "*.jpg *.jpeg *.png *.gif *.webp *.svg"), ("All files", "*.*")])
        if path:
            image_path = Path(path)
            valid, error = validate_image(image_path)
            
            if not valid:
                messagebox.showwarning("Invalid Image", f"Cannot use this image:\n{error}")
                return
                
            self.hero_image_path = image_path
            size_mb = get_file_size_mb(image_path)
            self.lbl_hero.config(text=f"{image_path.name} ({size_mb:.1f}MB)")

    def add_images(self):
        paths = filedialog.askopenfilenames(title="Choose additional images",
                                            filetypes=[("Images", "*.jpg *.jpeg *.png *.gif *.webp *.svg"), ("All files", "*.*")])
        for p in paths:
            pth = Path(p)
            valid, error = validate_image(pth)
            
            if not valid:
                messagebox.showwarning("Invalid Image", f"Cannot add {pth.name}:\n{error}")
                continue
                
            if pth not in self.additional_images:
                self.additional_images.append(pth)
                size_mb = get_file_size_mb(pth)
                self.lst_images.insert(tk.END, f"{pth.name} ({size_mb:.1f}MB)")

    def remove_selected_image(self):
        sel = list(self.lst_images.curselection())
        sel.reverse()
        for idx in sel:
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
        summary = self.txt_summary.get("1.0", tk.END).strip()
        if not summary:
            return False, "Summary is required."
        return True, ""

    def generate_draft(self):
        if self.is_generating:
            return
            
        ok, msg = self._validate_inputs()
        if not ok:
            messagebox.showerror("Invalid input", msg)
            return

        self.is_generating = True
        self.btn_gen.config(state='disabled')
        self.progress_label.config(text="Generating draft...")
        self.master.update()

        try:
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

            # Save author preference
            if author:
                self.settings['default_author'] = author
                self.save_settings()

            year, month = date_str.split('-')[0], date_str.split('-')[1]

            # Prepare output dirs
            self.progress_label.config(text="Creating directories...")
            self.master.update()
            
            content_dir = OUTPUT_ROOT / "content" / "news"
            uploads_dir = OUTPUT_ROOT / "static" / "uploads" / "news" / year / month
            ensure_dir(content_dir)
            ensure_dir(uploads_dir)

            # Copy images
            image_url = ""
            written_paths: list[Path] = []
            if self.hero_image_path:
                self.progress_label.config(text="Processing hero image...")
                self.master.update()
                
                hero_base = sanitize_filename(f"{date_str}-{slug}-hero")
                copied = copy_image_to_uploads(self.hero_image_path, uploads_dir, hero_base)
                # Compute absolute web path
                image_url = "/" + "/".join(copied.relative_to(OUTPUT_ROOT).parts)
                image_url = image_url.replace("\\", "/")
                written_paths.append(copied)

            # Additional images
            for i, add_path in enumerate(self.additional_images):
                self.progress_label.config(text=f"Processing image {i+1}/{len(self.additional_images)}...")
                self.master.update()
                
                base_name = add_path.stem
                desc = to_slug(base_name)
                if not desc or desc == "hero":
                    desc = f"image-{i+1}"
                add_base = sanitize_filename(f"{date_str}-{slug}-{desc}")
                copied = copy_image_to_uploads(add_path, uploads_dir, add_base)
                written_paths.append(copied)

            # Build frontmatter (compatible with site spec; date as YYYY-MM-DD)
            self.progress_label.config(text="Creating content...")
            self.master.update()
            
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
            filename = sanitize_filename(f"{date_str}-{slug}.md")
            md_path = content_dir / filename
            md_path.write_text(content, encoding='utf-8')
            written_paths.append(md_path)

            # Save last generated set (relative to OUTPUT_ROOT)
            rel_written = [p.relative_to(OUTPUT_ROOT) for p in written_paths]
            self.last_generated_paths = rel_written

            self.progress_label.config(text="")
            self.var_status.set(f"Draft generated: {md_path.name}")
            messagebox.showinfo("Success", f"Draft created at:\n{md_path.name}\n\nImages (if any) were copied under:\n{uploads_dir}")
            
        except Exception as e:
            self.progress_label.config(text="")
            messagebox.showerror("Error", f"Failed to generate draft:\n{str(e)}")
            traceback.print_exc()
            
        finally:
            self.is_generating = False
            self.btn_gen.config(state='normal')

    def create_zip(self):
        if not self.last_generated_paths:
            messagebox.showwarning("Nothing to zip", "Generate a draft first.")
            return

        self.progress_label.config(text="Creating ZIP file...")
        self.master.update()

        try:
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
            zip_name = sanitize_filename(f"news-draft-{slug_part}.zip")
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
            self.progress_label.config(text="")
            self.var_status.set(f"ZIP created: {zip_name}")
            messagebox.showinfo("ZIP ready", f"ZIP created at:\n{zip_name}\n\nYou can now copy it into your website folder's incoming/ directory.")
            
        except Exception as e:
            self.progress_label.config(text="")
            messagebox.showerror("Error", f"Failed to create ZIP:\n{str(e)}")

    def open_output_folder(self):
        ensure_dir(OUTPUT_ROOT)
        try:
            if sys.platform == 'win32':
                os.startfile(str(OUTPUT_ROOT))
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
        selected = filedialog.askdirectory(title="Select your website folder (or incoming)")
        if not selected:
            return
        target = Path(selected)
        incoming_dir = target if target.name.lower() == 'incoming' else (target / 'incoming')
        try:
            incoming_dir.mkdir(parents=True, exist_ok=True)
            dest = incoming_dir / self.last_zip_path.name
            shutil.copy2(self.last_zip_path, dest)
            self.var_status.set(f"Copied ZIP to: {dest.name}")
            messagebox.showinfo("Copied", f"ZIP copied to:\n{dest.name}\n\nCommit and push this to GitHub (main). The site will import it automatically.")
        except Exception as e:
            messagebox.showerror("Copy failed", f"Could not copy to incoming/:\n{e}")

    def show_help(self):
        steps = (
            "1) Title: Write the headline.\n"
            "2) Date: Click Today (or choose the publication date).\n"
            "3) Summary: Write 1-2 sentences describing the news.\n"
            "4) Optional: Choose a hero image and write a short description.\n"
            "5) Click Generate Draft.\n"
            "6) Click Create ZIP.\n"
            "7) Click Copy ZIP to incoming… and pick your website folder.\n\n"
            "After you push to GitHub (main), the site automatically places files in the right folders.\n\n"
            "Keyboard shortcuts:\n"
            "• Ctrl+S - Save draft\n"
            "• Ctrl+N - Reset form"
        )
        messagebox.showinfo("How it works", steps)

    def _add_tooltip(self, widget, text: str):
        tip = _Tooltip(widget, text)
        return tip

    def reset_form(self):
        if self.has_unsaved_changes():
            if not messagebox.askyesno("Reset Form", "You have unsaved changes. Reset anyway?"):
                return
                
        self.var_title.set("")
        self.var_date.set(today_date_str())
        self.var_datetime.set(now_iso_local())
        self.var_author.set(self.settings.get('default_author', ''))
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

    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes"""
        return (self.var_title.get().strip() or
                self.txt_summary.get("1.0", tk.END).strip() or
                self.txt_body.get("1.0", tk.END).strip() or
                self.hero_image_path is not None or
                len(self.additional_images) > 0)

    def load_settings(self) -> Dict[str, Any]:
        """Load saved settings"""
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_settings(self):
        """Save settings"""
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception:
            pass


def main():
    root = tk.Tk()
    # Better default minimum size
    root.minsize(800, 700)
    NewsGeneratorApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()