import { expect, test, type Page, type Locator } from '@playwright/test';
import type { Analysis } from '../src/api';

const normalApi = 'http://127.0.0.1:18080';
const missingRiskApi = 'http://127.0.0.1:18081';
const evaluations = new WeakMap<Page, Analysis[]>();
const browserErrors = new WeakMap<Page, string[]>();

async function useApi(page: Page, origin = normalApi) {
  await page.route('**/api/**', async route => {
    const url = new URL(route.request().url());
    const response = await route.fetch({ url: `${origin}${url.pathname}${url.search}` });
    if (url.pathname === '/api/evaluate' && response.ok()) {
      evaluations.get(page)!.push(await response.json() as Analysis);
    }
    await route.fulfill({ response });
  });
}

test.beforeEach(async ({ page }) => {
  evaluations.set(page, []);
  browserErrors.set(page, []);
  page.on('pageerror', error => browserErrors.get(page)!.push(error.message));
  // Numerical behavior and the map's vector alternative must not depend on
  // external tiles, fonts, analytics or a live provider.
  await page.route('**/*', route => {
    const url = new URL(route.request().url());
    return ['127.0.0.1', 'localhost'].includes(url.hostname) ? route.continue() : route.abort();
  });
  await useApi(page);
});

test.afterEach(async ({ page }) => {
  expect(browserErrors.get(page)).toEqual([]);
});

async function start(page: Page, hash = '#overview') {
  await page.goto(`/${hash}`);
  await expect(page.getByTestId('restoration-result').first()).toContainText('2.5–12');
}

async function nav(page: Page, name: 'Overview' | 'Prepare & alerts' | 'Grid insights') {
  await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('link', { name, exact: true }).click();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText(name === 'Overview' ? 'Your storm outlook' : name === 'Prepare & alerts' ? 'Prepare & stay informed' : 'Grid insights');
}

async function explore(page: Page) {
  const control = page.getByText('Explore this range', { exact: true });
  if (await control.count() && !(await page.getByRole('radio', { name: /^2 people/ }).isVisible())) await control.click();
}

async function result(page: Page, text: string) {
  await expect(page.getByTestId('restoration-result').first()).toContainText(text === 'unavailable' ? /isn.t available|unavailable/i : text);
}

async function crew(page: Page, people: number, expected: string) {
  await page.getByRole('radio', { name: new RegExp(`^${people} people`) }).check();
  await result(page, expected);
}

async function access(page: Page, name: string, expected: string) {
  await page.getByRole('radio', { name: new RegExp(`^${name}`) }).check();
  await result(page, expected);
}

function latest(page: Page) { return evaluations.get(page)!.at(-1)!; }
function update(data: Analysis) { return data.customer_journey.messages.find(message => message.state === 'estimate_updated')!; }

async function stage(page: Page, name: string) {
  await page.getByRole('radio', { name: new RegExp(name) }).check();
}

async function grid(page: Page) {
  await nav(page, 'Grid insights');
  await expect(page.getByTestId('decision-recommendation')).toBeVisible();
  await expect(page.getByTestId('policy-tradeoff')).toBeVisible();
  return page.getByTestId('restoration-decision');
}

async function visibleVectorGeometry(map: Locator) {
  const canvas = map.locator('.leaflet-overlay-pane > svg');
  await expect.poll(async () => (await canvas.boundingBox())?.width ?? 0).toBeGreaterThan(200);
  await expect.poll(async () => canvas.locator('path').evaluateAll(paths => paths.filter(path => {
    const box = path.getBoundingClientRect();
    return box.width > 0 && box.height > 0;
  }).length)).toBeGreaterThan(0);
}

