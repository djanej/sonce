#!/usr/bin/env python3
"""
Ultra Simple News Maker for Dad
Just fill in 2 fields and click one button!
"""

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
    from tkinter import ttk, filedialog, messagebox
except Exception:
    print("Python with Tkinter is required. Please install it.")
    sys.exit(1)


OUTPUT_ROOT = Path(__file__).parent / "output"


def to_slug(text):
    """Convert text to URL-friendly slug"""
    text = str(text or "").strip().lower()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"(^-|-$)", "", text)
    return text


def yaml_escape(text):
    """Escape text for YAML"""
    if not text:
        return ""
    s = str(text)
    if re.search(r'[":#\[\],]', s) or s.strip() != s:
        s = s.replace('"', '\\"')
        return f'"{s}"'
    return s


class UltraSimpleNewsApp:
    def __init__(self, root):
        self.root = root
        root.title("📰 Dad's News Maker")
        root.configure(bg='#f0f8ff')
        
        # Window setup
        root.geometry("700x600")
        root.minsize(600, 500)
        self.center_window()
        
        # Variables
        self.image_path = None
        
        # Build UI
        self.build_ui()
        
    def build_ui(self):
        """Build the ultra-simple UI"""
        # Main container
        main = tk.Frame(self.root, bg='#f0f8ff', padx=40, pady=30)
        main.pack(fill='both', expand=True)
        
        # Big title
        title = tk.Label(main, text="📰 Create News in 3 Steps!", 
                        font=('Arial', 26, 'bold'),
                        bg='#f0f8ff', fg='#2c3e50')
        title.pack(pady=(0, 30))
        
        # Step 1: Title
        step1_frame = self.create_step_frame(main, "1️⃣ What's the news?")
        
        self.title_entry = tk.Entry(step1_frame, font=('Arial', 14), width=50)
        self.title_entry.pack(fill='x', pady=(5, 0))
        self.title_entry.insert(0, "")
        
        # Placeholder text
        self.title_entry.bind('<FocusIn>', lambda e: self.clear_placeholder(self.title_entry, "Enter your news title here..."))
        self.title_entry.bind('<FocusOut>', lambda e: self.add_placeholder(self.title_entry, "Enter your news title here..."))
        self.add_placeholder(self.title_entry, "Enter your news title here...")
        
        # Step 2: Description
        step2_frame = self.create_step_frame(main, "2️⃣ Tell me more (2-3 sentences)")
        
        self.desc_text = tk.Text(step2_frame, font=('Arial', 12), height=4, 
                                wrap='word', relief='solid', bd=1)
        self.desc_text.pack(fill='x', pady=(5, 0))
        
        # Step 3: Image (optional)
        step3_frame = self.create_step_frame(main, "3️⃣ Add a picture (optional)")
        
        img_btn_frame = tk.Frame(step3_frame, bg='white')
        img_btn_frame.pack(fill='x', pady=(5, 0))
        
        self.img_button = tk.Button(img_btn_frame, text="📷 Choose Picture", 
                                   font=('Arial', 12),
                                   command=self.choose_image,
                                   bg='#3498db', fg='white',
                                   padx=15, pady=8)
        self.img_button.pack(side='left')
        
        self.img_label = tk.Label(img_btn_frame, text="No picture selected",
                                 font=('Arial', 11), bg='white', fg='#7f8c8d')
        self.img_label.pack(side='left', padx=(15, 0))
        
        # Big Create button
        tk.Frame(main, height=30, bg='#f0f8ff').pack()  # Spacer
        
        self.create_button = tk.Button(main, 
                                      text="✨ Create News ZIP File ✨",
                                      font=('Arial', 18, 'bold'),
                                      command=self.create_news,
                                      bg='#27ae60', fg='white',
                                      padx=40, pady=20,
                                      relief='raised', bd=3,
                                      cursor='hand2')
        self.create_button.pack()
        
        # Help text
        help_text = tk.Label(main, 
                           text="Click the green button to create your news file!",
                           font=('Arial', 10),
                           bg='#f0f8ff', fg='#7f8c8d')
        help_text.pack(pady=(10, 0))
        
        # Footer buttons
        footer = tk.Frame(main, bg='#f0f8ff')
        footer.pack(side='bottom', pady=(20, 0))
        
        tk.Button(footer, text="📁 See Files", command=self.open_folder,
                 font=('Arial', 10), bg='#95a5a6', fg='white',
                 padx=10, pady=5).pack(side='left', padx=5)
        
        tk.Button(footer, text="🔄 Start Over", command=self.reset,
                 font=('Arial', 10), bg='#95a5a6', fg='white',
                 padx=10, pady=5).pack(side='left', padx=5)
        
        tk.Button(footer, text="❓ Help", command=self.show_help,
                 font=('Arial', 10), bg='#95a5a6', fg='white',
                 padx=10, pady=5).pack(side='left', padx=5)
        
    def create_step_frame(self, parent, title):
        """Create a step frame with title"""
        frame = tk.Frame(parent, bg='white', relief='solid', bd=1)
        frame.pack(fill='x', pady=(0, 20), padx=10)
        
        inner = tk.Frame(frame, bg='white', padx=20, pady=15)
        inner.pack(fill='x')
        
        label = tk.Label(inner, text=title, font=('Arial', 14, 'bold'),
                        bg='white', fg='#2c3e50')
        label.pack(anchor='w')
        
        return inner
        
    def clear_placeholder(self, widget, placeholder):
        """Clear placeholder text"""
        if widget.get() == placeholder:
            widget.delete(0, 'end')
            widget.config(fg='black')
            
    def add_placeholder(self, widget, placeholder):
        """Add placeholder text"""
        if not widget.get():
            widget.insert(0, placeholder)
            widget.config(fg='#999')
            
    def choose_image(self):
        """Choose an image file"""
        path = filedialog.askopenfilename(
            title="Choose a picture for your news",
            filetypes=[
                ("Pictures", "*.jpg *.jpeg *.png *.gif"),
                ("All files", "*.*")
            ]
        )
        if path:
            self.image_path = Path(path)
            self.img_label.config(text=f"✅ {self.image_path.name}", fg='#27ae60')
            
    def create_news(self):
        """Create the news ZIP file"""
        # Get values
        title = self.title_entry.get().strip()
        if title == "Enter your news title here...":
            title = ""
            
        description = self.desc_text.get("1.0", tk.END).strip()
        
        # Validate
        if not title:
            messagebox.showwarning("Oops!", "Please enter a news title first! 😊")
            self.title_entry.focus()
            return
            
        if not description:
            messagebox.showwarning("Oops!", "Please write a short description! 😊")
            self.desc_text.focus()
            return
            
        # Create the news
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            slug = to_slug(title)
            year, month = date_str.split('-')[0], date_str.split('-')[1]
            
            # Prepare directories
            content_dir = OUTPUT_ROOT / "content" / "news"
            content_dir.mkdir(parents=True, exist_ok=True)
            
            written_files = []
            
            # Handle image
            image_url = ""
            if self.image_path and self.image_path.exists():
                uploads_dir = OUTPUT_ROOT / "static" / "uploads" / "news" / year / month
                uploads_dir.mkdir(parents=True, exist_ok=True)
                
                ext = self.image_path.suffix.lower()
                img_name = f"{date_str}-{slug}-hero{ext}"
                img_dest = uploads_dir / img_name
                
                shutil.copy2(self.image_path, img_dest)
                written_files.append(img_dest)
                
                image_url = "/" + "/".join(img_dest.relative_to(OUTPUT_ROOT).parts)
                image_url = image_url.replace("\\", "/")
                
            # Create markdown content
            frontmatter = [
                "---",
                f"title: {yaml_escape(title)}",
                f"date: {date_str}",
                f"slug: {yaml_escape(slug)}",
                f"summary: {yaml_escape(description[:200])}",
            ]
            
            if image_url:
                frontmatter.append(f"image: {yaml_escape(image_url)}")
                frontmatter.append(f"imageAlt: {yaml_escape(title)}")
                
            frontmatter.extend([
                "draft: true",
                f"datetime: {datetime.now().astimezone().isoformat()}",
                "---"
            ])
            
            content = "\n".join(frontmatter) + "\n\n" + description + "\n"
            
            # Write markdown file
            md_filename = f"{date_str}-{slug}.md"
            md_path = content_dir / md_filename
            md_path.write_text(content, encoding='utf-8')
            written_files.append(md_path)
            
            # Create ZIP
            zip_name = f"news-{date_str}-{slug}.zip"
            zip_path = OUTPUT_ROOT / zip_name
            
            OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                for file_path in written_files:
                    if file_path.is_file():
                        rel_path = file_path.relative_to(OUTPUT_ROOT)
                        zf.write(file_path, arcname=str(rel_path))
                        
            # Success!
            self.show_success(zip_name)
            
        except Exception as e:
            messagebox.showerror("Error", f"Something went wrong:\n{str(e)}")
            
    def show_success(self, filename):
        """Show success message"""
        msg = f"""
🎉 Great job! Your news is ready!

Created: {filename}

What to do next:
1. Click "See Files" below
2. Find the ZIP file: {filename}
3. Upload it to your website

Your news has been saved and is ready to share!
        """
        
        result = messagebox.showinfo("Success!", msg)
        self.open_folder()
        
    def open_folder(self):
        """Open the output folder"""
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        
        try:
            if sys.platform == 'win32':
                os.startfile(str(OUTPUT_ROOT))
            elif sys.platform == 'darwin':
                subprocess.run(['open', str(OUTPUT_ROOT)], check=False)
            else:
                subprocess.run(['xdg-open', str(OUTPUT_ROOT)], check=False)
        except Exception:
            messagebox.showinfo("Output Folder", 
                              f"Your files are saved in:\n{OUTPUT_ROOT}")
            
    def reset(self):
        """Reset the form"""
        self.title_entry.delete(0, 'end')
        self.add_placeholder(self.title_entry, "Enter your news title here...")
        self.desc_text.delete("1.0", tk.END)
        self.image_path = None
        self.img_label.config(text="No picture selected", fg='#7f8c8d')
        
    def show_help(self):
        """Show help"""
        help_msg = """
How to use Dad's News Maker:

1️⃣ Type your news title
   Example: "Community Picnic This Saturday"

2️⃣ Write 2-3 sentences about it
   Example: "Join us for a fun picnic in the park.
   Bring your family and friends!"

3️⃣ Add a picture (optional)
   Click "Choose Picture" to add a photo

4️⃣ Click the big green button!

That's it! Your news ZIP file will be created.
Upload it to the website to share with everyone.

Need help? Call me! 😊
        """
        messagebox.showinfo("Help for Dad", help_msg)
        
    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')


def main():
    root = tk.Tk()
    app = UltraSimpleNewsApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()