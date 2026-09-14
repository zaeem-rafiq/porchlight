-- Prevent duplicate active volunteer assignments and duplicate medical-silence
-- escalation reservations across workers. Existing conflicts make this migration
-- fail without deleting or silently changing any record.
begin;

create unique index if not exists dispatches_one_active_volunteer
  on porchlight.dispatches (volunteer_id)
  where volunteer_id is not null
    and status in ('sending', 'proposed', 'accepted');

create unique index if not exists dispatches_one_active_resident
  on porchlight.dispatches (event_id, resident_id)
  where resident_id is not null
    and status in ('sending', 'proposed', 'accepted');

create unique index if not exists escalations_one_medical_silence
  on porchlight.escalations (event_id, resident_id)
  where reason = 'medical silence past ladder';

commit;
