import { test, expect, chromium } from '@playwright/test';
import { spawn, execFileSync, type ChildProcess } from 'node:child_process';
import { mkdtemp, readFile, writeFile, rm } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';

const origin='http://127.0.0.1:18188';
const root=process.env.GRIDGUIDE_PACKAGE;
const python=process.env.GRIDGUIDE_PUBLIC_PYTHON;
const container=process.env.GRIDGUIDE_CONTAINER;
if(!root || !python)throw new Error('Explicit clean package and locked public Python required');
let server:ChildProcess;
let logs='';
const coldStarts:number[]=[];
async function boot(){
 const started=performance.now();
 server=container
  ? spawn('docker',['run','--rm','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--tmpfs','/tmp:rw,noexec,nosuid,size=16m','-p','127.0.0.1:18188:8000',container],{stdio:['ignore','pipe','pipe']})
  : spawn(python!,[join(root!,'deploy/serve.py')],{cwd:root!,env:{PATH:process.env.PATH,PORT:'18188',PYTHONDONTWRITEBYTECODE:'1'},stdio:['ignore','pipe','pipe']});
 server.stdout!.on('data',d=>logs+=String(d));server.stderr!.on('data',d=>logs+=String(d));
 await expect.poll(async()=>{
  if(server.exitCode!==null)throw new Error('Production server exited: '+logs);
  try{return (await fetch(origin+'/ready')).status;}catch{return 0;}
 },{timeout:20000}).toBe(200);
 coldStarts.push(performance.now()-started);
}
async function stop(){
 if(server && server.exitCode===null){
  const done=new Promise<void>(r=>server.once('exit',()=>r()));server.kill('SIGTERM');
  await Promise.race([done,new Promise<never>((_,reject)=>setTimeout(()=>reject(new Error('Shutdown exceeded 10s')),10000).unref())]);
 }
}
test.beforeAll(boot);
test.afterAll(async()=>{await stop();});

test('clean production customer journey, fixed default and independent exported replay',async({page},info)=>{
 const external:string[]=[];
 page.on('request',r=>{if(new URL(r.url()).origin!==origin)external.push(r.url());});
 const csp:string[]=[];page.on('console',m=>{if(m.text().includes('Content Security Policy'))csp.push(m.text());});
 await page.goto('/');await expect(page).toHaveURL(origin+'/');
 await expect(page.getByRole('heading',{name:'Your storm outlook',exact:true})).toBeVisible();
 await page.getByRole('link',{name:'Prepare now',exact:true}).click();
 await expect(page.getByRole('button',{name:'Save this demo snapshot'})).toBeEnabled();
 const path=page.getByRole('list',{name:'Fictional customer 1 ordered upstream dependencies'});
 await path.getByRole('button',{name:/Transformer/}).click();
 await expect(page.locator('#path-inspection')).toContainText('Repair prerequisites');
 await page.screenshot({path:info.outputPath('public-customer.png'),fullPage:true});
 await page.getByRole('navigation',{name:'Main navigation'}).getByRole('link',{name:'Grid insights',exact:true}).click();
 await expect(page.getByRole('heading',{name:'2. Compare identical assumptions'})).toBeVisible();
 await expect(page.getByRole('combobox',{name:'Selected policy'})).toHaveValue('legacy-release-per-person-hour-adapter-v1');
 await page.getByRole('combobox',{name:'Fictional scenario',exact:true}).selectOption('syn-micro-critical');
 await expect(page.getByRole('heading',{name:'2. Compare identical assumptions'})).toBeVisible();
 for(const checkbox of await page.getByRole('group',{name:'Explicit human acknowledgements'}).getByRole('checkbox').all())await checkbox.check();
 await page.getByRole('button',{name:'Mark reviewed in demo and prepare export'}).click();
 await expect(page.getByRole('heading',{name:'Reviewed in demo',exact:true})).toBeVisible();
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'Download review JSON'}).click();
 const output=info.outputPath('actual-browser-review.json');await (await download).saveAs(output);
 const replay=execFileSync(python!,[join(root!,'scripts/replay_review.py'),resolve(output)],
  {cwd:root!,env:{PATH:process.env.PATH,PYTHONDONTWRITEBYTECODE:'1'},encoding:'utf8'});
 expect(replay).toContain('verified');await writeFile(info.outputPath('replay.log'),replay);
 const summaryDownload=page.waitForEvent('download');
 await page.getByRole('button',{name:'Download readable summary'}).click();
 const summaryPath=info.outputPath('actual-browser-summary.txt');await(await summaryDownload).saveAs(summaryPath);
 const summary=await readFile(summaryPath,'utf8');expect(summary.length).toBeGreaterThan(100);
 expect(replay).toContain(summary);
 await page.screenshot({path:info.outputPath('public-operator.png'),fullPage:true});
 expect(external).toEqual([]);expect(csp).toEqual([]);
});

