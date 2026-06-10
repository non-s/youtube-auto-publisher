"""SQLite persistence for generated and published videos."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from loguru import logger
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

import config

Base = declarative_base()


class VideoRecord(Base):
    """A single generation/upload attempt."""

    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), unique=True, nullable=False)
    topic = Column(String(200), nullable=False)
    title = Column(String(500))
    description = Column(Text)
    tags = Column(Text)
    youtube_id = Column(String(50))
    youtube_url = Column(String(200))
    video_path = Column(String(500))
    duration_seconds = Column(Integer)
    clips_count = Column(Integer)
    subtitles_count = Column(Integer)
    voice_used = Column(String(100))
    published_at = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=False)
    error_message = Column(Text)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "topic": self.topic,
            "title": self.title,
            "description": self.description,
            "tags": json.loads(self.tags or "[]"),
            "youtube_id": self.youtube_id,
            "youtube_url": self.youtube_url,
            "video_path": self.video_path,
            "duration_seconds": self.duration_seconds,
            "clips_count": self.clips_count,
            "subtitles_count": self.subtitles_count,
            "voice_used": self.voice_used,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "success": bool(self.success),
            "error_message": self.error_message,
            "views": self.views or 0,
            "likes": self.likes or 0,
        }


class DatabaseManager:
    """Small SQLAlchemy wrapper used by the publishing pipeline."""

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or config.DATABASE_URL
        connect_args = {"check_same_thread": False} if self.db_url.startswith("sqlite") else {}
        self.engine = create_engine(self.db_url, echo=False, connect_args=connect_args)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info(f"Banco de dados inicializado: {self.db_url}")

    def get_session(self) -> Session:
        return self.SessionLocal()

    def save_video(
        self,
        session_id: str,
        topic: str,
        title: str | None = None,
        description: str | None = None,
        tags: list | None = None,
        youtube_id: str | None = None,
        youtube_url: str | None = None,
        video_path: str | None = None,
        duration_seconds: int | None = None,
        clips_count: int | None = None,
        subtitles_count: int | None = None,
        voice_used: str | None = None,
        success: bool = False,
        error_message: str | None = None,
    ) -> VideoRecord:
        """Insert or update a video attempt by ``session_id``."""
        session = self.get_session()
        try:
            record = session.query(VideoRecord).filter_by(session_id=session_id).one_or_none()
            if record is None:
                record = VideoRecord(session_id=session_id, topic=topic)
                session.add(record)
            record.topic = topic
            record.title = title
            record.description = description
            record.tags = json.dumps(tags or [], ensure_ascii=False)
            record.youtube_id = youtube_id
            record.youtube_url = youtube_url
            record.video_path = video_path
            record.duration_seconds = duration_seconds
            record.clips_count = clips_count
            record.subtitles_count = subtitles_count
            record.voice_used = voice_used
            record.success = success
            record.error_message = error_message
            record.published_at = datetime.utcnow()
            session.commit()
            session.refresh(record)
            return record
        except IntegrityError:
            session.rollback()
            raise
        finally:
            session.close()

    def recent_videos(self, limit: int = 20) -> list[dict]:
        session = self.get_session()
        try:
            rows = (
                session.query(VideoRecord)
                .order_by(VideoRecord.published_at.desc())
                .limit(limit)
                .all()
            )
            return [row.to_dict() for row in rows]
        finally:
            session.close()

    def topic_was_successful(self, topic: str) -> bool:
        session = self.get_session()
        try:
            return (
                session.query(VideoRecord)
                .filter(VideoRecord.topic == topic, VideoRecord.success.is_(True))
                .first()
                is not None
            )
        finally:
            session.close()
