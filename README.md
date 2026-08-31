# KaushAI

**AI-powered multilingual voice livelihood mapping and NSQF-aligned skilling
recommendations for SC communities under PM-AJAY.**
Smart India Hackathon 2026 · Problem statement **SIH26097**.

> ⚠️ Prototype. All seeded records are clearly labelled **DEMO / SIMULATED**
> (`is_demo` / `is_simulated`). This is **not** an official Government of India system.

---

## What it does

| | |
|---|---|
| **Voice-first intake** | Beneficiaries answer a structured interview by voice/text in Hindi, Santhali, Ho, Mundari or English. |
| **Multilingual understanding** | Speech → text → translation → deterministic entity extraction → structured livelihood profile. Provider layer is pluggable (mock / OpenAI / Bhashini). |
| **Explainable recommendations** | A transparent weighted-scoring engine (not "ask an LLM") — every match-score point is attributable to a named factor (education, existing skills, interest, local demand, mobility, employment preference, training availability, opportunity, family synergy). |
| **NSQF catalogue** | Skills, job roles, QP/NCO alignment, eligibility, duration, sectors, required competencies. |
| **Livelihood mapping** | District-level beneficiary distribution, skill demand vs supply, training centres, opportunities and skill gaps. |
| **Training workflow** | Catalogue → eligibility check → application → enrolment → progress → certification. |
| **Outcome tracking** | Interview → recommendation → training → certification → employment / self-employment, with income-improvement measurement. |
| **Government admin portal** | Overview KPIs, beneficiaries CRUD, AI interviews, recommendations, NSQF catalogue, training, livelihood map, skill demand, outcomes, reports, notifications, users & roles, audit log, settings. |

## Architecture

```
frontend/  Next.js 15 (App Router, TS) · Tailwind · Radix/shadcn-style UI · Recharts · framer-motion · TanStack Query
                │  REST (JWT bearer)  +  WebSocket (interview realtime)
backend/   FastAPI · SQLAlchemy 2 · Pydantic v2 · Alembic · slowapi (rate limit) · structlog
                │
           PostgreSQL (Supabase)   ·   Redis (cache, optional)   ·   Supabase Storage (optional)

AI providers (app/services/ai/)  — STT · TTS · Translation · LLM, behind interfaces.
   Default = fully-working MOCK providers (no external credentials needed).
```

- **Auth**: local JWT (access + refresh), register / login / forgot / reset /
  email-verify / logout / RBAC. Optional Supabase-Auth delegation.
- **Roles**: `admin`, `gov_officer`, `training_provider`, `beneficiary`.
- **Recommendation engine**: `backend/app/services/recommendation_engine.py` — weights
  are configurable via env (`RECOMMENDATION_WEIGHTS_FILE`) or per-request override.

---

## Quick start (local, zero external services)

### 1. Backend — FastAPI (SQLite fallback, mock AI)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env                     # defaults are fine for local
python -m app.seed.seed --fresh          # builds SQLite db + DEMO data
uvicorn app.main:app --reload --port 8000
```

- API docs: http://localhost:8000/docs · Health: http://localhost:8000/health
- Seed prints demo logins:

  | Role | Email | Password |
  |---|---|---|
  | Admin | `admin@kaushai.gov.in` | `KaushAI@2026` |
  | Gov Officer | `officer@kaushai.gov.in` | `Officer@2026` |
  | Training Provider | `provider@kaushai.gov.in` | `Provider@2026` |
  | Beneficiary (Ramesh Kumar) | `ramesh@kaushai.gov.in` | `Ramesh@2026` |

### 2. Frontend — Next.js

```bash
cd frontend
npm install
cp .env.example .env.local               # NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm run dev
```

Open http://localhost:3000 → **Sign in** (demo buttons pre-fill credentials).

### Or: one command with Docker (Postgres + Redis + API)

```bash
docker compose up --build       # API on :8000, seeded automatically
cd frontend && npm run dev      # frontend still runs on host
```

---

## Demo flow — Ramesh Kumar

Seeded and reproducible (`app/seed/seed.py :: build_demo`):

1. Beneficiary **Ramesh Kumar**, 22, Ranchi, 10th pass, farmer, interested in electronics/solar, wants self-employment, local mobility.
2. **AI voice interview** (Hindi) → structured profile extracted.
3. **Recommendations** generated → **Solar PV Installer (Suryamitra): 94% match** (rank 1, accepted), with runners-up (Domestic Electrician, Mobile Repair, CCTV, Assistant Solar).
4. **Training selected** → Suryamitra batch → **enrolled** → **in progress (35%)**.
5. **Livelihood roadmap** with career pathway and outcome timeline.

Open it: sign in as admin → dashboard shows an **"Open demo journey"** button, or
sign in as `ramesh@kaushai.gov.in` → `/app/assistant`.
Rebuild anytime: `python -m app.seed.seed --demo-only`.

---

## Testing / quality

```bash
cd backend && pytest -q          # 11 tests: auth, RBAC, full journey, analytics, engine config
cd backend && ruff check app tests
cd frontend && npm run build     # type-checks + production build
cd frontend && npx tsc --noEmit
```

---

## Production deployment

### Database / Auth / Storage → Supabase
See [`supabase/README.md`](supabase/README.md). Create the project, grab the pooled
`DATABASE_URL`, and (optionally) apply `supabase/policies.sql` for RLS.

### Backend → Render

```bash
# Render blueprint (backend/render.yaml): web service (Docker) + Redis key-value
render blueprint launch          # from repo root, or connect the repo in the Render UI
```

Set these env vars in the Render dashboard (marked `sync:false` in the blueprint):

| Var | Value |
|---|---|
| `DATABASE_URL` | Supabase **pooled** connection string |
| `CORS_ORIGINS` | `https://<your-vercel-domain>` |
| `SECRET_KEY` | auto-generated by the blueprint |
| `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET` | from Supabase (optional) |
| `OPENAI_API_KEY` + `AI_*_PROVIDER=openai` | optional — swap mock providers for real ones |

