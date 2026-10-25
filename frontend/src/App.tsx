import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { CustomerJourney } from './CustomerJourney';
import { GeographicContext } from './GeographicContext';
import { AskGridGuide } from './AskGridGuide';
import { RestorationDecision } from './RestorationDecision';
import { RepairEffort, RestorationSequence } from './RestorationEvidence';
import { RestorationRange } from './RestorationRange';
import { useCustomerAnalysis } from './useCustomerAnalysis';
import { Icon } from './Icon';
import type { IconName } from './Icon';
import type { Location, Need } from './api';

type Page = 'overview' | 'prepare' | 'grid';
const pages: { id: Page; label: string }[] = [{ id: 'overview', label: 'Overview' }, { id: 'prepare', label: 'Prepare & alerts' }, { id: 'grid', label: 'Grid insights' }];
const pageFromHash = (): Page => pages.some(p => p.id === window.location.hash.slice(1)) ? window.location.hash.slice(1) as Page : 'overview';
const pageHeading: Record<Page, string> = { overview: 'overview-title', prepare: 'prepare-page-title', grid: 'grid-page-title' };
const accessOptions = [{ value: 'clear', title: 'Clear', detail: 'Worksites accessible' }, { value: 'restricted', title: 'Restricted', detail: 'Extra access work' }, { value: 'blocked', title: 'Blocked', detail: 'Clearance needed first' }] as const;
const needsOptions: { value: Need; label: string; icon: IconName }[] = [
  { value: 'medical', label: 'Powered medical equipment / medical need', icon: 'medical' },
  { value: 'accessibility', label: 'Accessibility assistance', icon: 'accessibility' },
  { value: 'critical_responsibility', label: 'Critical responsibility', icon: 'critical' },
];

// Select verbatim server sentences/clauses for the preview; never compare or
// reinterpret numerical endpoints here. The full message stays in the existing
// model disclosure, and unknown server wording is shown without abbreviation.
function comparisonPreview(message: string): string[] {
  const sentences = message.split(/(?<=[.!?])\s+(?=[A-Z])/);
  if (!/^(Access |Crew size )/.test(sentences[0] ?? '')) return [message];
  return sentences.filter(sentence => !sentence.startsWith('The conditional outlook is ')
    && !sentence.startsWith('Actual crew efficiency is unknown;'))
    .map(sentence => sentence.startsWith('Repair effort remains ') ? sentence.split(';')[0] + '.' : sentence);
}

function Topology({ location }: { location: Location }) {
  const nodes = [{ alias: location.alias, title: 'Your location', subtitle: location.label, icon: 'home' as IconName },
    ...location.upstream_assets.map(asset => ({ alias: asset.alias, title: asset.kind === 'Distribution' ? 'Serving transformer' : asset.kind === 'Circuit Breaker' ? 'Supply terminal' : 'Upstream fuse',
      subtitle: asset.resolution === 'abstract_circuit_terminal' ? 'Abstract · no map position' : 'Source identity verified', icon: (asset.kind === 'Distribution' ? 'transformer' : asset.kind === 'Fuse' ? 'fuse' : 'network') as IconName }))];
  return <section className="topology" aria-labelledby="topology-title">
    <div className="section-heading"><div><span className="eyebrow">Source-derived dependencies</span><h2 id="topology-title" tabIndex={-1}>What supplies your location?</h2></div><Icon name="network"/></div>
    <ol className="dependency-path" aria-label="Upstream dependency path">{nodes.map(node => <li key={node.alias}>
      <span className="dependency-symbol"><Icon name={node.icon}/></span><strong>{node.title}</strong><span>{node.subtitle}</span>
      {location.dependency_edges.some(edge => edge.downstream_alias === node.alias) && <span className="dependency-link"><Icon name="arrow"/><small>depends on</small></span>}
    </li>)}</ol>
    <p className="fine">Approximate source topology · a dependency schematic, not a geographic line route.</p>
    {location.topology_warnings.map(warning => <p className="fine" key={warning.code}>{warning.message}</p>)}
  </section>;
}

