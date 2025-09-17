from sqlalchemy.orm import Session
from . import models, schemas

def get_video(db: Session, video_id: int):
    return db.query(models.Video).filter(models.Video.id == video_id).first()

def get_videos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Video).offset(skip).limit(limit).all()

def create_video(db: Session, video: schemas.VideoCreate):
    db_video = models.Video(filename=video.filename, duration=video.duration, size=video.size)
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return db_video

def create_trimmed_video(db: Session, trimmed_video: schemas.TrimmedVideoCreate):
    db_trimmed_video = models.TrimmedVideo(**trimmed_video.dict())
    db.add(db_trimmed_video)
    db.commit()
    db.refresh(db_trimmed_video)
    return db_trimmed_video

def create_overlay(db: Session, overlay: schemas.OverlayCreate):
    db_overlay = models.Overlay(**overlay.dict())
    db.add(db_overlay)
    db.commit()
    db.refresh(db_overlay)
    return db_overlay

def create_video_quality(db: Session, video_quality: schemas.VideoQualityCreate):
    db_video_quality = models.VideoQuality(**video_quality.dict())
    db.add(db_video_quality)
    db.commit()
    db.refresh(db_video_quality)
    return db_video_quality