test('customer-first overview gives the situation, actual location choice and honest delivery state', async ({ page }) => {
  await start(page);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Your storm outlook');
  await page.evaluate(() => document.fonts.ready);
  expect(await page.evaluate(() => document.fonts.check('18px Barlow') && document.fonts.check('700 40px \"Barlow Semi Condensed\"'))).toBe(true);
  await expect(page.getByTestId('risk-band')).toHaveText('HIGH');
  await expect(page.getByText(/Live outage status isn.t connected/)).toBeVisible();
  await expect(page.getByText(/No notifications are being sent/).first()).toBeVisible();
  await expect(page.getByRole('button', { name: 'Prepare now', exact: true })).toBeVisible();
  await expect(page.getByText(/After crew response begins/).first()).toBeVisible();
  const hero = await page.getByTestId('restoration-result').first().boundingBox();
  expect(hero!.y + hero!.height).toBeLessThan(900);
  expect(await page.getByTestId('restoration-decision').count()).toBe(0);
  await explore(page); await crew(page, 2, '5.5–12');
  const selectedResult = latest(page).result.result_id;
  await page.getByText('Choose location', { exact: true }).click();
  await expect(page.getByRole('radio', { name: /Demo location A/ })).toBeVisible();
  await page.getByRole('button', { name: 'Use this location', exact: true }).click();
  await expect(page.locator('.location-selector > summary')).toBeFocused();
  await result(page, '5.5–12');
  expect(latest(page).result.result_id).toBe(selectedResult);
  await expect(page.locator('input[type="text"], input[type="email"], input[type="tel"]')).toHaveCount(0);
});

test('B1 crew changes compare authoritative endpoints in both directions without false sooner/later claims', async ({ page }) => {
  await start(page); await explore(page);
  for (const [people, before, after] of [[2, '2.5–12', '5.5–12'], [4, '5.5–12', '2.5–12']] as const) {
    await crew(page, people, after);
    const data = latest(page);
    expect(update(data).body).toContain(`from ${before} to ${after} elapsed hours`);
    expect(update(data).body).not.toMatch(/\b(sooner|later)\b/i);
    expect(data.customer_journey.estimate_update_eligible).toBe(false);
    await nav(page, 'Prepare & alerts');
    await stage(page, 'Estimate updated');
    await expect(page.getByTestId('message-preview')).toContainText(update(data).body);
    await nav(page, 'Overview'); await explore(page);
  }
  await crew(page, 8, '1–12'); await access(page, 'Restricted', '2–16.5');
  await crew(page, 2, '8–16.5');
  expect(update(latest(page)).body).toContain('from 2–16.5 to 8–16.5');
  expect(latest(page).customer_journey.estimate_update_eligible).toBe(true);
  await crew(page, 8, '2–16.5');
  expect(update(latest(page)).body).toContain('from 8–16.5 to 2–16.5');
  expect(update(latest(page)).body).not.toMatch(/\b(sooner|later)\b/i);
});

test('B1 unchanged, both-endpoint, mixed and availability transitions retain correct semantics through the real API', async ({ request }) => {
  const transitions = [
    ['clear', 4, 'clear', 4], ['restricted', 4, 'clear', 4], ['clear', 4, 'restricted', 4],
    ['clear', 2, 'restricted', 8], ['restricted', 8, 'clear', 2],
    ['clear', 4, 'restricted', 6], ['restricted', 6, 'clear', 4],
    ['clear', 4, 'blocked', 4], ['blocked', 4, 'clear', 4], ['blocked', 4, 'blocked', 4],
  ] as const;
  for (const [before, people, after, nextPeople] of transitions) {
    const response = await request.post(`${normalApi}/api/evaluate`, { data: {
      access: after, crew_size: nextPeople, scenario_revision: 2,
      previous: { access: before, crew_size: people, scenario_revision: 1 },
    } });
    expect(response.status()).toBe(200);
    const data = await response.json() as Analysis;
    expect(update(data).body).not.toMatch(/\b(sooner|later)\b/i);
    if (before === after && people === nextPeople) expect(update(data).available).toBe(false);
    else if (after === 'blocked') {
      expect(data.result.restoration.display_hours).toBeNull();
      expect(update(data).body).toContain('Pending access clearance');
      expect(update(data).body).not.toMatch(/\d/);
    } else if (before === 'blocked') expect(update(data).body).toContain('available again');
    else expect(update(data).body).toContain('range changed from');
  }
});

test('B1 BLOCKED is intentional and returning finite restores a conditional range', async ({ page }) => {
  await start(page); await explore(page);
  await access(page, 'Blocked', 'unavailable');
  expect(latest(page).result.restoration.display_hours).toBeNull();
  expect(update(latest(page)).body).toContain('Pending access clearance');
  await nav(page, 'Prepare & alerts'); await stage(page, 'Estimate updated');
  await expect(page.getByTestId('message-preview')).toContainText('No finite restoration outlook');
  await nav(page, 'Overview'); await explore(page);
  await access(page, 'Clear', '2.5–12');
  expect(update(latest(page)).body).toContain('range is available again');
});

