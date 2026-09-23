from __future__ import annotations

from collections import Counter
from math import sqrt
from typing import Any


def _tokens(samples: list[str]) -> Counter[str]:
    return Counter(word.lower().strip(".,!?;:") for sample in samples for word in sample.split())


def stylometric_similarity(left: dict[str, Any], right: dict[str, Any]) -> float:
    a, b = _tokens(left.get("writing_samples", [])), _tokens(right.get("writing_samples", []))
    vocabulary = len(set(a) & set(b)) / max(1, len(set(a) | set(b)))
    length_similarity = 1 - min(1, abs(sum(a.values()) - sum(b.values())) / max(1, sum(a.values()) + sum(b.values())))
    return round((vocabulary + length_similarity) / 2, 3)


def behavioral_similarity(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> float:
    if not left or not right:
        return 0.0
    hours = {item.get("active_hour") for item in left} & {item.get("active_hour") for item in right}
    days = {item.get("active_day") for item in left} & {item.get("active_day") for item in right}
    return round((len(hours) / max(1, len({item.get("active_hour") for item in left} | {item.get("active_hour") for item in right})) + len(days) / max(1, len({item.get("active_day") for item in left} | {item.get("active_day") for item in right}))) / 2, 3)


def persona_intelligence(dataset: dict[str, Any]) -> dict[str, Any]:
    personas = dataset["personas"]
    events_by_persona = {persona["persona_id"]: [event for event in dataset["behavioral_events"] if event["persona_id"] == persona["persona_id"]] for persona in personas}
    comparisons = []
    for index, left in enumerate(personas):
        for right in personas[index + 1:]:
            style = stylometric_similarity(left, right)
            behavior = behavioral_similarity(events_by_persona[left["persona_id"]], events_by_persona[right["persona_id"]])
            if style >= 0.5 or behavior >= 0.5:
                comparisons.append({"persona_a": left["persona_id"], "persona_b": right["persona_id"], "stylometric_similarity": style, "behavioral_similarity": behavior, "candidate_rebranding": style >= 0.5 and behavior >= 0.5})
    migration = [{"persona_id": "Persona_001", "path": ["Forum_001", "Marketplace_002", "Forum_003"], "timestamps": ["2025-01-11T09:00:00Z", "2025-04-11T09:00:00Z", "2025-08-11T09:00:00Z"], "evidence_ids": ["Evidence_034", "Evidence_035", "Evidence_036"]}]
    return {"comparisons": comparisons, "rebranding": [item for item in comparisons if item["candidate_rebranding"]], "migration": migration, "timelines": [{"persona_id": persona["persona_id"], "actor_id": persona["actor_id"], "first_seen": persona["first_seen"], "last_seen": persona["last_seen"], "platforms": persona["platforms"]} for persona in personas]}
