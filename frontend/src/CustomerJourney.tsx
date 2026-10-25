import { Fragment, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import type { Analysis } from './api';
import { Icon } from './Icon';
import './CustomerJourney.css';

type Journey = Analysis['customer_journey'];
type Props = {
  journey: Journey;
  checkedActions: ReadonlySet<string>;
  onToggleAction: (action: string) => void;
  declarations?: ReactNode;
  explanation?: ReactNode;
};
const channelName = { app: 'In-app information', sms: 'SMS', phone_call: 'Phone call' };

export function CustomerJourney({ journey, checkedActions, onToggleAction, declarations, explanation }: Props) {
  const [selected, setSelected] = useState(journey.selected_state);
  useEffect(() => { setSelected(journey.selected_state); }, [journey.result_id, journey.selected_state]);
  const { preparation, alerts } = journey;
  const completed = preparation.actions.filter(action => checkedActions.has(action)).length;
  return <div className="journey-content">
    <div className="journey-preparation-layout">
      <section className="preparation journey-preparation" aria-labelledby="prepare-title">
        <div className="journey-section-heading">
          <div><span className="journey-kicker">Your next steps</span><h2 id="prepare-title">Be ready, one step at a time.</h2></div>
          <span className="checklist-count">{completed} of {preparation.actions.length} checked</span>
        </div>
        <p className="journey-intro">A practical checklist for this scenario. Check items for your own reference; checks stay in this session and reset on refresh.</p>
        {preparation.declared_actions.length > 0 && <aside className="declared-guidance" aria-label="Guidance for your declarations">
          <div className="journey-callout-heading"><Icon name="accessibility" /><strong>For the needs you shared</strong></div>
          <p className="journey-caption">User-declared · nothing inferred from your location</p>
          <ul>{preparation.declared_actions.map(action => <li key={action}>{action}</li>)}</ul>
          <div className="journey-source-links"><a href="https://www.fda.gov/medical-devices/emergency-situations-medical-devices/fda-offers-tips-about-medical-devices-and-natural-disasters">FDA device preparedness</a><a href="https://www.ready.gov/disability">Accessible emergency planning</a></div>
        </aside>}
        <ul className="preparation-actions journey-checklist" data-testid="preparation-actions">
          {preparation.actions.map(action => <li key={action} className={checkedActions.has(action) ? 'is-checked' : ''}>
            <label><input type="checkbox" checked={checkedActions.has(action)} onChange={() => onToggleAction(action)} /><span>{action}</span></label>
          </li>)}
        </ul>
        <p className="journey-note">{preparation.note}</p>
        {declarations && <div className="journey-declarations">{declarations}</div>}
      </section>
      <aside className="safety-guidance journey-safety" aria-labelledby="safety-title">
        <div className="journey-callout-heading"><Icon name="shield" /><h2 id="safety-title">Safety comes first</h2></div>
        <p className="journey-caption">Keep these precautions in mind, whatever the estimate.</p>
        <ul>{preparation.safety.map(tip => <li key={tip}>{tip}</li>)}</ul>
        <div className="journey-source-links"><a href="https://www.aepohio.com/safety/">Utility safety guidance</a><a href="https://www.foodsafety.gov/keep-food-safe/food-safety-in-disaster-or-emergency">Food safety during outages</a></div>
      </aside>
    </div>
    {explanation}
    <section className="journey-alert-section" aria-labelledby="eligibility-title">
      <div className="journey-section-heading"><div><span className="journey-kicker">Stay informed</span><h2 id="eligibility-title">What updates could I receive?</h2></div><Icon name="alert" /></div>
      <p className="journey-intro">Explore the recommended communication for this scenario. This prototype does not enroll you in a utility alert service.</p>
      <div className="journey-alert-summary">
        <div className="alert-eligibility">
          <span className="journey-label">Scenario eligibility</span>
          <strong className="eligibility-status" data-testid="alert-eligibility">{alerts.eligible === true ? 'Eligible for demo alerts' : alerts.eligible === false ? 'In-app information only' : 'Eligibility needs more information'}</strong>
          <p>{alerts.reason}</p>
        </div>
        <div className="journey-delivery"><span className="journey-label">Delivery status</span><strong>No notifications are being sent</strong><p>Preview only. No contact details, subscription or consent are collected.</p></div>
      </div>
      <div className="journey-channel-row">
        <div><span className="journey-label">Suggested channels</span><ul className="journey-channels">{alerts.suggested_channels.map(channel => <li key={channel}><Icon name={channel === 'sms' ? 'sms' : 'alert'} /><span>{channelName[channel]}</span></li>)}</ul></div>
        <div><span className="journey-label">Prototype triggers</span>{Object.keys(alerts.timing).length ? <dl className="journey-triggers">{Object.entries(alerts.timing).map(([kind, timing]) => <div key={kind}><dt>{kind === 'pre_storm' ? 'Pre-storm' : 'Estimate update'}</dt><dd>{timing}</dd></div>)}</dl> : <p className="journey-trigger-unknown">No timing recommendation is available for this eligibility state.</p>}</div>
      </div>
      <p className="journey-escalation">{alerts.escalation_guidance}</p>
      <details className="journey-policy"><summary>How this prototype decides eligibility</summary><p>{alerts.assumptions}</p><p>{journey.delivery_note}</p><p>No live storm schedule or notification service is connected.</p></details>
    </section>
    <section id="communications" tabIndex={-1} className="communication journey-communication" aria-labelledby="communications-title">
      <span className="journey-kicker">Communication preview · not sent</span>
      <h2 id="communications-title">A message for each stage</h2>
      <p className="journey-intro">Choose an example below. These stages are possible communications, not a record of an actual outage.</p>
      <fieldset className="lifecycle-selector journey-lifecycle"><legend className="sr-only">Communication stage preview</legend>
        {journey.messages.map((message, index) => <Fragment key={message.state}>
          <label className={`journey-stage journey-stage-${index + 1} ${selected === message.state ? 'selected' : ''}`}>
            <input type="radio" name="communication-stage" checked={selected === message.state} onChange={() => setSelected(message.state)} aria-controls={selected === message.state ? 'communication-message' : undefined} />
            <span className="journey-stage-number" aria-hidden="true">{String(index + 1).padStart(2, '0')}</span>
            <span className="journey-stage-title">{message.title}<small>{selected === message.state ? 'Viewing this preview' : 'View preview'}</small></span><Icon name="chevron" />
          </label>
          {selected === message.state && <div id="communication-message" className="message-preview journey-message" role="region" aria-labelledby="message-preview-title" data-testid="message-preview">
            <div className="journey-message-heading"><Icon name="sms" /><div><span className="journey-label">Example communication</span><h3 id="message-preview-title">{message.title}</h3></div><span className="journey-message-state">{message.available ? 'Preview only' : 'Not yet available'}</span></div>
            <p className="journey-message-body">{message.body}</p>
            {selected === 'estimate_updated' && <p className="journey-note journey-update-note">{journey.update_reason} {journey.estimate_update_eligible ? 'Eligible for a demo update; not sent.' : 'No qualifying update is scheduled.'}</p>}
            <p className="journey-message-footer">No notification has been sent. Selecting a stage does not change your outage status.</p>
          </div>}
        </Fragment>)}
      </fieldset>
    </section>
  </div>;
}