test('preparation completion, explicit declarations and customer settings survive navigation but not reload', async ({ page }) => {
  await start(page); await nav(page, 'Prepare & alerts');
  const charge = page.getByRole('checkbox', { name: 'Charge phones and power banks.', exact: true });
  await charge.check();
  const before = latest(page).result;
  for (const name of ['Powered medical equipment / medical need', 'Accessibility assistance', 'Critical responsibility']) {
    await page.getByRole('checkbox', { name, exact: true }).check();
    await expect.poll(() => latest(page).customer_journey.declared_needs.selections.length).toBe(
      name === 'Powered medical equipment / medical need' ? 1 : name === 'Accessibility assistance' ? 2 : 3);
  }
  await expect(page.locator('.declared-guidance li')).toHaveCount(3);
  expect(latest(page).result.restoration).toEqual(before.restoration);
  expect(latest(page).result.risk).toEqual(before.risk);
  await expect(page.getByTestId('alert-eligibility')).toContainText('Eligible');
  await expect(page.locator('.journey-channels').getByText('Phone call', { exact: true })).toBeVisible();
  await nav(page, 'Overview'); await nav(page, 'Prepare & alerts');
  await expect(charge).toBeChecked();
  await expect(page.locator('.declared-guidance li')).toHaveCount(3);
  await page.goBack(); await expect(page).toHaveURL(/#overview$/);
  await page.goForward(); await expect(page).toHaveURL(/#prepare$/);
  await expect(charge).toBeChecked();
  expect(await page.evaluate(() => ({ local: Object.keys(localStorage), session: Object.keys(sessionStorage) }))).toEqual({ local: [], session: [] });
  expect(page.url()).not.toMatch(/medical|accessibility|critical_responsibility/);
  await page.reload();
  await expect(charge).not.toBeChecked();
  await expect(page.locator('.declared-guidance li')).toHaveCount(0);
  expect(latest(page).customer_journey.declared_needs.selections).toEqual([]);
});

test('four communication stages remain examples and never change live utility confirmation', async ({ page }) => {
  await start(page); await nav(page, 'Prepare & alerts');
  const confirmation = latest(page).result.confirmed_utility;
  for (const name of ['Pre-storm', 'Outage confirmed', 'Estimate updated', 'Restored']) {
    await stage(page, name);
    const message = latest(page).customer_journey.messages.find(item => item.title === name)!;
    await expect(page.getByTestId('message-preview')).toContainText(message.body);
    await expect(page.getByTestId('message-preview')).toContainText(name);
    expect(latest(page).result.confirmed_utility).toEqual(confirmation);
  }
  await expect(page.locator('.journey-delivery').getByText('No notifications are being sent', { exact: true })).toBeVisible();
  await expect(page.getByRole('checkbox', { name: /SAFETY|downed power|generator indoors/ })).toHaveCount(0);
});

test('B2 null risk keeps valid restoration, general preparation and independent declared support', async ({ page }) => {
  await page.unroute('**/api/**'); await useApi(page, missingRiskApi);
  await start(page);
  expect(latest(page).result.risk.band).toBeNull();
  expect(latest(page).result.risk.score).toBeNull();
  expect(latest(page).result.risk.predictive_confidence).toBe('LOW');
  expect(latest(page).result.risk.missing_inputs).toContain('verified_historical_circuit_context');
  await expect(page.getByTestId('risk-band')).toContainText(/unavailable/i);
  await expect(page.getByRole('button', { name: 'What does HIGH mean?', exact: true })).toHaveCount(0);
  await nav(page, 'Prepare & alerts');
  await expect(page.getByTestId('alert-eligibility')).toContainText(/more information|undetermined/i);
  await expect(page.getByTestId('preparation-actions')).toContainText('Charge phones');
  await page.getByRole('checkbox', { name: 'Powered medical equipment / medical need', exact: true }).check();
  await expect(page.locator('.declared-guidance li')).toHaveCount(1);
  expect(latest(page).customer_journey.alerts.eligible).toBe(true);
  await nav(page, 'Overview'); await explore(page); await access(page, 'Blocked', 'unavailable');
  expect(latest(page).result.risk.band).toBeNull();
  expect(latest(page).result.restoration.display_hours).toBeNull();
  await nav(page, 'Prepare & alerts');
  await expect(page.locator('.declared-guidance li')).toHaveCount(1);
  await expect(page.getByText(/Never run a generator indoors/)).toBeVisible();
  await expect(page.getByTestId('preparation-actions')).not.toContainText('longer end of the range');
  await page.getByRole('button', { name: /None \/ clear declarations/ }).click();
  await expect(page.locator('.declared-guidance li')).toHaveCount(0);
  expect(latest(page).customer_journey.alerts.eligible).toBeNull();
  await expect(page.locator('.error-panel')).toHaveCount(0);
});

test('planning compares live policy responses, separates crews/people and preserves the customer scope', async ({ page }) => {
  await start(page); const panel = await grid(page);
  await expect(panel.getByTestId('policy-tradeoff')).toContainText('23');
  await expect(panel.getByTestId('policy-tradeoff')).toContainText('1.728');
  await expect(panel.getByTestId('decision-recommendation')).toContainText('Critical-context fuse');
  await panel.getByRole('radio', { name: /^Customer-impact focused/ }).check();
  await expect(panel.getByTestId('decision-recommendation')).toContainText('Historical fuse');
  await expect(panel.getByTestId('selected-dependency')).toContainText('Historical');
  await panel.getByRole('radio', { name: /^Critical-service aware/ }).check();
  await expect(panel.getByTestId('decision-recommendation')).toContainText('Critical-context fuse');
  await panel.locator('.decision-select').filter({ hasText: 'Historical fuse replay' }).click();
  await panel.getByRole('combobox', { name: /^Available crews/ }).selectOption('2');
  await expect(panel.getByTestId('decision-recommendation')).toContainText('3.25–13.5');
  await expect(panel.getByTestId('selected-dependency')).toContainText('Historical');
  await expect(panel.locator('.decision-lane')).toHaveCount(2);
  await expect(panel.locator('.decision-milestones')).toContainText('24');
  await panel.getByRole('combobox', { name: /^People per crew/ }).selectOption('2');
  await expect(panel.getByTestId('decision-recommendation')).toContainText('6.5–13.5');
  await nav(page, 'Overview'); await result(page, '2.5–12');
  await grid(page);
  await expect(panel.getByRole('combobox', { name: /^Available crews/ })).toHaveValue('2');
  await expect(panel.getByRole('combobox', { name: /^People per crew/ })).toHaveValue('2');
});

test('candidate selection synchronizes only supported map, dependency and facility evidence', async ({ page }) => {
  await start(page); const panel = await grid(page);
  await panel.locator('.decision-select').filter({ hasText: 'Historical fuse replay' }).click();
  await expect(panel.getByTestId('selected-dependency')).toContainText(/spatial|Spatial/);
  await expect(panel.getByTestId('selected-dependency')).toContainText('23');
  await expect(panel.getByTestId('decision-map')).toHaveAttribute('aria-label', /Historical fuse/);
  await visibleVectorGeometry(panel.getByTestId('decision-map'));
  await expect(panel.getByText(/not outage boundaries/).first()).toBeVisible();
  await panel.locator('.decision-select').filter({ hasText: 'Critical-context fuse' }).click();
  await expect(panel.getByTestId('selected-dependency')).toContainText(/unverified|not verified/);
  await expect(panel.getByTestId('decision-map')).toHaveAttribute('aria-label', /Critical-context fuse/);
  await expect(panel.getByRole('button', { name: /pole replacement|integrate pole/i })).toHaveCount(0);
});

test('blocked upstream work defers descendants, preserves independent release and all-blocked withholds time', async ({ page }) => {
  await start(page); const panel = await grid(page);
  await panel.getByText('Access at each repair candidate', { exact: true }).first().click();
  await panel.getByRole('combobox', { name: /^Golden upstream fuse/ }).selectOption('blocked');
  await expect(panel.getByTestId('deferred-work')).toContainText('Golden transformer');
  await expect(panel.getByTestId('deferred-work')).toContainText('24');
  await expect(panel.getByTestId('decision-recommendation')).toContainText(/Unavailable|unavailable/);
  for (const label of ['Historical fuse replay', 'Critical-context fuse', 'Golden transformer']) {
    await panel.getByRole('combobox', { name: new RegExp(`^${label}`) }).selectOption('blocked');
    await expect(panel.getByTestId('decision-recommendation')).toBeVisible();
  }
  await expect(panel.getByTestId('decision-recommendation')).toContainText(/No executable|No repair can/);
  await expect(panel.locator('.decision-task-select')).toHaveCount(0);
  await nav(page, 'Overview'); await result(page, '2.5–12');
});

test('Standard explanation uses bound results and never sends declared needs', async ({ page }) => {
  await start(page); await nav(page, 'Prepare & alerts');
  await page.getByRole('checkbox', { name: 'Powered medical equipment / medical need', exact: true }).check();
  await expect(page.locator('.declared-guidance li')).toHaveCount(1);
  await nav(page, 'Overview'); await explore(page);
  const request = page.waitForRequest(r => new URL(r.url()).pathname === '/api/explain');
  await page.getByRole('button', { name: 'Why is restoration 2.5–12 hours?', exact: true }).click();
  expect((await request).postDataJSON().declared_needs.selections).toEqual([]);
  await expect(page.getByTestId('ai-explanation').filter({ hasText: 'Standard explanation' })).toBeVisible();
  await expect(page.getByTestId('ai-explanation').filter({ hasText: 'Standard explanation' })).toContainText('2.5–12');
  const panel = await grid(page);
  await panel.getByRole('button', { name: 'Why this action first?', exact: true }).click();
  await expect(panel.getByTestId('decision-explanation')).toContainText('Standard explanation');
});

test('rapid inputs and delayed old responses never replace the latest combined customer selection', async ({ page }) => {
  await start(page); await explore(page);
  await page.route('**/api/evaluate', async route => {
    const response = await route.fetch({ url: `${normalApi}/api/evaluate` });
    const body = route.request().postDataJSON();
    if (body.crew_size === 2 && body.access === 'clear') await new Promise(resolve => setTimeout(resolve, 500));
    try { await route.fulfill({ response }); } catch { /* The browser cancelled the old request. */ }
  });
  await page.getByRole('radio', { name: /^2 people/ }).check();
  await page.getByRole('radio', { name: /^Restricted/ }).check();
  await result(page, '8–16.5');
  await page.waitForTimeout(650);
  await result(page, '8–16.5');
  await expect(page.getByRole('radio', { name: /^2 people/ })).toBeChecked();
  await expect(page.getByRole('radio', { name: /^Restricted/ })).toBeChecked();
});

test('customer transport failure hides stale claims and retry recovers', async ({ page }) => {
  await start(page); await explore(page);
  await page.route('**/api/evaluate', route => route.fulfill({ status: 503, json: {} }));
  await page.getByRole('radio', { name: /^2 people/ }).check();
  await expect(page.getByRole('button', { name: 'Try again', exact: true })).toBeVisible();
  await expect(page.getByTestId('restoration-result').first()).not.toContainText('2.5–12');
  await page.unroute('**/api/evaluate');
  await page.getByRole('button', { name: 'Try again', exact: true }).click();
  await result(page, '5.5–12');
});

test('alternative-policy failure preserves the current plan and can retry', async ({ page }) => {
  await start(page);
  await page.route('**/api/restoration-plan', async route => {
    if (route.request().postDataJSON().use_critical_proxy === false) return route.fulfill({ status: 503, json: {} });
    await route.fallback();
  });
  const panel = await grid(page);
  await expect(panel.getByTestId('decision-recommendation')).toContainText('Critical-context fuse');
  await expect(panel.getByRole('button', { name: 'Retry policy comparison', exact: true })).toBeVisible();
  await page.unroute('**/api/restoration-plan');
  await panel.getByRole('button', { name: 'Retry policy comparison', exact: true }).click();
  await expect(panel.getByTestId('policy-tradeoff')).toContainText('23');
});

for (const width of [1440, 1280, 1024, 768, 390, 320]) {
  test(`responsive customer and grid task flows at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: width < 768 ? 844 : 1000 });
    await start(page);
    const checkOverflow = async () => expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    await checkOverflow();
    await page.screenshot({ path: `test-results/overview-${width}.png`, fullPage: true });
    await nav(page, 'Prepare & alerts'); await checkOverflow();
    await stage(page, 'Outage confirmed'); await expect(page.getByTestId('message-preview')).toContainText('If an outage is confirmed');
    await page.screenshot({ path: `test-results/preparation-${width}.png`, fullPage: true });
    const panel = await grid(page); await checkOverflow();
    await visibleVectorGeometry(panel.getByTestId('decision-map'));
    await panel.getByRole('combobox', { name: /^Available crews/ }).selectOption('2');
    await expect(panel.getByTestId('decision-recommendation')).toContainText('3.25–13.5');
    await checkOverflow();
    await page.screenshot({ path: `test-results/grid-${width}.png`, fullPage: true });
    if (width < 768) {
      for (const name of ['Evidence', 'Crew plan']) {
        await panel.getByRole('tab', { name, exact: true }).click();
        await expect(panel.getByRole('tabpanel', { name, exact: true })).toBeVisible();
        await checkOverflow();
        await page.screenshot({ path: `test-results/grid-${name === 'Evidence' ? 'evidence' : 'crew'}-${width}.png`, fullPage: true });
        if (name === 'Evidence') {
          await panel.getByRole('tab', { name, exact: true }).focus();
          await page.keyboard.press('ArrowRight');
          await expect(panel.getByRole('tab', { name: 'Crew plan', exact: true })).toBeFocused();
          await expect(panel.getByRole('tab', { name: 'Crew plan', exact: true })).toHaveAttribute('aria-selected', 'true');
        }
      }
    }
  });
}

test('keyboard, reduced motion and text reflow preserve navigation and form tasks', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await start(page);
  const preparation = page.getByRole('navigation', { name: 'Main navigation' }).getByRole('link', { name: 'Prepare & alerts', exact: true });
  await preparation.focus(); await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/#prepare$/);
  await expect(page.getByRole('heading', { level: 1 })).toBeFocused();
  const checkbox = page.getByRole('checkbox', { name: 'Charge phones and power banks.', exact: true });
  await checkbox.focus(); await page.keyboard.press('Space'); await expect(checkbox).toBeChecked();
  expect(await checkbox.evaluate(element => getComputedStyle(element).outlineStyle)).not.toBe('none');
  expect(await checkbox.evaluate(element => getComputedStyle(element).transitionDuration)).toMatch(/^0s(?:, 0s)*$/);
  await page.addStyleTag({ content: 'body { zoom: 2; }' });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  await expect(page.getByTestId('alert-eligibility')).toBeVisible();
});

test('explanation HTTP failure and retry stay local while stale answers are cancelled', async ({ page }) => {
  await start(page); await explore(page);
  const explanation = page.locator('[data-explanation-context="restoration"]');
  await page.route('**/api/explain', route => route.fulfill({ status: 503, json: {} }));
  await explanation.getByRole('button', { name: 'Why is restoration 2.5–12 hours?', exact: true }).click();
  await expect(explanation.getByText('Explanation service unavailable', { exact: true })).toBeVisible();
  await result(page, '2.5–12');
  await page.unroute('**/api/explain');
  await explanation.getByRole('button', { name: 'Retry explanation', exact: true }).click();
  await expect(explanation.getByTestId('ai-explanation')).toContainText('Standard explanation');
  await page.route('**/api/explain', async route => {
    const response = await route.fetch({ url: `${normalApi}/api/explain` });
    await new Promise(resolve => setTimeout(resolve, 650));
    try { await route.fulfill({ response }); } catch { /* The changed scenario cancels the request. */ }
  });
  await explanation.getByRole('button', { name: 'Why is restoration 2.5–12 hours?', exact: true }).click();
  await crew(page, 2, '5.5–12');
  await page.waitForTimeout(800);
  await expect(explanation.getByTestId('ai-explanation')).toBeEmpty();
  await expect(explanation.getByRole('button', { name: 'Why is restoration 5.5–12 hours?', exact: true })).toBeVisible();
});

test('map transport and optional tile failure preserve numerical results and source context', async ({ page }) => {
  await start(page);
  await page.route('**/api/map**', route => route.fulfill({ status: 503, json: {} }));
  await page.getByText('See your grid context', { exact: true }).click();
  await expect(page.getByRole('button', { name: 'Retry map', exact: true })).toBeVisible();
  await result(page, '2.5–12');
  await expect(page.getByRole('list', { name: 'Upstream dependency path' })).toBeVisible();
  await page.unroute('**/api/map**');
  await page.getByRole('button', { name: 'Retry map', exact: true }).click();
  await expect(page.getByTestId('geographic-map')).toBeVisible();
  await visibleVectorGeometry(page.getByTestId('geographic-map'));
  const streets = page.getByRole('checkbox', { name: 'Street map', exact: true });
  if (!await streets.isChecked()) await streets.check();
  await expect(page.getByText(/Street basemap unavailable/)).toBeVisible();
  await expect(page.getByTestId('geographic-map').locator('.leaflet-marker-icon')).not.toHaveCount(0);
  await page.getByRole('button', { name: 'Retry basemap', exact: true }).click();
  await expect(page.getByText(/Street basemap unavailable/)).toBeVisible();
  await streets.uncheck();
  await expect(page.getByText(/Offline view: verified GIS/)).toBeVisible();
  await result(page, '2.5–12');
});

test('current planning failure and retry preserve customer analysis and latest crew inputs', async ({ page }) => {
  await start(page); const panel = await grid(page);
  await page.route('**/api/restoration-plan', route => route.fulfill({ status: 503, json: {} }));
  await panel.getByRole('combobox', { name: /^Available crews/ }).selectOption('2');
  await expect(panel.getByRole('button', { name: 'Retry plan', exact: true })).toBeVisible();
  await expect(panel.getByTestId('decision-recommendation')).toHaveCount(0);
  await nav(page, 'Overview'); await result(page, '2.5–12');
  await nav(page, 'Grid insights');
  await page.unroute('**/api/restoration-plan');
  await panel.getByRole('button', { name: 'Retry plan', exact: true }).click();
  await expect(panel.getByTestId('decision-recommendation')).toContainText('3.25–13.5');
  await expect(panel.getByRole('combobox', { name: /^Available crews/ })).toHaveValue('2');
});

test('delayed planning response and plan explanation cannot overwrite the latest scope', async ({ page }) => {
  await start(page); const panel = await grid(page);
  await page.route('**/api/restoration-plan/explain', async route => {
    const response = await route.fetch({ url: `${normalApi}/api/restoration-plan/explain` });
    await new Promise(resolve => setTimeout(resolve, 650));
    try { await route.fulfill({ response }); } catch { /* Cancellation is expected. */ }
  });
  await panel.getByRole('button', { name: 'Why this action first?', exact: true }).click();
  await page.route('**/api/restoration-plan', async route => {
    const response = await route.fetch({ url: `${normalApi}/api/restoration-plan` });
    const body = route.request().postDataJSON();
    if (body.crew_count === 2 && body.crew_size === 4) await new Promise(resolve => setTimeout(resolve, 500));
    try { await route.fulfill({ response }); } catch { /* Cancellation is expected. */ }
  });
  await panel.getByRole('combobox', { name: /^Available crews/ }).selectOption('2');
  await panel.getByRole('combobox', { name: /^People per crew/ }).selectOption('2');
  await expect(panel.getByTestId('decision-recommendation')).toContainText('6.5–13.5');
  await page.waitForTimeout(800);
  await expect(panel.getByTestId('decision-recommendation')).toContainText('6.5–13.5');
  await expect(panel.getByTestId('decision-explanation')).toHaveCount(0);
  await nav(page, 'Overview'); await result(page, '2.5–12');
});

for (const [width, height] of [[1440, 900], [1280, 800]]) {
  test(`desktop first view answers the customer before any disclosure at ${width}x${height}`, async ({ page }) => {
    await page.setViewportSize({ width, height });
    await start(page);
    for (const item of [
      page.locator('.location-identity').getByText('Demo location A', { exact: true }),
      page.getByTestId('risk-band'),
      page.locator('.confidence'),
      page.locator('.live-status'),
      page.getByTestId('restoration-result'),
      page.locator('.next-action h2'),
      page.getByRole('button', { name: 'Prepare now', exact: true }),
      page.locator('.next-alert h2'),
      page.locator('.next-alert').getByText('No notifications are being sent.', { exact: true }),
    ]) {
      await expect(item).toBeVisible();
      const box = await item.boundingBox();
      expect(box!.y).toBeGreaterThanOrEqual(0);
      expect(box!.y + box!.height).toBeLessThanOrEqual(height);
    }
  });
}

for (const width of [1440, 1280, 1024, 768, 390, 320]) {
  test(`partial, blocked, loading and recoverable error remain usable at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: width < 768 ? 844 : 1000 });
    const checkOverflow = async () => expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    await start(page); await explore(page);
    let release: (() => void) | undefined;
    await page.route('**/api/evaluate', async route => {
      await new Promise<void>(resolve => { release = resolve; });
      await route.fallback();
    });
    await page.getByRole('radio', { name: /^2 people/ }).check();
    await expect.poll(() => Boolean(release)).toBe(true);
    await expect(page.getByTestId('restoration-result')).toContainText('Updating');
    await checkOverflow();
    await page.screenshot({ path: `test-results/loading-${width}.png`, fullPage: true });
    release!();
    await result(page, '5.5–12');
    await page.unroute('**/api/evaluate');
    await access(page, 'Blocked', 'unavailable');
    await checkOverflow();
    await page.screenshot({ path: `test-results/blocked-${width}.png`, fullPage: true });
    await page.route('**/api/evaluate', route => route.fulfill({ status: 503, json: {} }));
    await page.getByRole('radio', { name: /^Clear/ }).check();
    await expect(page.getByRole('button', { name: 'Try again', exact: true })).toBeVisible();
    await checkOverflow();
    await page.screenshot({ path: `test-results/error-${width}.png`, fullPage: true });
    await page.unroute('**/api/evaluate');
    await page.getByRole('button', { name: 'Try again', exact: true }).click();
    await result(page, '5.5–12');
    await page.unroute('**/api/**'); await useApi(page, missingRiskApi);
    await page.reload();
    await result(page, '2.5–12');
    await expect(page.getByTestId('risk-band')).toContainText('Unavailable');
    await checkOverflow();
    await page.screenshot({ path: `test-results/partial-${width}.png`, fullPage: true });
    await nav(page, 'Prepare & alerts');
    await expect(page.getByTestId('preparation-actions')).toContainText('Charge phones');
    await expect(page.getByTestId('alert-eligibility')).toContainText('more information');
    await checkOverflow();
  });
}

