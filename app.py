import os
import re
import shutil
import tempfile
import threading
import time
import uuid
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import requests
from flask import Flask, after_this_request, jsonify, request, send_file, send_from_directory
from yt_dlp import YoutubeDL

BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__, static_folder=str(PUBLIC_DIR), static_url_path="")

# In-memory jobs. For big production use Redis/Celery/RQ instead.
JOBS = {}
JOBS_LOCK = threading.Lock()


def set_job(job_id, **kwargs):
    with JOBS_LOCK:
        job = JOBS.setdefault(job_id, {})
        job.update(kwargs)
        job["updated_at"] = time.time()


def get_job(job_id):
    with JOBS_LOCK:
        return dict(JOBS.get(job_id, {}))


def is_allowed_url(url: str) -> bool:
    """Allow common YouTube URL hosts only."""
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower().replace("www.", "")
        return parsed.scheme in {"http", "https"} and host in {
            "youtube.com",
            "m.youtube.com",
            "music.youtube.com",
            "youtu.be",
        }
    except Exception:
        return False


def clean_title(name: str) -> str:
    name = re.sub(r"[\\/:*?\"<>|]+", "-", name or "download")
    name = re.sub(r"\s+", " ", name).strip()
    return name[:90] or "download"


def _yt_cookies_path() -> str | None:
    """Return path to cookies.txt ONLY if it has actual Netscape-format cookie data.
    Empty cookie files or JSON files cause yt-dlp errors, so we skip them entirely."""
    txt_path = BASE_DIR / "cookies.txt"
    if not txt_path.exists():
        return None
    try:
        content = txt_path.read_text(encoding="utf-8", errors="ignore").strip()
        # Skip empty files or JSON masquerading as .txt
        if not content or content.startswith("{"):
            return None
        # Check for actual Netscape cookie lines (tab-separated values, not header comments)
        has_cookies = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                has_cookies = True
                break
        if not has_cookies:
            return None
        return str(txt_path)
    except Exception:
        return None


def _build_cookie_opts(opts: dict) -> None:
    cookie_path = _yt_cookies_path()
    if not cookie_path:
        return

    opts["cookiefile"] = cookie_path
    opts["extractor_args"] = {
        "youtube": {
            "player_client": ["web"],
        }
    }


def _classify_ydl_error(msg: str) -> tuple[str, str | None]:
    m = (msg or "").lower()
    if any(s in m for s in ["age-restricted", "age restriction", "this video may be inappropriate"]):
        return "Age-restricted video.", "Try again with cookies enabled (cookies.txt) and run the server without changing networks."
    if any(s in m for s in ["private video", "this video is private", "unavailable"]):
        return "Video is unavailable/private.", "The link might be private, removed, or not accessible from your region."
    if any(s in m for s in ["sign in", "login", "consent"]):
        return "Video requires sign-in/consent.", "Cookies are usually required for these."
    if any(s in m for s in ["http error 429", "429 too many requests", "too many requests", "rate limit"]):
        return "Rate limited (HTTP 429).", "Wait a few minutes and try again, or disable subtitles/download quickly."
    if any(s in m for s in ["ffmpeg", "not found"]):
        return "ffmpeg is missing.", "Install ffmpeg and ensure it is in PATH. See README."
    if any(s in m for s in ["requested format is not available"]):
        return "Format not available.", "The video may not have the requested quality. Try 'Best Available' quality instead."
    return "Could not fetch video.", None


def ydl_info(url: str):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "socket_timeout": 30,
        "retries": 10,
    }
    _build_cookie_opts(opts)
    with YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


def format_selector(kind: str, quality: str, file_format: str) -> str:
    quality = str(quality or "best").lower()
    file_format = str(file_format or "mp4").lower()

    height_map = {
        "2160": 2160,
        "4k": 2160,
        "1440": 1440,
        "2k": 1440,
        "1080": 1080,
        "720": 720,
        "480": 480,
        "360": 360,
    }
    height = None
    for key, value in height_map.items():
        if key in quality:
            height = value
            break

    if kind == "audio":
        return "bestaudio/best"

    if height:
        if file_format == "webm":
            return f"bestvideo[height<={height}][ext=webm]+bestaudio[ext=webm]/bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"
        return f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={height}]+bestaudio/best[height<={height}][ext=mp4]/best[height<={height}]/best"

    if file_format == "webm":
        return "bestvideo[ext=webm]+bestaudio[ext=webm]/bestvideo+bestaudio/best[ext=webm]/best"
    return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best"


