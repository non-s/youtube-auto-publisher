# YouTube Auto Publisher

Automacao para criar e publicar Shorts de curiosidades no YouTube usando Groq, Pexels, Edge TTS, Whisper e YouTube Data API v3.

O canal foi desenhado para curiosidades gerais, nao para um nicho unico. Os temas sao organizados em pilares editoriais:

- Espaco e Universo
- Corpo e Mente
- Historia Misteriosa
- Ciencia Rapida
- Tecnologia e Futuro
- Natureza Extrema
- Mundo Curioso

## Pipeline

```text
Topico -> roteiro Groq -> narracao Edge TTS -> legendas Whisper
-> clipes Pexels portrait -> edicao vertical -> quality gate -> upload YouTube
-> playlist por pilar -> comentario CTA -> ledger de clipes publicados
```

## Requisitos

- Python 3.10+
- FFmpeg
- `GROQ_API_KEY`
- `PEXELS_API_KEY`
- `YOUTUBE_TOKEN_JSON` quando `ENABLE_AUTO_PUBLISH=true`

O token do YouTube precisa cobrir estes escopos:

- `https://www.googleapis.com/auth/youtube.upload`
- `https://www.googleapis.com/auth/youtube.readonly`
- `https://www.googleapis.com/auth/youtube.force-ssl`
- `https://www.googleapis.com/auth/yt-analytics.readonly`

## Configuracao

```bash
pip install -r requirements.txt
cp .env.example .env
```

Configure os secrets no GitHub Actions com os mesmos nomes do `.env.example`.

## Uso

```bash
python main.py --status
python main.py --list-topics
python main.py --topic "curiosidades sobre buracos negros" --no-upload
python main.py --topic "segredos da Roma antiga" --dry-run
python main.py --check-auth
python main.py --schedule
```

Por padrao, o projeto gera Shorts verticais em `1080x1920`, com duracao curta e ate 4 publicacoes por dia.

## Protecoes

- Bloqueio de roteiro curto, generico ou lento demais para Shorts.
- Bloqueio de metadata fraca.
- Dedupe de clipes ja usados no ledger `data/published_clips.json`.
- Persistencia de estado depois do upload.
- OAuth interativo desativado no GitHub Actions.
- Retries no upload resumivel do YouTube.
- CI com compile, testes, auth preflight e artefatos de diagnostico.

## Desenvolvimento

```bash
python -m compileall -q .
python -m pytest -q
python main.py --status
```

Arquivos sensiveis como `.env`, tokens, credenciais e bancos locais ficam fora do Git.
