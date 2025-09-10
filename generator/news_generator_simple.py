#!/usr/bin/env python3

import os
import re
import sys
import json
import zipfile
import shutil
import unicodedata
import subprocess
from datetime import datetime
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, font
except Exception as e:
    print("This tool requires Python with Tkinter installed.\n"
          "On Windows and macOS, Tkinter is included with the standard installer.\n"
          "On Linux, install the Tkinter package via your package manager (e.g., python3-tk).\n")
    raise


APP_TITLE = "Sonce News Maker - Easy Mode"
OUTPUT_ROOT = Path(__file__).parent / "output"
SETTINGS_FILE = Path(__file__).parent / "settings.json"


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


class SimpleNewsApp:
    def __init__(self, master: tk.Tk):
        self.master = master
        master.title(APP_TITLE)
        
        # Configure style
        self.setup_styles()
        
        # State
        self.hero_image_path: Path | None = None
        self.last_zip_path: Path | None = None
        self.settings = self.load_settings()
        
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
        
    def build_step1(self, parent):
        """Step 1: Basic Information"""
        # Card frame
        card = ttk.Frame(parent, style='Card.TFrame', padding=20)
        card.pack(fill='x', pady=(0, 15))
        
        # Step header
        step_label = ttk.Label(card, text="Step 1: Basic Information", style='Step.TLabel')
        step_label.pack(anchor='w', pady=(0, 15))
        
        # Title field
        title_frame = ttk.Frame(card)
        title_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(title_frame, text="📝 News Title:", font=('Arial', 11, 'bold')).pack(anchor='w')
        ttk.Label(title_frame, text="Write a clear, attention-grabbing headline", 
                 style='Help.TLabel').pack(anchor='w')
        
        self.title_entry = ttk.Entry(title_frame, textvariable=self.var_title, 
                                     font=('Arial', 12), width=60)
        self.title_entry.pack(fill='x', pady=(5, 0))
        
        # Summary field
        summary_frame = ttk.Frame(card)
        summary_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(summary_frame, text="📄 Short Summary:", font=('Arial', 11, 'bold')).pack(anchor='w')
        ttk.Label(summary_frame, text="One or two sentences describing the news", 
                 style='Help.TLabel').pack(anchor='w')
        
        self.summary_text = tk.Text(summary_frame, height=3, font=('Arial', 11), 
                                   wrap='word', relief='solid', borderwidth=1)
        self.summary_text.pack(fill='x', pady=(5, 0))
        
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
        
    def build_step3(self, parent):
        """Step 3: Full Article"""
        # Card frame
        card = ttk.Frame(parent, style='Card.TFrame', padding=20)
        card.pack(fill='x', pady=(0, 15))
        
        # Step header
        step_label = ttk.Label(card, text="Step 3: Full Article (Optional)", style='Step.TLabel')
        step_label.pack(anchor='w', pady=(0, 15))
        
        # Body text
        body_frame = ttk.Frame(card)
        body_frame.pack(fill='x')
        
        ttk.Label(body_frame, text="📰 Write your full article here:", 
                 font=('Arial', 11)).pack(anchor='w', pady=(0, 5))
        ttk.Label(body_frame, text="You can leave this empty if you only want to create a news summary", 
                 style='Help.TLabel').pack(anchor='w', pady=(0, 5))
        
        self.body_text = tk.Text(body_frame, height=10, font=('Arial', 11), 
                                wrap='word', relief='solid', borderwidth=1)
        self.body_text.pack(fill='both', expand=True)
        
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
        
        ttk.Button(secondary_frame, text="🔄 Clear Form", 
                  command=self.reset_form).pack(side='left', padx=5)
        
        ttk.Button(secondary_frame, text="❓ Help", 
                  command=self.show_help).pack(side='left', padx=5)
        
    def choose_image(self):
        """Select hero image"""
        path = filedialog.askopenfilename(
            title="Choose main image for your news",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.gif *.webp *.svg"),
                ("All files", "*.*")
            ]
        )
        if path:
            self.hero_image_path = Path(path)
            self.image_label.config(text=f"✅ {self.hero_image_path.name}")
            self.update_status("Image selected")
            
    def remove_image(self):
        """Remove selected image"""
        self.hero_image_path = None
        self.image_label.config(text="No image selected")
        self.update_status("Image removed")
        
    def create_news_zip(self):
        """Create news and ZIP in one step"""
        # Validate inputs
        title = self.var_title.get().strip()
        if not title:
            messagebox.showwarning("Missing Title", "Please enter a news title.")
            self.title_entry.focus()
            return
            
        summary = self.summary_text.get("1.0", tk.END).strip()
        if not summary:
            messagebox.showwarning("Missing Summary", "Please enter a short summary.")
            self.summary_text.focus()
            return
            
        # Collect data
        date_str = today_date_str()
        dt_iso = now_iso_local()
        author = self.var_author.get().strip()
        slug = to_slug(title)
        body = self.body_text.get("1.0", tk.END).strip()
        
        # Save author preference
        if author:
            self.settings['default_author'] = author
            self.save_settings()
        
        year, month = date_str.split('-')[0], date_str.split('-')[1]
        
        # Prepare output dirs
        content_dir = OUTPUT_ROOT / "content" / "news"
        uploads_dir = OUTPUT_ROOT / "static" / "uploads" / "news" / year / month
        ensure_dir(content_dir)
        ensure_dir(uploads_dir)
        
        # Track generated files
        written_paths = []
        
        # Copy image if selected
        image_url = ""
        if self.hero_image_path:
            hero_base = f"{date_str}-{slug}-hero"
            copied = copy_image_to_uploads(self.hero_image_path, uploads_dir, hero_base)
            image_url = "/" + "/".join(copied.relative_to(OUTPUT_ROOT).parts)
            image_url = image_url.replace("\\", "/")
            written_paths.append(copied)
            
        # Build frontmatter
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
        filename = f"{date_str}-{slug}.md"
        md_path = content_dir / filename
        md_path.write_text(content, encoding='utf-8')
        written_paths.append(md_path)
        
        # Create ZIP immediately
        zip_name = f"news-{date_str}-{slug}.zip"
        zip_path = OUTPUT_ROOT / zip_name
        
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            for path in written_paths:
                if path.is_file():
                    rel_path = path.relative_to(OUTPUT_ROOT)
                    zf.write(path, arcname=str(rel_path))
                    
        self.last_zip_path = zip_path
        
        # Show success with clear instructions
        self.update_status(f"✅ ZIP created: {zip_name}")
        
        result = messagebox.askyesno(
            "Success! 🎉",
            f"News ZIP created successfully!\n\n"
            f"File: {zip_name}\n\n"
            f"Would you like to open the output folder now?\n\n"
            f"Upload this ZIP file to your news website to publish."
        )
        
        if result:
            self.open_output_folder()
            
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
            
    def reset_form(self):
        """Clear all form fields"""
        if self.has_unsaved_changes():
            if not messagebox.askyesno("Clear Form", "You have unsaved changes. Clear anyway?"):
                return
                
        self.var_title.set("")
        self.summary_text.delete("1.0", tk.END)
        self.body_text.delete("1.0", tk.END)
        self.hero_image_path = None
        self.image_label.config(text="No image selected")
        self.update_status("Form cleared")
        
    def show_help(self):
        """Show help dialog"""
        help_text = """
How to Create News:

1️⃣ Enter a catchy title for your news article

2️⃣ Write a short summary (1-2 sentences)

3️⃣ Optionally add a main image

4️⃣ Optionally write the full article

5️⃣ Click "Create News ZIP"

6️⃣ Upload the ZIP file to your website

That's it! The news will be created as a draft
and can be reviewed before publishing.

Tips:
• Keep titles short and clear
• Summaries should grab attention
• Images make news more engaging
• You can save just a summary without full text
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
                self.save_draft()
            self.auto_save_timer = self.master.after(30000, auto_save)  # Every 30 seconds
            
        self.auto_save_timer = self.master.after(30000, auto_save)
        
    def save_draft(self):
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
            self.update_status("Draft auto-saved")
        except Exception:
            pass  # Silent fail for auto-save
            
    def load_draft(self):
        """Load saved draft if exists"""
        draft_file = OUTPUT_ROOT / "draft.json"
        if draft_file.exists():
            try:
                with open(draft_file, 'r', encoding='utf-8') as f:
                    draft_data = json.load(f)
                    
                if messagebox.askyesno("Restore Draft", "Found a saved draft. Would you like to restore it?"):
                    self.var_title.set(draft_data.get('title', ''))
                    self.summary_text.insert("1.0", draft_data.get('summary', ''))
                    self.var_author.set(draft_data.get('author', ''))
                    self.body_text.insert("1.0", draft_data.get('body', ''))
                    
                    if draft_data.get('image'):
                        img_path = Path(draft_data['image'])
                        if img_path.exists():
                            self.hero_image_path = img_path
                            self.image_label.config(text=f"✅ {img_path.name}")
                            
                    self.update_status("Draft restored")
            except Exception:
                pass  # Silent fail
                
    def load_settings(self):
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
                json.dump(self.settings, f, indent=2)
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
            if messagebox.askyesno("Save Draft", "Would you like to save your work as a draft?"):
                app.save_draft()
        if app.auto_save_timer:
            root.after_cancel(app.auto_save_timer)
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == '__main__':
    main()