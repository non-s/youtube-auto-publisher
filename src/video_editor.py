"""
video_editor.py - Editor de video principal
Combina clipes do Pexels, audio, legendas e efeitos visuais
"""
import random
from pathlib import Path
from typing import List, Optional, Tuple
from loguru import logger
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip,
    CompositeAudioClip, concatenate_videoclips,
    TextClip, ImageClip, ColorClip,
)
from moviepy.video.fx import resize, fadein, fadeout
from moviepy.audio.fx.all import audio_fadein, audio_fadeout
import config


class VideoEditor:
      """Editor de video completo com efeitos dinamicos"""

    TRANSITIONS = ["fade", "slide_left", "slide_right", "zoom_in", "zoom_out"]
    TEXT_ANIMATIONS = ["fade", "slide_up", "typewriter"]

    def __init__(self):
              self.output_dir = config.OUTPUT_DIR
              self.temp_dir = config.TEMP_DIR
              self.fps = config.VIDEO_FPS
              resolution = config.VIDEO_RESOLUTION.split("x")
              self.width = int(resolution[0])
              self.height = int(resolution[1])
              self.font = config.SUBTITLE_FONT
              self.font_size = config.SUBTITLE_FONT_SIZE
              self.subtitle_color = config.SUBTITLE_COLOR
              self.stroke_color = config.SUBTITLE_STROKE_COLOR
              self.stroke_width = config.SUBTITLE_STROKE_WIDTH

    def load_clip(self, clip_path: Path, target_duration: Optional[float] = None) -> VideoFileClip:
              """Carrega e processa um clipe de video"""
              clip = VideoFileClip(str(clip_path))
              # Redimensiona para resolucao alvo
              clip = clip.resize((self.width, self.height))
              # Corta para duracao alvo se necessario
              if target_duration and clip.duration > target_duration:
                            clip = clip.subclip(0, target_duration)
                        return clip

    def apply_zoom_effect(
              self, clip: VideoFileClip, zoom_ratio: float = 0.04
    ) -> VideoFileClip:
              """Aplica efeito Ken Burns (zoom lento) no clipe"""
        def zoom(t):
                      return 1 + zoom_ratio * t / clip.duration
                  return clip.resize(zoom)

    def apply_transition(
              self,
              clip: VideoFileClip,
              transition_type: str = "fade",
              duration: float = 0.5,
    ) -> VideoFileClip:
              """Aplica transicao ao clipe"""
        if transition_type == "fade":
                      clip = clip.fadein(duration).fadeout(duration)
elif transition_type == "zoom_in":
            clip = self.apply_zoom_effect(clip, 0.03)
            clip = clip.fadein(duration)
elif transition_type == "zoom_out":
            def zoom_out(t):
                              return 1.04 - 0.04 * t / clip.duration
                          clip = clip.resize(zoom_out).fadeout(duration)
        return clip

    def create_subtitle_clip(
              self,
              text: str,
              start: float,
              end: float,
              video_size: Tuple[int, int],
              animation: str = "fade",
    ) -> TextClip:
              """Cria clip de legenda animada"""
        duration = end - start
        txt_clip = TextClip(
                      text,
                      font=self.font,
                      fontsize=self.font_size,
                      color=self.subtitle_color,
                      stroke_color=self.stroke_color,
                      stroke_width=self.stroke_width,
                      method="caption",
                      size=(int(video_size[0] * 0.85), None),
                      align="center",
        )
        # Posiciona na parte inferior
        margin = int(video_size[1] * 0.08)
        txt_clip = txt_clip.set_position(
                      ("center", video_size[1] - txt_clip.h - margin)
        )
        txt_clip = txt_clip.set_start(start).set_duration(duration)
        # Aplica animacao
        if animation == "fade":
                      fade_t = min(0.15, duration / 3)
                      txt_clip = txt_clip.fadein(fade_t).fadeout(fade_t)
