from fractions import Fraction
from pathlib import Path
import json
import tempfile
import unittest

from research.ml_lab.access import isolated
from research.ml_opportunity.evidence import ROOT, Sources, save_new
from research.ml_opportunity.statistics import ceiling, comparison, grouped, planning_budget, quantile


class EstimandTests(unittest.TestCase):
    def test_equal_group_weights_not_episode_weights(self):
        means = grouped([("a", 1), ("a", 3), ("b", 10)])
        self.assertEqual(means, {"a": 2, "b": 10})
        self.assertEqual(comparison(means, {"a": 3, "b": 11})["delta_ci95"], [1, 1])

    def test_two_ceiling_estimands_are_distinct(self):
        result = ceiling({"reactive": {"a": 10, "b": 100}, "model": {"a": 5, "b": 100}}, "reactive")
        self.assertEqual(result["mean_group_relative_improvement"], .25)
        self.assertAlmostEqual(result["ratio_of_means_improvement"], 5/110)
        self.assertEqual(result["winners"]["a"], "model")

    def test_support_and_nonfinite_fail_closed(self):
        for a, b in [({}, {}), ({"a": 1}, {"b": 2}), ({"a": float('nan')}, {"a": 1})]:
            with self.assertRaises(ValueError):
                comparison(a, b)
        with self.assertRaises(ValueError):
            ceiling({"a": {"g": 0}}, "a")
        with self.assertRaises(ValueError):
            quantile([], .5)

    def test_null_is_not_zero(self):
        self.assertEqual(grouped([("a", None), ("b", 4)]), {"b": 4})

    def test_power_sd_sensitivity(self):
        p = planning_budget({"a": 10, "b": 10}, {"a": 9, "b": 11})
        self.assertGreaterEqual(p["doubled_sd_groups"], 4*p["normal_approx_groups"]-4)

    def test_bootstrap_reproducible(self):
        self.assertEqual(comparison({"a": 2, "b": 3}, {"a": 1, "b": 4}),
                         comparison({"a": 2, "b": 3}, {"a": 1, "b": 4}))


class BoundaryTests(unittest.TestCase):
    def test_raw_and_external_denied(self):
        with isolated():
            for path in ("data/raw/Data1.zip", "data/external/no-such-file", "data/processed/customers.csv"):
                with self.assertRaises(PermissionError):
                    (ROOT/path).read_bytes()

    def test_source_allowlist(self):
        with self.assertRaises(ValueError):
            Sources().path("data/raw/Data1.zip")

    def test_output_refuses_existing_or_historical(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                save_new(d, {})
            with self.assertRaises(ValueError):
                save_new(ROOT/"docs/ml-lab/never-write-here", {})
            new = Path(d)/"new"
            save_new(new, {"a.json": {"fits": 0}})
            self.assertEqual(json.loads((new/"a.json").read_text()), {"fits": 0})


class ExactTests(unittest.TestCase):
    def test_corrupted_cost_rejected_against_schedule(self):
        from research.adaptive_dispatch.tests.fixtures import problem
        from research.adaptive_dispatch.environment import run_episode
        from research.adaptive_dispatch.policies import heuristic
        from research.ml_opportunity.audit import recomputed_metrics
        p = problem()
        row = run_episode(p, "deterministic", 0, lambda s:heuristic(s,"downstream"), "check")
        values = recomputed_metrics(p.model_dump(mode="json"), row)
        self.assertGreater(values['waiting'],0)
        row['metrics']['modeled_customer_outage_hours'] += 1
        with self.assertRaises(ValueError):
            recomputed_metrics(p.model_dump(mode="json"), row)

    def test_known_serial_expectation_and_independent_worlds(self):
        from research.adaptive_dispatch.tests.fixtures import problem
        from research.adaptive_dispatch.environment import Observation, public_problem
        from research.adaptive_dispatch.policies import heuristic
        from research.ml_opportunity.exact import expected, world_expectation
        p = problem(ticks=(3600, 7200), weights=(1, 1), crews=1)
        initial = Observation(public_problem(p, "high"), 0, (), ())
        optimal, _ = expected(initial)
        # Each support has mean 1; shortest-first total completion is 1+(1+2)=4 customer-hours.
        self.assertEqual(optimal, 4*3600)
        policy = lambda s:heuristic(s, "downstream")
        self.assertEqual(expected(initial, policy)[0], world_expectation(p, "high", policy)[0])

    def test_survival_conditions_next_event(self):
        from research.adaptive_dispatch.tests.fixtures import problem
        from research.adaptive_dispatch.environment import Observation, Active, WAIT, public_problem
        from research.ml_opportunity.exact import successors
        p = problem(ticks=(3600,), weights=(1,))
        state = Observation(public_problem(p, "high"), 1800, (), (Active("syn-t0", "syn-crew0", 0),))
        outcomes = successors(state, WAIT)
        self.assertEqual(len(outcomes), 1)
        self.assertEqual(outcomes[0][0], Fraction(1))
        self.assertEqual(outcomes[0][2].now, 8100)

    def test_budget_and_unsupported_fail(self):
        from research.adaptive_dispatch.tests.fixtures import problem
        from research.adaptive_dispatch.environment import Observation, public_problem
        from research.ml_opportunity.exact import expected
        state = Observation(public_problem(problem(), "low"), 0, (), ())
        with self.assertRaises(ValueError):
            expected(state, max_states=1)
        bad = Observation(public_problem(problem(unresolved=True), "low"), 0, (), ())
        with self.assertRaises(ValueError):
            expected(bad)


class ArchivedConsistencyTests(unittest.TestCase):
    def setUp(self):
        path = ROOT/"docs/research/ml-opportunity/evidence/audit.json"
        self.audit = json.loads(path.read_text())

    def test_replicated_headroom_not_global_bound(self):
        for cohort, value in (("final_id", .0185945), ("final_shift", .0130358)):
            record = self.audit[cohort]["restricted_ceiling"]
            self.assertAlmostEqual(record["ratio_of_means_improvement"], value, places=6)
            self.assertEqual(len(record["methods"]), 3)
            self.assertEqual(len(record["winners"]), 24)
            self.assertLessEqual(self.audit[cohort]["max_summary_wait_error"], 1e-10)

    def test_independently_counted_supervision(self):
        c = self.audit["signal"]["counts"]
        for key, n in {"discretionary_states":5352, "action_rows":24240, "wait_teacher_states":47,
                       "distinct_optimal_tie_states":1347, "zero_regret_rows":8801}.items():
            self.assertEqual(c[key], n)

    def test_static_original_units_and_negative_shift(self):
        r = self.audit["static"]
        self.assertEqual(r["final_id"]["eligible"], 90)
        self.assertEqual(r["final_shift"]["eligible"], 99)
        self.assertAlmostEqual(r["final_id"]["champion_regret_customer_hours"], 325.400, places=3)
        self.assertGreater(r["final_shift"]["champion_vs_fixed"]["delta_ci95"][0], 0)


if __name__ == "__main__":
    unittest.main()
