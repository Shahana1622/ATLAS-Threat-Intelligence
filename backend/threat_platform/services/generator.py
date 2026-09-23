from __future__ import annotations

from typing import Any

from backend.threat_platform.models.schemas import DATA_ORIGIN


def generate_dataset() -> dict[str, Any]:
    """Build a deterministic connected fictional investigation fixture."""
    actor_count = 15
    dataset: dict[str, Any] = {"data_origin": DATA_ORIGIN}
    dataset["actors"] = [{"actor_id": f"Actor_{i:03d}", "name": f"Fictional Cluster {i:03d}", "data_origin": DATA_ORIGIN} for i in range(1, actor_count + 1)]
    dataset["marketplaces"] = [{"marketplace_id": f"Marketplace_{i:03d}", "name": f"Fictional Market {i:03d}", "data_origin": DATA_ORIGIN} for i in range(1, 16)]
    dataset["forums"] = [{"forum_id": f"Forum_{i:03d}", "name": f"Fictional Forum {i:03d}", "data_origin": DATA_ORIGIN} for i in range(1, 16)]
    dataset["pgp_identifiers"] = [{"pgp_id": f"PGP_{i:03d}", "fingerprint": f"FICTIONAL-PGP-{i:03d}", "data_origin": DATA_ORIGIN} for i in range(1, 16)]
    dataset["wallet_identifiers"] = [{"wallet_id": f"Wallet_{i:03d}", "value": f"wallet-fixture-{i:03d}", "data_origin": DATA_ORIGIN} for i in range(1, 31)]
    dataset["infrastructure"] = [{"infra_id": f"Infra_{i:03d}", "fingerprint": {"tls": f"tls-{i % 5}", "host_pattern": f"host-{i % 4}", "timing": i % 3}, "kind": "fictional_fingerprint", "data_origin": DATA_ORIGIN} for i in range(1, 21)]
    dataset["sources"] = [{"source_id": f"Source_{i:03d}", "source_type": "fixture_forum" if i % 2 else "fixture_market", "source_family": f"Family_{i % 6:02d}", "reliability": round(0.62 + (i % 5) * 0.07, 2), "data_origin": DATA_ORIGIN} for i in range(1, 19)]
    personas, handles, posts, events = [], [], [], []
    for i in range(1, 19):
        actor = ((i - 1) % actor_count) + 1
        platforms = [f"Forum_{((i - 1) % 15) + 1:03d}", f"Marketplace_{((i + 1) % 15) + 1:03d}"]
        handles_for_persona = [f"Handle_{i:03d}", f"Handle_{i + 18:03d}"]
        handle_values = [f"handle_{i:03d}", f"alias_{i:03d}"]
        if i == 7:
            handle_values = ["northstar_mock", "northstar_mock"]
        personas.append({"persona_id": f"Persona_{i:03d}", "actor_id": f"Actor_{actor:03d}", "handles": handles_for_persona, "writing_samples": [f"Sample_{i:03d}_{j}" for j in range(1, 4)], "behavioral_events": [f"Event_{i:03d}_{j}" for j in range(1, 7)], "platforms": platforms, "first_seen": f"2025-01-{10 + i:02d}T09:00:00Z", "last_seen": f"2026-02-{(i % 20) + 1:02d}T21:00:00Z", "data_origin": DATA_ORIGIN})
        for offset, value in enumerate(handles_for_persona):
            handles.append({"handle_id": value, "value": handle_values[offset], "platform_id": platforms[offset % 2], "data_origin": DATA_ORIGIN})
        for j in range(1, 5):
            posts.append({"post_id": f"Post_{i:03d}_{j}", "author_handle_id": handles_for_persona[0], "source_id": f"Source_{((i + j) % 18) + 1:03d}", "timestamp": f"2025-{(i + j) % 12 + 1:02d}-{(i % 20) + 1:02d}T{(8 + j * 3) % 24:02d}:00:00Z", "content": f"fictional writing sample {i} {j} with measured rhythm {i % 4}", "data_origin": DATA_ORIGIN})
        for j in range(1, 7):
            events.append({"event_id": f"Event_{i:03d}_{j}", "persona_id": f"Persona_{i:03d}", "event_type": ["posting", "listing", "reply"][j % 3], "timestamp": f"2025-{(i + j) % 12 + 1:02d}-{(i % 20) + 1:02d}T{(7 + j * 2) % 24:02d}:00:00Z", "activity_frequency": 1 + (i + j) % 5, "active_hour": (7 + j * 2) % 24, "active_day": (i + j) % 7, "platform_id": platforms[j % 2], "data_origin": DATA_ORIGIN})
    dataset.update({"personas": personas, "handles": handles, "posts": posts, "behavioral_events": events})

    evidence, relationships = [], []
    def add_evidence(number: int, actor_a: str, actor_b: str, kind: str, direction: str, strength: float, group: str, source: int, description: str) -> str:
        evidence_id = f"Evidence_{number:03d}"
        evidence.append({"evidence_id": evidence_id, "actor_id": actor_a, "candidate_actor_id": actor_b, "evidence_type": kind, "source_id": f"Source_{source:03d}", "timestamp": f"2025-{number % 12 + 1:02d}-{number % 24 + 1:02d}T10:00:00Z", "reliability": round(0.66 + (number % 5) * 0.06, 2), "independence_group": group, "direction": direction, "strength": strength, "description": description, "data_origin": DATA_ORIGIN})
        return evidence_id
    def add_relationship(number: int, source_entity: str, target_entity: str, relationship_type: str, strength: float, evidence_id: str) -> None:
        relationships.append({"relationship_id": f"Relationship_{number:03d}", "source_entity": source_entity, "target_entity": target_entity, "relationship_type": relationship_type, "strength": strength, "evidence_ids": [evidence_id], "timestamp": evidence[-1]["timestamp"], "data_origin": DATA_ORIGIN})

    number = 1
    for kind, strength, group in [("stylometry", .92, "style"), ("behavior_similarity", .88, "behavior"), ("pgp_relationship", .95, "pgp"), ("wallet_relationship", .84, "wallet"), ("timeline_overlap", .86, "timeline"), ("infrastructure_similarity", .81, "infra")]:
        eid = add_evidence(number, "Actor_001", "Actor_007", kind, "supports", strength, group, number, f"Strong candidate signal: {kind}."); add_relationship(number, "Actor_001", "Actor_007", "candidate_identity_link", strength, eid); number += 1
    for kind, strength, group in [("handle_similarity", .91, "handle"), ("stylometry", .18, "false_style"), ("behavior_similarity", .21, "false_behavior"), ("timeline_conflict", .89, "false_timeline"), ("infrastructure_difference", .86, "false_infra")]:
        direction = "supports" if kind == "handle_similarity" else "contradicts"
        eid = add_evidence(number, "Actor_002", "Actor_009", kind, direction, strength, group, (number % 18) + 1, f"False-link scenario signal: {kind}."); add_relationship(number, "Actor_002", "Actor_009", "possible_false_link" if direction == "contradicts" else "candidate_identity_link", strength, eid); number += 1
    for offset in range(8):
        direction = "contradicts" if offset == 3 else "supports"
        eid = add_evidence(number, "Actor_003", "Actor_010", "conflict_signal" if offset == 3 else "support_signal", direction, .88 if offset == 3 else .74, "conflict_family", 2, "Conflict scenario with dependent source family."); add_relationship(number, "Actor_003", "Actor_010", "candidate_identity_link", .65, eid); number += 1
    for _ in range(5):
        eid = add_evidence(number, "Actor_004", "Actor_011", "redundant_signal", "supports", .58, "redundant_family", 4, "Repeated record from the same source family."); add_relationship(number, "Actor_004", "Actor_011", "candidate_identity_link", .42, eid); number += 1
    for _ in range(2):
        eid = add_evidence(number, "Actor_005", "Actor_012", "weak_dependent_signal", "supports", .31, "insufficient_family", 6, "Weak dependent support for abstention scenario."); add_relationship(number, "Actor_005", "Actor_012", "candidate_identity_link", .25, eid); number += 1
    for _ in range(4):
        eid = add_evidence(number, "Actor_001", "Actor_001", "rebranding_signal", "supports", .78, "rebranding", 8, "Persona_001 to Persona_007 continuity signal."); add_relationship(number, "Persona_001", "Persona_007", "persona_rebranding", .78, eid); number += 1
    for platform in ["Forum_001", "Marketplace_002", "Forum_003"]:
        eid = add_evidence(number, "Actor_001", "Actor_001", "persona_migration", "supports", .8, "migration", 10, f"Migration path includes {platform}."); add_relationship(number, "Persona_001", platform, "persona_migration", .8, eid); number += 1
    while len(evidence) < 120:
        actor_a = f"Actor_{(number % actor_count) + 1:03d}"; actor_b = f"Actor_{((number + 4) % actor_count) + 1:03d}"
        eid = add_evidence(number, actor_a, actor_b, "context_signal", "contextual", .45 + (number % 4) * .05, f"context_{number % 8}", (number % 18) + 1, "Contextual fixture signal for graph and timeline coverage."); add_relationship(number, actor_a, f"Infra_{(number % 20) + 1:03d}", "references", .4, eid); number += 1
    dataset.update({"evidence": evidence, "relationships": relationships})
    return dataset
