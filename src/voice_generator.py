"""
voice_generator.py - Geracao de voz com Groq TTS
Converte texto em audio usando a API Groq PlayAI TTS
"""
import random
from pathlib import Path
from typing import Optional
from groq import Groq
from loguru import logger
import config


class VoiceGenerator:
      """Gera narracoes em voz usando Groq TTS"""

    def __init__(self):
              self.client = Groq(api_key=config.GROQ_API_KEY)
              self.model = config.GROQ_TTS_MODEL
              self.default_voice = config.GROQ_TTS_VOICE
              self.available_voices = config.GROQ_TTS_VOICES

    def generate_audio(
              self,
              text: str,
              output_path: Path,
              voice: Optional[str] = None,
              speed: float = 1.0,
    ) -> Path:
              """Gera audio a partir de texto usando Groq TTS"""
              voice = voice or self.default_voice
              logger.info(f"Gerando audio com voz '{voice}': {text[:50]}...")
              response = self.client.audio.speech.create(
                  model=self.model,
                  voice=voice,
                  input=text,
                  response_format="wav",
              )
              output_path.parent.mkdir(parents=True, exist_ok=True)
              response.stream_to_file(str(output_path))
              logger.success(f"Audio gerado: {output_path}")
              return output_path

    def generate_script(
              self,
              topic: str,
              duration_seconds: int = 60,
              style: str = "engajante e dinamico",
              language: str = "pt-BR",
    ) -> str:
              """Gera roteiro de naracao usando Groq LLM"""
              words_per_minute = 150
              target_words = int((duration_seconds / 60) * words_per_minute)
              prompt = f"""Crie um roteiro de naracao em {language} sobre o tema: '{topic}'.

      O roteiro deve ter aproximadamente {target_words} palavras e ser {style}.
      Regras:
      - Use linguagem simples e clara
      - Seja envolvente e mantenha o espectador interessado
      - Inclua fatos interessantes ou dicas praticas
      - Termine com uma chamada para acao (curtir, comentar, se inscrever)
      - NAO inclua instrucoes de cena ou direcoes
      - Escreva APENAS o texto para ser narrado

      Escreva SOMENTE o texto da narracao, sem titulos ou marcacoes."""

        completion = self.client.chat.completions.create(
                      model=config.GROQ_MODEL,
                      messages=[
                                        {
                                                              "role": "system",
                                                              "content": "Voce e um roteirista especialista em videos curtos virais para YouTube."
                                        },
                                        {"role": "user", "content": prompt}
                      ],
                      temperature=0.8,
                      max_tokens=1000,
        )
        script = completion.choices[0].message.content.strip()
        logger.info(f"Roteiro gerado: {len(script.split())} palavras")
        return script

    def generate_random_voice_audio(
              self,
              text: str,
              output_path: Path,
    ) -> Path:
              """Gera audio com uma voz aleatoria"""
              voice = random.choice(self.available_voices)
              return self.generate_audio(text, output_path, voice=voice)

    def generate_title_and_description(self, topic: str, script: str) -> dict:
              """Gera titulo e descricao otimizados para SEO usando Groq"""
              prompt = f"""Com base no roteiro sobre '{topic}', crie:
      1. Um titulo chamativo e otimizado para SEO (max 100 chars)
      2. Uma descricao completa com hashtags (max 5000 chars)
      3. Tags separadas por virgula (max 500 chars)

      Formato de resposta (JSON):
      {{
        "title": "titulo aqui",
        "description": "descricao aqui",
        "tags": "tag1,tag2,tag3"
      }}

      Roteiro: {script[:500]}"""

        completion = self.client.chat.completions.create(
                      model=config.GROQ_MODEL,
                      messages=[
                                        {
                                                              "role": "system",
                                                              "content": "Voce e um especialista em SEO para YouTube. Responda APENAS com JSON valido."
                                        },
                                        {"role": "user", "content": prompt}
                      ],
                      temperature=0.7,
                      max_tokens=800,
                      response_format={"type": "json_object"},
        )
        import json
        result = json.loads(completion.choices[0].message.content)
        logger.info(f"Titulo gerado: {result.get('title', '')[:50]}")
        return result
