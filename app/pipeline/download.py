"""Baixa o vídeo (e metadados) de uma URL do YouTube usando yt-dlp."""
import os
from pathlib import Path
import yt_dlp


def download_video(url: str, dest_dir: Path) -> dict:
    """
    Baixa o vídeo em MP4 (melhor qualidade até 1080p, pra não pesar demais
    numa VPS free) e retorna informações básicas.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(dest_dir / "source.%(ext)s")

    # Verifica se há arquivo de cookies configurado
    cookie_path = os.environ.get("YOUTUBE_COOKIES_PATH")
    if cookie_path and not os.path.exists(cookie_path):
        cookie_path = None

    ydl_opts = {
        "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": out_template,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "cookiefile": cookie_path,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info)
        # merge_output_format garante .mp4, mas ajustamos o path se preciso
        mp4_path = Path(filepath).with_suffix(".mp4")
        if not mp4_path.exists():
            mp4_path = Path(filepath)

    return {
        "title": info.get("title", "video"),
        "duration": info.get("duration", 0),
        "video_path": str(mp4_path),
    }
