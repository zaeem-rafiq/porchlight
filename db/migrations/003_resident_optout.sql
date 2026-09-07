-- P-03: opt-out flag for STOP handling.
alter table porchlight.residents
  add column if not exists opted_out boolean not null default false;
