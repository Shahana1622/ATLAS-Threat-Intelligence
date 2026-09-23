from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.threat_platform.models.schemas import validate_dataset


def dataset_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "generated.json"


def save_dataset(dataset: dict[str, Any], path: Path) -> None:
    validate_dataset(dataset)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dataset, indent=2) + "\n", encoding="utf-8")


def load_dataset(path: Path) -> dict[str, Any]:
    dataset = json.loads(path.read_text(encoding="utf-8"))
    validate_dataset(dataset)
    return dataset

