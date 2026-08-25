"""Corta o trecho, reenquadra (opcional 9:16) e queima a legenda com ffmpeg."""
import subprocess
from pathlib import Path


def cut_clip(
    source_path: str,
    start: float,
    end: float,
    ass_path: Path,
    out_path: Path,
    vertical: bool = True,
):
    duration = end - start

    if vertical:
        # Corta o centro do vídeo em 9:16 (ex: 1080x1920) e depois queima a legenda.
        vf = (
            "crop=ih*9/16:ih,scale=1080:1920,"
            f"subtitles='{ass_path.as_posix()}'"
        )
    else:
        vf = f"subtitles='{ass_path.as_posix()}'"

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", source_path,
        "-t", str(duration),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
        "-c:a", "aac", "-b:a", "160k",
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg falhou: {result.stderr[-2000:]}")
    return out_path
