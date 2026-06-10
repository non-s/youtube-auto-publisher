"""
config.py - Configuracoes centralizadas do projeto
Carrega variaveis de ambiente e define constantes
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
PEXELS_BASE_URL = "https://api.pexels.com/v1"
PEXELS_VIDEO_URL = "https://api.pexels.com/videos"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_TTS_MODEL = os.getenv("GROQ_TTS_MODEL", "playai-tts")
GROQ_TTS_VOICE = os.getenv("GROQ_TTS_VOICE", "Fritz-PlayAI")

EDGE_TTS_VOICES_PTBR = [
    "pt-BR-FranciscaNeural",
    "pt-BR-AntonioNeural",
    "pt-BR-ThalitaNeural",
]

YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
YOUTUBE_TOKEN_JSON = os.getenv("YOUTUBE_TOKEN_JSON", "")
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]
VIDEO_PRIVACY_STATUS = os.getenv("VIDEO_PRIVACY_STATUS", "public")
VIDEO_CATEGORY_ID = os.getenv("VIDEO_CATEGORY_ID", "27")

VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", "1080"))
VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", "1920"))
VIDEO_FPS = int(os.getenv("VIDEO_FPS", "30"))
VIDEO_DURATION = int(os.getenv("VIDEO_DURATION", "35"))
VIDEO_NUM_CLIPS = int(os.getenv("VIDEO_NUM_CLIPS", "5"))

AUDIO_SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE", "44100"))
AUDIO_CHANNELS = int(os.getenv("AUDIO_CHANNELS", "2"))
AUDIO_VOICE_VOLUME = float(os.getenv("AUDIO_VOICE_VOLUME", "1.0"))
AUDIO_MUSIC_VOLUME = float(os.getenv("AUDIO_MUSIC_VOLUME", "0.15"))
AUDIO_FADE_DURATION = int(os.getenv("AUDIO_FADE_DURATION", "3"))

SUBTITLE_FONT = os.getenv("SUBTITLE_FONT", "Arial")
SUBTITLE_FONT_SIZE = int(os.getenv("SUBTITLE_FONT_SIZE", "52"))
SUBTITLE_COLOR = os.getenv("SUBTITLE_COLOR", "white")
SUBTITLE_STROKE_COLOR = os.getenv("SUBTITLE_STROKE_COLOR", "black")
SUBTITLE_STROKE_WIDTH = int(os.getenv("SUBTITLE_STROKE_WIDTH", "2"))
SUBTITLE_POSITION = os.getenv("SUBTITLE_POSITION", "bottom")

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", str(BASE_DIR / "output")))
TEMP_DIR = Path(os.getenv("TEMP_DIR", str(BASE_DIR / "temp")))
MUSIC_DIR = Path(os.getenv("MUSIC_DIR", str(BASE_DIR / "assets" / "music")))
FONTS_DIR = Path(os.getenv("FONTS_DIR", str(BASE_DIR / "assets" / "fonts")))
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

for d in [OUTPUT_DIR, TEMP_DIR, MUSIC_DIR, FONTS_DIR, DATA_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/videos.db")

PUBLISH_TIMES = os.getenv("PUBLISH_TIMES", "08:00,12:00,17:00,20:00")
MAX_VIDEOS_PER_DAY = int(os.getenv("MAX_VIDEOS_PER_DAY", "4"))
ENABLE_AUTO_PUBLISH = os.getenv("ENABLE_AUTO_PUBLISH", "true").lower() == "true"

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = Path(os.getenv("LOG_FILE", str(LOGS_DIR / "app.log")))

CURIOSITY_TOPICS = [
    "curiosidades sobre animais marinhos",
    "fenomenos naturais inexplicaveis",
    "fatos surpreendentes sobre o corpo humano",
    "curiosidades sobre insetos",
    "os animais mais estranhos do planeta",
    "fatos cientificos que vao te surpreender",
    "curiosidades sobre o cerebro humano",
    "os lugares mais extremos da Terra",
    "fatos fascinantes sobre plantas carnivoras",
    "os animais mais velozes do mundo",
    "curiosidades sobre golfinhos",
    "os predadores mais poderosos da natureza",
    "curiosidades sobre aves exoticas",
    "animais com habilidades sobre-humanas",
    "curiosidades sobre tubaroes",
    "os lugares mais perigosos do mundo",
    "fatos sobre o fundo do oceano",
    "curiosidades sobre a Antartica",
    "os desertos mais inospitos da Terra",
    "curiosidades sobre vulcoes",
    "fatos sobre meteoros e asteroides",
    "curiosidades sobre buracos negros",
    "os maiores animais que ja existiram",
    "curiosidades sobre fungos e cogumelos",
]

VIDEO_TOPICS = CURIOSITY_TOPICS
DEFAULT_TOPICS = CURIOSITY_TOPICS

def get_unused_topic(used_topics: list) -> str:
    import random
    available = [t for t in CURIOSITY_TOPICS if t not in used_topics]
    if not available:
        available = CURIOSITY_TOPICS
    return random.choice(available)

def validate_config(require_youtube: bool = True):
    required = {
        "GROQ_API_KEY": GROQ_API_KEY,
        "PEXELS_API_KEY": PEXELS_API_KEY,
    }
    if require_youtube and ENABLE_AUTO_PUBLISH:
        required["YOUTUBE_TOKEN_JSON"] = YOUTUBE_TOKEN_JSON
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise ValueError(f"Variaveis obrigatorias nao configuradas: {', '.join(missing)}")
    return True
