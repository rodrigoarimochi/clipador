"""Baixa o vídeo (e metadados) de uma URL do YouTube usando yt-dlp."""
import yt_dlp
from pathlib import Path


def download_video(url: str, dest_dir: Path) -> dict:
    """
    Baixa o vídeo em MP4 (melhor qualidade até 1080p, pra não pesar demais
    numa VPS free) e retorna informações básicas.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(dest_dir / "source.%(ext)s")

    ydl_opts = {
        "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": out_template,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
        "geo_bypass": True,
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
