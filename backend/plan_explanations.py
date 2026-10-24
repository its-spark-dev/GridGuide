"""Approved plan clauses only: the provider cannot author priority or numbers."""
from .contracts import ExplanationClause, ExplanationContext, RestorationPlan


def build_plan_context(plan: RestorationPlan, alternative: RestorationPlan | None = None) -> ExplanationContext:
    # Presentation-only comparison: both plans come from the unchanged engine.
    if alternative is not None:
        current_access = {c.id:c.access for c in plan.candidates}
        alternative_access = {c.id:c.access for c in alternative.candidates}
        if (plan.scenario_revision != alternative.scenario_revision or plan.crew_count != alternative.crew_count
                or plan.crew_size != alternative.crew_size or plan.use_critical_proxy == alternative.use_critical_proxy
                or current_access != alternative_access):
            raise ValueError("Policy explanation requires otherwise identical scenarios")
    clauses = []
    def add(id, text, source='mixed'):
        clauses.append(ExplanationClause(id=id,text=text,source_type=source))
    by_id = {c.id:c for c in plan.candidates}
    recommended = by_id.get(plan.recommended_id)
    counts = '; '.join(f'{c.label}: {c.dependent_premises if c.dependent_premises is not None else "unavailable"} dependent premises' for c in plan.candidates)
    add('impact-summary', f'This declared/historical replay comparison has {plan.unique_dependent_premises if plan.unique_dependent_premises is not None else "unavailable"} unique premise dependencies in this scenario. {counts}. Counts describe complete source topology dependencies, not a current outage count.')
    historical = next((c for c in plan.candidates if c.damage_source == 'historical ARCOS replay'), None)
    critical = next((c for c in plan.candidates if c.critical_proxies), None)
    add('damage-match', ('The selected historical damage association or complete premise evidence is unavailable; no complete impact is claimed. ' if historical is None or historical.dependent_premises is None else 'The selected historical replay passed the disclosed spatial association and complete reverse-membership checks. ') + 'The spatial policy uses same-type/circuit/station device proximity, a nearest-pole spatial hypothesis and a unique pole-location bridge to typed topology identity. Both spatial gates require at most 25 meters and at least 10 meters runner-up separation. The golden repairs and critical-context fuse are declared damage on verified source assets. No direct ARCOS asset identifier or current damage confirmation is claimed.')
    add('overlap', f'Summed asset memberships are {plan.summed_memberships}; unique premises are {plan.unique_dependent_premises}; duplicate memberships are {plan.overlap_memberships}. Each premise is potentially released only after all its selected damaged dependencies are repaired.')
    policy_name = 'Critical-service aware' if plan.use_critical_proxy else 'Customer-impact focused'
    other_name = 'Customer-impact focused' if plan.use_critical_proxy else 'Critical-service aware'
    other = next((c for c in alternative.candidates if c.id == alternative.recommended_id), None) if alternative else None
    if recommended:
        tradeoff = (f'Under {policy_name}, the scenario recommendation is {recommended.label}: '
                    f'{recommended.potential_release_at_stage} potential premise release(s) for '
                    f'{recommended.repair_person_hours:g} repair person-hours '
                    f'({recommended.total_person_hours:g} total person-hours including access). ')
    else:
        tradeoff = 'No repair is recommended while required access or evidence is unavailable. '
    if other:
        tradeoff += (f'With the same access and crews, {other_name} selects {other.label}: '
                     f'{other.potential_release_at_stage} potential premise release(s) for '
                     f'{other.repair_person_hours:g} repair person-hours '
                     f'({other.total_person_hours:g} total including access). ')
    elif alternative is not None:
        tradeoff += 'The other policy also has no executable recommendation. '
    else:
        tradeoff += 'A bound alternative-policy comparison is unavailable. '
    tradeoff += ('Critical-service aware puts supported spatial critical-service context before release per effort; '
                 'Customer-impact focused disables that preference. Both are GridGuide prototype policies, '
                 'not AEP dispatch rules or numeric AEP weights. Facility electrical service attachment is not verified.')
    add('policy-tradeoff', tradeoff)
    add('facility-connection', 'We cannot verify that the fire station is powered by this fuse. ' +
        (f'{critical.label} has a facility near an anonymized premise whose topology path is verified. '
         'The facility-to-premise relationship is spatially approximated; only the premise path is verified. '
         if critical else 'No supported critical-premise spatial proxy is available for the current candidate evidence. ') +
        'Facility electrical service attachment, current outage and backup arrangements remain unavailable.')
    add('current-outages', 'No current outage count is available. ' +
        (f'The {plan.unique_dependent_premises} figure counts unique premise dependencies in this scenario, '
         if plan.unique_dependent_premises is not None else 'Complete scenario dependency impact is unavailable; ') +
        'using declared repairs and historical spatial replay. It does not mean those premises are currently without power.')
    add('priority-summary', f'Scenario recommendation under the {policy_name} GridGuide prototype policy: {recommended.label} first. {recommended.reason}' if recommended else 'No candidate can be recommended until the missing evidence or access conditions are resolved.')
    add('criticality-context', 'Spatial criticality preference is ' + ('enabled' if plan.use_critical_proxy else 'disabled') + '. ' + (f'{critical.label} has a critical-facility/nearest-premise spatial proxy with a complete premise path. ' if critical else 'No supported critical-premise proxy is available in the current candidate evidence. ') + 'This is not a verified facility electrical connection. AEP supplies no priority weights; this preference is GridGuide prototype policy.')
    add('switching-limit', 'Switching cannot be confirmed to restore any of these premises from the supplied evidence. Dependency-release potential assumes other equipment intact, supply available, access cleared and operational authorization. Actual switching feasibility, confirmed restoration counts and facility electrical attachment remain unavailable.')
    assignments = '; '.join(f'Crew {task.crew}: {by_id[task.candidate_id].label}' for task in plan.tasks)
    b = plan.display_completion_hours
    add('plan-summary', f'With {plan.crew_count} available crew(s) and {plan.crew_size} people per crew, ' + (f'the complete conditional scenario elapsed-time envelope is {b.lower:g}–{b.upper:g} hours, not an AEP restoration guarantee.' if b else 'the complete plan duration is unavailable because some work is blocked or lacks evidence.') + ' ' + assignments + '. Adding a second crew does not halve every repair: it overlaps independent tasks while selected upstream predecessors must finish before their dependent repair. The golden transformer remains a long task after its fuse under conservative prototype policy; extra crews never split it.')
    add('crew-allocation', 'Crew count controls independent parallel work. People per crew only change the ideal duration boundary. Conservative ancestry ordering and per-crew availability constrain each start; extra crews never divide one repair task.')
    add('time-policy', f'The selected replacements require {plan.repair_person_hours:g} repair person-hours. Access-adjusted total person-hours are ' + (f'{plan.total_person_hours:g}' if plan.total_person_hours is not None else 'unavailable') + '. AEP direct labor × 4.5 once is person-hours. Elapsed duration uses ideal contribution through one effective worker per crew; actual efficiency remains unknown. Display rounds outward to quarter hours.')
    add('access-detail', '; '.join(f'{c.label}: {c.access}; {c.status.replace("_"," ")}' for c in plan.candidates) + '. Blocked work has no clearance duration and its dependent tasks are deferred; independent work may continue.')
    return ExplanationContext(scope='restoration_plan', result_id=plan.result_id, scenario_revision=plan.scenario_revision,
        location_label='Bounded restoration comparison', dataset_note='AEP challenge source data; historical replay plus declared damage. No live utility connection.',
        risk_band=None,risk_confidence='LOW',restoration_status='modeled' if b else 'unavailable',restoration_bounds=b,
        repair_person_hours=plan.repair_person_hours,total_person_hours=plan.total_person_hours,crew_size=plan.crew_size,
        access='blocked' if any(c.access=='blocked' for c in plan.candidates) else 'restricted' if any(c.access=='restricted' for c in plan.candidates) else 'clear',
        topology=(),alert_eligible=None,assumptions=tuple(f'{e.classification}: {e.input_or_rule}: {e.detail}' for e in plan.evidence),limitations=plan.limitations,clauses=tuple(clauses))
