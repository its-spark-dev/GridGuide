import { useEffect, useRef, useState } from 'react';
import { getExplanation } from './api';
import type { Analysis, Evaluation, Explanation } from './api';

export function AskGridGuide({ analysis, previous }: { analysis: Analysis; previous: Evaluation | null }) {
  const { result, comparison } = analysis;
  const bounds = result.restoration.display_hours;
  const questions = [
    bounds ? `Why is restoration ${bounds.lower}–${bounds.upper} hours?` : 'Why can’t GridGuide estimate restoration right now?',
    'Why did my estimate change?', 'What does HIGH mean?', 'What should I prepare for?', 'When will my power be restored?',
  ];
  const [question, setQuestion] = useState<string | null>(null);
  const [answer, setAnswer] = useState<Explanation | null>(null);
  const [pending, setPending] = useState(false);
  const [failed, setFailed] = useState(false);
  const active = useRef<AbortController | null>(null);
  const sequence = useRef(0);
  useEffect(() => () => { active.current?.abort(); }, []);

  async function ask(next: string) {
    const requestNumber = ++sequence.current;
    active.current?.abort();
    const controller = new AbortController(); active.current = controller;
    setQuestion(next); setAnswer(null); setFailed(false); setPending(true);
    try {
      const response = await getExplanation({
        location_alias: result.location.alias, access: result.simulated_inputs.access,
        scenario_revision: result.scenario_revision, result_id: result.result_id, question: next,
        previous: previous && comparison ? { access: previous.simulated_inputs.access, scenario_revision: previous.scenario_revision } : null,
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

  return <section className="ask-gridguide panel" aria-labelledby="ask-title">
    <div className="section-heading"><div><span className="eyebrow">UNDERSTAND YOUR OUTLOOK</span><h2 id="ask-title">Ask GridGuide</h2></div><span className="small-badge">Current scenario only</span></div>
    <p className="muted">Choose a question. Answers use this scenario’s validated results, with a standard explanation whenever AI is unavailable.</p>
    <div className="explanation-questions" aria-label="Suggested questions">{questions.map(item => <button key={item} type="button" aria-pressed={question === item} onClick={() => void ask(item)}>{item}</button>)}</div>
    <div className="explanation-answer" aria-live="polite" aria-atomic="true" aria-busy={pending} data-testid="ai-explanation">
      {pending && <p role="status">Preparing an explanation for this scenario…</p>}
      {answer && <>
        <div className="explanation-labels"><span className="small-badge">{answer.mode === 'ai_assisted' ? 'AI-assisted explanation' : answer.mode === 'unsupported' ? 'Outside verified scope' : 'Standard explanation'}</span><span className="small-badge">{answer.source_type === 'mixed' ? 'Verified context · simulated inputs · modeled results' : answer.source_type}</span></div>
        <p className="answer-lead">{answer.answer}</p>
        {answer.supporting_factors.length > 0 && <ul>{answer.supporting_factors.map(factor => <li key={factor.id}>{factor.text}</li>)}</ul>}
        <p className="fine muted">{answer.uncertainty_note}</p><p className="fine muted">{answer.dataset_note}</p>
      </>}
      {failed && <div role="status"><strong>Explanation service unavailable</strong><p>{comparison?.explanation ?? 'The validated outlook, assumptions and preparation guidance remain available on this page.'}</p><button type="button" onClick={() => question && void ask(question)}>Retry explanation</button></div>}
    </div>
  </section>;
}
