"""
Escolhe os melhores trechos do vídeo pra virarem clipes.

Se ANTHROPIC_API_KEY estiver configurada, pede pra IA ler a transcrição
e apontar os trechos mais fortes (gancho, virada, piada, dado forte etc).
Sem a chave, cai num heurístico simples baseado em densidade de fala,
palavras de impacto e perguntas.
"""
import json
import re
from app import config

IMPACT_WORDS = [
    "incrível", "chocante", "segredo", "erro", "nunca", "sempre",
    "verdade", "mentira", "dinheiro", "grátis", "rápido", "fácil",
    "difícil", "importante", "cuidado", "atenção", "olha", "gente",
]


def _heuristic_highlights(segments: list[dict], video_duration: float) -> list[dict]:
    scored = []
    for seg in segments:
        text = seg["text"].lower()
        score = 0.0
        score += len(re.findall(r"\?", text)) * 2  # perguntas prendem atenção
        score += len(re.findall(r"!", text)) * 1.5
        score += sum(1 for w in IMPACT_WORDS if w in text)
        dur = max(seg["end"] - seg["start"], 0.1)
        density = len(text.split()) / dur
        score += density  # fala mais densa/dinâmica tende a "prender"
        scored.append({"start": seg["start"], "end": seg["end"], "text": seg["text"], "score": score})

    scored.sort(key=lambda s: s["score"], reverse=True)
    return _expand_to_clips(scored, video_duration)


def _expand_to_clips(scored_segments: list[dict], video_duration: float) -> list[dict]:
    """Pega os picos de score e expande até formar clipes de duração aceitável,
    evitando sobreposição entre eles."""
    clips = []
    used_ranges = []

    def overlaps(a_start, a_end):
        return any(not (a_end < r[0] or a_start > r[1]) for r in used_ranges)

    for seg in scored_segments:
        if len(clips) >= config.MAX_CLIPS:
            break
        if overlaps(seg["start"], seg["end"]):
            continue

        start = max(seg["start"] - 3, 0)
        end = min(seg["end"] + config.CLIP_MIN_SECONDS, video_duration)
        if end - start < config.CLIP_MIN_SECONDS:
            end = min(start + config.CLIP_MIN_SECONDS, video_duration)
        end = min(start + config.CLIP_MAX_SECONDS, end, video_duration)

        if end - start < 8:  # curto demais, ignora
            continue
        if overlaps(start, end):
            continue

        used_ranges.append((start, end))
        clips.append({"start": start, "end": end, "reason": seg["text"][:120]})

    return clips


def _ai_highlights(segments: list[dict], video_duration: float, title: str) -> list[dict]:
    from anthropic import Anthropic

    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    transcript_txt = "\n".join(
        f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}" for s in segments
    )
    # Se o vídeo for muito longo, corta pra não estourar contexto
    if len(transcript_txt) > 60000:
        transcript_txt = transcript_txt[:60000]

    prompt = f"""Você é um editor profissional de clipes virais (estilo cortes de podcast/live).
Título do vídeo: "{title}"
Duração total: {video_duration:.0f}s

Aqui está a transcrição com timestamps:
{transcript_txt}

Escolha até {config.MAX_CLIPS} trechos com o MAIOR potencial de viralizar como clipe
independente (gancho forte no início, ideia fechada, emoção, virada, dado surpreendente
ou piada). Cada clipe deve ter entre {config.CLIP_MIN_SECONDS} e {config.CLIP_MAX_SECONDS} segundos.
Não deixe os clipes se sobreporem.

Responda APENAS com um JSON válido, neste formato exato, sem texto antes ou depois:
[{{"start": 12.3, "end": 45.0, "reason": "explicação curta de por que esse trecho viraliza"}}]
"""

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    text = re.sub(r"^```json|```$", "", text, flags=re.MULTILINE).strip()
    clips = json.loads(text)
    return [c for c in clips if 0 <= c["start"] < c["end"] <= video_duration][: config.MAX_CLIPS]


def select_highlights(segments: list[dict], video_duration: float, title: str) -> list[dict]:
    if config.ANTHROPIC_API_KEY:
        try:
            clips = _ai_highlights(segments, video_duration, title)
            if clips:
                return clips
        except Exception:
            pass  # cai pro heurístico se a IA falhar por qualquer motivo
    return _heuristic_highlights(segments, video_duration)
