"""Approved plan clauses only: the provider cannot author priority or numbers."""
from .contracts import ExplanationClause, ExplanationContext, RestorationPlan


def build_plan_context(plan: RestorationPlan) -> ExplanationContext:
    clauses = []
    def add(id, text, source='mixed'):
        clauses.append(ExplanationClause(id=id,text=text,source_type=source))
    by_id = {c.id:c for c in plan.candidates}
    recommended = by_id.get(plan.recommended_id)
    counts = '; '.join(f'{c.label}: {c.dependent_premises if c.dependent_premises is not None else "unavailable"} dependent premises' for c in plan.candidates)
    add('impact-summary', f'This declared/historical replay comparison has {plan.unique_dependent_premises if plan.unique_dependent_premises is not None else "unavailable"} unique dependent premises. {counts}. Counts describe complete source topology dependencies, not confirmed outages.')
    historical = next((c for c in plan.candidates if c.damage_source == 'historical ARCOS replay'), None)
    critical = next((c for c in plan.candidates if c.critical_proxies), None)
    add('damage-match', ('The selected historical damage association or complete premise evidence is unavailable; no complete impact is claimed. ' if historical is None or historical.dependent_premises is None else 'The selected historical replay passed the disclosed spatial association and complete reverse-membership checks. ') + 'The spatial policy uses same-type/circuit/station device proximity, a nearest-pole spatial hypothesis and a unique pole-location bridge to typed topology identity. Both spatial gates require at most 25 meters and at least 10 meters runner-up separation. The golden repairs and critical-context fuse are declared damage on verified source assets. No direct ARCOS asset identifier or current damage confirmation is claimed.')
    add('overlap', f'Summed asset memberships are {plan.summed_memberships}; unique premises are {plan.unique_dependent_premises}; duplicate memberships are {plan.overlap_memberships}. Each premise is potentially released only after all its selected damaged dependencies are repaired.')
    add('priority-summary', f'The GridGuide prototype policy recommends {recommended.label} first. {recommended.reason}' if recommended else 'No candidate can be recommended until the missing evidence or access conditions are resolved.')
    add('criticality-context', 'Spatial criticality preference is ' + ('enabled' if plan.use_critical_proxy else 'disabled') + '. ' + (f'{critical.label} has a critical-facility/nearest-premise spatial proxy with a complete premise path. ' if critical else 'No supported critical-premise proxy is available in the current candidate evidence. ') + 'This is not a verified facility electrical connection. AEP supplies no priority weights; this preference is GridGuide prototype policy.')
    add('switching-limit', 'Dependency-release potential assumes other equipment intact, supply available, access cleared and operational authorization. Actual switching feasibility, confirmed restoration counts and facility electrical attachment remain unavailable.')
    assignments = '; '.join(f'Crew {task.crew}: {by_id[task.candidate_id].label}' for task in plan.tasks)
    b = plan.display_completion_hours
    add('plan-summary', f'With {plan.crew_count} available crew(s) and {plan.crew_size} people per crew, ' + (f'the complete conditional plan spans {b.lower:g}–{b.upper:g} elapsed hours.' if b else 'the complete plan duration is unavailable because some work is blocked or lacks evidence.') + ' ' + assignments + '. Independent tasks may use separate crews only when source evidence supports that distinction. Selected upstream predecessors must finish first under conservative prototype policy.')
    add('crew-allocation', 'Crew count controls independent parallel work. People per crew only change the ideal duration boundary. Conservative ancestry ordering and per-crew availability constrain each start; extra crews never divide one repair task.')
    add('time-policy', f'The selected replacements require {plan.repair_person_hours:g} repair person-hours. Access-adjusted total person-hours are ' + (f'{plan.total_person_hours:g}' if plan.total_person_hours is not None else 'unavailable') + '. AEP direct labor × 4.5 once is person-hours. Elapsed duration uses ideal contribution through one effective worker per crew; actual efficiency remains unknown. Display rounds outward to quarter hours.')
    add('access-detail', '; '.join(f'{c.label}: {c.access}; {c.status.replace("_"," ")}' for c in plan.candidates) + '. Blocked work has no clearance duration and its dependent tasks are deferred; independent work may continue.')
    return ExplanationContext(scope='restoration_plan', result_id=plan.result_id, scenario_revision=plan.scenario_revision,
        location_label='Bounded restoration comparison', dataset_note='AEP challenge source data; historical replay plus declared damage. No live utility connection.',
        risk_band=None,risk_confidence='LOW',restoration_status='modeled' if b else 'unavailable',restoration_bounds=b,
        repair_person_hours=plan.repair_person_hours,total_person_hours=plan.total_person_hours,crew_size=plan.crew_size,
        access='blocked' if any(c.access=='blocked' for c in plan.candidates) else 'restricted' if any(c.access=='restricted' for c in plan.candidates) else 'clear',
        topology=(),alert_eligible=None,assumptions=tuple(f'{e.classification}: {e.input_or_rule}: {e.detail}' for e in plan.evidence),limitations=plan.limitations,clauses=tuple(clauses))
