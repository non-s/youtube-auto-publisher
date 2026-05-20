"""
subtitle_generator.py - Geracao de legendas automaticas
Usa Whisper para transcricao e gera SRT com timestamps
"""
import re
import srt
from pathlib import Path
from datetime import timedelta
from typing import List, Optional, Tuple
from loguru import logger
import whisper
import config


class SubtitleGenerator:
      """Gera legendas sincronizadas com o audio"""

    def __init__(self, model_size: str = "base"):
              self.model_size = model_size
              self._model = None
              self.language = config.VIDEO_LANGUAGE

    @property
    def model(self):
              if self._model is None:
                            logger.info(f"Carregando modelo Whisper '{self.model_size}'...")
                            self._model = whisper.load_model(self.model_size)
                        return self._model

    def transcribe_audio(
              self,
              audio_path: Path,
              language: Optional[str] = None,
    ) -> dict:
              """Transcreve audio usando Whisper"""
        lang = language or self.language
        lang_code = lang.split("-")[0] if "-" in lang else lang
        logger.info(f"Transcrevendo audio: {audio_path.name}")
        result = self.model.transcribe(
                      str(audio_path),
                      language=lang_code,
                      word_timestamps=True,
                      verbose=False,
        )
        logger.success(f"Transcricao concluida: {len(result['segments'])} segmentos")
        return result

    def create_srt_from_whisper(
              self,
              transcription: dict,
              max_chars_per_line: int = 42,
              max_words_per_subtitle: int = 8,
    ) -> List[srt.Subtitle]:
              """Cria subtitles SRT a partir da transcricao do Whisper"""
        subtitles = []
        subtitle_index = 1
        for segment in transcription.get("segments", []):
                      words = segment.get("words", [])
                      if not words:
                                        start = timedelta(seconds=segment["start"])
                                        end = timedelta(seconds=segment["end"])
                                        text = segment["text"].strip()
                                        if text:
                                                              subtitles.append(srt.Subtitle(
                                                                                        index=subtitle_index,
                                                                                        start=start,
                                                                                        end=end,
                                                                                        content=text,
                                                              ))
                                                              subtitle_index += 1
                                                          continue
                                    # Agrupa palavras por limite de caracteres/palavras
                                    current_words = []
            for word_data in words:
                              current_words.append(word_data)
                combined_text = " ".join(w["word"].strip() for w in current_words)
                should_break = (
                                      len(current_words) >= max_words_per_subtitle or
                                      len(combined_text) >= max_chars_per_line
                )
                if should_break and len(current_words) > 1:
                                      group = current_words[:-1]
                    start = timedelta(seconds=group[0]["start"])
                    end = timedelta(seconds=group[-1]["end"])
                    text = " ".join(w["word"].strip() for w in group)
                    subtitles.append(srt.Subtitle(
                                              index=subtitle_index,
                                              start=start,
                                              end=end,
                                              content=text,
                    ))
                    subtitle_index += 1
                    current_words = [current_words[-1]]
            # Ultimo grupo
            if current_words:
                              start = timedelta(seconds=current_words[0]["start"])
                end = timedelta(seconds=current_words[-1]["end"])
                text = " ".join(w["word"].strip() for w in current_words)
                subtitles.append(srt.Subtitle(
                                      index=subtitle_index,
                                      start=start,
                                      end=end,
                                      content=text,
                ))
                subtitle_index += 1
        return subtitles

    def save_srt(
              self,
              subtitles: List[srt.Subtitle],
              output_path: Path,
    ) -> Path:
              """Salva legendas em arquivo SRT"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        srt_content = srt.compose(subtitles)
        with open(output_path, "w", encoding="utf-8") as f:
                      f.write(srt_content)
        logger.success(f"SRT salvo: {output_path} ({len(subtitles)} legendas)")
        return output_path

    def generate_subtitles_from_audio(
              self,
              audio_path: Path,
              output_dir: Optional[Path] = None,
    ) -> Tuple[Path, List[srt.Subtitle]]:
              """Pipeline completo: audio -> transcricao -> SRT"""
        if output_dir is None:
                      output_dir = config.TEMP_DIR
        transcription = self.transcribe_audio(audio_path)
        subtitles = self.create_srt_from_whisper(transcription)
        srt_path = output_dir / audio_path.stem
        srt_path = srt_path.with_suffix(".srt")
        self.save_srt(subtitles, srt_path)
        return srt_path, subtitles

    def format_subtitle_for_display(
              self,
              text: str,
              max_width: int = 40,
    ) -> str:
              """Formata texto da legenda para exibicao"""
        words = text.split()
        lines = []
        current_line = []
        for word in words:
                      if sum(len(w) for w in current_line) + len(current_line) + len(word) <= max_width:
                                        current_line.append(word)
else:
                if current_line:
                                      lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
                      lines.append(" ".join(current_line))
        return "\n".join(lines)
