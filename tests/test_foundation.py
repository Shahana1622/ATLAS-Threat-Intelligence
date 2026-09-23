import json
import tempfile
import unittest
from pathlib import Path

from backend.threat_platform.models.schemas import validate_dataset
from backend.threat_platform.services.generator import generate_dataset
from backend.threat_platform.services.storage import load_dataset, save_dataset


class FoundationTests(unittest.TestCase):
    def setUp(self):
        self.dataset = generate_dataset()

    def test_generation_is_synthetic_and_complete(self):
        self.assertEqual(self.dataset["data_origin"], "synthetic")
        for field in ("actors", "personas", "handles", "marketplaces", "forums",
                      "pgp_identifiers", "wallet_identifiers", "infrastructure",
                      "posts", "behavioral_events", "evidence", "relationships"):
            self.assertTrue(self.dataset[field], field)

    def test_schema_validity(self):
        validate_dataset(self.dataset)

    def test_ids_are_unique(self):
        for records in self.dataset.values():
            if isinstance(records, list):
                ids = [next((value for key, value in record.items() if key.endswith("_id")), None)
                       for record in records]
                ids = [value for value in ids if value is not None]
                self.assertEqual(len(ids), len(set(ids)))

    def test_records_load_correctly(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dataset.json"
            save_dataset(self.dataset, path)
            loaded = load_dataset(path)
        self.assertEqual(len(loaded["evidence"]), 120)
        self.assertEqual(len(loaded["relationships"]), 120)
        self.assertEqual(len(loaded["personas"]), 18)

    def test_storage_is_plain_local_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dataset.json"
            save_dataset(self.dataset, path)
            parsed = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(parsed["data_origin"], "synthetic")
            self.assertNotIn("http://", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

