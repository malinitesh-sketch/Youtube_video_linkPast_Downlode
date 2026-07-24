@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo YouTube Downloader Local App - Windows
 echo ==========================================

where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python is not installed or not added to PATH.
  echo Install Python from https://www.python.org/downloads/
  pause
  exit /b 1
)

if not exist .venv (
  echo Creating Python virtual environment...
  python -m venv .venv
)

call .venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing required packages...
pip install -r requirements.txt

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
python app.py
pause
