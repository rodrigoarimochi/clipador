import json
import traceback
from pathlib import Path
from app import config
from app.pipeline import download, transcribe, highlights, subtitles, cut

JOBS_STATE: dict[str, dict] = {}  # em memória; troque por Redis/DB se escalar


def _save_state(job_id: str):
    (config.JOBS_DIR / f"{job_id}.json").write_text(
        json.dumps(JOBS_STATE[job_id], default=str, ensure_ascii=False, indent=2)
    )


def run_job(job_id: str, url: str, vertical: bool = True):
    state = JOBS_STATE[job_id] = {"status": "baixando", "progress": 5, "clips": [], "error": None}
    _save_state(job_id)
    job_dir = config.JOBS_DIR / job_id
    out_dir = config.OUTPUT_DIR / job_id
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        info = download.download_video(url, job_dir)
        state.update(status="transcrevendo", progress=25, title=info["title"], duration=info["duration"])
        _save_state(job_id)

        transcript = transcribe.transcribe(info["video_path"])
        state.update(status="escolhendo_melhores_momentos", progress=55)
        _save_state(job_id)

        picks = highlights.select_highlights(transcript["segments"], info["duration"], info["title"])
        if not picks:
            raise RuntimeError("Não encontrei trechos bons o suficiente nesse vídeo.")

        state.update(status="cortando", progress=65)
        _save_state(job_id)

        clips_meta = []
        for idx, pick in enumerate(picks):
            ass_path = job_dir / f"clip_{idx}.ass"
            subtitles.build_ass(transcript["words"], pick["start"], pick["end"], ass_path)

            out_path = out_dir / f"clip_{idx}.mp4"
            cut.cut_clip(info["video_path"], pick["start"], pick["end"], ass_path, out_path, vertical=vertical)

            clips_meta.append({
                "index": idx,
                "start": pick["start"],
                "end": pick["end"],
                "duration": round(pick["end"] - pick["start"], 1),
                "reason": pick.get("reason", ""),
                "file": out_path.name,
            })
            state["progress"] = 65 + int(30 * (idx + 1) / len(picks))
            state["clips"] = clips_meta
            _save_state(job_id)

        state.update(status="concluido", progress=100)
        _save_state(job_id)

    except Exception as e:
        state.update(status="erro", error=str(e), traceback=traceback.format_exc())
        _save_state(job_id)
