import uuid
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from app import config
from app.pipeline.runner import run_job, JOBS_STATE

app = FastAPI(title="Clipador")


class NewJob(BaseModel):
    url: str
    vertical: bool = True


@app.post("/api/jobs")
def create_job(payload: NewJob, background_tasks: BackgroundTasks):
    if "youtube.com" not in payload.url and "youtu.be" not in payload.url:
        raise HTTPException(400, "Manda um link válido do YouTube.")
    job_id = uuid.uuid4().hex[:10]
    JOBS_STATE[job_id] = {"status": "na_fila", "progress": 0, "clips": []}
    background_tasks.add_task(run_job, job_id, payload.url, payload.vertical)
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    state = JOBS_STATE.get(job_id)
    if not state:
        raise HTTPException(404, "Job não encontrado.")
    return {"job_id": job_id, **state}


@app.get("/api/jobs/{job_id}/clips/{filename}")
def download_clip(job_id: str, filename: str):
    path = config.OUTPUT_DIR / job_id / filename
    if not path.exists():
        raise HTTPException(404, "Clipe não encontrado.")
    return FileResponse(path, media_type="video/mp4", filename=filename)


@app.get("/", response_class=HTMLResponse)
def index():
    return (config.BASE_DIR / "static" / "index.html").read_text(encoding="utf-8")


app.mount("/static", StaticFiles(directory=str(config.BASE_DIR / "static")), name="static")
