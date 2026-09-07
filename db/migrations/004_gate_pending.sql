-- P-04: durable coordinator gate queue (survives process restarts).
create table if not exists porchlight.gate_pending (
  id uuid primary key default gen_random_uuid(),
  event_id uuid references porchlight.hazard_events(id) on delete cascade,
  tool text not null,
  input text not null default '',
  status text not null default 'open',
  created_at timestamptz not null default now()
);
grant all on table porchlight.gate_pending to anon, authenticated, service_role;
