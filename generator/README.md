### Sonce News Maker (Multiple Options)

This folder contains multiple tools for creating draft news files compatible with the website. Choose the option that works best for you:

## 🐍 Python GUI Generator (Advanced)

**File**: `news_generator.py`  
**Best for**: Users who prefer desktop applications with advanced features

### Features:
- Desktop GUI application with Tkinter
- Advanced image management and validation
- ZIP file creation and distribution
- Form validation and error handling
- Settings persistence
- Tooltips and help system

### Quick Start:
1. Double-click `run_mac_linux.sh` (Mac/Linux) or `run_windows.bat` (Windows)
2. Fill in the form and click "Generate Draft"
3. Click "Create ZIP" to package everything
4. Use "Copy ZIP to incoming…" to place it in your website folder

## 🌐 HTML Web Editor (Modern)

**File**: `html-editor/index.html`  
**Best for**: Users who prefer web-based tools with modern features

### Features:
- Beautiful web-based interface with sun-inspired design
- Live Markdown preview
- Drag & drop image handling
- Templates and version history
- Direct repository integration
- Auto-save and draft management
- Advanced export options

### Quick Start:
1. Open `html-editor/index.html` in your web browser
2. Fill in the form and use the Markdown toolbar
3. Click "Connect Repo Folder" to connect directly to your website
4. Click "Save to Repo" to save directly to your content folder

## 📋 What You Get

Both generators produce:
- A Markdown file with YAML frontmatter in `content/news/YYYY-MM-DD-slug.md` format
- Properly organized images in `static/uploads/news/YYYY/MM/` folders
- Compatible with the website's news system
- All drafts are clearly marked with `draft: true` in the front matter

## 🎯 Main Website Compatibility

Both tools generate content that works 100% with the main website:

### Required File Structure:
```
your-website/
├── content/
│   └── news/                    # News posts directory
│       ├── index.json           # Auto-generated index file
│       └── YYYY-MM-DD-slug.md   # Individual post files
├── static/
│   └── uploads/
│       └── news/                # News images directory
│           ├── YYYY/            # Year folders
│           │   └── MM/          # Month folders
│           │       └── YYYY-MM-DD-slug-hero.ext
```

### Frontmatter Fields (YAML):
```yaml
---
title: "Your Post Title"
date: 2024-01-15
author: "Author Name"
slug: "optional-custom-slug"
image: "/static/uploads/news/2024/01/2024-01-15-slug-hero.jpg"
imageAlt: "Alt text for accessibility"
summary: "Short excerpt shown on listing pages"
tags: [news, community, events]
draft: true
---
```

## 🚀 Upload Steps for Main Website

### Option 1: Direct Integration (HTML Editor)
1. Use the HTML editor's "Connect Repo Folder" feature
2. Select your website folder
3. Create and save your post directly
4. The editor handles everything automatically

### Option 2: ZIP Upload (Python Generator)
1. Generate your post using the Python GUI
2. Click "Create ZIP" to package everything
3. Use "Copy ZIP to incoming…" to place it in your website folder
4. Commit and push to GitHub - the site will import it automatically

### Option 3: Manual Upload
1. Generate your post using either tool
2. Download the Markdown file
3. Place it in `content/news/` with correct naming
4. Copy images to `static/uploads/news/YYYY/MM/` folders
5. Run the news build script to update the index

## 🔧 CLI Tool Usage

The HTML editor includes a CLI tool (`html-editor/tools/news-cli.mjs`) for automation:

### Create a new post:
```bash
node html-editor/tools/news-cli.mjs create \
  --title "Your Post Title" \
  --date 2024-01-15 \
  --author "Author Name" \
  --slug "optional-slug" \
  --image "/path/to/image.jpg" \
  --copy-image \
  --tags "news,community" \
  --summary "Short excerpt" \
  --body "Post content here"
```

### Rebuild the index:
```bash
node html-editor/tools/news-cli.mjs rebuild-index
```

## 📊 Auto-Generated Index

Both tools work with the system that automatically creates `content/news/index.json` with this structure:

```json
[
  {
    "id": "2024-01-15-slug",
    "title": "Post Title",
    "date": "2024-01-15",
    "author": "Author Name",
    "summary": "Post summary",
    "image": "/static/uploads/news/2024/01/image.jpg",
    "imageAlt": "Alt text",
    "tags": ["news", "community"],
    "slug": "slug",
    "filename": "2024-01-15-slug.md",
    "path": "/content/news/2024-01-15-slug.md",
    "link": "/content/news/2024-01-15-slug.md",
    "readingTimeMinutes": 3,
    "readingTimeLabel": "3 min"
  }
]
```

## 🎨 Design Features

### Python GUI:
- Clean, functional desktop interface
- Form-based input with validation
- Progress indicators and status messages
- Cross-platform compatibility

### HTML Editor:
- Warm color palette inspired by the sun
- Smooth animations and transitions
- Modern typography with proper hierarchy
- Accessibility features and keyboard navigation
- Responsive layout for all screen sizes

## 🔍 Troubleshooting

### Common Issues:

1. **Post not appearing**: Check filename format and run the index rebuild
2. **Images not loading**: Verify image paths and file permissions
3. **Frontmatter errors**: Ensure YAML syntax is correct
4. **Slug conflicts**: Use unique slugs or let auto-generation handle it

### Validation:
- Use the HTML editor's preview function to check rendering
- Validate YAML syntax in the frontmatter
- Check that all required fields are present
- Verify image paths are accessible

## 🛡️ Safety and Privacy

- **No sign-in or internet required** for either tool
- **The generators never commit, push, or publish anything** automatically
- **No deploy keys or credentials are included**
- **All data stays local** until you manually upload it

## 📱 Mobile Support

- **Python GUI**: Desktop application, not mobile-compatible
- **HTML Editor**: Fully responsive and works great on mobile devices

## 🤝 Contributing

Feel free to contribute improvements to either generator:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

Both generators are open source and available under the MIT License.

---

**Made for Sonce** — Choose the news generator that works best for your workflow! ☀️