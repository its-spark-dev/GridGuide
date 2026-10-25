import { useEffect, useId, useRef, useState } from 'react';
import { getExplanation } from './api';
import type { Analysis, Evaluation, Explanation } from './api';
import { Icon } from './Icon';
import { ExplanationView } from './ExplanationView';
import type { EvidenceTarget } from './ExplanationView';
import './CustomerJourney.css';

type Props = {
  analysis: Analysis;
  previous: Evaluation | null;
  context?: 'risk' | 'restoration' | 'preparation' | 'topology';
  anchorPrefix?: string;
  onEvidence?: (target: EvidenceTarget) => void;
};

export function AskGridGuide({ analysis, previous, context = 'restoration', anchorPrefix, onEvidence }: Props) {
  const unique = useId();
  const titleId = `${anchorPrefix ?? `ask-${context}-${unique}`}-explanation-title`;
  const { result, comparison } = analysis;
  const bounds = result.restoration.display_hours;
  const questions = context === 'preparation' ? ['What should I prepare for?', 'Am I eligible for demo alerts?']
    : context === 'topology' ? ['How is my location connected?', 'Why this repair sequence?', 'How is repair effort calculated?']
    : context === 'risk' ? result.risk.band === 'HIGH' ? ['What does HIGH mean?', 'What should I prepare for?'] : []
    : [bounds ? `Why is restoration ${bounds.lower}–${bounds.upper} hours?` : 'Why can’t GridGuide estimate restoration right now?',
      ...(comparison && previous ? ['Why did my estimate change?'] : []), 'How is repair effort calculated?'];
  const [question, setQuestion] = useState<string | null>(null);
  const [answer, setAnswer] = useState<Explanation | null>(null);
  const [pending, setPending] = useState(false);
  const [failed, setFailed] = useState(false);
  const active = useRef<AbortController | null>(null);
  const sequence = useRef(0);
  useEffect(() => {
    sequence.current += 1;
    active.current?.abort();
    setQuestion(null); setAnswer(null); setFailed(false); setPending(false);
    return () => { active.current?.abort(); };
  }, [context, result.result_id, result.scenario_revision]);

  async function ask(next: string) {
    const requestNumber = ++sequence.current;
    active.current?.abort();
    const controller = new AbortController(); active.current = controller;
    setQuestion(next); setAnswer(null); setFailed(false); setPending(true);
    try {
      const response = await getExplanation({
        location_alias: result.location.alias, access: result.simulated_inputs.access,
        crew_size: result.simulated_inputs.crew_size,
        declared_needs: { selections: [], classification: 'user-declared' },
        scenario_revision: result.scenario_revision, result_id: result.result_id, question: next,
        previous: previous && comparison ? { access: previous.simulated_inputs.access, crew_size: previous.simulated_inputs.crew_size, scenario_revision: previous.scenario_revision } : null,
        previous_result_id: comparison?.before_result_id ?? null,
      }, controller.signal);
      if (controller.signal.aborted || requestNumber !== sequence.current) return;
      if (response.result_id !== result.result_id || response.scenario_revision !== result.scenario_revision) throw new Error('Stale explanation');
      setAnswer(response);
    } catch {
      if (controller.signal.aborted || requestNumber !== sequence.current) return;
      setFailed(true);
    } finally {
      if (!controller.signal.aborted && requestNumber === sequence.current) setPending(false);
    }
  }

  return <section className="ask-gridguide contextual-explanation" aria-labelledby={titleId} data-explanation-context={context}>
    <div className="contextual-heading"><Icon name="explain" /><div><h3 id={titleId}>Ask GridGuide</h3><p>Understand the information behind this {context === 'preparation' ? 'guidance' : context === 'topology' ? 'connection' : 'outlook'}.</p></div></div>
    {context === 'risk' && result.risk.band === null && <details className="contextual-missing"><summary>Why is risk unavailable?</summary><p>There isn’t enough verified information to assign a risk band. Available restoration and preparation guidance remain separate.</p><ul>{result.risk.missing_inputs.map(input => <li key={input}>{input.replaceAll('_', ' ')}</li>)}</ul>{result.risk.limitations.map(limit => <p key={limit}>{limit}</p>)}</details>}
    {context === 'risk' && result.risk.band !== null && !questions.length && <details className="contextual-missing"><summary>What contributes to this risk band?</summary><ul>{result.risk.factors.map(factor => <li key={factor.id}><strong>{factor.label}:</strong> {factor.value === null ? 'Unavailable' : typeof factor.value === 'boolean' ? factor.value ? 'Evidence present' : 'No evidence in this extract' : String(factor.value)}</li>)}</ul></details>}
    {!!questions.length && <div className="explanation-questions" aria-label="Suggested questions">{questions.map(item => <button key={item} type="button" aria-pressed={question === item} onClick={() => void ask(item)}>{item}<Icon name="arrow" /></button>)}</div>}
    {context === 'restoration' && <details className="contextual-more"><summary>More about this restoration scenario</summary><div className="explanation-questions">{['When will my power be restored?', 'Why this repair sequence?'].map(item => <button key={item} type="button" aria-pressed={question === item} onClick={() => void ask(item)}>{item}<Icon name="arrow" /></button>)}</div></details>}
    <p className="sr-only" role="status" aria-atomic="true">{pending ? 'Preparing an explanation.' : answer ? 'Explanation ready below.' : failed ? 'Explanation unavailable. Retry is available.' : ''}</p>
    <div className="explanation-answer" aria-busy={pending} data-testid="ai-explanation">
      {pending && <p className="contextual-loading">Preparing an explanation for this scenario…</p>}
      {answer && <ExplanationView answer={answer} onEvidence={onEvidence} />}
      {failed && <div className="contextual-error"><strong>Explanation service unavailable</strong><p>{comparison?.explanation ?? 'The validated outlook, assumptions and preparation guidance remain available on this page.'}</p><button type="button" onClick={() => question && void ask(question)}>Retry explanation</button></div>}
    </div>
    <p className="contextual-footnote">{context === 'preparation' ? 'These explanations cover general guidance. Your optional declarations are not sent to AI.' : 'Explains validated results; it does not calculate your estimate.'} Standard explanations remain available when AI is unavailable.</p>
  </section>;
}
