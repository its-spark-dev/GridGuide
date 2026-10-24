"""Deterministic domain calculations over a source-verified, reusable context."""
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
import hashlib
import json

from pyproj import Geod

from .config import ASSUMPTIONS, RISK_VERSION, RESTORATION_VERSION, SNAPSHOT, Assumptions, risk_band_for_score
from .contracts import (
    Assumption, Bounds, Change, Comparison, Evaluation, Factor, LaborContribution,
    ModelVersions, RepairStage, RestorationResult, RiskResult, Scenario, SourceFacts, WorkItem,
)
from .data import CheckpointError, PreparedContext

RISK_LIMITATIONS = (
    "Uncalibrated ordinal concern rules, not an outage probability or measured predictive accuracy.",
    "Historical damage reports have no verified non-outage controls or reliable event labels.",
    "Transformer mounting is a limited exposure proxy, not a complete assessment of the supply path.",
)
RESTORATION_LIMITATIONS = (
    "Workbook hour basis is unspecified; elapsed hours use a provisional reference-crew conversion.",
    "Conditional on declared replacement tasks, available circuit supply, and the assumed serial repair sequence.",
    "Excludes the queue before crew assignment, unknown storm hold, unlisted damage and material shortages.",
    "The upper allowance is a team scenario assumption, not a calibrated confidence interval or guarantee.",
    "Not an AEP restoration estimate or confirmation that power is available.",
)


def default_scenario(context: PreparedContext, *, access="clear", **changes) -> Scenario:
    """Quantities/damage are declared simulations; node aliases come from the real trace."""
    by_kind = {a.token.kind: a.alias for a in context.assets}
    items = (
        WorkItem(task_id="fuse-task", node_alias=by_kind["Fuse"], recipe="fuse-cutout-replace", quantity=1),
        WorkItem(task_id="transformer-task", node_alias=by_kind["Distribution"], recipe="transformer-100kva-replace", quantity=1),
    )
    return Scenario.model_validate({"location_alias": context.location.alias, "access": access, "work_items": items, **changes})


def calculate_risk(facts: SourceFacts, storm_level: int | None) -> RiskResult:
    if storm_level is not None and (type(storm_level) is not int or not 0 <= storm_level <= 3):
        raise CheckpointError("invalid_storm_level", "Storm level must be an integer from zero to three, or unknown.")
    missing = []
    if storm_level is None:
        missing.append("storm_level")
    if facts.transformer_mounting == "Unknown":
        missing.append("transformer_mounting")
    if facts.historical_circuit_evidence is None:
        missing.append("verified_historical_circuit_context")
    overhead = None if facts.transformer_mounting == "Unknown" else int(facts.transformer_mounting == "Overhead")
    historical = None if facts.historical_circuit_evidence is None else int(facts.historical_circuit_evidence)
    factors = (
        Factor(id="storm-scenario", label="Selected storm concern level", provenance="simulated_input", value=storm_level,
               contribution_points=storm_level, source_refs=("declared storm scenario; team ordinal scale 0–3",)),
        Factor(id="overhead-transformer", label="Serving transformer mounting", provenance="source_fact", value=facts.transformer_mounting,
               contribution_points=overhead, source_refs=("Transformer_Clip.mounting; exact typed ID join",)),
        Factor(id="historical-circuit-damage", label="Historical damage evidence on the verified circuit alias", provenance="source_fact",
               value=facts.historical_circuit_evidence, contribution_points=historical,
               source_refs=("arcos_prod_damage_09_28_Clip.Circuit and Report_Tim; unambiguous GIS crosswalk",)),
    )
    limitations = RISK_LIMITATIONS
    if facts.historical_circuit_evidence is False:
        limitations += ("No records found in this extract does not mean the circuit has never had damage; coverage is unknown.",)
    score = None if missing else storm_level + overhead + historical
    return RiskResult(status="insufficient_data" if missing else "available", score=score,
        band=None if score is None else risk_band_for_score(score), factors=factors,
        limitations=limitations, missing_inputs=tuple(missing))


