import { useCallback, useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { components } from './api.generated';
import './RestorationDecision.css';

type Plan = components['schemas']['RestorationPlan'];
type Candidate = Plan['candidates'][number];
type PlanRequest = components['schemas']['PlanRequest'];
type Explanation = components['schemas']['ExplanationResponse'];
type Access = 'clear' | 'restricted' | 'blocked';
type Settings = { crew_count: 1 | 2; crew_size: number; use_critical_proxy: boolean; access: Record<string, Access> };

const initial: Settings = { crew_count: 1, crew_size: 4, use_critical_proxy: true, access: {} };
const format = (value: number | null | undefined) => value == null ? 'Unavailable' : new Intl.NumberFormat('en-US', { maximumFractionDigits: 3 }).format(value);
const hours = (value: { lower: number; upper: number } | null | undefined) => value ? `${format(value.lower)}–${format(value.upper)} h` : 'Unavailable';
const questions = ['Which customers depend on this damage?', 'Why this action first?', 'How do available crews change this plan?'];
const hostileQuestions = ['Why are you prioritizing one customer over 23?', 'Is that fire station actually powered by this fuse?', 'Are 28 customers currently out?', 'Why does adding a second crew not cut the time in half?', 'Can switching restore all of them?'];
const policyName = (critical: boolean) => critical ? 'Critical-service aware' : 'Customer-impact focused';
const statusLabel: Record<Candidate['status'], string> = { scheduled: 'Modeled repair', blocked: 'Access blocked', dependency_blocked: 'Waiting on upstream access', evidence_unavailable: 'Evidence incomplete' };

async function post<T>(path: string, body: unknown, signal: AbortSignal): Promise<T> {
  const response = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
    signal: AbortSignal.any([signal, AbortSignal.timeout(15_000)]), cache: 'no-store' });
  if (!response.ok) throw new Error('The planning service could not complete this request. Please try again.');
  return response.json() as Promise<T>;
}

function ImpactMap({ candidate }: { candidate: Candidate }) {
  const host = useRef<HTMLDivElement>(null);
  const hasGeometry = candidate.position !== null || candidate.customer_cells.length > 0;
  useEffect(() => {
    if (!host.current) return;
    const map = L.map(host.current, { scrollWheelZoom: false, minZoom: 7, maxZoom: 14, zoomAnimation: false, fadeAnimation: false });
    map.attributionControl.addAttribution('AEP challenge GIS · generalized areas');
    const bounds = L.latLngBounds([]);
    candidate.customer_cells.forEach(cell => {
      const { latitude, longitude, precision_degrees } = cell.position;
      const half = precision_degrees / 2;
      const area: L.LatLngBoundsExpression = [[latitude - half, longitude - half], [latitude + half, longitude + half]];
      bounds.extend(area);
      L.rectangle(area, { color: '#025a95', weight: 2, fillOpacity: .13, interactive: false }).addTo(map);
      L.marker([latitude, longitude], { keyboard: false, interactive: false,
        icon: L.divIcon({ className: 'decision-cell-count', html: `<span>${cell.premises}</span>`, iconSize: [34, 30], iconAnchor: [17, 15] }),
      }).addTo(map);
    });
    if (candidate.position) {
      const point: L.LatLngTuple = [candidate.position.latitude, candidate.position.longitude];
      bounds.extend(point);
      const label = document.createElement('div');
      label.textContent = `${candidate.label}: generalized equipment area. Exact position hidden.`;
      L.circleMarker(point, { color: '#af2218', fillColor: '#fff', fillOpacity: 1, weight: 3, radius: 8 })
        .addTo(map).bindPopup(label);
    }
    if (bounds.isValid()) map.fitBounds(bounds, { padding: [34, 34], maxZoom: 12 });
    const observer = new ResizeObserver(() => map.invalidateSize());
    observer.observe(host.current);
    return () => { observer.disconnect(); map.remove(); };
  }, [candidate]);

  return <div className="decision-map-wrap">
    {hasGeometry ? <div className="decision-map" ref={host} tabIndex={0} role="region" aria-label={`Approximate dependent premise areas for ${candidate.label}`} aria-describedby="decision-map-note" data-testid="decision-map" /> : <p role="status">Generalized geometry is unavailable for this candidate.</p>}
    <div className="decision-map-caption"><span><i className="decision-legend-cell" /> Dependent premise area</span><span><i className="decision-legend-asset" /> Selected equipment area</span></div>
    <p id="decision-map-note" className="fine muted">0.01° generalized cells; counts come from verified source dependencies. Cells are not outage boundaries. This view works without street tiles.</p>
    <details className="decision-map-accessible"><summary>Read the map as a list</summary>
      <ul>{candidate.customer_cells.map((cell, index) => <li key={index}>Approximate area {index + 1}: {format(cell.premises)} dependent premises.</li>)}</ul>
      {!candidate.customer_cells.length && <p>No validated premise areas are available for this candidate.</p>}
    </details>
  </div>;
}

