import { test, expect, chromium, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const origin = 'http://127.0.0.1:18186';
const key = 'gridguide.preparedness.snapshot.v1';
async function start(page: Page) {
  await page.goto('/preparedness/');
  await expect(page.getByRole('button', { name: 'Save this demo snapshot' })).toBeEnabled();
}
async function save(page: Page) {
  await page.getByRole('button', { name: 'Save this demo snapshot' }).click();
  await expect(page.getByText('Fictional snapshot saved explicitly', { exact: false })).toBeVisible();
}
async function enable(page: Page) {
  await page.getByRole('button', { name: 'Enable or check offline kit' }).click();
  await expect(page.getByText('Offline kit ready on this device', { exact: true })).toBeVisible();
}

test('declared dependencies, selection, repair milestones, blocked and unknown states', async ({ page }) => {
  await start(page);
  const path = page.getByRole('list', { name: 'Fictional customer 1 ordered upstream dependencies' });
  await expect(path.getByRole('button')).toHaveCount(3);
  await path.getByRole('button', { name: /Transformer/ }).click();
  await expect(page.locator('#path-inspection')).toContainText('Repair prerequisites');
  await page.getByLabel('Prepared milestone').selectOption('2');
  await expect(path.getByRole('button', { name: /Transformer/ })).toHaveAttribute('aria-pressed','true');
  await expect(page.getByLabel('Selected fictional result')).toContainText('2 fictional customers');
  await page.getByRole('combobox', { name: 'Fictional scenario', exact: true }).selectOption('syn-blocked');
  await expect(page.getByLabel('Selected fictional result')).toContainText('Unavailable');
  await expect(page.getByRole('button', { name: /Blocked access/ })).toBeVisible();
  await expect(page.getByRole('button', { name: /Blocked by prerequisite/ })).toBeVisible();
  await page.getByRole('combobox', { name: 'Fictional scenario', exact: true }).selectOption('syn-missing');
  await expect(page.getByText('Unknown connection ↓').first()).toBeVisible();
  await page.getByLabel('Prepared milestone').selectOption('1');
  await expect(page.getByLabel('Selected fictional result')).toContainText('0 fictional customers');
  await expect(page.getByLabel('Selected fictional result')).toContainText('Unavailable');
  await expect(page.getByText('Abstract · unlocated')).toBeVisible();
});

test('keyboard semantics, reduced motion, mobile and automated accessibility', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await start(page);
  const button = page.getByRole('button', { name: /Transformer 2/ }).first();
  await button.focus(); await page.keyboard.press('Enter');
  await expect(button).toHaveAttribute('aria-pressed','true');
  expect(await button.evaluate(el => getComputedStyle(el).outlineStyle)).not.toBe('none');
  await page.keyboard.press('Tab');
  await expect(button).not.toBeFocused();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  expect(await button.evaluate(el => getComputedStyle(el).animationName)).toBe('none');
  const result = await new AxeBuilder({ page }).analyze();
  expect(result.violations.filter(v => ['serious','critical'].includes(v.impact ?? ''))).toEqual([]);
});

test('explicit save only, narrow fields, historical state, corrupt/extra fields and deletion', async ({ page }) => {
  await start(page);
  expect(await page.evaluate(key => localStorage.getItem(key),key)).toBeNull();
  await save(page);
  const record = await page.evaluate(key=>JSON.parse(localStorage.getItem(key)!),key);
  expect(Object.keys(record).sort()).toEqual(['app_version','frame','saved_at','schema_version']);
  expect(record.frame.mode).toBe('synthetic-demo');
  expect(record.frame.model_version).toBe('conditional-dependency-playback-v1');
  expect(JSON.stringify(record)).not.toMatch(/road_name|critical_c|latitude|longitude|declarations|phone|email|token|password/);
  await page.getByRole('button', { name:'Open saved snapshot' }).click();
  await expect(page.getByText('Historical fictional snapshot',{exact:true})).toBeVisible();
  await expect(page.getByLabel('Prepared milestone')).toBeDisabled();
  await page.evaluate(key=>{ const r=JSON.parse(localStorage.getItem(key)!);r.frame.nodes[0].contact='must-reject';localStorage.setItem(key,JSON.stringify(r)); },key);
  await page.reload();
  await expect(page.getByText('Snapshot storage is unavailable, corrupt or incompatible.', {exact:false})).toBeVisible();
  await expect(page.getByRole('button', {name:'Open saved snapshot'})).toBeDisabled();
  await page.getByRole('button',{name:'Delete saved snapshot'}).click();
  expect(await page.evaluate(key=>localStorage.getItem(key),key)).toBeNull();
});

