from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    duration = Column(Float)
    size = Column(Float)
    upload_time = Column(DateTime, default=datetime.datetime.utcnow)

    trimmed_videos = relationship("TrimmedVideo", back_populates="original_video")
    overlays = relationship("Overlay", back_populates="video")
    qualities = relationship("VideoQuality", back_populates="original_video")

class TrimmedVideo(Base):
    __tablename__ = "trimmed_videos"

    id = Column(Integer, primary_key=True, index=True)
    original_video_id = Column(Integer, ForeignKey("videos.id"))
    filename = Column(String, index=True)
    duration = Column(Float)
    size = Column(Float)
    upload_time = Column(DateTime, default=datetime.datetime.utcnow)

    original_video = relationship("Video", back_populates="trimmed_videos")

class Overlay(Base):
    __tablename__ = "overlays"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"))
    overlay_type = Column(String)
    content = Column(String)
    x = Column(Integer)
    y = Column(Integer)
    start_time = Column(Float)
    end_time = Column(Float)

    video = relationship("Video", back_populates="overlays")

class VideoQuality(Base):
    __tablename__ = "video_qualities"

    id = Column(Integer, primary_key=True, index=True)
    original_video_id = Column(Integer, ForeignKey("videos.id"))
    quality = Column(String)
    filename = Column(String, index=True)
    size = Column(Float)

    original_video = relationship("Video", back_populates="qualities")
