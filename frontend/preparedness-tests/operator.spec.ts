import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { readFile } from 'node:fs/promises';
async function start(page:Page){await page.goto('/operator/');await expect(page.getByRole('heading',{name:'2. Compare identical assumptions'})).toBeVisible();}
async function acknowledge(page:Page){for(const checkbox of await page.getByRole('group',{name:'Explicit human acknowledgements'}).getByRole('checkbox').all())await checkbox.check();}
async function review(page:Page){await acknowledge(page);await page.getByRole('button',{name:'Mark reviewed in demo and prepare export'}).click();await expect(page.getByRole('heading',{name:'Reviewed in demo',exact:true})).toBeVisible();}

test('comparison and critical tradeoffs, structured alternative, real download and no persistence',async({page})=>{
 const posts:string[]=[];page.on('request',r=>{if(r.method()==='POST')posts.push(new URL(r.url()).pathname);});
 await start(page);await expect(page.getByRole('row')).toHaveCount(5);
 await expect(page.getByRole('combobox',{name:'Selected policy'})).toHaveValue('legacy-release-per-person-hour-adapter-v1');
 await expect(page.getByRole('button',{name:'Mark reviewed in demo and prepare export'})).toBeDisabled();
 await page.getByRole('combobox',{name:'Fictional scenario',exact:true}).selectOption('syn-micro-critical');
 await page.getByRole('combobox',{name:'Selected policy'}).selectOption('legacy-critical-proxy-first-adapter-v1');
 await expect(page.getByLabel('Selected policy tradeoffs')).toContainText('Completed customer-hours: regression');
 await expect(page.getByLabel('Selected policy tradeoffs')).toContainText('Critical syn-group-0: improvement');
 await page.getByRole('combobox',{name:'Structured reason'}).selectOption('critical-service-tradeoff');
 await review(page);const pending=page.waitForEvent('download');await page.getByRole('button',{name:'Download review JSON'}).click();
 const artifact=JSON.parse(await readFile((await (await pending).path())!,'utf8'));
 expect(artifact.review.reason).toBe('critical-service-tradeoff');
 expect(Object.keys(artifact).sort()).toEqual(['checksum','comparison','review','version']);
 expect(JSON.stringify(artifact)).not.toMatch(/road_name|latitude|longitude|medical|email|phone|credential/);
 expect(await page.evaluate(()=>({local:localStorage.length,session:sessionStorage.length}))).toEqual({local:0,session:0});
 expect(posts.every(p=>['/api/v2/operator/compare','/api/v2/operator/review-export'].includes(p))).toBe(true);
 await page.reload();await expect(page.getByRole('heading',{name:'Reviewed in demo',exact:true})).toHaveCount(0);
});

