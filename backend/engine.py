"""Deterministic domain calculations over a source-verified, reusable context."""
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
import hashlib
import json

from pyproj import Geod

from .config import ASSUMPTIONS, RISK_VERSION, RESTORATION_VERSION, SNAPSHOT, Assumptions, risk_band_for_score
from .contracts import (
    Assumption, Bounds, Change, Comparison, Evaluation, Factor, LaborContribution,
    ModelVersions, RepairStage, RestorationResult, RestorationPriority, RiskResult, Scenario, SourceFacts, WorkItem,
)
from .data import CheckpointError, PreparedContext

RISK_LIMITATIONS = (
    "Uncalibrated ordinal concern rules, not an outage probability or measured predictive accuracy.",
    "Historical damage reports have no verified non-outage controls or reliable event labels.",
    "Transformer mounting is a limited exposure proxy, not a complete assessment of the supply path.",
)
RESTORATION_LIMITATIONS = (
    "AEP labor effort is person-hours. Elapsed time uses an explicit conditional crew envelope; actual efficiency is unknown.",
    "Conditional on declared replacement tasks, available circuit supply, and the assumed serial repair sequence.",
    "Excludes the queue before crew assignment, unknown storm hold, unlisted damage and material shortages.",
    "The ideal-to-single-effective-worker envelope is a prototype policy, not a calibrated interval or a guaranteed duration limit.",
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
        Factor(id="storm-scenario", label="Selected storm concern level", classification="scenario assumption", provenance="simulated_input", value=storm_level,
               contribution_points=storm_level, source_refs=("declared storm scenario; team ordinal scale 0–3",)),
        Factor(id="overhead-transformer", label="Serving transformer mounting", classification="source-derived", provenance="source_fact", value=facts.transformer_mounting,
               contribution_points=overhead, source_refs=("Transformer_Clip.mounting; exact typed ID join",)),
        Factor(id="historical-circuit-damage", label="Historical damage evidence on the verified circuit alias", classification="source-derived", provenance="source_fact",
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
    installation = removal = Decimal(0)
    for work in scenario.work_items:
        if work.node_alias not in assets:
            raise CheckpointError("unknown_repair_node", "A repair task references an asset outside the verified customer path.")
        if work.recipe not in recipes:
            raise CheckpointError("unsupported_recipe", "This repair recipe has no validated labor mapping.")
        recipe = recipes[work.recipe]
        if assets[work.node_alias].token.kind != recipe.asset_kind:
            raise CheckpointError("recipe_asset_mismatch", "The repair recipe does not match the verified equipment type.")
        installation += work.quantity * recipe.install_hours
        removal += work.quantity * recipe.remove_hours
        contributions.append(LaborContribution(task_id=work.task_id, node_alias=work.node_alias, recipe=recipe.id,
            quantity=work.quantity, install_hours_per_unit=float(recipe.install_hours), remove_hours_per_unit=float(recipe.remove_hours),
            direct_labor_hours=float(work.quantity * (recipe.install_hours + recipe.remove_hours)), source_refs=recipe.source_refs))
    direct = installation + removal
    sites = worksite_count(context, scenario.work_items, assumptions.worksite_radius_m)
    access = (context.labor.restricted_access_hours * sites if scenario.access == "restricted" else
              None if scenario.access == "blocked" else Decimal(0))
    repair_person_hours = direct * context.labor.indirect_multiplier
    total = None if access is None else (direct + access) * context.labor.indirect_multiplier
    missing = []
    if not scenario.work_items: missing.append("declared_damage_work_items")
    if scenario.access == "blocked": missing.append("access_clearance_time")
    if scenario.crew_count == 0: missing.append("crew_assignment")
    status = ("insufficient_data" if not scenario.work_items else "pending_clearance" if scenario.access == "blocked" else
              "pending_assignment" if scenario.crew_count == 0 else "available")
    raw = display = None
    if status == "available":
        # No measured productivity is available. This is an explicit conditional
        # envelope: ideal all-person contribution through one effective worker.
        # Tasks remain serial; extra CREWS never divide this path's effort.
        low, high = total / Decimal(scenario.crew_size), total
        raw = Bounds(lower=float(low), upper=float(high))
        step = assumptions.display_step_hours
        display = Bounds(lower=float((low / step).to_integral_value(rounding=ROUND_FLOOR) * step),
                         upper=float((high / step).to_integral_value(rounding=ROUND_CEILING) * step))
    work_by_node = {w.node_alias: w for w in scenario.work_items}
    contributions_by_node = {c.node_alias: c for c in contributions}
    damaged = set(work_by_node)
    asset_impacts = tuple(item for item in context.impact.asset_impacts if item.node_alias in damaged)
    impact_available = (bool(damaged) and len(asset_impacts) == len(damaged) and
                        all(item.status == "verified_reverse_dependency" for item in asset_impacts))
    groups = [(set(path) & damaged, count) for path, count in context.impact.dependency_groups]
    affected = sum(count for required, count in groups if required)
    circuit_count = sum(count for _, count in groups)
    stages, completed, previous, released = [], set(), (), 0
    for asset in reversed(context.assets):
        if asset.alias in work_by_node:
            work = work_by_node[asset.alias]
            completed.add(asset.alias)
            eligible = sum(count for required, count in groups if required and required <= completed)
            stages.append(RepairStage(task_id=work.task_id, node_alias=asset.alias, depends_on_task_ids=previous,
                repair_person_hours=float(Decimal(str(contributions_by_node[asset.alias].direct_labor_hours)) * context.labor.indirect_multiplier),
                newly_eligible_customers=eligible-released if impact_available else None))
            released, previous = eligible, (work.task_id,)
    nearby = (None if any(f.within_primary_extent is None for f in context.impact.facilities)
              else sum(f.within_primary_extent for f in context.impact.facilities))
    facility_context = ("Critical-facility counts within the primary-line extent are unavailable. " if nearby is None else
                        f"{nearby} critical-facility features lie within the verified primary-line extent. ")
    priority = RestorationPriority(circuit_customer_paths=circuit_count,
        dependent_customer_paths=affected if impact_available else None,
        paths_outside_declared_damage=circuit_count-affected if impact_available else None,
        asset_impacts=asset_impacts, facilities=context.impact.facilities,
        recommended_first_task=stages[0].task_id if stages else None,
        reasoning=((f"Dependency-first sequence for {affected} source-matched customer paths through the declared damaged equipment. "
                   f"The first repair could release {stages[0].newly_eligible_customers if stages else 0} paths from this declared damage scope; "
                   "remaining repairs still gate their downstream customers. These are conditional releases, not confirmed restorations or independent competing repair jobs. "
                   "Damage is simulated on source-verified assets; an ARCOS-to-these-assets match and actual sectionalization-restorable count are unavailable.") if impact_available else
                   "A complete reverse dependency join is unavailable for the declared repair scope. Customer impact and potential release counts are withheld; repair order is only an assumed upstream sequence."),
        criticality_action=(facility_context +
                            "Confirm their electrical supply, outage status and backup arrangements before making a dispatch priority decision. "
                            "No facility is assigned to this damaged section by proximity, and no criticality weight or rank is invented."),
        limitations=("Customer counts use distinct source-matched approximate upstream paths, not live outage counts.",
                     "Possible release assumes all other equipment intact, supply available, access cleared and operational authorization.",
                     "A fuse is a potential isolation boundary; actual switching feasibility/state and complete connectivity are unavailable.",
                     "ARCOS-to-selected-asset identity is unavailable. Counts describe simulated damage on exact source assets, not an observed ARCOS outage.",
                     "Paths outside the declared damage need not await these repairs in principle; actual energization cannot be established.",
                     "Facility counts describe a geographic bounding extent, not an outage area. Affected facilities and operational priority remain unavailable."))
    def factor(identifier, label, value, classification, provenance="computed", unit=None, refs=()):
        return Factor(id=identifier, label=label, value=value, classification=classification, provenance=provenance, unit=unit, source_refs=refs)
    factors = (
        factor("replacement-work", "Direct installation plus removal labor", float(direct), "scenario assumption", unit="direct labor hours", refs=tuple(ref for c in contributions for ref in c.source_refs)),
        factor("access-condition", "Declared access condition", scenario.access, "scenario assumption", "simulated_input"),
        factor("restricted-access-work", "Additional direct access labor; unknown when blocked", None if access is None else float(access), "scenario assumption", unit="direct labor hours", refs=(context.labor.access_source,)),
        factor("worksite-count", "Modeled repair worksites", sites, "prototype policy", unit="worksites"),
        factor("indirect-labor-multiplier", "AEP multiplier: includes travel, safety discussions and setup once", float(context.labor.indirect_multiplier), "AEP-specified", "source_fact", "multiplier", (context.labor.multiplier_source,)),
        factor("total-person-hours", "Total labor effort, not elapsed duration", None if total is None else float(total), "prototype policy", unit="person-hours"),
        factor("serial-upstream-dependency", "Serial upstream-first repair stages", len(stages), "prototype policy", unit="stages"),
        factor("crew-capacity", "Available crews; extra crews do not divide serial work", scenario.crew_count, "scenario assumption", "simulated_input", "crews"),
        factor("crew-size", "People in the assigned crew", scenario.crew_size, "scenario assumption", "simulated_input", "people"),
        factor("elapsed-envelope", "Conditional ideal-to-single-effective-worker envelope; actual efficiency unknown", "not calibrated", "prototype policy", "team_rule"),
    )
    return RestorationResult(status=status, raw_hours=raw, display_hours=display, direct_labor_hours=float(direct),
        installation_direct_hours=float(installation), removal_direct_hours=float(removal),
        access_labor_hours=None if access is None else float(access), worksite_count=sites,
        indirect_labor_multiplier=float(context.labor.indirect_multiplier), repair_person_hours=float(repair_person_hours),
        total_person_hours=None if total is None else float(total), priority=priority,
        factors=factors, labor_contributions=tuple(contributions), repair_stages=tuple(stages),
        limitations=RESTORATION_LIMITATIONS, missing_inputs=tuple(missing))


def assumption_records(assumptions: Assumptions) -> tuple[Assumption, ...]:
    rows = (
        ("labor-semantics", "Direct labor times the 4.5 multiplier is total person-hours, not elapsed time.", "person-hours", "AEP-specified"),
        ("workbook-rates", "Installation, removal and access rates come from pinned workbook cells.", "source cells", "source-derived"),
        ("crew-range", "AEP describes a reasonable crew of 2–8 people and leaves assumptions open.", "2–8 people", "AEP-specified"),
        ("crew-default", "Initial four-person crew and one available crew are demo selections, not an AEP staffing rule.", "4 people; 1 crew", "scenario assumption"),
        ("productivity", "Actual skill mix, task parallelizability and person-hour conversion efficiency are not supplied.", None, "unavailable"),
        ("elapsed-envelope", "Serial task effort / selected people to serial task effort / one effective worker; conditional what-if envelope, not an outage-duration bound.", "ideal to single effective worker", "prototype policy"),
        ("rounding", "Outward elapsed-time display rounding step.", float(assumptions.display_step_hours), "prototype policy"),
        ("worksite-grouping", "Group repair points within this distance in meters; apply restricted-access work once per site.", assumptions.worksite_radius_m, "prototype policy"),
        ("scope", "Only the declared replacement quantities are damaged; circuit supply and materials are assumed available.", "simulated", "scenario assumption"),
        ("step-sequence", "Model upstream-first serial repairs; releases require all dependencies in the declared scope to complete.", "conditional release", "prototype policy"),
        ("switching", "Actual switching feasibility, operating state and facility electrical attachment are unknown.", None, "unavailable"),
        ("delays", "Dispatch queue, storm hold and access-clearance duration are unknown and not assigned convenient defaults.", None, "unavailable"),
        ("criticality", "AEP identifies hospitals, fire stations and ambulance locations as priority context; no weights are supplied.", "critical-facility context", "AEP-specified"),
        ("priority-weights", "Operational priority weights and independent competing repair candidates are not verified.", None, "unavailable"),
        ("risk-rule", "Ordinal score = declared storm level + overhead indicator + historical-circuit indicator; LOW 0, MODERATE 1–2, HIGH 3–4, SEVERE 5. Not calibrated probability.", "scenario-risk-v1", "prototype policy"),
        ("damage-identity", "Damage is declared explicitly on the exact GIS/topology-verified fuse and transformer; this is not a verified ARCOS damage match.", "declared on source assets", "scenario assumption"),
        ("arcos-join", "No verified ARCOS equipment ID or pole-to-topology join identifies the selected repairs; observed affected customers remain unavailable.", None, "unavailable"),
        ("reverse-dependencies", "All premise paths containing each declared asset's typed source identity are indexed and checked against customer GIS before a dependent count is exposed.", "exact reverse index", "source-derived"),
        ("access-rate", "Restricted-access direct labor rate is loaded from the pinned workbook; applying it once per modeled site is a separate scenario assumption.", "Labor only work!D2", "source-derived"),
        ("access-scope", "Restricted access requires the workbook access task at each modeled worksite; blocked clearance is unknown.", "one task per site", "scenario assumption"),
        ("alert-rule", "Update previews qualify for an eligible customer when an absolute raw elapsed endpoint change exceeds six hours, or availability changes. Not an AEP threshold.", ">6 elapsed hours or finite/unavailable", "prototype policy"),
        ("official-alert-rule", "Official AEP alert thresholds and escalation rules are not supplied.", None, "unavailable"),
        ("declared-needs", "Optional needs are explicitly selected by the customer; no selection is inferred from GIS, history or AI.", "optional session selections", "user-declared"),
    )
    return tuple(Assumption(id=i, description=d, value=v, classification=c) for i, d, v, c in rows)


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


def compare_scenarios(before: Evaluation, after: Evaluation) -> Comparison:
    """Explain only supported access/people changes; reject other causal confounders."""
    a = before.simulated_inputs.model_dump(exclude={"access", "crew_size", "scenario_revision"})
    b = after.simulated_inputs.model_dump(exclude={"access", "crew_size", "scenario_revision"})
    x, y = before.restoration, after.restoration
    if (a != b or before.location != after.location or before.data_snapshot != after.data_snapshot or
            before.source_facts != after.source_facts or before.model_versions != after.model_versions or before.assumptions != after.assumptions or
            before.risk != after.risk or x.labor_contributions != y.labor_contributions or
            x.indirect_labor_multiplier != y.indirect_labor_multiplier or x.worksite_count != y.worksite_count or
            x.repair_stages != y.repair_stages or x.priority != y.priority):
        raise CheckpointError("not_scenario_only", "A comparison requires identical non-access/non-crew-size inputs, data and assumptions.")
    changed = tuple(field for field in ("access", "crew_size") if getattr(before.simulated_inputs, field) != getattr(after.simulated_inputs, field))
    causes = ("access-condition", "restricted-access-work", "worksite-count", "indirect-labor-multiplier", "crew-size", "elapsed-envelope")
    changes = [Change(field=f"simulated_inputs.{field}", before=getattr(before.simulated_inputs,field), after=getattr(after.simulated_inputs,field), cause_factor_ids=("access-condition" if field=="access" else "crew-size",)) for field in changed]
    changes.append(Change(field="restoration.status", before=x.status, after=y.status, cause_factor_ids=causes))
    for field, unit in (("access_labor_hours", "direct labor hours"), ("total_person_hours", "person-hours")):
        old, new = getattr(x, field), getattr(y, field)
        changes.append(Change(field=f"restoration.{field}", before=old, after=new,
            delta=None if old is None or new is None else round(new-old,12), unit=unit, cause_factor_ids=causes))
    for endpoint in ("lower", "upper"):
        old = None if x.raw_hours is None else getattr(x.raw_hours, endpoint)
        new = None if y.raw_hours is None else getattr(y.raw_hours, endpoint)
        changes.append(Change(field=f"restoration.raw_hours.{endpoint}", before=old, after=new,
            delta=None if old is None or new is None else round(new-old,12), unit="elapsed hours", cause_factor_ids=causes))
    if y.status == "pending_clearance":
        explanation = "Access is blocked. Clearance time is unknown, so the finite restoration range is withdrawn. Crew size cannot resolve unknown clearance. Risk is unchanged."
    elif y.raw_hours is not None:
        parts = []
        if "access" in changed:
            parts.append(f"Access changed from {before.simulated_inputs.access} to {after.simulated_inputs.access} across {y.worksite_count} modeled worksites.")
            if x.total_person_hours is not None:
                parts.append(f"Total labor effort changes from {x.total_person_hours:g} to {y.total_person_hours:g} person-hours after one {y.indirect_labor_multiplier:g} multiplier.")
            else:
                parts.append(f"Clearance no longer blocks the declared scope; total effort is {y.total_person_hours:g} person-hours.")
        if "crew_size" in changed:
            parts.append(f"Crew size changed from {before.simulated_inputs.crew_size} to {after.simulated_inputs.crew_size} people. Repair effort remains {y.repair_person_hours:g} person-hours; people change the ideal-duration boundary, not the damage or serial dependencies.")
        if not changed: parts.append("Access and crew size are unchanged; the restoration outlook is unchanged.")
        parts.append(f"The conditional outlook is {y.display_hours.lower:g}–{y.display_hours.upper:g} elapsed hours. Actual crew efficiency is unknown; the single-effective-worker boundary is a scenario, not a guaranteed completion limit. Risk is unchanged.")
        explanation = " ".join(parts)
    else:
        explanation = "No finite restoration range is available: " + ", ".join(y.missing_inputs) + ". Risk is unchanged."
    return Comparison(before_result_id=before.result_id, after_result_id=after.result_id,
        changed_inputs=changed, changes=tuple(changes), explanation=explanation)


def compare_access(before: Evaluation, after: Evaluation) -> Comparison:
    """Narrow access-only caller compatibility; never attribute a crew change to access."""
    if before.simulated_inputs.crew_size != after.simulated_inputs.crew_size:
        raise CheckpointError("not_access_only", "An access-only comparison requires identical non-access inputs.")
    try:
        return compare_scenarios(before, after)
    except CheckpointError as error:
        raise CheckpointError("not_access_only", "An access-only comparison requires identical non-access inputs, data and assumptions.") from error
