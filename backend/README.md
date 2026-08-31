# KaushAI — Backend (FastAPI)

See the [root README](../README.md) for the full picture. Quick reference:

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python -m app.seed.seed --fresh      # SQLite by default
uvicorn app.main:app --reload
```

## Config

Everything is env-driven (`app/core/config.py`). With no `DATABASE_URL` the app
uses a local SQLite file and auto-creates tables on startup. Set `DATABASE_URL`
to a Postgres/Supabase URL for production (migrations run via Alembic).

## Migrations

```bash
alembic upgrade head
alembic revision --autogenerate -m "add X"     # after model changes
```

## AI providers

`AI_STT_PROVIDER` / `AI_LLM_PROVIDER` / `AI_TTS_PROVIDER` / `AI_TRANSLATE_PROVIDER`
= `mock` (default, no creds) | `openai` (needs `OPENAI_API_KEY`).
Add a provider by implementing the interfaces in `app/services/ai/base.py` and
registering it in `app/services/ai/registry.py` — no other code changes.

## Recommendation engine

`app/services/recommendation_engine.py`. Weights: `DEFAULT_WEIGHTS`, overridable
via `RECOMMENDATION_WEIGHTS_FILE` (JSON) or the `weights_override` field on
`POST /recommendations/generate`. `GET /recommendations/weights` returns the
active weights + descriptions.

## Tests

```bash
pytest -q          # uses a throwaway SQLite db in the temp dir, seeds it once
ruff check app tests
```

## Docker

```bash
docker build -t kaushai-api .
docker run -p 8000:8000 -e SECRET_KEY=... -e DATABASE_URL=... kaushai-api
```

The image runs `alembic upgrade head` then `gunicorn` (uvicorn workers).
