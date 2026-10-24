"""Bounded source-backed repair comparison. All public claims are server-owned."""
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR, ROUND_CEILING
from functools import lru_cache
import hashlib
import json
from pathlib import Path

from .config import RAW
from .contracts import (Bounds, CriticalProxyContext, ImpactCell, MapPoint, PlanCandidate,
    PlanCoverage, PlanEvidence, PlanRequest, PlanTask, ReleaseMilestone, RestorationPlan)
from .criticality import FacilityProxy, prepare_facility_proxies
from .damage import DamageAudit, DamageMatch, prepare_damage_audit
from .data import CheckpointError, LaborReference, NodeKey, read_labor
from .network import NetworkIndex, prepare_network, public_asset_alias

POLICY = (
    "Exclude blocked work and work with incomplete evidence. Defer its dependent tasks.",
    "Respect source ancestry using a conservative upstream-first repair policy. This is not proof that physical repair must be serial.",
    "When enabled, prioritize a supported critical-premise spatial proxy (including its prerequisites). This is a prototype preference, not an AEP weight.",
    "Among ready tasks, maximize marginal dependency-release potential per total person-hour including access; then prefer more release, less effort and stable alias.",
    "Assign the next ready task to the crew with the earliest conservative finish; a task cannot start before its prerequisites finish. Separate crews may work on independent branches.",
)
LIMITS = (
    "Historical ARCOS replay and declared damage are scenario inputs, not confirmed current outages or historical outage customer counts.",
    "A spatial damage association is a disclosed hypothesis, not an exact ARCOS asset identifier. Topology dependency is independently verified from all matching premise paths.",
    "Facility proximity is spatial criticality context; the facility's electrical service connection is unavailable.",
    "Dependency release assumes all selected required repairs complete, other equipment intact, supply available, access cleared and operational authorization. It does not confirm energization.",
    "Actual isolation/switching feasibility, switch state, alternate feed, protection, capacity, dispatch travel differences and clearance duration are unavailable. Switching-restorable counts remain null.",
    "Actual productivity and default crew composition are unavailable. Time spans ideal crew contribution to one effective worker per crew; it is not a confidence interval, guaranteed bound or official AEP ETR.",
    "The four-candidate comparison is curated; it is not an optimized system-wide dispatch plan. No operational prioritization weights are supplied by AEP.",
)
EVIDENCE = tuple(PlanEvidence(input_or_rule=name, classification=kind, detail=detail) for name, kind, detail in (
    ("labor semantics", "AEP-specified", "Direct labor multiplied by 4.5 once gives total person-hours including travel/setup."),
    ("crew size bounds", "AEP-specified", "The supplied guide allows reasonable crew assumptions of two through eight people; it does not prescribe four people or a crew composition."),
    ("spatial relationship allowance", "AEP-specified", "User-supplied guide excerpts permit reasonable nearest-pole and critical-location/premise spatial relationships; they supply no radius or positional accuracy guarantee."),
    ("topology and workbook rates", "source-derived", "Exact typed GIS IDs, complete premise paths, vetted circuit/station crosswalks and pinned workbook cells."),
    ("historical damage evidence", "source-derived", "ARCOS report and geometry are historical; no direct pole/equipment identifier was established."),
    ("damage match gates", "prototype policy", "Same type/circuit/station, nearest device and nearest pole each within 25 m with at least 10 m runner-up gap, then unique pole location-label bridge and typed topology identity."),
    ("facility match gates", "prototype policy", "Nearest premise within 50 m with at least 10 m runner-up gap, followed by complete premise-path validation; never a verified service connection."),
    ("replacement scope", "scenario assumption", "One fuse cutout per selected fuse-bank candidate and one 100 kVA transformer replacement. Source data does not establish damaged unit quantity."),
    ("historical replay and declared damage", "scenario assumption", "Treat the selected historical association and three declared source assets as simultaneous repairs for comparison."),
    ("access and staffing", "scenario assumption", "Default clear access, one available crew, four people per crew; users may select one/two crews and two through eight people."),
    ("crew capability and time origin", "scenario assumption", "Selected crews are available at the common modeled response start and assumed qualified/interchangeable for these tasks. Actual dispatch, composition and site-to-site travel differences are unavailable."),
    ("metric geometry", "source-derived", "Distances use source CRS transformed into EPSG:32617; coordinate accuracy is not supplied."),
    ("restricted access work", "scenario assumption", "Apply the workbook's 0.5 direct-hour access task once at each separate selected repair worksite; blocked duration stays unknown."),
    ("ranking and serial ancestry", "prototype policy", "Transparent lexicographic policy, optional spatial criticality preference, conservative upstream-before-downstream scheduling."),
    ("elapsed conversion", "prototype policy", "Per task, total person-hours / people through total person-hours / one effective worker; propagate crew and dependency constraints. No extra travel adder."),
    ("time display", "prototype policy", "Planning timelines round outward to quarter hours; exact internal envelopes remain available. Existing customer outlook retains its half-hour display policy."),
    ("privacy", "prototype policy", "Opaque asset aliases and 0.01-degree generalized cells; no raw customer/facility identifiers or precise positions in public/AI payloads."),
    ("individual needs", "user-declared", "Optional customer declarations remain separate; they do not alter this infrastructure plan and are not sent to the provider."),
    ("operational unknowns", "unavailable", "Actual productivity, crew composition, switching feasibility, dispatch availability, clearance duration, alert thresholds and AEP priority weights."),
))


