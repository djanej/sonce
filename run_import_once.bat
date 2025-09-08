@echo off
setlocal

set SCRIPT=%~dp0tools\import_incoming_zip.py

where py >nul 2>&1
if %ERRORLEVEL%==0 (
  py -3 "%SCRIPT%"
  goto :eof
)

where python >nul 2>&1
if %ERRORLEVEL%==0 (
  python "%SCRIPT%"
  goto :eof
)

where python3 >nul 2>&1
if %ERRORLEVEL%==0 (
  python3 "%SCRIPT%"
  goto :eof
)

echo Python 3 is required to run the importer. Install from https://www.python.org/downloads/
pause