elif animation == "slide_up":
              def slide_pos(t):
                                y_base = video_size[1] - txt_clip.h - margin
                                slide_amt = 20
                                progress = min(t / 0.3, 1)
                                return ("center", y_base + slide_amt * (1 - progress))
                            txt_clip = txt_clip.set_position(slide_pos)
        return txt_clip

    def add_subtitles_to_video(
              self,
              video: CompositeVideoClip,
              srt_subtitles: list,
              animation: str = "fade",
    ) -> CompositeVideoClip:
              """Adiciona legendas ao video"""
        subtitle_clips = []
        for subtitle in srt_subtitles:
                      start = subtitle.start.total_seconds()
                      end = subtitle.end.total_seconds()
                      if end > video.duration:
                                        end = video.duration
                                    if start >= video.duration:
                                                      continue
                                                  text = subtitle.content.strip()
            if not text:
                              continue
                          txt_clip = self.create_subtitle_clip(
                                            text=text,
                                            start=start,
                                            end=end,
                                            video_size=(self.width, self.height),
                                            animation=animation,
                          )
            subtitle_clips.append(txt_clip)
        logger.info(f"Adicionando {len(subtitle_clips)} legendas")
        return CompositeVideoClip([video] + subtitle_clips)

    def add_dynamic_text_overlay(
              self,
              video: CompositeVideoClip,
              title: str,
              duration: float = 3.0,
    ) -> CompositeVideoClip:
              """Adiciona titulo animado no inicio do video"""
        title_clip = TextClip(
                      title,
                      font=self.font,
                      fontsize=int(self.font_size * 1.3),
                      color="white",
                      stroke_color="black",
                      stroke_width=3,
                      method="caption",
                      size=(int(self.width * 0.8), None),
                      align="center",
        )
        title_clip = title_clip.set_position(("center", "center"))
        title_clip = title_clip.set_start(0.5).set_duration(duration)
        title_clip = title_clip.fadein(0.5).fadeout(0.5)
        return CompositeVideoClip([video, title_clip])

    def add_watermark(
              self,
              video: CompositeVideoClip,
              watermark_text: str = "",
              opacity: float = 0.7,
    ) -> CompositeVideoClip:
              """Adiciona marca d'agua ao video"""
        if not watermark_text:
                      return video
        wm_clip = TextClip(
                      watermark_text,
                      font=self.font,
                      fontsize=24,
                      color="white",
        ).set_opacity(opacity)
        wm_clip = wm_clip.set_position(("right", "top"), relative=False)
        wm_clip = wm_clip.margin(right=20, top=20, opacity=0)
        wm_clip = wm_clip.set_duration(video.duration)
        return CompositeVideoClip([video, wm_clip])

    def concatenate_clips(
              self,
              clips: List[VideoFileClip],
              method: str = "compose",
              apply_random_effects: bool = True,
    ) -> CompositeVideoClip:
              """Concatena clipes com transicoes dinamicas"""
        processed_clips = []
        for i, clip in enumerate(clips):
                      # Aplica efeito aleatorio
                      if apply_random_effects:
                                        effect = random.choice(["zoom_in", "fade", "zoom_out"])
                                        clip = self.apply_transition(clip, effect)
                                    processed_clips.append(clip)
        logger.info(f"Concatenando {len(processed_clips)} clipes")
        return concatenate_videoclips(processed_clips, method=method)

    def create_final_video(
              self,
              clips: List[Path],
              audio_path: Path,
              srt_subtitles: Optional[list] = None,
              output_filename: str = "final_video.mp4",
              title_text: str = "",
              watermark: str = "",
              target_duration: Optional[float] = None,
    ) -> Path:
              """Pipeline completo de criacao do video final"""
        logger.info("Iniciando criacao do video final...")
        # Carrega e processa clipes
        video_clips = []
        for clip_path in clips:
                      try:
                                        duration_per_clip = None
                                        if target_duration:
                                                              duration_per_clip = target_duration / len(clips) + 2
                                                          clip = self.load_clip(clip_path, duration_per_clip)
                video_clips.append(clip)
except Exception as e:
                logger.error(f"Erro ao carregar clipe {clip_path}: {e}")
        if not video_clips:
                      raise ValueError("Nenhum clipe de video valido encontrado")
        # Concatena clipes
        video = self.concatenate_clips(video_clips)
        # Carrega audio
        logger.info("Adicionando audio...")
        audio = AudioFileClip(str(audio_path))
        # Ajusta duracao do video ao audio
        if video.duration < audio.duration:
                      loops = int(audio.duration / video.duration) + 1
            video = concatenate_videoclips([video] * loops)
        video = video.subclip(0, audio.duration)
        video = video.set_audio(audio)
        # Adiciona titulo
        if title_text:
                      video = self.add_dynamic_text_overlay(video, title_text)
        # Adiciona legendas
        if srt_subtitles:
                      logger.info("Adicionando legendas...")
            anim = random.choice(self.TEXT_ANIMATIONS)
            video = self.add_subtitles_to_video(video, srt_subtitles, anim)
        # Adiciona watermark
        if watermark:
                      video = self.add_watermark(video, watermark)
        # Exporta
        output_path = self.output_dir / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Exportando video: {output_path}")
        video.write_videofile(
                      str(output_path),
                      fps=self.fps,
                      codec="libx264",
                      audio_codec="aac",
                      threads=4,
                      preset="fast",
                      verbose=False,
                      logger=None,
        )
        # Libera memoria
        video.close()
        audio.close()
        for clip in video_clips:
                      clip.close()
        logger.success(f"Video criado com sucesso: {output_path}")
        return output_path
