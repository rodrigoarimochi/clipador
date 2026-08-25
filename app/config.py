import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
JOBS_DIR = BASE_DIR / "jobs"
OUTPUT_DIR = BASE_DIR / "output"
JOBS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Chave da Anthropic é OPCIONAL. Sem ela, o sistema usa um heurístico
# (palavras de impacto, risadas, pausas, perguntas) pra escolher os cortes.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Modelo do faster-whisper: "tiny", "base", "small", "medium".
# Em VPS free (1-2 vCPU, 1-6GB RAM) use "tiny" ou "base" -- "small" já é pesado.
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "tiny")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

# Quantos clipes gerar por vídeo, e duração alvo (segundos)
MAX_CLIPS = int(os.getenv("MAX_CLIPS", "5"))
CLIP_MIN_SECONDS = int(os.getenv("CLIP_MIN_SECONDS", "20"))
CLIP_MAX_SECONDS = int(os.getenv("CLIP_MAX_SECONDS", "90"))

# Formato de saída: "vertical" (9:16, corta e centraliza pra Reels/Shorts/TikTok)
# ou "original" (mantém o enquadramento original só com legenda)
DEFAULT_FORMAT = os.getenv("DEFAULT_FORMAT", "vertical")
