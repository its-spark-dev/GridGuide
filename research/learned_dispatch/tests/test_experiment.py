from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from research.ml_lab.artifacts import read_json
from research.learned_dispatch import dataset, experiment, training
from research.learned_dispatch.analysis import paired_arrays, select
from research.learned_dispatch.models import CANDIDATES
from research.learned_dispatch.teacher import collect


class AnalysisTests(unittest.TestCase):
    def test_paired_configuration_estimator_and_uncertainty(self):
        result = paired_arrays({"a": 1., "b": 3.}, {"a": 2., "b": 6.})
        self.assertEqual(result["ratio"], 2.)
        np.testing.assert_allclose(result["ratio_ci95"], [2., 2.])
        self.assertEqual(result["degradation"], 2.)
        self.assertEqual(paired_arrays({}, {})["groups"], 0)

    def test_selection_uses_rollout_means_not_accuracy_or_runtime(self):
        values = {n: dict(mean_waiting_hours=10., agreement=1., timing=0.) for n in CANDIDATES}
        values["forest-depth8"]["mean_waiting_hours"] = 8.
        values["forest-depth8"]["agreement"] = 0.
        selected = select(dict(aggregates={"stochastic_pooled": values}))
        self.assertEqual(selected["champion"], "forest-depth8")
        self.assertEqual(selected["family_winners"]["ridge"], "ridge-alpha0.1")


class PipelineTests(unittest.TestCase):
    def test_real_fit_development_freeze_resumption_and_spent_guards(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d, t, labels = root/"dataset", root/"training", root/"teacher"
            dataset.prepare(d, "smoke")
            self.assertEqual(collect(d, labels, 1)["completed_groups"], 1)
            self.assertEqual(collect(d, labels, 1)["completed_groups"], 2)
            trained = training.fit(d, labels, t)
            self.assertEqual(set(trained["models"]), set(CANDIDATES))
            self.assertTrue(all(v["exact_repeat_export"] for v in trained["models"].values()))
            self.assertFalse(experiment.run(d, t, root/"dev", "dev", max_groups=1)["complete"])
            self.assertTrue(experiment.run(d, t, root/"dev", "dev", max_groups=1)["complete"])
            self.assertEqual(experiment.audit(d, t, root/"dev")["status"], "PASS")
            with self.assertRaises(ValueError):
                experiment.run(d, t, root/"dev", "dev")
            with self.assertRaises(ValueError):
                experiment.run(d, t, root/"final_id", "final_id")
            frozen = root/"freeze.json"
            experiment.freeze(d, t, root/"dev", frozen)
            # Simulated interruption before any episode: preserve failure and resume same receipt.
            with patch("research.learned_dispatch.experiment.execute", side_effect=RuntimeError("test interruption")):
                with self.assertRaises(RuntimeError):
                    experiment.run(d, t, root/"final_id", "final_id", max_groups=1, frozen_path=frozen)
            self.assertTrue((d/"evaluation-receipt.json").exists())
            self.assertEqual(len(list((root/"final_id/failures").glob("*.json"))), 1)
            with self.assertRaises(ValueError):
                training.fit(d, labels, root/"refit")
            with self.assertRaises(ValueError):
                collect(d, root/"relabel")
            with self.assertRaises(ValueError):
                experiment.run(d, t, root/"newdev", "dev")
            with self.assertRaises(ValueError):
                experiment.run(d, t, root/"different-root/final_id", "final_id", frozen_path=frozen)
            self.assertFalse(experiment.run(d, t, root/"final_id", "final_id", max_groups=1, frozen_path=frozen)["complete"])
            self.assertTrue(experiment.run(d, t, root/"final_id", "final_id", max_groups=1, frozen_path=frozen)["complete"])
            self.assertEqual(experiment.audit(d, t, root/"final_id")["status"], "PASS")
            summary = read_json(root/"final_id/summary.json")
            self.assertFalse(summary["promotion"]["support"])
            self.assertFalse(summary["promotion"]["pass"])
            with self.assertRaises(ValueError):
                experiment.run(d, t, root/"final_id", "final_id", frozen_path=frozen)


if __name__ == "__main__":
    unittest.main()
