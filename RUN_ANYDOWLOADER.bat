@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title AnyDownloader - YouTube Downloader

echo ==========================================
echo    🚀 AnyDownloader - YouTube Downloader
echo    Paste a link, download instantly!
echo ==========================================
echo.

:: Detect valid Python executable (prefer Windows Python Launcher 'py', avoid broken WindowsApps alias)
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
echo Please download and install Python from: https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation.
start https://www.python.org/downloads/
pause
exit /b 1

:PYTHON_FOUND
echo [1/3] Found Python launcher: !PYTHON!

:: Create virtual environment if it does not exist
if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creating Python virtual environment...
    !PYTHON! -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Install / update requirements using virtual environment's python directly
echo [2/3] Checking dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip -q
".venv\Scripts\python.exe" -m pip install -r requirements.txt -q

:: Check ffmpeg
where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo.
    echo ⚠ WARNING: ffmpeg not found. MP3/4K/1080p may fail.
    echo Install it from: https://ffmpeg.org/download.html
    echo.
)

:: Launch backend using virtual environment python
echo [3/3] Starting server...
echo.
echo ==========================================
echo    ✓ Server is starting...
echo    📺 Your browser will open automatically
echo    🌐 http://127.0.0.1:5000
echo ==========================================
echo.

".venv\Scripts\python.exe" app.py

pause


