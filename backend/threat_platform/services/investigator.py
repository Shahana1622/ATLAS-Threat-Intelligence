from __future__ import annotations

import csv
import io
import json
from typing import Any, Iterable

from backend.threat_platform.models.schemas import DATA_ORIGIN


def _records(dataset: dict[str, Any], field: str) -> list[dict[str, Any]]:
    return [record for record in dataset.get(field, []) if isinstance(record, dict)]


def _confidence(evidence: Iterable[dict[str, Any]]) -> float:
    records = list(evidence)
    if not records:
        return 0.0
    return round(sum(item["strength"] * item["reliability"] for item in records) / len(records), 3)


def build_graph(dataset: dict[str, Any]) -> dict[str, Any]:
    node_fields = {"actors": "Actor", "personas": "Persona", "handles": "Handle",
                   "pgp_identifiers": "PGP", "wallet_identifiers": "Wallet",
                   "infrastructure": "Infrastructure", "evidence": "Evidence", "sources": "Source"}
    nodes = []
    for field, node_type in node_fields.items():
        for record in _records(dataset, field):
            identifier = next((value for key, value in record.items() if key.endswith("_id")), None)
            if identifier:
                nodes.append({"id": identifier, "type": node_type,
                              "label": record.get("name", record.get("value", identifier)),
                              "data_origin": DATA_ORIGIN})
    edges = [{"id": item["relationship_id"], "source": item["source_entity"],
              "target": item["target_entity"], "relationship_type": item["relationship_type"],
              "strength": item["strength"], "evidence_ids": item["evidence_ids"],
              "data_origin": DATA_ORIGIN} for item in _records(dataset, "relationships")]
    return {"nodes": nodes, "edges": edges, "data_origin": DATA_ORIGIN}


def build_dashboard(dataset: dict[str, Any], analyses: dict[str, Any] | None = None) -> dict[str, Any]:
    analyses = analyses or {}
    evidence = _records(dataset, "evidence")
    results = analyses.get("reliability", {}).get("cas", analyses.get("attribution_results", []))
    distribution = [item["components"]["overall"] for item in analyses.get("reliability", {}).get("confidence_decomposition", [])]
    return {"data_origin": DATA_ORIGIN, "dataset_label": "Fictional investigation fixture",
            "counts": {"actors": len(_records(dataset, "actors")),
                       "personas": len(_records(dataset, "personas")), "evidence": len(evidence),
                       "relationships": len(_records(dataset, "relationships")),
                       "sources": len(_records(dataset, "sources")),
                       "conflicting_evidence": sum(item.get("direction") == "contradicts" for item in evidence),
                       "candidate_links": len(analyses.get("attribution", {}).get("candidates", [])) or sum(item.get("relationship_type") == "candidate_identity_link" for item in _records(dataset, "relationships")),
                       "abstentions": sum(item.get("status") == "ABSTAIN" for item in results)},
            "confidence_distribution": distribution or [item.get("confidence", 0) for item in results],
            "limitations": ["All entities, signals, and results are synthetic.",
                            "This view does not establish a real person's identity."]}


def investigate_actor(dataset: dict[str, Any], actor_id: str) -> dict[str, Any]:
    actor = next((item for item in _records(dataset, "actors") if item.get("actor_id") == actor_id), None)
    if actor is None:
        raise KeyError(actor_id)
    personas = [item for item in _records(dataset, "personas") if item.get("actor_id") == actor_id]
    evidence = [item for item in _records(dataset, "evidence")
                if actor_id in (item.get("actor_id"), item.get("candidate_actor_id"))]
    relationships = [item for item in _records(dataset, "relationships")
                     if actor_id in (item.get("source_entity"), item.get("target_entity"))]
    conflicting = [item["evidence_id"] for item in evidence if item.get("direction") == "contradicts"]
    groups = sorted({item["independence_group"] for item in evidence})
    return {"data_origin": DATA_ORIGIN, "actor": actor, "personas": personas,
            "handles": sorted({handle for persona in personas for handle in persona.get("handles", [])}),
            "platforms": sorted({platform for persona in personas for platform in persona.get("platforms", [])}),
            "evidence": evidence, "relationships": relationships,
            "confidence": _confidence(item for item in evidence if item.get("direction") == "supports"),
            "independent_evidence_count": len(groups), "conflicting_evidence_ids": conflicting,
            "attribution_status": "SUPPORTED" if evidence and not conflicting else "UNCERTAIN",
            "synthetic_attribution_hypothesis": True}


def build_timeline(dataset: dict[str, Any], actor_id: str | None = None,
                   start: str | None = None, end: str | None = None) -> list[dict[str, Any]]:
    events = []
    persona_by_id = {item.get("persona_id"): item for item in _records(dataset, "personas")}
    for item in _records(dataset, "evidence"):
        if not actor_id or actor_id in (item.get("actor_id"), item.get("candidate_actor_id")):
            events.append({"timestamp": item["timestamp"], "event_type": "evidence",
                           "entity_ids": [item["evidence_id"]], "description": item["description"]})
    for item in _records(dataset, "behavioral_events"):
        persona = persona_by_id.get(item.get("persona_id"), {})
        if not actor_id or persona.get("actor_id") == actor_id:
            events.append({"timestamp": item["timestamp"], "event_type": "persona_activity",
                           "entity_ids": [item.get("persona_id"), item["event_id"]],
                           "description": item.get("description", item.get("event_type", "activity"))})
    for item in _records(dataset, "relationships"):
        if not actor_id or actor_id in (item.get("source_entity"), item.get("target_entity")):
            events.append({"timestamp": item["timestamp"], "event_type": "relationship",
                           "entity_ids": [item["relationship_id"], item["source_entity"], item["target_entity"]],
                           "description": item["relationship_type"]})
    events.sort(key=lambda value: value["timestamp"])
    return [event for event in events if (not start or event["timestamp"] >= start)
            and (not end or event["timestamp"] <= end)]


