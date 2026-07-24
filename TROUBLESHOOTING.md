# Troubleshooting: API Not Connecting / Video Not Downloading

## 1. Do NOT open `index.html` directly

This will NOT work:

```text
file:///.../public/index.html
```

The website must be opened through the Python backend:

```text
http://127.0.0.1:5000
```

If you open the HTML file directly, `/api/info` and `/api/download` cannot connect.

## 2. Easiest start

### Windows

Double-click:

```text
start_windows.bat
```

Or run in Command Prompt:

```bat
cd youtube-downloader-app
start_windows.bat
```

### macOS / Linux

```bash
cd youtube-downloader-app
chmod +x start_mac_linux.sh
./start_mac_linux.sh
```

## 3. If browser says API not working

Make sure the terminal is still running and shows something like:

```text
Running on http://127.0.0.1:5000
```

Then open exactly:

```text
http://127.0.0.1:5000
```

## 4. If install fails

Try:

```bash
python -m pip install --upgrade pip
pip install Flask yt-dlp requests
```

On some systems use `python3` instead of `python`.

## 5. If MP3 / 1080p / 4K fails

Install `ffmpeg`.

- Windows: install ffmpeg and add `bin` folder to PATH
- macOS: `brew install ffmpeg`
- Ubuntu/Debian: `sudo apt install ffmpeg`

Check:

```bash
ffmpeg -version
```

## 6. If YouTube extraction fails

Update yt-dlp:

```bash
pip install -U yt-dlp
```

Then restart:

```bash
python app.py
```

## 7. Common errors

### `ModuleNotFoundError: No module named flask`

You did not install requirements. Run:

```bash
pip install -r requirements.txt
```

### `Address already in use` / port 5000 busy

Close the old server terminal, or change port in `app.py`.

### `ffmpeg not found`

Install ffmpeg. Without ffmpeg, some formats cannot be merged/converted.

## 8. Legal note

Use only for your own videos, videos with permission, or content legally allowed to download.
