"""Online rules and bounded non-clairvoyant rollout search."""
from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
import hashlib

from benchmarks.contracts import Assignment, canonical
from benchmarks.policies import schedule as g2_schedule

from . import VERSION
from .environment import (Action, Environment, Observation, PublicProblem, WAIT,
                          checked_result, keyed_choice, sample_durations)

HEURISTICS = ("fifo", "customer", "release", "critical", "downstream")


@lru_cache(maxsize=256)
def ancestry(static: PublicProblem) -> dict[str, frozenset[str]]:
    ancestors = {t.id: set(t.prerequisites) for t in static.tasks}
    for _ in static.tasks:
        expanded = {t: v | {a for p in v for a in ancestors[p]} for t, v in ancestors.items()}
        if expanded == ancestors:
            break
        ancestors = expanded
    return {t: frozenset(v | {t}) for t, v in ancestors.items()}


def heuristic(state: Observation, name: str) -> Action:
    if name not in HEURISTICS:
        raise ValueError("Unknown reactive policy")
    ready, crews = state.ready_tasks, state.available_crews
    if not ready or not crews:
        if not state.can_wait:
            raise ValueError("No valid online decision")
        return WAIT
    tasks = {t.id: t for t in state.static.tasks}
    done = {a.task_id for a in state.completed}
    ancestors = ancestry(state.static)
    critical = {i for g in state.static.groups if g.critical_service
                for t in g.required_tasks for i in ancestors[t]}
    def rank(i):
        task = tasks[i]
        if name == "fifo":
            return task.report_order, i
        if name == "customer":
            return -sum(len(g.customer_ids) for g in state.static.groups if i in g.required_tasks), i
        marginal = sum(len(g.customer_ids) for g in state.static.groups if not g.unresolved_dependency
                       and i in g.required_tasks and set(g.required_tasks) <= done | {i})
        if name == "downstream":
            benefit = sum(len(g.customer_ids) for g in state.static.groups if not g.unresolved_dependency
                          and not set(g.required_tasks) <= done
                          and any(i in ancestors[t] for t in g.required_tasks))
            expected = Fraction(sum(state.static.support(i)), len(state.static.support(i)))
            return -Fraction(benefit) / expected, -marginal, i
        return (-int(name == "critical" and i in critical),
                -Fraction(marginal) / Fraction(task.total_person_hours), -marginal, task.total_person_hours, i)
    return Action(min(ready, key=rank), crews[0])


def cost(state: Observation) -> float:
    ends = {a.task_id: a.end_tick for a in state.completed}
    partial = any(g.unresolved_dependency or not set(g.required_tasks) <= ends.keys() for g in state.static.groups)
    total = 0
    for g in state.static.groups:
        value = None if g.unresolved_dependency or not set(g.required_tasks) <= ends.keys() else max([0] + [ends[t] for t in g.required_tasks])
        total += len(g.customer_ids) * (state.static.horizon_ticks if value is None else min(value, state.static.horizon_ticks) if partial else value)
    return total / 3600


def hypothetical_draws(state: Observation, draw: int, median: bool = False) -> dict[str, int]:
    done = {a.task_id: a.end_tick-a.start_tick for a in state.completed}
    active = {a.task_id: state.now-a.start_tick for a in state.active}
    key = hashlib.sha256(canonical([VERSION, "teacher-only", state.now,
        [a.model_dump(mode="json") for a in state.completed], [vars(a) for a in state.active],
        state.static.nominal_ticks, state.static.profile])).hexdigest()
    values = dict(done)
    for task in state.static.executable - done.keys():
        support = state.static.support(task, active.get(task, -1))
        values[task] = (sorted(support)[len(support)//2] if median else
                        keyed_choice(support, [key, draw, task]))
    return values


def action_values(state: Observation, samples: int = 8, median: bool = False) -> tuple[tuple[Action, float], ...]:
    if type(samples) is not int or not 1 <= samples <= 32:
        raise ValueError("Search sample budget outside [1,32]")
    actions = state.actions(canonical_crew=True)
    futures = [hypothetical_draws(state, k, median) for k in range(1 if median else samples)]
    scored = []
    for action in actions:
        averages = []
        for continuation in HEURISTICS[:4]:
            outcomes = []
            for durations in futures:
                env = Environment.hypothetical(state, durations)
                env.step(action)
                while not (view := env.observe()).terminal:
                    env.step(heuristic(view, continuation))
                outcomes.append(cost(env.observe()))
            averages.append(sum(outcomes) / len(outcomes))
        scored.append((action, min(averages)))
    return tuple(scored)


def lookahead(state: Observation, samples: int = 8, median: bool = False) -> Action:
    actions = state.actions(canonical_crew=True)
    if len(actions) == 1:
        return actions[0]
    # Explicit stable key avoids comparing None to string for wait ties.
    return min(action_values(state, samples, median),
               key=lambda row: (row[1], row[0] == WAIT, row[0].task_id or "", row[0].crew_id or ""))[0]


def fixed_episode(problem, profile: str, seed: int, policy: str, planned_floors: bool = True) -> dict:
    """Same exogenous duration map; fixed crew assignment/order with optional G5 floors."""
    import time
    begun = time.perf_counter_ns()
    plan = g2_schedule(problem, policy)
    planning_ns = time.perf_counter_ns() - begun
    durations = sample_durations(problem, profile, seed)
    dependencies = {a.task_id: set(next(t.prerequisites for t in problem.tasks if t.id == a.task_id)) for a in plan.assignments}
    for crew in problem.crews:
        ordered = sorted((a for a in plan.assignments if a.crew_id == crew.id), key=lambda a: (a.start_tick, a.task_id))
        for before, after in zip(ordered, ordered[1:]):
            dependencies[after.task_id].add(before.task_id)
    assignments, ends = [], {}
    while len(ends) < len(plan.assignments):
        ready = [a for a in plan.assignments if a.task_id not in ends and dependencies[a.task_id] <= ends.keys()]
        if not ready:
            raise ValueError("Fixed crew/precedence graph is cyclic")
        for a in ready:
            crew = next(c for c in problem.crews if c.id == a.crew_id)
            start = max([crew.available_tick, a.start_tick if planned_floors else 0] + [ends[p] for p in dependencies[a.task_id]])
            ends[a.task_id] = start + durations[a.task_id]
            assignments.append(Assignment(task_id=a.task_id, crew_id=a.crew_id, start_tick=start, end_tick=ends[a.task_id]))
    result = checked_result(problem, durations, tuple(assignments), f"fixed-{'floor' if planned_floors else 'order'}:{policy}")
    result.update(profile=profile, episode_seed=seed, durations=durations, planning_nanoseconds=planning_ns)
    return result
