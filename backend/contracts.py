"""Explicit public allowlist. Private source records have separate internal types."""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .config import risk_band_for_score

Count = Annotated[int, Field(strict=True, ge=0)]
Access = Literal["clear", "restricted", "blocked"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Issue(Contract):
    code: str
    message: str


class MapPoint(Contract):
    longitude: Annotated[float, Field(ge=-180, le=180)]
    latitude: Annotated[float, Field(ge=-90, le=90)]
    crs: Literal["EPSG:4326"] = "EPSG:4326"
    precision_degrees: Literal[0.01] = 0.01
    approximate: Literal[True] = True


class PublicAsset(Contract):
    alias: str
    kind: Literal["Distribution", "Fuse", "Circuit Breaker"]
    resolution: Literal["exact_typed_id", "abstract_circuit_terminal"]
    map_position: MapPoint | None


class DependencyEdge(Contract):
    downstream_alias: str
    upstream_alias: str
    provenance: Literal["source_upstream_path"] = "source_upstream_path"


class Location(Contract):
    alias: str
    label: str
    map_position: MapPoint
    upstream_assets: tuple[PublicAsset, ...]
    dependency_edges: tuple[DependencyEdge, ...]
    topology_status: Literal["verified_subset"] = "verified_subset"
    topology_warnings: tuple[Issue, ...]
    unresolved_links: tuple[str, ...] = ()


class SourceFacts(Contract):
    kind: Literal["static_inventory_and_historical_extract"] = "static_inventory_and_historical_extract"
    snapshot_date: str
    path_types: tuple[str, ...]
    data_quality: Literal["verified_subset"] = "verified_subset"
    transformer_mounting: Literal["Overhead", "Underground", "Unknown"]
    historical_circuit_evidence: bool | None
    historical_damage_record_count: Count
    labor_unit_status: Literal["unspecified_workbook_labor_hours"] = "unspecified_workbook_labor_hours"


class WorkItem(Contract):
    task_id: Annotated[str, Field(min_length=1, max_length=64, pattern=r"^[a-z0-9-]+$")]
    node_alias: str
    recipe: str
    quantity: Annotated[int, Field(strict=True, ge=1, le=10)]


class Scenario(Contract):
    location_alias: str = "demo-a"
    scenario_revision: Annotated[int, Field(strict=True, ge=1)] = 1
    storm_level: Annotated[int, Field(strict=True, ge=0, le=3)] | None = 2
    crew_count: Annotated[int, Field(strict=True, ge=0, le=4)] = 1
    access: Access = "clear"
    work_items: tuple[WorkItem, ...]
    lifecycle_state: Literal["pre_storm"] = "pre_storm"
    provenance: Literal["declared_simulation"] = "declared_simulation"

    @model_validator(mode="after")
    def unique_tasks(self):
        if len({w.task_id for w in self.work_items}) != len(self.work_items):
            raise ValueError("Duplicate task IDs are not allowed")
        if len({w.node_alias for w in self.work_items}) != len(self.work_items):
            raise ValueError("Use quantity on one task per node; duplicate repair nodes are not allowed")
        return self


class Factor(Contract):
    id: str
    label: str
    provenance: Literal["source_fact", "simulated_input", "team_rule", "computed"]
    value: str | int | float | bool | None
    unit: str | None = None
    contribution_points: int | None = None
    source_refs: tuple[str, ...] = ()


class RiskResult(Contract):
    status: Literal["available", "insufficient_data"]
    band: Literal["LOW", "MODERATE", "HIGH", "SEVERE"] | None
    score: Annotated[int, Field(strict=True, ge=0, le=5)] | None
    probability: None = None
    predictive_confidence: Literal["LOW"] = "LOW"
    factors: tuple[Factor, ...]
    limitations: tuple[str, ...]
    missing_inputs: tuple[str, ...] = ()

    @model_validator(mode="after")
    def available_values(self):
        if self.status == "available":
            if self.score is None or self.band is None or self.missing_inputs:
                raise ValueError("An available risk result needs a score, band and complete inputs")
            if sum(f.contribution_points or 0 for f in self.factors) != self.score:
                raise ValueError("Risk contributions must sum to the score")
            if self.band != risk_band_for_score(self.score):
                raise ValueError("Risk band does not match the model's score boundaries")
        elif self.score is not None or self.band is not None or not self.missing_inputs:
            raise ValueError("Insufficient risk data requires null values and a missing-input reason")
        return self


class Bounds(Contract):
    lower: Annotated[float, Field(ge=0)]
    upper: Annotated[float, Field(ge=0)]

    @model_validator(mode="after")
    def ordered(self):
        if self.lower > self.upper:
            raise ValueError("Lower bound cannot exceed upper bound")
        return self


class LaborContribution(Contract):
    task_id: str
    node_alias: str
    recipe: str
    quantity: Count
    install_hours_per_unit: float
    remove_hours_per_unit: float
    direct_labor_hours: float
    source_refs: tuple[str, ...]
    provenance: Literal["source_rates_with_simulated_quantity"] = "source_rates_with_simulated_quantity"


class RepairStage(Contract):
    task_id: str
    node_alias: str
    depends_on_task_ids: tuple[str, ...]
    provenance: Literal["source_ancestry_with_assumed_serial_repairs"] = "source_ancestry_with_assumed_serial_repairs"


class RestorationResult(Contract):
    status: Literal["available", "pending_clearance", "pending_assignment", "insufficient_data"]
    kind: Literal["conditional_simulation"] = "conditional_simulation"
    unit: Literal["hours"] = "hours"
    provisional: Literal[True] = True
    time_origin: Literal["assigned_crew_begins_response"] = "assigned_crew_begins_response"
    raw_hours: Bounds | None
    display_hours: Bounds | None
    predictive_confidence: Literal["LOW"] = "LOW"
    direct_labor_hours: float
    access_labor_hours: float | None
    worksite_count: Count
    indirect_labor_multiplier: float
    modeled_effort_hours: float | None
    factors: tuple[Factor, ...]
    labor_contributions: tuple[LaborContribution, ...]
    repair_stages: tuple[RepairStage, ...]
    limitations: tuple[str, ...]
    missing_inputs: tuple[str, ...]

    @model_validator(mode="after")
    def status_matches_range(self):
        if self.status == "available":
            if self.raw_hours is None or self.display_hours is None or self.missing_inputs:
                raise ValueError("Available duration needs bounds and complete inputs")
            if self.display_hours.lower > self.raw_hours.lower or self.display_hours.upper < self.raw_hours.upper:
                raise ValueError("Displayed bounds must enclose the raw range")
        elif self.raw_hours is not None or self.display_hours is not None or not self.missing_inputs:
            raise ValueError("Unavailable duration requires null bounds and a reason")
        return self


class Assumption(Contract):
    id: str
    description: str
    value: str | float
    provenance: Literal["team_assumption"] = "team_assumption"


class ConfirmedUtility(Contract):
    outage_status: None = None
    restoration_time: None = None


class ModelVersions(Contract):
    risk: str
    restoration: str
    assumptions: str


class Evaluation(Contract):
    schema_version: Literal["1.0"] = "1.0"
    result_id: str
    scenario_revision: int
    data_snapshot: str
    model_versions: ModelVersions
    location: Location
    source_facts: SourceFacts
    confirmed_utility: ConfirmedUtility = ConfirmedUtility()
    simulated_inputs: Scenario
    risk: RiskResult
    restoration: RestorationResult
    assumptions: tuple[Assumption, ...]
    limitations: tuple[str, ...]
    generated_explanation: None = None


class Change(Contract):
    field: str
    before: str | int | float | None
    after: str | int | float | None
    delta: float | None = None
    unit: str | None = None
    cause_factor_ids: tuple[str, ...]


class Comparison(Contract):
    before_result_id: str
    after_result_id: str
    changes: tuple[Change, ...]
    explanation: str
    explanation_kind: Literal["deterministic_calculation_summary"] = "deterministic_calculation_summary"


class Preparation(Contract):
    actions: tuple[str, ...]
    safety: tuple[str, ...]
    duration_known: bool
    note: str


class AlertEligibility(Contract):
    eligible: bool | None
    reason: str
    suggested_channels: tuple[Literal["app", "sms", "phone_call"], ...]
    delivery: Literal["preview_only"] = "preview_only"
    priority_needs_declared: Literal[False] = False
    timing: dict[str, str]
    assumptions: str = "Thresholds are team assumptions, not official utility eligibility rules."


Lifecycle = Literal["pre_storm", "outage_confirmed", "estimate_updated", "restored"]


class CommunicationPreview(Contract):
    state: Lifecycle
    title: str
    body: str
    available: bool
    source: Literal["teammate_template_adapted", "null_state_adapter"]


class CustomerJourney(Contract):
    result_id: str
    source: Literal["pipeline.guidance"] = "pipeline.guidance"
    preparation: Preparation
    alerts: AlertEligibility
    messages: tuple[CommunicationPreview, ...]
    selected_state: Lifecycle
    estimate_update_eligible: bool
    update_reason: str
    delivery_note: str = "Preview only. No SMS, email or phone service is connected; no alert has been sent."