test('challenge or unknown mode cannot save; no source/declaration persistence', async ({ page }) => {
  await page.route('**/api/health', route=>route.fulfill({ json:{ready:true,mode:'challenge-local'} }));
  await page.goto('/preparedness/');
  await expect(page.getByText('Challenge-local mode:',{exact:false})).toBeVisible();
  await expect(page.getByRole('button',{name:'Save this demo snapshot'})).toBeDisabled();
  expect(await page.evaluate(key=>localStorage.getItem(key),key)).toBeNull();
  await page.unroute('**/api/health');
  await page.route('**/api/health', route=>route.fulfill({ json:{ready:true,mode:'unknown'} }));
  await page.getByRole('button',{name:'Reconnect and refresh'}).click();
  await expect(page.getByText('Mode or provenance could not be verified.',{exact:false})).toBeVisible();
  await expect(page.getByRole('button',{name:'Save this demo snapshot'})).toBeDisabled();
});

test('production shell survives actual browser process restart with all network denied', async () => {
  const directory = await mkdtemp(join(tmpdir(),'gridguide-offline-browser-'));
  let context = await chromium.launchPersistentContext(directory,{channel:process.env.CI?undefined:'chrome',headless:true});
  try {
    const page = await context.newPage(); await page.goto(origin+'/preparedness/');
    await expect(page.getByRole('button',{name:'Save this demo snapshot'})).toBeEnabled();
    await page.getByRole('combobox',{name:'Fictional scenario',exact:true}).selectOption('syn-blocked');
    await page.getByLabel('Prepared milestone').selectOption('1'); await save(page); await enable(page);
    const saved = await page.evaluate(key=>localStorage.getItem(key),key);
    await context.close();
    context = await chromium.launchPersistentContext(directory,{channel:process.env.CI?undefined:'chrome',headless:true});
    await context.setOffline(true);
    const offline = await context.newPage(); await offline.goto(origin+'/preparedness/');
    await expect(offline.getByRole('heading',{name:'Your generic preparedness kit'})).toBeVisible();
    await expect(offline.getByRole('button',{name:'Save this demo snapshot'})).toBeDisabled();
    await offline.getByRole('button',{name:'Open saved snapshot'}).click();
    await expect(offline.getByText('Historical fictional snapshot',{exact:true})).toBeVisible();
    await expect(offline.getByLabel('Selected fictional result')).toContainText('Unavailable');
    await expect(offline.getByLabel('Prepared milestone')).toBeDisabled();
    expect(await offline.evaluate(key=>localStorage.getItem(key),key)).toBe(saved);
    await context.setOffline(false); await offline.getByRole('button',{name:'Reconnect and refresh'}).click();
    await expect(offline.getByRole('button',{name:'Save this demo snapshot'})).toBeEnabled();
    await expect(offline.getByText('Historical fictional snapshot',{exact:true})).toHaveCount(0);
  } finally { await context.close(); await rm(directory,{recursive:true,force:true}); }
});

test('cache exact allowlist, API/tile/POST exclusion and actual reset', async ({ page }) => {
  await start(page); await save(page); await enable(page);
  const paths = await page.evaluate(async()=>{ const out:string[]=[];for(const name of await caches.keys())for(const req of await (await caches.open(name)).keys())out.push(new URL(req.url).pathname);return out.sort(); });
  expect(paths).toContain('/preparedness/'); expect(paths).toContain('/preparedness/kit.txt');
  expect(paths.some(p=>p.includes('/api/')||p.includes('frames.json')||p.includes('fonts')||p==='/')).toBe(false);
  await page.evaluate(async()=>{ await fetch('/api/v2/scenarios',{cache:'no-store'});await fetch('/api/v2/unsupported',{method:'POST',body:'private-declaration',headers:{'Content-Type':'text/plain'}}); });
  expect(await page.evaluate(async()=>{ let n=0;for(const name of await caches.keys())n+=(await (await caches.open(name)).keys()).length;return n; })).toBe(paths.length);
  await page.getByRole('button',{name:'Reset preparedness storage'}).click();
  await expect(page.getByText('Preparedness cache and snapshot removed.',{exact:false})).toBeVisible();
  expect(await page.evaluate(async()=>({ keys:await caches.keys(),snapshot:localStorage.getItem('gridguide.preparedness.snapshot.v1'),registration:Boolean(await navigator.serviceWorker.getRegistration('/preparedness/')) }))).toEqual({keys:[],snapshot:null,registration:false});
});

