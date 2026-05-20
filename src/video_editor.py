"""
video_editor.py - Edicao e montagem de video
Combina clipes, audio e legendas em video final
Compativel com moviepy 2.x
"""
import random
from pathlib import Path
from loguru import logger
import config


class VideoEditor:
    """Editor de video completo com efeitos e legendas"""

    def __init__(self):
        self.width = config.VIDEO_WIDTH
        self.height = config.VIDEO_HEIGHT
        self.fps = config.VIDEO_FPS

    def create_video(
        self,
        clips: list,
        audio_path: Path,
        srt_path: Path,
        output_path: Path,
        duration: int = 60,
    ) -> Path:
        """Monta o video final com clipes, audio e legendas"""
        try:
            # moviepy 2.x usa importacao direta
            from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips

            if not clips:
                raise ValueError("Nenhum clipe de video disponivel")

            logger.info(f"Montando video com {len(clips)} clipes...")

            clip_duration = duration / len(clips)
            video_clips = []

            for clip_path in clips:
                try:
                    clip = VideoFileClip(str(clip_path))
                    # Redimensiona para resolucao alvo mantendo proporcao
                    clip = clip.resized((self.width, self.height))
                    # Corta para duracao alvo
                    if clip.duration > clip_duration:
                        clip = clip.subclipped(0, clip_duration)
                    video_clips.append(clip)
                except Exception as e:
                    logger.warning(f"Erro ao carregar clipe {clip_path.name}: {e}")
                    continue

            if not video_clips:
                raise ValueError("Nenhum clipe valido encontrado")

            # Concatena clipes
            final_video = concatenate_videoclips(video_clips, method="compose")

            # Adiciona audio
            if audio_path and audio_path.exists():
                audio = AudioFileClip(str(audio_path))
                if audio.duration > final_video.duration:
                    audio = audio.subclipped(0, final_video.duration)
                final_video = final_video.with_audio(audio)

            # Renderiza video
            output_path.parent.mkdir(parents=True, exist_ok=True)
            final_video.write_videofile(
                str(output_path),
                fps=self.fps,
                codec="libx264",
                audio_codec="aac",
                logger=None,
            )

            # Libera memoria
            for clip in video_clips:
                clip.close()
            final_video.close()

            logger.success(f"Video criado: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Erro ao criar video: {e}")
            raise
