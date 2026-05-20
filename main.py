"""
main.py - Ponto de entrada principal do YouTube Auto Publisher
Orquestra todo o pipeline de criacao e publicacao de videos
"""
import sys
import random
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from loguru import logger
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table
import config

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from pexels_downloader import PexelsDownloader
from voice_generator import VoiceGenerator
from subtitle_generator import SubtitleGenerator
from music_mixer import MusicMixer
from video_editor import VideoEditor
from youtube_uploader import YouTubeUploader

console = Console()


def setup_logging():
      """Configura o sistema de logs"""
      logger.remove()
      logger.add(
          sys.stderr,
          level=config.LOG_LEVEL,
          format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
      )
      logger.add(
          config.LOG_FILE,
          level="DEBUG",
          rotation="10 MB",
          retention="30 days",
          encoding="utf-8",
      )


def create_video(
      topic: str,
      duration: int = 60,
      num_clips: int = 5,
      voice: str = None,
      upload: bool = True,
      dry_run: bool = False,
) -> dict:
      """
          Pipeline completo de criacao e publicacao de video.

                  Args:
                          topic: Topico do video (ex: 'tecnologia', 'natureza')
                                  duration: Duracao alvo em segundos
                                          num_clips: Numero de clipes do Pexels
                                                  voice: Nome da voz (None = aleatoria)
                                                          upload: Se deve publicar no YouTube
                                                                  dry_run: Modo de teste sem publicar

                                                                          Returns:
                                                                                  dict com informacoes do video criado
                                                                                      """
      start_time = datetime.now()
      session_id = start_time.strftime("%Y%m%d_%H%M%S")
      session_dir = config.TEMP_DIR / session_id
      session_dir.mkdir(parents=True, exist_ok=True)

    result = {
              "topic": topic,
              "session_id": session_id,
              "success": False,
              "video_path": None,
              "youtube_id": None,
              "youtube_url": None,
    }

    try:
              console.print(Panel(
                            f"[bold green]Criando video sobre: [cyan]{topic}[/cyan][/bold green]\n"
                            f"Duracao: {duration}s | Clipes: {num_clips} | Sessao: {session_id}",
                            title="YouTube Auto Publisher"
              ))

        # ETAPA 1: Gerar roteiro
              with Progress(SpinnerColumn(), TextColumn("{task.description}")) as p:
                            t = p.add_task("Gerando roteiro com Groq...", total=None)
                            voice_gen = VoiceGenerator()
                            script = voice_gen.generate_script(topic, duration)
                            p.update(t, description="Roteiro gerado!")

              console.print(f"[green]Roteiro:[/green] {script[:100]}...")

        # ETAPA 2: Gerar audio (TTS)
              with Progress(SpinnerColumn(), TextColumn("{task.description}")) as p:
                            t = p.add_task("Gerando narracao (Groq TTS)...", total=None)
                            voice_path = session_dir / "narration.wav"
                            if voice:
                                              voice_gen.generate_audio(script, voice_path, voice=voice)
    else:
                voice_gen.generate_random_voice_audio(script, voice_path)
                  p.update(t, description="Narracao gerada!")

        # ETAPA 3: Gerar legendas
        with Progress(SpinnerColumn(), TextColumn("{task.description}")) as p:
                      t = p.add_task("Gerando legendas (Whisper)...", total=None)
                      sub_gen = SubtitleGenerator(model_size="base")
                      srt_path, subtitles = sub_gen.generate_subtitles_from_audio(
                          voice_path, session_dir
                      )
                      p.update(t, description=f"Legendas geradas! ({len(subtitles)} segmentos)")

        # ETAPA 4: Mixar com musica
        with Progress(SpinnerColumn(), TextColumn("{task.description}")) as p:
                      t = p.add_task("Mixando audio com musica...", total=None)
                      mixer = MusicMixer()
                      mixed_audio_path = session_dir / "mixed_audio.wav"
                      mixed_audio_path = mixer.mix_voice_with_music(
                          voice_path,
                          output_path=mixed_audio_path,
                          topic=topic,
                      )
                      p.update(t, description="Audio mixado!")

        # ETAPA 5: Baixar clipes do Pexels
        with Progress(SpinnerColumn(), TextColumn("{task.description}")) as p:
                      t = p.add_task(f"Baixando clipes do Pexels ({num_clips})...", total=None)
                      downloader = PexelsDownloader()
                      clips_dir = session_dir / "clips"
                      clip_paths = downloader.download_clips_for_topic(
                          topic, num_clips=num_clips, output_dir=clips_dir
                      )
                      if not clip_paths:
                                        # Tenta topico em ingles
                                        clip_paths = downloader.download_clips_for_topic(
                                                              "nature", num_clips=num_clips, output_dir=clips_dir
                                        )
                                    p.update(t, description=f"{len(clip_paths)} clipes baixados!")

        if not clip_paths:
                      raise ValueError("Nenhum clipe de video disponivel")

        # ETAPA 6: Gerar titulo e descricao
        with Progress(SpinnerColumn(), TextColumn("{task.description}")) as p:
                      t = p.add_task("Gerando titulo e descricao (Groq)...", total=None)
            meta = voice_gen.generate_title_and_description(topic, script)
            title = meta.get("title", f"Video sobre {topic}")
            description = meta.get("description", script[:500])
            tags_str = meta.get("tags", topic)
            tags = [t.strip() for t in tags_str.split(",")][:30]
            p.update(t, description="Metadados gerados!")

        # ETAPA 7: Editar video
        with Progress(SpinnerColumn(), TextColumn("{task.description}")) as p:
                      t = p.add_task("Editando video final...", total=None)
            editor = VideoEditor()
            output_filename = f"{topic.replace(' ', '_')}_{session_id}.mp4"
            video_path = editor.create_final_video(
                              clips=clip_paths,
                              audio_path=mixed_audio_path,
                              srt_subtitles=subtitles,
                              output_filename=output_filename,
                              title_text=title,
                              target_duration=float(duration),
            )
            p.update(t, description="Video editado com sucesso!")

        result["video_path"] = str(video_path)

        # Exibe informacoes do video
        table = Table(title="Video Criado")
        table.add_column("Campo", style="cyan")
        table.add_column("Valor", style="white")
        table.add_row("Titulo", title[:60])
        table.add_row("Arquivo", video_path.name)
        table.add_row("Clipes", str(len(clip_paths)))
        table.add_row("Legendas", str(len(subtitles)))
        console.print(table)

        # ETAPA 8: Publicar no YouTube
        if upload and not dry_run:
                      with Progress(SpinnerColumn(), TextColumn("{task.description}")) as p:
                                        t = p.add_task("Publicando no YouTube...", total=None)
                                        uploader = YouTubeUploader()
                                        yt_response = uploader.upload_video(
                                            video_path=video_path,
                                            title=title,
                                            description=description,
                                            tags=tags,
                                        )
                                        youtube_id = yt_response.get("id")
                                        youtube_url = f"https://youtube.com/watch?v={youtube_id}"
                                        result["youtube_id"] = youtube_id
                                        result["youtube_url"] = youtube_url
                                        p.update(t, description="Publicado!")

            console.print(Panel(
                              f"[bold green]Video publicado com sucesso![/bold green]\n"
                              f"[cyan]{youtube_url}[/cyan]",
                              title="Sucesso!"
            ))