test('storage denial, quota, unavailable worker and downloadable fallback', async ({ browser }) => {
  for (const fault of ['denied', 'quota', 'worker']) {
    const context = await browser.newContext(); const page = await context.newPage();
    await page.addInitScript(fault => {
      if (fault === 'denied') Object.defineProperty(window, 'localStorage', {get(){throw new DOMException('denied','SecurityError');}});
      if (fault === 'quota') Storage.prototype.setItem = () => {throw new DOMException('full','QuotaExceededError');};
      if (fault === 'worker') Object.defineProperty(navigator, 'serviceWorker', {value:undefined});
    },fault);
    await start(page);
    if (fault !== 'worker') {
      await page.getByRole('button',{name:'Save this demo snapshot'}).click();
      await expect(page.getByText('Snapshot was not saved:',{exact:false})).toBeVisible();
      await expect(page.getByRole('button',{name:'Open saved snapshot'})).toBeDisabled();
    } else {
      await page.getByRole('button',{name:'Enable or check offline kit'}).click();
      await expect(page.getByText('Offline caching unavailable.',{exact:false})).toBeVisible();
    }
    const download = page.waitForEvent('download');
    await page.getByRole('button',{name:'Download generic kit'}).click();
    expect((await download).suggestedFilename()).toBe('gridguide-generic-preparedness.txt');
    await context.close();
  }
});

