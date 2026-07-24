@echo off
setlocal
cd /d "%~dp0"
title AnyDownloader - YouTube Downloader

echo ==========================================
echo    🚀 AnyDownloader - YouTube Downloader
echo    Paste a link, download instantly!
echo ==========================================
echo.

:: Check Python
where python >nul 2>nul
if errorlevel 1 (
    where py >nul 2>nul
    if errorlevel 1 (
        echo ERROR: Python is not installed.
        start https://www.python.org/downloads/
        pause
        exit /b 1
    )
    set PYTHON=py
) else (
    set PYTHON=python
)

:: Create virtual environment if not exists
if not exist ".venv\" (
    echo [1/3] Creating virtual environment...
    %PYTHON% -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Activate and install requirements
echo [2/3] Installing dependencies...
call .venv\Scripts\activate.bat
%PYTHON% -m pip install --upgrade pip -q
pip install -r requirements.txt -q

:: Check ffmpeg
where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo.
    echo ⚠ WARNING: ffmpeg not found. MP3/4K/1080p may fail.
    echo Install it from: https://ffmpeg.org/download.html
    echo.
)

:: Launch
echo [3/3] Starting server...
echo.
echo ==========================================
echo    ✓ Server is starting...
echo    📺 Your browser will open automatically
echo    🌐 http://127.0.0.1:5000
echo ==========================================
echo.
python app.py

pause

