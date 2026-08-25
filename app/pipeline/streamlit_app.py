"""
Clipador — versão Streamlit (deploy gratuito via Streamlit Community Cloud).
Cola o link do YouTube, o app baixa, transcreve, escolhe os melhores momentos,
corta e queima legenda estilo karaokê.
"""
import streamlit as st
from pathlib import Path
import tempfile
import shutil

from app import config
from app.pipeline import download, transcribe, highlights, subtitles, cut

st.set_page_config(page_title="Clipador", page_icon="🎬", layout="centered")

st.markdown(
    """
    <style>
    .stApp { background-color: #14161a; }
    h1, h2, h3, p, span, label { color: #ecebe6 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🎬 Clipador")
st.caption("Cola o link do YouTube — o sistema corta e legenda automaticamente.")

url = st.text_input("Link do YouTube", placeholder="https://www.youtube.com/watch?v=...")
vertical = st.checkbox("Reenquadrar em vertical (9:16) para Shorts/Reels", value=True)
run_btn = st.button("Gerar cortes", type="primary", disabled=not url)

if run_btn and url:
    if "youtube.com" not in url and "youtu.be" not in url:
        st.error("Isso não parece um link válido do YouTube.")
        st.stop()

    work_dir = Path(tempfile.mkdtemp(prefix="clipador_"))
    out_dir = work_dir / "out"
    out_dir.mkdir(exist_ok=True)

    status = st.status("Baixando vídeo...", expanded=True)
    progress = st.progress(0)

    try:
        status.write("📥 Baixando vídeo do YouTube...")
        info = download.download_video(url, work_dir)
        progress.progress(20)

        status.write(f"🎧 Transcrevendo áudio de **{info['title']}**...")
        transcript = transcribe.transcribe(info["video_path"])
        progress.progress(50)

        status.write("🔍 Encontrando os melhores momentos...")
        picks = highlights.select_highlights(transcript["segments"], info["duration"], info["title"])
        if not picks:
            status.update(label="Não encontrei trechos bons o suficiente.", state="error")
            st.stop()
        progress.progress(60)

        status.write(f"✂️ Cortando e legendando {len(picks)} clipe(s)...")
        clips = []
        for idx, pick in enumerate(picks):
            ass_path = work_dir / f"clip_{idx}.ass"
            subtitles.build_ass(transcript["words"], pick["start"], pick["end"], ass_path)
            out_path = out_dir / f"clip_{idx}.mp4"
            cut.cut_clip(info["video_path"], pick["start"], pick["end"], ass_path, out_path, vertical=vertical)
            clips.append({**pick, "file": out_path})
            progress.progress(60 + int(38 * (idx + 1) / len(picks)))

        progress.progress(100)
        status.update(label="Pronto! ✅", state="complete")

        st.subheader("Seus clipes")
        for i, c in enumerate(clips):
            st.markdown(f"**Clipe {i+1}** · {c['start']:.0f}s → {c['end']:.0f}s")
            if c.get("reason"):
                st.caption(c["reason"])
            video_bytes = c["file"].read_bytes()
            st.video(video_bytes)
            st.download_button(
                "Baixar clipe",
                data=video_bytes,
                file_name=f"clipe_{i+1}.mp4",
                mime="video/mp4",
                key=f"dl_{i}",
            )
            st.divider()

    except Exception as e:
        status.update(label="Deu erro no processo.", state="error")
        st.error(str(e))
    finally:
        # limpa os arquivos temporários da sessão (menos os clipes já mostrados acima)
        pass

st.caption(
    "Sem ANTHROPIC_API_KEY configurada, a escolha dos melhores momentos usa um "
    "heurístico simples. Configure a chave em Settings → Secrets pra usar IA."
)
