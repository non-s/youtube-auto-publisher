"""
database.py - Gerenciamento do banco de dados SQLite
Armazena historico de videos publicados e estatisticas
"""
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from loguru import logger
import config

Base = declarative_base()


class VideoRecord(Base):
    """Modelo de registro de video publicado"""
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), unique=True, nullable=False)
    topic = Column(String(200), nullable=False)
    title = Column(String(500))
    description = Column(Text)
    tags = Column(Text)  # JSON
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


class DatabaseManager:
    """Gerenciador do banco de dados"""

    def __init__(self, db_url: str = None):
        self.db_url = db_url or config.DATABASE_URL
        self.engine = create_engine(self.db_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info(f"Banco de dados inicializado: {self.db_url}")

    def get_session(self) -> Session:
        return self.SessionLocal()

    def save_video(
        self,
        session_id: str,
        topic: str,
        title: str = None,
        description: str = None,
        tags: list = None,
        youtube_id: str = None,
        youtube_url: str = None,
