FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Hugging Face Spaces commonly sets PORT=7860
EXPOSE 7860

CMD ["bash", "-lc", "uvicorn apps.api.app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
