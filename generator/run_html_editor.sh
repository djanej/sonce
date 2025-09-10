#!/bin/bash

# Sonce News Editor (HTML) Launcher
# Opens the HTML-based news editor in the default web browser

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EDITOR_DIR="$SCRIPT_DIR/html-editor"
INDEX_FILE="$EDITOR_DIR/index.html"

echo "☀️  Sonce News Editor (HTML)"
echo "================================"
echo ""

# Check if the HTML editor exists
if [ ! -f "$INDEX_FILE" ]; then
    echo "❌ Error: HTML editor not found at $INDEX_FILE"
    echo "   Please ensure the html-editor folder is present."
    exit 1
fi

echo "📁 Editor location: $EDITOR_DIR"
echo "🌐 Opening in browser..."
echo ""

# Try to open in the default browser
if command -v xdg-open >/dev/null 2>&1; then
    # Linux
    xdg-open "$INDEX_FILE"
elif command -v open >/dev/null 2>&1; then
    # macOS
    open "$INDEX_FILE"
elif command -v start >/dev/null 2>&1; then
    # Windows (Git Bash)
    start "$INDEX_FILE"
else
    echo "❌ Could not automatically open browser."
    echo "   Please manually open: $INDEX_FILE"
    exit 1
fi

echo "✅ HTML editor should now be open in your browser!"
echo ""
echo "💡 Tips:"
echo "   • Use 'Connect Repo Folder' to save directly to your website"
echo "   • Use 'Download Markdown' to save files manually"
echo "   • Check the README.md for detailed instructions"
echo ""
echo "🔗 Alternative: You can also open the file directly:"
echo "   file://$INDEX_FILE"