The container runs `alembic upgrade head` on boot. Load demo data once:

```bash
render jobs create --service kaushai-api --command "python -m app.seed.seed --fresh"
```

Health check: `GET /health`. OpenAPI: `/openapi.json`, Swagger `/docs`.

### Frontend → Vercel

```bash
cd frontend
vercel link
vercel env add NEXT_PUBLIC_API_BASE_URL production   # https://kaushai-api.onrender.com
vercel --prod
```

`frontend/vercel.json` pins the framework, region (`bom1`) and security headers.

---

## Repo layout

```
backend/
  app/
    core/            config, security (JWT/bcrypt), structured logging
    db/              SQLAlchemy engine + session + Base
    models/          17 tables: users, locations, beneficiaries, interviews,
                     interview_messages, skills, nsqf_roles, recommendations,
                     training_providers, training_programs, applications,
                     outcomes, opportunities, skill_demand, notifications, audit_logs
    schemas/         Pydantic v2 request/response models
    api/routes/      auth, users, locations, beneficiaries, skills, training,
                     interviews (+voice +ws), recommendations, applications,
                     outcomes, opportunities, analytics, notifications, meta
    services/
      ai/            provider abstraction + mock + openai implementations
      interview_engine.py     multilingual question script + entity extraction
      interview_runner.py     turn orchestration + profile assembly
      recommendation_engine.py  explainable weighted scoring
      analytics.py            overview / outcomes / livelihood-map aggregation
      eligibility.py, audit.py, notifications.py, cache.py
    seed/            reference data + Ramesh Kumar demo builder
  alembic/           migrations (0001 bootstrap from models)
  tests/             pytest
  Dockerfile, render.yaml, requirements*.txt, .env.example
frontend/
  src/app/           App Router: (auth), dashboard/*, app/* (beneficiary)
  src/components/     ui/ primitives, shell/, charts, map, interview console, reco card
  src/lib/           api client, auth context, react-query hooks, types
  vercel.json, tailwind.config.ts, .env.example
supabase/            policies.sql (RLS) + setup guide
docker-compose.yml, Makefile
```

## API surface (selected)

`/api/v1` — `auth/*`, `users`, `audit-logs`, `roles`, `locations/*`,
`beneficiaries/*` (+ `export/csv`, `me`), `skills/*`, `nsqf-roles/*`,
`training-providers/*`, `training-programs/*`, `interviews/*`
(`/turn`, `/complete`, `/transcript`, `/ws`), `voice/transcribe`, `voice/synthesize`,
`recommendations/*` (`/generate`, `/weights`, `/{id}/decision`), `applications/*`
(`/enroll`, `/certificate`), `outcomes/*`, `opportunities/*`,
`analytics/overview`, `analytics/outcomes`, `map/livelihood`, `notifications/*`,
`meta/config`, `meta/demo`, `health`.

Full interactive spec at `/docs`.
