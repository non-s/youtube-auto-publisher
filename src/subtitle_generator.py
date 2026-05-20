"""
subtitle_generator.py - Geracao de legendas sincronizadas
Usa Whisper da OpenAI para transcrever audio e gerar legendas SRT.
Tambem gera legendas sinteticas como fallback quando Whisper falha.
"""
import srt
import re
from pathlib import Path
from datetime import timedelta
from loguru import logger
import config


class SubtitleGenerator:
    """Gera legendas sincronizadas com o audio"""

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._model = None
        self.language = "pt"

    @property
    def model(self):
        if self._model is None:
            import whisper
            logger.info(f"Carregando modelo Whisper '{self.model_size}'...")
            self._model = whisper.load_model(self.model_size)
        return self._model

    def transcribe_audio(self, audio_path: Path) -> dict:
        """Transcreve audio usando Whisper"""
        logger.info(f"Transcrevendo audio: {audio_path}")
        result = self.model.transcribe(
            str(audio_path),
            language=self.language,
            task="transcribe",
            word_timestamps=True,
        )
        return result

    def create_srt_subtitles(self, transcription: dict) -> list:
        """Converte transcricao Whisper em objetos SRT"""
        subtitles = []
        index = 1
        for segment in transcription.get("segments", []):
            start = timedelta(seconds=segment["start"])
            end = timedelta(seconds=segment["end"])
            text = segment["text"].strip()
            if text:
                subtitle = srt.Subtitle(
                    index=index,
                    start=start,
                    end=end,
                    content=text,
                )
                subtitles.append(subtitle)
                index += 1
        return subtitles

    def save_srt_file(self, subtitles: list, output_path: Path) -> Path:
        """Salva legendas em arquivo SRT"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if not subtitles:
            output_path.write_text("", encoding="utf-8")
            logger.warning("Legendas vazias - arquivo SRT em branco criado")
            return output_path
        srt_content = srt.compose(subtitles)
        output_path.write_text(srt_content, encoding="utf-8")
        logger.success(f"Legendas salvas: {output_path} ({len(subtitles)} segmentos)")
        return output_path

    def generate_synthetic_subtitles(
        self, script: str, audio_path: Path, output_dir: Path,
        words_per_second: float = 2.3
    ) -> tuple:
        """
        Gera legendas sinteticas a partir do roteiro quando Whisper falha.
        Distribui o texto ao longo da duracao estimada do audio.
        """
        logger.info("Gerando legendas sinteticas do roteiro...")
        # Estima duracao do audio
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(str(audio_path))
            total_duration = len(audio) / 1000.0
        except Exception:
            words = len(script.split())
            total_duration = words / words_per_second

        # Divide o roteiro em segmentos de ~8-10 palavras
        words = script.split()
        chunk_size = 8
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)

        if not chunks:
            return output_dir / "subtitles.srt", []

        time_per_chunk = total_duration / len(chunks)
        subtitles = []
        for i, chunk in enumerate(chunks):
            start_sec = i * time_per_chunk
            end_sec = min((i + 1) * time_per_chunk, total_duration)
            subtitle = srt.Subtitle(
                index=i + 1,
                start=timedelta(seconds=start_sec),
                end=timedelta(seconds=end_sec - 0.1),
                content=chunk,
            )
            subtitles.append(subtitle)

        srt_path = output_dir / "subtitles.srt"
        self.save_srt_file(subtitles, srt_path)
        logger.success(f"Legendas sinteticas geradas: {len(subtitles)} segmentos")
        return srt_path, subtitles

    def generate_subtitles_from_audio(
        self, audio_path: Path, output_dir: Path
    ) -> tuple:
        """Pipeline completo: audio -> transcricao Whisper -> arquivo SRT"""
        try:
            transcription = self.transcribe_audio(audio_path)
            subtitles = self.create_srt_subtitles(transcription)
            srt_path = output_dir / "subtitles.srt"
            self.save_srt_file(subtitles, srt_path)
            if len(subtitles) == 0:
                logger.warning("Whisper retornou legendas vazias")
            return srt_path, subtitles
        except Exception as e:
            logger.error(f"Erro ao gerar legendas com Whisper: {e}")
            # Retorna arquivo vazio - main.py vai chamar generate_synthetic_subtitles
            empty_path = output_dir / "subtitles.srt"
            empty_path.parent.mkdir(parents=True, exist_ok=True)
            empty_path.write_text("", encoding="utf-8")
            return empty_path, []
