FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg fonts-noto \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /code/jobs /code/output

# Hugging Face Spaces expõe a porta 7860 por padrão
EXPOSE 7860
ENV PORT=7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
