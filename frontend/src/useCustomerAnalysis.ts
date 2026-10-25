import { useCallback, useEffect, useRef, useState } from 'react';
import { getAnalysis, getLocations } from './api';
import type { Access, Analysis, Evaluation, Location, Need } from './api';

type Selection = { access: NonNullable<Access>; crewSize: number; needs: Need[] };
export function useCustomerAnalysis() {
  const [locations, setLocations] = useState<Location[]>([]);
  const [location, setLocation] = useState<Location | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [previousResult, setPreviousResult] = useState<Evaluation | null>(null);
  const [settings, setSettings] = useState<Selection>({ access: 'clear', crewSize: 4, needs: [] });
  const [pending, setPending] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [bootAttempt, setBootAttempt] = useState(0);
  const revision = useRef(0);
  const active = useRef<AbortController | null>(null);
  const confirmed = useRef<Evaluation | null>(null);
  const selection = useRef(settings);

  const analyze = useCallback(async (alias: string, next: Selection) => {
    const requestRevision = ++revision.current;
    active.current?.abort();
    const controller = new AbortController(); active.current = controller;
    selection.current = next; setSettings(next); setPending(true); setError(null);
    const previous = confirmed.current;
    try {
      const response = await getAnalysis({ location_alias: alias, access: next.access, crew_size: next.crewSize,
        declared_needs: { selections: next.needs, classification: 'user-declared' }, scenario_revision: requestRevision,
        previous: previous ? { access: previous.simulated_inputs.access, crew_size: previous.simulated_inputs.crew_size, scenario_revision: previous.scenario_revision } : null,
      }, controller.signal);
      if (requestRevision !== revision.current || controller.signal.aborted) return;
      if (response.result.scenario_revision !== requestRevision || response.result.simulated_inputs.access !== next.access ||
          response.result.simulated_inputs.crew_size !== next.crewSize || response.customer_journey.declared_needs.selections.join(',') !== next.needs.join(',') ||
          response.result.location.alias !== alias || response.customer_journey.result_id !== response.result.result_id ||
          (previous && response.comparison?.before_result_id !== previous.result_id)) {
        throw new Error('The analysis response did not match your selection. Please try again.');
      }
      setPreviousResult(previous); confirmed.current = response.result; setAnalysis(response); setPending(false);
    } catch (failure) {
      if (requestRevision !== revision.current || controller.signal.aborted) return;
      setError(failure instanceof Error && failure.name !== 'TimeoutError' ? failure.message : 'The analysis service took too long to respond. Please try again.');
      setPending(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController(); setPending(true); setError(null);
    getLocations(controller.signal).then(items => {
      if (controller.signal.aborted) return;
      if (!items.length) throw new Error('No verified demo location is available.');
      setLocations(items); setLocation(items[0]);
      void analyze(items[0].alias, { access: 'clear', crewSize: 4, needs: [] });
    }).catch(() => {
      if (!controller.signal.aborted) {
        setError('We could not load your demo location. Check that the analysis service is running and try again.'); setPending(false);
      }
    });
    return () => { controller.abort(); active.current?.abort(); };
  }, [analyze, bootAttempt]);

  const changeSelection = (patch: Partial<Selection>) => {
    if (location) void analyze(location.alias, { ...selection.current, ...patch });
  };
  const toggleNeed = (need: Need) => changeSelection({ needs: selection.current.needs.includes(need)
    ? selection.current.needs.filter(item => item !== need) : [...selection.current.needs, need].sort() });
  const selectLocation = (next: Location) => {
    if (next.alias === location?.alias) return;
    confirmed.current = null; setPreviousResult(null); setAnalysis(null); setLocation(next);
    void analyze(next.alias, { access: 'clear', crewSize: 4, needs: [] });
  };
  return { locations, location, analysis, previousResult, settings, pending, error, changeSelection, toggleNeed, selectLocation,
    current: !pending && !error ? analysis : null,
    retry: () => location ? changeSelection({}) : setBootAttempt(value => value + 1) };
}
