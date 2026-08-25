"""Baixa o vídeo (e metadados) de uma URL do YouTube usando yt-dlp."""
import os
from pathlib import Path
import yt_dlp


def download_video(url: str, dest_dir: Path) -> dict:
    """
    Baixa o vídeo evitando o erro HTTP 403 através de clientes móveis.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(dest_dir / "source.%(ext)s")

    cookie_path = os.environ.get("YOUTUBE_COOKIES_PATH")
    if cookie_path and not os.path.exists(cookie_path):
        cookie_path = None

    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": out_template,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "cookiefile": cookie_path,
        "concurrent_fragment_downloads": 1,
        "extractor_args": {
            "youtube": {
                "player_client": ["android_vr", "android", "ios"],
                "player_skip": ["webpage", "configs"],
            }
        },
        "http_headers": {
            "User-Agent": "com.google.android.youtube/19.29.37 (Linux; U; Android 14; US) gzip",
            "Accept-Language": "en-US,en;q=0.9",
        },
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info)
        
        mp4_path = Path(filepath).with_suffix(".mp4")
        if not mp4_path.exists():
            mp4_path = Path(filepath)

    return {
        "title": info.get("title", "video"),
        "duration": info.get("duration", 0),
        "video_path": str(mp4_path),
    }