def worksite_count(context: PreparedContext, work_items: tuple[WorkItem, ...], radius_m: float) -> int:
    """Complete-link distance grouping for the supported repair nodes; not an asset join."""
    points = {a.alias: a.point for a in context.assets}
    groups: list[list[tuple[float, float]]] = []
    geod = Geod(ellps="WGS84")
    for alias in sorted(w.node_alias for w in work_items):
        point = points[alias]
        if point is None:
            raise CheckpointError("missing_worksite_geometry", "A repair worksite lacks verified geometry.")
        for group in groups:
            if all(geod.inv(*point, *other)[2] <= radius_m for other in group):
                group.append(point)
                break
        else:
            groups.append([point])
    return len(groups)


def calculate_restoration(context: PreparedContext, scenario: Scenario, assumptions: Assumptions) -> RestorationResult:
    assets = {a.alias: a for a in context.assets}
    recipes = {r.id: r for r in context.labor.recipes}
    contributions = []
    direct = Decimal(0)
    # Validate all tasks before considering blocked/no-crew states.
    for work in scenario.work_items:
        if work.node_alias not in assets:
            raise CheckpointError("unknown_repair_node", "A repair task references an asset outside the verified customer path.")
        if work.recipe not in recipes:
            raise CheckpointError("unsupported_recipe", "This repair recipe has no validated checkpoint labor mapping.")
        recipe = recipes[work.recipe]
        if assets[work.node_alias].token.kind != recipe.asset_kind:
            raise CheckpointError("recipe_asset_mismatch", "The repair recipe does not match the verified equipment type.")
        effort = work.quantity * (recipe.install_hours + recipe.remove_hours)
        direct += effort
        contributions.append(LaborContribution(task_id=work.task_id, node_alias=work.node_alias, recipe=recipe.id,
            quantity=work.quantity, install_hours_per_unit=float(recipe.install_hours), remove_hours_per_unit=float(recipe.remove_hours),
            direct_labor_hours=float(effort), source_refs=recipe.source_refs))

    sites = worksite_count(context, scenario.work_items, assumptions.worksite_radius_m)
    access = (context.labor.restricted_access_hours * sites if scenario.access == "restricted" else
              None if scenario.access == "blocked" else Decimal(0))
    nominal = None if access is None else (direct + access) * context.labor.indirect_multiplier * assumptions.reference_crew_hours_per_labor_hour
    missing = []
    if not scenario.work_items:
        missing.append("declared_damage_work_items")
    if scenario.access == "blocked":
        missing.append("access_clearance_time")
    if scenario.crew_count == 0:
        missing.append("crew_assignment")
    status = ("insufficient_data" if not scenario.work_items else "pending_clearance" if scenario.access == "blocked" else
              "pending_assignment" if scenario.crew_count == 0 else "available")
    raw = display = None
    if status == "available":
        high = nominal * assumptions.upper_scope_multiplier
        raw = Bounds(lower=float(nominal), upper=float(high))
        display = Bounds(lower=int(nominal.to_integral_value(rounding=ROUND_FLOOR)), upper=int(high.to_integral_value(rounding=ROUND_CEILING)))

    work_by_node = {w.node_alias: w for w in scenario.work_items}
    stages = []
    previous = ()
    for asset in reversed(context.assets):
        if asset.alias in work_by_node:
            work = work_by_node[asset.alias]
            stages.append(RepairStage(task_id=work.task_id, node_alias=asset.alias, depends_on_task_ids=previous))
            previous = (work.task_id,)
    factors = (
        Factor(id="replacement-work", label="Direct replacement labor for declared quantities", value=float(direct), unit="source_labor_hours",
               provenance="computed", source_refs=tuple(ref for c in contributions for ref in c.source_refs)),
        Factor(id="access-condition", label="Declared access condition", value=scenario.access, provenance="simulated_input"),
        Factor(id="restricted-access-work", label="Additional access labor; unknown when blocked", value=None if access is None else float(access),
               unit="source_labor_hours", provenance="computed", source_refs=(context.labor.access_source, "A2-worksite-access-adder")),
        Factor(id="worksite-count", label="Distinct modeled repair worksites", value=sites, unit="worksites", provenance="computed",
               source_refs=("verified asset geometry; A2-worksite-access-adder",)),
        Factor(id="indirect-labor-multiplier", label="Travel, setup and other indirect work included once", value=float(context.labor.indirect_multiplier),
               unit="multiplier", provenance="source_fact", source_refs=(context.labor.multiplier_source,)),
        Factor(id="serial-upstream-dependency", label="Upstream tasks must complete before downstream restoration stages", value=len(stages),
               unit="ordered_repair_stages", provenance="computed", source_refs=("matched_upstream.txt; assumed serial repair sequencing",)),
        Factor(id="crew-capacity", label="Additional crews cannot shorten this serial path", value=scenario.crew_count,
               unit="available_reference_crews", provenance="simulated_input"),
        Factor(id="upper-scope-allowance", label="Illustrative upper scope allowance, not statistical confidence", value=float(assumptions.upper_scope_multiplier),
               unit="multiplier", provenance="team_rule", source_refs=("A3-upper-scope-allowance",)),
    )
    return RestorationResult(status=status, raw_hours=raw, display_hours=display, direct_labor_hours=float(direct),
        access_labor_hours=None if access is None else float(access), worksite_count=sites,
        indirect_labor_multiplier=float(context.labor.indirect_multiplier), modeled_effort_hours=None if nominal is None else float(nominal),
        factors=factors, labor_contributions=tuple(contributions), repair_stages=tuple(stages),
        limitations=RESTORATION_LIMITATIONS, missing_inputs=tuple(missing))


