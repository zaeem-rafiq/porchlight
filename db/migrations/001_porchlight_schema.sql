-- P-01 migration: porchlight schema tables + REST grants.
-- Run once in Supabase SQL Editor (Management API token lacks DDL rights).
-- Idempotent: CREATE TABLE IF NOT EXISTS; grants re-runnable.

create schema if not exists porchlight;

create table if not exists porchlight.residents (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  language text not null default 'en',
  age_band text not null,
  lives_alone boolean not null default false,
  has_ac boolean not null default true,
  powered_medical_device text,
  mobility text not null default 'independent',
  phone text not null unique,
  emergency_contact text not null,
  preferred_channel text not null default 'sms',
  notes text not null default ''
);

create table if not exists porchlight.volunteers (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  phone text not null unique,
  opted_in boolean not null default true,
  home_block text not null
);

create table if not exists porchlight.resources (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  kind text not null,
  address text not null,
  hours text not null,
  phone text
);

create table if not exists porchlight.hazard_events (
  id uuid primary key default gen_random_uuid(),
  type text not null,
  severity text not null,
  headline text not null,
  zone text not null,
  onset timestamptz,
  expires timestamptz,
  source text not null,
  status text not null default 'open'
);

create table if not exists porchlight.contacts (
  id uuid primary key default gen_random_uuid(),
  event_id uuid not null references porchlight.hazard_events(id) on delete cascade,
  resident_id uuid not null references porchlight.residents(id) on delete cascade,
  tier integer not null,
  attempts integer not null default 0,
  status text not null default 'pending',
  last_inbound timestamptz,
  last_outbound timestamptz,
  unique (event_id, resident_id)
);

create table if not exists porchlight.dispatches (
  id uuid primary key default gen_random_uuid(),
  event_id uuid references porchlight.hazard_events(id) on delete cascade,
  resident_id uuid references porchlight.residents(id) on delete set null,
  volunteer_id uuid references porchlight.volunteers(id) on delete set null,
  resource_id uuid references porchlight.resources(id) on delete set null,
  detail text not null default '',
  status text not null default 'open',
  created_at timestamptz not null default now()
);

create table if not exists porchlight.escalations (
  id uuid primary key default gen_random_uuid(),
  event_id uuid references porchlight.hazard_events(id) on delete cascade,
  resident_id uuid references porchlight.residents(id) on delete cascade,
  reason text not null,
  status text not null default 'open',
  created_at timestamptz not null default now()
);

create table if not exists porchlight.audit_log (
  id uuid primary key default gen_random_uuid(),
  event_id uuid references porchlight.hazard_events(id) on delete cascade,
  actor text not null,
  action text not null,
  detail text not null default '',
  created_at timestamptz not null default now()
);

create table if not exists porchlight.protocol (
  id text primary key,
  rules_yaml text not null
);

-- REST grants (service_role drives seed + app; anon/authenticated for console reads later)
grant usage on schema porchlight to anon, authenticated, service_role;
grant all on all tables in schema porchlight to anon, authenticated, service_role;
grant all on all sequences in schema porchlight to anon, authenticated, service_role;
alter default privileges in schema porchlight grant all on tables to anon, authenticated, service_role;
alter default privileges in schema porchlight grant all on sequences to anon, authenticated, service_role;

notify pgrst, 'reload schema';
