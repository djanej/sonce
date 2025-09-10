@echo off
REM Sonce News Editor (HTML) Launcher for Windows
REM Opens the HTML-based news editor in the default web browser

setlocal

echo ☀️  Sonce News Editor (HTML)
echo ================================
echo.

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
set "EDITOR_DIR=%SCRIPT_DIR%html-editor"
set "INDEX_FILE=%EDITOR_DIR%\index.html"

REM Check if the HTML editor exists
if not exist "%INDEX_FILE%" (
    echo ❌ Error: HTML editor not found at %INDEX_FILE%
    echo    Please ensure the html-editor folder is present.
    pause
    exit /b 1
)

echo 📁 Editor location: %EDITOR_DIR%
echo 🌐 Opening in browser...
echo.

REM Open in the default browser
start "" "%INDEX_FILE%"

echo ✅ HTML editor should now be open in your browser!
echo.
echo 💡 Tips:
echo    • Use 'Connect Repo Folder' to save directly to your website
echo    • Use 'Download Markdown' to save files manually
echo    • Check the README.md for detailed instructions
echo.
echo 🔗 Alternative: You can also open the file directly:
echo    file:///%INDEX_FILE%
echo.
pause