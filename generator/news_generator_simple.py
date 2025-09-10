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
    from tkinter import ttk, filedialog, messagebox, font
except Exception as e:
    print("This tool requires Python with Tkinter installed.\n"
          "On Windows and macOS, Tkinter is included with the standard installer.\n"
          "On Linux, install the Tkinter package via your package manager (e.g., python3-tk).\n")
    raise


APP_TITLE = "Sonce News Maker (Simple)"
OUTPUT_ROOT = Path(__file__).parent / "output"
SETTINGS_FILE = Path(__file__).parent / "settings.json"
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


class SimpleNewsApp:
    def __init__(self, master: tk.Tk):
        self.master = master
        master.title(APP_TITLE)
        
        # Configure style
        self.setup_styles()
        
        # State
        self.hero_image_path: Optional[Path] = None
        self.last_zip_path: Optional[Path] = None
        self.settings = self.load_settings()
        self.is_creating = False  # Prevent double-clicks
        
        # Variables
        self.var_title = tk.StringVar()
        self.var_summary = tk.StringVar()
        self.var_author = tk.StringVar(value=self.settings.get('default_author', ''))
        self.var_body = tk.StringVar()
        
        # Build UI
        self.build_ui()
        
        # Set window size and center
        master.geometry("900x750")
        master.minsize(700, 600)
        self.center_window()
        
        # Auto-save timer
        self.auto_save_timer = None
        self.setup_auto_save()
        
        # Keyboard shortcuts
        self.setup_shortcuts()
        
    def setup_styles(self):
        """Configure modern, clean styles"""
        style = ttk.Style()
        
        # Use a more modern theme if available
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')
            
        # Configure colors
        bg_color = '#f5f5f5'
        primary_color = '#2196F3'
        success_color = '#4CAF50'
        danger_color = '#f44336'
        warning_color = '#FF9800'
        
        self.master.configure(bg=bg_color)
        
        # Configure button styles
        style.configure('Primary.TButton', 
                       font=('Arial', 11, 'bold'),
                       foreground='white',
                       background=primary_color)
        
        style.configure('Success.TButton',
                       font=('Arial', 11, 'bold'),
                       foreground='white',
                       background=success_color)
                       
        style.configure('Danger.TButton',
                       font=('Arial', 10),
                       foreground='white',
                       background=danger_color)
        
        style.configure('Warning.TButton',
                       font=('Arial', 10),
                       foreground='white',
                       background=warning_color)
        
        # Configure label styles
        style.configure('Heading.TLabel',
                       font=('Arial', 24, 'bold'),
                       background=bg_color)
                       
        style.configure('Step.TLabel',
                       font=('Arial', 14, 'bold'),
                       background=bg_color,
                       foreground=primary_color)
                       
        style.configure('Help.TLabel',
                       font=('Arial', 10),
                       background=bg_color,
                       foreground='#666')
        
        # Configure frame style
        style.configure('Card.TFrame',
                       background='white',
                       relief='solid',
                       borderwidth=1)
                       
    def build_ui(self):
        """Build the simplified UI"""
        # Main container with padding
        main_frame = tk.Frame(self.master, bg='#f5f5f5')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_frame, text="📰 Create News Article", style='Heading.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Create a canvas with scrollbar for the form
        canvas = tk.Canvas(main_frame, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mouse wheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Build form sections in scrollable frame
        self.build_step1(scrollable_frame)
        self.build_step2(scrollable_frame)
        self.build_step3(scrollable_frame)
        self.build_actions(scrollable_frame)
        
        # Status bar at bottom
        self.status_frame = tk.Frame(main_frame, bg='#e0e0e0', height=30)
        self.status_frame.pack(fill='x', pady=(10, 0))
        self.status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(self.status_frame, text="Ready to create news", 
                                     bg='#e0e0e0', fg='#333', font=('Arial', 10))
        self.status_label.pack(side='left', padx=10, pady=5)
        
        # Progress indicator (hidden by default)
        self.progress_label = tk.Label(self.status_frame, text="", 
                                      bg='#e0e0e0', fg='#666', font=('Arial', 10))
        self.progress_label.pack(side='right', padx=10, pady=5)
        
    def build_step1(self, parent):
        """Step 1: Basic Information"""
        # Card frame
        card = ttk.Frame(parent, style='Card.TFrame', padding=20)
        card.pack(fill='x', pady=(0, 15))
        
        # Step header
        step_label = ttk.Label(card, text="Step 1: Basic Information", style='Step.TLabel')
        step_label.pack(anchor='w', pady=(0, 15))
        
        # Title field with character counter
        title_frame = ttk.Frame(card)
        title_frame.pack(fill='x', pady=(0, 15))
        
        title_header_frame = ttk.Frame(title_frame)
        title_header_frame.pack(fill='x')
        
        ttk.Label(title_header_frame, text="📝 News Title:", font=('Arial', 11, 'bold')).pack(side='left')
        self.title_counter = ttk.Label(title_header_frame, text="0/100", 
                                      font=('Arial', 9), foreground='#666')
        self.title_counter.pack(side='right')
        
        ttk.Label(title_frame, text="Write a clear, attention-grabbing headline", 
                 style='Help.TLabel').pack(anchor='w')
        
        self.title_entry = ttk.Entry(title_frame, textvariable=self.var_title, 
                                     font=('Arial', 12), width=60)
        self.title_entry.pack(fill='x', pady=(5, 0))
        self.title_entry.bind('<KeyRelease>', self.update_title_counter)
        
        # Summary field with character counter
        summary_frame = ttk.Frame(card)
        summary_frame.pack(fill='x', pady=(0, 15))
        
        summary_header_frame = ttk.Frame(summary_frame)
        summary_header_frame.pack(fill='x')
        
        ttk.Label(summary_header_frame, text="📄 Short Summary:", font=('Arial', 11, 'bold')).pack(side='left')
        self.summary_counter = ttk.Label(summary_header_frame, text="0/200", 
                                        font=('Arial', 9), foreground='#666')
        self.summary_counter.pack(side='right')
        
        ttk.Label(summary_frame, text="One or two sentences describing the news", 
                 style='Help.TLabel').pack(anchor='w')
        
        self.summary_text = tk.Text(summary_frame, height=3, font=('Arial', 11), 
                                   wrap='word', relief='solid', borderwidth=1)
        self.summary_text.pack(fill='x', pady=(5, 0))
        self.summary_text.bind('<KeyRelease>', self.update_summary_counter)
        
        # Author field (optional)
        author_frame = ttk.Frame(card)
        author_frame.pack(fill='x')
        
        ttk.Label(author_frame, text="✍️ Author (optional):", font=('Arial', 11, 'bold')).pack(anchor='w')
        
        self.author_entry = ttk.Entry(author_frame, textvariable=self.var_author, 
                                      font=('Arial', 11), width=30)
        self.author_entry.pack(anchor='w', pady=(5, 0))
        
    def build_step2(self, parent):
        """Step 2: Add Image"""
        # Card frame
        card = ttk.Frame(parent, style='Card.TFrame', padding=20)
        card.pack(fill='x', pady=(0, 15))
        
        # Step header
        step_label = ttk.Label(card, text="Step 2: Add Main Image (Optional)", style='Step.TLabel')
        step_label.pack(anchor='w', pady=(0, 15))
        
        # Image selection
        image_frame = ttk.Frame(card)
        image_frame.pack(fill='x')
        
        ttk.Label(image_frame, text="🖼️ Choose an image that represents your news:", 
                 font=('Arial', 11)).pack(anchor='w', pady=(0, 10))
        
        # Image info and button frame
        img_button_frame = ttk.Frame(image_frame)
        img_button_frame.pack(fill='x')
        
        self.image_label = ttk.Label(img_button_frame, text="No image selected", 
                                     font=('Arial', 10, 'italic'), foreground='#666')
        self.image_label.pack(side='left', padx=(0, 15))
        
        ttk.Button(img_button_frame, text="Choose Image", 
                  command=self.choose_image).pack(side='left')
        
        ttk.Button(img_button_frame, text="Remove", 
                  command=self.remove_image).pack(side='left', padx=(10, 0))
        
        # Image preview (hidden by default)
        self.image_preview_frame = ttk.Frame(image_frame)
        self.image_preview_frame.pack(fill='x', pady=(10, 0))
        
    def build_step3(self, parent):
        """Step 3: Full Article"""
        # Card frame
        card = ttk.Frame(parent, style='Card.TFrame', padding=20)
        card.pack(fill='x', pady=(0, 15))
        
        # Step header
        step_label = ttk.Label(card, text="Step 3: Full Article (Optional)", style='Step.TLabel')
        step_label.pack(anchor='w', pady=(0, 15))
        
        # Body text with word counter
        body_frame = ttk.Frame(card)
        body_frame.pack(fill='x')
        
        body_header_frame = ttk.Frame(body_frame)
        body_header_frame.pack(fill='x')
        
        ttk.Label(body_header_frame, text="📰 Write your full article here:", 
                 font=('Arial', 11)).pack(side='left')
        self.word_counter = ttk.Label(body_header_frame, text="0 words", 
                                     font=('Arial', 9), foreground='#666')
        self.word_counter.pack(side='right')
        
        ttk.Label(body_frame, text="You can leave this empty if you only want to create a news summary", 
                 style='Help.TLabel').pack(anchor='w', pady=(0, 5))
        
        self.body_text = tk.Text(body_frame, height=10, font=('Arial', 11), 
                                wrap='word', relief='solid', borderwidth=1)
        self.body_text.pack(fill='both', expand=True)
        self.body_text.bind('<KeyRelease>', self.update_word_counter)
        
    def build_actions(self, parent):
        """Action buttons"""
        # Card frame for actions
        card = ttk.Frame(parent, style='Card.TFrame', padding=20)
        card.pack(fill='x', pady=(0, 15))
        
        # Main actions frame
        actions_frame = ttk.Frame(card)
        actions_frame.pack()
        
        # Create ZIP button (primary action)
        self.create_btn = tk.Button(actions_frame, text="🎯 Create News ZIP", 
                                   command=self.create_news_zip,
                                   font=('Arial', 14, 'bold'),
                                   bg='#4CAF50', fg='white',
                                   padx=30, pady=15,
                                   relief='raised', bd=2)
        self.create_btn.pack(pady=(0, 15))
        
        # Help text
        ttk.Label(card, text="Click the button above to create a ZIP file ready for upload", 
                 style='Help.TLabel').pack()
        
        # Secondary actions
        secondary_frame = ttk.Frame(card)
        secondary_frame.pack(pady=(15, 0))
        
        ttk.Button(secondary_frame, text="📁 Open Output Folder", 
                  command=self.open_output_folder).pack(side='left', padx=5)
        ttk.Button(secondary_frame, text="📤 Copy ZIP to incoming…", 
                  command=self.copy_zip_to_incoming).pack(side='left', padx=5)
        
        ttk.Button(secondary_frame, text="🔄 Clear Form", 
                  command=self.reset_form).pack(side='left', padx=5)
        
        ttk.Button(secondary_frame, text="💾 Load Draft", 
                  command=self.load_draft_manual).pack(side='left', padx=5)
        
        ttk.Button(secondary_frame, text="❓ Help", 
                  command=self.show_help).pack(side='left', padx=5)
        
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.master.bind('<Control-s>', lambda e: self.save_draft())
        self.master.bind('<Control-n>', lambda e: self.reset_form())
        self.master.bind('<Control-o>', lambda e: self.load_draft_manual())
        self.master.bind('<Control-Return>', lambda e: self.create_news_zip())
        
    def update_title_counter(self, event=None):
        """Update title character counter"""
        length = len(self.var_title.get())
        color = '#666' if length <= 100 else '#f44336'
        self.title_counter.config(text=f"{length}/100", foreground=color)
        
    def update_summary_counter(self, event=None):
        """Update summary character counter"""
        text = self.summary_text.get("1.0", tk.END).strip()
        length = len(text)
        color = '#666' if length <= 200 else '#f44336'
        self.summary_counter.config(text=f"{length}/200", foreground=color)
        
    def update_word_counter(self, event=None):
        """Update word counter for body text"""
        text = self.body_text.get("1.0", tk.END).strip()
        words = len(text.split()) if text else 0
        self.word_counter.config(text=f"{words} words")
        
    def choose_image(self):
        """Select hero image with validation"""
        path = filedialog.askopenfilename(
            title="Choose main image for your news",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.gif *.webp *.svg"),
                ("All files", "*.*")
            ]
        )
        if path:
            image_path = Path(path)
            valid, error = validate_image(image_path)
            
            if not valid:
                messagebox.showwarning("Invalid Image", f"Cannot use this image:\n{error}")
                return
                
            self.hero_image_path = image_path
            size_mb = get_file_size_mb(image_path)
            self.image_label.config(text=f"✅ {image_path.name} ({size_mb:.1f}MB)")
            self.update_status("Image selected")
            
    def remove_image(self):
        """Remove selected image"""
        self.hero_image_path = None
        self.image_label.config(text="No image selected")
        self.update_status("Image removed")
        
    def create_news_zip(self):
        """Create news and ZIP in one step with progress feedback"""
        if self.is_creating:
            return
            
        # Validate inputs
        title = self.var_title.get().strip()
        if not title:
            messagebox.showwarning("Missing Title", "Please enter a news title.")
            self.title_entry.focus()
            return
            
        if len(title) > 100:
            messagebox.showwarning("Title Too Long", "Title should be less than 100 characters.")
            self.title_entry.focus()
            return
            
        summary = self.summary_text.get("1.0", tk.END).strip()
        if not summary:
            messagebox.showwarning("Missing Summary", "Please enter a short summary.")
            self.summary_text.focus()
            return
            
        if len(summary) > 200:
            if not messagebox.askyesno("Long Summary", 
                                       "Summary is longer than 200 characters. It will be truncated. Continue?"):
                return
        
        self.is_creating = True
        self.create_btn.config(state='disabled', text='Creating...')
        self.progress_label.config(text="Preparing files...")
        self.master.update()
        
        try:
            # Collect data
            date_str = today_date_str()
            dt_iso = now_iso_local()
            author = self.var_author.get().strip()
            slug = to_slug(title)
            
            if not slug:
                raise ValueError("Could not generate valid slug from title")
            
            body = self.body_text.get("1.0", tk.END).strip()
            
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
            
            # Track generated files
            written_paths = []
            
            # Copy image if selected
            image_url = ""
            if self.hero_image_path:
                self.progress_label.config(text="Processing image...")
                self.master.update()
                
                hero_base = f"{date_str}-{slug}-hero"
                hero_base = sanitize_filename(hero_base)
                copied = copy_image_to_uploads(self.hero_image_path, uploads_dir, hero_base)
                image_url = "/" + "/".join(copied.relative_to(OUTPUT_ROOT).parts)
                image_url = image_url.replace("\\", "/")
                written_paths.append(copied)
                
            # Build frontmatter
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
                # Limit to 200 chars
                short = summary[:200].rstrip()
                fm_lines.append(f"summary: {yaml_escape(short)}")
                
            if image_url:
                fm_lines.append(f"image: {yaml_escape(image_url)}")
                fm_lines.append(f"imageAlt: {yaml_escape(title)}")
                
            # Always mark as draft for safety
            fm_lines.append("draft: true")
            fm_lines.append(f"datetime: {yaml_escape(dt_iso)}")
            fm_lines.append("---")
            
            # Markdown content
            if not body:
                body = summary  # Use summary as body if no full article
                
            content = "\n".join(fm_lines) + "\n\n" + body + "\n"
            
            # Write markdown file
            filename = sanitize_filename(f"{date_str}-{slug}.md")
            md_path = content_dir / filename
            md_path.write_text(content, encoding='utf-8')
            written_paths.append(md_path)
            
            # Create ZIP
            self.progress_label.config(text="Creating ZIP file...")
            self.master.update()
            
            zip_name = sanitize_filename(f"news-draft-{date_str}-{slug}.zip")
            zip_path = OUTPUT_ROOT / zip_name
            
            with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                for path in written_paths:
                    if path.is_file():
                        rel_path = path.relative_to(OUTPUT_ROOT)
                        zf.write(path, arcname=str(rel_path))
                        
            self.last_zip_path = zip_path
            
            # Clear progress and show success
            self.progress_label.config(text="")
            self.update_status(f"✅ ZIP created: {zip_name}")
            
            # Clear draft file since we successfully created the news
            draft_file = OUTPUT_ROOT / "draft.json"
            if draft_file.exists():
                try:
                    draft_file.unlink()
                except:
                    pass
            
            result = messagebox.askyesno(
                "Success! 🎉",
                f"News ZIP created successfully!\n\n"
                f"File: {zip_name}\n\n"
                f"Would you like to open the output folder now?\n\n"
                f"Upload this ZIP file to your news website to publish."
            )
            
            if result:
                self.open_output_folder()
                
        except Exception as e:
            self.progress_label.config(text="")
            error_msg = f"Failed to create news ZIP:\n{str(e)}"
            if sys.platform == 'win32' and 'Permission denied' in str(e):
                error_msg += "\n\nTip: Close any programs that might be using the output folder."
            messagebox.showerror("Error", error_msg)
            traceback.print_exc()
            
        finally:
            self.is_creating = False
            self.create_btn.config(state='normal', text='🎯 Create News ZIP')
            
    def open_output_folder(self):
        """Open the output folder"""
        ensure_dir(OUTPUT_ROOT)
        try:
            if sys.platform == 'win32':
                os.startfile(str(OUTPUT_ROOT))
            elif sys.platform == 'darwin':
                subprocess.run(['open', str(OUTPUT_ROOT)], check=False)
            else:
                subprocess.run(['xdg-open', str(OUTPUT_ROOT)], check=False)
        except Exception as e:
            messagebox.showinfo("Output Folder", f"Your files are in:\n{OUTPUT_ROOT}")
            
    def copy_zip_to_incoming(self):
        """Copy the last created ZIP into a chosen website incoming/ folder"""
        if not self.last_zip_path or not self.last_zip_path.exists():
            candidates = sorted(OUTPUT_ROOT.glob('news-draft-*.zip'), key=lambda p: p.stat().st_mtime, reverse=True)
            if candidates:
                self.last_zip_path = candidates[0]
            else:
                messagebox.showwarning("No ZIP found", "Please click 'Create News ZIP' first.")
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
            self.update_status(f"Copied ZIP to: {dest.name}")
            messagebox.showinfo("Copied", f"ZIP copied to:\n{dest.name}\n\nCommit and push this to GitHub (main). The site will import it automatically.")
        except Exception as e:
            messagebox.showerror("Copy failed", f"Could not copy to incoming/:\n{e}")
            
    def reset_form(self):
        """Clear all form fields"""
        if self.has_unsaved_changes():
            if not messagebox.askyesno("Clear Form", 
                                       "You have unsaved changes. Clear anyway?\n\n"
                                       "Tip: Press Ctrl+S to save as draft first."):
                return
                
        self.var_title.set("")
        self.summary_text.delete("1.0", tk.END)
        self.body_text.delete("1.0", tk.END)
        self.hero_image_path = None
        self.image_label.config(text="No image selected")
        self.update_status("Form cleared")
        
        # Update counters
        self.update_title_counter()
        self.update_summary_counter()
        self.update_word_counter()
        
    def show_help(self):
        """Show help dialog"""
        help_text = """
How to Create News:

1️⃣ Enter a catchy title for your news article
   • Keep it under 100 characters
   • Make it attention-grabbing

2️⃣ Write a short summary (1-2 sentences)
   • Maximum 200 characters
   • This appears in news listings

3️⃣ Optionally add a main image
   • Supported: JPG, PNG, GIF, WebP, SVG
   • Maximum size: 10MB

4️⃣ Optionally write the full article
   • No length limit
   • Can use basic formatting

5️⃣ Click "Create News ZIP" or press Ctrl+Enter

6️⃣ Upload the ZIP file to your website

Keyboard Shortcuts:
• Ctrl+S - Save draft
• Ctrl+N - New/Clear form
• Ctrl+O - Load draft
• Ctrl+Enter - Create ZIP

Tips:
• Keep titles short and clear
• Summaries should grab attention
• Images make news more engaging
• Drafts are auto-saved every 30 seconds
        """
        
        messagebox.showinfo("Help - How to Use", help_text)
        
    def update_status(self, message):
        """Update status bar"""
        self.status_label.config(text=message)
        self.master.update()
        
    def center_window(self):
        """Center window on screen"""
        self.master.update_idletasks()
        width = self.master.winfo_width()
        height = self.master.winfo_height()
        x = (self.master.winfo_screenwidth() // 2) - (width // 2)
        y = (self.master.winfo_screenheight() // 2) - (height // 2)
        self.master.geometry(f'{width}x{height}+{x}+{y}')
        
    def has_unsaved_changes(self):
        """Check if there are unsaved changes"""
        return (self.var_title.get().strip() or 
                self.summary_text.get("1.0", tk.END).strip() or
                self.body_text.get("1.0", tk.END).strip() or
                self.hero_image_path is not None)
                
    def setup_auto_save(self):
        """Setup auto-save functionality"""
        def auto_save():
            if self.has_unsaved_changes():
                self.save_draft(silent=True)
            self.auto_save_timer = self.master.after(30000, auto_save)  # Every 30 seconds
            
        self.auto_save_timer = self.master.after(30000, auto_save)
        
    def save_draft(self, silent=False):
        """Save current form as draft"""
        draft_file = OUTPUT_ROOT / "draft.json"
        ensure_dir(OUTPUT_ROOT)
        
        draft_data = {
            'title': self.var_title.get(),
            'summary': self.summary_text.get("1.0", tk.END).strip(),
            'author': self.var_author.get(),
            'body': self.body_text.get("1.0", tk.END).strip(),
            'image': str(self.hero_image_path) if self.hero_image_path else None,
            'saved_at': now_iso_local()
        }
        
        try:
            with open(draft_file, 'w', encoding='utf-8') as f:
                json.dump(draft_data, f, indent=2, ensure_ascii=False)
            if not silent:
                self.update_status("✅ Draft saved")
        except Exception as e:
            if not silent:
                messagebox.showerror("Save Error", f"Could not save draft:\n{str(e)}")
            
    def load_draft(self):
        """Load saved draft if exists (called on startup)"""
        draft_file = OUTPUT_ROOT / "draft.json"
        if draft_file.exists():
            try:
                with open(draft_file, 'r', encoding='utf-8') as f:
                    draft_data = json.load(f)
                    
                if messagebox.askyesno("Restore Draft", 
                                       "Found a saved draft. Would you like to restore it?"):
                    self.var_title.set(draft_data.get('title', ''))
                    
                    summary = draft_data.get('summary', '')
                    if summary:
                        self.summary_text.insert("1.0", summary)
                    
                    self.var_author.set(draft_data.get('author', ''))
                    
                    body = draft_data.get('body', '')
                    if body:
                        self.body_text.insert("1.0", body)
                    
                    if draft_data.get('image'):
                        img_path = Path(draft_data['image'])
                        if img_path.exists():
                            self.hero_image_path = img_path
                            size_mb = get_file_size_mb(img_path)
                            self.image_label.config(text=f"✅ {img_path.name} ({size_mb:.1f}MB)")
                            
                    self.update_status("Draft restored")
                    
                    # Update counters
                    self.update_title_counter()
                    self.update_summary_counter()
                    self.update_word_counter()
                    
            except Exception as e:
                print(f"Could not load draft: {e}")
                
    def load_draft_manual(self):
        """Manually load a draft"""
        draft_file = OUTPUT_ROOT / "draft.json"
        if not draft_file.exists():
            messagebox.showinfo("No Draft", "No saved draft found.")
            return
            
        if self.has_unsaved_changes():
            if not messagebox.askyesno("Load Draft", 
                                       "You have unsaved changes. Load draft anyway?"):
                return
        
        # Clear form first
        self.var_title.set("")
        self.summary_text.delete("1.0", tk.END)
        self.body_text.delete("1.0", tk.END)
        self.hero_image_path = None
        self.image_label.config(text="No image selected")
        
        try:
            with open(draft_file, 'r', encoding='utf-8') as f:
                draft_data = json.load(f)
                
            self.var_title.set(draft_data.get('title', ''))
            
            summary = draft_data.get('summary', '')
            if summary:
                self.summary_text.insert("1.0", summary)
            
            self.var_author.set(draft_data.get('author', ''))
            
            body = draft_data.get('body', '')
            if body:
                self.body_text.insert("1.0", body)
            
            if draft_data.get('image'):
                img_path = Path(draft_data['image'])
                if img_path.exists():
                    self.hero_image_path = img_path
                    size_mb = get_file_size_mb(img_path)
                    self.image_label.config(text=f"✅ {img_path.name} ({size_mb:.1f}MB)")
                    
            self.update_status("Draft loaded")
            
            # Update counters
            self.update_title_counter()
            self.update_summary_counter()
            self.update_word_counter()
            
        except Exception as e:
            messagebox.showerror("Load Error", f"Could not load draft:\n{str(e)}")
                
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
    app = SimpleNewsApp(root)
    
    # Load any saved draft on startup
    app.load_draft()
    
    # Handle window close
    def on_closing():
        if app.has_unsaved_changes():
            result = messagebox.askyesnocancel("Save Draft", 
                                               "Would you like to save your work as a draft?")
            if result is None:  # Cancel
                return
            elif result:  # Yes
                app.save_draft()
                
        if app.auto_save_timer:
            root.after_cancel(app.auto_save_timer)
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == '__main__':
    main()