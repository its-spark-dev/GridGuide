"""Source-dependent G1 reproduction; not part of the source-free synthetic lane.

Missing challenge files are an error here, never a passing skipped audit.
"""
import json
from pathlib import Path
import unittest

from scripts.phase1_evidence import report


class SourceEvidenceTests(unittest.TestCase):
    def test_checked_in_aggregate_evidence_reproduces_from_pinned_sources(self):
        expected = json.loads((Path(__file__).resolve().parents[1] /
                               "docs/research/phase1/source_coverage.json").read_text())
        actual = report()
        self.assertEqual(actual, expected)
        network = actual["network"]
        self.assertEqual(network["topology_paths"], 117599)
        self.assertEqual(network["fully_verified_paths"], 40779)
        terminals = network["by_kind"]["Circuit Breaker"]["fully_verified_reverse_assets"]
        self.assertEqual(network["fully_verified_reverse_assets"] - terminals, 8093)
        self.assertEqual(actual["damage_quality"]["zero_outage_ids"], 1659)
        self.assertIsNone(actual["damage_quality"]["observed_outage_duration_targets"])


if __name__ == "__main__":
    unittest.main()
