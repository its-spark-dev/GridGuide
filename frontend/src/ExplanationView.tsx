import type { Explanation } from './api';
import { Icon } from './Icon';
import './CustomerJourney.css';

export type EvidenceTarget = 'risk' | 'restoration' | 'preparation' | 'topology';
const evidenceLabel: Record<EvidenceTarget, string> = { risk: 'View risk factors', restoration: 'View repair assumptions', preparation: 'View preparation guidance', topology: 'View grid context' };
const targetFor = (id: string): EvidenceTarget => id.startsWith('risk-') ? 'risk' : /^(preparation|alerts)-/.test(id) ? 'preparation' : /^(topology|priority)-/.test(id) ? 'topology' : 'restoration';

export function ExplanationView({ answer, onEvidence }: { answer: Explanation; onEvidence?: (target: EvidenceTarget) => void }) {
  const targets = [...new Set(answer.supporting_factors.map(factor => targetFor(factor.id)))];
  return <div className="grounded-answer">
    <div className="explanation-labels"><Icon name="evidence" /><strong>{answer.mode === 'ai_assisted' ? 'AI-assisted explanation' : answer.mode === 'unsupported' ? 'Outside verified scope' : 'Standard explanation'}</strong><span>{answer.source_type === 'mixed' ? 'Verified context · simulated inputs · modeled results' : answer.source_type}</span></div>
    <p className="answer-lead">{answer.answer}</p>
    {answer.supporting_factors.length > 0 && <ul className="grounded-factors">{answer.supporting_factors.map(factor => <li key={factor.id}>{factor.text}</li>)}</ul>}
    {onEvidence && targets.length > 0 && <div className="grounded-links" aria-label="Related evidence">{targets.map(target => <button key={target} type="button" onClick={() => onEvidence(target)}>{evidenceLabel[target]}<Icon name="arrow" /></button>)}</div>}
    <details className="grounded-limits"><summary>Uncertainty and source context</summary><p>{answer.uncertainty_note}</p><p>{answer.dataset_note}</p></details>
  </div>;
}
