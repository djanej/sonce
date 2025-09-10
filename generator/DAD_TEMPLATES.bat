@echo off
color 0B
cls

echo.
echo  ====================================
echo    DAD'S NEWS MAKER WITH TEMPLATES
echo  ====================================
echo.

set SCRIPT=%~dp0news_maker_dad_plus.py

rem Try to run with Python
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

echo.
echo  ERROR: Python is not installed!
echo.
echo  Please install Python first:
echo  1. Go to https://www.python.org/downloads/
echo  2. Download Python
echo  3. Install it (check "Add to PATH")
echo  4. Try again
echo.
pause