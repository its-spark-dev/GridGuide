import { useEffect, useRef, useState } from 'react';
import { PublicShell } from './PublicShell';
import { PowerPath } from './PowerPath';
import { Icon } from './Icon';
import { loadFrames, verifyMode } from './offline';
import type { PathFrame } from './offline';
import { frameHash, linkedFrame } from './frameSelection';

function FrameExplanation({ frame }: { frame: PathFrame }) {
  const [question, setQuestion] = useState<'timing' | 'path' | 'risk' | null>(null);
  return <section className="dashboard-explanation" aria-labelledby="ask-title">
    <div className="section-heading"><div><span className="eyebrow">Understand the evidence</span><h2 id="ask-title">Ask GridGuide</h2></div><span className="explanation-badge">Standard explanation</span></div>
    <p>Choose a question about this fictional result. No external AI is required.</p>
    <div className="actions">{([['timing', 'What does this timing mean?'], ['path', 'What is holding up release?'], ['risk', 'Why is risk unavailable?']] as const).map(([id, label]) =>
      <button type="button" key={id} aria-pressed={question === id} onClick={() => setQuestion(id)}>{label}</button>)}</div>
    <div role="status" aria-live="polite" aria-atomic="true" className="standard-answer">
      {question && <><strong>{frame.label} · {frame.step_label}</strong>
        {question === 'timing' && <><p>{frame.completion_hours === null ? 'Full completion is unavailable because unresolved dependencies remain. No finite restoration time can be inferred.' : <>Full modeled completion is {frame.completion_hours} conditional elapsed hours from modeled response start.</>}</p><p>This is a precomputed deterministic schedule assuming one effective worker per crew. It is not a utility ETR, a confidence interval or observed restoration. Real productivity and clearance remain unknown.</p></>}
        {question === 'path' && <><p>Each customer requires every declared repair along its path. The selected milestone reports {frame.released_customers} released and {frame.unresolved_customers} unresolved fictional customers.</p><ul>{frame.customers.map(c => <li key={c.id}>{c.label}: {c.reason}</li>)}</ul></>}
        {question === 'risk' && <p>These fictional definitions have no validated household outage labels or approved concern-band inputs. Outage probability and predictive confidence are unavailable. The evidence-bounded research No-Go remains in force; synthetic repairs cannot establish a prediction.</p>}
        <a href="#dashboard-path">Inspect the dependencies</a></>}
      {!question && <p>Select a question to see an explanation bound to the current milestone.</p>}
    </div>
  </section>;
}

