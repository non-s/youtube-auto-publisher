"""
music_mixer.py - Mixagem de audio com musica de fundo
Combina narracao com musica ambiente para criar audio engajante
"""
import random
from pathlib import Path
from loguru import logger
import config


class MusicMixer:
    """Gerencia e mixa musicas de fundo para videos"""

    MUSIC_CATEGORIES = {
        "motivacional": ["uplifting", "energetic", "inspiring"],
        "relaxante": ["ambient", "calm", "peaceful"],
        "tecnologia": ["electronic", "futuristic", "digital"],
        "natureza": ["acoustic", "natural", "organic"],
        "aventura": ["epic", "cinematic", "dramatic"],
    }

    TOPIC_MUSIC_MAP = {
        "natureza": "relaxante",
        "tecnologia": "tecnologia",
        "ciencia": "motivacional",
        "historia": "aventura",
        "curiosidades": "motivacional",
        "saude": "relaxante",
        "fitness": "motivacional",
        "culinaria": "relaxante",
        "animais": "natureza",
        "espaco": "aventura",
        "oceano": "relaxante",
        "viagem": "aventura",
    }

    def find_music_files(self) -> list:
        """Encontra arquivos de musica no diretorio de assets"""
        music_dir = config.MUSIC_DIR
        extensions = [".mp3", ".wav", ".ogg", ".flac"]
        files = []
        for ext in extensions:
            files.extend(music_dir.glob(f"*{ext}"))
        return files

    def mix_with_background(
        self,
        voice_path: Path,
        output_dir: Path,
        topic: str = None,
        voice_volume: float = None,
        music_volume: float = None,
    ) -> Path:
        """Mixa naracao com musica de fundo"""
        from pydub import AudioSegment

        voice_vol = voice_volume or config.AUDIO_VOICE_VOLUME
        music_vol = music_volume or config.AUDIO_MUSIC_VOLUME
        fade_dur = config.AUDIO_FADE_DURATION * 1000  # ms

        output_path = output_dir / "mixed_audio.wav"

        try:
            # Carrega naracao
            voice = AudioSegment.from_file(str(voice_path))
            voice = voice + (20 * (voice_vol - 1))  # ajusta volume

            # Tenta usar musica de fundo
            music_files = self.find_music_files()
            if music_files:
                music_file = random.choice(music_files)
                music = AudioSegment.from_file(str(music_file))

                # Repete musica se necessario
                while len(music) < len(voice):
                    music = music + music

                music = music[:len(voice)]
                music = music - (20 * (1 - music_vol))  # reduz volume da musica
                music = music.fade_in(fade_dur).fade_out(fade_dur)

                mixed = voice.overlay(music)
                logger.info(f"Musica mixada: {music_file.name}")
            else:
                # Sem musica, usa apenas a naracao
                mixed = voice
                logger.warning("Nenhuma musica encontrada, usando apenas naracao")

            output_path.parent.mkdir(parents=True, exist_ok=True)
            mixed.export(str(output_path), format="wav")
            logger.success(f"Audio mixado salvo: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Erro ao mixar audio: {e}")
            # Fallback: retorna naracao original
            import shutil
            shutil.copy(voice_path, output_path)
            return output_path
