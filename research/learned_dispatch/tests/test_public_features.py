import copy
from dataclasses import replace
import unittest

import numpy as np

from benchmarks.contracts import Assignment
from research.adaptive_dispatch.environment import Action, Active, Environment, WAIT, sample_durations
from research.adaptive_dispatch.policies import action_values, cost, hypothetical_draws, heuristic
from research.adaptive_dispatch.tests.fixtures import problem
from research.learned_dispatch.features import FEATURE_NAMES, extract, feature_rows, schema
from research.learned_dispatch.public import from_public_dict, public_dict, validate_state
from research.learned_dispatch.teacher import label


def state(p=None, profile="deterministic"):
    p = p or problem()
    return Environment(p, profile, sample_durations(p, profile, 0)).observe()


class PublicFeatureTests(unittest.TestCase):
    def test_roundtrip_and_no_private_metadata(self):
        p = problem(crews=2)
        env = Environment(p, "high", sample_durations(p, "high", 8))
        while not env.observe().terminal:
            s = env.observe()
            self.assertEqual(from_public_dict(public_dict(s)), s)
            self.assertEqual(validate_state(s).actions, s.actions())
            feature_rows(s)
            env.step(heuristic(s, "downstream"))
        self.assertEqual(validate_state(env.observe()).actions, ())
        self.assertEqual(set(public_dict(state())["static"]),
            {"tasks", "groups", "crews", "nominal_ticks", "executable", "profile", "horizon_ticks"})
        for injected in ("seed", "case_id", "actual_remaining_duration", "future_event_queue"):
            payload = public_dict(state())
            payload[injected] = 1
            with self.assertRaises(ValueError):
                from_public_dict(payload)

    def test_hand_computed_features_and_aliases(self):
        s = state(problem(crews=2))
        f = extract(s, Action("syn-t0", "syn-crew0"))
        self.assertEqual(len(f), 46)
        self.assertEqual(tuple(f), FEATURE_NAMES)
        self.assertEqual(len(schema()["features"]), 46)
        self.assertEqual(f["task_count"], 2)
        self.assertEqual(f["ready_fraction"], 1)
        self.assertEqual(f["unreleased_customer_fraction"], 1)
        self.assertAlmostEqual(f["action_nominal_scaled"], 2/3)
        self.assertAlmostEqual(f["direct_customer_fraction"], 1/3)
        self.assertAlmostEqual(f["critical_downstream_fraction"], 1/3)
        self.assertAlmostEqual(f["marginal_per_duration"], .5)
        self.assertEqual(f, extract(s, Action("syn-t0", "syn-crew1")))
        with self.assertRaises(ValueError):
            extract(s, WAIT)

    def test_future_intervention_and_conditional_residual(self):
        p = problem(crews=2, arrivals={1: 2000})
        a = Environment(p, "low", {"syn-t0": 5400, "syn-t1": 3600})
        b = Environment(p, "low", {"syn-t0": 5400, "syn-t1": 10800})
        for env in (a, b):
            env.step(Action("syn-t0", "syn-crew0"))
            env.step(WAIT)
        np.testing.assert_array_equal(feature_rows(a.observe())[1], feature_rows(b.observe())[1])
        self.assertEqual(label(a.observe()), label(b.observe()))
        f = extract(a.observe(), WAIT)
        self.assertAlmostEqual(f["active_remaining_mean_scaled"], 3400/5400)
        self.assertAlmostEqual(f["active_elapsed_scaled"], 2000/5400)
        self.assertEqual(f["action_wait"], 1)
        self.assertEqual(f["action_nominal_scaled"], 0)
        self.assertEqual(f["wait_active_release_fraction"], 1/3)

    def test_identity_renaming_does_not_change_features(self):
        p = problem(ticks=(3600, 7200, 9000), weights=(3, 2, 1), prerequisites={2: (0,)}, crews=2)
        s = state(p)
        payload = public_dict(s)
        # Rename all identity strings, retaining the semantic structure.
        def rename(value):
            if isinstance(value, str) and value.startswith("syn-"):
                return value.replace("syn-", "syn-renamed-")
            if isinstance(value, dict):
                return {k: rename(v) for k, v in value.items()}
            if isinstance(value, (list, tuple)):
                return [rename(v) for v in value]
            return value
        renamed = from_public_dict(rename(payload))
        np.testing.assert_array_equal(feature_rows(s)[1], feature_rows(renamed)[1])

    def test_malformed_and_impossible_histories(self):
        s = state(problem(crews=2, prerequisites={1: (0,)}))
        invalid = [replace(s, now=True), replace(s, active=(Active("syn-t1", "syn-crew0", 0),)),
            replace(s, active=(Active("syn-t0", "syn-crew0", 0), Active("syn-t0", "syn-crew1", 0))),
            replace(s, now=3600, active=(Active("syn-t0", "syn-crew0", 0),)),
            replace(s, now=3000, completed=(Assignment(task_id="syn-t0", crew_id="syn-crew0", start_tick=0, end_tick=3000),))]
        for bad in invalid:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_state(bad)
        forged = replace(s, static=replace(s.static, tasks=(s.static.tasks[0].model_copy(update={"report_order": -1}), *s.static.tasks[1:])))
        with self.assertRaises(ValueError):
            validate_state(forged)
        s = state(problem(crews=2))
        with self.assertRaises(ValueError):
            validate_state(replace(s, active=(Active("syn-t0", "syn-crew0", 0), Active("syn-t1", "syn-crew0", 0))))

    def test_unsupported_complete_scope_and_wait_mask(self):
        for p in (problem(blocked=(0,)), problem(unresolved=True)):
            s = state(p)
            self.assertFalse(validate_state(s).supported)
            with self.assertRaises(ValueError):
                feature_rows(s)
        p = problem(ticks=(3600,), weights=(1,), arrivals={0: 100})
        s = state(p)
        self.assertEqual(feature_rows(s)[0], (WAIT,))
        self.assertIsNone(label(s)["targets"])

    def test_real_teacher_costs_and_crew_equivalence(self):
        s = state(problem(ticks=(3600, 7200), weights=(1, 4)))
        teaching = label(s)
        self.assertEqual(teaching["costs"], [13., 11.])
        self.assertEqual(teaching["teacher"], vars(Action("syn-t1", "syn-crew0")))
        np.testing.assert_allclose(teaching["targets"], [2/7.5, 0])
        s = state(problem(crews=2))
        q = dict(action_values(s, median=True))
        futures = hypothetical_draws(s, 0, median=True)
        # Compute both idle-crew choices rather than assuming copied costs are correct.
        for action in s.actions():
            costs = []
            for continuation in ("fifo", "customer", "release", "critical"):
                env = Environment.hypothetical(s, futures)
                env.step(action)
                while not env.observe().terminal:
                    env.step(heuristic(env.observe(), continuation))
                costs.append(cost(env.observe()))
            self.assertEqual(min(costs), q[Action(action.task_id, "syn-crew0")])

    def test_teacher_can_label_wait_as_best(self):
        p = problem(ticks=(3600, 36000, 3600, 3600), weights=(1, 1, 100, 100),
                    prerequisites={2: (0,), 3: (0,)}, crews=2)
        env = Environment(p, "deterministic", sample_durations(p, "deterministic", 0))
        s = env.step(Action("syn-t0", "syn-crew0"))
        self.assertEqual(label(s)["teacher"], vars(WAIT))


if __name__ == "__main__":
    unittest.main()