def cas_explanation(dataset: dict[str, Any], actor_id: str | None = None, analyses: dict[str, Any] | None = None) -> dict[str, Any]:
    if analyses and analyses.get("reliability", {}).get("cas"):
        matches = [item for item in analyses["reliability"]["cas"] if not actor_id or actor_id in item.get("candidate", [])]
        if matches:
            result = matches[0].copy()
            result.update({"data_origin": DATA_ORIGIN, "explanation": "CAS result calculated from evidence independence, conflicts, persona signals, and confidence decomposition."})
            return result
    evidence = _records(dataset, "evidence")
    if actor_id:
        evidence = [item for item in evidence if actor_id in (item.get("actor_id"), item.get("candidate_actor_id"))]
    groups = {item.get("independence_group") for item in evidence}
    conflicting = [item["evidence_id"] for item in evidence if item.get("direction") == "contradicts"]
    reasons = []
    if len(groups) < 2:
        reasons.append("insufficient independent evidence")
    if conflicting:
        reasons.append("conflicting evidence detected")
    if not evidence:
        reasons.append("no evidence selected")
    return {"status": "ABSTAIN" if reasons else "SYNTHETIC_SUPPORTED_SET", "reasons": reasons,
            "supporting_evidence_ids": [item["evidence_id"] for item in evidence if item.get("direction") == "supports"],
            "conflicting_evidence_ids": conflicting, "data_origin": DATA_ORIGIN,
            "explanation": "CAS-style investigator summary derived from local synthetic records; it is not a real-world identity claim."}


def build_coverage_validation(evaluation: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    cases = evaluation or []
    counts = {status: sum(item.get("status") == status for item in cases)
              for status in ("SUPPORTED", "UNCERTAIN", "ABSTAIN")}
    correct = sum(item.get("correct", False) for item in cases)
    return {"data_origin": DATA_ORIGIN, "synthetic_evaluation": True,
            "total_cases": len(cases), "supported_cases": counts["SUPPORTED"],
            "uncertain_cases": counts["UNCERTAIN"], "abstained_cases": counts["ABSTAIN"],
            "synthetic_coverage": round((len(cases) - counts["ABSTAIN"]) / len(cases), 3) if cases else None,
            "synthetic_accuracy": round(correct / len(cases), 3) if cases else None,
            "status": "NO_UPSTREAM_EVALUATION" if not cases else "SYNTHETIC_ONLY",
            "explanation": "No A-D evaluation payload is present in this foundation-only checkout." if not cases
            else "Metrics apply only to the supplied synthetic evaluation cases."}


def build_audit_trail(actions: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    actions = actions or [{"action": "investigation_started"}]
    return [{"event_id": f"Audit_{index:03d}", "timestamp": "2025-01-01T00:00:00Z",
             "action": action["action"], "entity_ids": action.get("entity_ids", []),
             "evidence_ids": action.get("evidence_ids", []), "parameters": action.get("parameters", {}),
             "data_origin": DATA_ORIGIN} for index, action in enumerate(actions, 1)]


def build_report(dataset: dict[str, Any], actor_id: str | None = None, analyses: dict[str, Any] | None = None) -> dict[str, Any]:
    report = {"title": "Synthetic Investigator Report",
              "statement": "This report was generated from synthetic demonstration data.",
              "dashboard": build_dashboard(dataset, analyses), "graph": build_graph(dataset),
              "timeline": build_timeline(dataset, actor_id), "cas": cas_explanation(dataset, actor_id),
              "audit": build_audit_trail([{"action": "investigation_started", "entity_ids": [actor_id] if actor_id else []},
                                          {"action": "report_generated", "entity_ids": [actor_id] if actor_id else []}]),
              "limitations": ["No external services or datasets are used.", "Signals are synthetic and illustrative.",
                              "Candidate relationships must not be interpreted as proof of identity."],
              "analysis": analyses or {}, "data_origin": DATA_ORIGIN}
    if actor_id:
        report["actor_investigation"] = investigate_actor(dataset, actor_id)
    return report


def export_csv(report: dict[str, Any]) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["section", "key", "value"])
    for section, value in report.items():
        if isinstance(value, (str, int, float, bool)):
            writer.writerow([section, "", value])
        elif isinstance(value, dict):
            for key, nested in value.items():
                writer.writerow([section, key, json.dumps(nested, sort_keys=True)])
    return output.getvalue().encode("utf-8")


def export_json(report: dict[str, Any]) -> bytes:
    return (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")


def export_pdf(report: dict[str, Any]) -> bytes:
    lines = [report["title"], report["statement"], f"Actors: {report['dashboard']['counts']['actors']}",
             f"Evidence: {report['dashboard']['counts']['evidence']}", "Synthetic data only."]
    text = " BT /F1 12 Tf 72 720 Td " + " ".join(f"({line.replace('(', '[').replace(')', ']')}) Tj 0 -18 Td" for line in lines) + " ET"
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>", f"<< /Length {len(text.encode())} >>\nstream\n{text}\nendstream".encode()]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for index, obj in enumerate(objects, 1):
        offsets.append(len(pdf)); pdf.extend(f"{index} 0 obj\n".encode()); pdf.extend(obj); pdf.extend(b"\nendobj\n")
    start = len(pdf); pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    pdf.extend("".join(f"{offset:010d} 00000 n \n" for offset in offsets).encode())
    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n".encode())
    return bytes(pdf)