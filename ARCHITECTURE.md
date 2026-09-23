# Architecture

## Scope

This phase implements storage, schemas, deterministic fictional data
generation, loading, validation, A-D analytical services, a local API, and
Module E Investigator Intelligence. The investigator layer consumes the
calculated upstream outputs and retains traceability to source evidence.

The foundation records evidence and relationships without asserting that
personas or identifiers belong to a real individual.

## Components

- `threat_platform.models.schemas`: dataclass-like schema definitions and
  validation for records shared by all future modules.
- `threat_platform.services.generator`: deterministic, fictional dataset
  generator. Every record carries `data_origin: "synthetic"`.
- `threat_platform.services.storage`: local JSON read/write and dataset
  validation.
- `threat_platform.api.server`: loopback-only standard-library HTTP server for
  health, dataset, investigator views, and exports.
- `threat_platform.services.investigator`: dashboard, actor view, timeline,
  graph, deterministic audit trail, CAS-style explanation, report, and local
  CSV/JSON/PDF serializers.
- `threat_platform.algorithms.evidence`: provenance, source reliability,
  independence, conflict, redundancy, and evidence graph calculations.
- `threat_platform.algorithms.attribution`: candidate links, false-link
  detection, and infrastructure similarity.
- `threat_platform.algorithms.persona`: stylometric, behavioral, migration,
  and rebranding calculations.
- `threat_platform.algorithms.reliability`: confidence decomposition, CAS,
  calibration, fragility, and abstention calculations.
- `threat_platform.ui`: dependency-free responsive investigator console.
- `data/generated.json`: generated, reviewable fixture used by the application
  and tests.

## Data flow

`generator -> generated.json -> storage loader -> schema validation -> A -> B ->
C -> D -> E -> local API or browser console`

The generator uses a fixed seed and explicit values so test results are
reproducible. The application has no network client and uses no external
service.

