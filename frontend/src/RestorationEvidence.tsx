import type { Evaluation } from './api';

const number = (value: number) => new Intl.NumberFormat('en-US', { maximumFractionDigits: 3 }).format(value);

export function RepairEffort({ result }: { result: Evaluation }) {
  const r = result.restoration;
  return <section className="panel repair-evidence" aria-labelledby="effort-title">
    <div className="section-heading"><div><span className="eyebrow">DAMAGE → WORK → EFFORT</span><h2 id="effort-title">The work behind this outlook</h2></div><span className="small-badge">Scenario assumption · replacement scope</span></div>
    <p>{r.labor_contributions.map(work => `${work.quantity} × ${work.recipe.replaceAll('-', ' ')}`).join(' + ')}. Historical circuit reports do not confirm damage to these assets.</p>
    <p className="effort-total" data-testid="repair-effort"><strong>{number(r.repair_person_hours)} person-hours</strong> of repair effort {r.total_person_hours !== null && r.access_labor_hours !== 0 ? <span>· {number(r.total_person_hours)} with access work</span> : null}</p>
    <p className="muted">AEP-specified: direct labor × 4.5 produces person-hours. This is effort, not an elapsed restoration estimate.</p>
    <details><summary>Follow the labor derivation</summary>
      <ul>{r.labor_contributions.map(work => <li key={work.task_id}><strong>{work.recipe.replaceAll('-', ' ')}</strong>: {work.quantity} unit(s) × ({number(work.install_hours_per_unit)} installation + {number(work.remove_hours_per_unit)} removal) = {number(work.direct_labor_hours)} direct labor hours.<small>Source-derived rates: {work.source_refs.join('; ')}. Quantity: scenario assumption.</small></li>)}</ul>
      <p>Installation: {number(r.installation_direct_hours)} + removal: {number(r.removal_direct_hours)} = <strong>{number(r.direct_labor_hours)} direct labor hours</strong>.</p>
      <p>Access work: {r.access_labor_hours === null ? 'unavailable until clearance is known' : `${number(r.access_labor_hours)} direct labor hours across ${r.worksite_count} modeled work sites`}. Total after the single {number(r.indirect_labor_multiplier)} multiplier: {r.total_person_hours === null ? 'unavailable' : `${number(r.total_person_hours)} person-hours`}.</p>
      <p>Prototype policy: keep tasks sequential; span ideal contribution by all {result.simulated_inputs.crew_size} crew members to one effective worker. Outward half-hour rounding avoids false precision. Actual efficiency and skill mix are unavailable; delays can exceed this conditional envelope.</p>
      <p>Travel, safety discussions and setup are already included. No duplicate travel/setup time is added.</p>
    </details>
  </section>;
}

export function RestorationSequence({ result }: { result: Evaluation }) {
  const { priority, repair_stages } = result.restoration;
  return <section className="panel restoration-sequence" aria-labelledby="sequence-title">
    <div className="section-heading"><div><span className="eyebrow">CUSTOMER IMPACT & RESTORATION ORDER</span><h2 id="sequence-title">Which declared repair comes first?</h2></div><span className="small-badge">Prototype policy · conditional sequence</span></div>
    <p data-testid="priority-summary">{priority.reasoning}</p>
    <div data-testid="asset-impact"><h3>Declared damage → premise dependencies</h3><p>Scenario assumption: damage declared on exact source-verified assets. An ARCOS damage record has not been linked to these repairs; observed outage impact is unavailable.</p><ul>{priority.asset_impacts.map(asset => <li key={asset.node_alias}><strong>{asset.node_alias === 'protective-a' ? 'Upstream fuse' : 'Serving transformer'}</strong>: {asset.dependent_customers ?? 'unavailable'} premise dependencies in this scenario.<small>Source-derived: {asset.identity_basis.replaceAll('_', ' ')} · all {asset.topology_path_count ?? 'unknown'} indexed premise paths checked; {asset.unresolved_path_count} unresolved.</small></li>)}</ul></div>
    <ol className="repair-stages">{repair_stages.map(stage => <li key={stage.task_id}><strong>{stage.node_alias === 'protective-a' ? 'Upstream fuse repair' : 'Serving transformer repair'}</strong><span>{number(stage.repair_person_hours)} repair person-hours · {stage.newly_eligible_customers ?? 'unavailable'} additional customer path(s) could clear their declared damage dependency.</span></li>)}</ol>
    <p className="muted">Source-derived approximate topology: {priority.circuit_customer_paths} matched circuit customer paths; {priority.dependent_customer_paths ?? 'unavailable'} depend on the declared damaged equipment. {priority.paths_outside_declared_damage ?? 'unavailable'} paths lie outside this declared damage scope; this is not their current outage status.</p>
    <p><strong>Customers restorable through actual sectionalization: unavailable.</strong> Repair-dependent release above assumes supply, other equipment and operational authorization; it does not specify a switching operation.</p>
    <details><summary>Critical facilities & limits to this sequence</summary>
      <p>Spatial criticality context only: source-derived facility inventory within the verified primary-line geographic extent. This is not verified electrical dependency.</p>
      <ul>{priority.facilities.map(f => <li key={f.kind}>{f.kind.replaceAll('_', ' ')}: {f.within_primary_extent ?? 'unavailable'} in this geographic context; {f.regional_features} in the supplied regional layer.<small>{f.source_layer}</small></li>)}</ul>
      <p data-testid="criticality-context">{priority.criticality_action}</p>
      <p><strong>Affected facility count, actual switching feasibility and operational priority: unavailable.</strong> No facility locations, identities or customer medical inferences are shown.</p>
      <ul>{priority.limitations.map(limit => <li key={limit}>{limit}</li>)}</ul>
    </details>
  </section>;
}
