# Deploy YouTube Downloader App on Render

> Important: Use this app only for content you own, have permission to download, or that is legally allowed. Hosting providers may suspend apps that violate copyright or platform terms.

## Files ready for deployment

This project includes:

- `app.py` - Flask backend
- `public/index.html` - frontend
- `requirements.txt` - Python packages
- `Dockerfile` - production deploy with ffmpeg

## Step 1: Create GitHub repository

1. Open https://github.com
2. Create a new repository, for example: `youtube-downloader-app`
3. Upload/push all files inside `youtube-downloader-app` folder.

Using git commands:

```bash
cd youtube-downloader-app
git init
git add .
git commit -m "Initial YouTube downloader app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/youtube-downloader-app.git
git push -u origin main
```

## Step 2: Deploy on Render

1. Open https://render.com
2. Sign up / log in
3. Click **New +**
4. Select **Web Service**
5. Connect your GitHub repository
6. Choose deployment type: **Docker**
7. Render will use the included `Dockerfile`
8. Click **Create Web Service**

Render will build and start the app. After deploy you will get a live URL like:

```text
https://your-app-name.onrender.com
```

## Step 3: Test

Open the Render URL in browser.

Try first:

- Download Type: Video + Audio
- Quality: 720p
- Format: MP4
- Keep **Include subtitles OFF**

## Common live-hosting problems

### 1. Download timeout

Free hosting has request time limits. Large videos may fail. Start with small videos and 360p/720p.

### 2. HTTP 429 Too Many Requests

YouTube may rate-limit hosting server IPs. Try later, disable subtitles, or use another hosting provider/VPS.

### 3. MP3 or 1080p fails

Dockerfile installs ffmpeg, so it should work. If not, check Render logs.

### 4. App sleeps on free plan

Free hosting may sleep after inactivity. First load can be slow.

## Better production option

For a real public downloader with many users, use a VPS:

- DigitalOcean
- Hetzner
- AWS Lightsail
- Google Cloud VM

A VPS gives more control but costs money.