export function App() {
  const customer = useCustomerAnalysis();
  const { location, locations, current, previousResult, settings, pending, error } = customer;
  const result = current?.result;
  const journey = current?.customer_journey;
  const [page, setPage] = useState<Page>(pageFromHash);
  const [gridVisited, setGridVisited] = useState(page === 'grid');
  const [explore, setExplore] = useState(false);
  const [mapOpen, setMapOpen] = useState(false);
  const [riskOpen, setRiskOpen] = useState(false);
  const [checkedActions, setCheckedActions] = useState<Set<string>>(new Set());
  const [draftLocation, setDraftLocation] = useState('');
  const locationDetails = useRef<HTMLDetailsElement>(null);
  const declarationFields = useRef<HTMLFieldSetElement>(null);
  const declarationFocus = useRef<Need | 'clear' | null>(null);
  const focusTarget = useRef<string | null>(null);
  const initialNavigation = useRef(true);
  const focusSection = (id: string) => window.requestAnimationFrame(() => {
    const target = document.getElementById(id); target?.focus({ preventScroll: true }); target?.scrollIntoView({ block: 'start' });
  });
  useEffect(() => {
    // Route history always starts at page top; native history restoration must
    // not compete with the route's focus/scroll handling below.
    const restoration = window.history.scrollRestoration;
    window.history.scrollRestoration = 'manual';
    const onHash = () => { if (!window.location.hash || pages.some(p => p.id === window.location.hash.slice(1))) setPage(pageFromHash()); };
    window.addEventListener('hashchange', onHash);
    return () => { window.removeEventListener('hashchange', onHash); window.history.scrollRestoration = restoration; };
  }, []);
  useLayoutEffect(() => {
    if (page === 'grid') setGridVisited(true);
    if (initialNavigation.current) { initialNavigation.current = false; return; }
    const target = focusTarget.current;
    focusTarget.current = null;
    // Explicit evidence/communication links retain their section destination.
    if (target) {
      const frame = focusSection(target);
      return () => window.cancelAnimationFrame(frame);
    }
    document.getElementById(pageHeading[page])?.focus({ preventScroll: true });
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
  }, [page]);
  useEffect(() => { if (location) setDraftLocation(location.alias); }, [location]);
  // Results are withdrawn during a request. Restore keyboard position when that
  // replacement remounts its declaration controls, unless the user moved on.
  useEffect(() => {
    const moved = () => { declarationFocus.current = null; };
    const focused = (event: FocusEvent) => {
      if (event.target !== document.body && !declarationFields.current?.contains(event.target as Node)) moved();
    };
    document.addEventListener('pointerdown', moved);
    document.addEventListener('keydown', moved);
    document.addEventListener('focusin', focused);
    return () => {
      document.removeEventListener('pointerdown', moved);
      document.removeEventListener('keydown', moved);
      document.removeEventListener('focusin', focused);
    };
  }, []);
  useEffect(() => {
    if (pending) return;
    const target = declarationFocus.current;
    declarationFocus.current = null;
    if (page === 'prepare' && target && document.activeElement === document.body) {
      declarationFields.current?.querySelector<HTMLElement>(`[data-declaration="${target}"]`)?.focus({ preventScroll: true });
    }
  }, [pending, page]);
  const navigate = (next: Page, target?: string) => {
    focusTarget.current = target ?? null;
    if (next === page) {
      if (target) focusSection(target);
      else document.getElementById(pageHeading[next])?.focus({ preventScroll: true });
      focusTarget.current = null;
    }
    else window.location.hash = next;
  };
  const showEvidence = (target: 'risk' | 'restoration' | 'preparation' | 'topology') => {
    if (target === 'preparation') { navigate('prepare'); return; }
    if (target === 'risk') setRiskOpen(true);
    if (target === 'restoration') setExplore(true);
    if (target === 'topology') setMapOpen(true);
    navigate('overview', target === 'risk' ? 'risk-title' : target === 'restoration' ? 'restoration-details' : 'customer-map-section');
  };
  const toggleAction = (action: string) => setCheckedActions(old => { const next = new Set(old); if (next.has(action)) next.delete(action); else next.add(action); return next; });
  const declarations = <fieldset className="declared-needs" ref={declarationFields}><legend>Your optional needs</legend>
    <p className="fine">Only what you choose to share. These selections stay in this page session and are not sent to AI.</p>
    {needsOptions.map(need => <label key={need.value}><input type="checkbox" data-declaration={need.value} checked={settings.needs.includes(need.value)} disabled={!location} onChange={event => { if (document.activeElement === event.currentTarget) declarationFocus.current = need.value; customer.toggleNeed(need.value); }}/><Icon name={need.icon}/><span>{need.label}</span></label>)}
    <button className="button button-text" data-declaration="clear" type="button" onClick={event => { if (settings.needs.length) { if (document.activeElement === event.currentTarget) declarationFocus.current = 'clear'; customer.changeSelection({ needs: [] }); } }} disabled={!location}>None / clear declarations</button>
    <p className="fine">User-declared · no need is inferred, no enrollment or contact is created.</p>
  </fieldset>;
  const alertLabel = journey?.alerts.eligible === true ? 'Eligible under prototype rules' : journey?.alerts.eligible === false ? 'In-app information only' : 'Eligibility needs more information';

  return <>
    <a className="skip-link" href="#main">Skip to content</a>
    <header className="site-header"><div className="header-inner">
      <a className="brand" href="#overview" onClick={event => { event.preventDefault(); navigate('overview'); }} aria-label="GridGuide overview"><span className="brand-mark"><Icon name="network"/></span><span><strong>GridGuide</strong><small>AI Outage Concierge</small></span></a>
      <nav className="product-nav" aria-label="Main navigation">{pages.map(item => <a href={'#' + item.id} key={item.id} aria-current={page === item.id ? 'page' : undefined} onClick={event => { event.preventDefault(); navigate(item.id); }}>{item.label}</a>)}</nav>
      <span className="prototype-identity">HackOHI/O 2026<br/>Challenge Prototype</span>
    </div></header>
    <main id="main" tabIndex={-1}>
      <div className="service-location"><div className="location-identity"><Icon name="location"/><div><span className="field-label">Service location</span><strong>{location?.label ?? 'Loading location…'}</strong></div><span className="location-context">Anonymized Virginia challenge data</span></div>
        <details ref={locationDetails} className="location-selector"><summary>Choose location <Icon name="chevron"/></summary><div className="location-options"><h2>Choose your service location</h2><p>Explore a verified, anonymized location from the challenge dataset. Address search is not connected.</p>
          {locations.map(item => <label key={item.alias}><input type="radio" name="service-location" checked={draftLocation === item.alias} onChange={() => setDraftLocation(item.alias)}/><span><strong>{item.label}</strong><small>Source-verified dependencies · Virginia</small></span></label>)}
          <button className="button" type="button" disabled={!locations.length} onClick={() => { const item = locations.find(l => l.alias === draftLocation); if (item) { if (item.alias !== location?.alias) setCheckedActions(new Set()); customer.selectLocation(item); } if (locationDetails.current) { locationDetails.current.open = false; locationDetails.current.querySelector('summary')?.focus({ preventScroll: true }); } }}>Use this location</button>
        </div></details>
      </div>
      <p className="sr-only" role="status" aria-live="polite" aria-atomic="true">{pending ? 'Updating your scenario.' : error ? 'Customer analysis is unavailable.' : result ? 'Customer scenario updated. ' + settings.access + ' access, ' + settings.crewSize + ' people. ' + (result.restoration.display_hours ? result.restoration.display_hours.lower + ' to ' + result.restoration.display_hours.upper + ' conditional elapsed hours.' : 'Restoration range unavailable.') : ''}</p>
      <section className="product-page overview-page" hidden={page !== 'overview'} aria-labelledby="overview-title">
        <div className="page-intro"><div><span className="eyebrow">A little clarity. A better plan.</span><h1 id="overview-title" tabIndex={-1}>Your storm outlook</h1></div><p className="live-status"><Icon name="unknown"/><span>Live outage status isn’t connected.<small>This outlook explores a modeled storm scenario.</small></span></p></div>
        {error && <div className="error-panel" role="alert"><Icon name="unknown"/><div><h2>Analysis unavailable</h2><p>{error}</p></div><button className="button" onClick={customer.retry}>Try again</button></div>}
        <div className="outlook-grid" aria-busy={pending}>
          <section className={'risk-summary ' + (result?.risk.band === null ? 'risk-unknown' : '')} aria-labelledby="risk-title">
            <div className="result-heading"><Icon name="storm"/><h2 id="risk-title" tabIndex={-1}>Could I lose power?</h2></div>
            <div className="risk-heading"><strong data-testid="risk-band">{result?.risk.band ?? (pending ? 'Loading…' : 'Unavailable')}</strong><span>{result?.risk.band ? 'Modeled concern' : 'Risk estimate'}</span></div>
            <p className="confidence">Confidence in prediction: <strong>{result?.risk.predictive_confidence.toLowerCase() ?? 'unavailable'}</strong></p>
            <p className="risk-meaning">{result?.risk.band === null ? 'There is not enough verified evidence to assign a risk band. Your other results are still available.' : 'Modeled concern, not an outage prediction.'}</p>
            <details className="risk-details" open={riskOpen} onToggle={event => setRiskOpen(event.currentTarget.open)}><summary>{result?.risk.band === null ? 'Why is risk unavailable?' : 'What informs this outlook?'}<Icon name="chevron"/></summary>
              <p className="fine">Ordinal model score: {result?.risk.score ?? 'unavailable'}. This is not an outage probability.</p>
              <ul className="risk-factors">{result?.risk.factors.map(factor => <li key={factor.id}><strong>{factor.label}</strong><span>{typeof factor.value === 'boolean' ? factor.value ? 'Historical evidence present' : 'No evidence in this extract' : String(factor.value ?? 'Unknown')}{factor.unit ? ` ${factor.unit}` : ''}</span><small>{factor.classification}{factor.contribution_points != null ? ` · ${factor.contribution_points} model points` : ''}</small>{factor.source_refs.length > 0 && <small>Source: {factor.source_refs.join('; ')}</small>}</li>)}</ul>
              {result?.risk.missing_inputs.map(input => <p key={input} className="missing-evidence">Missing: {input.replaceAll('_', ' ')}</p>)}
              <p className="fine">{result?.risk.limitations[0] ?? 'Factors will appear after analysis loads.'}</p>
              {current && result?.risk.band === 'HIGH' && <AskGridGuide key={'risk-' + result.result_id} analysis={current} previous={previousResult} context="risk" anchorPrefix="risk" onEvidence={showEvidence}/>}
            </details>
          </section>
          <section className={'restoration-summary ' + (result?.restoration.display_hours === null ? 'range-unavailable' : '')} aria-labelledby="restoration-title">
            <div className="result-heading"><Icon name="clock"/><h2 id="restoration-title">If an outage occurs</h2><span className="scenario-access">{settings.access} access</span></div>
            {result ? <RestorationRange result={result}/> : <div className="result-placeholder" data-testid="restoration-result"><strong>{pending ? 'Updating your outlook…' : 'Estimate unavailable'}</strong><p>{pending ? 'Using the verified scenario inputs.' : 'Retry the analysis to see your outlook.'}</p></div>}
            <div className="restoration-footer"><p>Modeled range · not a live AEP estimate</p><button className="button button-text" type="button" disabled={!location} onClick={() => { setExplore(true); focusSection('restoration-details'); }}>Explore this range <Icon name="arrow"/></button></div>
          </section>
        </div>
        <div className="next-steps" aria-busy={pending}>
          <section className="next-action"><span className="action-symbol"><Icon name="check"/></span><div><span className="field-label">Start here</span><h2>{journey?.preparation.actions[0] ?? (pending ? 'Preparing your guidance…' : 'Your preparation guidance')}</h2><button className="button" onClick={() => navigate('prepare')}>Prepare now <Icon name="arrow"/></button></div></section>
          <section className="next-alert"><Icon name="alert"/><div><span className="field-label">Your updates</span><h2>{journey ? alertLabel : 'Preview communications'}</h2><p>No notifications are being sent.</p><button className="button button-text" onClick={() => navigate('prepare', 'communications')}>Preview communications <Icon name="arrow"/></button></div></section>
        </div>
        {journey && journey.preparation.declared_actions.length > 0 && <aside className="overview-declared"><Icon name="shield"/><div><strong>Your declared needs are included in preparation.</strong><p>{journey.preparation.declared_actions[0]}</p><button className="button button-text" onClick={() => navigate('prepare')}>Review your support guidance</button></div></aside>}
        <details className="restoration-details" open={explore} onToggle={event => setExplore(event.currentTarget.open)}><summary id="restoration-details"><span><Icon name="crew"/>Explore repair conditions</span><Icon name="chevron"/></summary>
          <div className="details-content"><div className="section-heading"><div><span className="eyebrow">Your location · two declared repairs</span><h2>What changes the range?</h2><p>Explore crew size and access. These scenario controls do not request real crews.</p></div></div>
            <div className="scenario-controls"><fieldset className="crew-options"><legend>People in one assigned crew</legend>{[2, 4, 8].map(people => <label className={settings.crewSize === people ? 'selected' : ''} key={people}><input type="radio" name="crew-size" checked={settings.crewSize === people} disabled={!location} onChange={() => customer.changeSelection({ crewSize: people })}/><Icon name="crew"/><span><strong>{people} people</strong><small>One assigned crew</small></span></label>)}</fieldset>
              <fieldset className="access-options"><legend>Repair access</legend>{accessOptions.map(option => <label className={settings.access === option.value ? 'selected' : ''} key={option.value}><input type="radio" name="access" checked={settings.access === option.value} disabled={!location} onChange={() => customer.changeSelection({ access: option.value })}/><span><strong>{option.title}</strong><small>{option.detail}</small></span></label>)}</fieldset>
            </div>
            <p className="fine">Scenario default: four people. Actual staffing and efficiency are unknown; more people do not guarantee proportional speedup.</p>
            {current && result && <><div className="scenario-comparison" data-testid="outlook-update"><RestorationRange result={result} previous={previousResult} compact/>
              <div data-testid="change-explanation"><h3>{current.comparison ? current.comparison.changed_inputs.length ? 'What changed' : 'Scenario unchanged' : 'Try a scenario'}</h3>{current.comparison ? comparisonPreview(current.comparison.explanation).map((line, index) => <p key={index}>{line}</p>) : <p>Change people or access to compare with your last completed scenario.</p>}</div>
            </div><AskGridGuide key={'restoration-' + result.result_id} analysis={current} previous={previousResult} context="restoration" anchorPrefix="restoration" onEvidence={showEvidence}/>
              <details className="evidence-disclosure"><summary><Icon name="evidence"/>Work, effort & repair dependencies<Icon name="chevron"/></summary><RepairEffort result={result}/><RestorationSequence result={result}/></details>
              <details className="evidence-disclosure"><summary><Icon name="book"/>Model assumptions & limits<Icon name="chevron"/></summary><div className="assumptions-body">{current.comparison && <div className="full-comparison"><h3>Full server comparison</h3><p>{current.comparison.explanation}</p></div>}<ul>{result.assumptions.map(assumption => <li key={assumption.id}><strong>{assumption.classification}</strong><p>{assumption.description}</p><small>Value: {assumption.value === null ? 'Unavailable' : String(assumption.value)}</small></li>)}</ul><ul>{result.restoration.limitations.map(limit => <li key={limit}>{limit}</li>)}</ul></div></details>
            </>}
            {pending && <p className="loading-state">Updating your comparison…</p>}
          </div>
        </details>
        <div className="context-entry"><div><Icon name="network"/><h2>See the reasoning behind your outlook</h2><p>Explore the supplied equipment and approximate dependencies, or compare a separate four-candidate repair scenario.</p></div><button className="button button-secondary" onClick={() => navigate('grid')}>Explore grid insights <Icon name="arrow"/></button></div>
        <details className="customer-map-section" open={mapOpen} onToggle={event => setMapOpen(event.currentTarget.open)}><summary id="customer-map-section"><span><Icon name="location"/>See your grid context</span><Icon name="chevron"/></summary>{mapOpen && location && <div className="details-content"><GeographicContext locationAlias={location.alias}/><Topology location={location}/>{current && <AskGridGuide key={'topology-' + current.result.result_id} analysis={current} previous={previousResult} context="topology" anchorPrefix="topology" onEvidence={showEvidence}/>}</div>}</details>
      </section>
      <section className="product-page prepare-page" hidden={page !== 'prepare'} aria-labelledby="prepare-page-title"><div className="page-intro"><div><span className="eyebrow">A few practical steps</span><h1 id="prepare-page-title" tabIndex={-1}>Prepare & stay informed</h1><p>Make a plan for this scenario. Your checklist stays with you during this visit.</p></div></div>
        {current && journey ? <CustomerJourney key={current.result.scenario_revision} journey={journey} checkedActions={checkedActions} onToggleAction={toggleAction} declarations={declarations} explanation={<AskGridGuide key={'prepare-' + current.result.result_id} analysis={current} previous={previousResult} context="preparation" anchorPrefix="preparation" onEvidence={showEvidence}/>}/> : <><div className="loading-state" role="status"><h2>{pending ? 'Updating preparation and communication previews…' : 'Preparation is unavailable'}</h2>{error && <><p>{error}</p><button className="button" onClick={customer.retry}>Try again</button></>}</div>{declarations}</>}
      </section>
      <section className="product-page grid-page" hidden={page !== 'grid'} aria-labelledby="grid-page-title"><div className="page-intro"><div><span className="eyebrow">Evidence behind the decisions</span><h1 id="grid-page-title" tabIndex={-1}>Grid insights</h1><p>A separate four-candidate repair scenario. Explore dependencies, priorities and available crews.</p></div><span className="scope-note"><Icon name="model"/>This plan is not your personal restoration estimate.</span></div>{gridVisited && <RestorationDecision active={page === 'grid'}/>}</section>
    </main>
    <footer className="site-footer"><div><strong>GridGuide</strong><span>HackOHI/O 2026 Challenge Prototype</span></div><p>Verified challenge data. Modeled scenarios.<br/>No live utility connection or notification delivery.</p><details><summary>Privacy & prototype scope</summary><p>Location data is generalized. Optional needs and checklist selections stay in this page session. No contact information is collected. This is not an official AEP service.</p></details></footer>
  </>;
}
