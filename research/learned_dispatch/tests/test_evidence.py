"""Read-only checks of the retained scientific training artifacts; never retrain them."""
from pathlib import Path
import unittest

import numpy as np

from research.ml_lab.artifacts import ROOT, file_hash, read_json
from research.learned_dispatch.features import feature_rows
from research.learned_dispatch.models import LearnedPolicy
from research.learned_dispatch.teacher import load_shards, restore, label
from research.learned_dispatch.training import approved_models


class RetainedEvidenceTests(unittest.TestCase):
    def test_retained_models_and_teacher_label_replay(self):
        root = ROOT/"docs/learned-dispatch/evidence"
        info = read_json(root/"training/training.json")
        models, timings = approved_models(root/"training")
        self.assertEqual(set(models), set(info["models"]))
        self.assertTrue(all(ns > 0 for ns in timings.values()))
        for name, row in info["models"].items():
            self.assertEqual(file_hash(root/"training"/row["file"]), row["sha256"])
            self.assertTrue(row["exact_repeat_export"])
        shards = load_shards(root/"dataset", root/"teacher")
        self.assertEqual(len(shards), 48)
        self.assertEqual(sum(s["diagnostics"]["episodes"] for s in shards), 480)
        states_checked = 0
        for shard in shards:
            for record in shard["states"]:
                observation = restore(shard, record)
                self.assertEqual(label(observation), record["label"])
                states_checked += 1
            # Independent model loading and feasible inference on each configuration.
            observation = restore(shard, next(r for r in shard["states"] if r["label"]["discretionary"]))
            actions, X = feature_rows(observation)
            for model in models.values():
                self.assertTrue(np.isfinite(model.predict(X)).all())
                policy = LearnedPolicy(model)
                self.assertIn(policy(observation), actions)
                self.assertEqual(policy.fallbacks, [])
        self.assertEqual(states_checked, 12055)


if __name__ == "__main__":
    unittest.main()
