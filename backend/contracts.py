"""Explicit public allowlist. Private source records have separate internal types."""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .config import risk_band_for_score

Count = Annotated[int, Field(strict=True, ge=0)]
Access = Literal["clear", "restricted", "blocked"]
CrewSize = Annotated[int, Field(strict=True, ge=2, le=8)]
EvidenceClass = Literal["AEP-specified", "source-derived", "scenario assumption", "prototype policy", "user-declared", "unavailable"]
Need = Literal["medical", "accessibility", "critical_responsibility"]


class DeclaredNeeds(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    selections: Annotated[tuple[Need, ...], Field(max_length=3)] = ()
    classification: Literal["user-declared"] = "user-declared"

    @model_validator(mode="after")
    def unique_selections(self):
        if len(set(self.selections)) != len(self.selections):
            raise ValueError("Duplicate declarations are not allowed")
        return self


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
    labor_unit_status: Literal["AEP_direct_labor_times_4_5_is_person_hours"] = "AEP_direct_labor_times_4_5_is_person_hours"


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
    crew_size: CrewSize = 4
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
    classification: EvidenceClass
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
    rate_classification: Literal["source-derived"] = "source-derived"
    quantity_classification: Literal["scenario assumption"] = "scenario assumption"


class RepairStage(Contract):
    task_id: str
    node_alias: str
    depends_on_task_ids: tuple[str, ...]
    provenance: Literal["source_ancestry_with_assumed_serial_repairs"] = "source_ancestry_with_assumed_serial_repairs"
    repair_person_hours: float
    newly_eligible_customers: Count | None
    release_status: Literal["conditional_only"] = "conditional_only"


class FacilityCount(Contract):
    kind: Literal["hospital", "fire_station", "ambulance"]
    source_layer: str
    regional_features: Count
    within_primary_extent: Count | None
    classification: Literal["source-derived"] = "source-derived"


class AssetImpact(Contract):
    node_alias: str
    status: Literal["verified_reverse_dependency", "unavailable"]
    identity_basis: Literal["exact_typed_GIS_and_topology", "unavailable"]
    topology_path_count: Count | None
    dependent_customers: Count | None
    unresolved_path_count: Count
    damage_classification: Literal["scenario assumption"] = "scenario assumption"
    dependency_classification: Literal["source-derived", "unavailable"]
    source_refs: tuple[str, ...]
    note: str


class RestorationPriority(Contract):
    circuit_customer_paths: Count
    dependent_customer_paths: Count | None
    paths_outside_declared_damage: Count | None
    asset_impacts: tuple[AssetImpact, ...]
    damage_origin: Literal["declared_on_source_verified_assets"] = "declared_on_source_verified_assets"
    arcos_asset_match: Literal["unavailable"] = "unavailable"
    arcos_affected_customers: None = None
    sectionalization_restorable_customers: None = None
    facilities: tuple[FacilityCount, ...]
    affected_critical_facilities: None = None
    switching_feasibility: Literal["unavailable"] = "unavailable"
    priority_score: None = None
    recommended_first_task: str | None
    reasoning: str
    criticality_action: str
    limitations: tuple[str, ...]
    classification: Literal["prototype policy"] = "prototype policy"


class RestorationResult(Contract):
    status: Literal["available", "pending_clearance", "pending_assignment", "insufficient_data"]
    kind: Literal["conditional_simulation"] = "conditional_simulation"
    unit: Literal["elapsed hours"] = "elapsed hours"
    provisional: Literal[True] = True
    time_origin: Literal["assigned_crew_begins_response"] = "assigned_crew_begins_response"
    raw_hours: Bounds | None
    display_hours: Bounds | None
    predictive_confidence: Literal["LOW"] = "LOW"
    direct_labor_hours: float
    installation_direct_hours: float
    removal_direct_hours: float
    access_labor_hours: float | None
    worksite_count: Count
    indirect_labor_multiplier: float
    repair_person_hours: float
    total_person_hours: float | None
    effort_unit: Literal["person-hours"] = "person-hours"
    actual_conversion_efficiency: None = None
    elapsed_method: Literal["serial_tasks_ideal_to_single_effective_worker"] = "serial_tasks_ideal_to_single_effective_worker"
    priority: RestorationPriority
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
    value: str | float | None
    classification: EvidenceClass


class ConfirmedUtility(Contract):
    outage_status: None = None
    restoration_time: None = None


class ModelVersions(Contract):
    risk: str
    restoration: str
    assumptions: str


class Evaluation(Contract):
    schema_version: Literal["2.0"] = "2.0"
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
    changed_inputs: tuple[Literal["access", "crew_size"], ...] = ()
    explanation_kind: Literal["deterministic_calculation_summary"] = "deterministic_calculation_summary"


class Preparation(Contract):
    actions: tuple[str, ...]
    safety: tuple[str, ...]
    duration_known: bool
    note: str
    declared_actions: tuple[str, ...] = ()


class AlertEligibility(Contract):
    eligible: bool | None
    reason: str
    suggested_channels: tuple[Literal["app", "sms", "phone_call"], ...]
    delivery: Literal["preview_only"] = "preview_only"
    priority_needs_declared: bool = False
    escalation_guidance: str
    classification: Literal["prototype policy"] = "prototype policy"
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
    declared_needs: DeclaredNeeds = DeclaredNeeds()
    source: Literal["pipeline.guidance"] = "pipeline.guidance"
    preparation: Preparation
    alerts: AlertEligibility
    messages: tuple[CommunicationPreview, ...]
    selected_state: Lifecycle
    estimate_update_eligible: bool
    update_reason: str
    delivery_note: str = "Preview only. No SMS, email or phone service is connected; no alert has been sent."


class GeographicAsset(Contract):
    alias: str
    label: str
    kind: Literal["customer", "transformer", "fuse", "circuit_terminal"]
    position: MapPoint | None
    geometry_status: Literal["verified_generalized", "unavailable"]
    source_layer: Literal["Customer_Clip", "Transformer_Clip", "Fuse_Bank_Clip"] | None
    provenance: Literal["verified_customer_record", "verified_typed_upstream_id", "abstract_circuit_terminal"]

    @model_validator(mode="after")
    def geometry_consistent(self):
        if (self.position is None) != (self.geometry_status == "unavailable"):
            raise ValueError("Unavailable geometry must have a null position")
        if self.kind == "circuit_terminal" and (self.position is not None or self.source_layer is not None):
            raise ValueError("Abstract circuit terminal has no supplied geometry")
        return self


class PrimaryLineContext(Contract):
    alias: Literal["primary-context-a"] = "primary-context-a"
    source_layer: Literal["Primary_ExportFeatures"] = "Primary_ExportFeatures"
    provenance: Literal["verified_circuit_code_alias_station"] = "verified_circuit_code_alias_station"
    topology_verified: Literal[False] = False
    status: Literal["available", "unavailable"]
    paths: tuple[tuple[MapPoint, ...], ...]
    source_segment_count: Count
    omitted_collapsed_parts: Count
    note: str

    @model_validator(mode="after")
    def valid_paths(self):
        if (self.status == "available") != bool(self.paths):
            raise ValueError("Available line context must contain paths")
        if any(len(path) < 2 or len({(p.longitude, p.latitude) for p in path}) < 2 for path in self.paths):
            raise ValueError("A line requires at least two distinct source-derived points")
        return self


class GeographicMap(Contract):
    schema_version: Literal["map-v1"] = "map-v1"
    location_alias: str
    data_snapshot: str
    region_label: Literal["Virginia challenge data"] = "Virginia challenge data"
    crs: Literal["EPSG:4326"] = "EPSG:4326"
    precision_degrees: Literal[0.01] = 0.01
    assets: tuple[GeographicAsset, ...]
    primary_lines: PrimaryLineContext
    disclosures: tuple[str, ...]


ExplanationIntent = Literal["risk", "restoration", "change", "preparation", "availability", "topology", "alerts", "labor", "priority", "impact", "crew_plan", "unsupported"]
ExplanationSource = Literal["modeled", "simulated", "verified", "mixed"]


class ExplanationClause(Contract):
    id: str
    text: str
    source_type: ExplanationSource


class ExplanationContext(Contract):
    """Provider allowlist: no coordinates, source rows, contact fields or raw IDs."""
    version: Literal["explanation-v2"] = "explanation-v2"
    scope: Literal["customer", "restoration_plan"] = "customer"
    result_id: str
    scenario_revision: int
    location_label: str
    dataset_note: str
    risk_band: Literal["LOW", "MODERATE", "HIGH", "SEVERE"] | None
    risk_confidence: Literal["LOW"]
    outage_probability: None = None
    restoration_status: str
    restoration_bounds: Bounds | None
    repair_person_hours: float
    total_person_hours: float | None
    crew_size: CrewSize
    access: Access
    topology: tuple[str, ...]
    alert_eligible: bool | None
    alert_delivery: Literal["preview_only"] = "preview_only"
    assumptions: tuple[str, ...]
    limitations: tuple[str, ...]
    clauses: tuple[ExplanationClause, ...]


class ModelSelection(Contract):
    """No free prose, numbers or new facts can cross this model boundary."""
    result_id: str
    intent: ExplanationIntent
    supporting_refs: Annotated[tuple[str, ...], Field(min_length=1, max_length=3)]


class ExplanationResponse(Contract):
    result_id: str
    scenario_revision: int
    intent: ExplanationIntent
    answer: str
    supporting_factors: tuple[ExplanationClause, ...]
    uncertainty_note: str
    dataset_note: str
    source_type: ExplanationSource
    mode: Literal["ai_assisted", "standard", "unsupported"]
    fallback_reason: Literal["not_configured", "timeout", "provider_unavailable", "invalid_response", "unsupported_question"] | None


class CandidateAccess(Contract):
    candidate_id: str
    access: Access


class PlanRequest(Contract):
    scenario_revision: Annotated[int, Field(strict=True, ge=1)] = 1
    crew_count: Annotated[int, Field(strict=True, ge=1, le=2)] = 1
    crew_size: CrewSize = 4
    use_critical_proxy: bool = True
    access: tuple[CandidateAccess, ...] = ()

    @model_validator(mode="after")
    def unique_access(self):
        if len({a.candidate_id for a in self.access}) != len(self.access):
            raise ValueError("Duplicate candidate selection")
        return self


class PlanExplanationRequest(PlanRequest):
    result_id: Annotated[str, Field(min_length=1, max_length=128)]
    question: Annotated[str, Field(min_length=1, max_length=240)]


class ImpactCell(Contract):
    position: MapPoint
    premises: Count


class CriticalProxyContext(Contract):
    kind: str
    distance_m: float
    runner_up_distance_m: float
    classification: Literal["prototype policy"] = "prototype policy"
    relationship: Literal["spatially associated critical premise proxy"] = "spatially associated critical premise proxy"
    verified_electrical_attachment: None = None


class PlanCandidate(Contract):
    id: str
    label: str
    kind: str
    damage_source: Literal["historical ARCOS replay", "declared damage scenario"]
    match_method: str
    match_distance_m: float | None
    pole_distance_m: float | None
    runner_up_distance_m: float | None
    evidence_note: str
    dependent_premises: Count | None
    overlap_premises: Count | None
    prerequisite_ids: tuple[str, ...]
    direct_labor_hours: float
    repair_person_hours: float
    access: Access
    access_direct_hours: float | None
    total_person_hours: float | None
    elapsed_hours: Bounds | None
    potential_release_at_stage: Count | None
    release_per_total_person_hour: float | None
    critical_proxies: tuple[CriticalProxyContext, ...]
    status: Literal["scheduled", "blocked", "dependency_blocked", "evidence_unavailable"]
    priority_rank: int | None
    reason: str
    position: MapPoint | None
    customer_cells: tuple[ImpactCell, ...]
    current_damage_confirmed: None = None
    actually_restorable_via_switching: None = None


class PlanTask(Contract):
    candidate_id: str
    crew: int
    start_hours: Bounds
    finish_hours: Bounds
    display_finish_hours: Bounds


class ReleaseMilestone(Contract):
    candidate_ids: tuple[str, ...]
    elapsed_hours: Bounds
    display_hours: Bounds
    additional_premises: Count
    cumulative_premises: Count


class PlanCoverage(Contract):
    indexed_paths: Count
    indexed_assets: Count
    indexed_memberships: Count
    verified_paths: Count
    unresolved_paths: Count
    complete_reverse_assets: Count
    supported_physical_reverse_assets: Count
    transformer_reverse_assets: Count
    fuse_reverse_assets: Count
    missing_customer_paths: Count
    missing_topology_customer_rows: Count
    arcOS_records: Count
    spatial_candidates: Count
    complete_spatial_candidates: Count
    facility_features: Count
    facility_spatial_proxies: Count
    facility_proxies_with_verified_paths: Count


class PlanEvidence(Contract):
    input_or_rule: str
    classification: EvidenceClass
    detail: str


class RestorationPlan(Contract):
    version: Literal["restoration-plan-v1"] = "restoration-plan-v1"
    result_id: str
    scenario_revision: int
    crew_count: int
    crew_size: int
    use_critical_proxy: bool
    candidates: tuple[PlanCandidate, ...]
    tasks: tuple[PlanTask, ...]
    milestones: tuple[ReleaseMilestone, ...]
    recommended_id: str | None
    unique_dependent_premises: Count | None
    summed_memberships: Count | None
    overlap_memberships: Count | None
    scheduled_release_potential: Count | None
    repair_person_hours: float
    total_person_hours: float | None
    completion_hours: Bounds | None
    display_completion_hours: Bounds | None
    executable_completion_hours: Bounds | None
    coverage: PlanCoverage
    policy: tuple[str, ...]
    evidence: tuple[PlanEvidence, ...]
    limitations: tuple[str, ...]
    actual_efficiency: None = None
    actual_switching_restorable_premises: None = None
    verified_critical_electrical_dependencies: None = None
