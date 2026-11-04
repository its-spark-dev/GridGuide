"""Fresh, bounded four-task diagnostic; exact expectation is not hindsight."""
from collections import defaultdict
from decimal import Decimal
from fractions import Fraction
from functools import lru_cache
from itertools import product
import random

from benchmarks.contracts import Assignment, BenchmarkProblem
from research.adaptive_dispatch.environment import Active, Environment, Observation, WAIT, public_problem
from research.adaptive_dispatch.policies import heuristic, lookahead
from .statistics import SEED, grouped, comparison


def problems():
    rng = random.Random(SEED)
    output = []
    for index in range(12):
        tasks = [dict(id=f"syn-op-t{i}", total_person_hours=str((Decimal(rng.randint(1, 6)*900)-Decimal('.1'))/3600),
                      prerequisites=[f"syn-op-t{j}" for j in range(i) if rng.random() < .3], report_order=i) for i in range(4)]
        groups = [dict(id=f"syn-op-g{i}", customer_ids=[f"syn-op-c{i}-{j}" for j in range(rng.randint(1, 9))],
                       required_tasks=sorted(rng.sample([t['id'] for t in tasks], rng.choice((1, 1, 2)))),
                       branch=f"syn-op-b{i%2}", critical_service=i == 0) for i in range(4)]
        for crews in (1, 2):
            p = BenchmarkProblem.model_validate(dict(id=f"syn-opportunity-{index:03d}-c{crews}",
                family="opportunity-four-task-exploratory", seed=SEED+index, split="micro",
                duration_assumption="one_effective_worker", tasks=tasks, groups=groups,
                crews=[dict(id=f"syn-op-crew{i}", people=4, available_tick=0) for i in range(crews)]))
            output.append((f"opportunity-{index:03d}", p))
    return output


def successors(state, action):
    """Conditional transitions use observed survival; unstarted work stays unknown."""
    if action not in state.actions(canonical_crew=True):
        raise ValueError("Illegal canonical action")
    if action != WAIT:
        active = tuple(sorted((*state.active, Active(action.task_id, action.crew_id, state.now)), key=lambda a:a.task_id))
        return [(Fraction(1), 0, Observation(state.static, state.now, state.completed, active))]
    supports = [state.static.support(a.task_id, state.now-a.start_tick) for a in state.active]
    worlds = list(product(*supports))
    arrival = [c.available_tick for c in state.static.crews if c.available_tick > state.now]
    mass = Fraction(1, len(worlds))
    combined = defaultdict(Fraction)
    for world in worlds:
        finishes = {a.task_id:a.start_tick+d for a, d in zip(state.active, world)}
        tick = min([*finishes.values(), *arrival])
        done = tuple(Assignment(task_id=a.task_id, crew_id=a.crew_id, start_tick=a.start_tick, end_tick=tick)
                     for a in state.active if finishes[a.task_id] == tick)
        nxt = Observation(state.static, tick,
            tuple(sorted((*state.completed, *done), key=lambda a:(a.end_tick, a.task_id))),
            tuple(a for a in state.active if finishes[a.task_id] != tick))
        combined[nxt] += mass
    completed = {a.task_id for a in state.completed}
    waiting = sum(len(g.customer_ids) for g in state.static.groups if not set(g.required_tasks) <= completed)
    return [(prob, waiting*(nxt.now-state.now), nxt) for nxt, prob in combined.items()]


def expected(initial, policy=None, max_states=100000):
    """Exact customer-seconds, minimizing before sampling next public event."""
    if len(initial.static.tasks) > 4 or any(g.unresolved_dependency for g in initial.static.groups):
        raise ValueError("Diagnostic limited to resolved <=4-task problems")
    if set(t.id for t in initial.static.tasks) != initial.static.executable:
        raise ValueError("Diagnostic requires executable tasks")
    count = 0

    @lru_cache(None)
    def value(state):
        nonlocal count
        count += 1
        if count > max_states:
            raise ValueError("Diagnostic state budget exceeded")
        if state.terminal:
            return Fraction(0)
        actions = state.actions(canonical_crew=True) if policy is None else (policy(state),)
        return min(sum(prob*(cost+value(nxt)) for prob, cost, nxt in successors(state, a)) for a in actions)
    result = value(initial)
    return result, count


def world_expectation(problem, profile, policy):
    """Independent check through actual event environment for every duration vector."""
    static = public_problem(problem, profile)
    ids = sorted(static.executable)
    total, count = Fraction(0), 0
    for world in product(*(static.support(i) for i in ids)):
        env = Environment(problem, profile, dict(zip(ids, world)))
        while not (state := env.observe()).terminal:
            env.step(policy(state))
        ends = {a.task_id:a.end_tick for a in env.completed}
        total += sum(len(g.customer_ids)*max([0]+[ends[t] for t in g.required_tasks]) for g in static.groups)
        count += 1
    return total/count, count


def run(sources):
    from research.adaptive_dispatch.exact import solve
    callbacks = {"fifo": lambda s:heuristic(s, "fifo"), "downstream":lambda s:heuristic(s,"downstream"),
                 "median":lambda s:lookahead(s, median=True)}
    prior = set()
    for directory in ("docs/ml-lab/evidence/dataset", "docs/learned-dispatch/evidence/dataset"):
        for part in ("train", "dev", "final_id", "final_shift"):
            for row in sources.rows(directory+f"/{part}.jsonl.gz"):
                prior.add(row["problem"]["id"])
                if len(row["problem"]["tasks"]) <= 4:
                    raise ValueError("Historical graph size overlaps tiny diagnostic")
    for row in sources.rows("docs/adaptive-dispatch/evidence/dataset/cases.jsonl.gz"):
        if len(row["problem"]["tasks"]) <= 4:
            raise ValueError("Historical adaptive graph size overlaps tiny diagnostic")
    results, inputs = [], []
    for group, p in problems():
        if p.id in prior:
            raise ValueError("Historical identity collision")
        inputs.append(dict(group=group, fingerprint=p.fingerprint, problem=p.model_dump(mode="json")))
        for profile in ("low", "high"):
            initial = Observation(public_problem(p, profile), 0, (), ())
            optimal, states = expected(initial)
            cross = solve(initial)
            if optimal/3600 != cross["expected_remaining_customer_hours"]:
                raise ValueError("Independent exact optimum mismatch")
            customers = sum(len(g.customer_ids) for g in p.groups)
            costs = {"optimal":float(optimal/3600/customers)}
            policy_states = {}
            for name, policy in callbacks.items():
                val, visited = expected(initial, policy)
                enumeration, worlds = world_expectation(p, profile, policy)
                if val != enumeration or val < optimal:
                    raise ValueError("Exact expectation/world rollout mismatch")
                costs[name] = float(val/3600/customers)
                policy_states[name] = visited
            results.append(dict(group=group, case=p.id, profile=profile, crews=len(p.crews),
                mean_wait_hours=costs, optimal_customer_seconds=str(optimal), bellman_states=states,
                independent_solver_states=cross["states"], policy_states=policy_states, duration_worlds=worlds,
                exact_checks_pass=True))
    by_method = {m:grouped((r["group"],r["mean_wait_hours"][m]) for r in results) for m in ("optimal", *callbacks)}
    return dict(inputs=inputs, results=results, group_means=by_method,
                comparisons={m:comparison(by_method[m],by_method["optimal"]) for m in callbacks},
                scope="12 fresh configurations, 24 crew variants, 48 stochastic expectations; no fitted model or holdout",
                limits="Four tasks cannot bound 10–24-task opportunity; exact optimum knows supports, never sampled futures")
