/* ALLOW and CACHE are supplied only by the production build. No runtime caching. */
const PREFIX = 'gridguide-preparedness-';
async function hash(response) {
  return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', await response.arrayBuffer())),
    b => b.toString(16).padStart(2, '0')).join('');
}
async function verify() {
  if (!await caches.has(CACHE)) return false;
  const cache = await caches.open(CACHE);
  for (const [path, expected] of Object.entries(ALLOW)) {
    const response = await cache.match(path);
    if (!response || await hash(response) !== expected) return false;
  }
  return true;
}
self.addEventListener('install', event => event.waitUntil((async () => {
  const cache = await caches.open(CACHE);
  try {
    for (const [path, expected] of Object.entries(ALLOW)) {
      const response = await fetch(path, { cache: 'reload', credentials: 'omit' });
      if (!response.ok || response.redirected || await hash(response.clone()) !== expected) throw new Error('Shell integrity failure');
      await cache.put(path, response);
    }
    if (!await verify()) throw new Error('Shell incomplete');
  } catch (error) {
    await caches.delete(CACHE);
    throw error;
  }
})()));
self.addEventListener('activate', event => event.waitUntil((async () => {
  for (const key of await caches.keys()) if (key.startsWith(PREFIX) && key !== CACHE) await caches.delete(key);
  await self.clients.claim();
})()));
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || url.origin !== self.location.origin || url.search || !Object.hasOwn(ALLOW, url.pathname)) return;
  event.respondWith((async () => {
    if (!await caches.has(CACHE)) return fetch(event.request);
    const cache = await caches.open(CACHE);
    const response = await cache.match(url.pathname);
    if (response && await hash(response.clone()) === ALLOW[url.pathname]) return response;
    // A missing/changed resource is not silently cached or declared offline ready.
    return fetch(event.request);
  })());
});
self.addEventListener('message', event => {
  const source = event.source && new URL(event.source.url);
  if (!source || source.origin !== self.location.origin || !source.pathname.startsWith('/preparedness/')) return;
  if (event.data === 'ACTIVATE') event.waitUntil(self.skipWaiting());
  if (event.data === 'VERIFY') event.waitUntil((async () => {
    try { event.ports[0]?.postMessage({ ready: await verify(), version: CACHE }); }
    catch { event.ports[0]?.postMessage({ ready: false, version: CACHE }); }
  })());
});
