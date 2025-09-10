#!/bin/bash

clear

echo ""
echo "  ===================================="
echo "    DAD'S NEWS MAKER - STARTING..."
echo "  ===================================="
echo ""

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCRIPT="$DIR/news_maker_dad.py"

# Try to run with Python
if command -v python3 &> /dev/null; then
    python3 "$SCRIPT"
elif command -v python &> /dev/null; then
    python "$SCRIPT"
else
    echo ""
    echo "  ERROR: Python is not installed!"
    echo ""
    echo "  Please install Python first:"
    echo "  1. Go to https://www.python.org/downloads/"
    echo "  2. Download Python for Mac"
    echo "  3. Install it"
    echo "  4. Try again"
    echo ""
    read -p "Press Enter to close..."
fi