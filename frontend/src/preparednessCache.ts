const SCOPE = '/preparedness/';
export async function cacheReady(): Promise<boolean> {
  if (!('serviceWorker' in navigator)) return false;
  const registration = await navigator.serviceWorker.getRegistration(SCOPE);
  if (!registration?.active) return false;
  return new Promise(resolve => {
    const channel = new MessageChannel();
    const timer = setTimeout(() => { channel.port1.close(); resolve(false); }, 5000);
    channel.port1.onmessage = event => { clearTimeout(timer); channel.port1.close(); resolve(event.data?.ready === true); };
    registration.active!.postMessage('VERIFY', [channel.port2]);
  });
}
export async function installKit(): Promise<{ ready: boolean; update: boolean }> {
  if (!('serviceWorker' in navigator)) throw new Error('This browser cannot cache the kit. Print or download it instead.');
  const registration = await navigator.serviceWorker.register('/preparedness/service-worker.js', { scope: SCOPE, updateViaCache: 'none' });
  await registration.update();
  const worker = registration.installing;
  if (worker) await new Promise<void>((resolve, reject) => {
    const timer = setTimeout(() => { worker.removeEventListener('statechange', change); reject(new Error('Offline installation timed out. Retry while connected.')); }, 15000);
    const change = () => {
      if (['installed','activated','redundant'].includes(worker.state)) {
        clearTimeout(timer); worker.removeEventListener('statechange', change);
        worker.state === 'redundant' ? reject(new Error('Offline installation failed integrity or storage checks.')) : resolve();
      }
    };
    worker.addEventListener('statechange', change); change();
  });
  // Initial activation can follow installation asynchronously; a bounded wait only.
  for (let i=0;i<20 && !registration.active && !registration.waiting;i++) await new Promise(resolve=>setTimeout(resolve,100));
  return { ready: await cacheReady(), update: Boolean(registration.waiting) };
}
export async function activateUpdate(): Promise<void> {
  const registration = await navigator.serviceWorker.getRegistration(SCOPE);
  if (!registration?.waiting) { location.reload(); return; }
  navigator.serviceWorker.addEventListener('controllerchange', () => location.reload(), { once: true });
  registration.waiting.postMessage('ACTIVATE');
}
export async function removeKit(): Promise<void> {
  if ('serviceWorker' in navigator) {
    const registration = await navigator.serviceWorker.getRegistration(SCOPE);
    if (registration && !await registration.unregister()) throw new Error('Offline worker could not be removed.');
  }
  if ('caches' in window) {
    for (const key of await caches.keys()) if (key.startsWith('gridguide-preparedness-')) await caches.delete(key);
    if ((await caches.keys()).some(key=>key.startsWith('gridguide-preparedness-'))) throw new Error('Offline cache could not be removed.');
  }
}
