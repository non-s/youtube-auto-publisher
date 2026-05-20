"""
subtitle_generator.py - Geracao de legendas sincronizadas
Usa Whisper da OpenAI para transcrever audio e gerar legendas SRT
"""
import srt
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
        """Carrega o modelo Whisper sob demanda"""
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
        srt_content = srt.compose(subtitles)
        output_path.write_text(srt_content, encoding="utf-8")
        logger.success(f"Legendas salvas: {output_path} ({len(subtitles)} segmentos)")
        return output_path

    def generate_subtitles_from_audio(
        self, audio_path: Path, output_dir: Path
    ) -> tuple:
        """Pipeline completo: audio -> transcricao -> arquivo SRT"""
        try:
            transcription = self.transcribe_audio(audio_path)
            subtitles = self.create_srt_subtitles(transcription)

            srt_path = output_dir / "subtitles.srt"
            self.save_srt_file(subtitles, srt_path)

            return srt_path, subtitles

        except Exception as e:
            logger.error(f"Erro ao gerar legendas: {e}")
            # Retorna legenda vazia em caso de erro
            return output_dir / "subtitles.srt", []
