#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "=========================================="
echo "YouTube Downloader Local App - macOS/Linux"
echo "=========================================="

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is not installed."
  exit 1
fi

if [ ! -d .venv ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "Upgrading pip..."
python -m pip install --upgrade pip

echo "Installing required packages..."
pip install -r requirements.txt

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo ""
  echo "WARNING: ffmpeg was not found."
  echo "MP3, 1080p/2K/4K, and video+audio merge may fail."
  echo "Install ffmpeg: macOS 'brew install ffmpeg' or Ubuntu 'sudo apt install ffmpeg'"
  echo ""
fi

echo ""
echo "Starting server..."
echo "Open this link in your browser:"
echo "http://127.0.0.1:5000"
echo ""
python app.py
