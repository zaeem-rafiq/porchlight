# ADR-003: single sending number (Path B) after A2P 30034 block

- Status: accepted
- Date: 2026-09-07
- Context: Twilio error 30034 blocks ALL US-bound SMS from unregistered 10DLC numbers, so the "skip A2P" plan failed closed. The fast lane (Sole Proprietor brand, no EIN) allows exactly one sending number, but the design gave coordinator and resident channels one number each with routing by To number.
- Decision (user-directed, chosen over Standard brand with EIN and over toll-free): register number B only under a Sole Proprietor brand + campaign. Number B sends everything. Coordinator pings go out from B prefixed `[Coordinator]`. Inbound all arrives at B; messages from OWNER_PHONE starting with `COORD ` are coordinator commands, everything else from that number is Ruth-the-resident. Number A stays purchased but sends nothing (kept for the P-08 voice-call stretch, which is inbound-friendly).
- Consequences: `agent/outreach.py` unchanged (already sends from B). P-04 coordinator gate sends from B with the prefix and parses `COORD ` inbound. Revisit only if a second sending number gets registered later.
