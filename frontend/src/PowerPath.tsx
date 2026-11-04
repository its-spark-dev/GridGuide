import { useEffect, useState } from 'react';
import type { PathFrame } from './offline';
import { Icon } from './Icon';

const states = { intact_assumption: 'Assumed intact', declared_damage: 'Declared damage', blocked: 'Blocked access',
  dependency_blocked: 'Blocked by prerequisite', completed_simulated: 'Completed in this fictional milestone', unresolved: 'Unresolved evidence' };

export function PowerPath({ frame }: { frame: PathFrame }) {
  const [selected, setSelected] = useState<string | null>(null);
  useEffect(() => { setSelected(null); }, [frame.scenario_id]);
  const node = frame.nodes.find(n => n.id === selected);
  const affected = node ? frame.customers.filter(c => c.asset_ids.includes(node.id)) : [];
  return <section className="power-path" aria-labelledby="power-path-title">
    <div className="section-heading"><div><span className="eyebrow">Fictional dependency example</span>
      <h2 id="power-path-title">What does each customer depend on?</h2></div><Icon name="network"/></div>
    <p>Select a component to inspect its assumptions. Paths run from the customer toward an abstract supply terminal.</p>
    <p className="fine">Declared schematic only. No map coordinates or real utility connectivity. Geographic lines never establish electrical dependencies.</p>
    <div className="path-layout">
      <div>{frame.customers.map(customer => <section className="customer-path" key={customer.id} aria-label={customer.label}>
        <h3>{customer.label}</h3>
        <p><strong>{customer.release_state === 'released_simulated' ? 'Dependencies released in this fictional milestone' :
          customer.release_state === 'unresolved' ? 'Release unresolved' : 'Waiting for required repairs'}</strong></p>
        <p>{customer.reason}</p>
        <ol aria-label={customer.label + ' ordered upstream dependencies'} className="path-nodes">
          {customer.asset_ids.map(id => {
            const item = frame.nodes.find(n => n.id === id)!;
            return <li key={id}>
              <button type="button" className={'path-node state-' + item.state} aria-pressed={selected === id}
                onClick={() => setSelected(id)} aria-controls="path-inspection">
                <strong>{item.label}</strong><span>{states[item.state]}</span>
                {item.kind === 'supply_terminal' && <small>Abstract · unlocated</small>}
              </button>
              {customer.unresolved_link_from_ids.includes(id) ? <span className="path-edge">Unknown connection ↓</span> :
                item.kind !== 'supply_terminal' && <span className="path-edge">Declared dependency ↓</span>}
            </li>;
          })}
        </ol>
      </section>)}</div>
      <aside id="path-inspection" aria-live="polite" aria-atomic="true" className="path-inspection">
        <h3>{node ? node.label : 'Inspect a dependency'}</h3>
        {node ? <><p><strong>{states[node.state]}</strong></p><p>{node.reason}</p>
          <p>Known here: this component is explicitly listed in the fictional definition. It is not an observed utility asset.</p>
          <p>Assumed: supply and listed dependencies; actual productivity, switching and restoration outcomes are unavailable.</p>
          {node.prerequisite_ids.length > 0 && <><h4>Repair prerequisites</h4><ul>{node.prerequisite_ids.map(id =>
            <li key={id}>{frame.nodes.find(n => n.repair_id === id)?.label ?? 'Unresolved prerequisite'}</li>)}</ul></>}
          <h4>Fictional paths using this component</h4><ul>{affected.map(c => <li key={c.id}>{c.label}: {c.reason}</li>)}</ul>
          <p>All required repairs along each path must finish; an unknown connection or clearance prevents a confirmed modeled release.</p>
        </> : <p>Use Tab to reach a component, then Enter or Space to select it. Its state and affected paths will appear here.</p>}
      </aside>
    </div>
  </section>;
}
