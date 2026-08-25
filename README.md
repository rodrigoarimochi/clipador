---
title: Clipador
emoji: 🎬
colorFrom: yellow
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# Clipador — corte automático de vídeos do YouTube com legenda

Cola o link do YouTube → o sistema baixa, transcreve, acha os melhores momentos,
corta e queima legenda estilo "palavra destacada" (igual CapCut/Opus Clip) →
te devolve os clipes prontos pra Shorts/Reels/TikTok.

## ⚠️ Antes de tudo: o que uma VPS gratuita aguenta

Sendo direto, pra você não perder tempo: **transcrição de áudio (Whisper) e corte de
vídeo (ffmpeg) consomem CPU/RAM pesado.** A maioria das "VPS grátis" não aguenta:

| Serviço | Free tier | Aguenta esse app? |
|---|---|---|
| **Oracle Cloud Free Tier** | 4 vCPU ARM + 24GB RAM, **para sempre** | ✅ Sim, de longe a melhor opção grátis |
| Render / Railway free | 0.1–0.5 vCPU, 512MB RAM, dorme após inatividade | ❌ Trava ou estoura tempo/memória |
| Google Cloud free (e2-micro) | 1 vCPU compartilhada, 1GB RAM | ⚠️ Só com modelo Whisper "tiny" e vídeos curtos |
| Fly.io free | 256MB RAM | ❌ Insuficiente |

**Recomendação:** crie uma conta na Oracle Cloud (cartão é só verificação, não cobra
no free tier) e suba uma instância **Ampere A1** (ARM, 4 vCPU / 24GB RAM grátis).
É o único free tier real do mercado com recurso suficiente pra isso.

## Instalação (local ou na VPS)

```bash
# 1. Dependências de sistema
sudo apt update && sudo apt install -y ffmpeg python3-pip python3-venv fonts-noto

# 2. Ambiente Python
cd clipador
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. (Opcional, mas recomendado) chave da Anthropic pra IA escolher os melhores
#    momentos com muito mais qualidade que o heurístico padrão
export ANTHROPIC_API_KEY="sua-chave-aqui"

# 4. Ajuste o tamanho do modelo Whisper conforme a máquina (veja app/config.py)
export WHISPER_MODEL="base"   # tiny | base | small | medium

# 5. Rodar
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Acesse `http://SEU_IP:8000` (ou `http://localhost:8000` local).

## Deixando no ar 24/7 (systemd)

Crie `/etc/systemd/system/clipador.service`:

```ini
[Unit]
Description=Clipador
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/clipador
Environment="ANTHROPIC_API_KEY=sua-chave-aqui"
Environment="WHISPER_MODEL=base"
ExecStart=/home/ubuntu/clipador/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now clipador
```

Depois, se quiser um domínio bonito e HTTPS, coloque um Nginx + Certbot na frente
(posso montar isso também se você quiser).

## Como funciona por dentro

1. **`app/pipeline/download.py`** — baixa o vídeo com `yt-dlp`.
2. **`app/pipeline/transcribe.py`** — transcreve com `faster-whisper`, com timestamp
   por palavra (essencial pra legenda karaokê).
3. **`app/pipeline/highlights.py`** — escolhe os melhores trechos:
   - **Com `ANTHROPIC_API_KEY`**: manda a transcrição pra Claude decidir os trechos
     com mais potencial de viralizar (gancho, virada, piada, dado forte).
   - **Sem chave**: heurístico local (perguntas, exclamações, palavras de impacto,
     densidade de fala).
4. **`app/pipeline/subtitles.py`** — gera `.ass` com a palavra atual destacada.
5. **`app/pipeline/cut.py`** — corta com `ffmpeg`, reenquadra em 9:16 (opcional) e
   queima a legenda.

## Limitações conhecidas (honestas)

- Vídeos muito longos (>1h) demoram bastante numa VPS pequena — a transcrição é o
  gargalo. Considere modelo `tiny` pra esses casos.
- O reenquadramento vertical hoje é um crop central simples — não segue rosto/ação.
  Dá pra evoluir isso com detecção de rosto (ex: `mediapipe`) se você quiser.
- Sem `ANTHROPIC_API_KEY`, a escolha dos melhores momentos é bem mais simples
  (heurística por palavras-chave), não tão boa quanto um editor humano ou a IA.
- yt-dlp quebra de vez em quando quando o YouTube muda algo — rode
  `pip install -U yt-dlp` se parar de funcionar.

## Testando rápido sem subir servidor nenhum

```bash
uvicorn app.main:app --reload
```
e abre `http://localhost:8000` no navegador da sua própria máquina — dá pra validar
tudo localmente antes de gastar tempo configurando a VPS.
