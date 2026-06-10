"""
youtube_uploader.py - Upload de videos para o YouTube
Gerencia autenticacao OAuth e upload via YouTube Data API v3
"""
import json
import os
import random
import time
from pathlib import Path
from loguru import logger
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import config


SCOPES = config.YOUTUBE_SCOPES
TOKEN_FILE = Path("token.json")
CLIENT_SECRETS_FILE = Path("client_secrets.json")
RETRIABLE_STATUS_CODES = {500, 502, 503, 504}
MAX_RETRIES = 6


class YouTubeUploader:
    """Gerencia upload de videos para o YouTube"""

    def __init__(self):
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Autentica com a API do YouTube"""
        creds = None

        # 1. Tenta usar token do GitHub Secret (CI/CD)
        token_json_str = config.YOUTUBE_TOKEN_JSON
        if token_json_str:
            try:
                token_data = json.loads(token_json_str)
                creds = Credentials.from_authorized_user_info(token_data, SCOPES)
                logger.info("Usando token do ambiente (GitHub Secret)")
            except Exception as e:
                logger.warning(f"Erro ao carregar token do ambiente: {e}")

        # 2. Tenta usar token.json local
        if not creds and TOKEN_FILE.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
                logger.info("Usando token local (token.json)")
            except Exception as e:
                logger.warning(f"Erro ao carregar token local: {e}")

        # 3. Renova token expirado
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("Token renovado com sucesso")
                # Salva token renovado
                TOKEN_FILE.write_text(creds.to_json())
            except Exception as e:
                logger.error(f"Erro ao renovar token: {e}")
                creds = None

        # 4. Fluxo OAuth interativo (apenas local)
        if not creds or not creds.valid:
            if os.getenv("GITHUB_ACTIONS") == "true":
                raise RuntimeError("Token YouTube invalido no CI. Gere um novo YOUTUBE_TOKEN_JSON.")
            if CLIENT_SECRETS_FILE.exists():
                logger.info("Iniciando fluxo OAuth interativo...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CLIENT_SECRETS_FILE), SCOPES
                )
                creds = flow.run_local_server(port=0)
                TOKEN_FILE.write_text(creds.to_json())
                logger.success(f"Token salvo em {TOKEN_FILE}")
            else:
                # Tenta usar client_id/secret do ambiente
                client_config = {
                    "installed": {
                        "client_id": config.YOUTUBE_CLIENT_ID,
                        "client_secret": config.YOUTUBE_CLIENT_SECRET,
                        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                }
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                creds = flow.run_local_server(port=0)
                TOKEN_FILE.write_text(creds.to_json())
                logger.success(f"Token salvo em {TOKEN_FILE}")

        self.service = build("youtube", "v3", credentials=creds, cache_discovery=False)
        logger.success("Autenticado com YouTube API v3")

    def check_auth(self) -> bool:
        """Validate credentials before rendering a video."""
        if not self.service:
            return False
        self.service.channels().list(part="id", mine=True).execute()
        logger.success("Preflight YouTube OK")
        return True

    def upload_video(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: list = None,
        privacy_status: str = "private",
        category_id: str = None,
    ) -> str:
        """Faz upload de video para o YouTube e retorna o ID do video"""
        if not self.service:
            raise RuntimeError("Servico YouTube nao autenticado")

        cat_id = category_id or config.VIDEO_CATEGORY_ID

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags or [],
                "categoryId": cat_id,
                "defaultLanguage": "pt",
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            resumable=True,
            chunksize=1024 * 1024 * 5,  # 5 MB chunks
        )

        logger.info(f"Iniciando upload: '{title[:50]}'...")
        request = self.service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        retry = 0
        while response is None:
            try:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"Upload: {progress}%")
            except HttpError as exc:
                if exc.resp.status not in RETRIABLE_STATUS_CODES:
                    raise
                retry += 1
                if retry > MAX_RETRIES:
                    raise RuntimeError(f"Upload falhou apos retries: HTTP {exc.resp.status}") from exc
                sleep_for = random.uniform(1, 2 ** retry)
                logger.warning(f"Upload HTTP {exc.resp.status}; retry em {sleep_for:.1f}s")
                time.sleep(sleep_for)
            except (OSError, TimeoutError) as exc:
                retry += 1
                if retry > MAX_RETRIES:
                    raise RuntimeError(f"Upload falhou apos retries: {exc}") from exc
                sleep_for = random.uniform(1, 2 ** retry)
                logger.warning(f"Upload instavel; retry em {sleep_for:.1f}s: {exc}")
                time.sleep(sleep_for)

        video_id = response.get("id")
        logger.success(f"Video publicado! ID: {video_id}")
        logger.success(f"URL: https://youtu.be/{video_id}")
        return {"id": video_id, "url": f"https://youtu.be/{video_id}"}

    def add_to_playlist(self, video_id: str, playlist_title: str) -> dict:
        """Create/find a playlist and add the uploaded video."""
        playlist_id = None
        response = self.service.playlists().list(part="snippet", mine=True, maxResults=50).execute()
        for item in response.get("items", []):
            if (item.get("snippet") or {}).get("title") == playlist_title:
                playlist_id = item.get("id")
                break
        if not playlist_id:
            created = self.service.playlists().insert(
                part="snippet,status",
                body={
                    "snippet": {"title": playlist_title, "description": "Videos organizados automaticamente."},
                    "status": {"privacyStatus": "public"},
                },
            ).execute()
            playlist_id = created.get("id")
        item = self.service.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {"kind": "youtube#video", "videoId": video_id},
                }
            },
        ).execute()
        return {"playlist_id": playlist_id, "playlist_item_id": item.get("id")}

    def post_comment(self, video_id: str, text: str) -> dict:
        """Post a first CTA comment. Pinning is not exposed by the official API."""
        response = self.service.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {"snippet": {"textOriginal": text[:500]}},
                }
            },
        ).execute()
        return {"comment_thread_id": response.get("id"), "pin_status": "not_supported_by_youtube_data_api"}

    def get_channel_info(self) -> dict:
        """Retorna informacoes do canal autenticado"""
        try:
            response = self.service.channels().list(
                part="snippet,statistics",
                mine=True,
            ).execute()
            items = response.get("items", [])
            if items:
                channel = items[0]
                return {
                    "id": channel["id"],
                    "name": channel["snippet"]["title"],
                    "subscribers": channel["statistics"].get("subscriberCount", "N/A"),
                    "videos": channel["statistics"].get("videoCount", "N/A"),
                    "views": channel["statistics"].get("viewCount", "N/A"),
                }
        except Exception as e:
            logger.error(f"Erro ao obter info do canal: {e}")
        return {}
