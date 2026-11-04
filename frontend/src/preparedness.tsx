import { PublicShell } from './PublicShell';
import { linkedFrame } from './frameSelection';
import { createRoot } from 'react-dom/client';
import { useEffect, useRef, useState } from 'react';
import { PowerPath } from './PowerPath';
import { deleteSnapshot, loadFrames, readSnapshot, saveSnapshot, verifyMode, SNAPSHOT_KEY } from './offline';
import type { PathFrame, Snapshot, VerifiedMode } from './offline';
import { activateUpdate, cacheReady, installKit, removeKit } from './preparednessCache';
import kit from '../public/preparedness/kit.txt?raw';


function Preparedness() {
  const [mode, setMode] = useState<VerifiedMode>('unavailable');
  const [frames, setFrames] = useState<PathFrame[]>([]);
  const [frame, setFrame] = useState<PathFrame | null>(null);
  const [stored, setStored] = useState<Snapshot | null>(null);
  const [historical, setHistorical] = useState<Snapshot | null>(null);
  const [message, setMessage] = useState('Checking the Python service. Generic guidance is available below.');
  const [storageMessage, setStorageMessage] = useState('');
  const [ready, setReady] = useState(false);
  const [update, setUpdate] = useState(false);
  const [cacheMessage, setCacheMessage] = useState('Offline readiness has not been verified.');
  const [busy, setBusy] = useState(false);
  const [cacheBusy, setCacheBusy] = useState(false);
  const request = useRef<AbortController | null>(null);
  const saving = useRef<AbortController | null>(null);
  const storageRevision = useRef(0);
  const viewRevision = useRef(0);
  const cacheRevision = useRef(0);
  const alive = useRef(true);

  function cancelSave() { saving.current?.abort(); saving.current = null; setBusy(false); }
  async function inspectStorage() {
    const revision = ++storageRevision.current;
    try { const snapshot = await readSnapshot(); if (alive.current && revision === storageRevision.current) { setStored(snapshot); setStorageMessage(''); } }
    catch { if (alive.current && revision === storageRevision.current) { setStored(null); setStorageMessage('Snapshot storage is unavailable, corrupt or incompatible. You can delete it; generic guidance remains available.'); } }
  }
  async function refresh() {
    ++viewRevision.current;
    request.current?.abort(); cancelSave();
    const controller = new AbortController(); request.current = controller;
    const signal = AbortSignal.any([controller.signal, AbortSignal.timeout(10000)]);
    setMode('unavailable'); setFrames([]); setFrame(null); setHistorical(null);
    setMessage('Checking service mode and fictional artifact provenance…');
    try {
      const currentMode = await verifyMode(signal);
      const choices = currentMode === 'synthetic-demo' ? await loadFrames(signal) : [];
      if (controller.signal.aborted || !alive.current) return;
      setMode(currentMode); setFrames(choices); setFrame(linkedFrame(choices, window.location.hash) ?? choices[0] ?? null);
      setMessage(currentMode === 'synthetic-demo' ? 'Synthetic demo verified. These are precomputed fictional milestones, not live outage information.' :
        currentMode === 'challenge-local' ? 'Challenge-local mode: only the generic preparedness kit is available here. Challenge snapshots are disabled.' :
          'Mode or provenance could not be verified. Fictional examples and saving are disabled.');
      if (currentMode === 'challenge-local') {
        ++storageRevision.current; setStored(null); setHistorical(null);
        try { deleteSnapshot(); setStorageMessage('Any prior fictional snapshot on this origin has been removed for challenge-local mode.'); }
        catch { setStorageMessage('Snapshot removal was blocked by this browser. Clear this site’s storage in browser settings.'); }
      }
    } catch { if (!controller.signal.aborted && alive.current) setMessage('Python service unreachable or artifact unavailable. Recalculation and new example selection are disabled. Open an explicitly saved snapshot or use the generic kit.'); }
  }
  useEffect(() => {
    alive.current = true;
    void inspectStorage(); void refresh();
    const revision = cacheRevision.current;
    void cacheReady().then(value => { if (alive.current && revision === cacheRevision.current) { setReady(value); setCacheMessage(value ? 'Required shell resources verified on this device.' : 'Offline kit is not yet ready.'); } }).catch(() => { if (alive.current && revision === cacheRevision.current) setCacheMessage('Cache access unavailable. Print or download the generic kit.'); });
    const disconnected = () => { ++viewRevision.current; request.current?.abort(); cancelSave(); setMode('unavailable'); setFrame(null); setFrames([]); setMessage('Network disconnected. No numerical recalculation is available. Saved snapshots are historical fiction.'); };
    const connected = () => setMessage('Connection may be available. Use Reconnect and refresh to verify the service before selecting a new example.');
    const storageChanged = (event: StorageEvent) => { if (event.key === SNAPSHOT_KEY || event.key === null) { ++viewRevision.current; setHistorical(null); cancelSave(); void inspectStorage(); } };
    window.addEventListener('offline', disconnected); window.addEventListener('online', connected); window.addEventListener('storage', storageChanged);
    return () => { alive.current = false; request.current?.abort(); saving.current?.abort(); ++storageRevision.current;
      window.removeEventListener('offline', disconnected); window.removeEventListener('online', connected); window.removeEventListener('storage', storageChanged); };
  }, []);

  function select(next: PathFrame | undefined) { ++viewRevision.current; cancelSave(); setHistorical(null); setFrame(next ?? null); }
  async function save() {
    if (!frame || mode !== 'synthetic-demo' || historical) return;
    cancelSave(); const controller = new AbortController(); saving.current = controller; setBusy(true);
    try {
      const snapshot = await saveSnapshot(frame, AbortSignal.any([controller.signal, AbortSignal.timeout(10000)]));
      if (!controller.signal.aborted) { ++storageRevision.current; setStored(snapshot); setStorageMessage('Fictional snapshot saved explicitly on this device. It is historical immediately, not a utility update.'); }
    } catch { if (!controller.signal.aborted) setStorageMessage('Snapshot was not saved: storage, service or provenance verification failed. No offline readiness is implied.'); }
    finally { if (saving.current === controller) { saving.current = null; setBusy(false); } }
  }
  async function openSaved() {
    const revision = ++viewRevision.current;
    cancelSave();
    try { const value = await readSnapshot(); if (!alive.current || revision !== viewRevision.current || mode === 'challenge-local') return; setStored(value); setHistorical(value); setStorageMessage(value ? 'Opened a historical fictional snapshot. Refresh explicitly to return to server-verified examples.' : 'No saved snapshot remains.'); }
    catch { if (alive.current && revision === viewRevision.current) { setHistorical(null); setStored(null); setStorageMessage('Saved snapshot could not be validated. Delete it and save a fresh example.'); } }
  }
  function removeSnapshot() {
    ++viewRevision.current;
    cancelSave(); ++storageRevision.current; setHistorical(null);
    try { deleteSnapshot(); setStored(null); setStorageMessage('Snapshot deleted from this device.'); }
    catch { setStorageMessage('Deletion failed. Use browser site-data controls; this page cannot confirm removal.'); }
  }
  async function enableOffline() {
    ++cacheRevision.current; setCacheBusy(true);
    setCacheMessage('Installing and verifying the minimal generic shell…');
    try { const result = await installKit(); setReady(result.ready); setUpdate(result.update);
      setCacheMessage(result.ready ? 'Required shell resources verified on this device.' : 'Installation has not established offline readiness. Retry while connected.'); }
    catch { setReady(false); setCacheMessage('Offline caching unavailable. Print or download the generic kit; do not rely on browser restart working offline.'); }
    finally { setCacheBusy(false); }
  }
  async function reset() {
    ++cacheRevision.current; setCacheBusy(true);
    ++viewRevision.current;
    cancelSave(); ++storageRevision.current; setHistorical(null);
    try { deleteSnapshot(); setStored(null); await removeKit(); setReady(false); setUpdate(false); setCacheMessage('Preparedness cache and snapshot removed. Enable offline access again when needed.'); }
    catch { setReady(false); setCacheMessage('Reset could not confirm removal of all data. Use browser site-data controls.'); }
    finally { setCacheBusy(false); }
  }
  const shown = historical?.frame ?? frame;
  const scenarios = frames.filter(f => f.step === 0);
  return <PublicShell page="prepare" mainId="preparedness-main">
    <main id="preparedness-main" className="journey-page" tabIndex={-1}>
      <div className="no-print page-intro"><div><span className="eyebrow">Be ready, with clear limits</span><h1>Prepare for an outage</h1>
        <p>Keep general safety guidance close. Explore explicitly fictional dependencies without confusing them with your utility’s network.</p>
        <p className="fine">Communication previews and tailored declarations require authorized challenge-local inputs. This public kit provides general guidance; no messages are sent.</p></div></div>
      <nav className="journey-sections no-print" aria-label="Preparedness sections"><a href="#kit-title">Safety kit</a><a href="#offline-title">Offline access</a><a href="#fiction-title">Fictional power path & snapshot</a></nav>
      <div className="no-print"><p className="notice" role="status">{message}</p>
        <button onClick={() => void refresh()}>Reconnect and refresh</button>
      </div>
      <section className="generic-kit" aria-labelledby="kit-title">
        <h2 id="kit-title">Your generic preparedness kit</h2>
        <p>Reviewed November 3, 2026 · offline reference, not live outage awareness.</p>
        <div className="kit-copy">{kit.split('\n').slice(3, -2).join('\n')}</div>
        <p><a href="https://www.redcross.org/get-help/how-to-prepare-for-emergencies/types-of-emergencies/power-outage.html">Source: American Red Cross power outage safety</a> (requires a connection).</p>
        <div className="actions no-print"><button onClick={() => window.print()}>Print generic kit</button>
          <button onClick={() => { const url = URL.createObjectURL(new Blob([kit], { type: 'text/plain' })); const a = document.createElement('a'); a.href = url; a.download = 'gridguide-generic-preparedness.txt'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); }}>Download generic kit</button></div>
      </section>
      <section className="offline-controls no-print" aria-labelledby="offline-title"><h2 id="offline-title">Keep this page available offline</h2>
        <p><strong>{ready ? 'Offline kit ready on this device' : 'Offline kit not verified'}</strong></p><p role="status">{cacheMessage}</p>
        <p>Browsers can evict stored data. Check readiness before relying on it. Only the generic shell is cached; API responses, declarations, map tiles and challenge data are excluded.</p>
        <div className="actions"><button disabled={cacheBusy} onClick={() => void enableOffline()}>Enable or check offline kit</button>
          {update && <button onClick={() => void activateUpdate().catch(() => setCacheMessage('Update could not be applied. Retry while connected.'))}>Apply available update and reload</button>}
          <button disabled={cacheBusy} onClick={() => void reset()}>Reset preparedness storage</button></div>
      </section>
      <section className="fictional-area no-print" aria-labelledby="fiction-title"><span className="eyebrow">A learning example</span><h2 id="fiction-title">Understand a fictional power path</h2>
        <p>Explore fictional repair milestones and their customer dependencies. These examples do not predict outages or provide calibrated restoration confidence.</p>
        <fieldset disabled={mode !== 'synthetic-demo' || Boolean(historical)}><legend>Choose a precomputed example</legend>
          <label>Fictional scenario<select value={frame?.scenario_id ?? ''} onChange={event => select(frames.find(f => f.scenario_id === event.target.value && f.step === 0))}>
            <option value="" disabled>Requires verified synthetic mode</option>{scenarios.map(f => <option value={f.scenario_id} key={f.scenario_id}>{f.label}</option>)}</select></label>
          <label>Prepared milestone<select value={frame?.step ?? 0} onChange={event => select(frames.find(f => f.scenario_id === frame?.scenario_id && f.step === Number(event.target.value)))}>
            {frames.filter(f => f.scenario_id === frame?.scenario_id).map(f => <option key={f.step} value={f.step}>{f.step_label}</option>)}</select></label>
        </fieldset>
        <div className="actions"><button disabled={!frame || mode !== 'synthetic-demo' || Boolean(historical) || busy} onClick={() => void save()}>Save this demo snapshot</button>
          <button disabled={!stored || mode === 'challenge-local'} onClick={() => void openSaved()}>Open saved snapshot</button>
          <button onClick={removeSnapshot}>Delete saved snapshot</button></div>
        <p role="status">{storageMessage}</p>
        {stored && <p>Snapshot saved on this device: <time dateTime={stored.saved_at}>{stored.saved_at}</time>. Age never establishes utility validity.</p>}
        {historical && <aside className="notice historical"><strong>Historical fictional snapshot</strong><p>Saved {historical.saved_at}. No live server result or recalculation. App {historical.app_version}.</p></aside>}
        {shown && <><section className="frame-summary" aria-label="Selected fictional result"><h3>{shown.label} · {shown.step_label}</h3>
          <p>Selected milestone: {shown.elapsed_hours} conditional elapsed hours after modeled response start.</p>
          <p>{shown.released_customers} fictional customers have completed declared dependencies; {shown.unresolved_customers} have unresolved release.</p>
          <p>Full modeled completion: {shown.completion_hours === null ? 'Unavailable — unresolved dependencies remain.' : `${shown.completion_hours} conditional elapsed hours from modeled response start; not a utility ETR.`}</p>
          <details><summary>Versions and fictional provenance</summary><p>Independently authored fiction · revision {shown.scenario_revision}. Model: {shown.model_version}. Policy: {shown.policy_id}. One effective worker per crew is an assumption.</p>
            <p className="fingerprint">Input: {shown.input_fingerprint}<br/>Result: {shown.result_fingerprint}</p></details></section><PowerPath frame={shown}/></>}
      </section>
    </main></PublicShell>;
}

createRoot(document.getElementById('root')!).render(<Preparedness/>);
