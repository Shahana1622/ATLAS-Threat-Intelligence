import json
import unittest

from backend.threat_platform.services.generator import generate_dataset
from backend.threat_platform.services.investigator import (
    build_audit_trail,
    build_coverage_validation,
    build_dashboard,
    build_graph,
    build_report,
    build_timeline,
    cas_explanation,
    export_csv,
    export_json,
    export_pdf,
    investigate_actor,
)


class InvestigatorTests(unittest.TestCase):
    def setUp(self):
        self.dataset = generate_dataset()

    def test_dashboard_uses_synthetic_counts(self):
        dashboard = build_dashboard(self.dataset)
        self.assertEqual(dashboard["data_origin"], "synthetic")
        self.assertEqual(dashboard["counts"]["actors"], 15)
        self.assertEqual(dashboard["counts"]["evidence"], 120)

    def test_actor_investigation_is_traceable(self):
        result = investigate_actor(self.dataset, "Actor_001")
        self.assertEqual(result["actor"]["actor_id"], "Actor_001")
        self.assertIn("Evidence_001", [item["evidence_id"] for item in result["evidence"]])
        self.assertTrue(result["synthetic_attribution_hypothesis"])

    def test_timeline_is_sorted_and_filterable(self):
        timeline = build_timeline(self.dataset, actor_id="Actor_001")
        self.assertEqual(timeline, sorted(timeline, key=lambda item: item["timestamp"]))
        self.assertTrue(all("Actor_002" not in item["entity_ids"] for item in timeline))

    def test_graph_preserves_evidence_ids(self):
        graph = build_graph(self.dataset)
        self.assertGreaterEqual(len(graph["nodes"]), 2)
        self.assertEqual(graph["edges"][0]["evidence_ids"], ["Evidence_001"])

    def test_cas_explanation_is_deterministic(self):
        first = cas_explanation(self.dataset, "Actor_001")
        second = cas_explanation(self.dataset, "Actor_001")
        self.assertEqual(first, second)
        self.assertEqual(first["data_origin"], "synthetic")

    def test_coverage_validation_does_not_fabricate_results(self):
        coverage = build_coverage_validation()
        self.assertEqual(coverage["status"], "NO_UPSTREAM_EVALUATION")
        self.assertIsNone(coverage["synthetic_accuracy"])

    def test_audit_report_and_exports(self):
        report = build_report(self.dataset, "Actor_001")
        audit = build_audit_trail([{"action": "actor_selected", "entity_ids": ["Actor_001"]}])
        self.assertEqual(audit[0]["event_id"], "Audit_001")
        self.assertIn("synthetic demonstration data", report["statement"])
        self.assertIn(b"section,key,value", export_csv(report))
        self.assertEqual(json.loads(export_json(report))["data_origin"], "synthetic")
        self.assertTrue(export_pdf(report).startswith(b"%PDF-1.4"))


if __name__ == "__main__":
    unittest.main()