def build_ydl_opts(job_id: str, job_dir: Path, kind: str, quality: str, file_format: str, include_subtitles: bool, embed_thumbnail: bool):
    outtmpl = str(job_dir / "%(title).90s-%(id)s.%(ext)s")
    postprocessors = []

    def progress_hook(d):
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes") or 0
            percent = round(downloaded * 100 / total, 2) if total else None
            set_job(
                job_id,
                status="downloading",
                percent=percent,
                downloaded_bytes=downloaded,
                total_bytes=total,
                speed=d.get("speed"),
                eta=d.get("eta"),
                message="Downloading...",
            )
        elif status == "finished":
            set_job(job_id, status="processing", percent=100, message="Download finished. Processing/merging with ffmpeg...")

    ydl_opts = {
        "outtmpl": outtmpl,
        "format": format_selector(kind, quality, file_format),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": False,
        "windowsfilenames": True,
        "continuedl": True,
        "retries": 20,
        "fragment_retries": 20,
        "file_access_retries": 10,
        "extractor_retries": 5,
        "socket_timeout": 60,
        "sleep_interval_requests": 1,
        "concurrent_fragment_downloads": 4,
        "progress_hooks": [progress_hook],
    }

    if kind == "video":
        if file_format in {"mp4", "webm"}:
            ydl_opts["merge_output_format"] = file_format
    else:
        if file_format not in {"mp3", "m4a", "opus", "wav"}:
            file_format = "mp3"
        postprocessors.append({
            "key": "FFmpegExtractAudio",
            "preferredcodec": file_format,
            "preferredquality": "192",
        })

    if include_subtitles:
        ydl_opts["writesubtitles"] = True
        ydl_opts["writeautomaticsub"] = True
        ydl_opts["subtitleslangs"] = ["en", "en.*"]
        ydl_opts["subtitlesformat"] = "srt/best"

    if embed_thumbnail:
        ydl_opts["writethumbnail"] = True
        postprocessors.append({"key": "EmbedThumbnail"})

    if postprocessors:
        ydl_opts["postprocessors"] = postprocessors

    return ydl_opts


def collect_output_file(job_dir: Path, include_subtitles: bool):
    files = [p for p in job_dir.iterdir() if p.is_file() and not p.name.endswith(".part")]
    if not files:
        raise RuntimeError("Download failed. No output file was created.")

    media_exts = {"mp4", "webm", "mkv", "mp3", "m4a", "opus", "wav"}
    media_files = [p for p in files if p.suffix.lower().lstrip(".") in media_exts]

    if include_subtitles and len(files) > 1:
        zip_path = job_dir / "download-with-subtitles.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in files:
                if p != zip_path:
                    zf.write(p, arcname=p.name)
        return zip_path

    return media_files[0] if media_files else files[0]


def run_download_job(job_id: str, data: dict):
    url = (data.get("url") or "").strip()
    kind = (data.get("type") or "video").lower()
    quality = data.get("quality") or "best"
    file_format = (data.get("format") or "mp4").lower().replace(".", "")
    include_subtitles = bool(data.get("subtitles"))
    embed_thumbnail = bool(data.get("embedThumbnail"))

    job_dir = DOWNLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    set_job(job_id, status="starting", percent=0, message="Starting download...", file_url=None)

    try:
        if kind == "thumbnail":
            set_job(job_id, status="processing", percent=10, message="Fetching thumbnail...")
            info = ydl_info(url)
            thumb_url = info.get("thumbnail")
            if not thumb_url:
                raise RuntimeError("Thumbnail not found.")
            response = requests.get(thumb_url, timeout=60)
            response.raise_for_status()
            ext = "webp" if "webp" in response.headers.get("content-type", "") else "jpg"
            filename = f"{clean_title(info.get('title'))}-thumbnail.{ext}"
            file_path = job_dir / filename
            file_path.write_bytes(response.content)
            set_job(job_id, status="finished", percent=100, message="Thumbnail ready.", file_path=str(file_path), filename=filename, file_url=f"/api/file/{job_id}")
            return

        ydl_opts = build_ydl_opts(job_id, job_dir, kind, quality, file_format, include_subtitles, embed_thumbnail)

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as download_error:
            msg = str(download_error).lower()
            if include_subtitles and ("subtitles" in msg or "429" in msg or "too many requests" in msg):
                include_subtitles = False
                for key in ["writesubtitles", "writeautomaticsub", "subtitleslangs", "subtitlesformat"]:
                    ydl_opts.pop(key, None)
                set_job(job_id, status="downloading", message="Subtitles failed/rate-limited. Retrying video without subtitles...")
                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            else:
                raise

        chosen = collect_output_file(job_dir, include_subtitles)
        set_job(job_id, status="finished", percent=100, message="Download ready.", file_path=str(chosen), filename=chosen.name, file_url=f"/api/file/{job_id}")

    except Exception as e:
        set_job(
            job_id,
            status="error",
            percent=0,
            error=str(e),
            message="Download failed.",
            hint="For 4K/MP3 use ffmpeg and a server with enough disk/RAM/time. If error is HTTP 429, wait and try later or disable subtitles. Use only authorized content.",
        )


@app.route("/")
def home():
    return send_from_directory(PUBLIC_DIR, "index.html")


