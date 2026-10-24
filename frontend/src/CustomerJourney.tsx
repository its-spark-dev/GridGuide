import { useState } from 'react';
import type { Analysis } from './api';

type Journey = Analysis['customer_journey'];

export function CustomerJourney({ journey }: { journey: Journey }) {
  const [selected, setSelected] = useState(journey.selected_state);
  const preview = journey.messages.find(message => message.state === selected)!;
  const { preparation, alerts } = journey;
  return <div className="journey-content">
    <div className="journey-columns">
      <article className="preparation" aria-labelledby="prepare-title">
        <h3 id="prepare-title">What should I do now?</h3>
        <ul className="preparation-actions" data-testid="preparation-actions">{preparation.actions.slice(0, 4).map(action => <li key={action}>{action}</li>)}</ul>
        {preparation.actions.length > 4 && <details><summary>More preparation for this scenario</summary><ul>{preparation.actions.slice(4).map(action => <li key={action}>{action}</li>)}</ul></details>}
        <p className="journey-note">{preparation.note}</p>
      </article>
      <article className="alert-eligibility" aria-labelledby="eligibility-title">
        <h3 id="eligibility-title">Will GridGuide keep me informed?</h3>
        <strong className="eligibility-status" data-testid="alert-eligibility">{alerts.eligible === true ? 'Eligible for demo alerts' : alerts.eligible === false ? 'In-app information only' : 'Eligibility needs more information'}</strong>
        <p>{alerts.reason}</p>
        <p>Suggested channels: {alerts.suggested_channels.map(channel => ({ app: 'in-app', sms: 'SMS', phone_call: 'phone call' })[channel]).join(', ')}.</p>
        <p className="delivery-note">{journey.delivery_note}</p>
        <details><summary>How demo eligibility works</summary><p>{alerts.assumptions}</p>{Object.entries(alerts.timing).map(([kind, timing]) => <p key={kind}>{kind === 'pre_storm' ? 'Pre-storm' : 'Estimate update'}: {timing}.</p>)}<p>No live storm schedule, subscription or contact information is connected.</p></details>
      </article>
    </div>
    <article className="communication" aria-labelledby="communications-title">
      <span className="eyebrow">COMMUNICATION PREVIEW · NOT SENT</span>
      <h3 id="communications-title">What will I be told as things change?</h3>
      <p>Select a stage to preview a possible communication. These are not observed outage events.</p>
      <fieldset className="lifecycle-selector"><legend className="sr-only">Communication stage preview</legend>
        {journey.messages.map((message, index) => <label className={selected === message.state ? 'selected' : ''} key={message.state}>
          <input type="radio" name="communication-stage" checked={selected === message.state} onChange={() => setSelected(message.state)} />
          <span><small>Stage {index + 1}</small>{message.title}</span>
        </label>)}
      </fieldset>
      <div className="message-preview" role="status" aria-live="polite" aria-atomic="true" data-testid="message-preview">
        <strong>{preview.title} · {preview.available ? 'sample message' : 'not yet available'}</strong>
        <p>{preview.body}</p>
        {selected === 'estimate_updated' && <p className="journey-note">{journey.update_reason} {journey.estimate_update_eligible ? 'Eligible for a demo update; not sent.' : 'No qualifying update is scheduled.'}</p>}
      </div>
    </article>
    <aside className="safety-guidance" aria-labelledby="safety-title"><h3 id="safety-title">Safety comes first</h3><ul>{preparation.safety.map(tip => <li key={tip}>{tip}</li>)}</ul>
      <p><a href="https://www.aepohio.com/safety/">Utility safety guidance</a> · <a href="https://www.foodsafety.gov/keep-food-safe/food-safety-in-disaster-or-emergency">Food safety during outages</a></p>
    </aside>
  </div>;
}
