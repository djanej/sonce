# 🛠️ Sonce Development Tools

This directory contains **development tools and generators** for creating content for the Sonce website.

## ⚠️ Important: These Are NOT Part of the Website

These tools are **standalone utilities** that run on your local computer to help you create news posts and other content. They are **NOT part of the live website** - they generate files that the website then displays.

## 📁 What's Here

```
generator/
├── html-editor/          # 🌐 Web-based news editor
├── news_generator.py     # 🐍 Desktop news generator  
├── examples/             # 📝 Sample content
├── scripts/              # 🔧 Build tools
└── README.md            # 📖 Documentation
```

## 🚀 Quick Start

### Python GUI Generator (Desktop App)
```bash
./run_mac_linux.sh    # Mac/Linux
run_windows.bat       # Windows
```

### HTML Web Editor (Browser App)
```bash
./run_html_editor.sh  # Mac/Linux
run_html_editor.bat  # Windows
```

## 🎯 What These Tools Do

They create **Markdown files with YAML frontmatter** in the format your website expects:

- **News posts**: `content/news/YYYY-MM-DD-slug.md`
- **Images**: `static/uploads/news/YYYY/MM/`
- **Index updates**: `content/news/index.json`

## 🔒 Safety & Privacy

- ✅ **100% local** - runs on your computer only
- ✅ **No internet required** - works offline
- ✅ **No tracking** - completely private
- ✅ **Safe to modify** - changes don't affect the website

## 📚 Documentation

- **`README.md`** - Complete guide to both generators
- **`CHOOSE_GENERATOR.md`** - Comparison of tools
- **`html-editor/README.md`** - HTML editor details

## 🤝 Contributing

These tools are open source! Feel free to improve them:

1. Make your changes
2. Test with `python3 test_integration.py`
3. Submit a pull request

---

**Remember**: These are **content creation tools**, not the website itself! They help you write posts that the website displays. 🛠️