test('snapshot versions and arbitrary free text fail closed; deletion works across tabs', async ({ page, context }) => {
  await start(page); await save(page);
  const original = await page.evaluate(key=>localStorage.getItem(key)!,key);
  for (const mutation of ['schema','text','mode','root','json']) {
    await page.evaluate(({key,original,mutation})=>{
      const record=JSON.parse(original);
      if(mutation==='schema')record.schema_version='preparedness-snapshot-v99';
      if(mutation==='text')record.frame.nodes[0].reason='unapproved arbitrary free text';
      if(mutation==='mode')record.frame.mode='challenge-local';
      if(mutation==='root')record.declarations={medical:true};
      localStorage.setItem(key,mutation==='json'?'{broken':JSON.stringify(record));
    },{key,original,mutation});
    await page.reload();
    await expect(page.getByText('Snapshot storage is unavailable, corrupt or incompatible.',{exact:false})).toBeVisible();
    await expect(page.getByRole('button',{name:'Open saved snapshot'})).toBeDisabled();
  }
  await start(page); await save(page);
  const other=await context.newPage();await start(other);
  await other.getByRole('button',{name:'Open saved snapshot'}).click();
  await expect(other.getByText('Historical fictional snapshot',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Delete saved snapshot'}).click();
  await expect(other.getByText('Historical fictional snapshot',{exact:true})).toHaveCount(0);
  await expect(other.getByRole('button',{name:'Open saved snapshot'})).toBeDisabled();
});

test('stale save cancellation and provenance changes never persist a result', async ({ page }) => {
  await start(page);
  let release!:()=>void;const gate=new Promise<void>(resolve=>release=resolve);
  let requested!:()=>void;const entered=new Promise<void>(resolve=>requested=resolve);
  await page.route('**/api/v2/scenarios/syn-simple',async route=>{requested();await gate;await route.continue().catch(()=>{});});
  await page.getByRole('button',{name:'Save this demo snapshot'}).click();await entered;
  await page.getByRole('combobox',{name:'Fictional scenario',exact:true}).selectOption('syn-missing');release();
  await page.unroute('**/api/v2/scenarios/syn-simple');
  await page.route('**/api/health',route=>route.fulfill({json:{ready:true,mode:'challenge-local'}}));
  await page.getByRole('button',{name:'Save this demo snapshot'}).click();
  await expect(page.getByText('Snapshot was not saved:',{exact:false})).toBeVisible();
  expect(await page.evaluate(key=>localStorage.getItem(key),key)).toBeNull();
});

test('corrupted cache is not ready; worker update migrates only its own caches', async ({ page, request }) => {
  await request.post('/__test__/worker/0');
  try {
    await start(page);await enable(page);
    await page.evaluate(async()=>{
      await caches.open('unrelated-application-cache');
      await caches.open('gridguide-preparedness-old-schema');
      for(const name of await caches.keys())if(name.startsWith('gridguide-preparedness-')&&!name.endsWith('old-schema'))
        await (await caches.open(name)).put('/preparedness/kit.txt',new Response('corrupt'));
    });
    await page.getByRole('button',{name:'Enable or check offline kit'}).click();
    await expect(page.getByText('Offline kit not verified',{exact:true})).toBeVisible();
    await request.post('/__test__/worker/1');
    await page.getByRole('button',{name:'Enable or check offline kit'}).click();
    await expect(page.getByRole('button',{name:'Apply available update and reload'})).toBeVisible();
    await page.getByRole('button',{name:'Apply available update and reload'}).click();
    await expect(page.getByText('Offline kit ready on this device',{exact:true})).toBeVisible();
    const names=await page.evaluate(()=>caches.keys());
    expect(names).toContain('unrelated-application-cache');
    expect(names.filter(n=>n.startsWith('gridguide-preparedness-'))).toHaveLength(1);
    expect(names.some(n=>n.startsWith('gridguide-preparedness-test1-'))).toBe(true);
    await page.getByRole('button',{name:'Reset preparedness storage'}).click();
    await expect(page.getByText('Preparedness cache and snapshot removed.',{exact:false})).toBeVisible();
    expect(await page.evaluate(()=>caches.keys())).toEqual(['unrelated-application-cache']);
  } finally { await request.post('/__test__/worker/0'); }
});

test('all fictional path states and historical snapshot have no serious or critical axe findings', async ({ page }) => {
  await start(page);
  for(const id of ['syn-simple','syn-branching','syn-overlap','syn-blocked','syn-missing','syn-critical']) {
    await page.getByRole('combobox',{name:'Fictional scenario',exact:true}).selectOption(id);
    const result=await new AxeBuilder({page}).analyze();
    expect(result.violations.filter(v=>['serious','critical'].includes(v.impact??'')),id).toEqual([]);
  }
  await save(page);await page.getByRole('button',{name:'Open saved snapshot'}).click();
  const result=await new AxeBuilder({page}).analyze();
  expect(result.violations.filter(v=>['serious','critical'].includes(v.impact??''))).toEqual([]);
});

test('missing service and damaged artifact leave generic guidance; later refresh cannot revive stale data', async ({ page }) => {
  await page.route('**/preparedness/frames.json',route=>route.fulfill({json:{version:'forged',frames:[]}}));
  await page.goto('/preparedness/');
  await expect(page.getByText('Python service unreachable or artifact unavailable.',{exact:false})).toBeVisible();
  await expect(page.getByRole('button',{name:'Save this demo snapshot'})).toBeDisabled();
  await expect(page.getByRole('heading',{name:'Your generic preparedness kit'})).toBeVisible();
  await page.unroute('**/preparedness/frames.json');
  await page.route('**/api/health',route=>route.abort('connectionrefused'));
  await page.getByRole('button',{name:'Reconnect and refresh'}).click();
  await expect(page.getByRole('combobox',{name:'Fictional scenario'})).toBeDisabled();
  await expect(page.getByLabel('Selected fictional result')).toHaveCount(0);
});

test('browser evidence: selected dependency, narrow screen, and offline historical view', async ({ page, context }, info) => {
  await start(page);
  await page.locator('.generic-kit').screenshot({path:info.outputPath('generic-kit.png')});
  await page.getByRole('button',{name:/Transformer 2/}).first().click();
  await page.locator('.fictional-area').screenshot({path:info.outputPath('power-path-desktop.png')});
  await page.setViewportSize({width:390,height:844});
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.getByRole('combobox',{name:'Fictional scenario'}).selectOption('syn-missing');
  await page.locator('.fictional-area').screenshot({path:info.outputPath('power-path-mobile-unresolved.png')});
  await save(page);await enable(page);await context.setOffline(true);
  await page.getByRole('button',{name:'Open saved snapshot'}).click();
  await expect(page.getByText('Historical fictional snapshot',{exact:true})).toBeVisible();
  await page.locator('.fictional-area').screenshot({path:info.outputPath('offline-snapshot.png')});
  const axe=await new AxeBuilder({page}).analyze();
  expect(axe.violations.filter(v=>['serious','critical'].includes(v.impact??''))).toEqual([]);
  await info.attach('offline-accessibility',{body:JSON.stringify({violations:axe.violations,passes:axe.passes.map(p=>p.id)},null,2),contentType:'application/json'});
});
