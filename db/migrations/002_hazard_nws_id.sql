-- P-02: NWS dedupe key for the poller.
alter table porchlight.hazard_events
  add column if not exists nws_id text unique;
