@echo off
setlocal

set SCRIPT=%~dp0news_generator.py

rem Try Windows Python launcher first
where py >nul 2>&1
if %ERRORLEVEL%==0 (
  py -3 "%SCRIPT%"
  goto :eof
)

rem Fallback to python
where python >nul 2>&1
if %ERRORLEVEL%==0 (
  python "%SCRIPT%"
  goto :eof
)

rem Fallback to python3
where python3 >nul 2>&1
if %ERRORLEVEL%==0 (
  python3 "%SCRIPT%"
  goto :eof
)

echo.
echo Could not find Python 3. Please install it from https://www.python.org/downloads/ and try again.
pause

