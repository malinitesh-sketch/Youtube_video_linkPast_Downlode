# Large Video + 4K Hosting Guide

This version is improved for large videos and 4K:

- Downloads run in a **background job** instead of one long browser request.
- Frontend polls `/api/progress/<job_id>` for progress.
- Final file is downloaded from `/api/file/<job_id>`.
- Dockerfile installs `ffmpeg`, required for 1080p/2K/4K merge and MP3.

## Very important reality

No developer can guarantee YouTube downloads will never error on public hosting because:

1. YouTube can rate-limit server IPs with HTTP 429.
2. Some hosting providers have timeout/disk/RAM limits.
3. 4K videos are very large and require ffmpeg merge.
4. Free hosting storage is often temporary or small.

For reliable large video/4K, use a paid VPS with enough disk.

## Recommended server for 4K

Minimum:

- 2 CPU cores
- 4 GB RAM
- 50 GB disk
- ffmpeg installed
- Stable bandwidth

Better:

- 4 CPU cores
- 8 GB RAM
- 100+ GB disk

Good providers:

- Hetzner VPS
- DigitalOcean Droplet
- AWS Lightsail / EC2
- Google Cloud VM
- Azure VM

## Free Render warning

Render free can work for small videos, but large/4K may fail due to:

- limited disk
- service sleeping
- bandwidth/time limitations
- IP rate limits

## Deploy with Docker

This project includes Dockerfile.

```bash
docker build -t yt-downloader .
docker run -p 5000:5000 yt-downloader
```

Open:

```text
http://YOUR_SERVER_IP:5000
```

## Production command behind Nginx

For real hosting use Nginx reverse proxy and HTTPS.

Example Docker run:

```bash
docker run -d --name yt-downloader \
  -p 5000:5000 \
  -v yt_downloads:/app/downloads \
  --restart unless-stopped \
  yt-downloader
```

## Best settings for first test

- Type: Video + Audio
- Quality: 720p
- Format: MP4
- Include subtitles: OFF

Then test 1080p/4K.

## If HTTP 429 appears

- Disable subtitles
- Wait and retry later
- Update yt-dlp
- Try another server/network
- Avoid repeated requests

## Legal note

Use only for content you own, have permission to download, or that is legally allowed. Do not use it to bypass access controls, DRM, paywalls, or copyright restrictions.