elif dry_run:
            console.print("[yellow]Modo dry-run: video nao publicado[/yellow]")

        result["success"] = True
        elapsed = (datetime.now() - start_time).seconds
        console.print(f"\n[green]Concluido em {elapsed}s[/green]")

except Exception as e:
        logger.error(f"Erro ao criar video: {e}")
        console.print(f"[red]Erro: {e}[/red]")
        raise

finally:
        # Limpa arquivos temporarios
          if session_dir.exists():
                        try:
                                          shutil.rmtree(session_dir)
except Exception:
                pass

    return result


def run_scheduler():
      """Executa o agendador de publicacao automatica"""
    import schedule
    import time

    console.print(Panel(
              f"[bold]Agendador iniciado[/bold]\n"
              f"Horario: {config.PUBLISH_SCHEDULE}\n"
              f"Max por dia: {config.MAX_VIDEOS_PER_DAY}",
              title="Scheduler"
    ))

    daily_count = {"date": None, "count": 0}

    def job():
              today = datetime.now().date()
        if daily_count["date"] != today:
                      daily_count["date"] = today
            daily_count["count"] = 0

        if daily_count["count"] >= config.MAX_VIDEOS_PER_DAY:
                      logger.info(f"Limite diario atingido: {config.MAX_VIDEOS_PER_DAY} videos")
            return

        topic = random.choice(config.VIDEO_TOPICS)
        logger.info(f"Agendador: criando video sobre '{topic}'")

        try:
                      create_video(topic=topic, upload=True)
            daily_count["count"] += 1
