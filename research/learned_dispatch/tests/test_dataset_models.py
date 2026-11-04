import copy
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from research.ml_lab.artifacts import digest, file_hash, write_json
from research.learned_dispatch.dataset import generate, validate_cases, prepare, load, historical_signatures, episode_seed
from research.learned_dispatch.models import CANDIDATES, LearnedPolicy, fit_export, load_model, parse_model
from research.learned_dispatch.teacher import demonstrations, training_matrix
from research.learned_dispatch.features import FEATURE_NAMES, feature_rows
from research.adaptive_dispatch.environment import Action, WAIT, run_episode
from research.adaptive_dispatch.tests.fixtures import problem
from .test_public_features import state


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = generate("smoke")

    def test_deterministic_disjoint_and_fresh(self):
        self.assertEqual(self.rows, generate("smoke"))
        self.assertEqual(validate_cases(self.rows)["groups"], 8)
        self.assertEqual(len(self.rows), 16)
        old, _ = historical_signatures()
        self.assertGreater(len(old), 240)
        self.assertFalse(old & {r["graph_hash"] for r in self.rows})
        seeds = {episode_seed(profile, part, 0) for profile in ("full", "smoke")
                 for part in ("train", "dev", "final_id", "final_shift")}
        self.assertEqual(len(seeds), 8)

    def test_group_contamination_and_tampering_rejected(self):
        for mode in ("split", "hash", "seed", "duplicate"):
            rows = copy.deepcopy(self.rows)
            if mode == "split":
                rows[1]["partition"] = "dev"
            elif mode == "hash":
                rows[0]["graph_hash"] = "0"*64
            elif mode == "seed":
                rows[0]["configuration"]["seed"] += 1
            else:
                rows.append(rows[0])
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                validate_cases(rows)

    def test_partition_loading_does_not_open_final(self):
        from research.ml_lab.access import isolated
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)/"dataset"
            prepare(d, "smoke")
            with isolated(d/"final_id.jsonl.gz", d/"final_shift.jsonl.gz"):
                self.assertEqual(len(load(d, "train")[1]), 4)
                with self.assertRaises(PermissionError):
                    load(d, "final_id")


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Genuine varied tiny teacher labels; smoke data, never a scientific partition.
        rows = []
        for i, p in enumerate((problem(weights=(1, 4)), problem(ticks=(7200, 3600), weights=(5, 1), crews=2))):
            rows.append(dict(group_id="unit-training", partition="train", input_fingerprint=p.fingerprint,
                             problem=p.model_dump(mode="json")))
        cls.shard = demonstrations(rows, "smoke")
        cls.X, cls.y, cls.w, cls.lineage = training_matrix([cls.shard])
        cls.exports = {}
        for name in CANDIDATES:
            payload, reference, _ = fit_export(cls.X, cls.y, cls.w, name, {"purpose": "unit-smoke"})
            cls.exports[name] = payload
            np.testing.assert_allclose(parse_model(payload).predict(cls.X), reference(cls.X), rtol=0, atol=1e-10)

    def test_weighting_and_lineage(self):
        totals = {}
        for lineage, w in zip(self.lineage, self.w):
            totals[lineage] = totals.get(lineage, 0)+w
        np.testing.assert_allclose(list(totals.values()), np.mean(list(totals.values())))
        self.assertGreater(np.ptp(self.y), 0)
        self.assertEqual(self.shard["diagnostics"]["episodes"], 10)
        self.assertTrue(all(r["trajectory_validated"] for r in self.shard["episodes"]))
        self.assertNotIn("durations", self.shard)

    def test_all_candidates_repeat_fit_and_genuine_weights(self):
        for name, original in self.exports.items():
            repeated, _, _ = fit_export(self.X, self.y, self.w, name, {"purpose": "unit-smoke"})
            self.assertEqual(digest(original), digest(repeated))
            trained = parse_model(original)
            self.assertGreater(np.ptp(trained.predict(self.X)), 0)
        self.assertTrue(any(abs(v) > 0 for v in self.exports["ridge-alpha1"]["parameters"]["coefficients"]))

    def test_hash_loader_and_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"model.json"
            write_json(path, self.exports["ridge-alpha1"])
            model, ns = load_model(path, file_hash(path))
            self.assertGreater(ns, 0)
            np.testing.assert_array_equal(model.predict(self.X), parse_model(self.exports["ridge-alpha1"]).predict(self.X))
            with self.assertRaises(ValueError):
                load_model(path, "0"*64)
            text = path.read_text()
            path.write_text('{"version":"learned-dispatch-v1",'+text[1:])
            with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
                load_model(path, file_hash(path))
        for name in self.exports:
            bad = copy.deepcopy(self.exports[name])
            bad["feature_names"][0] = "actual_future"
            with self.assertRaises(ValueError):
                parse_model(bad)

    def test_prediction_failure_fallback_and_malformed_rejection(self):
        model = parse_model(self.exports["forest-depth4"])
        policy = LearnedPolicy(model)
        s = state()
        with patch.object(type(model), "predict", return_value=np.full(len(s.actions()), np.nan)):
            self.assertIn(policy(s), s.actions())
        self.assertEqual(policy.fallbacks[-1]["reason"], "inference-failure")
        count = len(policy.fallbacks)
        with self.assertRaises(ValueError):
            policy(replace(s, now=True))
        self.assertEqual(len(policy.fallbacks), count)

    def test_tree_structure_corruption_rejected(self):
        for corruption in ("cycle", "nan", "feature", "unreachable"):
            bad = copy.deepcopy(self.exports["forest-depth4"])
            tree = bad["parameters"]["trees"][0]
            if corruption == "cycle":
                tree["left"][0] = 0
            elif corruption == "nan":
                tree["value"][0] = float("nan")
            elif corruption == "feature":
                tree["feature"][0] = 999
            else:
                for field in tree:
                    tree[field].append(tree[field][-1])
            with self.subTest(corruption=corruption), self.assertRaises(ValueError):
                parse_model(bad)

    def test_learned_full_rollouts_mask_score_and_fallback(self):
        p = problem(ticks=(3600, 7200, 9000), weights=(3, 2, 1), prerequisites={2: (0,)}, crews=2)
        for payload in self.exports.values():
            policy = LearnedPolicy(parse_model(payload))
            for profile in ("deterministic", "low", "high"):
                a = run_episode(p, profile, 0, policy, "learned")
                b = run_episode(p, profile, 0, policy, "learned")
                self.assertEqual(a["schedule"], b["schedule"])
                self.assertTrue(a["trajectory_validated"])
            self.assertEqual(policy.fallbacks, [])
            s = state(p)
            actions, _ = feature_rows(s)
            scores = [policy.score(s, a) for a in actions]
            self.assertEqual(policy.score(s, policy(s)), max(scores))
            with self.assertRaises(ValueError):
                policy.score(s, WAIT)
            policy(state(problem(unresolved=True)))
            self.assertEqual(policy.fallbacks[-1]["reason"], "unsupported-public-scope")
        with self.assertRaises(ValueError):
            LearnedPolicy(None)
        fallback = LearnedPolicy(None, allow_no_model=True)
        self.assertIn(fallback(state()), state().actions())
        self.assertEqual(fallback.fallbacks[0]["reason"], "explicit-no-model")


if __name__ == "__main__":
    unittest.main()
