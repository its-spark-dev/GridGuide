import { Icon, type IconName } from './Icon';
import type { Candidate, Plan } from './useRestorationPlan';

const number = (value: number | null) => value === null ? 'Unavailable' : new Intl.NumberFormat('en-US', { maximumFractionDigits: 3 }).format(value);
type Classification = Plan['evidence'][number]['classification'];
export const hasEvidence = (plan: Plan, rule: string, classification: Classification) =>
  plan.evidence.some(item => item.input_or_rule === rule && item.classification === classification);

/** Source roles come from the public plan ledger; no dataset counters or joins. */
export function ScenarioSources({ plan }: { plan: Plan }) {
  const source = hasEvidence(plan, 'topology and workbook rates', 'source-derived');
  const historical = hasEvidence(plan, 'historical damage evidence', 'source-derived') && plan.candidates.some(c => c.damage_source === 'historical ARCOS replay');
  const critical = hasEvidence(plan, 'facility match gates', 'prototype policy') && plan.candidates.some(c => c.critical_proxies.length > 0);
  const ranked = hasEvidence(plan, 'ranking and serial ancestry', 'prototype policy');
  const items: { icon: IconName; label: string; role: string; classification: Classification; spatial?: boolean }[] = [
    { icon: 'evidence', label: 'Historical ARCOS damage', role: historical ? 'Observation for a spatial replay' : 'Historical context unavailable', classification: historical ? 'source-derived' : 'unavailable', spatial: historical },
    { icon: 'fuse', label: 'GIS equipment', role: source ? 'Typed source asset identity' : 'Source identity unavailable', classification: source ? 'source-derived' : 'unavailable' },
    { icon: 'network', label: 'Premises & upstream paths', role: source ? 'Approximate customer dependencies' : 'Dependency evidence unavailable', classification: source ? 'source-derived' : 'unavailable' },
    { icon: 'book', label: 'AEP labor workbook', role: source ? 'Installation + removal rates' : 'Labor source unavailable', classification: source ? 'source-derived' : 'unavailable' },
    { icon: 'spatial', label: 'Critical-service context', role: critical ? 'Spatial proxy; electrical link unverified' : 'Supported spatial proxy unavailable', classification: critical ? 'prototype policy' : 'unavailable', spatial: critical },
    { icon: 'model', label: 'GridGuide priority lens', role: ranked ? 'Compares the same repair inputs' : 'Priority evidence unavailable', classification: ranked ? 'prototype policy' : 'unavailable' },
  ];
  return <section className="scenario-sources" aria-labelledby="scenario-sources-title" data-testid="scenario-sources">
    <div className="scenario-sources-heading"><Icon name="evidence" /><h3 id="scenario-sources-title">Data behind this scenario</h3></div>
    <ul>{items.map(item => <li key={item.label} className={item.spatial ? 'is-spatial' : ''}><Icon name={item.icon} /><div><strong>{item.label}</strong><p>{item.role}</p><span>{item.classification}</span></div></li>)}</ul>
    <p className="decision-fine">Scenario assumption: selected damage and replacement scope. Source facts do not confirm a current outage.</p>
  </section>;
}

/** A visual reading of authoritative values, never a client-side calculation. */
export function CandidateLineage({ candidate, plan }: { candidate: Candidate; plan: Plan }) {
  const historical = candidate.damage_source === 'historical ARCOS replay';
  const complete = candidate.dependent_premises !== null;
  const rates = hasEvidence(plan, 'topology and workbook rates', 'source-derived');
  const labor = hasEvidence(plan, 'labor semantics', 'AEP-specified');
  const task = plan.tasks.find(item => item.candidate_id === candidate.id);
  return <div className="candidate-lineage" data-testid="candidate-lineage">
    <p className="lineage-selection"><Icon name={candidate.kind === 'Distribution' ? 'transformer' : 'fuse'} /><strong>{candidate.label}</strong></p>
    <p className={`lineage-boundary ${historical ? 'is-spatial' : ''}`}>{historical ? 'Historical replay · no exact damage identifier match. Not a current outage.' : 'Damage is declared for this scenario, not confirmed by a current outage report.'}</p>
    <ol className="decision-evidence-chain" aria-label="Damage to premise evidence chain">
      <li className={historical ? 'is-spatial' : 'is-declared'}><Icon name={historical ? 'evidence' : 'model'} /><div><strong>{historical ? 'Historical ARCOS observation' : 'Declared damage scenario'}</strong><span>{historical ? 'Source-derived observation · scenario replay' : 'Scenario assumption · damage and quantity'}</span></div></li>
      <li className={historical ? 'is-spatial' : ''}><Icon name={historical ? 'spatial' : 'check'} /><div><strong>{!complete ? 'Association unavailable' : historical ? 'Qualified spatial hypothesis' : 'Verified source identity'}</strong><span>{historical ? 'Prototype match gates · not an exact ARCOS ID' : 'Source-derived asset · declared damage'}</span></div></li>
      <li><Icon name="network" /><div><strong>{complete ? `Verified source ${candidate.kind === 'Distribution' ? 'transformer' : 'fuse'}` : 'Topology evidence incomplete'}</strong><span>{complete ? 'Source-derived · approximate upstream topology' : 'Complete reverse membership unavailable'}</span></div></li>
      <li className="lineage-result"><Icon name="home" /><div><strong>{number(candidate.dependent_premises)} customer {candidate.dependent_premises === 1 ? 'location' : 'locations'}</strong><span>{complete ? 'All reverse memberships validated · source-derived' : 'Incomplete dependency count withheld'}</span></div></li>
      <li className="lineage-result"><Icon name="repair" /><div><strong>{number(candidate.repair_person_hours)} repair person-hours</strong><span>{rates ? `${number(candidate.direct_labor_hours)} direct hours · workbook rates` : 'Workbook provenance unavailable'}</span><span>{labor ? '×4.5 once → person-hours · AEP-specified' : 'Labor semantics unavailable'}</span><span>Replacement scope assumed; not elapsed time.</span></div></li>
      <li className="lineage-decision"><Icon name="crew" /><div><strong>{candidate.id === plan.recommended_id ? 'Recommended first' : task ? 'Later in the current plan' : 'Repair deferred'}</strong><span>{task ? `Crew ${task.crew} · finish ${number(task.display_finish_hours.lower)}–${number(task.display_finish_hours.upper)} h` : 'No executable crew assignment'}</span><span>GridGuide prototype policy</span></div></li>
    </ol>
    <p className="lineage-release-boundary">Potential dependency release is not confirmed restoration.</p>
  </div>;
}
