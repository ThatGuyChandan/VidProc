from celery import Celery
import subprocess
import json
import os

from backend.database import SessionLocal
from backend import crud, schemas

celery_app = Celery(
    "tasks",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)

def get_video_metadata(video_path: str):
    """
    Extracts video metadata using ffprobe.
    """
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception("Error running ffprobe")
    
    metadata = json.loads(result.stdout)
    
    duration = float(metadata["format"]["duration"])
    size = float(metadata["format"]["size"])
    
    return duration, size

@celery_app.task
def process_upload(file_path: str, filename: str):
    db = SessionLocal()
    try:
        duration, size = get_video_metadata(file_path)
        video = schemas.VideoCreate(filename=filename, duration=duration, size=size)
        crud.create_video(db=db, video=video)
    finally:
        db.close()
    return {"status": "completed", "file_path": file_path}

@celery_app.task
def process_trim(video_id: int, start_time: float, end_time: float):
    db = SessionLocal()
    try:
        original_video = crud.get_video(db, video_id=video_id)
        if not original_video:
            return {"status": "error", "message": "Original video not found"}

        upload_dir = "uploads"
        trim_dir = "trims"
        if not os.path.exists(trim_dir):
            os.makedirs(trim_dir)

        original_video_path = os.path.join(upload_dir, original_video.filename)
        trimmed_video_filename = f"trimmed_{original_video.filename}"
        trimmed_video_path = os.path.join(trim_dir, trimmed_video_filename)

        cmd = [
            "ffmpeg",
            "-i",
            original_video_path,
            "-ss",
            str(start_time),
            "-to",
            str(end_time),
            "-c",
            "copy",
            trimmed_video_path,
        ]
        
        subprocess.run(cmd, check=True)

        duration, size = get_video_metadata(trimmed_video_path)

        trimmed_video = schemas.TrimmedVideoCreate(
            filename=trimmed_video_filename,
            duration=duration,
            size=size,
            original_video_id=video_id,
        )
        crud.create_trimmed_video(db=db, trimmed_video=trimmed_video)
    finally:
        db.close()
    return {"status": "completed", "file_path": trimmed_video_path}

@celery_app.task
def process_text_overlay(video_id: int, text: str, x: int, y: int, start_time: float, end_time: float):
    db = SessionLocal()
    try:
        original_video = crud.get_video(db, video_id=video_id)
        if not original_video:
            return {"status": "error", "message": "Original video not found"}

        upload_dir = "uploads"
        output_dir = "outputs"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        original_video_path = os.path.join(upload_dir, original_video.filename)
        output_video_filename = f"overlay_{original_video.filename}"
        output_video_path = os.path.join(output_dir, output_video_filename)

        font_file = "fonts/NotoSans-Regular.ttf"
        if not os.path.exists(font_file):
            return {"status": "error", "message": "Font file not found"}

        cmd = [
            "ffmpeg",
            "-i",
            original_video_path,
            "-vf",
            f"drawtext=text='{text}':x={x}:y={y}:fontsize=24:fontcolor=white:fontfile={font_file}:enable='between(t,{start_time},{end_time})'",
            output_video_path,
        ]

        subprocess.run(cmd, check=True)

        overlay = schemas.OverlayCreate(
            video_id=video_id,
            overlay_type="text",
            content=text,
            x=x,
            y=y,
            start_time=start_time,
            end_time=end_time,
        )
        crud.create_overlay(db=db, overlay=overlay)
    finally:
        db.close()
    return {"status": "completed", "file_path": output_video_path}

@celery_app.task
def process_image_overlay(video_id: int, image_name: str, x: int, y: int, start_time: float, end_time: float):
    db = SessionLocal()
    try:
        original_video = crud.get_video(db, video_id=video_id)
        if not original_video:
            return {"status": "error", "message": "Original video not found"}

        upload_dir = "uploads"
        output_dir = "outputs"
        overlay_dir = "overlays"

        original_video_path = os.path.join(upload_dir, original_video.filename)
        output_video_filename = f"overlay_image_{original_video.filename}"
        output_video_path = os.path.join(output_dir, output_video_filename)
        overlay_image_path = os.path.join(overlay_dir, image_name)

        if not os.path.exists(overlay_image_path):
            return {"status": "error", "message": f"Overlay image not found at {overlay_image_path}"}

        cmd = [
            "ffmpeg",
            "-i",
            original_video_path,
            "-i",
            overlay_image_path,
            "-filter_complex",
            f"[1:v]scale=100:-1[ovrl]; [0:v][ovrl]overlay={x}:{y}:enable='between(t,{start_time},{end_time})'",
            output_video_path,
        ]

        subprocess.run(cmd, check=True)

        overlay = schemas.OverlayCreate(
            video_id=video_id,
            overlay_type="image",
            content=image_name,
            x=x,
            y=y,
            start_time=start_time,
            end_time=end_time,
        )
        crud.create_overlay(db=db, overlay=overlay)
    finally:
        db.close()
    return {"status": "completed", "file_path": output_video_path}

