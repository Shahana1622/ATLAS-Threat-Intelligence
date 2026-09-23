from __future__ import annotations

from collections import defaultdict
from typing import Any


def source_reliability(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"source_id": source["source_id"], "reliability": source["reliability"], "source_family": source["source_family"], "explanation": "Configured fixture reliability adjusted by observed supporting/conflicting direction."} for source in dataset["sources"]]


def evidence_intelligence(dataset: dict[str, Any]) -> dict[str, Any]:
    evidence = dataset["evidence"]
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in evidence:
        source = next((record for record in dataset["sources"] if record["source_id"] == item["source_id"]), {})
        by_family[source.get("source_family", item["independence_group"])].append(item)
    independent_groups = {item["independence_group"] for item in evidence}
    conflicts = [item["evidence_id"] for item in evidence if item["direction"] == "contradicts"]
    redundancy = [{"source_family": family, "evidence_ids": [item["evidence_id"] for item in items], "dependent_count": len(items)} for family, items in by_family.items() if len(items) > 1]
    nodes = []
    edges = []
    for field, node_type in (("actors", "Actor"), ("personas", "Persona"), ("handles", "Handle"), ("pgp_identifiers", "PGP"), ("wallet_identifiers", "Wallet"), ("infrastructure", "Infrastructure"), ("evidence", "Evidence"), ("sources", "Source")):
        for record in dataset[field]:
            identifier = next((value for key, value in record.items() if key.endswith("_id")), None)
            if identifier:
                nodes.append({"id": identifier, "type": node_type})
    for relationship in dataset["relationships"]:
        edges.append({"source": relationship["source_entity"], "target": relationship["target_entity"], "type": relationship["relationship_type"], "strength": relationship["strength"], "evidence_ids": relationship["evidence_ids"]})
    return {"provenance": evidence, "source_reliability": source_reliability(dataset), "independent_evidence_count": len(independent_groups), "total_evidence": len(evidence), "common_sources": [{"source_family": family, "evidence_ids": [item["evidence_id"] for item in items]} for family, items in by_family.items() if len(items) > 1], "conflicts": conflicts, "redundancy": redundancy, "graph": {"nodes": nodes, "edges": edges}}
