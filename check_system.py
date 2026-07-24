import shutil
import sys

print('Python:', sys.version)
print('Python executable:', sys.executable)

for module in ['flask', 'yt_dlp', 'requests']:
    try:
        __import__(module)
        print(f'OK: {module} installed')
    except Exception as e:
        print(f'MISSING: {module} -> {e}')

ffmpeg = shutil.which('ffmpeg')
if ffmpeg:
    print('OK: ffmpeg found at', ffmpeg)
else:
    print('WARNING: ffmpeg not found. MP3 and high-quality video merge may fail.')

print('\nIf all modules are OK, run: python app.py')
