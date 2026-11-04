"""Tiny finite-support, non-clairvoyant Bellman verification; never a training teacher."""
from collections import defaultdict
from fractions import Fraction
from functools import lru_cache
from itertools import product
import math

from benchmarks.contracts import Assignment
from .environment import Action, Active, Observation, WAIT


def solve(initial: Observation, max_states: int = 100000) -> dict:
    if len(initial.static.tasks) > 5:
        raise ValueError("Exact verification is restricted to <=5 tasks")
    if any(g.unresolved_dependency or not set(g.required_tasks) <= initial.static.executable
           for g in initial.static.groups):
        raise ValueError("Exact completed-cost verification requires resolved customer scope")
    states = 0
    factors = {"deterministic": (Fraction(1),), "low": (Fraction(1, 2), Fraction(3, 2)),
               "high": (Fraction(1, 4), Fraction(1, 2), Fraction(9, 4))}[initial.static.profile]
    nominal = dict(initial.static.nominal_ticks)

    def actions(state):
        done = {a.task_id for a in state.completed}
        started = done | {a.task_id for a in state.active}
        busy = {a.crew_id for a in state.active}
        idle = sorted(c.id for c in state.static.crews if c.id not in busy and c.available_tick <= state.now)
        ready = sorted(t.id for t in state.static.tasks if t.id in state.static.executable
                       and t.id not in started and set(t.prerequisites) <= done)
        available = [Action(t, idle[0]) for t in ready] if idle else []
        if state.active or any(c.available_tick > state.now for c in state.static.crews):
            available.append(WAIT)
        return available

    def after_wait(state):
        # Enumerate conditional active outcomes only. Unstarted future draws remain unknown.
        supports = [tuple(math.ceil(nominal[a.task_id] * f) for f in factors
                    if math.ceil(nominal[a.task_id] * f) > state.now-a.start_tick) for a in state.active]
        if any(not s for s in supports):
            raise ValueError("Impossible active observation")
        mass = Fraction(1, math.prod(len(s) for s in supports))
        arrivals = [c.available_tick for c in state.static.crews if c.available_tick > state.now]
        successors = defaultdict(Fraction)
        for durations in product(*supports):
            ends = {a.task_id: a.start_tick+d for a, d in zip(state.active, durations)}
            tick = min(list(ends.values()) + arrivals)
            finished = [Assignment(task_id=a.task_id, crew_id=a.crew_id, start_tick=a.start_tick, end_tick=tick)
                        for a in state.active if ends[a.task_id] == tick]
            view = Observation(state.static, tick,
                tuple(sorted((*state.completed, *finished), key=lambda a: (a.end_tick, a.task_id))),
                tuple(a for a in state.active if ends[a.task_id] != tick))
            successors[view] += mass
        return successors

    def q(state, action):
        if action != WAIT:
            view = Observation(state.static, state.now, state.completed,
                tuple(sorted((*state.active, Active(action.task_id, action.crew_id, state.now)), key=lambda a: a.task_id)))
            return value(view)
        done = {a.task_id for a in state.completed}
        waiting = sum(len(g.customer_ids) for g in state.static.groups if not set(g.required_tasks) <= done)
        return sum(probability * (Fraction(waiting * (view.now-state.now), 3600) + value(view))
                   for view, probability in after_wait(state).items())

    @lru_cache(maxsize=None)
    def value(state):
        nonlocal states
        states += 1
        if states > max_states:
            raise ValueError("Exact verification state budget exceeded")
        if not state.active and {a.task_id for a in state.completed} == state.static.executable:
            return Fraction(0)
        return min(q(state, action) for action in actions(state))

    optimum = value(initial)
    root_values = tuple((a, q(initial, a)) for a in actions(initial)) if not initial.terminal else ()
    return {"expected_remaining_customer_hours": optimum, "action_values": root_values,
            "states": states, "interpretation": "non-clairvoyant finite-support optimum"}
