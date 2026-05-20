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

        # ETAPA 4: Baixar clipes do Pexels
        with Progress(SpinnerColumn(), TextColumn("{task.description}")) as p:
            t = p.add_task("Baixando clipes do Pexels...", total=None)
            downloader = PexelsDownloader()
            clips = downloader.download_clips_for_topic(topic, session_dir, count=num_clips)
            p.update(t, description=f"Clipes baixados! ({len(clips)} clipes)")

        # ETAPA 5: Mixar musica
        with Progress(SpinnerColumn(), TextColumn("{task.description}")) as p:
            t = p.add_task("Mixando audio com musica...", total=None)
            mixer = MusicMixer()
            mixed_audio = mixer.mix_with_background(voice_path, session_dir)
            p.update(t, description="Audio mixado!")

        # ETAPA 6: Editar video
        with Progress(SpinnerColumn(), TextColumn("{task.description}")) as p:
            t = p.add_task("Editando video...", total=None)
            editor = VideoEditor()
            output_path = session_dir / f"output_{session_id}.mp4"
            editor.create_video(
                clips=clips,
                audio_path=mixed_audio,
                srt_path=srt_path,
                output_path=output_path,
                duration=duration,
            )
            p.update(t, description="Video editado!")

        result["video_path"] = str(output_path)

        if dry_run:
            console.print("[yellow]Modo dry-run: video criado mas nao publicado[/yellow]")
            result["success"] = True
            return result

        # ETAPA 7: Publicar no YouTube
        if upload:
            with Progress(SpinnerColumn(), TextColumn("{task.description}")) as p:
                t = p.add_task("Publicando no YouTube...", total=None)
                uploader = YouTubeUploader()

                # Gerar titulo e descricao
                meta = voice_gen.generate_title_and_description(topic, script)
                title = meta.get("title", f"Video sobre {topic}")
                description = meta.get("description", script[:500])
                tags = meta.get("tags", [topic])

                video_id = uploader.upload_video(
                    video_path=output_path,
                    title=title,
                    description=description,
                    tags=tags,
                    privacy_status=config.VIDEO_PRIVACY_STATUS,
                )
                p.update(t, description=f"Publicado! ID: {video_id}")

            result["youtube_id"] = video_id
            result["youtube_url"] = f"https://youtu.be/{video_id}"
            console.print(f"[bold green]Video publicado:[/bold green] {result['youtube_url']}")

        result["success"] = True

    except Exception as e:
        logger.error(f"Erro no pipeline: {e}")
        console.print(f"[bold red]Erro:[/bold red] {e}")
        raise

    finally:
        # Limpar arquivos temporarios
        if session_dir.exists():
            shutil.rmtree(session_dir, ignore_errors=True)

    elapsed = (datetime.now() - start_time).seconds
    console.print(f"[green]Concluido em {elapsed}s[/green]")

    return result


def run_scheduler(interval_hours: int = 24):
    """Executa o publisher em loop com intervalo definido"""
    import time
    topics = config.DEFAULT_TOPICS if hasattr(config, 'DEFAULT_TOPICS') else [
        "natureza", "tecnologia", "ciencia", "historia", "curiosidades"
    ]

    console.print(f"[bold]Iniciando scheduler - intervalo: {interval_hours}h[/bold]")

    while True:
        topic = random.choice(topics)
        try:
            create_video(topic=topic, upload=True)
        except Exception as e:
            logger.error(f"Erro no scheduler: {e}")

        console.print(f"[dim]Aguardando {interval_hours}h...[/dim]")
        time.sleep(interval_hours * 3600)


def main():
    """Ponto de entrada principal"""
    setup_logging()

    parser = argparse.ArgumentParser(
        description="YouTube Auto Publisher - Cria e publica videos automaticamente"
    )
    parser.add_argument("--topic", type=str, default=None, help="Topico do video")
    parser.add_argument("--duration", type=int, default=60, help="Duracao em segundos")
    parser.add_argument("--clips", type=int, default=5, help="Numero de clipes")
    parser.add_argument("--voice", type=str, default=None, help="Nome da voz TTS")
    parser.add_argument("--no-upload", action="store_true", help="Nao publicar no YouTube")
    parser.add_argument("--dry-run", action="store_true", help="Modo teste sem publicar")
    parser.add_argument("--schedule", action="store_true", help="Modo agendador")
    parser.add_argument("--interval", type=int, default=24, help="Intervalo em horas")

    args = parser.parse_args()

    if args.schedule:
        run_scheduler(interval_hours=args.interval)
        return

    topic = args.topic
    if not topic:
        topics = ["natureza", "tecnologia", "ciencia", "historia", "curiosidades"]
        topic = random.choice(topics)
        console.print(f"[dim]Topico aleatorio: {topic}[/dim]")

    result = create_video(
        topic=topic,
        duration=args.duration,
        num_clips=args.clips,
        voice=args.voice,
        upload=not args.no_upload,
        dry_run=args.dry_run,
    )

    # Exibir resultado
    table = Table(title="Resultado")
    table.add_column("Campo", style="cyan")
    table.add_column("Valor", style="green")
    table.add_row("Topico", result["topic"])
    table.add_row("Sucesso", str(result["success"]))
    table.add_row("Video", result["video_path"] or "N/A")
    table.add_row("YouTube ID", result["youtube_id"] or "N/A")
    table.add_row("URL", result["youtube_url"] or "N/A")
    console.print(table)


if __name__ == "__main__":
    main()