except Exception as e:
            logger.error(f"Erro no agendador: {e}")

    schedule.every().day.at("10:00").do(job)

    while True:
              schedule.run_pending()
        time.sleep(60)


def main():
      """Ponto de entrada com CLI"""
    setup_logging()

    parser = argparse.ArgumentParser(
              description="YouTube Auto Publisher - Cria e publica videos automaticamente",
              formatter_class=argparse.RawDescriptionHelpFormatter,
              epilog="""
              Exemplos:
                python main.py --topic natureza
                  python main.py --topic tecnologia --duration 90 --clips 6
                    python main.py --topic viagem --dry-run
                      python main.py --schedule
                        python main.py --list-topics
                        """
    )
    parser.add_argument("--topic", "-t", help="Topico do video")
    parser.add_argument("--duration", "-d", type=int, default=60, help="Duracao em segundos (default: 60)")
    parser.add_argument("--clips", "-c", type=int, default=5, help="Numero de clipes (default: 5)")
    parser.add_argument("--voice", "-v", help="Voz para naracao")
    parser.add_argument("--no-upload", action="store_true", help="Nao publicar no YouTube")
    parser.add_argument("--dry-run", action="store_true", help="Modo de teste")
    parser.add_argument("--schedule", "-s", action="store_true", help="Modo agendador")
    parser.add_argument("--list-topics", action="store_true", help="Lista topicos disponiveis")
    parser.add_argument("--list-voices", action="store_true", help="Lista vozes disponiveis")
    parser.add_argument("--channel-info", action="store_true", help="Info do canal")

    args = parser.parse_args()

    if args.list_topics:
              console.print(Panel(
                            "\n".join(f"  [cyan]{t}[/cyan]" for t in config.VIDEO_TOPICS),
                            title="Topicos Disponiveis"
              ))
        return

    if args.list_voices:
              vg = VoiceGenerator()
        console.print(Panel(
                      "\n".join(f"  [cyan]{v}[/cyan]" for v in vg.available_voices),
                      title="Vozes Disponiveis (Groq PlayAI)"
        ))
        return

    if args.channel_info:
              uploader = YouTubeUploader()
        info = uploader.get_channel_info()
        if info:
                      table = Table(title="Informacoes do Canal")
            for k, v in info.items():
                              table.add_row(str(k), str(v))
                          console.print(table)
        return

    if args.schedule:
              run_scheduler()
        return

    # Valida configuracao
    try:
              config.validate_config()
except ValueError as e:
        console.print(f"[red]Configuracao invalida:[/red] {e}")
        console.print("Verifique o arquivo .env com base no .env.example")
        sys.exit(1)

    topic = args.topic
    if not topic:
              topic = random.choice(config.VIDEO_TOPICS)
        console.print(f"[yellow]Topico aleatorio selecionado: [cyan]{topic}[/cyan][/yellow]")

    create_video(
              topic=topic,
              duration=args.duration,
              num_clips=args.clips,
              voice=args.voice,
              upload=not args.no_upload,
              dry_run=args.dry_run,
    )


if __name__ == "__main__":
      main()
