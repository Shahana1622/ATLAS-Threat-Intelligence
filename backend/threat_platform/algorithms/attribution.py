from __future__ import annotations

from collections import defaultdict
from typing import Any


def _pair_evidence(dataset: dict[str, Any]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    pairs: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in dataset["evidence"]:
        if item["actor_id"] and item["candidate_actor_id"] and item["actor_id"] != item["candidate_actor_id"]:
            pairs[(item["actor_id"], item["candidate_actor_id"])].append(item)
    return pairs


def _handle_signal(dataset: dict[str, Any], actor_a: str, actor_b: str) -> float:
    personas = [persona for persona in dataset["personas"] if persona["actor_id"] in (actor_a, actor_b)]
    handles = [handle for persona in personas for handle in persona["handles"]]
    return 1.0 if len(handles) != len(set(handles)) else 0.0


def attribution_resolution(dataset: dict[str, Any], persona_results: dict[str, Any]) -> dict[str, Any]:
    candidates = []
    for (actor_a, actor_b), items in _pair_evidence(dataset).items():
        support = [item for item in items if item["direction"] == "supports"]
        conflicts = [item for item in items if item["direction"] == "contradicts"]
        groups = len({item["independence_group"] for item in items})
        weighted_support = sum(item["strength"] * item["reliability"] for item in support) / max(1, len(support))
        weighted_conflict = sum(item["strength"] * item["reliability"] for item in conflicts) / max(1, len(conflicts))
        score = max(0.0, min(0.99, weighted_support + _handle_signal(dataset, actor_a, actor_b) * 0.08 - weighted_conflict * 0.35))
        false_link = bool(conflicts and score < 0.7) or (len(support) == 1 and groups == 1)
        candidates.append({"candidate_a": actor_a, "candidate_b": actor_b, "relationship_type": "POSSIBLE_FALSE_LINK" if false_link else "CANDIDATE_IDENTITY_LINK", "confidence": round(score, 3), "supporting_evidence_ids": [item["evidence_id"] for item in support], "conflicting_evidence_ids": [item["evidence_id"] for item in conflicts], "independent_evidence_count": groups, "signals": {"support_weight": round(weighted_support, 3), "conflict_weight": round(weighted_conflict, 3), "handle_signal": _handle_signal(dataset, actor_a, actor_b)}, "explanation": "Score combines reliability-weighted evidence, independence groups, and handle signal; contradictions reduce confidence."})
    infrastructure = []
    for index, left in enumerate(dataset["infrastructure"]):
        for right in dataset["infrastructure"][index + 1:]:
            left_values, right_values = left["fingerprint"], right["fingerprint"]
            matching = [key for key in left_values if left_values[key] == right_values.get(key)]
            infrastructure.append({"infra_a": left["infra_id"], "infra_b": right["infra_id"], "matching_features": matching, "similarity": round(len(matching) / max(1, len(left_values)), 3)})
    return {"candidates": candidates, "infrastructure_correlations": infrastructure}
