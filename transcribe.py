"""Transcreve o áudio com timestamp POR PALAVRA (necessário pra legenda estilo karaokê)."""
from faster_whisper import WhisperModel
from app import config

_model = None


def get_model():
    global _model
    if _model is None:
        _model = WhisperModel(
            config.WHISPER_MODEL,
            device=config.WHISPER_DEVICE,
            compute_type=config.WHISPER_COMPUTE_TYPE,
        )
    return _model


def transcribe(video_path: str) -> list[dict]:
    """
    Retorna uma lista de palavras:
    [{"word": "oi", "start": 0.12, "end": 0.34}, ...]
    e também os segmentos (frases) originais em "segments".
    """
    model = get_model()
    segments, _info = model.transcribe(
        video_path,
        word_timestamps=True,
        vad_filter=True,  # remove silêncio, ajuda a achar picos de fala
        language=None,  # auto-detecta (funciona bem com PT-BR)
    )

    words = []
    seg_list = []
    for seg in segments:
        seg_list.append({"start": seg.start, "end": seg.end, "text": seg.text.strip()})
        if seg.words:
            for w in seg.words:
                words.append({"word": w.word.strip(), "start": w.start, "end": w.end})

    return {"words": words, "segments": seg_list}
