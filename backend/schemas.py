from pydantic import BaseModel
import datetime

class VideoQualityBase(BaseModel):
    quality: str
    filename: str
    size: float

class VideoQualityCreate(VideoQualityBase):
    original_video_id: int

class VideoQuality(VideoQualityBase):
    id: int

    class Config:
        orm_mode = True

class OverlayBase(BaseModel):
    overlay_type: str
    content: str
    x: int
    y: int
    start_time: float
    end_time: float

class OverlayCreate(OverlayBase):
    video_id: int

class Overlay(OverlayBase):
    id: int

    class Config:
        orm_mode = True

class TrimmedVideoBase(BaseModel):
    filename: str
    duration: float
    size: float

class TrimmedVideoCreate(TrimmedVideoBase):
    original_video_id: int

class TrimmedVideo(TrimmedVideoBase):
    id: int
    upload_time: datetime.datetime
    original_video_id: int

    class Config:
        orm_mode = True

class VideoBase(BaseModel):
    filename: str
    duration: float
    size: float

class VideoCreate(VideoBase):
    pass

class Video(VideoBase):
    id: int
    upload_time: datetime.datetime
    trimmed_videos: list[TrimmedVideo] = []
    overlays: list[Overlay] = []
    qualities: list[VideoQuality] = []

    class Config:
        orm_mode = True