test('mobile overview keeps the first preparation action within the initial viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await start(page);
  await page.evaluate(() => scrollTo(0, 0));
  const box = await page.getByRole('button', { name: 'Prepare now', exact: true }).boundingBox();
  expect(box!.y + box!.height).toBeLessThanOrEqual(844);
});

test('Back to the original empty hash restores Overview and Forward retains session preparation', async ({ page }) => {
  await page.goto('/');
  await result(page, '2.5–12');
  await nav(page, 'Prepare & alerts');
  const action = page.getByRole('checkbox', { name: 'Charge phones and power banks.', exact: true });
  await action.check();
  await page.goBack();
  await expect(page).toHaveURL('http://127.0.0.1:15173/');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Your storm outlook');
  await result(page, '2.5–12');
  await page.goForward();
  await expect(page).toHaveURL(/#prepare$/);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Prepare & stay informed');
  await expect(action).toBeChecked();
});

test('evidence disclosures have unique anchors and communication CTA focuses its destination', async ({ page }) => {
  await start(page);
  await page.getByText('What informs this outlook?', { exact: true }).click();
  await explore(page);
  await page.getByText('See your grid context', { exact: true }).click();
  await expect(page.getByTestId('geographic-map')).toBeVisible();
  expect(await page.evaluate(() => {
    const ids = Array.from(document.querySelectorAll('[id]')).map(element => element.id);
    return ids.filter((id, index) => ids.indexOf(id) !== index);
  })).toEqual([]);
  await page.getByRole('button', { name: 'Preview communications', exact: true }).click();
  await expect(page).toHaveURL(/#prepare$/);
  await expect(page.locator('#communications')).toBeFocused();
  await expect(page.getByTestId('message-preview')).toBeVisible();
});

test('keyboard declaration updates retain focus without stealing focus after navigation', async ({ page }) => {
  await start(page); await nav(page, 'Prepare & alerts');
  const need = page.getByRole('checkbox', { name: 'Accessibility assistance', exact: true });
  await need.focus(); await page.keyboard.press('Space');
  await expect(page.locator('.declared-guidance li')).toHaveCount(1);
  await expect(need).toBeFocused();
  const clear = page.getByRole('button', { name: 'None / clear declarations', exact: true });
  await clear.focus(); await page.keyboard.press('Enter');
  await expect(page.locator('.declared-guidance li')).toHaveCount(0);
  await expect(clear).toBeFocused();
  await page.route('**/api/evaluate', async route => {
    const response = await route.fetch({ url: `${normalApi}/api/evaluate` });
    await new Promise(resolve => setTimeout(resolve, 400));
    try { await route.fulfill({ response }); } catch { /* Cancellation is allowed. */ }
  });
  await need.focus(); await page.keyboard.press('Space');
  const overview = page.getByRole('navigation', { name: 'Main navigation' }).getByRole('link', { name: 'Overview', exact: true });
  await overview.focus(); await page.keyboard.press('Enter');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Your storm outlook');
  await result(page, '2.5–12');
  await page.waitForTimeout(500);
  await expect(page.getByRole('heading', { level: 1 })).toBeFocused();
});
