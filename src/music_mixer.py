"""
music_mixer.py - Mixer de musica de fundo para videos
Seleciona e mixa musicas CC0 com controle de volume e fade
"""
import os
import random
from pathlib import Path
from typing import Optional, List
from pydub import AudioSegment
from pydub.effects import normalize
from loguru import logger
import config


class MusicMixer:
      """Gerencia e mixa musicas de fundo para videos"""

    MUSIC_CATEGORIES = {
              "motivacional": ["uplifting", "energetic", "inspirational"],
              "relaxante": ["ambient", "calm", "peaceful"],
              "tecnologia": ["electronic", "futuristic", "digital"],
              "natureza": ["acoustic", "natural", "organic"],
              "drama": ["cinematic", "epic", "dramatic"],
    }

    # URLs de musicas CC0 gratuitas do Free Music Archive / ccMixter
    FREE_MUSIC_SOURCES = [
              "https://freemusicarchive.org/api/",
              "https://ccmixter.org/api/",
    ]

    def __init__(self):
              self.music_dir = config.MUSIC_DIR
              self.voice_volume = config.AUDIO_VOICE_VOLUME
              self.music_volume = config.AUDIO_MUSIC_VOLUME
              self.fade_duration = config.AUDIO_FADE_DURATION * 1000  # ms

    def get_available_tracks(self) -> List[Path]:
              """Lista todas as faixas de musica disponiveis"""
              extensions = [".mp3", ".wav", ".ogg", ".flac", ".m4a"]
              tracks = []
              for ext in extensions:
                            tracks.extend(self.music_dir.glob(f"*{ext}"))
                        logger.info(f"{len(tracks)} faixas de musica encontradas")
        return tracks

    def select_music_for_topic(self, topic: str) -> Optional[Path]:
              """Seleciona musica mais adequada para o topico"""
        tracks = self.get_available_tracks()
        if not tracks:
                      logger.warning("Nenhuma musica disponivel em: " + str(self.music_dir))
                      return None
                  # Tenta encontrar musica com nome relacionado ao topico
                  topic_words = topic.lower().split()
        for track in tracks:
                      track_name = track.stem.lower()
                      if any(word in track_name for word in topic_words):
                                        logger.info(f"Musica selecionada por topico: {track.name}")
                                        return track
                                # Seleciona aleatoriamente
                                selected = random.choice(tracks)
        logger.info(f"Musica selecionada aleatoriamente: {selected.name}")
        return selected

    def load_audio(self, audio_path: Path) -> AudioSegment:
              """Carrega arquivo de audio"""
        suffix = audio_path.suffix.lower()
        format_map = {".mp3": "mp3", ".wav": "wav", ".ogg": "ogg",
                                            ".flac": "flac", ".m4a": "mp4"}
        fmt = format_map.get(suffix, "mp3")
        return AudioSegment.from_file(str(audio_path), format=fmt)

    def adjust_music_duration(
              self,
              music: AudioSegment,
              target_duration_ms: int,
    ) -> AudioSegment:
              """Ajusta duracao da musica ao video (loop ou corte)"""
        if len(music) < target_duration_ms:
                      loops_needed = (target_duration_ms // len(music)) + 1
            music = music * loops_needed
        music = music[:target_duration_ms]
        return music

    def apply_fade(
              self,
              audio: AudioSegment,
              fade_in_ms: int = 2000,
              fade_out_ms: int = 3000,
    ) -> AudioSegment:
              """Aplica fade in/out na musica"""
        return audio.fade_in(fade_in_ms).fade_out(fade_out_ms)

    def mix_voice_with_music(
              self,
              voice_path: Path,
              music_path: Optional[Path] = None,
              output_path: Optional[Path] = None,
              topic: str = "",
    ) -> Path:
              """Mixa naracao com musica de fundo"""
        voice = self.load_audio(voice_path)
        voice = normalize(voice)
        voice = voice + (20 * (self.voice_volume - 1))
        # Seleciona musica
        if music_path is None:
                      music_path = self.select_music_for_topic(topic)
        if music_path is None:
                      logger.warning("Sem musica disponivel, usando apenas a voz")
            if output_path is None:
                              output_path = voice_path.parent / f"mixed_{voice_path.name}"
                          voice.export(str(output_path), format="wav")
            return output_path
        logger.info(f"Mixando voz com musica: {music_path.name}")
        music = self.load_audio(music_path)
        music = normalize(music)
        # Ajusta volume da musica
        music_db_adjust = 20 * (self.music_volume - 1) - 6
        music = music + music_db_adjust
        # Ajusta duracao
        music = self.adjust_music_duration(music, len(voice) + self.fade_duration)
        music = self.apply_fade(music, self.fade_duration, self.fade_duration)
        # Mistura
        mixed = voice.overlay(music, position=0)
        # Exporta
        if output_path is None:
                      output_path = voice_path.parent / f"mixed_{voice_path.stem}.wav"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        mixed.export(str(output_path), format="wav")
        logger.success(f"Audio mixado: {output_path} ({len(mixed)/1000:.1f}s)")
        return output_path

    def create_dynamic_audio(
              self,
              voice_path: Path,
              segments: list,
              output_path: Optional[Path] = None,
    ) -> Path:
              """Cria audio dinamico com variacao de musica por segmento"""
        voice = self.load_audio(voice_path)
        voice = normalize(voice)
        available_tracks = self.get_available_tracks()
        if not available_tracks:
                      return self.mix_voice_with_music(voice_path, output_path=output_path)
        final_audio = AudioSegment.silent(duration=len(voice))
        segment_duration = len(voice) // max(len(segments), 1)
        for i, segment in enumerate(segments):
                      start_ms = i * segment_duration
            end_ms = min(start_ms + segment_duration, len(voice))
            track = random.choice(available_tracks)
            music = self.load_audio(track)
            music_db = 20 * (self.music_volume - 0.7) - 6
            music = music + music_db
            music = self.adjust_music_duration(music, end_ms - start_ms)
            music = self.apply_fade(music, 500, 500)
            final_audio = final_audio.overlay(music, position=start_ms)
        mixed = voice.overlay(final_audio)
        if output_path is None:
                      output_path = voice_path.parent / f"dynamic_{voice_path.stem}.wav"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        mixed.export(str(output_path), format="wav")
        logger.success(f"Audio dinamico criado: {output_path}")
        return output_path
