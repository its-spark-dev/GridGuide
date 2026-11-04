import copy
from dataclasses import FrozenInstanceError, fields
from fractions import Fraction
import unittest

from benchmarks.contracts import Assignment, duration_ticks
from benchmarks.metrics import calculate
from benchmarks.policies import POLICIES, schedule
from research.adaptive_dispatch.environment import (Action, Active, Environment, Observation, WAIT, PROFILES,
    conditional_problem, public_problem, run_episode, sample_durations)
from research.adaptive_dispatch.exact import solve
from research.adaptive_dispatch.policies import (HEURISTICS, action_values, cost, fixed_episode,
    heuristic, hypothetical_draws, lookahead)
from research.adaptive_dispatch.validation import validate_trajectory
from research.adaptive_dispatch.tests.fixtures import problem


class EnvironmentTests(unittest.TestCase):
    def test_distributions_have_exact_mean_one(self):
        for factors in PROFILES.values():
            self.assertEqual(sum(factors) / len(factors), 1)

    def test_prerequisite_and_capacity(self):
        p = problem(prerequisites={1: (0,)}, crews=2)
        env = Environment(p, "deterministic", sample_durations(p, "deterministic", 0))
        with self.assertRaises(ValueError):
            env.step(Action("syn-t1", "syn-crew0"))
        env.step(Action("syn-t0", "syn-crew0"))
        with self.assertRaises(ValueError):
            env.step(Action("syn-t0", "syn-crew1"))
        view = env.step(WAIT)
        self.assertEqual(view.now, 3600)
        self.assertEqual(view.ready_tasks, ("syn-t1",))

    def test_wait_crew_arrival_and_terminal(self):
        p = problem(ticks=(3600,), weights=(1,), arrivals={0: 100})
        env = Environment(p, "low", {"syn-t0": 1800})
        self.assertEqual(env.observe().actions(), (WAIT,))
        env.step(WAIT)
        self.assertEqual(env.now, 100)
        env.step(Action("syn-t0", "syn-crew0"))
        env.step(WAIT)
        self.assertEqual(env.now, 1900)
        with self.assertRaises(ValueError):
            env.step(WAIT)

    def test_simultaneous_completions(self):
        p = problem(ticks=(3600, 3600), crews=2)
        env = Environment(p, "deterministic", sample_durations(p, "deterministic", 0))
        for i in range(2):
            env.step(Action(f"syn-t{i}", f"syn-crew{i}"))
        view = env.step(WAIT)
        self.assertTrue(view.terminal)
        self.assertEqual(len(view.completed), 2)

    def test_strict_actions(self):
        p = problem()
        env = Environment(p, "deterministic", sample_durations(p, "deterministic", 0))
        for action in (WAIT, {"task_id": "syn-t0", "crew_id": "syn-crew0"}, Action("syn-t0", "syn-missing")):
            with self.assertRaises(ValueError):
                env.step(action)
        with self.assertRaises(ValueError):
            Action("syn-t0")
        with self.assertRaises(ValueError):
            Action(1, "syn-crew0")

    def test_duration_support_and_private_copy(self):
        p = problem()
        durations = sample_durations(p, "high", 8)
        env = Environment(p, "high", durations)
        durations.clear()
        env.step(Action("syn-t0", "syn-crew0"))
        env.step(WAIT)
        for invalid in ({}, {"syn-t0": 1, "syn-t1": 2}, {"syn-t0": True, "syn-t1": 7200}):
            with self.assertRaises(ValueError):
                Environment(p, "high", invalid)

    def test_public_state_has_no_future(self):
        self.assertEqual({f.name for f in fields(Active)}, {"task_id", "crew_id", "start_tick"})
        self.assertEqual({f.name for f in fields(Observation)}, {"static", "now", "completed", "active"})
        p = problem(crews=2)
        a = Environment(p, "low", {"syn-t0": 1800, "syn-t1": 3600})
        b = Environment(p, "low", {"syn-t0": 5400, "syn-t1": 10800})
        for env in (a, b):
            env.step(Action("syn-t0", "syn-crew0"))
        self.assertEqual(a.observe(), b.observe())
        self.assertEqual(action_values(a.observe(), samples=2), action_values(b.observe(), samples=2))
        for name in HEURISTICS:
            self.assertEqual(heuristic(a.observe(), name), heuristic(b.observe(), name))
        with self.assertRaises(FrozenInstanceError):
            a.observe().now = 5

    def test_conditioning_and_observed_history(self):
        p = problem(crews=2, arrivals={1: 2000})
        env = Environment(p, "low", {"syn-t0": 5400, "syn-t1": 3600})
        env.step(Action("syn-t0", "syn-crew0"))
        view = env.step(WAIT)
        self.assertEqual(view.now, 2000)
        self.assertEqual(view.static.support("syn-t0", 2000), (5400,))
        for draw in range(10):
            self.assertEqual(hypothetical_draws(view, draw)["syn-t0"], 5400)
        with self.assertRaises(ValueError):
            Environment.hypothetical(view, {"syn-t0": 1800, "syn-t1": 3600})

    def test_support_mass_and_stream_pairing(self):
        p = problem(ticks=(1,), weights=(1,))
        self.assertEqual(public_problem(p, "high").support("syn-t0"), (1, 1, 3))
        p = problem()
        for seed in range(5):
            expected = sample_durations(p, "high", seed)
            for name in HEURISTICS:
                row = run_episode(p, "high", seed, lambda s: heuristic(s, name), name)
                self.assertEqual(row["durations"], expected)
            for name in POLICIES:
                self.assertEqual(fixed_episode(p, "high", seed, name)["durations"], expected)
        with self.assertRaises(ValueError):
            sample_durations(p, "low", True)

    def test_blocked_descendants_and_null_customer_scope(self):
        p = problem(blocked=(0,), prerequisites={1: (0,)})
        row = run_episode(p, "low", 1, lambda s: heuristic(s, "fifo"), "fifo", trace=True)
        self.assertEqual(row["schedule"]["assignments"], [])
        self.assertIsNone(row["metrics"]["modeled_customer_outage_hours"])
        self.assertEqual(row["metrics"]["restricted_horizon_customer_hours"], 3*168)
        self.assertEqual(row["metrics"]["unresolved_customers"], 3)

    def test_missing_effort_and_unresolved_group(self):
        p = problem(unresolved=True)
        p = type(p).model_validate({**p.model_dump(), "tasks": [
            {**p.tasks[0].model_dump(), "total_person_hours": None}, p.tasks[1].model_dump()]})
        row = run_episode(p, "high", 0, lambda s: heuristic(s, "release"), "release")
        self.assertEqual(row["metrics"]["unresolved_customers"], 1)
        self.assertIsNone(row["metrics"]["modeled_customer_outage_hours"])

    def test_people_and_crews_are_separate(self):
        serial = problem(people=8, crews=2)
        ideal = problem(people=8, crews=2, assumption="ideal_all_people")
        self.assertEqual(duration_ticks(serial, serial.tasks[0]), 3600)
        self.assertEqual(duration_ticks(ideal, ideal.tasks[0]), 450)
        for p in (serial, ideal):
            durations = sample_durations(p, "high", 1)
            conditional = conditional_problem(p, durations)
            self.assertEqual({t.id: duration_ticks(conditional, t) for t in conditional.tasks}, durations)

    def test_fixed_deterministic_equivalence(self):
        p = problem(ticks=(3600, 7200, 9000), weights=(2, 7, 1), prerequisites={2: (0,)}, crews=2)
        for name in POLICIES:
            planned = schedule(p, name)
            for floors in (False, True):
                row = fixed_episode(p, "deterministic", 0, name, planned_floors=floors)
                self.assertEqual(row["metrics"], calculate(p, planned))
                self.assertEqual(sorted(row["schedule"]["assignments"], key=lambda a: a["task_id"]),
                                 sorted(planned.model_dump(mode="json")["assignments"], key=lambda a: a["task_id"]))

    def test_trajectory_validator_rejects_corruption(self):
        p = problem(crews=2)
        row = run_episode(p, "low", 0, lambda s: heuristic(s, "fifo"), "fifo", trace=True)
        def check(trace):
            return validate_trajectory(p, "low", row["durations"], trace, row["schedule"])
        self.assertEqual(check(row["trace"]), [])
        damaged = copy.deepcopy(row["trace"])
        damaged[0]["now"] = 1
        self.assertEqual(check(damaged), ["observed_history"])
        damaged = copy.deepcopy(row["trace"])
        damaged[1]["active"][0]["end_tick"] = 1800
        self.assertEqual(check(damaged), ["active_public_state"])
        damaged = copy.deepcopy(row["trace"])
        damaged[1]["action"]["crew_id"] = "syn-crew0"
        self.assertEqual(check(damaged), ["crew_capacity"])
        self.assertEqual(check(row["trace"][:-1]), ["incomplete_trajectory"])

    def test_release_union_and_exact_metric_validation(self):
        p = problem(crews=2)
        p = type(p).model_validate({**p.model_dump(), "groups": [
            {**p.groups[0].model_dump(), "required_tasks": ["syn-t0", "syn-t1"]}, p.groups[1].model_dump()]})
        row = run_episode(p, "deterministic", 0, lambda s: heuristic(s, "customer"), "customer")
        self.assertEqual(row["metrics"]["modeled_customer_outage_hours"], 6)
        self.assertEqual(row["metrics"]["milestones"], [dict(tick=7200, additional_customers=3, cumulative_customers=3)])


