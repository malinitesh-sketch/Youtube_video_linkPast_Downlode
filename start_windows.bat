@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
echo ==========================================
echo YouTube Downloader Local App - Windows
echo ==========================================

:: Detect valid Python executable
set PYTHON=

py -3 --version >nul 2>&1
if !errorlevel! equ 0 (
    set PYTHON=py -3
    goto :PYTHON_FOUND
)

py --version >nul 2>&1
if !errorlevel! equ 0 (
    set PYTHON=py
    goto :PYTHON_FOUND
)

python -c "import sys; sys.exit(0)" >nul 2>&1
if !errorlevel! equ 0 (
    set PYTHON=python
    goto :PYTHON_FOUND
)

echo ERROR: Python is not installed or not working properly.
echo Install Python from https://www.python.org/downloads/
pause
exit /b 1

:PYTHON_FOUND
if not exist ".venv\Scripts\python.exe" (
  echo Creating Python virtual environment...
  !PYTHON! -m venv .venv
)

echo Upgrading pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip

echo Installing required packages...
".venv\Scripts\python.exe" -m pip install -r requirements.txt

where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo.
  echo WARNING: ffmpeg was not found.
  echo MP3, 1080p/2K/4K, and video+audio merge may fail.
  echo Install ffmpeg and add it to PATH.
  echo.
)

echo.
echo Starting server...
echo Open this link in your browser:
echo http://127.0.0.1:5000
echo.
".venv\Scripts\python.exe" app.py
pause
