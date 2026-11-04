"""Phase 2 validity, leakage and baseline checks without challenge data."""
import ast
import inspect
import math
import unittest
from unittest.mock import patch

from benchmarks.contracts import BenchmarkProblem
from benchmarks.policies import POLICIES
from research.ml_lab import features
from research.ml_lab.baselines import fit_baselines, heuristic
from research.ml_lab.features import FEATURE_NAMES, FEATURE_SCHEMA, extract_features, inference_supported
from research.ml_lab.labels import evaluate_problem


def example(**overrides):
    raw = dict(id="syn-case", family="test", seed=1, split="micro",
        tasks=[dict(id="syn-a", total_person_hours="2", report_order=0),
               dict(id="syn-b", total_person_hours="1", report_order=1)],
        groups=[dict(id="syn-ga", customer_ids=["syn-ca"], required_tasks=["syn-a"], branch="syn-ba"),
                dict(id="syn-gb", customer_ids=["syn-cb", "syn-cc", "syn-cd"],
                     required_tasks=["syn-b"], branch="syn-bb", critical_service=True)],
        crews=[dict(id="syn-crew", people=4)])
    raw.update(overrides)
    return BenchmarkProblem.model_validate(raw)


class FeatureTests(unittest.TestCase):
    def test_schema_and_hand_calculation(self):
        row = extract_features(example())
        self.assertEqual(tuple(row), FEATURE_NAMES)
        self.assertEqual(len(row), 41)
        self.assertEqual(set(row), set(FEATURE_SCHEMA))
        expected = dict(task_count=2, crew_count=1, effort_mean=1.5, effort_std=.5,
                        effort_q25=1.25, effort_median=1.5, effort_q75=1.75,
                        dag_depth=0, dag_level_width=2, customer_count=4,
                        requirements_mean=1, dependency_overlap=0, critical_group_fraction=.5,
                        report_effort_correlation=-1, report_customer_correlation=1)
        for key, value in expected.items():
            self.assertAlmostEqual(row[key], value, msg=key)
        self.assertTrue(all(type(value) is float and math.isfinite(value) for value in row.values()))

    def test_prerequisites_overlap_and_order_independence(self):
        raw = example().model_dump(mode="json")
        raw["tasks"][1]["prerequisites"] = ["syn-a"]
        raw["groups"][1]["required_tasks"] = ["syn-a", "syn-b"]
        row = extract_features(raw)
        self.assertEqual(row["dag_depth"], 1)
        self.assertEqual(row["dag_edge_density"], 1)
        self.assertEqual(row["ancestor_mean"], .5)
        self.assertEqual(row["bottleneck_fraction"], .5)
        self.assertEqual(row["dependency_overlap"], .5)
        raw["tasks"].reverse()
        raw["groups"].reverse()
        self.assertEqual(extract_features(raw), row)

    def test_metadata_and_identifier_leakage_invariance(self):
        original = example()
        raw = original.model_dump(mode="json")
        raw.update(id="syn-other", family="final-oracle-shortcut", seed=987654, split="evaluation")
        mapping = {name: "syn-renamed-" + str(i) for i, name in enumerate(
            ["syn-a", "syn-b", "syn-ga", "syn-gb", "syn-ca", "syn-cb", "syn-cc", "syn-cd",
             "syn-ba", "syn-bb", "syn-crew"])}
        def rename(value):
            if isinstance(value, dict):
                return {key: rename(item) for key, item in value.items()}
            if isinstance(value, list):
                return [rename(item) for item in value]
            return mapping.get(value, value) if isinstance(value, str) else value
        self.assertEqual(extract_features(original), extract_features(rename(raw)))

    def test_features_do_not_import_outcomes_and_reject_injection(self):
        tree = ast.parse(inspect.getsource(features))
        imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        self.assertFalse(any(name and any(part in name for part in ("policies", "metrics", "labels", "oracle"))
                             for name in imports))
        raw = example().model_dump(mode="json")
        for key in ("oracle_policy", "cost_ticks", "schedule", "label", "outcomes"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                extract_features({**raw, key: "shortcut"})

    def test_missing_effort_retains_indicator_and_abstains(self):
        raw = example().model_dump(mode="json")
        for task in raw["tasks"]:
            task["total_person_hours"] = None
        row = extract_features(raw)
        self.assertEqual(row["effort_mean"], 0)
        self.assertEqual(row["effort_missing_fraction"], 1)
        self.assertFalse(inference_supported(raw))
        self.assertIsNone(heuristic(raw))
        self.assertTrue(all(math.isfinite(value) for value in row.values()))

    def test_unchecked_invalid_model_copy_is_revalidated(self):
        p = example()
        invalid = p.model_copy(update={"tasks": (p.tasks[0], p.tasks[0])})
        with self.assertRaises(ValueError):
            extract_features(invalid)

    def test_heuristic_is_structural_and_predeclared(self):
        p = example()
        self.assertEqual(heuristic(p), POLICIES[2])
        raw = p.model_dump(mode="json")
        for group in raw["groups"]:
            group["required_tasks"] = ["syn-a", "syn-b"]
        self.assertEqual(heuristic(raw), POLICIES[1])


class LabelBaselineTests(unittest.TestCase):
    def test_exact_label_costs_and_ties(self):
        row = evaluate_problem(example())
        self.assertTrue(row["eligible"])
        self.assertIsNone(row["reason"])
        self.assertEqual(row["outcomes"][POLICIES[0]]["cost_ticks"], 11 * 3600)
        self.assertEqual(row["outcomes"][POLICIES[1]]["cost_ticks"], 6 * 3600)
        self.assertEqual(row["ties"], sorted(POLICIES[1:]))
        self.assertEqual(row["label"], POLICIES[1])
        self.assertTrue(all(type(outcome["cost_ticks"]) is int for outcome in row["outcomes"].values()))

    def test_unknown_release_never_acquires_numeric_target(self):
        raw = example().model_dump(mode="json")
        raw["groups"][0]["unresolved_dependency"] = True
        row = evaluate_problem(raw)
        self.assertFalse(row["eligible"])
        self.assertIsNone(row["label"])
        self.assertEqual(row["ties"], [])
        for outcome in row["outcomes"].values():
            self.assertIsNone(outcome["cost_ticks"])
            self.assertIsNone(outcome["metrics"]["modeled_customer_outage_hours"])
            self.assertEqual(outcome["metrics"]["unresolved_customers"], 1)

    def test_blocked_unrelated_task_still_excludes_training(self):
        raw = example().model_dump(mode="json")
        raw["tasks"].append(dict(id="syn-blocked", total_person_hours="5", report_order=2, access="blocked"))
        row = evaluate_problem(raw)
        self.assertFalse(row["eligible"])
        self.assertEqual(row["reason"], "incomplete_task_scope")
        self.assertIsNone(row["label"])
        self.assertTrue(all(outcome["cost_ticks"] is not None for outcome in row["outcomes"].values()))

    def test_known_later_censoring_not_unresolved_or_truncated(self):
        raw = example().model_dump(mode="json")
        raw["tasks"][0]["total_person_hours"] = "200"
        row = evaluate_problem(raw)
        self.assertTrue(row["eligible"])
        fifo = row["outcomes"][POLICIES[0]]
        self.assertEqual(fifo["metrics"]["unresolved_customers"], 0)
        self.assertEqual(fifo["metrics"]["censored_customers"], 4)
        self.assertEqual(fifo["cost_ticks"], 803 * 3600)
        self.assertEqual(fifo["metrics"]["restricted_horizon_customer_hours"], 672)

    def test_independent_validator_rejects_corrupt_metric(self):
        from benchmarks.metrics import calculate
        def corrupt(problem, plan):
            result = calculate(problem, plan)
            result["modeled_customer_outage_hours"] = 0
            return result
        with patch("research.ml_lab.labels.calculate", side_effect=corrupt), self.assertRaises(ValueError):
            evaluate_problem(example())

    def test_baselines_training_only_and_exact_target_validation(self):
        row = {**evaluate_problem(example()), "partition": "train"}
        self.assertEqual(fit_baselines([row]), {"fixed": POLICIES[1], "majority": POLICIES[1]})
        with self.assertRaises(ValueError):
            fit_baselines([row], partition="dev")
        with self.assertRaises(ValueError):
            fit_baselines([{**row, "partition": "final_id"}])
        with self.assertRaises(ValueError):
            fit_baselines([{**row, "label": POLICIES[0]}])
        with self.assertRaises(ValueError):
            fit_baselines([])

    def test_baselines_reject_missing_partition_even_on_ineligible_rows(self):
        row = evaluate_problem(example())
        with self.assertRaises(ValueError):
            fit_baselines([row])
        with self.assertRaises(ValueError):
            fit_baselines([{**row, "partition": "train"}, {**row, "eligible": False}])
        with self.assertRaises(ValueError):
            fit_baselines([{**row, "partition": None}])

    def test_fixed_and_majority_are_distinct_objectives(self):
        def labeled(costs):
            best = min(costs)
            ties = sorted(policy for policy, cost in zip(POLICIES, costs) if cost == best)
            return dict(partition="train", eligible=True, label=ties[0], ties=ties,
                        outcomes={policy: {"cost_ticks": cost} for policy, cost in zip(POLICIES, costs)})
        rows = [labeled([10, 11, 12, 13]), labeled([10, 11, 12, 13]), labeled([1000, 1, 1000, 1000])]
        self.assertEqual(fit_baselines(rows), {"fixed": POLICIES[1], "majority": POLICIES[0]})


if __name__ == "__main__":
    unittest.main()