test('browser restart with network disabled, real service outage and cold restart',async({},info)=>{
 const profile=await mkdtemp(join(tmpdir(),'gridguide-g8-browser-'));
 const launch=()=>chromium.launchPersistentContext(profile,{channel:process.env.CI?undefined:'chrome',headless:true});
 let context=await launch();
 try{
  let page=await context.newPage();await page.goto(origin+'/preparedness/');
  await page.getByRole('button',{name:'Enable or check offline kit'}).click();
  await expect(page.getByText('Offline kit ready on this device',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Save this demo snapshot'}).click();
  await expect(page.getByText('Fictional snapshot saved explicitly',{exact:false})).toBeVisible();
  const saved=await page.evaluate(()=>localStorage.getItem('gridguide.preparedness.snapshot.v1'));
  await context.close();await stop();
  await expect(fetch(origin+'/ready')).rejects.toThrow();
  context=await launch();await context.setOffline(true);page=await context.newPage();
  await page.goto(origin+'/preparedness/');
  await expect(page.getByRole('heading',{name:'Your generic preparedness kit'})).toBeVisible();
  await page.getByRole('button',{name:'Open saved snapshot'}).click();
  await expect(page.getByText('Historical fictional snapshot',{exact:true})).toBeVisible();
  await expect(page.getByLabel('Prepared milestone')).toBeDisabled();
  expect(await page.evaluate(()=>localStorage.getItem('gridguide.preparedness.snapshot.v1'))).toBe(saved);
  await page.screenshot({path:info.outputPath('public-offline-outage.png'),fullPage:true});
  await boot();await context.setOffline(false);
  await page.getByRole('button',{name:'Reconnect and refresh'}).click();
  await expect(page.getByRole('button',{name:'Save this demo snapshot'})).toBeEnabled();
  await page.getByRole('button',{name:'Delete saved snapshot'}).click();
  await expect(page.getByRole('button',{name:'Open saved snapshot'})).toBeDisabled();
  expect(await page.evaluate(()=>localStorage.getItem('gridguide.preparedness.snapshot.v1'))).toBeNull();
  await writeFile(info.outputPath('cold-start.json'),JSON.stringify({milliseconds:coldStarts,host:process.platform,scope:container?'fresh Docker containers; local image; no image pull':'fresh Python processes; local package; no image pull'},null,2));
 }finally{await context.close();await rm(profile,{recursive:true,force:true});}
});

test('bounded actual HTTP comparison latency and unavailable route boundaries',async({request},info)=>{
 const ready=await (await request.get(origin+'/ready')).json();expect(ready.interactive_solver).toBe(false);
 const catalog=await (await request.get(origin+'/api/v2/operator/scenarios')).json();
 const samples:{scenario:string;milliseconds:number}[]=[];
 for(let i=0;i<5;i++)for(const scenario of catalog.scenarios){
  const start=performance.now();
  const response=await request.post(origin+'/api/v2/operator/compare',{data:{scenario_id:scenario.scenario_id,scenario_fingerprint:scenario.scenario_fingerprint,include_experimental:true}});
  expect(response.status()).toBe(200);const value=await response.json();
  expect(value.recommended_policy).toBe('legacy-release-per-person-hour-adapter-v1');
  const milliseconds=performance.now()-start;samples.push({scenario:scenario.scenario_id,milliseconds});
  expect(milliseconds).toBeLessThan(5000);
 }
 for(const path of ['/docs','/openapi.json','/api/evaluate','/data/raw/','/backend/review.py','/__test__/worker/1'])
  expect((await request.get(origin+path)).status()).toBe(404);
 expect((await request.post(origin+'/api/v2/operator/compare',{data:{secret:'g8-request-body-must-not-be-logged'}})).status()).toBe(422);
 expect(logs).not.toContain('g8-request-body-must-not-be-logged');
 await writeFile(info.outputPath('http-latency.json'),JSON.stringify({samples,interactive_solver:false,budget_ms:5000},null,2));
 await writeFile(info.outputPath('server.log'),logs);
});

test('integrated overview renders only approved milestones and preserves customer/operator boundaries',async({page,request})=>{
 const frames=(await (await request.get('/preparedness/frames.json')).json()).frames;
 const forbidden:string[]=[];
 page.on('request',r=>{if(/\/api\/(evaluate|locations|map|explain|restoration-plan)/.test(r.url()))forbidden.push(r.url());});
 await page.goto('/');
 for(const f of frames){
  await page.getByRole('combobox',{name:'Fictional scenario',exact:true}).selectOption(f.scenario_id);
  await page.getByRole('combobox',{name:'Prepared milestone',exact:true}).selectOption(String(f.step));
  await expect(page.getByRole('region',{name:'Selected fictional result'})).toContainText(`${f.elapsed_hours} conditional elapsed hours`);
  await expect(page.getByTestId('fictional-completion')).toContainText(f.completion_hours===null?'Completion unresolved':`${f.completion_hours} modeled hours`);
  for(const customer of f.customers){
   const list=page.getByRole('list',{name:customer.label+' ordered upstream dependencies'});
   expect(await list.getByRole('button').count()).toBe(customer.asset_ids.length);
  }
 }
 await page.getByRole('combobox',{name:'Fictional scenario',exact:true}).selectOption('syn-blocked');
 await page.getByRole('button',{name:'What does this timing mean?',exact:true}).click();
 await expect(page.locator('.standard-answer')).toContainText('No finite restoration time can be inferred');
 await page.getByRole('combobox',{name:'Fictional scenario',exact:true}).selectOption('syn-simple');
 await expect(page.locator('.standard-answer')).toContainText('Select a question');
 await page.getByRole('combobox',{name:'Prepared milestone',exact:true}).selectOption('1');
 await page.getByRole('button',{name:'What is holding up release?',exact:true}).click();
 await expect(page.locator('.standard-answer')).toContainText('Fictional simple path · Modeled milestone 1');
 await page.getByRole('link',{name:'Prepare now',exact:true}).click();
 await expect(page.getByRole('combobox',{name:'Fictional scenario',exact:true})).toHaveValue('syn-simple');
 await expect(page.getByRole('combobox',{name:'Prepared milestone',exact:true})).toHaveValue('1');
 await page.getByRole('button',{name:'Save this demo snapshot'}).click();
 await expect(page.getByText('Fictional snapshot saved explicitly',{exact:false})).toBeVisible();
 const saved=await page.evaluate(()=>JSON.parse(localStorage.getItem('gridguide.preparedness.snapshot.v1')!));
 expect(saved.frame.result_fingerprint).toBe(frames.find((f:any)=>f.scenario_id==='syn-simple'&&f.step===1).result_fingerprint);
 await page.getByRole('navigation',{name:'Main navigation'}).getByRole('link',{name:'Grid insights',exact:true}).click();
 await expect(page.getByText('These cases are separate',{exact:false})).toBeVisible();
 await expect(page.getByRole('combobox',{name:'Fictional scenario',exact:true})).toHaveValue('syn-micro-weighted');
 await expect(page.getByRole('combobox',{name:'Selected policy'})).toHaveValue('legacy-release-per-person-hour-adapter-v1');
 expect(forbidden).toEqual([]);
});

test('overview withholds invalid or disconnected evidence and retries without a source fallback',async({page})=>{
 await page.route('**/preparedness/frames.json',async route=>{
  const response=await route.fetch();const data=await response.json();data.frames[0].completion_hours=0;
  await route.fulfill({json:data});
 });
 await page.goto('/#syn-simple/999');
 await expect(page.getByTestId('fictional-completion')).toContainText('Unavailable');
 await expect(page.getByRole('combobox',{name:'Fictional scenario',exact:true})).toBeDisabled();
 await expect(page.getByRole('button',{name:'Retry fictional results'})).toBeVisible();
 await page.unroute('**/preparedness/frames.json');
 await page.getByRole('button',{name:'Retry fictional results'}).click();
 await expect(page.getByRole('combobox',{name:'Prepared milestone',exact:true})).toHaveValue('0');
 await expect(page.getByTestId('fictional-completion')).toContainText('7 modeled hours');
 await page.evaluate(()=>window.dispatchEvent(new Event('offline')));
 await expect(page.getByRole('combobox',{name:'Fictional scenario',exact:true})).toBeDisabled();
 await expect(page.getByTestId('fictional-completion')).toContainText('Unavailable');
 expect(await page.evaluate(()=>localStorage.length)).toBe(0);
 await page.route('**/api/health',route=>route.fulfill({json:{ready:true,mode:'challenge-local'}}));
 await page.getByRole('button',{name:'Retry fictional results'}).click();
 await expect(page.getByRole('combobox',{name:'Fictional scenario',exact:true})).toBeDisabled();
 await expect(page.getByText('Fictional results unavailable:',{exact:false})).toBeVisible();
});

test('dashboard keyboard, responsive continuity and automatic accessibility checks',async({page},info)=>{
 const {default:AxeBuilder}=await import('@axe-core/playwright');
 for(const width of [1440,390,320]){
  await page.setViewportSize({width,height:width===1440?1000:844});
  await page.emulateMedia({reducedMotion:'reduce'});await page.goto('/');
  await expect(page.getByRole('combobox',{name:'Fictional scenario',exact:true})).toBeEnabled();
  await expect(page.getByRole('navigation',{name:'Main navigation'})).toBeVisible();
  const select=page.getByRole('combobox',{name:'Fictional scenario',exact:true});await select.focus();
  await page.keyboard.press('s');await page.keyboard.press('Enter');
  const dependency=page.getByRole('list',{name:'Fictional customer 1 ordered upstream dependencies'}).getByRole('button').first();
  await dependency.focus();await page.keyboard.press('Enter');await expect(dependency).toHaveAttribute('aria-pressed','true');
  await expect(page.locator('#path-inspection')).toContainText('Known here:');
  await page.getByRole('button',{name:'Why is risk unavailable?',exact:true}).click();
  await expect(page.locator('.standard-answer')).toContainText('evidence-bounded research No-Go');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  expect((await new AxeBuilder({page}).analyze()).violations.filter(v=>['serious','critical'].includes(v.impact??''))).toEqual([]);
  await page.screenshot({path:info.outputPath(`overview-${width}.png`),fullPage:true});
 }
});
