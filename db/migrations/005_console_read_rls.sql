-- P-07: read-only anon access for the console board (service key bypasses RLS).
alter table porchlight.residents enable row level security;
alter table porchlight.volunteers enable row level security;
alter table porchlight.resources enable row level security;
alter table porchlight.hazard_events enable row level security;
alter table porchlight.contacts enable row level security;
alter table porchlight.dispatches enable row level security;
alter table porchlight.escalations enable row level security;
alter table porchlight.audit_log enable row level security;
alter table porchlight.protocol enable row level security;
alter table porchlight.gate_pending enable row level security;

do $$
declare t text;
begin
  foreach t in array array['residents','volunteers','resources','hazard_events','contacts',
                           'dispatches','escalations','audit_log','protocol','gate_pending']
  loop
    execute format('drop policy if exists porchlight_read on porchlight.%I', t);
    execute format('create policy porchlight_read on porchlight.%I for select to anon using (true)', t);
  end loop;
end $$;
