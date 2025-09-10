# 🛠️ Development Tools & Generators

This directory contains **development tools and generators** for creating content for the Sonce website. These are **NOT part of the website itself** - they are standalone tools that help you create news posts and other content.

## 📁 Directory Structure

```
generator/
├── html-editor/          # 🌐 HTML-based news editor (web tool)
├── news_generator.py     # 🐍 Python GUI news generator (desktop app)
├── examples/             # 📝 Example news posts
├── scripts/              # 🔧 Build and packaging scripts
└── README.md            # 📖 This file
```

## 🎯 What These Tools Do

These generators create **Markdown files with YAML frontmatter** that are compatible with the main website's news system. They generate files in the correct format and structure that the website expects.

### Output Format:
- **Files**: `content/news/YYYY-MM-DD-slug.md`
- **Images**: `static/uploads/news/YYYY/MM/YYYY-MM-DD-slug-hero.ext`
- **Index**: Updates `content/news/index.json`

## 🚀 Quick Start

### Option 1: Python GUI Generator
```bash
# Desktop application with advanced features
./run_mac_linux.sh    # Mac/Linux
run_windows.bat       # Windows
```

### Option 2: HTML Web Editor
```bash
# Web-based editor with modern features
./run_html_editor.sh  # Mac/Linux
run_html_editor.bat  # Windows
```

## 🔗 How It Works

1. **Use a generator** to create your news post
2. **Generate the Markdown file** with proper frontmatter
3. **Place the file** in `content/news/` (or use direct integration)
4. **The website automatically** picks up and displays the new post

## ⚠️ Important Notes

- **These are development tools** - not part of the live website
- **They run locally** on your computer
- **No internet required** - everything works offline
- **Safe to modify** - changes here don't affect the website
- **Version controlled** - you can commit changes to these tools

## 🛡️ Safety & Privacy

- **100% local** - no data sent to external servers
- **No tracking** - no analytics or monitoring
- **Open source** - transparent and auditable code
- **No credentials** - no API keys or passwords stored

## 📚 Documentation

- **`README.md`** - Complete documentation for both generators
- **`CHOOSE_GENERATOR.md`** - Detailed comparison guide
- **`html-editor/README.md`** - HTML editor specific documentation
- **`examples/`** - Sample news posts and templates

## 🔧 For Developers

If you want to modify or extend these tools:

1. **Python Generator**: Modify `news_generator.py`
2. **HTML Editor**: Modify files in `html-editor/`
3. **Build Scripts**: Check `scripts/` directory
4. **Test Integration**: Run `python3 test_integration.py`

## 🤝 Contributing

Feel free to improve these tools:

1. Fork the repository
2. Make your changes
3. Test with `python3 test_integration.py`
4. Submit a pull request

---

**Remember**: These are **content creation tools**, not part of the website itself! They help you create content that the website will display. 🛠️