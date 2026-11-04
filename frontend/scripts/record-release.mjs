// Unedited production browser footage. No request interception or product changes.
import {chromium,expect} from '@playwright/test';
import {spawn,execFileSync} from 'node:child_process';
import {mkdir,writeFile,readFile,unlink} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {createHash} from 'node:crypto';
const root=process.env.GRIDGUIDE_PACKAGE,python=process.env.GRIDGUIDE_PUBLIC_PYTHON;
if(!root||!python||!process.env.GG_RECORD_DIR)throw Error('Explicit immutable package, Python and output required');
const out=resolve(process.env.GG_RECORD_DIR);await mkdir(out,{recursive:true});
const origin='http://127.0.0.1:18190';let server,browser,context;const shots=[];const checks=[];
async function boot(){
 server=spawn(python,[join(root,'deploy/serve.py')],{cwd:root,env:{PATH:process.env.PATH,PORT:'18190',PYTHONDONTWRITEBYTECODE:'1'},stdio:'ignore'});
 await expect.poll(async()=>{if(server.exitCode!==null)throw Error('Package exited');try{return(await fetch(origin+'/ready')).status;}catch{return 0;}},{timeout:20000}).toBe(200);
}
async function stop(){if(server&&server.exitCode===null&&server.signalCode===null){const done=new Promise(r=>server.once('exit',r));server.kill('SIGTERM');await Promise.race([done,new Promise((_,reject)=>setTimeout(()=>reject(Error('Shutdown timeout')),10000).unref())]);}}
const stamp=t=>new Date(Math.round(t*1000)).toISOString().slice(11,23);
try{
 await boot();browser=await chromium.launch({channel:process.env.CI?undefined:'chrome',headless:true});
 context=await browser.newContext({viewport:{width:1280,height:800},recordVideo:{dir:out,size:{width:1280,height:800}},acceptDownloads:true});
 const page=await context.newPage();const epoch=Date.now();
 async function shot(name,caption,seconds=17){
  await page.evaluate(()=>document.fonts.ready);
  const start=(Date.now()-epoch)/1000;await page.screenshot({path:join(out,name+'.png')});
  await new Promise(r=>setTimeout(r,seconds*1000));shots.push({name,caption,start,end:(Date.now()-epoch)/1000});console.log(name);
 }
 const scenario=()=>page.getByRole('combobox',{name:'Fictional scenario',exact:true});
 const milestone=()=>page.getByRole('combobox',{name:'Prepared milestone',exact:true});
 const nav=()=>page.getByRole('navigation',{name:'Main navigation'});
 const acknowledge=async()=>{await expect(page.getByRole('group',{name:'Explicit human acknowledgements'}).getByRole('checkbox')).toHaveCount(5);for(const c of await page.getByRole('group',{name:'Explicit human acknowledgements'}).getByRole('checkbox').all())await c.check();await page.getByRole('button',{name:'Mark reviewed in demo and prepare export'}).click();await expect(page.getByRole('heading',{name:'Reviewed in demo',exact:true})).toBeVisible();};
 await page.goto(origin+'/');await expect(scenario()).toBeEnabled();await expect(page).toHaveURL(origin+'/');checks.push('production root is integrated dashboard');
 await shot('01-overview','GridGuide 1.1.0: the integrated Overview, Prepare & alerts and Grid insights journey. Independently authored fiction; no live utility connection.',20);
 await scenario().selectOption('syn-branching');await milestone().selectOption('1');await page.locator('#scenario-controls').scrollIntoViewIfNeeded();
 await shot('02-scenario','Select an approved fictional scenario and prepared milestone. Timing is a conditional Python-owned schedule, not a measured restoration outcome or confidence interval.',18);
 await scenario().selectOption('syn-simple');await milestone().selectOption('2');
 await page.getByRole('list',{name:'Fictional customer 1 ordered upstream dependencies'}).getByRole('button',{name:/Transformer/}).click();await page.locator('#path-inspection').scrollIntoViewIfNeeded();
 await shot('03-completed','Completed means declared dependency repairs are complete at this fictional milestone. The schematic has no geographic coordinates and is not utility-confirmed connectivity.');
 await scenario().selectOption('syn-blocked');await page.getByRole('list',{name:'Fictional customer 1 ordered upstream dependencies'}).getByRole('button').first().click();await page.locator('#path-inspection').scrollIntoViewIfNeeded();
 await shot('04-blocked','Blocked clearance remains unknown. Full completion is unresolved; GridGuide never converts unknown completion into a finite utility ETR.');
 await scenario().selectOption('syn-missing');await page.getByRole('list',{name:'Fictional customer 1 ordered upstream dependencies'}).getByRole('button').first().click();await page.locator('#path-inspection').scrollIntoViewIfNeeded();
 await shot('05-unresolved','Missing evidence stays unresolved. Approved fictional definitions support this educational path, not real locations, household predictions or inferred facility attachments.');
 await scenario().selectOption('syn-simple');await milestone().selectOption('1');await page.getByRole('button',{name:'What does this timing mean?',exact:true}).click();await page.locator('.standard-answer').scrollIntoViewIfNeeded();
 await shot('06-explanation','Ask GridGuide renders a deterministic explanation bound to this selected milestone. No external AI or browser calculation is required.',15);
 await page.getByRole('button',{name:'Why is risk unavailable?',exact:true}).click();await page.locator('.standard-answer').scrollIntoViewIfNeeded();
 await shot('07-risk','Household predictive risk is unavailable. G4 remains an evidence-bounded No-Go. Live maps, custom crew edits, alerts and G5 interval visualization are not implemented publicly.',15);
 await page.getByRole('link',{name:'Prepare now',exact:true}).click();await expect(scenario()).toHaveValue('syn-simple');await expect(milestone()).toHaveValue('1');checks.push('Overview handoff preserves syn-simple milestone 1');
 await page.locator('.frame-summary').scrollIntoViewIfNeeded();await shot('08-handoff','Prepare now preserves the exact approved scenario and milestone. Prepare & alerts provides generic safety guidance and snapshots; tailored communications require authorized challenge-local inputs.',18);
 await page.getByRole('button',{name:'Enable or check offline kit'}).click();await expect(page.getByText('Offline kit ready on this device',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Save this demo snapshot'}).click();await expect(page.getByText('Fictional snapshot saved explicitly',{exact:false})).toBeVisible();
 await page.reload();await stop();await expect(fetch(origin+'/ready')).rejects.toThrow();await context.setOffline(true);await page.goto(origin+'/preparedness/');await page.getByRole('button',{name:'Open saved snapshot'}).click();await expect(page.getByText('Historical fictional snapshot',{exact:true})).toBeVisible();await expect(milestone()).toBeDisabled();await page.locator('.historical').scrollIntoViewIfNeeded();checks.push('real service stopped; networking disabled; cached kit and historical snapshot recovered');
 await shot('09-offline','The actual service is stopped and browser networking is disabled. Only cached preparedness and the explicitly saved historical snapshot remain. Storage can be evicted; this is not live outage awareness.',25);
 await boot();await context.setOffline(false);await page.getByRole('button',{name:'Reconnect and refresh'}).click();await expect(scenario()).toBeEnabled();await nav().getByRole('link',{name:'Grid insights',exact:true}).click();await expect(page.getByRole('heading',{name:'2. Compare identical assumptions'})).toBeVisible();await expect(page.getByRole('combobox',{name:'Selected policy'})).toHaveValue('legacy-release-per-person-hour-adapter-v1');checks.push('Preparedness to operator navigation; fixed baseline default');
 await scenario().selectOption('syn-micro-critical');await page.locator('.comparison-scroll').scrollIntoViewIfNeeded();
 await shot('10-policies','Four baselines compare identical inputs in a separate fictional operator case. Completed and restricted-horizon customer-hours differ in meaning; unresolved and censored outcomes remain visible.',20);
 await page.getByRole('combobox',{name:'Selected policy'}).selectOption('legacy-critical-proxy-first-adapter-v1');await page.getByLabel('Selected policy tradeoffs').scrollIntoViewIfNeeded();
 await shot('11-tradeoff','Critical-first improves one critical-service latency while worsening customer-hours. Fairness tradeoffs remain visible. The strongest fixed baseline stays default; optional CP-SAT remains experimental after its failed promotion target.',20);
 await scenario().selectOption('syn-micro-weighted');await acknowledge();await page.getByRole('heading',{name:'Reviewed in demo',exact:true}).scrollIntoViewIfNeeded();
 await shot('12-reviewed','Explicit acknowledgements mark this fictional comparison reviewed. Changing settings or a constraint must invalidate this review; no dispatch or utility approval occurs.',12);
 await page.getByRole('button',{name:'Add precedence and recompute'}).click();await expect(page.getByRole('heading',{name:'Reviewed in demo',exact:true})).toHaveCount(0);await expect(page.locator('.selected-plan')).toContainText('18000');await expect(page.getByRole('button',{name:'Mark reviewed in demo and prepare export'})).toBeDisabled();await page.locator('.selected-plan').scrollIntoViewIfNeeded();checks.push('supported precedence recomputed; prior review and acknowledgements invalidated');
 await shot('13-override','A supported precedence override is recomputed and independently validated in Python. The previous review disappeared; fresh acknowledgements are required. A constraint can worsen modeled outcomes.',17);
 await acknowledge();const pending=page.waitForEvent('download');await page.getByRole('button',{name:'Download review JSON'}).click();const exported=join(out,'review.json');await(await pending).saveAs(exported);
 await shot('14-export','The actual downloaded JSON contains this reviewed fictional case. Checksums establish internal consistency, not authenticated reviewer identity or tamper-proof audit history.',15);
 const transcript=execFileSync(python,[join(root,'scripts/replay_review.py'),exported],{cwd:root,env:{PATH:process.env.PATH,PYTHONDONTWRITEBYTECODE:'1'},encoding:'utf8'});
 await writeFile(join(out,'replay.txt'),'Python CLI replay of the actual downloaded review.json\n\n'+transcript);await page.goto('file://'+join(out,'replay.txt'));checks.push('downloaded JSON independently replayed with exit 0');
 await shot('15-replay','Actual Python CLI output from replaying the downloaded JSON. Replay recomputes and validates the record; it does not train a model or rerun CP-SAT.',18);
 await page.goto(origin+'/');await expect(scenario()).toBeEnabled();
 await shot('16-closing','A reproducible fictional portfolio, not operational utility software. Start with docs/REPRODUCING_V1_1.md and run the inspected package via python deploy/serve.py. Hosting needs separate security review and authorization.',15);
 const video=page.video();const original=await video.path();await context.close();context=null;await video.saveAs(join(out,'gridguide-1.1.0-integrated.webm'));if(original!==join(out,'gridguide-1.1.0-integrated.webm'))await unlink(original);
 const mobile=await browser.newContext({viewport:{width:390,height:844}});const m=await mobile.newPage();
 for(const [name,path] of [['mobile-overview','/'],['mobile-preparedness','/preparedness/'],['mobile-operator','/operator/']]){await m.goto(origin+path);if(path==='/operator/')await expect(m.getByRole('heading',{name:'2. Compare identical assumptions'})).toBeVisible();else await expect(m.getByRole('combobox',{name:'Fictional scenario',exact:true})).toBeEnabled();await m.evaluate(()=>document.fonts.ready);await m.screenshot({path:join(out,name+'.png')});}await mobile.close();
 const source=await readFile(new URL(import.meta.url));const manifest=await readFile(join(root,'PUBLIC_MANIFEST.json'));
 await writeFile(join(out,'shots.json'),JSON.stringify({application_commit:'3c53d8e9429318f121c210d148f7d2b35ae52147',capture:'native unedited Playwright browser footage; silent',browser:await browser.version(),viewport:[1280,800],capture_script_sha256:createHash('sha256').update(source).digest('hex'),package_manifest_sha256:createHash('sha256').update(manifest).digest('hex'),checks,shots},null,2)+'\n');
 await writeFile(join(out,'captions.vtt'),'WEBVTT\n\n'+shots.map((s,i)=>`${i+1}\n${stamp(s.start)} --> ${stamp(s.end)}\n${s.caption}\n`).join('\n'));console.log(JSON.stringify({shots:shots.length,seconds:shots.at(-1).end}));
}finally{if(context)await context.close();if(browser)await browser.close();await stop();}
