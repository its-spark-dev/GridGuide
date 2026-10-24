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
const statusLabel: Record<Candidate['status'], string> = { scheduled: 'Ready for modeled plan', blocked: 'Access blocked', dependency_blocked: 'Waiting on upstream access', evidence_unavailable: 'Evidence incomplete' };

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
  return <details className="decision-candidate-evidence"><summary>Identity, labor & uncertainty</summary>
    <p>{candidate.evidence_note}</p>
    <dl>
      <div><dt>Damage origin</dt><dd>{candidate.damage_source}</dd></div>
      <div><dt>Match method</dt><dd>{candidate.match_method}</dd></div>
      {candidate.match_distance_m != null && <div><dt>Asset distance</dt><dd>{format(candidate.match_distance_m)} m</dd></div>}
      {candidate.runner_up_distance_m != null && <div><dt>Next candidate distance</dt><dd>{format(candidate.runner_up_distance_m)} m</dd></div>}
      {candidate.pole_distance_m != null && <div><dt>Pole context distance</dt><dd>{format(candidate.pole_distance_m)} m</dd></div>}
      <div><dt>Direct replacement labor</dt><dd>{format(candidate.direct_labor_hours)} hours</dd></div>
      <div><dt>Repair effort</dt><dd>{format(candidate.repair_person_hours)} person-hours</dd></div>
      <div><dt>Access work</dt><dd>{format(candidate.access_direct_hours)} direct hours</dd></div>
      <div><dt>Conditional task duration</dt><dd>{hours(candidate.elapsed_hours)}</dd></div>
    </dl>
    {candidate.critical_proxies.map((proxy, index) => <p key={index}>{proxy.kind.replaceAll('_', ' ')}: {proxy.relationship}. Spatial distance {format(proxy.distance_m)} m; next premise {format(proxy.runner_up_distance_m)} m. Electrical attachment is unverified.</p>)}
    <p>Current damage confirmation and actual restoration through switching remain unavailable.</p>
  </details>;
}

