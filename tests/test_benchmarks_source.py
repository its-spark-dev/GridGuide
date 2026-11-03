"""Explicit source-dependent lane; absent sources never count as success."""
import unittest
from benchmarks.legacy import verify


class LegacyBenchmarkTests(unittest.TestCase):
    def test_exact_four_candidate_legacy_regressions(self):
        result=verify()
        self.assertEqual(result['status'],'passed')
        self.assertEqual(result['cases'],24)
