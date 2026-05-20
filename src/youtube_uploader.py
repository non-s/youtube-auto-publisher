"""
youtube_uploader.py - Upload e publicacao no YouTube
Gerencia autenticacao OAuth2 e upload de videos
"""
import os
import time
import json
from pathlib import Path
from typing import Optional, List
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
import config


class YouTubeUploader:
      """Gerencia autenticacao e upload para o YouTube"""

    UPLOAD_CHUNK_SIZE = 256 * 1024  # 256KB
    MAX_RETRIES = 10
    RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
    RETRIABLE_EXCEPTIONS = (Exception,)

    def __init__(self):
              self.credentials_file = Path(config.YOUTUBE_CREDENTIALS_FILE)
              self.token_file = Path(config.YOUTUBE_TOKEN_FILE)
              self.scopes = config.YOUTUBE_SCOPES
              self._service = None

    def authenticate(self) -> Credentials:
              """Autentica com OAuth2 e retorna credenciais"""
              creds = None
              if self.token_file.exists():
                            creds = Credentials.from_authorized_user_file(
                                              str(self.token_file), self.scopes
                            )
                        if not creds or not creds.valid:
                                      if creds and creds.expired and creds.refresh_token:
                                                        logger.info("Renovando token de acesso...")
                                                        creds.refresh(Request())
                        else:
                logger.info("Iniciando fluxo de autenticacao OAuth2...")
                                          if not self.credentials_file.exists():
                                                                raise FileNotFoundError(
                                                                                          f"Arquivo de credenciais nao encontrado: {self.credentials_file}\n"
                                                                                          "Baixe o arquivo credentials.json do Google Cloud Console."
                                                                )
                                                            flow = InstalledAppFlow.from_client_secrets_file(
                                                                                  str(self.credentials_file), self.scopes
                                                            )
                creds = flow.run_local_server(port=8080)
            with open(self.token_file, "w") as f:
                              f.write(creds.to_json())
                          logger.success("Autenticacao concluida e token salvo")
        return creds

    @property
    def service(self):
              if self._service is None:
                            creds = self.authenticate()
                            self._service = build("youtube", "v3", credentials=creds)
                        return self._service

    def upload_video(
              self,
              video_path: Path,
              title: str,
              description: str,
              tags: List[str],
              category_id: int = None,
              privacy_status: str = None,
              thumbnail_path: Optional[Path] = None,
              language: str = None,
    ) -> dict:
              """Faz upload de video para o YouTube"""
        category_id = category_id or config.VIDEO_CATEGORY_ID
        privacy_status = privacy_status or config.VIDEO_PRIVACY_STATUS
        language = language or config.VIDEO_LANGUAGE
        if not video_path.exists():
                      raise FileNotFoundError(f"Video nao encontrado: {video_path}")
                  logger.info(f"Iniciando upload: {video_path.name}")
        logger.info(f"Titulo: {title[:60]}...")
        body = {
                      "snippet": {
                                        "title": title[:100],
                                        "description": description[:5000],
                                        "tags": tags[:500],
                                        "categoryId": str(category_id),
                                        "defaultLanguage": language.split("-")[0],
                                        "defaultAudioLanguage": language.split("-")[0],
                      },
                      "status": {
                                        "privacyStatus": privacy_status,
                                        "selfDeclaredMadeForKids": False,
                      },
        }
        media = MediaFileUpload(
                      str(video_path),
                      mimetype="video/mp4",
                      chunksize=self.UPLOAD_CHUNK_SIZE,
                      resumable=True,
        )
        insert_request = self.service.videos().insert(
                      part="snippet,status",
                      body=body,
                      media_body=media,
        )
        response = self._resumable_upload(insert_request)
        video_id = response.get("id")
        logger.success(f"Video publicado! ID: {video_id}")
        logger.info(f"URL: https://www.youtube.com/watch?v={video_id}")
        # Upload thumbnail
        if thumbnail_path and thumbnail_path.exists() and video_id:
                      self.upload_thumbnail(video_id, thumbnail_path)
                  return response

    def _resumable_upload(self, insert_request) -> dict:
              """Executa upload resumivel com retry automatico"""
        response = None
        error = None
        retry_count = 0
        while response is None:
                      try:
                                        logger.info(f"Fazendo upload... (tentativa {retry_count + 1})")
                                        status, response = insert_request.next_chunk()
                                        if status:
                                                              progress = int(status.progress() * 100)
                                                              logger.info(f"Upload: {progress}%")
                      except Exception as e:
                                        error = e
                                        retry_count += 1
                                        if retry_count > self.MAX_RETRIES:
                                                              raise Exception(f"Upload falhou apos {self.MAX_RETRIES} tentativas: {e}")
                                                          sleep_time = 2 ** retry_count
                                        logger.warning(f"Erro no upload, aguardando {sleep_time}s: {e}")
                                        time.sleep(sleep_time)
                                return response

    def upload_thumbnail(
              self,
              video_id: str,
              thumbnail_path: Path,
    ) -> dict:
              """Faz upload da thumbnail do video"""
        logger.info(f"Fazendo upload da thumbnail para video {video_id}")
        media = MediaFileUpload(
                      str(thumbnail_path),
                      mimetype="image/jpeg",
        )
        response = self.service.thumbnails().set(
                      videoId=video_id,
                      media_body=media,
        ).execute()
        logger.success("Thumbnail atualizada com sucesso")
        return response

    def get_channel_info(self) -> dict:
              """Retorna informacoes do canal"""
        response = self.service.channels().list(
                      part="snippet,statistics",
                      mine=True,
        ).execute()
        items = response.get("items", [])
        if items:
                      channel = items[0]
            info = {
                              "id": channel["id"],
                              "title": channel["snippet"]["title"],
                              "subscribers": channel["statistics"].get("subscriberCount", 0),
                              "views": channel["statistics"].get("viewCount", 0),
                              "videos": channel["statistics"].get("videoCount", 0),
            }
            logger.info(f"Canal: {info['title']} | {info['subscribers']} inscritos")
            return info
        return {}

    def list_uploaded_videos(
              self,
              max_results: int = 10,
    ) -> List[dict]:
              """Lista videos publicados no canal"""
        response = self.service.search().list(
                      part="snippet",
                      forMine=True,
                      type="video",
                      order="date",
                      maxResults=max_results,
        ).execute()
        videos = []
        for item in response.get("items", []):
                      videos.append({
                          "id": item["id"]["videoId"],
                          "title": item["snippet"]["title"],
                          "published_at": item["snippet"]["publishedAt"],
                          "url": f"https://youtube.com/watch?v={item['id']['videoId']}",
        })
        return videos
