"""Versioned offline benchmark contracts, intentionally not HTTP API contracts."""
from decimal import Decimal, ROUND_CEILING
import hashlib
import json
from typing import Annotated, Literal
from pydantic import Field, model_validator
from backend.contracts import Contract, SyntheticID, CrewSize

Tick = Annotated[int, Field(strict=True, ge=0)]
Effort = Annotated[Decimal, Field(gt=0, allow_inf_nan=False)]


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


class BenchmarkTask(Contract):
    id: SyntheticID
    total_person_hours: Effort | None
    prerequisites: tuple[SyntheticID, ...] = ()
    report_order: Tick
    access: Literal['clear', 'blocked', 'unresolved'] = 'clear'


class CustomerGroup(Contract):
    id: SyntheticID
    customer_ids: Annotated[tuple[SyntheticID, ...], Field(min_length=1)]
    required_tasks: tuple[SyntheticID, ...]
    unresolved_dependency: bool = False
    branch: SyntheticID
    critical_service: bool = False


class BenchmarkCrew(Contract):
    id: SyntheticID
    available_tick: Tick = 0
    people: CrewSize = 4


class BenchmarkProblem(Contract):
    version: Literal['benchmark-problem-v1'] = 'benchmark-problem-v1'
    id: SyntheticID
    revision: Literal[1] = 1
    generator_version: Literal['benchmark-generator-v1'] = 'benchmark-generator-v1'
    family: str
    seed: Tick
    split: Literal['development', 'evaluation', 'micro']
    origin: Literal['independently_authored_synthetic'] = 'independently_authored_synthetic'
    response_origin: Literal['modeled_response_start'] = 'modeled_response_start'
    horizon_ticks: Literal[604800] = 604800
    duration_assumption: Literal['one_effective_worker', 'ideal_all_people'] = 'one_effective_worker'
    tasks: Annotated[tuple[BenchmarkTask, ...], Field(min_length=1, max_length=100)]
    groups: Annotated[tuple[CustomerGroup, ...], Field(min_length=1)]
    crews: Annotated[tuple[BenchmarkCrew, ...], Field(min_length=1, max_length=4)]
    # Exactly one classification per important input/rule; no inherited source facts.
    input_classification: Literal['scenario assumption'] = 'scenario assumption'
    duration_rule_classification: Literal['prototype policy'] = 'prototype policy'
    precedence_classification: Literal['prototype policy'] = 'prototype policy'
    missing_evidence_classification: Literal['unavailable'] = 'unavailable'
    actual_efficiency: None = None
    observed_outcomes: None = None

    @model_validator(mode='after')
    def integrity(self):
        tasks = {t.id: t for t in self.tasks}
        ids = [t.id for t in self.tasks] + [g.id for g in self.groups] + [c.id for c in self.crews]
        members = [c for g in self.groups for c in g.customer_ids]
        if len(set(ids)) != len(ids) or len(set(members)) != len(members) or set(ids) & set(members):
            raise ValueError('Duplicate entity or customer membership')
        if len({c.people for c in self.crews}) != 1:
            raise ValueError('v1 compares identical crew composition only')
        done = set()
        while len(done) < len(tasks):
            ready = {t.id for t in self.tasks if set(t.prerequisites) <= done} - done
            if not ready:
                raise ValueError('Cyclic or undefined repair prerequisite')
            done |= ready
        for t in self.tasks:
            if len(set(t.prerequisites)) != len(t.prerequisites):
                raise ValueError('Duplicate prerequisite')
        for g in self.groups:
            if not set(g.required_tasks) <= tasks.keys() or len(set(g.required_tasks)) != len(g.required_tasks):
                raise ValueError('Invalid customer dependency')
        return self

    @property
    def fingerprint(self):
        return hashlib.sha256(canonical(self.model_dump(mode='json'))).hexdigest()


def duration_ticks(problem, task):
    if task.access != 'clear' or task.total_person_hours is None:
        return None
    people = problem.crews[0].people if problem.duration_assumption == 'ideal_all_people' else 1
    return int((task.total_person_hours * 3600 / people).to_integral_value(rounding=ROUND_CEILING))


class Assignment(Contract):
    task_id: SyntheticID
    crew_id: SyntheticID
    start_tick: Tick
    end_tick: Tick


class Schedule(Contract):
    version: Literal['benchmark-schedule-v1'] = 'benchmark-schedule-v1'
    problem_fingerprint: str
    policy: str
    assignments: tuple[Assignment, ...]
    unscheduled_tasks: tuple[SyntheticID, ...]
