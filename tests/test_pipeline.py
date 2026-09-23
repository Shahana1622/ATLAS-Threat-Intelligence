import unittest

from threat_platform.services.generator import generate_dataset
from threat_platform.services.pipeline import run_analysis


class PipelineIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.dataset = generate_dataset()
        self.analysis = run_analysis(self.dataset)

    def candidate(self, actor_a, actor_b):
        return next(item for item in self.analysis["attribution"]["candidates"] if item["candidate_a"] == actor_a and item["candidate_b"] == actor_b)

    def test_dataset_has_connected_scale(self):
        self.assertGreaterEqual(len(self.dataset["evidence"]), 100)
        self.assertGreaterEqual(len(self.dataset["behavioral_events"]), 100)
        self.assertGreaterEqual(len(self.dataset["posts"]), 50)
        self.assertGreaterEqual(len(self.dataset["relationships"]), 100)
        self.assertTrue(all(item["evidence_ids"] for item in self.dataset["relationships"]))

    def test_strong_candidate_uses_multiple_independent_signals(self):
        result = self.candidate("Actor_001", "Actor_007")
        self.assertEqual(result["relationship_type"], "CANDIDATE_IDENTITY_LINK")
        self.assertGreaterEqual(result["independent_evidence_count"], 6)
        self.assertEqual(len(result["supporting_evidence_ids"]), 6)

    def test_false_link_and_conflict_are_detected(self):
        false_link = self.candidate("Actor_002", "Actor_009")
        conflict = self.candidate("Actor_003", "Actor_010")
        self.assertEqual(false_link["relationship_type"], "POSSIBLE_FALSE_LINK")
        self.assertTrue(false_link["conflicting_evidence_ids"])
        self.assertTrue(conflict["conflicting_evidence_ids"])
        self.assertTrue(self.analysis["reliability"]["calibration"]["instability_warning"])

    def test_redundancy_insufficiency_and_cas(self):
        self.assertTrue(self.analysis["evidence"]["redundancy"])
        weak = self.candidate("Actor_005", "Actor_012")
        cas = next(item for item in self.analysis["reliability"]["cas"] if item["candidate"] == ["Actor_005", "Actor_012"])
        self.assertLess(weak["confidence"], 0.68)
        self.assertEqual(cas["status"], "ABSTAIN")
        self.assertTrue(cas["reasons"])

    def test_persona_migration_rebranding_and_infrastructure(self):
        self.assertTrue(self.analysis["persona"]["rebranding"])
        self.assertEqual(self.analysis["persona"]["migration"][0]["path"], ["Forum_001", "Marketplace_002", "Forum_003"])
        self.assertTrue(any(item["similarity"] > 0 for item in self.analysis["attribution"]["infrastructure_correlations"]))

    def test_pipeline_outputs_are_reproducible(self):
        self.assertEqual(self.analysis, run_analysis(generate_dataset()))


if __name__ == "__main__":
    unittest.main()
