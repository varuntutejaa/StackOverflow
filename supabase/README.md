# Supabase setup for KaushAI

KaushAI uses Supabase for **Postgres**, and optionally **Auth** and **Storage**.
The FastAPI backend owns the schema via SQLAlchemy + Alembic; Supabase is the
managed Postgres host.

## 1. Create the project

```bash
# with the Supabase CLI (https://supabase.com/docs/guides/cli)
supabase projects create kaushai --org-id <ORG_ID> --region ap-south-1 --db-password '<STRONG_PW>'
supabase projects api-keys --project-ref <PROJECT_REF>   # note anon + service_role keys
```

Connection string (Session pooler, IPv4-friendly — use this for Render):

```
postgresql://postgres.<PROJECT_REF>:<DB_PASSWORD>@aws-0-ap-south-1.pooler.supabase.com:5432/postgres
```

## 2. Apply the schema

The backend applies migrations automatically on boot (`alembic upgrade head` in the
Docker `CMD`). To run it manually:

```bash
cd backend
export DATABASE_URL="postgresql://postgres.<REF>:<PW>@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
alembic upgrade head
python -m app.seed.seed --fresh      # loads DEMO/SIMULATED data
```

## 3. Row Level Security (defense in depth)

The API enforces RBAC server-side. If you also expose tables through the Supabase
data API (PostgREST), apply `policies.sql` so direct table access is locked down:

```bash
psql "$DATABASE_URL" -f supabase/policies.sql
```

`policies.sql` enables RLS on every table and grants:

* `service_role` — full access (used by the FastAPI backend)
* `authenticated` — read-only on catalogue tables (skills, nsqf_roles, locations,
  training_*), and row-scoped read on their own `beneficiaries` / `interviews` /
  `recommendations` / `applications` when `beneficiaries.user_account_id = auth.uid()`
* `anon` — no access

## 4. Storage (optional — interview audio)

```bash
supabase storage create kaushai-media --project-ref <REF> --public false
```

Set `SUPABASE_STORAGE_BUCKET=kaushai-media` and the service-role key in the backend
env. Audio upload is stubbed behind the AI provider interface — the mock provider
returns `data:` URIs and does not touch Storage.

## 5. Supabase Auth (optional)

By default KaushAI issues its own JWTs (`SECRET_KEY`). To delegate to Supabase Auth,
set `SUPABASE_JWT_SECRET` and `SUPABASE_URL`; the backend will additionally accept
Supabase access tokens and upsert a local `users` row keyed by `supabase_uid`.
(Local-JWT mode is the default and needs no Supabase Auth configuration.)
