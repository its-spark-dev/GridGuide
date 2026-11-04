import type { components } from './api.generated';
import { pathTrust } from './pathTrust.generated';
import { PRODUCT_VERSION } from './version';

export type PathFrame = components['schemas']['CustomerPathFrame'];
export type Snapshot = { schema_version: 'preparedness-snapshot-v1'; app_version: 'v1.1-phase6' | typeof PRODUCT_VERSION; saved_at: string; frame: PathFrame };
export const SNAPSHOT_KEY = 'gridguide.preparedness.snapshot.v1';
export const MAX_RECORD_BYTES = 50_000;
const approved = new Set<string>(pathTrust.approved_frames);
const byteLength = (text: string) => new TextEncoder().encode(text).byteLength;
const frameKeys = ['schema_version','mode','provenance','scenario_id','scenario_revision','label','input_fingerprint',
  'model_version','policy_id','duration_assumption','step','step_label','elapsed_hours','nodes','customers',
  'released_customers','unresolved_customers','completion_hours','result_fingerprint'];

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function exact(value: unknown, keys: string[]): value is Record<string, unknown> {
  return object(value) && Object.keys(value).length === keys.length && keys.every(k => Object.hasOwn(value, k));
}
function canonical(value: unknown): string {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (object(value)) return '{' + Object.keys(value).sort().map(k => JSON.stringify(k) + ':' + canonical(value[k])).join(',') + '}';
  return JSON.stringify(value);
}
async function sha(value: unknown): Promise<string> {
  const bytes = new TextEncoder().encode(canonical(value));
  return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), x => x.toString(16).padStart(2, '0')).join('');
}

/** Runtime checks AND a build-approved content digest. Arbitrary text/source fields
 * cannot enter storage merely by matching a TypeScript shape. No numerical modeling. */
export async function validateFrame(value: unknown): Promise<PathFrame> {
  if (!exact(value, frameKeys) || byteLength(JSON.stringify(value)) > MAX_RECORD_BYTES ||
      value.mode !== 'synthetic-demo' || value.provenance !== 'independently_authored_fiction' ||
      typeof value.result_fingerprint !== 'string' || !approved.has(value.result_fingerprint)) throw new Error('Unsupported fictional artifact.');
  const { result_fingerprint, ...content } = value;
  if (await sha(content) !== result_fingerprint) throw new Error('Fictional artifact integrity check failed.');
  // Equality to a generated, Python-validated approved frame establishes its nested
  // field allowlist and exact content. This is integrity validation, not authentication.
  return JSON.parse(JSON.stringify(value)) as PathFrame;
}

export async function loadFrames(signal: AbortSignal): Promise<PathFrame[]> {
  const response = await fetch('/preparedness/frames.json', { signal, cache: 'no-store', credentials: 'omit' });
  if (!response.ok) throw new Error('Fictional examples are unavailable.');
  const text = await response.text();
  if (text.length > 500_000) throw new Error('Unsupported artifact size.');
  const value: unknown = JSON.parse(text);
  if (!exact(value, ['version','catalog_sha256','frames']) || value.version !== 'customer-path-catalog-v1' ||
      value.catalog_sha256 !== pathTrust.catalog_sha256 || !Array.isArray(value.frames) ||
      await sha(value) !== pathTrust.frames_sha256) throw new Error('Unsupported fictional catalog.');
  return Promise.all(value.frames.map(validateFrame));
}

export async function parseSnapshot(raw: string): Promise<Snapshot> {
  if (byteLength(raw) > MAX_RECORD_BYTES) throw new Error('Saved snapshot is too large.');
  const value: unknown = JSON.parse(raw);
  if (!exact(value, ['schema_version','app_version','saved_at','frame']) ||
      value.schema_version !== 'preparedness-snapshot-v1' || (value.app_version !== PRODUCT_VERSION && value.app_version !== 'v1.1-phase6') ||
      typeof value.saved_at !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(value.saved_at) ||
      !Number.isFinite(Date.parse(value.saved_at))) throw new Error('Saved snapshot is corrupt or incompatible. Delete it and save a fresh example.');
  return { schema_version: 'preparedness-snapshot-v1', app_version: value.app_version as Snapshot['app_version'], saved_at: value.saved_at,
    frame: await validateFrame(value.frame) };
}

export async function readSnapshot(): Promise<Snapshot | null> {
  const raw = localStorage.getItem(SNAPSHOT_KEY);
  return raw === null ? null : parseSnapshot(raw);
}

export type VerifiedMode = 'synthetic-demo' | 'challenge-local' | 'unavailable';
export async function verifyMode(signal: AbortSignal): Promise<VerifiedMode> {
  const response = await fetch('/api/health', { signal, cache: 'no-store', credentials: 'omit' });
  if (!response.ok) throw new Error('Python service unreachable.');
  const value: unknown = await response.json();
  if (object(value) && value.ready === true && value.mode === 'synthetic-demo' && value.catalog_sha256 === pathTrust.catalog_sha256) return 'synthetic-demo';
  if (object(value) && value.mode === 'challenge-local') return 'challenge-local';
  return 'unavailable';
}

export async function saveSnapshot(frame: PathFrame, signal: AbortSignal): Promise<Snapshot> {
  // Recheck mode at the explicit save action, never trust a stale component flag.
  if (await verifyMode(signal) !== 'synthetic-demo') throw new Error('Saving requires a verified synthetic-demo service.');
  const definition = await fetch('/api/v2/scenarios/' + encodeURIComponent(frame.scenario_id), { signal, cache: 'no-store', credentials: 'omit' });
  if (!definition.ok) throw new Error('Scenario provenance could not be verified.');
  const value: unknown = await definition.json();
  if (!object(value) || !object(value.metadata) || value.metadata.mode !== 'synthetic-demo' ||
      value.metadata.provenance !== 'independently_authored_fiction' || value.metadata.scenario_id !== frame.scenario_id ||
      value.metadata.scenario_revision !== frame.scenario_revision || value.metadata.input_fingerprint !== frame.input_fingerprint)
    throw new Error('Scenario provenance changed. Refresh before saving.');
  const snapshot: Snapshot = { schema_version: 'preparedness-snapshot-v1', app_version: PRODUCT_VERSION,
    saved_at: new Date().toISOString(), frame: await validateFrame(frame) };
  if (signal.aborted) throw new Error('Save cancelled.');
  const raw = JSON.stringify(snapshot);
  localStorage.setItem(SNAPSHOT_KEY, raw);
  if (localStorage.getItem(SNAPSHOT_KEY) !== raw) throw new Error('Snapshot was not retained by this browser.');
  return snapshot;
}

export function deleteSnapshot(): void {
  localStorage.removeItem(SNAPSHOT_KEY);
  if (localStorage.getItem(SNAPSHOT_KEY) !== null) throw new Error('Browser did not remove the snapshot.');
}