export function RestorationDecision() {
  const [settings, setSettings] = useState<Settings>(initial);
  const [plan, setPlan] = useState<Plan | null>(null);
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
    setPending(true); setError(null); setPlan(null); setAnswer(null); setAnswerPending(false); setAnswerFailed(false); setQuestion(null);
    const body: PlanRequest = { scenario_revision: requestRevision, crew_count: next.crew_count, crew_size: next.crew_size,
      use_critical_proxy: next.use_critical_proxy, access: Object.entries(next.access).map(([candidate_id, access]) => ({ candidate_id, access })) };
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
    } catch (failure) {
      if (controller.signal.aborted || requestRevision !== revision.current) return;
      setError(failure instanceof Error && failure.name !== 'TimeoutError' ? failure.message : 'The planning service took too long to respond. Please try again.');
      setPending(false);
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
  const chosen = current?.candidates.find(candidate => candidate.id === selected) ?? current?.candidates[0];
  const label = (id: string) => current?.candidates.find(candidate => candidate.id === id)?.label ?? 'Repair candidate';

  return <section className="restoration-decision" aria-labelledby="decision-title" data-testid="restoration-decision">
    <div className="section-heading"><div><span className="eyebrow">RESTORATION DECISION SUPPORT</span><h2 id="decision-title">What should happen next?</h2></div><span className="small-badge">Conditional repair scenario</span></div>
    <p className="muted decision-intro">Compare damaged assets, the premises that depend on them and a crew plan. Historical damage is replayed as a scenario; this is not a live dispatch or AEP restoration estimate.</p>

    {current && <div className="decision-summary" data-testid="decision-recommendation">
      <div className="decision-next"><span className="eyebrow">RECOMMENDED NEXT ACTION</span><h3>{recommended?.label ?? 'Resolve blocked work or missing evidence'}</h3><p>{recommended?.reason ?? 'A repair cannot be recommended from the current accessible, validated candidates.'}</p></div>
      <dl className="decision-stats"><div><dt>Unique dependent premises</dt><dd>{format(current.unique_dependent_premises)}</dd></div><div><dt>Full plan · conditional elapsed</dt><dd>{hours(current.display_completion_hours)}</dd></div><div><dt>Total labor effort</dt><dd>{format(current.total_person_hours)} <small>person-hours</small></dd></div></dl>
      <p className="decision-summary-note">Dependency releases require every damaged asset on a premise’s path to be repaired. Actual efficiency, energization and switching feasibility remain unknown.</p>
    </div>}

    <fieldset className="decision-controls"><legend>Change planning assumptions</legend>
      <label>Available crews<select value={settings.crew_count} onChange={event => change({ crew_count: Number(event.target.value) as 1 | 2 })}><option value={1}>1 crew</option><option value={2}>2 crews</option></select></label>
      <label>People per crew<select value={settings.crew_size} onChange={event => change({ crew_size: Number(event.target.value) })}>{[2, 3, 4, 5, 6, 7, 8].map(value => <option key={value} value={value}>{value} people</option>)}</select></label>
      <label className="decision-proxy-toggle"><input type="checkbox" checked={settings.use_critical_proxy} onChange={event => change({ use_critical_proxy: event.target.checked })} /><span>Include critical-facility spatial proxy<small>Scenario priority rule; electrical attachment is unverified.</small></span></label>
    </fieldset>
    {catalog.length > 0 && <fieldset className="decision-access"><legend>Access at each repair candidate</legend>{catalog.map(candidate => <label key={candidate.id}>{candidate.label}<select value={settings.access[candidate.id] ?? 'clear'} onChange={event => changeAccess(candidate.id, event.target.value as Access)}><option value="clear">Clear</option><option value="restricted">Restricted · extra work</option><option value="blocked">Blocked · clearance unknown</option></select></label>)}</fieldset>}

    <div aria-live="polite" aria-atomic="true" aria-busy={pending} className="decision-load-state">
      {pending && <p role="status">Updating impact, priorities and crew assignments for this scenario…</p>}
      {error && <div className="error-panel" role="alert"><div><strong>Restoration plan unavailable</strong><p>{error}</p></div><button type="button" onClick={() => void evaluate(currentSettings.current)}>Retry plan</button></div>}
    </div>

    {current && <>
      {previous && <div className="decision-comparison" role="status" data-testid="decision-comparison"><strong>Compared with your last completed scenario</strong><div><span>Crews</span><b>{previous.crew_count} → {current.crew_count}</b></div><div><span>People per crew</span><b>{previous.crew_size} → {current.crew_size}</b></div><div><span>Conditional completion</span><b>{hours(previous.display_completion_hours)} → {hours(current.display_completion_hours)}</b></div><div><span>Labor effort</span><b>{format(previous.total_person_hours)} → {format(current.total_person_hours)} person-hours</b></div></div>}

      <div className="decision-impacts-heading"><h3>Compare repair candidates</h3><p className="fine muted">{format(current.summed_memberships)} memberships include {format(current.overlap_memberships)} overlaps. Unique impact is {format(current.unique_dependent_premises)} premises.</p></div>
      <div className="decision-candidates" role="group" aria-label="Select a candidate to explore its dependent premise areas">
        {current.candidates.map(candidate => <article key={candidate.id} className={`decision-candidate ${chosen?.id === candidate.id ? 'is-selected' : ''}`}>
          <button className="decision-select" type="button" aria-pressed={chosen?.id === candidate.id} onClick={() => setSelected(candidate.id)}><span className="decision-rank">{candidate.priority_rank ?? '—'}</span><span><strong>{candidate.label}</strong><small>{candidate.damage_source}</small></span><span aria-hidden="true">↗</span></button>
          <span className={`decision-status ${candidate.status === 'scheduled' ? '' : 'is-blocked'}`}>{statusLabel[candidate.status]}</span>
          <span className="decision-identity">{candidate.damage_source === 'historical ARCOS replay' ? 'Spatial association · provisional identity' : 'Exact source asset · declared damage'}</span>
          <dl className="decision-candidate-metrics"><div><dt>Dependent premises</dt><dd>{format(candidate.dependent_premises)}</dd></div><div><dt>Conditional stage release</dt><dd>{format(candidate.potential_release_at_stage)}</dd></div><div><dt>Total person-hours</dt><dd>{format(candidate.total_person_hours)}</dd></div><div><dt>Potential releases / total person-hour</dt><dd>{format(candidate.release_per_total_person_hour)}</dd><small>Includes modeled access work</small></div></dl>
          <p className="decision-prerequisite">{candidate.status === 'evidence_unavailable' ? 'Dependency ordering unavailable until complete evidence is restored.' : candidate.prerequisite_ids.length ? `Requires: ${candidate.prerequisite_ids.map(label).join(', ')}.` : 'Independent of the other declared repair candidates.'}</p>
          <CandidateEvidence candidate={candidate} />
        </article>)}
      </div>

      {chosen && <section className="decision-geography" aria-labelledby="decision-geography-title"><div><span className="eyebrow">SELECTED IMPACT</span><h3 id="decision-geography-title">{chosen.label}</h3><p>{chosen.dependent_premises === null ? 'The complete dependent count is unavailable; unresolved source evidence is retained.' : `${format(chosen.dependent_premises)} distinct premises on fully validated source paths.`}</p><p className="fine muted">Selecting a candidate changes the map, while the plan continues to include all declared damage.</p><p className="fine muted">{chosen.critical_proxies.length ? 'Critical-facility context is a spatial proxy; it does not prove a facility depends on this asset.' : 'No verified critical-facility electrical dependency is asserted.'}</p></div><ImpactMap candidate={chosen} /></section>}

      <section className="decision-schedule" aria-labelledby="decision-schedule-title"><div className="section-heading"><div><span className="eyebrow">DEPENDENCIES + AVAILABLE CREWS</span><h3 id="decision-schedule-title">Conditional work plan</h3></div><span className="small-badge">{current.crew_count} {current.crew_count === 1 ? 'crew' : 'crews'} · {current.crew_size} people each</span></div>
        <p className="fine muted">Crew count opens independent work in parallel. People per crew change the ideal contribution boundary. Neither assumption removes upstream prerequisites or unknown clearance.</p>
        <div className="decision-lanes">{Array.from({ length: current.crew_count }, (_, index) => index + 1).map(crew => <div className="decision-lane" key={crew}><h4>Crew {crew}</h4><ol>{current.tasks.filter(task => task.crew === crew).map(task => <li key={task.candidate_id}><strong>{label(task.candidate_id)}</strong><span>Start {hours(task.start_hours)}</span><span>Finish {hours(task.display_finish_hours)}</span></li>)}</ol>{!current.tasks.some(task => task.crew === crew) && <p className="muted fine">No eligible work assigned in this scenario.</p>}</div>)}</div>
        {current.milestones.length > 0 && <div className="decision-table-scroll"><table className="decision-milestones"><caption>Premises conditionally released from declared damage</caption><thead><tr><th scope="col">Completed repair</th><th scope="col">Elapsed scenario</th><th scope="col">Additional</th><th scope="col">Cumulative</th></tr></thead><tbody>{current.milestones.map((milestone, index) => <tr key={index}><th scope="row">{milestone.candidate_ids.map(label).join(' + ')}</th><td>{hours(milestone.display_hours)}</td><td>{format(milestone.additional_premises)}</td><td>{format(milestone.cumulative_premises)}</td></tr>)}</tbody></table></div>}
        {!current.completion_hours && <p className="decision-unavailable">Full completion is unavailable while a required repair is blocked or lacks evidence. Scheduled work could release {format(current.scheduled_release_potential)} premises from declared damage; this does not confirm restoration.</p>}
      </section>

      <section className="decision-explanation" aria-labelledby="decision-ask-title"><span className="eyebrow">EXPLAIN THIS DECISION</span><h3 id="decision-ask-title">Ask GridGuide about this plan</h3><div className="explanation-questions">{questions.map(item => <button key={item} type="button" aria-pressed={question === item} onClick={() => void ask(item)}>{item}</button>)}</div>
        <div aria-live="polite" aria-atomic="true" aria-busy={answerPending} data-testid="decision-explanation">{answerPending && <p role="status">Preparing an explanation bound to this plan…</p>}{answer && <div className="decision-answer"><span className="small-badge">{answer.mode === 'ai_assisted' ? 'AI-assisted explanation' : answer.mode === 'unsupported' ? 'Outside verified scope' : 'Standard explanation'}</span><p>{answer.answer}</p><ul>{answer.supporting_factors.map(factor => <li key={factor.id}>{factor.text}</li>)}</ul><p className="fine muted">{answer.uncertainty_note}</p></div>}{answerFailed && <div role="status"><p>The explanation service is unavailable. The validated plan and evidence remain available.</p><button type="button" onClick={() => question && void ask(question)}>Retry explanation</button></div>}</div>
      </section>

      <details className="decision-audit"><summary>Source coverage, assumptions & limitations</summary><p>Indexed source paths: {format(current.coverage.indexed_paths)}. Fully validated paths: {format(current.coverage.verified_paths)}. Paths with unresolved evidence: {format(current.coverage.unresolved_paths)}.</p><p>Complete physical reverse dependencies: {format(current.coverage.supported_physical_reverse_assets)} assets ({format(current.coverage.transformer_reverse_assets)} transformers and {format(current.coverage.fuse_reverse_assets)} fuses). Unknown membership is withheld, never reported as zero.</p><p>Historical ARCOS records: {format(current.coverage.arcOS_records)}. Spatial candidates with complete reverse evidence: {format(current.coverage.complete_spatial_candidates)}. Spatial associations do not establish confirmed damage identity.</p><ul>{current.policy.map(policy => <li key={policy}>{policy}</li>)}</ul><dl>{current.evidence.map((item, index) => <div key={index}><dt>{item.input_or_rule} <span className="small-badge">{item.classification}</span></dt><dd>{item.detail}</dd></div>)}</dl><ul>{current.limitations.map(limit => <li key={limit}>{limit}</li>)}</ul></details>
    </>}
  </section>;
}
