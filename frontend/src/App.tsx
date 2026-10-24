import { useCallback, useEffect, useRef, useState } from 'react';
import { getAnalysis, getLocations } from './api';
import { CustomerJourney } from './CustomerJourney';
import { GeographicContext } from './GeographicContext';
import { AskGridGuide } from './AskGridGuide';
import type { Access, Analysis, Evaluation, Location } from './api';

const options: { value: NonNullable<Access>; title: string; detail: string }[] = [
  { value: 'clear', title: 'Clear', detail: 'Worksites are accessible' },
  { value: 'restricted', title: 'Restricted', detail: 'Extra access work is needed' },
  { value: 'blocked', title: 'Blocked', detail: 'Access must be cleared first' },
];
const format = (value: number) => new Intl.NumberFormat('en-US', { maximumFractionDigits: 3 }).format(value);

function GridMark() {
  return <svg viewBox="0 0 32 32" fill="none" aria-hidden="true"><path d="M17 3 5 18h10l-1 11 13-16H17l1-10Z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" /></svg>;
}

function Topology({ location }: { location: Location }) {
  const nodes = [{ alias: location.alias, title: 'Customer', subtitle: location.label },
    ...location.upstream_assets.map(asset => ({ alias: asset.alias,
      title: asset.kind === 'Distribution' ? 'Distribution transformer' : asset.kind,
      subtitle: asset.resolution === 'abstract_circuit_terminal' ? 'Abstract supply terminal' : 'Verified equipment' }))];
  return <section className="panel topology" aria-labelledby="topology-title">
    <div className="section-heading"><div><span className="eyebrow">YOUR GRID CONTEXT</span><h2 id="topology-title">Connected to your location</h2></div><span className="small-badge">Verified path</span></div>
    <p className="muted">Follow your location’s dependencies upstream.</p>
    <ol className="path" aria-label="Upstream dependency path">
      {nodes.map((node, index) => <li key={node.alias}>
        <span className="node-symbol" aria-hidden="true">{index === 0 ? '⌂' : index === nodes.length - 1 ? '↥' : '◇'}</span>
        <div><strong>{node.title}</strong><span>{node.subtitle}</span></div>
        {index < nodes.length - 1 && <span className="path-arrow" aria-hidden="true">→</span>}
      </li>)}
    </ol>
    <p className="diagram-note">Dependency diagram · not a geographic map</p>
    {location.topology_warnings.map(warning => <p className="muted fine" key={warning.code}>{warning.message}</p>)}
  </section>;
}