@app.route("/api/info", methods=["POST"])
def api_info():
    data = request.get_json(force=True, silent=True) or {}
    url = (data.get("url") or "").strip()

    if not url:
        return jsonify({"error": "URL is required."}), 400

    if not is_allowed_url(url):
        return jsonify({"error": "Please enter a valid YouTube link."}), 400

    try:
        info = ydl_info(url)
        formats = []
        seen = set()
        for f in info.get("formats", []):
            height = f.get("height")
            ext = f.get("ext")
            if height and ext:
                key = (height, ext)
                if key not in seen:
                    seen.add(key)
                    formats.append({"height": height, "ext": ext})
        formats = sorted(formats, key=lambda x: x["height"], reverse=True)[:40]

        return jsonify({
            "id": info.get("id"),
            "title": info.get("title"),
            "uploader": info.get("uploader"),
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "webpage_url": info.get("webpage_url"),
            "formats": formats,
        })
    except Exception as e:
        err = str(e)
        short_msg, hint = _classify_ydl_error(err)
        try:
            print(f"[yt-dlp:/api/info] url={url}\nerror={err}\nclassified={short_msg}\nhint={hint}", flush=True)
        except Exception:
            pass
        payload = {"error": short_msg, "details": err}
        if hint:
            payload["hint"] = hint
        return jsonify(payload), 500


@app.post("/api/start-download")
def api_start_download():
    data = request.get_json(force=True, silent=True) or {}
    url = (data.get("url") or "").strip()
    kind = (data.get("type") or "video").lower()

    if not is_allowed_url(url):
        return jsonify({"error": "Please enter a valid YouTube link."}), 400
    if kind not in {"video", "audio", "thumbnail"}:
        return jsonify({"error": "Invalid download type."}), 400

    job_id = uuid.uuid4().hex
    set_job(job_id, status="queued", percent=0, message="Queued...", created_at=time.time())
    thread = threading.Thread(target=run_download_job, args=(job_id, data), daemon=True)
    thread.start()
    return jsonify({"job_id": job_id, "progress_url": f"/api/progress/{job_id}"})


@app.get("/api/progress/<job_id>")
def api_progress(job_id):
    job = get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found."}), 404
    safe = {k: v for k, v in job.items() if k != "file_path"}
    return jsonify(safe)


@app.get("/api/file/<job_id>")
def api_file(job_id):
    job = get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found."}), 404
    if job.get("status") != "finished" or not job.get("file_path"):
        return jsonify({"error": "File is not ready yet."}), 400
    file_path = Path(job["file_path"])
    if not file_path.exists():
        return jsonify({"error": "File no longer exists on server."}), 404
    return send_file(file_path, as_attachment=True, download_name=job.get("filename") or file_path.name)


@app.post("/api/download")
def api_download():
    data = request.get_json(force=True, silent=True) or {}
    url = (data.get("url") or "").strip()
    kind = (data.get("type") or "video").lower()
    quality = data.get("quality") or "best"
    file_format = (data.get("format") or "mp4").lower().replace(".", "")
    include_subtitles = bool(data.get("subtitles"))
    embed_thumbnail = bool(data.get("embedThumbnail"))

    if not is_allowed_url(url):
        return jsonify({"error": "Please enter a valid YouTube link."}), 400
    if kind not in {"video", "audio", "thumbnail"}:
        return jsonify({"error": "Invalid download type."}), 400

    tmpdir = tempfile.mkdtemp(prefix="yt_download_")

    @after_this_request
    def cleanup(response):
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass
        return response

    try:
        job_id = "direct_" + uuid.uuid4().hex
        job_dir = Path(tmpdir)
        if kind == "thumbnail":
            info = ydl_info(url)
            thumb_url = info.get("thumbnail")
            if not thumb_url:
                return jsonify({"error": "Thumbnail not found."}), 404
            response = requests.get(thumb_url, timeout=60)
            response.raise_for_status()
            ext = "webp" if "webp" in response.headers.get("content-type", "") else "jpg"
            filename = f"{clean_title(info.get('title'))}-thumbnail.{ext}"
            file_path = job_dir / filename
            file_path.write_bytes(response.content)
            return send_file(file_path, as_attachment=True, download_name=filename)

        ydl_opts = build_ydl_opts(job_id, job_dir, kind, quality, file_format, include_subtitles, embed_thumbnail)
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        chosen = collect_output_file(job_dir, include_subtitles)
        return send_file(chosen, as_attachment=True, download_name=chosen.name)
    except Exception as e:
        return jsonify({
            "error": str(e),
            "hint": "For large videos use the new background download endpoint. If this is MP3, 1080p, 2K, or 4K, install ffmpeg.",
        }), 500


def open_browser():
    """Open browser after a short delay so the server is ready."""
    import time
    time.sleep(1.5)
    port = int(os.environ.get("PORT", 5000))
    url = f"http://127.0.0.1:{port}"
    try:
        import webbrowser
        webbrowser.open(url)
        print(f"  Browser opened at {url}")
    except Exception:
        print(f"  Open manually: {url}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"

    if os.environ.get("NO_BROWSER") != "1":
        threading.Thread(target=open_browser, daemon=True).start()

    print(f"\n  AnyDownloader is running!")
    print(f"  Open: http://127.0.0.1:{port}")
    print(f"  Press Ctrl+C to stop the server\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