test('precedence recomputes; cyclic override clears result; review invalidates on edits',async({page})=>{
 await start(page);await review(page);
 await page.getByRole('combobox',{name:'Repair first'}).selectOption('syn-task-1');
 await expect(page.getByRole('heading',{name:'Reviewed in demo',exact:true})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Mark reviewed in demo and prepare export'})).toBeDisabled();
 await page.getByRole('combobox',{name:'Repair first'}).selectOption('syn-task-0');
 await page.getByRole('button',{name:'Add precedence and recompute'}).click();
 await expect(page.locator('.selected-plan')).toContainText('18000');await review(page);
 await page.getByRole('combobox',{name:'Repair first'}).selectOption('syn-task-1');
 await page.getByRole('combobox',{name:'Then repair'}).selectOption('syn-task-0');
 await page.getByRole('button',{name:'Add precedence and recompute'}).click();
 await expect(page.getByRole('status')).toContainText('Validation failed');
 await expect(page.getByRole('heading',{name:'2. Compare identical assumptions'})).toHaveCount(0);
 await page.getByRole('button',{name:'Reset constraints and recompute'}).click();
 await expect(page.getByRole('heading',{name:'2. Compare identical assumptions'})).toBeVisible();
});

test('optional frozen optimizer and unsupported overrides never replace fixed default',async({page})=>{
 await start(page);await page.getByRole('checkbox',{name:'Include optional frozen CP-SAT comparison'}).check();
 await expect(page.getByRole('row')).toHaveCount(6);
 await expect(page.getByRole('combobox',{name:'Selected policy'})).toHaveValue('legacy-release-per-person-hour-adapter-v1');
 await page.getByRole('combobox',{name:'Selected policy'}).selectOption('restoration-cpsat-v1');
 await expect(page.locator('.selected-plan')).toContainText('historical G3 wrapper');
 await page.getByRole('combobox',{name:'Selected policy'}).selectOption('fifo-v1');
 await page.getByRole('button',{name:'Add precedence and recompute'}).click();
 await expect(page.getByText('CP-SAT unavailable for changed precedence:',{exact:false})).toBeVisible();
 await expect(page.getByRole('row')).toHaveCount(5);
});

test('null completion and known-later censoring remain distinct',async({page})=>{
 await start(page);await page.getByRole('combobox',{name:'Fictional scenario',exact:true}).selectOption('syn-micro-blocked');
 await expect(page.locator('.selected-plan')).toContainText('Unavailable');
 await expect(page.locator('.selected-plan')).toContainText('Unscheduled tasks: syn-task-0, syn-task-1');
 await page.getByRole('combobox',{name:'Fictional scenario',exact:true}).selectOption('syn-micro-censored');
 const row=page.getByRole('row').filter({hasText:'Fixed release/person-hour baseline'});
 await expect(row).toContainText('202');await expect(row).toContainText('169');await expect(row).toContainText('0 / 1');
});

test('wrong-scenario response rejected and stale export cannot restore review',async({page})=>{
 await start(page);
 await page.route('**/api/v2/operator/compare',async route=>{const response=await route.fetch();const value=await response.json();value.request.scenario_id='syn-forged';await route.fulfill({json:value});});
 await page.getByRole('combobox',{name:'Fictional scenario',exact:true}).selectOption('syn-micro-critical');
 await expect(page.getByRole('status')).toContainText('Mismatched scenario response rejected');
 await expect(page.getByRole('heading',{name:'2. Compare identical assumptions'})).toHaveCount(0);
 await page.unroute('**/api/v2/operator/compare');await start(page);await acknowledge(page);
 let unblock!:()=>void;const gate=new Promise<void>(r=>unblock=r);let entered!:()=>void;const ready=new Promise<void>(r=>entered=r);
 await page.route('**/api/v2/operator/review-export',async route=>{entered();await gate;await route.continue().catch(()=>{});});
 await page.getByRole('button',{name:'Mark reviewed in demo and prepare export'}).click();await ready;
 await page.getByRole('combobox',{name:'Fictional scenario',exact:true}).selectOption('syn-micro-unknown');unblock();
 await expect(page.getByRole('heading',{name:'2. Compare identical assumptions'})).toBeVisible();
 await expect(page.getByRole('heading',{name:'Reviewed in demo',exact:true})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Mark reviewed in demo and prepare export'})).toBeDisabled();
});

test('late comparison and changed review rationale cannot restore acknowledgements',async({page})=>{
 await start(page);await review(page);
 await page.getByRole('combobox',{name:'Structured reason'}).selectOption('fairness-consideration');
 await expect(page.getByRole('heading',{name:'Reviewed in demo',exact:true})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Mark reviewed in demo and prepare export'})).toBeDisabled();
 let unblock!:()=>void;const gate=new Promise<void>(r=>unblock=r);let entered!:()=>void;const ready=new Promise<void>(r=>entered=r);
 await page.route('**/api/v2/operator/compare',async route=>{
  if(route.request().postDataJSON().scenario_id==='syn-micro-critical'){
   const response=await route.fetch();entered();await gate;await route.fulfill({response}).catch(()=>{});
  }else await route.continue();
 });
 await page.getByRole('combobox',{name:'Fictional scenario',exact:true}).selectOption('syn-micro-critical');await ready;
 const current=page.waitForResponse(r=>r.url().endsWith('/operator/compare')&&r.request().postDataJSON().scenario_id==='syn-micro-unknown');
 await page.getByRole('combobox',{name:'Fictional scenario',exact:true}).selectOption('syn-micro-unknown');await current;unblock();
 await expect(page.getByRole('heading',{name:'2. Compare identical assumptions'})).toBeVisible();
 await expect(page.getByRole('combobox',{name:'Fictional scenario',exact:true})).toHaveValue('syn-micro-unknown');
 await expect(page.locator('.selected-plan')).toContainText('Unscheduled tasks: syn-task-0');
 await expect(page.getByRole('heading',{name:'Reviewed in demo',exact:true})).toHaveCount(0);
});

test('accessible desktop/mobile reviewed states with authentic screenshots',async({page},info)=>{
 await start(page);await page.getByRole('combobox',{name:'Fictional scenario',exact:true}).selectOption('syn-micro-critical');
 const audit=async()=>expect((await new AxeBuilder({page}).analyze()).violations.filter(v=>['serious','critical'].includes(v.impact??''))).toEqual([]);
 for(const scenario of ['weighted','overlap','chain-eight','two-crews','blocked','unknown','censored','critical']){
  await page.getByRole('combobox',{name:'Fictional scenario',exact:true}).selectOption('syn-micro-'+scenario);
  await expect(page.getByRole('heading',{name:'2. Compare identical assumptions'})).toBeVisible();await audit();
 }
 await audit();await page.screenshot({path:info.outputPath('operator-desktop.png'),fullPage:true});
 await page.setViewportSize({width:390,height:844});await page.emulateMedia({reducedMotion:'reduce'});
 const button=page.getByRole('button',{name:'Reset constraints and recompute'});await button.focus();await page.keyboard.press('Enter');
 await expect(page.getByRole('heading',{name:'2. Compare identical assumptions'})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await review(page);await audit();await page.screenshot({path:info.outputPath('operator-mobile-review.png'),fullPage:true});
});
