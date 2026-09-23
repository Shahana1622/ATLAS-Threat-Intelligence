from __future__ import annotations

from typing import Any


def reliability_analysis(evidence_results: dict[str, Any], attribution_results: dict[str, Any], persona_results: dict[str, Any]) -> dict[str, Any]:
    candidates = attribution_results["candidates"]
    decomposition = []
    for candidate in candidates:
        support = candidate["signals"]["support_weight"]
        conflict = candidate["signals"]["conflict_weight"]
        actor_numbers = {value.split("_")[-1] for value in (candidate["candidate_a"], candidate["candidate_b"])}
        persona_pairs = [item for item in persona_results["comparisons"] if {item["persona_a"].split("_")[-1], item["persona_b"].split("_")[-1]} & actor_numbers]
        persona_score = max(((item["stylometric_similarity"] + item["behavioral_similarity"]) / 2 for item in persona_pairs), default=0.0)
        components = {"evidence": round(support * 0.35, 3), "independence": round(min(1, candidate["independent_evidence_count"] / 6) * 0.2, 3), "persona": round(persona_score * 0.25, 3), "conflict_penalty": round(-conflict * 0.25, 3)}
        components["overall"] = round(max(0.0, min(0.99, sum(components.values()))), 3)
        decomposition.append({"candidate": [candidate["candidate_a"], candidate["candidate_b"]], "components": components})
    fragility = []
    for candidate in candidates:
        base = next(item["components"]["overall"] for item in decomposition if item["candidate"] == [candidate["candidate_a"], candidate["candidate_b"]])
        for signal, delta in (("pgp", .18), ("wallet", .12), ("stylometry", .11), ("behavior", .08)):
            fragility.append({"candidate": [candidate["candidate_a"], candidate["candidate_b"]], "removed_signal": signal, "confidence_after": round(max(0, base - delta), 3), "effect": round(delta, 3)})
    cas = []
    for candidate in candidates:
        breakdown = next(item for item in decomposition if item["candidate"] == [candidate["candidate_a"], candidate["candidate_b"]])
        reasons = []
        if candidate["independent_evidence_count"] < 3: reasons.append("insufficient independent evidence")
        if candidate["conflicting_evidence_ids"]: reasons.append("conflicting evidence detected")
        if breakdown["components"]["overall"] < 0.68: reasons.append("confidence below threshold")
        cas.append({"candidate": [candidate["candidate_a"], candidate["candidate_b"]], "attribution_set": [candidate["candidate_a"], candidate["candidate_b"]] if not reasons else [], "status": "ABSTAIN" if reasons else "SUPPORTED", "coverage_level": 0.95, "reasons": reasons, "supporting_evidence_ids": candidate["supporting_evidence_ids"], "conflicting_evidence_ids": candidate["conflicting_evidence_ids"]})
    total = max(1, evidence_results["total_evidence"])
    dependent = sum(item["dependent_count"] for item in evidence_results["redundancy"])
    conflicting = len(evidence_results["conflicts"])
    calibration = {"independent": round(max(0.0, 1 - conflicting / total), 3), "dependent": round(dependent / total, 3), "redundant": round(max(0.0, (dependent - len(evidence_results["redundancy"])) / total), 3), "instability_warning": any(item["effect"] >= .15 for item in fragility)}
    return {"confidence_decomposition": decomposition, "fragility": fragility, "cas": cas, "calibration": calibration}
