"""Strict public-observation validation and reusable structural context; no private future."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from types import MappingProxyType
from typing import Mapping

from benchmarks.contracts import (Assignment, BenchmarkCrew, BenchmarkProblem, BenchmarkTask,
                                 CustomerGroup, canonical, duration_ticks)
from research.adaptive_dispatch.environment import (Action, Active, Observation, PublicProblem,
                                                   PROFILES, WAIT, public_problem)


@dataclass(frozen=True)
class StaticContext:
    static: PublicProblem
    tasks: Mapping[str, BenchmarkTask]
    crews: Mapping[str, BenchmarkCrew]
    nominal: Mapping[str, int | None]
    ancestors: Mapping[str, frozenset[str]]
    descendants: Mapping[str, frozenset[str]]
    children: Mapping[str, frozenset[str]]
    depth: Mapping[str, int]
    mean_nominal: float
    customers: int


@dataclass(frozen=True)
class ValidatedState:
    observation: Observation
    context: StaticContext
    done: frozenset[str]
    active: Mapping[str, Active]
    available: tuple[str, ...]
    ready: tuple[str, ...]
    actions: tuple[Action, ...]

    @property
    def supported(self) -> bool:
        s = self.context.static
        return (len(s.tasks) <= 64 and len(s.executable) == len(s.tasks)
                and not any(g.unresolved_dependency for g in s.groups)
                and self.observation.now <= 10**12
                and all(v is not None and v <= 10**9 for v in self.context.nominal.values()))


@lru_cache(maxsize=128)
def static_context(static: PublicProblem) -> StaticContext:
    if type(static) is not PublicProblem or static.profile not in PROFILES:
        raise ValueError("Expected known public stochastic problem")
    if (type(static.tasks) is not tuple or type(static.groups) is not tuple or type(static.crews) is not tuple
            or any(type(t) is not BenchmarkTask for t in static.tasks)
            or any(type(g) is not CustomerGroup for g in static.groups)
            or any(type(c) is not BenchmarkCrew for c in static.crews)):
        raise ValueError("Invalid public entity types")
    p = BenchmarkProblem.model_validate(dict(id="syn-public-observation", family="public-only", seed=0,
        split="micro", tasks=static.tasks, groups=static.groups, crews=static.crews,
        horizon_ticks=static.horizon_ticks), strict=True)
    # Reparse nested models too: unchecked Pydantic model_copy must not bypass validation.
    p = BenchmarkProblem.model_validate(p.model_dump(), strict=True)
    if (type(static.nominal_ticks) is not tuple or type(static.executable) is not frozenset
            or len(static.nominal_ticks) != len(p.tasks)
            or any(type(pair) is not tuple or len(pair) != 2 or type(pair[0]) is not str
                   or (pair[1] is not None and type(pair[1]) is not int) for pair in static.nominal_ticks)):
        raise ValueError("Invalid known duration schema")
    nominal = dict(static.nominal_ticks)
    if len(nominal) != len(p.tasks) or set(nominal) != {t.id for t in p.tasks}:
        raise ValueError("Known-duration identity mismatch")
    conventions = []
    for convention in ("one_effective_worker", "ideal_all_people"):
        candidate = p.model_copy(update={"duration_assumption": convention})
        if {t.id: duration_ticks(candidate, t) for t in p.tasks} == nominal:
            conventions.append(candidate)
    if not conventions or public_problem(conventions[0], static.profile).executable != static.executable:
        raise ValueError("Known duration convention or executable closure mismatch")
    tasks = {t.id: t for t in p.tasks}
    ancestors, depth = {}, {}
    while len(ancestors) < len(tasks):
        for i, t in tasks.items():
            if i not in ancestors and set(t.prerequisites) <= ancestors.keys():
                ancestors[i] = frozenset({i} | {a for parent in t.prerequisites for a in ancestors[parent]})
                depth[i] = 1 + max((depth[parent] for parent in t.prerequisites), default=0)
    descendants = {i: frozenset(j for j in tasks if i in ancestors[j] and i != j) for i in tasks}
    children = {i: frozenset(j for j, t in tasks.items() if i in t.prerequisites) for i in tasks}
    known = [v for v in nominal.values() if v is not None]
    return StaticContext(static, MappingProxyType(tasks), MappingProxyType({c.id: c for c in p.crews}),
        MappingProxyType(nominal), MappingProxyType(ancestors), MappingProxyType(descendants),
        MappingProxyType(children), MappingProxyType(depth), sum(known)/len(known) if known else 0.,
        sum(len(g.customer_ids) for g in p.groups))


def validate_state(state: Observation) -> ValidatedState:
    if (type(state) is not Observation or type(state.now) is not int or state.now < 0
            or type(state.completed) is not tuple or type(state.active) is not tuple):
        raise ValueError("Invalid public observation schema")
    try:
        ctx = static_context(state.static)
    except (TypeError, AttributeError, OverflowError) as error:
        raise ValueError("Invalid public structure") from error
    done, active, intervals = {}, {}, {c: [] for c in ctx.crews}
    for raw in state.completed:
        if type(raw) is not Assignment:
            raise ValueError("Invalid completed record")
        a = Assignment.model_validate(raw.model_dump(), strict=True)
        if (a.task_id not in ctx.static.executable or a.task_id in done or a.crew_id not in ctx.crews
                or a.end_tick > state.now or a.end_tick <= a.start_tick
                or a.start_tick < ctx.crews[a.crew_id].available_tick
                or a.end_tick-a.start_tick not in ctx.static.support(a.task_id)):
            raise ValueError("Invalid observed completion")
        done[a.task_id] = a
        intervals[a.crew_id].append((a.start_tick, a.end_tick))
    for a in state.active:
        if (type(a) is not Active or type(a.task_id) is not str or type(a.crew_id) is not str
                or type(a.start_tick) is not int or a.start_tick < 0 or a.start_tick > state.now
                or a.task_id not in ctx.static.executable or a.task_id in done or a.task_id in active
                or a.crew_id not in ctx.crews or a.start_tick < ctx.crews[a.crew_id].available_tick):
            raise ValueError("Invalid active public record")
        ctx.static.support(a.task_id, state.now-a.start_tick)  # conditional support must be nonempty
        active[a.task_id] = a
        intervals[a.crew_id].append((a.start_tick, state.now+1))
    for a in (*done.values(), *active.values()):
        if any(parent not in done or done[parent].end_tick > a.start_tick for parent in ctx.tasks[a.task_id].prerequisites):
            raise ValueError("Observed prerequisite violation")
    for spans in intervals.values():
        ordered = sorted(spans)
        if any(a[1] > b[0] for a, b in zip(ordered, ordered[1:])):
            raise ValueError("Observed crew overlap/preemption")
    busy = {a.crew_id for a in active.values()}
    available = tuple(sorted(c for c, v in ctx.crews.items() if v.available_tick <= state.now and c not in busy))
    ready = tuple(sorted(t for t in ctx.static.executable - done.keys() - active.keys()
                         if set(ctx.tasks[t].prerequisites) <= done.keys()))
    terminal = not active and done.keys() == ctx.static.executable
    can_wait = not terminal and (bool(active) or any(c.available_tick > state.now for c in ctx.crews.values()))
    actions = tuple(Action(t, c) for t in ready for c in available) + ((WAIT,) if can_wait else ())
    return ValidatedState(state, ctx, frozenset(done), MappingProxyType(active), available, ready, actions)


def action_key(action: Action) -> tuple:
    return action == WAIT, action.task_id or "", action.crew_id or ""


def public_dict(state: Observation) -> dict:
    validate_state(state)
    s = state.static
    return dict(version="learned-public-state-v1", now=state.now,
        completed=[a.model_dump(mode="json") for a in state.completed], active=[vars(a) for a in state.active],
        static=dict(tasks=[t.model_dump(mode="json") for t in s.tasks],
                    groups=[g.model_dump(mode="json") for g in s.groups],
                    crews=[c.model_dump(mode="json") for c in s.crews],
                    nominal_ticks=list(s.nominal_ticks), executable=sorted(s.executable),
                    profile=s.profile, horizon_ticks=s.horizon_ticks))


def from_public_dict(payload: dict) -> Observation:
    if type(payload) is not dict or set(payload) != {"version", "now", "completed", "active", "static"} or payload["version"] != "learned-public-state-v1":
        raise ValueError("Unexpected public state fields/version")
    s = payload["static"]
    if type(s) is not dict or set(s) != {"tasks", "groups", "crews", "nominal_ticks", "executable", "profile", "horizon_ticks"}:
        raise ValueError("Unexpected public static fields")
    try:
        static = PublicProblem(
            tuple(BenchmarkTask.model_validate_json(canonical(t), strict=True) for t in s["tasks"]),
            tuple(CustomerGroup.model_validate_json(canonical(g), strict=True) for g in s["groups"]),
            tuple(BenchmarkCrew.model_validate_json(canonical(c), strict=True) for c in s["crews"]),
            tuple(tuple(p) for p in s["nominal_ticks"]), frozenset(s["executable"]), s["profile"], s["horizon_ticks"])
        active = []
        for a in payload["active"]:
            if type(a) is not dict or set(a) != {"task_id", "crew_id", "start_tick"}:
                raise ValueError("Unexpected active fields")
            active.append(Active(**a))
        state = Observation(static, payload["now"],
            tuple(Assignment.model_validate_json(canonical(a), strict=True) for a in payload["completed"]), tuple(active))
        validate_state(state)
        return state
    except (TypeError, KeyError, OverflowError) as error:
        raise ValueError("Malformed public observation") from error
