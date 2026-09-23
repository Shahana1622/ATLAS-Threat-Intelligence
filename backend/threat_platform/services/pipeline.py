from __future__ import annotations

from typing import Any

from backend.threat_platform.algorithms.attribution import attribution_resolution
from backend.threat_platform.algorithms.evidence import evidence_intelligence
from backend.threat_platform.algorithms.persona import persona_intelligence
from backend.threat_platform.algorithms.reliability import reliability_analysis


def run_analysis(dataset: dict[str, Any]) -> dict[str, Any]:
    evidence = evidence_intelligence(dataset)
    persona = persona_intelligence(dataset)
    attribution = attribution_resolution(dataset, persona)
    reliability = reliability_analysis(evidence, attribution, persona)
    return {"evidence": evidence, "persona": persona, "attribution": attribution, "reliability": reliability, "data_origin": "synthetic"}