function CandidateEvidence({ candidate }: { candidate: Candidate }) {
  return <details className="decision-candidate-evidence"><summary>Inspect match, labor & uncertainty</summary>
    <p>{candidate.evidence_note}</p>
    <dl>
      <div><dt>Match classification</dt><dd>{candidate.dependent_premises == null ? 'Unavailable' : candidate.damage_source === 'historical ARCOS replay' ? 'Qualified spatial hypothesis · no exact identifier match' : 'Source identity verified · damage declared'}</dd></div>
      <div><dt>Damage origin</dt><dd>{candidate.damage_source}</dd></div>
      <div><dt>Match method</dt><dd>{candidate.match_method}</dd></div>
      {candidate.match_distance_m != null && <div><dt>Asset distance</dt><dd>{format(candidate.match_distance_m)} m</dd></div>}
      {candidate.runner_up_distance_m != null && <div><dt>Next candidate distance</dt><dd>{format(candidate.runner_up_distance_m)} m</dd></div>}
      {candidate.pole_distance_m != null && <div><dt>Pole context distance</dt><dd>{format(candidate.pole_distance_m)} m</dd></div>}
      <div><dt>Direct replacement labor</dt><dd>{format(candidate.direct_labor_hours)} hours</dd></div>
      <div><dt>Repair effort</dt><dd>{format(candidate.repair_person_hours)} person-hours</dd></div>
      <div><dt>Access work</dt><dd>{format(candidate.access_direct_hours)} direct hours</dd></div>
      <div><dt>Conditional task envelope</dt><dd>{hours(candidate.elapsed_hours)}</dd></div>
    </dl>
    {candidate.critical_proxies.map((proxy, index) => <p key={index}>{proxy.kind.replaceAll('_', ' ')}: {proxy.relationship}. Spatial distance {format(proxy.distance_m)} m; next premise {format(proxy.runner_up_distance_m)} m. Electrical attachment is unverified.</p>)}
    <p>Current damage confirmation and actual restoration through switching remain unavailable.</p>
  </details>;
}