@dataclass(frozen=True)
class Candidate:
    key: NodeKey
    label: str
    recipe: str
    match: DamageMatch | None = None


@dataclass(frozen=True)
class PlanningContext:
    network: NetworkIndex
    damage: DamageAudit
    proxies: tuple[FacilityProxy, ...]
    labor: LaborReference
    candidates: tuple[Candidate, ...]
    coverage: PlanCoverage


@lru_cache(maxsize=2)
def prepare_planning(raw: Path = RAW) -> PlanningContext:
    network = prepare_network(raw)
    damage = prepare_damage_audit(raw, network.topology)
    proxies = prepare_facility_proxies(network, raw)
    specs = (
        ("Fuse_Bank_Clip", 6096, "Golden upstream fuse", "fuse-cutout-replace", None),
        ("Transformer_Clip", 24215, "Golden transformer", "transformer-100kva-replace", None),
        ("Fuse_Bank_Clip", 6271, "Historical fuse replay", "fuse-cutout-replace", damage.for_row(933)),
        ("Fuse_Bank_Clip", 2557, "Critical-context fuse", "fuse-cutout-replace", None),
    )
    candidates = []
    for layer, row, label, recipe, match in specs:
        key = network.key_for_locator(layer, row)
        if key is None:
            raise CheckpointError("planning_source_unavailable", "A curated repair asset could not be resolved uniquely.")
        asset = network.equipment_by_key[key]
        if recipe == "transformer-100kva-replace" and (not any(asset.phase_specs) or any(x != "100 kVA XFR PL" for x in asset.phase_specs if x)):
            raise CheckpointError("planning_recipe_unavailable", "Transformer rating no longer supports this replacement recipe.")
        candidates.append(Candidate(key, label, recipe, match))
    c = network.coverage
    coverage = PlanCoverage(indexed_paths=c['topology_paths'], indexed_assets=c['topology_assets'], indexed_memberships=c['topology_memberships'],
        verified_paths=c['fully_verified_paths'], unresolved_paths=c['topology_paths'] - c['fully_verified_paths'],
        complete_reverse_assets=c['fully_verified_reverse_assets'],
        supported_physical_reverse_assets=sum(c['by_kind'][k]['fully_verified_reverse_assets'] for k in ('Distribution', 'Fuse')),
        transformer_reverse_assets=c['by_kind']['Distribution']['fully_verified_reverse_assets'], fuse_reverse_assets=c['by_kind']['Fuse']['fully_verified_reverse_assets'],
        missing_customer_paths=c['topology_paths_missing_customers'], missing_topology_customer_rows=c['customer_rows_missing_paths'],
        arcOS_records=len(damage.matches), spatial_candidates=sum(m.status == 'spatial_candidate' for m in damage.matches),
        complete_spatial_candidates=sum(m.status == 'spatial_candidate' and network.dependents(m.asset_key) is not None for m in damage.matches),
        facility_features=len(proxies), facility_spatial_proxies=sum(p.status == 'spatial_proxy' for p in proxies),
        facility_proxies_with_verified_paths=sum(p.path_validated is True for p in proxies))
    return PlanningContext(network, damage, proxies, read_labor(raw), tuple(candidates), coverage)


def _bounds(lower, upper):
    return Bounds(lower=float(lower), upper=float(upper))


def _display(bounds):
    if bounds is None:
        return None
    step = Decimal('.25')
    return _bounds((Decimal(str(bounds.lower)) / step).to_integral_value(rounding=ROUND_FLOOR) * step,
                   (Decimal(str(bounds.upper)) / step).to_integral_value(rounding=ROUND_CEILING) * step)


def _position(point):
    return MapPoint(longitude=round(point[0], 2), latitude=round(point[1], 2))


