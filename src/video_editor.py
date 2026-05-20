"""
video_editor.py - Edicao e montagem de video
Combina clipes, audio e legendas em video final
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
            from moviepy.editor import (
                VideoFileClip,
                AudioFileClip,
                concatenate_videoclips,
                CompositeVideoClip,
            )
            from moviepy.video.fx.all import resize, fadein, fadeout

            if not clips:
                raise ValueError("Nenhum clipe de video disponivel")

            logger.info(f"Montando video com {len(clips)} clipes...")

            # Carrega e redimensiona clipes
            video_clips = []
            clip_duration = duration / len(clips)

            for clip_path in clips:
                try:
                    clip = VideoFileClip(str(clip_path))
                    # Redimensiona para resolucao alvo
                    clip = clip.resize((self.width, self.height))
                    # Corta ou repete para duração alvo
                    if clip.duration > clip_duration:
                        clip = clip.subclip(0, clip_duration)
                    clip = clip.set_fps(self.fps)
                    video_clips.append(clip)
                except Exception as e:
                    logger.warning(f"Erro ao carregar clipe {clip_path}: {e}")
                    continue

            if not video_clips:
                raise ValueError("Nenhum clipe valido encontrado")

            # Concatena clipes
            final_video = concatenate_videoclips(video_clips, method="compose")

            # Adiciona audio
            if audio_path.exists():
                audio = AudioFileClip(str(audio_path))
                # Ajusta duracao do audio ao video
                if audio.duration > final_video.duration:
                    audio = audio.subclip(0, final_video.duration)
                final_video = final_video.set_audio(audio)

            # Renderiza video
            output_path.parent.mkdir(parents=True, exist_ok=True)
            final_video.write_videofile(
                str(output_path),
                fps=self.fps,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile=str(output_path.parent / "temp_audio.m4a"),
                remove_temp=True,
                verbose=False,
                logger=None,
            )

            # Fecha clipes para liberar memoria
            for clip in video_clips:
                clip.close()
            final_video.close()

            logger.success(f"Video criado: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Erro ao criar video: {e}")
            raise
