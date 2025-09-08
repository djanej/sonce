@echo off
setlocal

echo Watching incoming\ for ZIP files. Close this window to stop.
:loop
call "%~dp0run_import_once.bat"
timeout /t 5 >nul
goto loop

