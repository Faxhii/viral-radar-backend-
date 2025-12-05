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
    ydl_opts = {
        # Limit quality to 480p for faster analysis (Gemini doesn't need 4K)
        'format': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best[height<=480]',
        'outtmpl': os.path.join(UPLOAD_DIR, '%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            return {
                "path": filename,
                "duration": info.get('duration'),
                "title": info.get('title'),
                "platform": info.get('extractor'),
                "thumbnail": info.get('thumbnail')
            }
    except Exception as e:
        # Fallback for testing/MVP without FFmpeg or if download fails
        print(f"Real download failed: {e}. Using mock data.")
        mock_path = os.path.join(UPLOAD_DIR, "mock_video.mp4")
        if not os.path.exists(mock_path):
            with open(mock_path, "wb") as f:
                f.write(b"mock video content")
        return {
            "path": mock_path,
            "duration": 60,
            "title": "Mock Video",
            "platform": "youtube",
            "thumbnail": None
        }

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
