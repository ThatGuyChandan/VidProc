from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Body
from sqlalchemy.orm import Session
import os
import uuid
from pydantic import BaseModel
from fastapi.responses import FileResponse
from celery.result import AsyncResult

from backend import crud, models, schemas
from backend.database import SessionLocal, engine
from .celery_worker import celery_app, process_upload, process_trim, process_quality, process_image_overlay, process_video_overlay, process_text_overlay, process_watermark

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

class TrimRequest(BaseModel):
    video_id: int
    start_time: float
    end_time: float

class TextOverlayRequest(BaseModel):
    video_id: int
    text: str
    x: int
    y: int
    start_time: float
    end_time: float

class ImageOverlayRequest(BaseModel):
    video_id: int
    image_name: str
    x: int
    y: int
    start_time: float
    end_time: float

class VideoOverlayRequest(BaseModel):
    video_id: int
    video_name: str
    x: int
    y: int
    start_time: float
    end_time: float

class WatermarkRequest(BaseModel):
    video_id: int
    image_name: str

class QualityRequest(BaseModel):
    video_id: int
    quality: str

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/upload/")
async def upload_video(file: UploadFile = File(...)):
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(upload_dir, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")

    task = process_upload.delay(file_path, unique_filename)
    return {"job_id": task.id, "filename": unique_filename}

@app.get("/videos/", response_model=list[schemas.Video])
def read_videos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    videos = crud.get_videos(db, skip=skip, limit=limit)
    return videos

@app.post("/trim/")
def trim_video(trim_request: TrimRequest):
    task = process_trim.delay(trim_request.video_id, trim_request.start_time, trim_request.end_time)
    return {"job_id": task.id}

@app.post("/overlays/text")
def add_text_overlay(request: TextOverlayRequest):
    task = process_text_overlay.delay(request.video_id, request.text, request.x, request.y, request.start_time, request.end_time)
    return {"job_id": task.id}

@app.post("/overlays/image")
def add_image_overlay(request: ImageOverlayRequest):
    task = process_image_overlay.delay(request.video_id, request.image_name, request.x, request.y, request.start_time, request.end_time)
    return {"job_id": task.id}

@app.post("/overlays/video")
def add_video_overlay(request: VideoOverlayRequest):
    task = process_video_overlay.delay(request.video_id, request.video_name, request.x, request.y, request.start_time, request.end_time)
    return {"job_id": task.id}

@app.post("/watermark")
def add_watermark(request: WatermarkRequest):
    task = process_watermark.delay(request.video_id, request.image_name)
    return {"job_id": task.id}

@app.post("/quality")
def generate_quality(request: QualityRequest):
    task = process_quality.delay(request.video_id, request.quality)
    return {"job_id": task.id}

@app.get("/videos/{video_id}/quality/{quality}")
def get_quality_video(video_id: int, quality: str, db: Session = Depends(get_db)):
    video = crud.get_video(db, video_id=video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    for q in video.qualities:
        if q.quality == quality:
            quality_dir = "qualities"
            file_path = os.path.join(quality_dir, q.filename)
            if os.path.exists(file_path):
                return FileResponse(file_path)
            else:
                raise HTTPException(status_code=404, detail="File not found")
    
    raise HTTPException(status_code=404, detail="Quality not found")

@app.get("/status/{job_id}")
def get_status(job_id: str):
    task_result = AsyncResult(job_id, app=celery_app)
    return {"status": task_result.status, "result": task_result.result}

@app.get("/result/{job_id}")
def get_result(job_id: str):
    task_result = AsyncResult(job_id, app=celery_app)
    if task_result.ready():
        result = task_result.get()
        if result["status"] == "completed":
            return FileResponse(result["file_path"])
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    else:
        raise HTTPException(status_code=202, detail="Job not ready")
