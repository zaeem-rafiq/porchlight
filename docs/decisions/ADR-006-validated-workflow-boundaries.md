# ADR-006: Enforce declared triage and dispatch boundaries

Date: 2026-09-14

The public implementation accepted arbitrary triage status/need strings and out-of-range confidence, despite the declared contract. The deadline recovery enforces the existing allowed values and validates quote containment at the model boundary. Invalid model output follows the existing conservative fallback path.

Dispatch may carry optional resident_id and resource_id identifiers so a coordinator-approved request remains attached to the selected resident/resource instead of a hard-coded rehearsal object. Existing consumers without those optional fields remain compatible. Relevant constructors, handlers, evaluation code and tests must be checked together.

Approval uses a durable deterministic queue. No Strands interrupt/resume, persistent memory, concurrent resident execution, or Calendar completion is claimed without execution evidence. Synthetic and owner-only transport remain explicitly distinct.
