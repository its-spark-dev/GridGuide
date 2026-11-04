"""Strict shared HTTP/export contracts for bounded fictional review only."""
from datetime import datetime
from typing import Annotated, Literal
from pydantic import Field, model_validator
from backend.contracts import Contract, SyntheticID
from benchmarks.contracts import BenchmarkProblem, Schedule

Digest = Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]
Number = Annotated[float, Field(ge=0, strict=True)]
Count = Annotated[int, Field(ge=0, strict=True)]
Policy = Literal['fifo-v1', 'customer-count-v1', 'legacy-release-per-person-hour-adapter-v1',
                 'legacy-critical-proxy-first-adapter-v1', 'restoration-cpsat-v1']
Reason = Literal['lowest-modeled-customer-hours','critical-service-tradeoff','fairness-consideration',
                 'conservative-baseline-preference','demonstration-comparison']

class Precedence(Contract):
    before: SyntheticID
    after: SyntheticID

class CompareRequest(Contract):
    version: Literal['operator-request-v1'] = 'operator-request-v1'
    scenario_id: SyntheticID
    scenario_revision: Literal[1] = 1
    scenario_fingerprint: Digest
    revision: Annotated[int, Field(strict=True, ge=1, le=1000000)] = 1
    selected_policy: Policy = 'legacy-release-per-person-hour-adapter-v1'
    include_experimental: Annotated[bool, Field(strict=True)] = False
    precedence: Annotated[tuple[Precedence, ...], Field(max_length=16)] = ()

class Milestone(Contract):
    tick: Count
    additional_customers: Count
    cumulative_customers: Count

class ReviewMetrics(Contract):
    version: Literal['benchmark-metrics-v1']
    customers: Count
    release_ticks: dict[SyntheticID, Count | None]
    milestones: tuple[Milestone, ...]
    modeled_customer_outage_hours: Number | None
    restricted_horizon_customer_hours: Number
    horizon_hours: Literal[168]
    unresolved_customers: Count
    censored_customers: Count
    unreleased_customers_at_horizon: Count
    known_release_customers: Count
    makespan_hours: Number | None
    full_customer_release_hours: Number | None
    release_50_hours: Number | None
    release_90_hours: Number | None
    release_100_hours: Number | None
    weighted_median_hours: Number | None
    weighted_p95_hours: Number | None
    maximum_wait_hours: Number | None
    critical_service_latency_hours: dict[SyntheticID, Number | None]
    branch_mean_wait_hours: dict[SyntheticID, Number | None]
    branch_mean_disparity_hours: Number | None
    small_group_customers: Count
    small_group_mean_wait_hours: Number | None

class PolicyResult(Contract):
    policy: Policy
    schedule: Schedule
    metrics: ReviewMetrics
    feasibility: Literal['independently_validated'] = 'independently_validated'
    origin: Literal['recomputed_baseline','frozen_g3_protected_result']
    returned_source: Literal['baseline','solver']
    baseline_policy: Policy
    solver_status: str | None = None
    fallback_reason: str | None = None
    primary_optimal: bool = False
    best_bound_ticks: Number | None = None
    relative_gap: Number | None = None
    recorded_seconds: Number | None = None
    timing_scope: Literal['not_recorded','historical_g3_wrapper'] = 'not_recorded'
    tradeoffs: tuple[str, ...]
    explanation: str

class Evidence(Contract):
    version: Literal['operator-evidence-v1'] = 'operator-evidence-v1'
    origin: Literal['independently_authored_synthetic'] = 'independently_authored_synthetic'
    topology_effort_crews: Literal['scenario assumption'] = 'scenario assumption'
    scheduling_release_rules: Literal['prototype policy'] = 'prototype policy'
    override_precedence: Literal['user-declared'] = 'user-declared'
    observed_outcomes_clearance_efficiency: Literal['unavailable'] = 'unavailable'

class OperatorComparison(Contract):
    version: Literal['operator-comparison-v1'] = 'operator-comparison-v1'
    catalog_fingerprint: Digest
    request: CompareRequest
    problem: BenchmarkProblem
    evidence: Evidence = Evidence()
    recommended_policy: Literal['legacy-release-per-person-hour-adapter-v1'] = 'legacy-release-per-person-hour-adapter-v1'
    best_of_four_policy: Policy
    results: tuple[PolicyResult, ...]
    experimental_status: Literal['not_requested','supported_frozen','unsupported_override']
    uncertainty: Literal['not_integrated_no_quantiles'] = 'not_integrated_no_quantiles'
    explanation: str
    result_fingerprint: Digest

class Acknowledgements(Contract):
    @model_validator(mode='before')
    @classmethod
    def explicit_true(cls, value):
        if not isinstance(value, dict) or any(v is not True for v in value.values()):
            raise ValueError('Explicit acknowledgements required')
        return value

    fictional: Literal[True]
    modeled_not_field_confirmed: Literal[True]
    gaps_and_unresolved: Literal[True]
    objective_and_tradeoffs: Literal[True]
    experimental_and_simulation_limits: Literal[True]

class ReviewRequest(Contract):
    request: CompareRequest
    result_fingerprint: Digest
    acknowledgements: Acknowledgements
    reason: Reason

class ReviewRecord(Contract):
    status: Literal['reviewed_in_demo'] = 'reviewed_in_demo'
    timestamp: str
    reason: Reason
    acknowledgements: Acknowledgements
    selected_policy: Policy
    result_fingerprint: Digest

    @model_validator(mode='after')
    def time_format(self):
        if not self.timestamp.endswith('Z'): raise ValueError('Invalid review time')
        datetime.fromisoformat(self.timestamp.replace('Z','+00:00'))
        return self

class ReviewArtifact(Contract):
    version: Literal['operator-review-artifact-v1'] = 'operator-review-artifact-v1'
    comparison: OperatorComparison
    review: ReviewRecord
    checksum: Digest

class ReviewExport(Contract):
    artifact: ReviewArtifact
    summary: str

class ReviewScenario(Contract):
    scenario_id: SyntheticID
    scenario_revision: Literal[1] = 1
    scenario_fingerprint: Digest
    label: str
    problem: BenchmarkProblem

class ReviewCatalog(Contract):
    version: Literal['operator-catalog-v1'] = 'operator-catalog-v1'
    catalog_fingerprint: Digest
    scenarios: tuple[ReviewScenario, ...]