def make_plan(context: PlanningContext, request: PlanRequest) -> RestorationPlan:
    network = context.network
    candidates = {public_asset_alias(c.key): c for c in context.candidates}
    access = {a.candidate_id: a.access for a in request.access}
    if set(access) - set(candidates):
        raise CheckpointError("unknown_candidate", "Choose a candidate from the current prepared comparison.")
    recipes = {r.id: r for r in context.labor.recipes}
    keys = frozenset(c.key for c in candidates.values())
    members = {i: network.dependents(c.key) if c.match is None or (c.match.status == 'spatial_candidate' and c.match.asset_key == c.key) else None for i, c in candidates.items()}
    # Never silently shrink the declared damage union if an identity/path is unavailable.
    complete = all(m is not None for m in members.values())
    union = network.affected_union(keys) if complete else None
    deps_by_key = network.upstream_damaged_dependencies(keys) if complete else None
    deps = {i: {public_asset_alias(k) for k in deps_by_key[c.key]} if deps_by_key else set() for i,c in candidates.items()}
    critical = {i: tuple(p for p in context.proxies if p.status == 'spatial_proxy' and p.path_validated and p.premise in (members[i] or ())) for i in candidates}
    direct, repair, total, access_hours = {}, {}, {}, {}
    for i, c in candidates.items():
        recipe = recipes[c.recipe]
        direct[i] = recipe.install_hours + recipe.remove_hours
        repair[i] = direct[i] * context.labor.indirect_multiplier
        state = access.get(i, 'clear')
        access_hours[i] = None if state == 'blocked' else context.labor.restricted_access_hours if state == 'restricted' else Decimal(0)
        total[i] = None if access_hours[i] is None else (direct[i] + access_hours[i]) * context.labor.indirect_multiplier
    status = {i: 'evidence_unavailable' if not complete else 'blocked' if total[i] is None else 'scheduled' for i in candidates}
    # All ancestry is explicit. Blocked parents propagate even if later in catalog.
    for i in candidates:
        if status[i] == 'scheduled' and any(status[j] != 'scheduled' for j in deps[i]):
            status[i] = 'dependency_blocked'
    remaining = {i for i in candidates if status[i] == 'scheduled'}
    ordered, tasks, potential, reasons, finishes = [], [], {}, {}, {}
    availability = [(Decimal(0), Decimal(0)) for _ in range(request.crew_count)]
    completed_keys = set()
    released = frozenset()
    while remaining:
        ready = [i for i in remaining if deps[i] <= set(ordered)]
        if not ready:
            raise CheckpointError("planning_dependency_cycle", "No valid conservative repair sequence is available.")
        def marginal(i):
            return len(network.released_premises(keys, completed_keys | {candidates[i].key}) - released)
        def has_critical(i):
            return bool(critical[i] or any(critical[j] and i in deps[j] for j in candidates))
        def rank(i):
            n = marginal(i)
            return (-int(request.use_critical_proxy and has_critical(i)), -Decimal(n) / total[i], -n, total[i], i)
        i = min(ready, key=rank)
        n = marginal(i)
        potential[i] = n
        reasons[i] = ("Supported critical-premise spatial proxy takes precedence under the enabled prototype policy. "
                      if request.use_critical_proxy and has_critical(i) else "Highest marginal dependency release per total person-hour among ready comparable candidates. ")
        reasons[i] += f"{n} additional {'premise' if n == 1 else 'premises'} potentially released for {float(total[i]):g} total person-hours."
        if deps[i]:
            reasons[i] += " Starts after its selected upstream repair under conservative ancestry ordering."
        crew = min(range(request.crew_count), key=lambda j: (availability[j][1], j))
        low = max([availability[crew][0], *(finishes[j][0] for j in deps[i])])
        high = max([availability[crew][1], *(finishes[j][1] for j in deps[i])])
        finish = (low + total[i] / request.crew_size, high + total[i])
        availability[crew] = finishes[i] = finish
        tasks.append(PlanTask(candidate_id=i, crew=crew+1, start_hours=_bounds(low,high), finish_hours=_bounds(*finish), display_finish_hours=_display(_bounds(*finish))))
        ordered.append(i)
        remaining.remove(i)
        completed_keys.add(candidates[i].key)
        released = network.released_premises(keys, completed_keys)
    # Group simultaneous scenario completions. Conservative endpoint ordering is
    # explicit; no assertion that uncertain real completion windows cannot overlap.
    milestones, finished, prior = [], set(), frozenset()
    grouped = {}
    for task in tasks:
        grouped.setdefault((task.finish_hours.lower, task.finish_hours.upper), []).append(task.candidate_id)
    for (low,high), ids in sorted(grouped.items(), key=lambda entry: (entry[0][1],entry[0][0])):
        finished.update(candidates[i].key for i in ids)
        now = network.released_premises(keys, finished)
        milestones.append(ReleaseMilestone(candidate_ids=tuple(ids), elapsed_hours=_bounds(low,high), display_hours=_display(_bounds(low,high)),
            additional_premises=len(now-prior), cumulative_premises=len(now)))
        prior = now
    outputs = []
    for i,c in candidates.items():
        asset = network.equipment_by_key[c.key]
        m = members[i]
        others = set().union(*(v for j,v in members.items() if j != i and v is not None))
        cells = Counter((round(network.customers_by_premise[p][0].point[0],2),round(network.customers_by_premise[p][0].point[1],2)) for p in m or ())
        proxies = tuple(CriticalProxyContext(kind=p.kind, distance_m=round(p.nearest_distance_m,1), runner_up_distance_m=round(p.runner_up_distance_m,1)) for p in critical[i])
        match = c.match
        outputs.append(PlanCandidate(id=i,label=c.label,kind=asset.kind,
            damage_source='historical ARCOS replay' if match else 'declared damage scenario',
            match_method='Same-type/circuit/station device proximity + nearest-pole location bridge + typed topology identity' if match else 'Declared damage on an exact typed source topology asset',
            match_distance_m=round(match.distance_m,1) if match and match.distance_m is not None else None,
            pole_distance_m=round(match.pole_distance_m,1) if match and match.pole_distance_m is not None else None,
            runner_up_distance_m=round(match.runner_up_distance_m,1) if match and match.runner_up_distance_m is not None else None,
            evidence_note=('Damage association or complete premise membership evidence is unavailable; no complete impact is claimed.' if m is None else 'Historical spatial association, not direct identity or a current outage. All dependent paths independently validated.' if match else 'Source asset and all dependent paths verified; damage and replacement quantity are declared.'),
            dependent_premises=len(m) if m is not None else None, overlap_premises=len(m & others) if m is not None and complete else None,
            prerequisite_ids=tuple(sorted(deps[i])), direct_labor_hours=float(direct[i]),repair_person_hours=float(repair[i]), access=access.get(i,'clear'),
            access_direct_hours=None if access_hours[i] is None else float(access_hours[i]), total_person_hours=None if total[i] is None else float(total[i]),
            elapsed_hours=_bounds(total[i]/request.crew_size,total[i]) if total[i] is not None and status[i]=='scheduled' else None,
            potential_release_at_stage=potential.get(i), release_per_total_person_hour=float(Decimal(potential[i])/total[i]) if i in potential else None,
            critical_proxies=proxies,status=status[i],priority_rank=ordered.index(i)+1 if i in ordered else None,
            reason=reasons.get(i, 'Clearance duration is unknown; work is excluded.' if status[i]=='blocked' else 'An upstream selected repair is blocked; this task is deferred.' if status[i]=='dependency_blocked' else 'Complete damage identity and customer membership evidence is required; impact and scheduling are withheld.'),
            position=_position(asset.point),customer_cells=tuple(ImpactCell(position=_position(p),premises=n) for p,n in sorted(cells.items()))))
    executable = _bounds(max(a[0] for a in availability),max(a[1] for a in availability)) if tasks else None
    completion = executable if len(tasks)==len(candidates) else None
    payload = dict(scenario_revision=request.scenario_revision,crew_count=request.crew_count,crew_size=request.crew_size,use_critical_proxy=request.use_critical_proxy,
        candidates=tuple(outputs),tasks=tuple(tasks),milestones=tuple(milestones),recommended_id=ordered[0] if ordered else None,
        unique_dependent_premises=len(union) if union is not None else None,
        summed_memberships=sum(len(m) for m in members.values()) if complete else None,
        overlap_memberships=sum(len(m) for m in members.values())-len(union) if complete else None,
        scheduled_release_potential=len(released) if complete else None,repair_person_hours=float(sum(repair.values())),
        total_person_hours=float(sum(total.values())) if all(t is not None for t in total.values()) else None,
        completion_hours=completion,display_completion_hours=_display(completion),executable_completion_hours=executable,
        coverage=context.coverage,policy=POLICY,evidence=EVIDENCE,limitations=LIMITS)
    provisional = RestorationPlan(result_id='pending',**payload)
    digest = hashlib.sha256((provisional.model_dump_json()+json.dumps(network.source_hashes)).encode()).hexdigest()[:24]
    return provisional.model_copy(update={'result_id':'plan-'+digest})
