#!/bin/bash

cd "$(dirname "$0")"

show_gui_error() {
  local message="$1"
  if command -v zenity >/dev/null 2>&1; then
    zenity --error --title="Sonce News Maker - Easy Mode" --width=480 --text="$message" || true
  elif command -v kdialog >/dev/null 2>&1; then
    kdialog --error "$message" || true
  elif command -v xmessage >/dev/null 2>&1; then
    xmessage -center "$message" || true
  else
    printf "%s\n" "$message" >&2
  fi
}

SCRIPT="news_generator_simple.py"

# Pick Python interpreter
PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  show_gui_error "Python 3 is required.\n\nInstall it and try again.\n\nExamples:\n• Ubuntu/Debian: sudo apt-get install python3 python3-tk\n• Fedora: sudo dnf install python3 python3-tkinter\n• Arch: sudo pacman -S python tk"
  exit 1
fi

# Verify Tkinter
if ! "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
import sys
try:
    import tkinter  # noqa: F401
except Exception:
    sys.exit(2)
sys.exit(0)
PY
then
  show_gui_error "Tkinter (python3-tk) is missing for Python 3.\n\nInstall it and try again.\n\nExamples:\n• Ubuntu/Debian: sudo apt-get install python3-tk\n• Fedora: sudo dnf install python3-tkinter\n• Arch: sudo pacman -S tk"
  exit 1
fi

exec "$PYTHON_BIN" "$SCRIPT"
