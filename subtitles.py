"""Gera legendas .ass com destaque palavra-por-palavra (estilo CapCut/Opus Clip)."""
from pathlib import Path

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat Black,72,&H00FFFFFF,&H0000D7FF,&H00101010,&H00000000,-1,0,0,0,100,100,0,0,1,6,0,2,60,60,220,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _fmt_time(t: float) -> str:
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def _group_words_into_lines(words: list[dict], max_words_per_line=4) -> list[list[dict]]:
    lines, current = [], []
    for w in words:
        current.append(w)
        if len(current) >= max_words_per_line or w["word"].strip().endswith((".", "!", "?")):
            lines.append(current)
            current = []
    if current:
        lines.append(current)
    return lines


def build_ass(words: list[dict], clip_start: float, clip_end: float, out_path: Path):
    """Recebe as palavras (timestamps ABSOLUTOS do vídeo original) e gera o .ass
    já reancorado no tempo 0 do clipe (clip_start vira 0)."""
    clip_words = [w for w in words if clip_start <= w["start"] < clip_end]
    lines = _group_words_into_lines(clip_words)

    events = []
    for line in lines:
        line_start = line[0]["start"] - clip_start
        line_end = line[-1]["end"] - clip_start
        # Cria um evento por PALAVRA, mas reescreve a linha toda a cada vez,
        # destacando (cor accent) só a palavra ativa -> efeito karaokê.
        for i, w in enumerate(line):
            w_start = w["start"] - clip_start
            w_end = w["end"] - clip_start
            parts = []
            for j, w2 in enumerate(line):
                word_txt = w2["word"].strip()
                if j == i:
                    parts.append("{\\c&H00D7FF&}" + word_txt + "{\\c&HFFFFFF&}")
                else:
                    parts.append(word_txt)
            text = " ".join(parts)
            events.append(
                f"Dialogue: 0,{_fmt_time(w_start)},{_fmt_time(w_end)},Default,,0,0,0,,{text}"
            )

    out_path.write_text(ASS_HEADER + "\n".join(events), encoding="utf-8")
    return out_path
