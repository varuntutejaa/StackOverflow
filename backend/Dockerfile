# ── Kaushal AI backend ───────────────────────────────────────────
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-prod.txt ./
RUN pip install --upgrade pip && pip install -r requirements-prod.txt

COPY . .

# non-root
RUN useradd -m -u 1000 kaushai && chown -R kaushai:kaushai /app
USER kaushai

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:${PORT}/health || exit 1

# entrypoint: migrate → (optional) seed → serve
RUN chmod +x scripts/start.sh
CMD ["sh", "scripts/start.sh"]