export function App() {
  const [location, setLocation] = useState<Location | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [previousResult, setPreviousResult] = useState<Evaluation | null>(null);
  const [selected, setSelected] = useState<NonNullable<Access>>('clear');
  const [pending, setPending] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [bootAttempt, setBootAttempt] = useState(0);
  const revision = useRef(0);
  const active = useRef<AbortController | null>(null);
  const confirmed = useRef<Evaluation | null>(null);

  const analyze = useCallback(async (alias: string, access: NonNullable<Access>) => {
    const requestRevision = ++revision.current;
    active.current?.abort();
    const controller = new AbortController();
    active.current = controller;
    setSelected(access);
    setPending(true);
    setError(null);
    const previous = confirmed.current;
    try {
      const response = await getAnalysis({ location_alias: alias, access, scenario_revision: requestRevision,
        previous: previous ? { access: previous.simulated_inputs.access, scenario_revision: previous.scenario_revision } : null,
      }, controller.signal);
      if (requestRevision !== revision.current || controller.signal.aborted) return;
      if (response.result.scenario_revision !== requestRevision || response.result.simulated_inputs.access !== access ||
          response.result.location.alias !== alias || response.customer_journey.result_id !== response.result.result_id || (previous && response.comparison?.before_result_id !== previous.result_id)) {
        throw new Error('The analysis response did not match your selection. Please try again.');
      }
      setPreviousResult(previous);
      confirmed.current = response.result;
      setAnalysis(response);
      setPending(false);
    } catch (failure) {
      if (requestRevision !== revision.current || controller.signal.aborted) return;
      setError(failure instanceof Error && failure.name !== 'TimeoutError' ? failure.message : 'The analysis service took too long to respond. Please try again.');
      setPending(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setPending(true);
    setError(null);
    getLocations(controller.signal).then(locations => {
      if (controller.signal.aborted) return;
      if (!locations.length) throw new Error('No verified demo location is available.');
      setLocation(locations[0]);
      void analyze(locations[0].alias, 'clear');
    }).catch(() => {
      if (!controller.signal.aborted) {
        setError('We could not load your demo location. Check that the analysis service is running and try again.');
        setPending(false);
      }
    });
    return () => { controller.abort(); active.current?.abort(); };
  }, [analyze, bootAttempt]);

  const result = analysis?.result;
  const current = !pending && !error ? result : undefined;
  const range = current?.restoration.display_hours;
  const comparison = current ? analysis?.comparison : null;
  const causeIds = new Set(comparison?.changes.flatMap(change => change.cause_factor_ids) ?? []);
  const causes = current?.restoration.factors.filter(factor => causeIds.has(factor.id)) ?? [];
  const risk = result?.risk;
  const retry = () => location ? void analyze(location.alias, selected) : setBootAttempt(attempt => attempt + 1);

  return <>
    <a className="skip-link" href="#main">Skip to analysis</a>
    <div className="utility-bar"><span>Customer outage information</span><span>Demo environment</span></div>
    <header className="site-header"><div className="header-inner">
      <a className="brand" href="/" aria-label="GridGuide home"><span className="brand-mark"><GridMark /></span>GridGuide</a>
      <nav className="customer-nav" aria-label="Customer navigation"><a href="#main" aria-current="page">Outage status</a><a href="#geography-title">Grid context</a><a href="#customer-updates">Alerts & preparation</a></nav>
    </div></header>
    <div className="breadcrumb"><span>GridGuide</span><span aria-hidden="true">/</span><span>Outage status</span></div>

    <main id="main">
      <div className="intro"><div><span className="eyebrow">OUTAGE STATUS</span>
        <h1>Your outage & restoration outlook</h1><p>Explore how access conditions affect a possible restoration.</p></div>
        <div className="location-chip"><span className="location-icon" aria-hidden="true">⌖</span><div><strong>{location?.label ?? 'Loading location…'}</strong><span>Anonymized customer · verified AEP data</span></div></div>
      </div>

      {error && <div className="error-panel" role="alert"><div><strong>Analysis unavailable</strong><p>{error}</p></div><button onClick={retry}>Try again</button></div>}
      <div className="results-grid">
        <section className="panel risk-panel" aria-labelledby="risk-title">
          <span className="eyebrow">OUTAGE RISK</span><div className="risk-heading"><h2 id="risk-title" data-testid="risk-band">{risk?.band ?? (pending ? 'Loading…' : 'Unavailable')}</h2><span className="risk-caption">Concern under this scenario</span></div>
          <p className="confidence">Predictive confidence: <strong>{risk?.predictive_confidence.toLowerCase() ?? (pending ? 'pending' : 'unavailable')}</strong></p>
          <details className="risk-details"><summary>What contributes to this risk?</summary><ul className="risk-factors">{risk?.factors.map(factor => <li key={factor.id}><div><strong>{factor.label}</strong><span>{typeof factor.value === 'boolean' ? (factor.value ? 'Evidence present in the historical extract' : 'No evidence in this extract') : String(factor.value ?? 'Unknown')}</span></div><span className="points">{factor.contribution_points == null ? '—' : `+${factor.contribution_points}`}</span></li>)}</ul>
          <p className="muted fine">{risk?.limitations[0] ?? 'Risk factors will appear after the verified analysis loads.'}</p></details>
        </section>

        <section className={`restoration-panel ${current?.restoration.status === 'pending_clearance' ? 'blocked' : ''}`} aria-labelledby="restoration-title" aria-busy={pending}>
          <div className="restoration-top"><span className="eyebrow" id="restoration-title">RESTORATION OUTLOOK</span><span className="access-badge">{selected} access</span></div>
          <div className="estimate" role="status" aria-live="polite" aria-atomic="true" data-testid="restoration-result">
            {pending ? <><h2 className="state-title">Updating estimate<span className="loading-dots" aria-hidden="true">…</span></h2><p>Calculating the {selected} access scenario.</p></> : error ? <><h2 className="state-title">Estimate unavailable</h2><p>Reconnect to the analysis service to update this scenario.</p></> : range ? <><h2 className="range">{format(range.lower)}–{format(range.upper)} <span>{current?.restoration.unit}</span></h2><p>From when an assigned crew begins its response</p></> : <><h2 className="state-title">Estimate unavailable</h2><p>{current?.restoration.status === 'pending_clearance' ? 'Pending access clearance' : 'Required information is missing'}</p></>}
          </div>
          <div className="estimate-note"><strong>Model-based provisional estimate · not an official live AEP ETR</strong><p>{result?.restoration.limitations[0] ?? 'Labor-hour interpretation uses a disclosed provisional assumption.'}</p></div>
          {current?.restoration.missing_inputs.length ? <p className="blocked-note">{current.restoration.missing_inputs.map(input => input.replaceAll('_', ' ')).join(' · ')}</p> : null}
        </section>
      </div>

      <div className="scenario-label"><span className="small-badge">SIMULATED SCENARIO</span><p>Explore a repair scenario. Current utility outage status and official AEP restoration times are not connected.</p></div>

      <section className="panel access-panel" aria-labelledby="access-title">
        <div><span className="eyebrow">RESTORATION DETAILS</span><h2 id="access-title">What may affect restoration?</h2><p className="muted">Worksite access can affect when repairs can finish. Explore the conditions below.</p></div>
        <fieldset className="access-options"><legend className="sr-only">Repair access</legend>
          {options.map(option => <label key={option.value} className={`access-option ${selected === option.value ? 'selected' : ''}`}>
            <input type="radio" name="access" value={option.value} checked={selected === option.value} disabled={!location}
              onChange={() => location && void analyze(location.alias, option.value)} />
            <span><strong>{option.title}</strong><small>{option.detail}</small></span>
          </label>)}
        </fieldset>
      </section>

      <section className="panel change-panel" aria-labelledby="change-title" aria-busy={pending}>
        <div className="change-heading"><span className="change-icon" aria-hidden="true">↗</span><div><span className="eyebrow">SCENARIO UPDATE</span><h2 id="change-title">Why the outlook changed</h2></div><span className="small-badge">Model-generated update</span></div>
        {comparison && previousResult && comparison.before_result_id === previousResult.result_id && <div className="outlook-update" data-testid="outlook-update">
          <strong>Restoration outlook updated</strong>
          <div className="range-transition"><div><span>{previousResult.simulated_inputs.access} access</span><b>{previousResult.restoration.display_hours ? `${format(previousResult.restoration.display_hours.lower)}–${format(previousResult.restoration.display_hours.upper)} hours` : 'Estimate unavailable'}</b></div><span aria-hidden="true">→</span><div><span>{current?.simulated_inputs.access} access</span><b>{range ? `${format(range.lower)}–${format(range.upper)} hours` : 'Estimate unavailable'}</b></div></div>
          <p>Model comparison · access is the only changed input.</p>
        </div>}
        <div role="status" aria-live="polite" data-testid="change-explanation">
          {pending ? <p className="muted">Updating the comparison with your last completed scenario…</p> : error ? <p className="muted">The comparison will return when analysis is available.</p> : comparison ? <p className="explanation">{comparison.explanation}</p> : <p className="muted">Choose Restricted or Blocked above to compare with this scenario. The explanation will show which calculated factors changed.</p>}
        </div>
        {causes.length > 0 && <ul className="cause-list">{causes.map(factor => <li key={factor.id}><span>{factor.label}</span><strong>{factor.value == null ? 'Unknown' : String(factor.value)}{factor.unit ? ` ${factor.unit.replaceAll('_', ' ')}` : ''}</strong></li>)}</ul>}
      </section>

      {current && analysis && <AskGridGuide key={current.result_id} analysis={analysis} previous={previousResult} />}
      {location && <GeographicContext locationAlias={location.alias} />}
      {location && <Topology location={location} />}
      {result && <details className="panel assumptions"><summary>What this scenario assumes <span>Scope, sources & limitations</span></summary>
        <div className="assumptions-body"><div><h3>Declared repair scope</h3><ul>{result.restoration.labor_contributions.map(work => <li key={work.task_id}>{work.quantity} × {work.recipe.replaceAll('-', ' ')}<small>Workbook: {work.source_refs.join('; ')}</small></li>)}</ul><p className="muted">Storm concern level {result.simulated_inputs.storm_level}; {result.simulated_inputs.crew_count} available reference crew. Damage and access are simulated inputs.</p></div>
        <div><h3>Model assumptions</h3><ul>{result.assumptions.map(assumption => <li key={assumption.id}>{assumption.description}<small>Assumed value: {String(assumption.value)}</small></li>)}</ul></div>
        <div><h3>Limits to the estimate</h3><ul>{result.restoration.limitations.slice(1).map(limit => <li key={limit}>{limit}</li>)}</ul></div></div>
      </details>}
      <section className="customer-updates" id="customer-updates" aria-labelledby="updates-title" aria-busy={pending}>
        <h2 id="updates-title">Preparation & alerts</h2>
        {current && analysis ? <CustomerJourney key={current.scenario_revision} journey={analysis.customer_journey} /> : <p className="journey-pending" role="status">{pending ? 'Updating preparation and communication previews…' : 'Preparation and communication previews are unavailable. Use Try again above to reconnect.'}</p>}
      </section>
      <footer><span>GridGuide</span><p>Verified challenge data · modeled scenarios · no live utility connection</p></footer>
    </main>
  </>;
}
