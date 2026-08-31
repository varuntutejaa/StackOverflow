#!/usr/bin/env sh
# Production entrypoint: migrate, optionally seed, then serve.
set -e

echo "[start] running database migrations…"
alembic upgrade head

# SEED_ON_BOOT=true  -> idempotently ensure DEMO/SIMULATED data + demo logins exist.
# (seed.py without --fresh only creates what is missing; safe to run every boot.)
if [ "${SEED_ON_BOOT:-false}" = "true" ]; then
  echo "[start] SEED_ON_BOOT=true — ensuring demo data…"
  python -m app.seed.seed || echo "[start] seed step failed (continuing)"
fi

echo "[start] launching gunicorn…"
exec gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  -b "0.0.0.0:${PORT:-8000}" \
  -w "${WEB_CONCURRENCY:-2}" \
  --timeout 120 \
  --access-logfile - --error-logfile -
