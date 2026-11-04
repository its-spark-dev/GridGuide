"""Offline synthetic simulation contracts; public HTTP schemas remain unchanged."""
from typing import Annotated, Literal
from pydantic import Field, model_validator
from backend.contracts import Contract
from benchmarks.contracts import BenchmarkProblem, Schedule
from benchmarks.validation import validate

ProfileID = Literal['deterministic-v1','independent-025-v1','independent-050-v1',
                    'shared-025-v1','shared-050-v1','storm-hold-v1','uniform-sensitivity-v1']


class SimulationInput(Contract):
    version: Literal['simulation-input-v1'] = 'simulation-input-v1'
    numerical_version: Literal['fixed-timetable-simulation-v1'] = 'fixed-timetable-simulation-v1'
    profile_version: Literal['simulation-profiles-v1'] = 'simulation-profiles-v1'
    evidence_class: Literal['scenario assumption'] = 'scenario assumption'
    problem: BenchmarkProblem
    schedule: Schedule
    profile: ProfileID
    trials: Annotated[int, Field(strict=True, ge=1, le=10000)] = 2000
    seed: Annotated[int, Field(strict=True, ge=0, le=2**63-1)] = 20261103

    @model_validator(mode='after')
    def valid_schedule(self):
        errors = validate(self.problem,self.schedule)
        if errors:
            raise ValueError('Invalid simulation schedule: '+','.join(errors))
        return self


class SimulationMetadata(Contract):
    version: Literal['simulation-output-v1'] = 'simulation-output-v1'
    numerical_version: str
    input_fingerprint: str
    schedule_fingerprint: str
    problem_fingerprint: str
    profile_sha256: str
    profile: ProfileID
    policy: str
    trials: int
    seed: int
    rng: str
    duration_assumption: str
    evidence_class: Literal['scenario assumption'] = 'scenario assumption'
    environment: dict[str,str]
    array_units: dict[str,str]
    numerical_sha256: str
