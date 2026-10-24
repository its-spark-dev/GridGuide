import type { components } from './api.generated';

export type Analysis = components['schemas']['AnalysisResponse'];
export type Evaluation = Analysis['result'];
export type Location = Evaluation['location'];
export type AnalysisRequest = components['schemas']['AnalysisRequest'];
export type Access = AnalysisRequest['access'];
export type Need = Analysis['customer_journey']['declared_needs']['selections'][number];

export type Explanation = components['schemas']['ExplanationResponse'];
export type ExplanationRequest = components['schemas']['ExplanationRequest'];

async function request<T>(path: string, signal: AbortSignal, body?: AnalysisRequest | ExplanationRequest): Promise<T> {
  const response = await fetch(path, {
    method: body ? 'POST' : 'GET',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
    signal: AbortSignal.any([signal, AbortSignal.timeout(10_000)]),
    cache: 'no-store',
  });
  if (!response.ok) throw new Error('The analysis service could not complete this request. Please try again.');
  return response.json() as Promise<T>;
}

export const getLocations = (signal: AbortSignal) => request<Location[]>('/api/locations', signal);
export const getAnalysis = (body: AnalysisRequest, signal: AbortSignal) => request<Analysis>('/api/evaluate', signal, body);

export type MapData = components['schemas']['GeographicMap'];
export const getMap = (alias: string, signal: AbortSignal) => request<MapData>(`/api/map?location_alias=${encodeURIComponent(alias)}`, signal);
export const getExplanation = (body: ExplanationRequest, signal: AbortSignal) => request<Explanation>('/api/explain', signal, body);
