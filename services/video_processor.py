import os
import subprocess
import yt_dlp
from datetime import datetime

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")

def download_video(url: str) -> dict:
    """
    Downloads a video from a URL using yt-dlp.
    Returns a dict with 'path', 'duration', 'title', 'platform'.
    """
    
    # specialized options for Instagram to avoid blocks
    # note: instagram is very aggressive with blocks without cookies
    is_instagram = "instagram.com" in url
    is_tiktok = "tiktok.com" in url
    
    ydl_opts = {
        # Limit quality to 1080p max to avoid huge files, but be flexible
        'format': 'best[ext=mp4]/best' if is_instagram else 'best[height<=1080][ext=mp4]/best[ext=mp4]/best', 
        'outtmpl': os.path.join(UPLOAD_DIR, '%(id)s.%(ext)s'),
        'quiet': False, # Enable logs for debugging
        'no_warnings': False,
        'ignoreerrors': True, # Don't crash on minor errors
        'geo_bypass': True,
        'nocheckcertificate': True,
        # Updated User Agent (Chrome 120 on Windows 10)
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'http_headers': {
            'Referer': 'https://www.instagram.com/' if is_instagram else 'https://www.tiktok.com/' if is_tiktok else 'https://www.google.com/'
        }
    }
    
    if is_instagram:
        # Instagram specific tweaks
        ydl_opts.update({
             'extractor_args': {
                'instagram': {
                    'max_comments': [0], # Don't download comments, triggers blocks
                    'api_limit': [0]
                }
            },
            'sleep_interval': 5, # Slow down to look human
            'max_sleep_interval': 10
        })

    try:
        print(f"Downloading video from {url}...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # First try to extract info
            info = ydl.extract_info(url, download=True)
            
            if not info:
                raise ValueError("Download failed (no info returned). The video might be private or deleted.")

            # If it's a playlist or list (rare for single link, but possible)
            if 'entries' in info:
                info = info['entries'][0]
                
            filename = ydl.prepare_filename(info)
            
            # Verify file exists, sometimes yt-dlp returns success but file is weird
            if not os.path.exists(filename):
                # Fallback: check if maybe it saved with a different extension
                base, _ = os.path.splitext(filename)
                for ext in ['.mp4', '.mkv', '.webm']:
                     if os.path.exists(base + ext):
                         filename = base + ext
                         break
            
            return {
                "path": filename,
                "duration": info.get('duration'),
                "title": info.get('title'),
                "platform": info.get('extractor'),
                "thumbnail": info.get('thumbnail')
            }
    except Exception as e:
        print(f"Download failed: {e}")
        # Re-raise with a clear message
        raise ValueError(f"Could not download video. Access might be restricted or link is invalid. Error: {str(e)}")

def extract_audio(video_path: str) -> str:
    """
    Extracts audio from video using ffmpeg.
    Returns the path to the audio file.
    """
    base, _ = os.path.splitext(video_path)
    audio_path = f"{base}.mp3"
    
    # ffmpeg -i video.mp4 -q:a 0 -map a audio.mp3 -y
    cmd = [
        FFMPEG_PATH, "-i", video_path,
        "-q:a", "0", "-map", "a",
        audio_path, "-y"
    ]
    
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return audio_path

def extract_frames(video_path: str, interval: int = 1) -> list[str]:
    """
    Extracts frames from video every 'interval' seconds.
    Returns a list of paths to the extracted frames.
    """
    base, _ = os.path.splitext(video_path)
    frames_dir = f"{base}_frames"
    os.makedirs(frames_dir, exist_ok=True)
    
    # ffmpeg -i video.mp4 -vf fps=1/interval frames_dir/frame_%04d.jpg
    cmd = [
        FFMPEG_PATH, "-i", video_path,
        "-vf", f"fps=1/{interval}",
        os.path.join(frames_dir, "frame_%04d.jpg"),
        "-y"
    ]
    
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    frames = sorted([
        os.path.join(frames_dir, f) 
        for f in os.listdir(frames_dir) 
        if f.endswith(".jpg")
    ])
    return frames