export function RestorationDecision() {
  const [settings, setSettings] = useState<Settings>(initial);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [alternative, setAlternative] = useState<Plan | null>(null);
  const [alternativePending, setAlternativePending] = useState(true);
  const [previous, setPrevious] = useState<Plan | null>(null);
  const [catalog, setCatalog] = useState<{ id: string; label: string }[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [pending, setPending] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [answer, setAnswer] = useState<Explanation | null>(null);
  const [answerPending, setAnswerPending] = useState(false);
  const [answerFailed, setAnswerFailed] = useState(false);
  const [question, setQuestion] = useState<string | null>(null);
  const revision = useRef(0);
  const currentSettings = useRef<Settings>(initial);
  const lastConfirmed = useRef<Plan | null>(null);
  const activeResult = useRef<Plan | null>(null);
  const activeRequest = useRef<PlanRequest | null>(null);
  const evaluationController = useRef<AbortController | null>(null);
  const explanationController = useRef<AbortController | null>(null);
  const explanationSequence = useRef(0);

  const evaluate = useCallback(async (next: Settings) => {
    const requestRevision = ++revision.current;
    currentSettings.current = next;
    setSettings(next);
    evaluationController.current?.abort(); explanationController.current?.abort();
    explanationSequence.current += 1;
    const controller = new AbortController(); evaluationController.current = controller;
    activeResult.current = null; activeRequest.current = null;
    setPending(true); setError(null); setPlan(null); setAlternative(null); setAlternativePending(true); setAnswer(null); setAnswerPending(false); setAnswerFailed(false); setQuestion(null);
    const body: PlanRequest = { scenario_revision: requestRevision, crew_count: next.crew_count, crew_size: next.crew_size,
      use_critical_proxy: next.use_critical_proxy, access: Object.entries(next.access).map(([candidate_id, access]) => ({ candidate_id, access })) };
    const opposite = post<Plan>('/api/restoration-plan', { ...body, use_critical_proxy: !next.use_critical_proxy }, controller.signal).catch(() => null);
    try {
      const response = await post<Plan>('/api/restoration-plan', body, controller.signal);
      if (controller.signal.aborted || requestRevision !== revision.current) return;
      if (response.scenario_revision !== requestRevision || response.crew_count !== next.crew_count || response.crew_size !== next.crew_size ||
          response.use_critical_proxy !== next.use_critical_proxy || response.candidates.some(candidate => candidate.access !== (next.access[candidate.id] ?? 'clear')) ||
          Object.keys(next.access).some(id => !response.candidates.some(candidate => candidate.id === id)) ||
          (response.recommended_id !== null && !response.candidates.some(candidate => candidate.id === response.recommended_id))) {
        throw new Error('The plan did not match your scenario. Please try again.');
      }
      setPrevious(lastConfirmed.current); lastConfirmed.current = response; activeResult.current = response; activeRequest.current = body;
      setCatalog(response.candidates.map(({ id, label }) => ({ id, label })));
      setSelected(value => response.candidates.some(candidate => candidate.id === value) ? value : response.recommended_id ?? response.candidates[0]?.id ?? null);
      setPlan(response); setPending(false);
      const other = await opposite;
      if (controller.signal.aborted || requestRevision !== revision.current) return;
      if (other && other.scenario_revision === requestRevision && other.crew_count === next.crew_count && other.crew_size === next.crew_size &&
          other.use_critical_proxy === !next.use_critical_proxy && Array.isArray(other.candidates) && other.candidates.length === response.candidates.length &&
          other.candidates.every(c => c && response.candidates.some(original => original.id === c.id && original.access === c.access)) &&
          new Set(other.candidates.map(c => c.id)).size === response.candidates.length &&
          (other.recommended_id === null || other.candidates.some(c => c.id === other.recommended_id))) setAlternative(other);
      setAlternativePending(false);
    } catch (failure) {
      if (controller.signal.aborted || requestRevision !== revision.current) return;
      setError(failure instanceof Error && failure.name !== 'TimeoutError' ? failure.message : 'The planning service took too long to respond. Please try again.');
      setPending(false); setAlternativePending(false);
      controller.abort();
    }
  }, []);

  useEffect(() => {
    void evaluate(initial);
    return () => { revision.current += 1; explanationSequence.current += 1; evaluationController.current?.abort(); explanationController.current?.abort(); };
  }, [evaluate]);

  function change(patch: Partial<Settings>) { void evaluate({ ...currentSettings.current, ...patch }); }
  function changeAccess(id: string, access: Access) { change({ access: { ...currentSettings.current.access, [id]: access } }); }

  async function ask(next: string) {
    const current = activeResult.current; const request = activeRequest.current;
    if (!current || !request) return;
    const number = ++explanationSequence.current;
    explanationController.current?.abort();
    const controller = new AbortController(); explanationController.current = controller;
    setQuestion(next); setAnswer(null); setAnswerPending(true); setAnswerFailed(false);
    try {
      const response = await post<Explanation>('/api/restoration-plan/explain', { ...request, result_id: current.result_id, question: next }, controller.signal);
      if (controller.signal.aborted || number !== explanationSequence.current || activeResult.current?.result_id !== current.result_id) return;
      if (response.result_id !== current.result_id || response.scenario_revision !== current.scenario_revision) throw new Error('Explanation binding mismatch');
      setAnswer(response);
    } catch {
      if (!controller.signal.aborted && number === explanationSequence.current && activeResult.current?.result_id === current.result_id) setAnswerFailed(true);
    } finally {
      if (!controller.signal.aborted && number === explanationSequence.current) setAnswerPending(false);
    }
  }

  const current = !pending && !error ? plan : null;
  const recommended = current?.candidates.find(candidate => candidate.id === current.recommended_id);
  const counterfactual = current && alternative?.candidates.find(candidate => candidate.id === alternative.recommended_id);
  const chosen = current?.candidates.find(candidate => candidate.id === selected) ?? current?.candidates[0];
  const label = (id: string) => current?.candidates.find(candidate => candidate.id === id)?.label ?? 'Repair candidate';
  const assigned = (id: string) => current?.tasks.find(task => task.candidate_id === id);
  const hasDeferred = current?.candidates.some(candidate => candidate.status !== 'scheduled');
  const criticalInfluenced = !!(recommended?.critical_proxies.length && current?.use_critical_proxy);

  return <section className="restoration-decision" aria-labelledby="decision-title" data-testid="restoration-decision">
    <div className="section-heading"><div><span className="eyebrow">DAMAGE → DEPENDENCIES → REPAIR PLAN</span><h2 id="decision-title">Which repair first?</h2></div><span className="evidence-tag modeled">Scenario · not AEP dispatch</span></div>
    <p className="muted decision-intro">Historical replay and declared damage. Compare what each repair could release, under a policy you can change.</p>

    {current && <div className="decision-summary" data-testid="decision-recommendation">
      <div className="decision-next">
        <span className="eyebrow">SCENARIO RECOMMENDATION</span>
        <h3>{recommended?.label ?? 'No executable repair recommendation'}</h3>
        <p className="decision-active-policy"><span className="evidence-tag policy">Prototype policy</span> <strong>{policyName(current.use_critical_proxy)}</strong></p>
        <p>{recommended ? criticalInfluenced ? 'Critical-service spatial context takes precedence over premise release per effort under this GridGuide policy.' : recommended.reason : 'Required access or complete evidence is unavailable. No clearance duration is assumed.'}</p>
        {criticalInfluenced && <p className="decision-critical-inline"><span className="evidence-tag spatial">Spatial critical-premise proxy</span><strong>Facility service attachment is not verified.</strong></p>}
        {recommended && <p className="decision-action-facts"><strong>{format(recommended.potential_release_at_stage)}</strong> potential premise release · <strong>{format(recommended.repair_person_hours)}</strong> repair person-hours · <strong>Crew {assigned(recommended.id)?.crew}</strong></p>}
        {counterfactual && recommended && counterfactual.id !== recommended.id && <p className="decision-lead-counterfactual">Under <strong>{policyName(!current.use_critical_proxy)}</strong>, <strong>{counterfactual.label}</strong> leads: {format(counterfactual.potential_release_at_stage)} potential premise releases for {format(counterfactual.repair_person_hours)} repair person-hours.</p>}
      </div>
      <dl className="decision-stats"><div><dt>Unique premise dependencies<br />in this scenario</dt><dd>{format(current.unique_dependent_premises)}</dd></div><div><dt>Repair effort · whole plan</dt><dd>{format(current.repair_person_hours)} <small>person-hours</small>{current.total_person_hours !== current.repair_person_hours && <small>Total with access: {format(current.total_person_hours)}</small>}</dd></div><div><dt>Conditional scenario time<br /><small>Whole plan · prototype envelope</small></dt><dd>{hours(current.display_completion_hours)}</dd></div></dl>
      <p className="decision-summary-note">No current outage count or confirmed restoration. Person-hours describe work; elapsed time depends on crew and access assumptions. This is not an official AEP dispatch order or restoration guarantee.</p>
      <nav className="decision-story-links" aria-label="Scenario story shortcuts"><a href="#decision-geography-title">Inspect selected damage & dependencies</a><a href="#decision-schedule-title">See crews & release milestones</a></nav>
    </div>}

    <fieldset className="decision-policy"><legend>Choose a scenario policy <span>GridGuide prototype · not an AEP setting</span></legend>
      <label className={settings.use_critical_proxy ? 'is-active' : ''}><input type="radio" name="planning-policy" checked={settings.use_critical_proxy} onChange={() => change({ use_critical_proxy: true })} /><span><strong>Critical-service aware</strong><small>Spatial critical-service context before release / effort. Electrical attachment is unverified.</small></span></label>
      <label className={!settings.use_critical_proxy ? 'is-active' : ''}><input type="radio" name="planning-policy" checked={!settings.use_critical_proxy} onChange={() => change({ use_critical_proxy: false })} /><span><strong>Customer-impact focused</strong><small>Prioritize marginal premise release / effort, with criticality preference disabled.</small></span></label>
    </fieldset>

    {current && <section className="decision-tradeoff" aria-labelledby="tradeoff-title" data-testid="policy-tradeoff"><h3 id="tradeoff-title">The tradeoff, made explicit</h3>
      {alternativePending ? <p role="status">Checking the other policy with the same access and crews…</p> : alternative ? <>
        <div className="decision-tradeoff-options"><div><span>Selected · {policyName(current.use_critical_proxy)}</span><strong>{recommended?.label ?? 'No executable recommendation'}</strong><p>{recommended ? `${format(recommended.potential_release_at_stage)} potential premise release · ${format(recommended.repair_person_hours)} repair person-hours` : 'Access or evidence must be resolved.'}</p></div><div><span>Alternative · {policyName(alternative.use_critical_proxy)}</span><strong>{counterfactual?.label ?? 'No executable recommendation'}</strong><p>{counterfactual ? `${format(counterfactual.potential_release_at_stage)} potential premise release · ${format(counterfactual.repair_person_hours)} repair person-hours` : 'Access or evidence must be resolved.'}</p></div></div>
        <p>{recommended && counterfactual ? recommended.id === counterfactual.id ? 'Both policies select the same first repair under the current constraints.' : current.use_critical_proxy ? 'Without critical-service preference, the alternative leads on marginal premise release per total effort. The preference is a visible policy choice, not an AEP weight.' : 'Enabling critical-service preference changes which repair leads. Its facility relationship remains spatially approximated.' : 'Changing policy cannot make blocked work executable or supply missing evidence.'} Access-adjusted total effort is {format(recommended?.total_person_hours)} / {format(counterfactual?.total_person_hours)} person-hours for these respective actions.</p>
      </> : <><p role="status">The alternative-policy comparison is unavailable. The current validated plan remains available.</p><button type="button" onClick={() => void evaluate(currentSettings.current)}>Retry policy comparison</button></>}
    </section>}

    <fieldset className="decision-controls"><legend>Set crew assumptions</legend>
      <label htmlFor="plan-crew-count">Available crews<select id="plan-crew-count" value={settings.crew_count} onChange={event => change({ crew_count: Number(event.target.value) as 1 | 2 })}><option value={1}>1 crew</option><option value={2}>2 crews</option></select><small>Separate crews can overlap independent repairs.</small></label>
      <label htmlFor="plan-crew-size">People per crew<select id="plan-crew-size" value={settings.crew_size} onChange={event => change({ crew_size: Number(event.target.value) })}>{[2, 3, 4, 5, 6, 7, 8].map(value => <option key={value} value={value}>{value} people</option>)}</select><small>Changes the ideal lower time boundary per task.</small></label>
    </fieldset>
    {catalog.length > 0 && <fieldset className="decision-access"><legend>Access at each repair candidate</legend>{catalog.map(candidate => <label key={candidate.id}>{candidate.label}<select value={settings.access[candidate.id] ?? 'clear'} onChange={event => changeAccess(candidate.id, event.target.value as Access)}><option value="clear">Clear</option><option value="restricted">Restricted · extra work</option><option value="blocked">Blocked · clearance unknown</option></select></label>)}</fieldset>}

    <div aria-live="polite" aria-atomic="true" aria-busy={pending} className="decision-load-state">
      {pending && <p role="status">Updating the scenario recommendation, dependencies and crew plan…</p>}
      {current && <span className="sr-only">Scenario updated. {policyName(current.use_critical_proxy)}. {recommended?.label ?? 'No executable repair recommendation'}. {format(current.unique_dependent_premises)} unique premise dependencies in this scenario. Conditional time {hours(current.display_completion_hours)}.</span>}
      {error && <div className="error-panel" role="alert"><div><strong>Restoration plan unavailable</strong><p>{error}</p></div><button type="button" onClick={() => void evaluate(currentSettings.current)}>Retry plan</button></div>}
    </div>

    {current && <>
      {hasDeferred && <div className="decision-deferred" role="status" data-testid="deferred-work"><span className="evidence-tag unavailable">Unavailable · full completion time</span><h3>{current.tasks.length ? 'Deferred work does not stop independent repairs' : 'No work can be scheduled in this scenario'}</h3><p>{current.tasks.length ? `${format(current.scheduled_release_potential)} potential premise releases remain in the executable part of the plan. Blocked repairs and their dependents are deferred.` : 'Resolve access or evidence before choosing a repair. No recommendation, schedule or clearance duration is invented.'}</p><ul>{current.candidates.filter(c => c.status !== 'scheduled').map(c => <li key={c.id}><strong>{c.label}:</strong> {c.reason}</li>)}</ul></div>}
      {previous && <div className="decision-comparison" role="status" data-testid="decision-comparison"><strong>Compared with your last completed scenario</strong><div><span>Policy</span><b>{policyName(previous.use_critical_proxy)} → {policyName(current.use_critical_proxy)}</b></div><div><span>Crews / people per crew</span><b>{previous.crew_count} / {previous.crew_size} → {current.crew_count} / {current.crew_size}</b></div><div><span>Conditional scenario time</span><b>{hours(previous.display_completion_hours)} → {hours(current.display_completion_hours)}</b></div><div><span>Total effort including access</span><b>{format(previous.total_person_hours)} → {format(current.total_person_hours)} person-hours</b></div></div>}

      <div className="decision-impacts-heading"><h3>Compare repair candidates</h3><p className="fine muted">{format(current.summed_memberships)} asset memberships include {format(current.overlap_memberships)} duplicate memberships. The union is {format(current.unique_dependent_premises)} unique premise dependencies in this scenario—not current outages.</p></div>
      <div className="decision-candidates" role="group" aria-label="Select a candidate to inspect its map, dependencies and crew assignment">
        {current.candidates.map(candidate => <article key={candidate.id} className={`decision-candidate ${chosen?.id === candidate.id ? 'is-selected' : ''}`}>
          <button className="decision-select" type="button" aria-pressed={chosen?.id === candidate.id} onClick={() => setSelected(candidate.id)}><span className="decision-rank" aria-label={`Scenario rank ${candidate.priority_rank ?? 'unavailable'}`}>{candidate.priority_rank ?? '—'}</span><span><strong>{candidate.label}</strong><small>{candidate.damage_source}</small></span><span aria-hidden="true">↗</span></button>
          <span className={`decision-status ${candidate.status === 'scheduled' ? '' : 'is-blocked'}`}>{statusLabel[candidate.status]}</span>
          <p className="decision-identity">{candidate.damage_source === 'historical ARCOS replay' ? 'Historical replay · qualified spatial hypothesis, not exact identity.' : 'Known source asset · declared damage.'}</p>
          {candidate.critical_proxies.length > 0 && <p className="decision-critical-inline"><span className="evidence-tag spatial">Critical-service spatial context</span><strong>Facility service attachment is not verified.</strong></p>}
          <dl className="decision-candidate-metrics"><div><dt>Premise dependencies</dt><dd>{format(candidate.dependent_premises)}</dd></div><div><dt>Potential release at its stage</dt><dd>{format(candidate.potential_release_at_stage)}</dd></div><div><dt>Repair effort · person-hours</dt><dd>{format(candidate.repair_person_hours)}</dd></div><div><dt>Potential releases / total person-hour</dt><dd>{format(candidate.release_per_total_person_hour)}</dd><small>Includes modeled access work</small></div></dl>
          <p className="decision-prerequisite">{candidate.status === 'evidence_unavailable' ? 'Dependency ordering unavailable until complete evidence is restored.' : candidate.prerequisite_ids.length ? `Requires: ${candidate.prerequisite_ids.map(label).join(', ')}.` : 'No other selected repair prerequisite.'} {assigned(candidate.id) ? `Assigned to Crew ${assigned(candidate.id)?.crew}.` : 'Not scheduled.'}</p>
          <CandidateEvidence candidate={candidate} />
        </article>)}
      </div>

      {chosen && <section className="decision-geography" aria-labelledby="decision-geography-title" data-testid="selected-dependency"><div><span className="eyebrow">SELECTED CANDIDATE · WHERE + WHO DEPENDS</span><h3 id="decision-geography-title" tabIndex={-1}>{chosen.label}</h3>
        <p>{chosen.dependent_premises == null ? 'Complete reverse dependency evidence is unavailable.' : `${format(chosen.dependent_premises)} premises with verified reverse topology dependencies${chosen.damage_source === 'historical ARCOS replay' ? ' for this historical spatial replay' : ' under declared damage'}.`}</p>
        <ol className="decision-evidence-chain" aria-label="Damage to premise evidence chain"><li>{chosen.damage_source === 'historical ARCOS replay' ? 'Historical ARCOS observation' : 'Declared damage scenario'}</li><li>{chosen.dependent_premises == null ? 'Association or membership unavailable' : chosen.damage_source === 'historical ARCOS replay' ? 'Qualified spatial match · no exact identifier' : 'Verified source identity'}</li><li>Source {chosen.kind === 'Distribution' ? 'transformer' : 'fuse'} → reverse topology index</li><li>{format(chosen.dependent_premises)} scenario premise dependencies</li></ol>
        <div className="decision-selected-prerequisites"><span className="evidence-tag known">Source-derived dependencies</span><p>{chosen.status === 'evidence_unavailable' ? 'Selected-repair dependencies unavailable.' : chosen.prerequisite_ids.length ? `${chosen.prerequisite_ids.map(label).join(' + ')} → ${chosen.label} → premise dependencies` : `${chosen.label} → premise dependencies. No other selected repair prerequisite.`}</p><p className="fine muted">Selected repairs only; not a complete electrical diagram. {assigned(chosen.id) ? `Crew ${assigned(chosen.id)?.crew} · conditional finish ${hours(assigned(chosen.id)?.display_finish_hours)}.` : 'No crew assignment.'}</p></div>
        {chosen.critical_proxies.length > 0 && <p className="decision-critical-inline"><span className="evidence-tag spatial">Spatial critical-premise proxy</span><strong>Facility service attachment is not verified.</strong></p>}
        <p className="fine muted">Selection highlights the same candidate in the map and crew plan. It does not remove other repairs from the scenario.</p></div><ImpactMap candidate={chosen} /></section>}

      <section className="decision-schedule" aria-labelledby="decision-schedule-title"><div className="section-heading"><div><span className="eyebrow">WHO WORKS · WHO WAITS · WHAT COULD RELEASE</span><h3 id="decision-schedule-title" tabIndex={-1}>Scenario crew plan</h3></div><span className="evidence-tag modeled">{current.crew_count} {current.crew_count === 1 ? 'crew' : 'crews'} · {current.crew_size} people each</span></div>
        <p className="fine muted">Elapsed-time envelopes start at the modeled crew response. Independent tasks can overlap; selected upstream repairs finish before dependent work. Actual efficiency and clearance duration remain unavailable.</p>
        <div className="decision-lanes">{Array.from({ length: current.crew_count }, (_, index) => index + 1).map(crew => <div className="decision-lane" key={crew}><h4>Crew {crew}</h4><ol>{current.tasks.filter(task => task.crew === crew).map((task, taskIndex, crewTasks) => {
          const candidate = current.candidates.find(c => c.id === task.candidate_id)!;
          return <li key={task.candidate_id} className={chosen?.id === task.candidate_id ? 'is-selected' : ''}>
            {candidate.prerequisite_ids.length > 0 && <p className="decision-task-wait"><strong>Wait for {candidate.prerequisite_ids.map(label).join(' + ')}</strong><span>Upstream prerequisite must finish before this task.</span></p>}
            <button type="button" className="decision-task-select" aria-pressed={chosen?.id === task.candidate_id} onClick={() => setSelected(task.candidate_id)}>{label(task.candidate_id)}</button>
            <span>{task.start_hours.upper === 0 ? 'Starts with available independent work' : taskIndex > 0 ? `After ${label(crewTasks[taskIndex - 1].candidate_id)} on this crew` : 'After its upstream prerequisite'}</span><span>Conditional finish {hours(task.display_finish_hours)}</span>
          </li>;
        })}</ol>{!current.tasks.some(task => task.crew === crew) && <p className="muted fine">No executable work assigned.</p>}</div>)}</div>
        {current.milestones.length > 0 && <div className="decision-table-scroll" tabIndex={0} role="region" aria-label="Dependency-release milestone table"><table className="decision-milestones"><caption>Dependency-release milestones · not confirmed restoration</caption><thead><tr><th scope="col">Modeled completed repair</th><th scope="col">Conditional elapsed</th><th scope="col">Additional potential release</th><th scope="col">Cumulative potential release</th></tr></thead><tbody>{current.milestones.map((milestone, index) => <tr key={index}><th scope="row">{milestone.candidate_ids.map(label).join(' + ')}</th><td>{hours(milestone.display_hours)}</td><td>{format(milestone.additional_premises)}</td><td>{format(milestone.cumulative_premises)}</td></tr>)}</tbody></table></div>}
        {!current.completion_hours && <p className="decision-unavailable">Full completion is unavailable. Executable work has {format(current.scheduled_release_potential)} potential premise releases; this does not confirm power restoration. Actual switching feasibility is unavailable.</p>}
      </section>

      <section className="decision-explanation" aria-labelledby="decision-ask-title"><span className="eyebrow">EXPLAIN THIS SCENARIO</span><h3 id="decision-ask-title">Ask GridGuide about this plan</h3><p className="fine muted">Answers use server-owned facts and policy. Gemini may select supporting evidence; Standard explanations use the same authoritative answer.</p><div className="explanation-questions">{questions.map(item => <button key={item} type="button" aria-pressed={question === item} onClick={() => void ask(item)}>{item}</button>)}</div>
        <details className="decision-hostile"><summary>Challenge the policy and evidence</summary><div className="explanation-questions">{hostileQuestions.map(item => <button key={item} type="button" aria-pressed={question === item} onClick={() => void ask(item)}>{item}</button>)}</div></details>
        <div aria-live="polite" aria-atomic="true" aria-busy={answerPending} data-testid="decision-explanation">{answerPending && <p role="status">Selecting supporting evidence for this scenario… The validated plan above remains available.</p>}{answer && <div className="decision-answer"><span className="evidence-tag modeled">{answer.mode === 'ai_assisted' ? 'AI-assisted explanation' : answer.mode === 'unsupported' ? 'Outside verified scope' : 'Standard explanation'}</span><p>{answer.answer}</p><ul>{answer.supporting_factors.map(factor => <li key={factor.id}>{factor.text}</li>)}</ul><p className="fine muted">{answer.uncertainty_note}</p></div>}{answerFailed && <div role="status"><p>The explanation service is unavailable. The validated plan and evidence remain available.</p><button type="button" onClick={() => question && void ask(question)}>Retry explanation</button></div>}</div>
      </section>

      <details className="decision-audit"><summary>Source coverage, assumptions & limitations</summary><p>Indexed source paths: {format(current.coverage.indexed_paths)}. Fully validated paths: {format(current.coverage.verified_paths)}. Paths with unresolved evidence: {format(current.coverage.unresolved_paths)}.</p><p>Complete physical reverse dependencies: {format(current.coverage.supported_physical_reverse_assets)} assets ({format(current.coverage.transformer_reverse_assets)} transformers and {format(current.coverage.fuse_reverse_assets)} fuses). Unknown membership is withheld, never reported as zero.</p><p>Historical ARCOS records: {format(current.coverage.arcOS_records)}. Spatial candidates with complete reverse evidence: {format(current.coverage.complete_spatial_candidates)}. Spatial associations do not establish confirmed damage identity.</p><ul>{current.policy.map(policy => <li key={policy}>{policy}</li>)}</ul><dl>{current.evidence.map((item, index) => <div key={index}><dt>{item.input_or_rule} <span className="small-badge">{item.classification}</span></dt><dd>{item.detail}</dd></div>)}</dl><ul>{current.limitations.map(limit => <li key={limit}>{limit}</li>)}</ul></details>
    </>}
  </section>;
}
