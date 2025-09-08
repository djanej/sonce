@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0.."
python "news-generator\generator.py" --interactive --bundle-zip --verify --auto-index | type
pause