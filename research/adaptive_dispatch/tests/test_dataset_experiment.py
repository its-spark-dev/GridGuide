import copy
import json
from pathlib import Path
import tempfile
import unittest

from research.ml_lab.access import isolated
from research.ml_lab.artifacts import read_json
from research.adaptive_dispatch.dataset import episode_seed, generate, load, prepare, validate_cases
from research.adaptive_dispatch.experiment import METHODS, REACTIVE, TEACHER, execute, paired, run, summarize
from research.adaptive_dispatch.tests.fixtures import problem


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = generate("smoke")

    def test_deterministic_diverse_grouped_generation(self):
        self.assertEqual(self.rows, generate("smoke"))
        self.assertEqual(validate_cases(self.rows), dict(cases=16, groups=8, partitions={"discovery": 8, "confirmation": 8}))
        self.assertEqual(len({r["graph_hash"] for r in self.rows}), 8)
        for row in self.rows:
            self.assertNotIn("metrics", row)
            self.assertNotIn("durations", row)
            self.assertTrue(10 <= len(row["problem"]["tasks"]) <= 14)

    def test_split_and_identity_rejection(self):
        for change in ("partition", "input_fingerprint", "graph_hash"):
            rows = copy.deepcopy(self.rows)
            rows[1][change] = "confirmation" if change == "partition" else "wrong"
            with self.assertRaises(ValueError):
                validate_cases(rows)
        with self.assertRaises(ValueError):
            validate_cases(self.rows[:-1])

    def test_distinct_duration_namespaces(self):
        seeds = [episode_seed(profile, stage, i) for profile in ("full", "smoke")
                 for stage in ("discovery", "confirmation") for i in range(16)]
        self.assertEqual(len(seeds), len(set(seeds)))

    def test_immutable_manifest_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp)/"inputs"
            with isolated():
                manifest = prepare(destination, "smoke")
                self.assertEqual(load(destination)[1], self.rows)
            with self.assertRaises(ValueError):
                prepare(destination, "smoke")
            path = destination/"cases.jsonl.gz"
            path.write_bytes(path.read_bytes()+b"changed")
            with self.assertRaises(ValueError):
                load(destination)
            self.assertEqual(manifest["counts"]["groups"], 8)

    def test_stages_refuse_unfrozen_inputs_and_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prepare(root/"inputs", "smoke")
            with self.assertRaisesRegex(ValueError, "requires completed discovery"):
                run(root/"inputs", root/"confirmation", "confirmation")
            self.assertFalse((root/"confirmation").exists())
            with self.assertRaisesRegex(ValueError, "already-used"):
                run(root/"inputs", root/"inputs", "discovery")
            path = root/"inputs/manifest.json"
            manifest = read_json(path)
            manifest["source_hashes"]["research/adaptive_dispatch/environment.py"] = "changed"
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "changed since input seal"):
                run(root/"inputs", root/"discovery", "discovery")
            self.assertFalse((root/"discovery").exists())


class ExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = []
        p = problem(ticks=(3600, 7200, 9000), weights=(1, 4, 3), crews=2)
        for group in range(2):
            for profile in ("deterministic", "low", "high"):
                for method in METHODS:
                    result = execute(p, profile, group, method)
                    cls.rows.append(dict(result, case_id=f"fixture-{group}", group_id=f"group-{group}", method=method))

    def test_grouped_pairing_and_mean(self):
        rows = [r for r in self.rows if r["profile"] != "deterministic"]
        result = paired(rows, REACTIVE[0], TEACHER)
        self.assertEqual(result["supported_groups"], 2)
        self.assertEqual(result["supported_episodes"], 4)
        self.assertAlmostEqual(result["improvement"], sum(result["per_group_improvement"].values())/2)
        self.assertEqual(result["wins"]+result["ties"]+result["losses"], 4)

    def test_common_draws_and_missing_comparators_rejected(self):
        with self.assertRaises(ValueError):
            summarize(self.rows[:-1])
        with self.assertRaises(ValueError):
            summarize(self.rows+[self.rows[0]])
        corrupted = copy.deepcopy(self.rows)
        next(r for r in corrupted if r["method"] == TEACHER)["durations"]["syn-t0"] += 1
        with self.assertRaises(ValueError):
            paired(corrupted, REACTIVE[0], TEACHER)

    def test_discovery_selection_is_fixed_on_confirmation(self):
        result = summarize(self.rows)
        selected = result["selected"]
        altered = copy.deepcopy(self.rows)
        for row in altered:
            if row["method"] == selected["dynamic"]:
                row["metrics"]["modeled_customer_outage_hours"] *= 10
        confirmation = summarize(altered, selected)
        self.assertEqual(confirmation["selected"], selected)
        self.assertFalse(confirmation["gate"]["teacher_headroom"] and confirmation["comparisons"]["teacher_headroom"]["improvement"] < 0)


if __name__ == "__main__":
    unittest.main()
