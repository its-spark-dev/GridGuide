"""Event-driven dynamics. Policies receive Observation, never Environment."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
import hashlib
import math
from typing import Callable

from benchmarks.contracts import (Assignment, BenchmarkCrew, BenchmarkProblem,
                                 BenchmarkTask, CustomerGroup, Schedule, canonical, duration_ticks)
from benchmarks.metrics import calculate
from benchmarks.validation import validate

from . import VERSION

PROFILES = {"deterministic": (Fraction(1),), "low": (Fraction(1, 2), Fraction(3, 2)),
            "high": (Fraction(1, 4), Fraction(1, 2), Fraction(9, 4))}


@dataclass(frozen=True, order=True)
class Action:
    task_id: str | None = None
    crew_id: str | None = None

    def __post_init__(self):
        if (self.task_id is None) != (self.crew_id is None):
            raise ValueError("Wait has neither task nor crew")
        if self.task_id is not None and (type(self.task_id) is not str or type(self.crew_id) is not str):
            raise ValueError("Action IDs must be strings")


WAIT = Action()


@dataclass(frozen=True)
class Active:
    task_id: str
    crew_id: str
    start_tick: int


@dataclass(frozen=True)
class PublicProblem:
    tasks: tuple[BenchmarkTask, ...]
    groups: tuple[CustomerGroup, ...]
    crews: tuple[BenchmarkCrew, ...]
    nominal_ticks: tuple[tuple[str, int | None], ...]
    executable: frozenset[str]
    profile: str
    horizon_ticks: int

    def support(self, task_id: str, elapsed: int = -1) -> tuple[int, ...]:
        nominal = dict(self.nominal_ticks)[task_id]
        if nominal is None:
            raise ValueError("Unavailable repair has no duration distribution")
        values = tuple(math.ceil(nominal * m) for m in PROFILES[self.profile])
        # Retain repeated values: equal original support points carry equal probability.
        conditional = tuple(v for v in values if v > elapsed)
        if not conditional:
            raise ValueError("Observation has zero probability under declared duration model")
        return conditional


@dataclass(frozen=True)
class Observation:
    static: PublicProblem
    now: int
    completed: tuple[Assignment, ...]
    active: tuple[Active, ...]

    @property
    def available_crews(self) -> tuple[str, ...]:
        busy = {a.crew_id for a in self.active}
        return tuple(sorted(c.id for c in self.static.crews if c.available_tick <= self.now and c.id not in busy))

    @property
    def ready_tasks(self) -> tuple[str, ...]:
        done = {a.task_id for a in self.completed}
        started = done | {a.task_id for a in self.active}
        return tuple(sorted(t.id for t in self.static.tasks if t.id in self.static.executable
                            and t.id not in started and set(t.prerequisites) <= done))

    @property
    def terminal(self) -> bool:
        return not self.active and {a.task_id for a in self.completed} == self.static.executable

    @property
    def can_wait(self) -> bool:
        return not self.terminal and (bool(self.active) or any(c.available_tick > self.now for c in self.static.crews))

    def actions(self, canonical_crew: bool = False) -> tuple[Action, ...]:
        crews = self.available_crews[:1] if canonical_crew else self.available_crews
        return tuple(Action(t, c) for t in self.ready_tasks for c in crews) + ((WAIT,) if self.can_wait else ())


def public_problem(problem: BenchmarkProblem, profile: str) -> PublicProblem:
    if profile not in PROFILES:
        raise ValueError("Unknown stochastic profile")
    executable: set[str] = set()
    while True:
        added = {t.id for t in problem.tasks if duration_ticks(problem, t) is not None
                 and set(t.prerequisites) <= executable} - executable
        if not added:
            break
        executable |= added
    return PublicProblem(problem.tasks, problem.groups, problem.crews,
                         tuple((t.id, duration_ticks(problem, t)) for t in problem.tasks),
                         frozenset(executable), profile, problem.horizon_ticks)


def keyed_choice(values: tuple[int, ...], key: object) -> int:
    """Exact rejection sampling from SHA-256 counter blocks; no modulo bias."""
    n, counter = len(values), 0
    if not n:
        raise ValueError("Empty support")
    ceiling = (1 << 256) // n * n
    while True:
        integer = int.from_bytes(hashlib.sha256(canonical([key, counter])).digest(), "big")
        if integer < ceiling:
            return values[integer % n]
        counter += 1


def sample_durations(problem: BenchmarkProblem, profile: str, episode_seed: int) -> dict[str, int]:
    if type(episode_seed) is not int or episode_seed < 0:
        raise ValueError("Episode seed must be a nonnegative integer")
    static = public_problem(problem, profile)
    return {t.id: keyed_choice(static.support(t.id), [VERSION, "environment", problem.fingerprint,
            profile, episode_seed, t.id]) for t in problem.tasks if t.id in static.executable}


class Environment:
    def __init__(self, problem: BenchmarkProblem, profile: str, durations: dict[str, int]):
        # Reparse unchecked model_copy edits at the public boundary.
        self.problem = BenchmarkProblem.model_validate(problem.model_dump())
        self.static = public_problem(self.problem, profile)
        if set(durations) != self.static.executable:
            raise ValueError("Duration scope mismatch")
        if any(type(v) is not int or v not in self.static.support(k) for k, v in durations.items()):
            raise ValueError("Duration outside declared discrete support")
        self._durations = dict(durations)
        self.now = 0
        self.completed: list[Assignment] = []
        self.active: list[Active] = []

    @classmethod
    def hypothetical(cls, state: Observation, durations: dict[str, int]) -> Environment:
        """Search rollout from public state with independently sampled hypothetical work."""
        obj = cls.__new__(cls)
        obj.static = state.static
        obj.now = state.now
        obj.completed = list(state.completed)
        obj.active = list(state.active)
        obj._durations = dict(durations)
        obj.problem = None  # hypothetical rollouts cannot impersonate a validated real episode
        if set(durations) != state.static.executable or any(
                type(v) is not int or v not in state.static.support(k) for k, v in durations.items()):
            raise ValueError("Invalid hypothetical duration scope/support")
        if any(durations[a.task_id] != a.end_tick-a.start_tick for a in state.completed):
            raise ValueError("Hypothetical history contradicts observed completion")
        for a in state.active:
            if durations[a.task_id] not in state.static.support(a.task_id, state.now-a.start_tick):
                raise ValueError("Hypothetical active duration contradicts observation")
        return obj

    def observe(self) -> Observation:
        return Observation(self.static, self.now, tuple(sorted(self.completed, key=lambda a: (a.end_tick, a.task_id))),
                           tuple(sorted(self.active, key=lambda a: a.task_id)))

    def step(self, action: Action) -> Observation:
        state = self.observe()
        if type(action) is not Action or action not in state.actions():
            raise ValueError("Invalid, blocked, duplicate or unavailable action")
        if action == WAIT:
            events = [a.start_tick + self._durations[a.task_id] for a in self.active]
            events += [c.available_tick for c in self.static.crews if c.available_tick > self.now]
            self.now = min(events)
            finished = [a for a in self.active if a.start_tick + self._durations[a.task_id] == self.now]
            for a in finished:
                self.completed.append(Assignment(task_id=a.task_id, crew_id=a.crew_id,
                                                 start_tick=a.start_tick, end_tick=self.now))
            self.active = [a for a in self.active if a not in finished]
        else:
            self.active.append(Active(action.task_id, action.crew_id, self.now))
        return self.observe()


def conditional_problem(problem: BenchmarkProblem, durations: dict[str, int]) -> BenchmarkProblem:
    """Exact duration materialization solely for the independent G2 checker."""
    # one_effective_worker makes exact integer seconds possible via rational Decimal hours;
    # use a decimal strictly within the interval whose ceiling is the intended integer.
    tasks = tuple(BenchmarkTask.model_validate({**t.model_dump(), "total_person_hours":
                  (Decimal(durations[t.id]) - Decimal("0.1")) / Decimal(3600)}) if t.id in durations else t
                  for t in problem.tasks)
    return BenchmarkProblem.model_validate({**problem.model_dump(), "duration_assumption": "one_effective_worker",
                                            "tasks": tasks})


def checked_result(problem: BenchmarkProblem, durations: dict[str, int], assignments: tuple[Assignment, ...], policy: str) -> dict:
    conditional = conditional_problem(problem, durations)
    schedule = Schedule(problem_fingerprint=conditional.fingerprint, policy=policy, assignments=assignments,
                        unscheduled_tasks=tuple(sorted({t.id for t in problem.tasks} - {a.task_id for a in assignments})))
    metrics = calculate(conditional, schedule)
    errors = validate(conditional, schedule, metrics)
    if errors:
        raise RuntimeError(f"Independent validation failed: {errors}")
    return {"original_problem_fingerprint": problem.fingerprint,
            "conditional_problem_fingerprint": conditional.fingerprint,
            "schedule": schedule.model_dump(mode="json"), "metrics": metrics}


def run_episode(problem: BenchmarkProblem, profile: str, episode_seed: int,
                policy: Callable[[Observation], Action], name: str, trace: bool = False) -> dict:
    import time
    durations = sample_durations(problem, profile, episode_seed)
    env = Environment(problem, profile, durations)
    records, timings, choice_counts = [], [], []
    while not (state := env.observe()).terminal:
        begun = time.perf_counter_ns()
        action = policy(state)
        timings.append(time.perf_counter_ns() - begun)
        choice_counts.append(len(state.actions(canonical_crew=True)))
        records.append({"now": state.now, "completed": [a.model_dump() for a in state.completed],
                        "active": [vars(a) for a in state.active], "action": vars(action)})
        env.step(action)
    result = checked_result(problem, durations, tuple(env.completed), name)
    from .validation import validate_trajectory
    errors = validate_trajectory(problem, profile, durations, records, result["schedule"])
    if errors:
        raise RuntimeError(f"Independent trajectory validation failed: {errors}")
    result.update(profile=profile, episode_seed=episode_seed, durations=durations,
                  decision_nanoseconds=timings, decision_choice_counts=choice_counts,
                  trajectory_validated=True, trace=records if trace else [])
    return result
