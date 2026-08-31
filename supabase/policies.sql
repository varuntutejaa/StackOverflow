-- ─────────────────────────────────────────────────────────────
-- Kaushal AI · Supabase Row Level Security
-- Apply AFTER `alembic upgrade head` has created the schema.
--   psql "$DATABASE_URL" -f supabase/policies.sql
--
-- The FastAPI backend connects as `service_role` (via the pooled Postgres
-- connection string) and is therefore unaffected by these policies — they only
-- matter if tables are also exposed through PostgREST / the Supabase data API.
-- ─────────────────────────────────────────────────────────────

do $$
declare t text;
begin
  foreach t in array array[
    'users','locations','beneficiaries','interviews','interview_messages',
    'skills','nsqf_roles','role_skill_link','training_providers','training_programs',
    'recommendations','applications','outcomes','opportunities','skill_demand',
    'notifications','audit_logs'
  ] loop
    execute format('alter table public.%I enable row level security;', t);
    execute format('alter table public.%I force row level security;', t);
    -- backend / service role: full access
    execute format($f$
      drop policy if exists svc_all on public.%1$I;
      create policy svc_all on public.%1$I
        for all to service_role using (true) with check (true);
    $f$, t);
  end loop;
end $$;

-- ── Public read-only catalogue (any signed-in user) ──────────
do $$
declare t text;
begin
  foreach t in array array[
    'locations','skills','nsqf_roles','role_skill_link',
    'training_providers','training_programs','opportunities','skill_demand'
  ] loop
    execute format($f$
      drop policy if exists read_catalogue on public.%1$I;
      create policy read_catalogue on public.%1$I
        for select to authenticated using (true);
    $f$, t);
  end loop;
end $$;

-- ── Beneficiary self-service (row-scoped) ────────────────────
drop policy if exists ben_self_read on public.beneficiaries;
create policy ben_self_read on public.beneficiaries
  for select to authenticated
  using (user_account_id = auth.uid()::text or created_by_id = auth.uid()::text);

drop policy if exists interview_self_read on public.interviews;
create policy interview_self_read on public.interviews
  for select to authenticated
  using (exists (
    select 1 from public.beneficiaries b
    where b.id = interviews.beneficiary_id
      and (b.user_account_id = auth.uid()::text)
  ));

drop policy if exists reco_self_read on public.recommendations;
create policy reco_self_read on public.recommendations
  for select to authenticated
  using (exists (
    select 1 from public.beneficiaries b
    where b.id = recommendations.beneficiary_id
      and b.user_account_id = auth.uid()::text
  ));

drop policy if exists appl_self_read on public.applications;
create policy appl_self_read on public.applications
  for select to authenticated
  using (exists (
    select 1 from public.beneficiaries b
    where b.id = applications.beneficiary_id
      and b.user_account_id = auth.uid()::text
  ));

drop policy if exists notif_self_read on public.notifications;
create policy notif_self_read on public.notifications
  for select to authenticated
  using (user_id = auth.uid()::text);

-- anon role: explicitly no grants
revoke all on all tables in schema public from anon;
