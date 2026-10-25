import type { CSSProperties } from 'react';
import type { Evaluation } from './api';
import { Icon } from './Icon';

type Bounds = NonNullable<Evaluation['restoration']['display_hours']>;
const format = (value: number) => new Intl.NumberFormat('en-US', { maximumFractionDigits: 3 }).format(value);

export function RestorationRange({ result, previous, compact = false }: { result: Evaluation; previous?: Evaluation | null; compact?: boolean }) {
  const bounds = result.restoration.display_hours;
  const old = previous?.restoration.display_hours;
  const changed = old && bounds && (old.lower !== bounds.lower || old.upper !== bounds.upper);
  const scale = Math.max(bounds?.upper ?? 0, old?.upper ?? 0, 1) * 1.16;
  const rail = (range: Bounds, historical: boolean) => <div className={`range-track ${historical ? 'range-track-old' : ''}`} aria-hidden="true">
    <span className="range-origin" />
    <span className="range-interval" style={{ '--range-start': `${range.lower / scale * 100}%`, '--range-width': `${(range.upper - range.lower) / scale * 100}%` } as CSSProperties}>
      <span className="range-end range-end-start">{format(range.lower)}<small>h</small></span>
      <span className="range-end range-end-finish">{format(range.upper)}<small>h</small></span>
      <span className="range-continuation" />
    </span>
  </div>;
  return <div className={`restoration-visual ${compact ? 'compact' : ''}`}>
    <div data-testid={compact ? "restoration-comparison-result" : "restoration-result"} className="restoration-value">
      {bounds ? <><strong>{format(bounds.lower)}–{format(bounds.upper)} <span>hours</span></strong><p>After crew response begins</p></> : <><Icon name="access"/><strong className="unavailable-title">A restoration range isn’t available</strong><p>{result.restoration.status === 'pending_clearance' ? 'Pending access clearance' : 'Required information is missing'}</p></>}
    </div>
    {bounds ? <>
      <div className="range-diagram" role="img" aria-label={`Conditional restoration range ${format(bounds.lower)} to ${format(bounds.upper)} elapsed hours after crew response begins.${changed ? ` Previous range ${format(old.lower)} to ${format(old.upper)} hours.` : ''} Actual completion may take longer.`}>
        {changed && <div className="previous-range"><span>Previous <b>{format(old.lower)}–{format(old.upper)} h</b></span>{rail(old, true)}</div>}
        {rail(bounds, false)}
        <div className="range-axis"><span>Crew response begins</span><span>Conditional boundaries</span></div>
      </div>
      <p className="range-limit"><Icon name="unknown"/>Actual completion may take longer.</p>
    </> : <p className="unavailable-note">{result.restoration.status === 'pending_clearance' ? 'Access must be cleared before a complete modeled range can be provided. Clearance duration is unknown.' : 'The available evidence cannot support a complete range. Preparation and safety guidance are still available.'}</p>}
  </div>;
}
