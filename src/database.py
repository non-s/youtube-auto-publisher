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
              video_path: str = None,
              duration_seconds: int = None,
              clips_count: int = None,
              subtitles_count: int = None,
              voice_used: str = None,
              success: bool = False,
              error_message: str = None,
    ) -> VideoRecord:
              """Salva registro de video no banco"""
              import json
              session = self.get_session()
              try:
                            record = VideoRecord(
                                              session_id=session_id,
                                              topic=topic,
                                              title=title,
                                              description=description,
                                              tags=json.dumps(tags or []),
                                              youtube_id=youtube_id,
                                              youtube_url=youtube_url,
                                              video_path=str(video_path) if video_path else None,
                                              duration_seconds=duration_seconds,
                                              clips_count=clips_count,
                                              subtitles_count=subtitles_count,
                                              voice_used=voice_used,
                                              success=success,
                                              error_message=error_message,
                            )
                            session.add(record)
                            session.commit()
                            logger.info(f"Video salvo no banco: {session_id}")
                            return record
except Exception as e:
            session.rollback()
            logger.error(f"Erro ao salvar video: {e}")
            raise
finally:
            session.close()

    def get_videos(
              self,
              limit: int = 10,
              topic: str = None,
              success_only: bool = False,
    ) -> List[VideoRecord]:
              """Lista videos publicados"""
              session = self.get_session()
              try:
                            query = session.query(VideoRecord)
                            if topic:
                                              query = query.filter(VideoRecord.topic == topic)
                                          if success_only:
                                                            query = query.filter(VideoRecord.success == True)
                                                        return query.order_by(VideoRecord.published_at.desc()).limit(limit).all()
finally:
            session.close()

    def get_stats(self) -> Dict:
              """Retorna estatisticas gerais"""
              session = self.get_session()
              try:
                            total = session.query(VideoRecord).count()
                            successful = session.query(VideoRecord).filter(VideoRecord.success == True).count()
                            return {
                                "total_videos": total,
                                "successful": successful,
                                "failed": total - successful,
                                "success_rate": f"{(successful/total*100):.1f}%" if total > 0 else "0%",
                            }
finally:
            session.close()

    def get_topics_count(self) -> Dict[str, int]:
              """Retorna contagem de videos por topico"""
              from sqlalchemy import func
              session = self.get_session()
              try:
                            results = session.query(
                                              VideoRecord.topic,
                                              func.count(VideoRecord.id)
                            ).group_by(VideoRecord.topic).all()
                            return {topic: count for topic, count in results}
finally:
            session.close()

    def update_video_stats(
              self,
              youtube_id: str,
              views: int = 0,
              likes: int = 0,
    ) -> bool:
              """Atualiza estatisticas do video"""
              session = self.get_session()
              try:
                            record = session.query(VideoRecord).filter(
                                              VideoRecord.youtube_id == youtube_id
                            ).first()
                            if record:
                                              record.views = views
                                              record.likes = likes
                                              session.commit()
                                              return True
                                          return False
finally:
            session.close()
