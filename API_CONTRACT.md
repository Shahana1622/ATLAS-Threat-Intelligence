# API Contract

The current local API is intentionally read-only:

- `GET /health` returns `{ "status": "ok", "data_origin": "synthetic" }`.
- `GET /dataset` returns the complete generated JSON dataset.
- `GET /` serves the local investigator console.
- `GET /v1/investigator/dashboard` returns synthetic dashboard counts.
- `GET /v1/analysis` returns the calculated A-D pipeline output, including
  evidence intelligence, persona comparisons, candidate relationships, CAS,
  confidence decomposition, calibration, and fragility.
- `GET /v1/investigator/graph` returns graph nodes and evidence-linked edges.
- `GET /v1/investigator/timeline?actor_id=Actor_001` returns sorted events.
- `GET /v1/investigator/actors/{actor_id}` returns an actor investigation.
- `GET /v1/investigator/cas?actor_id=Actor_001` returns a deterministic
  CAS-style explanation with supporting/conflicting evidence IDs.
- `GET /v1/investigator/coverage` returns synthetic evaluation coverage; it
  reports when no upstream evaluation cases are available.
- `GET /v1/investigator/report?actor_id=Actor_001` returns a structured report.
- `GET /v1/investigator/export.json`, `/export.csv`, and `/export.pdf` download
  local report exports.
- Other paths return `404`.

The server binds to `127.0.0.1` and uses only Python's standard library.

## Upstream compatibility

These are contracts for later phases, not implementations:

- **Evidence Intelligence**: `POST /v1/evidence/search` accepts typed filters
  and returns matching evidence with provenance.
- **Attribution & Identity Resolution**: `POST /v1/attribution/candidates`
  accepts an evidence set and returns ranked candidates with explanations,
  never a definitive identity claim.
- **AI Persona Intelligence**: `POST /v1/personas/compare` accepts persona
  IDs and returns feature comparisons tied to evidence IDs.
- **Attribution Reliability**: `POST /v1/reliability/score` accepts evidence
  and independence groups and returns an auditable score breakdown.
The investigator service accepts optional upstream analysis payloads where
available, while remaining compatible with the current foundation-only
dataset. All endpoints remain local, synthetic-data-only, evidence-driven,
and explicit about uncertainty. They do not add external data sources or
identity/deanonymization behavior.