@celery_app.task
def process_video_overlay(video_id: int, video_name: str, x: int, y: int, start_time: float, end_time: float):
    db = SessionLocal()
    try:
        original_video = crud.get_video(db, video_id=video_id)
        if not original_video:
            return {"status": "error", "message": "Original video not found"}

        upload_dir = "uploads"
        output_dir = "outputs"
        overlay_dir = "overlays"

        original_video_path = os.path.join(upload_dir, original_video.filename)
        output_video_filename = f"overlay_video_{original_video.filename}"
        output_video_path = os.path.join(output_dir, output_video_filename)
        overlay_video_path = os.path.join(overlay_dir, video_name)

        if not os.path.exists(overlay_video_path):
            return {"status": "error", "message": f"Overlay video not found at {overlay_video_path}"}

        cmd = [
            "ffmpeg",
            "-i",
            original_video_path,
            "-i",
            overlay_video_path,
            "-filter_complex",
            f"[1:v]scale=100:-1[ovrl]; [0:v][ovrl]overlay={x}:{y}:enable='between(t,{start_time},{end_time})'",
            output_video_path,
        ]

        subprocess.run(cmd, check=True)

        overlay = schemas.OverlayCreate(
            video_id=video_id,
            overlay_type="video",
            content=video_name,
            x=x,
            y=y,
            start_time=start_time,
            end_time=end_time,
        )
        crud.create_overlay(db=db, overlay=overlay)
    finally:
        db.close()
    return {"status": "completed", "file_path": output_video_path}

@celery_app.task
def process_watermark(video_id: int, image_name: str):
    db = SessionLocal()
    try:
        original_video = crud.get_video(db, video_id=video_id)
        if not original_video:
            return {"status": "error", "message": "Original video not found"}

        upload_dir = "uploads"
        output_dir = "outputs"
        overlay_dir = "overlays"

        original_video_path = os.path.join(upload_dir, original_video.filename)
        output_video_filename = f"watermarked_{original_video.filename}"
        output_video_path = os.path.join(output_dir, output_video_filename)
        watermark_image_path = os.path.join(overlay_dir, image_name)

        if not os.path.exists(watermark_image_path):
            return {"status": "error", "message": f"Watermark image not found at {watermark_image_path}"}

        cmd = [
            "ffmpeg",
            "-i",
            original_video_path,
            "-i",
            watermark_image_path,
            "-filter_complex",
            "[1:v]scale=100:-1[ovrl]; [0:v][ovrl]overlay=W-w-10:10",
            output_video_path,
        ]

        subprocess.run(cmd, check=True)

        overlay = schemas.OverlayCreate(
            video_id=video_id,
            overlay_type="watermark",
            content=image_name,
            x=0,
            y=0,
            start_time=0,
            end_time=0,
        )
        crud.create_overlay(db=db, overlay=overlay)
    finally:
        db.close()
    return {"status": "completed", "file_path": output_video_path}

@celery_app.task
def process_quality(video_id: int, quality: str):
    db = SessionLocal()
    try:
        original_video = crud.get_video(db, video_id=video_id)
        if not original_video:
            return {"status": "error", "message": "Original video not found"}

        upload_dir = "uploads"
        quality_dir = "qualities"
        if not os.path.exists(quality_dir):
            os.makedirs(quality_dir)

        original_video_path = os.path.join(upload_dir, original_video.filename)
        quality_video_filename = f"{quality}_{original_video.filename}"
        quality_video_path = os.path.join(quality_dir, quality_video_filename)

        height = -1
        if quality == "1080p":
            height = 1080
        elif quality == "720p":
            height = 720
        elif quality == "480p":
            height = 480
        else:
            return {"status": "error", "message": "Invalid quality specified"}

        cmd = [
            "ffmpeg",
            "-i",
            original_video_path,
            "-vf",
            f"scale=-2:{height}",
            quality_video_path,
        ]

        subprocess.run(cmd, check=True)

        _, size = get_video_metadata(quality_video_path)

        video_quality = schemas.VideoQualityCreate(
            original_video_id=video_id,
            quality=quality,
            filename=quality_video_filename,
            size=size,
        )
        crud.create_video_quality(db=db, video_quality=video_quality)
    finally:
        db.close()
    return {"status": "completed", "file_path": quality_video_path}