import { useCallback, useEffect, useRef, useState } from 'react';
import type { components } from './api.generated';

export type Plan = components['schemas']['RestorationPlan'];
export type Candidate = Plan['candidates'][number];
type PlanRequest = components['schemas']['PlanRequest'];
type Explanation = components['schemas']['ExplanationResponse'];
export type PlanAccess = 'clear' | 'restricted' | 'blocked';
export type PlanSettings = { crew_count: 1 | 2; crew_size: number; use_critical_proxy: boolean; access: Record<string, PlanAccess> };
const initial: PlanSettings = { crew_count: 1, crew_size: 4, use_critical_proxy: true, access: {} };

async function post<T>(path: string, body: unknown, signal: AbortSignal): Promise<T> {
  const response = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
    signal: AbortSignal.any([signal, AbortSignal.timeout(15_000)]), cache: 'no-store' });
  if (!response.ok) throw new Error('The planning service could not complete this request. Please try again.');
  return response.json() as Promise<T>;
}

function matchesAlternative(other: Plan, current: Plan): boolean {
  return other.scenario_revision === current.scenario_revision && other.crew_count === current.crew_count && other.crew_size === current.crew_size &&
    other.use_critical_proxy === !current.use_critical_proxy && Array.isArray(other.candidates) && other.candidates.length === current.candidates.length &&
    other.candidates.every(c => c && current.candidates.some(original => original.id === c.id && original.access === c.access)) &&
    new Set(other.candidates.map(c => c.id)).size === current.candidates.length &&
    (other.recommended_id === null || other.candidates.some(c => c.id === other.recommended_id));
}