class ExactTests(unittest.TestCase):
    def test_expected_smith_order_without_future_access(self):
        p = problem(ticks=(3600, 7200), weights=(1, 4))
        for profile in ("deterministic", "low", "high"):
            state = Environment(p, profile, sample_durations(p, profile, 0)).observe()
            result = solve(state)
            self.assertEqual(result["expected_remaining_customer_hours"], 11)
            values = dict(result["action_values"])
            self.assertEqual(values[Action("syn-t0", "syn-crew0")], 13)
            self.assertEqual(values[Action("syn-t1", "syn-crew0")], 11)

    def test_expected_parallel_maximum_and_arrivals(self):
        p = problem(ticks=(3600, 3600), weights=(1, 1), crews=2)
        p = type(p).model_validate({**p.model_dump(), "groups": [
            {**p.groups[0].model_dump(), "required_tasks": ["syn-t0", "syn-t1"]}]})
        state = Environment(p, "low", sample_durations(p, "low", 0)).observe()
        self.assertEqual(solve(state)["expected_remaining_customer_hours"], Fraction(5, 4))
        p = problem(ticks=(3600,), weights=(2,), arrivals={0: 3600})
        state = Environment(p, "low", sample_durations(p, "low", 0)).observe()
        self.assertEqual(solve(state)["expected_remaining_customer_hours"], 4)

    def test_search_matches_deterministic_exact_tiny(self):
        p = problem(ticks=(3600, 7200, 10800), weights=(1, 5, 3))
        state = Environment(p, "deterministic", sample_durations(p, "deterministic", 0)).observe()
        optimum = solve(state)
        self.assertEqual(dict(optimum["action_values"])[lookahead(state, samples=2)],
                         optimum["expected_remaining_customer_hours"])
        row = run_episode(p, "deterministic", 0, lambda s: lookahead(s, samples=2), "search")
        self.assertEqual(row["metrics"]["modeled_customer_outage_hours"], float(optimum["expected_remaining_customer_hours"]))

    def test_exact_and_search_budgets(self):
        p = problem()
        state = Environment(p, "low", sample_durations(p, "low", 0)).observe()
        with self.assertRaises(ValueError):
            solve(state, max_states=1)
        with self.assertRaises(ValueError):
            action_values(state, samples=33)
        p = problem(unresolved=True)
        with self.assertRaises(ValueError):
            solve(Environment(p, "low", sample_durations(p, "low", 0)).observe())

    def test_deliberate_wait_can_be_optimal(self):
        # Reserve the idle crew for two important descendants of the active task.
        p = problem(ticks=(3600, 36000, 3600, 3600), weights=(1, 1, 100, 100),
                    prerequisites={2: (0,), 3: (0,)}, crews=2)
        env = Environment(p, "deterministic", sample_durations(p, "deterministic", 0))
        state = env.step(Action("syn-t0", "syn-crew0"))
        result = solve(state)
        self.assertEqual(result["expected_remaining_customer_hours"], 413)
        self.assertEqual(dict(result["action_values"])[WAIT], 413)
        self.assertEqual(dict(result["action_values"])[Action("syn-t1", "syn-crew1")], 511)
        self.assertEqual(lookahead(state), WAIT)

    def test_observed_completion_changes_ready_decision(self):
        p = problem(ticks=(3600, 3600, 3600, 3600), weights=(1, 1, 10, 10),
                    prerequisites={2: (0,), 3: (1,)}, crews=2)
        first = {"syn-t0": 1800, "syn-t1": 5400, "syn-t2": 1800, "syn-t3": 1800}
        second = {**first, "syn-t0": 5400, "syn-t1": 1800}
        decisions = []
        for durations in (first, second):
            env = Environment(p, "low", durations)
            env.step(Action("syn-t0", "syn-crew0"))
            env.step(Action("syn-t1", "syn-crew1"))
            observed = env.step(WAIT)
            self.assertEqual(observed.now, 1800)
            decisions.append(heuristic(observed, "customer").task_id)
        self.assertEqual(decisions, ["syn-t2", "syn-t3"])


if __name__ == "__main__":
    unittest.main()
