from __future__ import annotations

from typing import Any

DATA_ORIGIN = "synthetic"
DATASET_LIST_FIELDS = (
    "actors", "personas", "handles", "marketplaces", "forums",
    "pgp_identifiers", "wallet_identifiers", "infrastructure", "posts",
    "behavioral_events", "evidence", "relationships", "sources",
)

EVIDENCE_REQUIRED = (
    "evidence_id", "actor_id", "candidate_actor_id", "evidence_type",
    "source_id", "timestamp", "reliability", "independence_group",
    "direction", "strength", "description", "data_origin",
)
RELATIONSHIP_REQUIRED = (
    "relationship_id", "source_entity", "target_entity", "relationship_type",
    "strength", "evidence_ids", "timestamp", "data_origin",
)
PERSONA_REQUIRED = (
    "persona_id", "actor_id", "handles", "writing_samples",
    "behavioral_events", "platforms", "first_seen", "last_seen", "data_origin",
)


def validate_record(record: dict[str, Any], required: tuple[str, ...]) -> None:
    missing = [field for field in required if field not in record]
    if missing:
        raise ValueError(f"record missing required fields: {', '.join(missing)}")
    if record["data_origin"] != DATA_ORIGIN:
        raise ValueError("all records must have data_origin='synthetic'")


def validate_dataset(dataset: dict[str, Any]) -> None:
    if dataset.get("data_origin") != DATA_ORIGIN:
        raise ValueError("dataset must have data_origin='synthetic'")
    for field in DATASET_LIST_FIELDS:
        if not isinstance(dataset.get(field), list):
            raise ValueError(f"dataset field {field!r} must be a list")
    for record in dataset["evidence"]:
        validate_record(record, EVIDENCE_REQUIRED)
        if not 0 <= record["reliability"] <= 1 or not 0 <= record["strength"] <= 1:
            raise ValueError("evidence reliability and strength must be between 0 and 1")
    for record in dataset["relationships"]:
        validate_record(record, RELATIONSHIP_REQUIRED)
        if not 0 <= record["strength"] <= 1:
            raise ValueError("relationship strength must be between 0 and 1")
    for record in dataset["personas"]:
        validate_record(record, PERSONA_REQUIRED)