def assumption_records(assumptions: Assumptions) -> tuple[Assumption, ...]:
    return (
        Assumption(id="A1-reference-crew-unit", description="Provisional reference-crew hours per workbook labor hour; source unit basis is not confirmed.",
                   value=float(assumptions.reference_crew_hours_per_labor_hour)),
        Assumption(id="A2-worksite-access-adder", description="Apply restricted-access labor once per modeled worksite; group repair points within this distance.",
                   value=assumptions.worksite_radius_m),
        Assumption(id="A3-upper-scope-allowance", description="Upper duration multiplier is a team scenario allowance, not a fitted statistical interval.",
                   value=float(assumptions.upper_scope_multiplier)),
        Assumption(id="supply-available", description="Circuit supply is assumed available in the scenario; it is not observed live.", value="simulated"),
        Assumption(id="listed-damage-only", description="Only the declared component quantities require replacement; other units are assumed intact.", value="simulated"),
        Assumption(id="serial-repair-sequencing", description="Conservative upstream-first serial repair stages; no parallel crew acceleration.", value="team_model"),
    )


def evaluate(context: PreparedContext, scenario: Scenario, assumptions: Assumptions = ASSUMPTIONS) -> Evaluation:
    # Also validate copies constructed by callers using Pydantic's unchecked model_copy.
    scenario = Scenario.model_validate(scenario.model_dump())
    if scenario.location_alias != context.location.alias:
        raise CheckpointError("unsupported_location", "Scenario location does not match the verified prepared context.")
    risk = calculate_risk(context.facts, scenario.storm_level)
    restoration = calculate_restoration(context, scenario, assumptions)
    versions = ModelVersions(risk=RISK_VERSION, restoration=RESTORATION_VERSION, assumptions=assumptions.version)
    data = dict(scenario_revision=scenario.scenario_revision, data_snapshot=SNAPSHOT, model_versions=versions,
        location=context.location, source_facts=context.facts, simulated_inputs=scenario, risk=risk, restoration=restoration,
        assumptions=assumption_records(assumptions), limitations=(
            "Only one source-verified customer is supported; do not extrapolate coverage to the full network.",
            "No current utility outage or restoration information is connected.",
            "Damage, storm conditions and access are declared simulations, not live observations.",))
    provisional = Evaluation(result_id="pending", **data)
    signature = {"public_result": provisional.model_dump(mode="json"), "source_hashes": dict(context.source_hashes)}
    digest = hashlib.sha256(json.dumps(signature, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return Evaluation(result_id=f"{scenario.location_alias}:{digest}", **data)


def compare_access(before: Evaluation, after: Evaluation) -> Comparison:
    """Only claim access causality when every other scenario/model/source input is fixed."""
    a = before.simulated_inputs.model_dump(exclude={"access", "scenario_revision"})
    b = after.simulated_inputs.model_dump(exclude={"access", "scenario_revision"})
    x, y = before.restoration, after.restoration
    if (a != b or before.location != after.location or before.data_snapshot != after.data_snapshot or
            before.source_facts != after.source_facts or before.model_versions != after.model_versions or before.assumptions != after.assumptions or
            before.risk != after.risk or x.labor_contributions != y.labor_contributions or
            x.indirect_labor_multiplier != y.indirect_labor_multiplier or x.worksite_count != y.worksite_count or
            x.repair_stages != y.repair_stages):
        raise CheckpointError("not_access_only", "An access-only comparison requires identical non-access inputs, data and assumptions.")
    causes = ("access-condition", "restricted-access-work", "worksite-count", "indirect-labor-multiplier")
    changes = [Change(field="simulated_inputs.access", before=before.simulated_inputs.access, after=after.simulated_inputs.access, cause_factor_ids=("access-condition",))]
    changes.append(Change(field="restoration.status", before=x.status, after=y.status, cause_factor_ids=("access-condition",)))
    changes.append(Change(field="restoration.access_labor_hours", before=x.access_labor_hours, after=y.access_labor_hours,
        delta=None if x.access_labor_hours is None or y.access_labor_hours is None else round(y.access_labor_hours-x.access_labor_hours, 12),
        unit="source_labor_hours", cause_factor_ids=("access-condition", "restricted-access-work", "worksite-count")))
    for endpoint in ("lower", "upper"):
        old = None if x.raw_hours is None else getattr(x.raw_hours, endpoint)
        new = None if y.raw_hours is None else getattr(y.raw_hours, endpoint)
        changes.append(Change(field=f"restoration.raw_hours.{endpoint}", before=old, after=new,
            delta=None if old is None or new is None else round(new-old, 12), unit="hours", cause_factor_ids=causes))
    if x.raw_hours is not None and y.raw_hours is not None:
        extra_labor = round(y.access_labor_hours - x.access_labor_hours, 12)
        lower_delta = round(y.raw_hours.lower-x.raw_hours.lower, 12)
        upper_delta = round(y.raw_hours.upper-x.raw_hours.upper, 12)
        explanation = (f"Access changed from {before.simulated_inputs.access} to {after.simulated_inputs.access}. "
            f"Access labor changed by {extra_labor:g} source labor hours across {y.worksite_count} modeled worksites. "
            f"After the {y.indirect_labor_multiplier:g} indirect-work multiplier and the disclosed unit/scope assumptions, "
            f"the raw lower bound changed by {lower_delta:g} hours and the upper bound by {upper_delta:g} hours. "
            "Risk is unchanged because access is not a risk-band input.")
    elif y.status == "pending_clearance":
        explanation = "Access is blocked. Clearance time is unknown, so the finite restoration range is withdrawn. Risk is unchanged."
    elif y.raw_hours is not None:
        explanation = "Access no longer blocks the declared repairs. A conditional finite range is available under the same assumptions. Risk is unchanged."
    else:
        explanation = "No finite restoration range is available: " + ", ".join(y.missing_inputs) + ". Risk is unchanged."
    return Comparison(before_result_id=before.result_id, after_result_id=after.result_id, changes=tuple(changes), explanation=explanation)
