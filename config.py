"""
config.py - Configuracoes centralizadas do projeto
Carrega variaveis de ambiente e define constantes
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variaveis do .env
load_dotenv()

BASE_DIR = Path(__file__).parent

# ===== PEXELS =====
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
PEXELS_BASE_URL = "https://api.pexels.com/v1"
PEXELS_VIDEO_URL = "https://api.pexels.com/videos"

# ===== GROQ =====
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")
GROQ_TTS_MODEL = os.getenv("GROQ_TTS_MODEL", "playai-tts")
GROQ_TTS_VOICE = os.getenv("GROQ_TTS_VOICE", "Fritz-PlayAI")
GROQ_TTS_VOICES = [
      "Fritz-PlayAI",
      "Aaliyah-PlayAI",
      "Adelaide-PlayAI",
      "Angelo-PlayAI",
      "Arsenio-PlayAI",
      "Briggs-PlayAI",
      "Calum-PlayAI",
      "Celeste-PlayAI",
]

# ===== MISTRAL =====
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-large-latest")

# ===== YOUTUBE =====
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
YOUTUBE_REDIRECT_URI = os.getenv("YOUTUBE_REDIRECT_URI", "http://localhost:8080")
YOUTUBE_TOKEN_FILE = os.getenv("YOUTUBE_TOKEN_FILE", "token.json")
YOUTUBE_CREDENTIALS_FILE = os.getenv("YOUTUBE_CREDENTIALS_FILE", "credentials.json")
YOUTUBE_SCOPES = [
      "https://www.googleapis.com/auth/youtube.upload",
      "https://www.googleapis.com/auth/youtube",
      "https://www.googleapis.com/auth/youtube.force-ssl",
]

# ===== VIDEO =====
VIDEO_LANGUAGE = os.getenv("VIDEO_LANGUAGE", "pt-BR")
VIDEO_CATEGORY_ID = int(os.getenv("VIDEO_CATEGORY_ID", "22"))
VIDEO_PRIVACY_STATUS = os.getenv("VIDEO_PRIVACY_STATUS", "public")
VIDEO_MAX_DURATION = int(os.getenv("VIDEO_MAX_DURATION", "60"))
VIDEO_MIN_DURATION = int(os.getenv("VIDEO_MIN_DURATION", "30"))
VIDEO_RESOLUTION = os.getenv("VIDEO_RESOLUTION", "1920x1080")
VIDEO_FPS = int(os.getenv("VIDEO_FPS", "30"))

# ===== AUDIO =====
AUDIO_VOICE_VOLUME = float(os.getenv("AUDIO_VOICE_VOLUME", "1.0"))
AUDIO_MUSIC_VOLUME = float(os.getenv("AUDIO_MUSIC_VOLUME", "0.3"))
AUDIO_FADE_DURATION = int(os.getenv("AUDIO_FADE_DURATION", "2"))

# ===== LEGENDAS =====
SUBTITLE_FONT = os.getenv("SUBTITLE_FONT", "Arial")
SUBTITLE_FONT_SIZE = int(os.getenv("SUBTITLE_FONT_SIZE", "48"))
SUBTITLE_COLOR = os.getenv("SUBTITLE_COLOR", "white")
SUBTITLE_STROKE_COLOR = os.getenv("SUBTITLE_STROKE_COLOR", "black")
SUBTITLE_STROKE_WIDTH = int(os.getenv("SUBTITLE_STROKE_WIDTH", "2"))
SUBTITLE_POSITION = os.getenv("SUBTITLE_POSITION", "bottom")

# ===== CAMINHOS =====
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", str(BASE_DIR / "output")))
TEMP_DIR = Path(os.getenv("TEMP_DIR", str(BASE_DIR / "temp")))
MUSIC_DIR = Path(os.getenv("MUSIC_DIR", str(BASE_DIR / "assets" / "music")))
FONTS_DIR = Path(os.getenv("FONTS_DIR", str(BASE_DIR / "assets" / "fonts")))
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Cria diretorios se nao existirem
for d in [OUTPUT_DIR, TEMP_DIR, MUSIC_DIR, FONTS_DIR, DATA_DIR, LOGS_DIR]:
      d.mkdir(parents=True, exist_ok=True)

# ===== BANCO DE DADOS =====
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/videos.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# ===== PUBLICACAO =====
PUBLISH_SCHEDULE = os.getenv("PUBLISH_SCHEDULE", "0 10 * * *")
MAX_VIDEOS_PER_DAY = int(os.getenv("MAX_VIDEOS_PER_DAY", "3"))
ENABLE_AUTO_PUBLISH = os.getenv("ENABLE_AUTO_PUBLISH", "true").lower() == "true"

# ===== LOGS =====
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = Path(os.getenv("LOG_FILE", str(LOGS_DIR / "app.log")))

# ===== TOPICOS DE VIDEO =====
VIDEO_TOPICS = [
      "natureza", "viagem", "tecnologia", "culinaria",
      "saude", "fitness", "negocios", "motivacao",
      "cultura", "historia", "ciencia", "arte",
]

# ===== VALIDACAO =====
def validate_config():
      """Valida as configuracoes obrigatorias"""
      required = {
          "PEXELS_API_KEY": PEXELS_API_KEY,
          "GROQ_API_KEY": GROQ_API_KEY,
          "YOUTUBE_CLIENT_ID": YOUTUBE_CLIENT_ID,
          "YOUTUBE_CLIENT_SECRET": YOUTUBE_CLIENT_SECRET,
      }
      missing = [k for k, v in required.items() if not v]
      if missing:
                raise ValueError(f"Variaveis obrigatorias nao configuradas: {', '.join(missing)}")
            return True
