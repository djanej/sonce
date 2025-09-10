#!/bin/bash

echo "Starting Easy News Maker..."
echo ""

SCRIPT="$(dirname "$0")/news_generator_simple.py"

# Try python3 first
if command -v python3 &> /dev/null; then
    python3 "$SCRIPT"
# Try python
elif command -v python &> /dev/null; then
    python "$SCRIPT"
else
    echo "Error: Python 3 is not installed."
    echo "Please install Python 3 and try again."
    echo ""
    echo "On macOS: Download from https://www.python.org/downloads/"
    echo "On Ubuntu/Debian: sudo apt-get install python3 python3-tk"
    echo "On Fedora: sudo dnf install python3 python3-tkinter"
    echo "On Arch: sudo pacman -S python tk"
    exit 1
fi