export function PublicDashboard() {
  const [frames, setFrames] = useState<PathFrame[]>([]);
  const [frame, setFrame] = useState<PathFrame | null>(null);
  const [message, setMessage] = useState('Verifying the fictional catalog and Python service…');
  const [pending, setPending] = useState(true);
  const [attempt, setAttempt] = useState(0);
  const revision = useRef(0);
  useEffect(() => {
    const controller = new AbortController(); const rev = ++revision.current;
    const signal = AbortSignal.any([controller.signal, AbortSignal.timeout(10000)]);
    setPending(true); setFrames([]); setFrame(null);
    setMessage('Verifying the fictional catalog and Python service…');
    const disconnect = () => { controller.abort(); setFrames([]); setFrame(null); setPending(false); setMessage('Connection lost. Results are withdrawn. Open the offline preparedness kit if you previously enabled it.'); };
    window.addEventListener('offline', disconnect);
    void (async () => {
      try {
        if (await verifyMode(signal) !== 'synthetic-demo') throw new Error('Unsupported mode');
        const approved = await loadFrames(signal);
        if (controller.signal.aborted || revision.current !== rev) return;
        setFrames(approved); setFrame(linkedFrame(approved, window.location.hash) ?? approved[0]);
        setMessage('Verified fictional examples. Select a scenario or milestone to explore its declared dependencies.');
      } catch { if (!controller.signal.aborted && revision.current === rev) setMessage('Fictional results unavailable: service mode or artifact integrity could not be verified. Generic preparedness remains available.'); }
      finally { if (!controller.signal.aborted && revision.current === rev) setPending(false); }
    })();
    return () => { controller.abort(); window.removeEventListener('offline', disconnect); };
  }, [attempt]);
  useEffect(() => {
    const navigate = () => { const next = linkedFrame(frames, window.location.hash); if (next) setFrame(next); };
    window.addEventListener('hashchange', navigate);
    return () => window.removeEventListener('hashchange', navigate);
  }, [frames]);
  function select(next: PathFrame | undefined) {
    if (!next) return;
    setFrame(next); window.history.replaceState(null, '', frameHash(next));
  }
  const milestones = frames.filter(f => f.scenario_id === frame?.scenario_id);
  return <PublicShell page="overview" mainId="main"><main id="main" tabIndex={-1}>
    <div className="service-location"><div className="location-identity"><Icon name="home"/><div><span className="field-label">Fictional service scenario</span><strong>{frame?.label ?? 'No verified scenario selected'}</strong></div><span className="location-context">Independently authored · no real location</span></div>
      <a className="button button-text" href="#scenario-controls">Choose scenario <Icon name="chevron"/></a></div>
    <section className="product-page overview-page" aria-labelledby="overview-title">
      <div className="page-intro"><div><span className="eyebrow">A little clarity. A better plan.</span><h1 id="overview-title">Your storm outlook</h1></div><p className="live-status"><Icon name="unknown"/><span>A fictional learning scenario.<small>Live outages and utility ETRs aren’t connected.</small></span></p></div>
      <div className="outlook-grid" aria-busy={pending}>
        <section className="risk-summary risk-unknown" aria-labelledby="risk-title"><div className="result-heading"><Icon name="storm"/><h2 id="risk-title">Could I lose power?</h2></div>
          <div className="risk-heading"><strong>Unavailable</strong><span>Household concern band</span></div><p className="confidence">Predictive confidence: <strong>unavailable</strong></p><p className="risk-meaning">Fictional repair scenarios cannot establish your outage risk.</p>
          <details className="risk-details"><summary>Why is risk unavailable?<Icon name="chevron"/></summary><p>No validated outage labels or concern-band inputs exist for this public example. Probability remains unavailable. The original ordinal band remains available only in authorized challenge-local mode; it is not a calibrated prediction.</p></details>
        </section>
        <section className="restoration-summary" aria-labelledby="restoration-title"><div className="result-heading"><Icon name="clock"/><h2 id="restoration-title">How repairs could unfold</h2></div>
          <div className="restoration-value" data-testid="fictional-completion"><strong>{frame ? frame.completion_hours === null ? 'Completion unresolved' : <>{frame.completion_hours} <span>modeled hours</span></> : pending ? 'Loading…' : 'Unavailable'}</strong><p>{frame?.completion_hours != null ? 'Full dependency release from modeled response start.' : 'A finite completion time cannot be stated.'}</p></div>
          <p className="range-limit"><Icon name="unknown"/>Conditional schedule · not a utility restoration estimate</p>
          <div className="restoration-footer"><p>No calibrated uncertainty interval is available.</p><a className="button button-text" href="#scenario-controls">Explore milestones <Icon name="arrow"/></a></div>
        </section>
      </div>
      <section className="next-steps" aria-label="Next steps"><div className="next-action"><span className="action-symbol"><Icon name="shield"/></span><div><h2>A little preparation can make an outage easier to manage.</h2><a className="button" href={'/preparedness/' + (frame ? frameHash(frame) : '')}>Prepare now <Icon name="arrow"/></a></div></div>
        <div className="next-alert"><Icon name="network"/><div><h2>See the decisions behind repair order.</h2><p>Compare four policies in a separate fictional operator exercise.</p><a className="button button-text" href="/operator/">Explore grid insights <Icon name="arrow"/></a></div></div></section>
      <section id="scenario-controls" className="dashboard-controls" aria-labelledby="controls-title"><div className="section-heading"><div><span className="eyebrow">Explore a declared scenario</span><h2 id="controls-title">Change the example. Follow the repairs.</h2><p>Every milestone is prepared and validated in Python. Changing the selection plays back an approved result.</p></div><Icon name="model"/></div>
        <p role="status" className="fine">{message}</p>
        <div className="scenario-picker"><label>Fictional scenario<select disabled={!frames.length} value={frame?.scenario_id ?? ''} onChange={e => select(frames.find(f => f.scenario_id === e.target.value && f.step === 0))}><option value="" disabled>Select a verified example</option>{frames.filter(f => f.step === 0).map(f => <option key={f.scenario_id} value={f.scenario_id}>{f.label}</option>)}</select></label>
          <label>Prepared milestone<select disabled={!frame} value={frame?.step ?? 0} onChange={e => select(milestones.find(f => f.step === Number(e.target.value)))}>{milestones.map(f => <option key={f.step} value={f.step}>{f.step_label}</option>)}</select></label></div>
        {!frame && !pending && <button type="button" onClick={() => setAttempt(n => n + 1)}>Retry fictional results</button>}
        <details className="control-limits"><summary>Crew size, access and uncertainty</summary><p>These approved frames assume one effective worker per crew. Staffing and access are fixed in each fictional definition; custom people-per-crew and access recalculation are unavailable here. Select the blocked-access example to inspect unknown clearance. Operator cases separately include declared one/two-crew schedules.</p><p>This is deterministic playback, not the G5 fixed-timetable delay simulation or adaptive dispatch. G5 reported 195 stable and 15 unstable combinations, without empirical calibration. No simulation quantiles are presented here.</p></details>
        {frame && <section className="milestone-card" aria-label="Selected fictional result"><strong>{frame.label} · {frame.step_label}</strong><p>{frame.elapsed_hours} conditional elapsed hours · {frame.released_customers} fictional customers with completed dependencies · {frame.unresolved_customers} unresolved.</p><ol className="milestone-rail" aria-label="Prepared repair timeline">{milestones.map(f => <li key={f.step}><button type="button" aria-pressed={f.step === frame.step} onClick={() => select(f)}><strong>{f.elapsed_hours} h</strong><span>{f.step_label}</span></button></li>)}</ol></section>}
      </section>
      <section id="dashboard-path" className="dashboard-path" aria-label="Fictional grid context"><div className="geography-unavailable"><Icon name="location"/><p><strong>Geographic context is unavailable in this public example.</strong> These are declared dependencies, not a geographic map. No real or invented coordinates are used.</p></div>{frame ? <PowerPath frame={frame}/> : <p>Verify a fictional scenario to inspect its power path.</p>}</section>
      {frame && <><FrameExplanation key={frame.result_fingerprint} frame={frame}/><details className="dashboard-provenance"><summary>Assumptions, versions and evidence</summary><p>Independently authored fiction · revision {frame.scenario_revision}. Model {frame.model_version}. Policy {frame.policy_id}. The fixed release/person-hour baseline remains the default. CP-SAT is optional and experimental in Grid insights.</p><p className="fingerprint">Input: {frame.input_fingerprint}<br/>Result: {frame.result_fingerprint}</p><p>Topology and effort: scenario assumptions. Scheduling: prototype policy. Measured productivity, observed restoration and household probabilities: unavailable. Hashes establish internal consistency, not authenticity.</p></details></>}
    </section>
  </main></PublicShell>;
}