/** The planning scenario has its own revisions and never changes the customer outlook. */
export function useRestorationPlan(active: boolean) {
  const [settings, setSettings] = useState<PlanSettings>(initial);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [alternative, setAlternative] = useState<Plan | null>(null);
  const [alternativePending, setAlternativePending] = useState(false);
  const [previous, setPrevious] = useState<Plan | null>(null);
  const [catalog, setCatalog] = useState<{ id: string; label: string }[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [answer, setAnswer] = useState<Explanation | null>(null);
  const [answerPending, setAnswerPending] = useState(false);
  const [answerFailed, setAnswerFailed] = useState(false);
  const [question, setQuestion] = useState<string | null>(null);
  const started = useRef(false);
  const revision = useRef(0);
  const currentSettings = useRef<PlanSettings>(initial);
  const lastConfirmed = useRef<Plan | null>(null);
  const activeResult = useRef<Plan | null>(null);
  const activeRequest = useRef<PlanRequest | null>(null);
  const evaluationController = useRef<AbortController | null>(null);
  const explanationController = useRef<AbortController | null>(null);
  const explanationSequence = useRef(0);

  const evaluate = useCallback(async (next: PlanSettings, followRecommendation = false) => {
    const requestRevision = ++revision.current;
    currentSettings.current = next;
    setSettings(next);
    evaluationController.current?.abort(); explanationController.current?.abort();
    explanationSequence.current += 1;
    const controller = new AbortController(); evaluationController.current = controller;
    activeResult.current = null; activeRequest.current = null;
    setPending(true); setError(null); setPlan(null); setAlternative(null); setAlternativePending(true);
    setAnswer(null); setAnswerPending(false); setAnswerFailed(false); setQuestion(null);
    const body: PlanRequest = { scenario_revision: requestRevision, crew_count: next.crew_count, crew_size: next.crew_size,
      use_critical_proxy: next.use_critical_proxy, access: Object.entries(next.access).map(([candidate_id, access]) => ({ candidate_id, access })) };
    const opposite = post<Plan>('/api/restoration-plan', { ...body, use_critical_proxy: !next.use_critical_proxy }, controller.signal).catch(() => null);
    try {
      const response = await post<Plan>('/api/restoration-plan', body, controller.signal);
      if (controller.signal.aborted || requestRevision !== revision.current) return;
      if (response.scenario_revision !== requestRevision || response.crew_count !== next.crew_count || response.crew_size !== next.crew_size ||
          response.use_critical_proxy !== next.use_critical_proxy || response.candidates.some(candidate => candidate.access !== (next.access[candidate.id] ?? 'clear')) ||
          Object.keys(next.access).some(id => !response.candidates.some(candidate => candidate.id === id)) ||
          (response.recommended_id !== null && !response.candidates.some(candidate => candidate.id === response.recommended_id))) {
        throw new Error('The plan did not match your scenario. Please try again.');
      }
      setPrevious(lastConfirmed.current); lastConfirmed.current = response; activeResult.current = response; activeRequest.current = body;
      setCatalog(response.candidates.map(({ id, label }) => ({ id, label })));
      setSelected(value => !followRecommendation && response.candidates.some(candidate => candidate.id === value)
        ? value : response.recommended_id ?? response.candidates[0]?.id ?? null);
      setPlan(response); setPending(false);
      const other = await opposite;
      if (controller.signal.aborted || requestRevision !== revision.current) return;
      if (other && matchesAlternative(other, response)) setAlternative(other);
      setAlternativePending(false);
    } catch (failure) {
      if (controller.signal.aborted || requestRevision !== revision.current) return;
      setError(failure instanceof Error && failure.name !== 'TimeoutError' ? failure.message : 'The planning service took too long to respond. Please try again.');
      setPending(false); setAlternativePending(false); controller.abort();
    }
  }, []);

  useEffect(() => {
    if (active && !started.current) { started.current = true; void evaluate(initial, true); }
  }, [active, evaluate]);
  useEffect(() => () => {
    revision.current += 1; explanationSequence.current += 1;
    evaluationController.current?.abort(); explanationController.current?.abort();
  }, []);

  function change(patch: Partial<PlanSettings>) {
    const follow = patch.use_critical_proxy !== undefined && patch.use_critical_proxy !== currentSettings.current.use_critical_proxy;
    void evaluate({ ...currentSettings.current, ...patch }, follow);
  }
  function changeAccess(id: string, access: PlanAccess) { change({ access: { ...currentSettings.current.access, [id]: access } }); }
  function retry() { void evaluate(currentSettings.current); }

  async function retryAlternative() {
    const current = activeResult.current; const request = activeRequest.current; const controller = evaluationController.current;
    if (!current || !request || !controller || controller.signal.aborted) return;
    setAlternativePending(true);
    const other = await post<Plan>('/api/restoration-plan', { ...request, use_critical_proxy: !request.use_critical_proxy }, controller.signal).catch(() => null);
    if (controller.signal.aborted || activeResult.current?.result_id !== current.result_id) return;
    setAlternative(other && matchesAlternative(other, current) ? other : null); setAlternativePending(false);
  }

  async function ask(next: string) {
    const current = activeResult.current; const request = activeRequest.current;
    if (!current || !request) return;
    const number = ++explanationSequence.current;
    explanationController.current?.abort();
    const controller = new AbortController(); explanationController.current = controller;
    setQuestion(next); setAnswer(null); setAnswerPending(true); setAnswerFailed(false);
    try {
      const response = await post<Explanation>('/api/restoration-plan/explain', { ...request, result_id: current.result_id, question: next }, controller.signal);
      if (controller.signal.aborted || number !== explanationSequence.current || activeResult.current?.result_id !== current.result_id) return;
      if (response.result_id !== current.result_id || response.scenario_revision !== current.scenario_revision) throw new Error('Explanation binding mismatch');
      setAnswer(response);
    } catch {
      if (!controller.signal.aborted && number === explanationSequence.current && activeResult.current?.result_id === current.result_id) setAnswerFailed(true);
    } finally {
      if (!controller.signal.aborted && number === explanationSequence.current) setAnswerPending(false);
    }
  }

  return { settings, current: !pending && !error ? plan : null, alternative, alternativePending, previous, catalog,
    selected, setSelected, pending, error, answer, answerPending, answerFailed, question, change, changeAccess, retry, retryAlternative, ask };
}
