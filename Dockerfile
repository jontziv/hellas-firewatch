FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# HF Docker Spaces run as UID 1000; using a non-root user avoids permission issues. :contentReference[oaicite:2]{index=2}
RUN useradd -m -u 1000 user
USER user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .

EXPOSE 7860

CMD ["bash", "-lc", "gunicorn -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:${PORT:-7860} apps.api.app.main:app"]
