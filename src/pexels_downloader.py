"""
pexels_downloader.py - Download de videos do Pexels
"""
import os
import random
import requests
from pathlib import Path
import config
from published_ledger import used_clip_ids


class PexelsDownloader:
    """Classe para download de videos do Pexels"""

    def __init__(self):
        self.api_key = config.PEXELS_API_KEY
        self.headers = {"Authorization": self.api_key}
        self.video_url = config.PEXELS_VIDEO_URL
        self.temp_dir = config.TEMP_DIR

    def search_videos(self, query: str, per_page: int = 15) -> list:
        """Busca videos no Pexels"""
        url = f"{self.video_url}/search"
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": "portrait",
            "size": "medium",
        }
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("videos", [])
        except Exception as e:
            print(f"Erro ao buscar videos: {e}")
            return []

    def get_video_download_url(self, video: dict) -> str:
        """Extrai URL de download do video"""
        files = video.get("video_files", [])
        hd_files = [f for f in files if f.get("quality") == "hd"]
        if hd_files:
            return hd_files[0]["link"]
        if files:
            return files[0]["link"]
        return ""

    def download_video(self, url: str, output_path: Path) -> bool:
        """Baixa um video para o caminho especificado"""
        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            print(f"Erro ao baixar video: {e}")
            return False

    def download_clips_for_topic(self, topic: str, output_dir: Path, count: int = 5, num_clips: int | None = None) -> list:
        """Baixa multiplos clipes para um topico"""
        if num_clips is not None:
            count = num_clips
        output_dir.mkdir(parents=True, exist_ok=True)
        topic_translations = {
            "natureza": "nature", "tecnologia": "technology",
            "ciencia": "science", "historia": "history",
            "curiosidades": "curiosities", "saude": "health",
            "fitness": "fitness", "culinaria": "cooking food",
            "animais": "animals wildlife", "espaco": "space universe",
            "oceano": "ocean sea", "viagem": "travel",
        }
        search_query = topic_translations.get(topic.lower(), topic)
        videos = self.search_videos(search_query, per_page=count * 3)
        if not videos:
            videos = self.search_videos("nature wildlife", per_page=count * 3)
        used = used_clip_ids()
        videos = [v for v in videos if str(v.get("id") or "") not in used]
        random.shuffle(videos)
        downloaded = []
        self.last_downloaded_metadata = []
        for i, video in enumerate(videos[:count]):
            download_url = self.get_video_download_url(video)
            if not download_url:
                continue
            output_path = output_dir / f"clip_{i:03d}.mp4"
            if self.download_video(download_url, output_path):
                downloaded.append(output_path)
                self.last_downloaded_metadata.append({
                    "id": str(video.get("id") or ""),
                    "url": video.get("url", ""),
                    "source": "Pexels",
                    "download_url": download_url,
                })
        return downloaded
