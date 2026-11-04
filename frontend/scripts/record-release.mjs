// Authentic, silent browser footage; no generated UI, mocked APIs or edited results.
// Run from frontend with GRIDGUIDE_PACKAGE, GRIDGUIDE_PUBLIC_PYTHON and GG_RECORD_DIR.
import {chromium,expect} from '@playwright/test';
import {spawn,execFileSync} from 'node:child_process';
import {mkdir,writeFile,rename} from 'node:fs/promises';
import {resolve,join} from 'node:path';
const root=process.env.GRIDGUIDE_PACKAGE,python=process.env.GRIDGUIDE_PUBLIC_PYTHON;
if(!root||!python||!process.env.GG_RECORD_DIR)throw Error('Explicit immutable package, Python and recording output required');
const out=resolve(process.env.GG_RECORD_DIR);await mkdir(out,{recursive:true});
const origin='http://127.0.0.1:18190';
let server;let context;const shots=[];let epoch;
async function boot(){
 server=spawn(python,[join(root,'deploy/serve.py')],{cwd:root,env:{PATH:process.env.PATH,PORT:'18190',PYTHONDONTWRITEBYTECODE:'1'},stdio:'ignore'});
 await expect.poll(async()=>{try{return(await fetch(origin+'/ready')).status;}catch{return 0;}},{timeout:20000}).toBe(200);
}
async function stop(){if(server&&server.exitCode===null&&server.signalCode===null){const done=new Promise(r=>server.once('exit',r));server.kill('SIGTERM');await done;}}
function timestamp(t){return new Date(Math.round(t)*1000).toISOString().slice(11,23);}
try{
 await boot();const browser=await chromium.launch({channel:process.env.CI?undefined:'chrome',headless:true});
 context=await browser.newContext({viewport:{width:1280,height:800},recordVideo:{dir:out,size:{width:1280,height:800}},acceptDownloads:true});
 const page=await context.newPage();epoch=Date.now();
 async function shot(name,caption,seconds=25){
  const start=(Date.now()-epoch)/1000;await page.screenshot({path:join(out,name+'.png')});
  await new Promise(r=>setTimeout(r,seconds*1000));shots.push({name,caption,start,end:(Date.now()-epoch)/1000});
 }
 await page.goto(origin+'/');await expect(page.getByRole('button',{name:'Save this demo snapshot'})).toBeEnabled();
 await shot('01-introduction','GridGuide 1.1.0 release candidate. Independently authored fictional examples, not live utility observations. No deployment or safety certification.',20);
 await page.locator('.fictional-area').scrollIntoViewIfNeeded();
 await page.getByRole('list',{name:'Fictional customer 1 ordered upstream dependencies'}).getByRole('button',{name:/Transformer/}).click();
 await shot('02-path','Declared power paths distinguish repair prerequisites from customer dependencies. Python prepared these milestone results.');
 await page.getByLabel('Prepared milestone').selectOption('2');
 await shot('03-completed','Completed means the fictional dependency repairs are complete at this modeled milestone. It does not mean utility-confirmed restoration.');
 await page.getByRole('combobox',{name:/^Fictional scenario/}).selectOption('syn-blocked');
 await shot('04-blocked','Blocked access has unknown clearance. Full modeled completion stays unavailable; it is never converted to a finite ETR.');
 await page.getByRole('combobox',{name:/^Fictional scenario/}).selectOption('syn-missing');
 await shot('05-unresolved','Unresolved evidence stays visible. No validated outage probability or empirically calibrated restoration confidence is available.');
 await page.goto(origin+'/operator/');
 await expect(page.getByRole('heading',{name:'2. Compare identical assumptions'})).toBeVisible();
 await page.getByRole('combobox',{name:/^Fictional scenario/}).selectOption('syn-micro-critical');
 await page.getByRole('combobox',{name:'Selected policy',exact:true}).selectOption('legacy-critical-proxy-first-adapter-v1');
 await page.getByLabel('Selected policy tradeoffs').scrollIntoViewIfNeeded();
 await shot('06-tradeoff','Four policies use identical assumptions. Critical-first improves one critical latency but worsens total customer-hours. Release/person-hour remains the default; optional CP-SAT is frozen and experimental.');
 await page.getByRole('combobox',{name:/^Fictional scenario/}).selectOption('syn-micro-weighted');
 await page.getByRole('button',{name:'Add precedence and recompute'}).click();
 await expect(page.locator('.selected-plan')).toContainText('18000');
 await page.locator('.selected-plan').scrollIntoViewIfNeeded();
 await shot('07-override','This supported precedence override is recomputed by Python and independently validated. Changing the scenario or review invalidates earlier acknowledgement.');
 for(const c of await page.getByRole('group',{name:'Explicit human acknowledgements'}).getByRole('checkbox').all())await c.check();
 await page.getByRole('button',{name:'Mark reviewed in demo and prepare export'}).click();
 await expect(page.getByRole('heading',{name:'Reviewed in demo',exact:true})).toBeVisible();
 const pending=page.waitForEvent('download');await page.getByRole('button',{name:'Download review JSON'}).click();
 const exported=join(out,'review.json');await(await pending).saveAs(exported);
 await shot('08-review','Explicit acknowledgements produce a reproducible fictional review record. Checksums establish consistency, not authenticated reviewer identity or tamper-proof history.');
 const command='python scripts/replay_review.py review.json';
 const transcript=execFileSync(python,[join(root,'scripts/replay_review.py'),exported],{cwd:root,env:{PATH:process.env.PATH,PYTHONDONTWRITEBYTECODE:'1'},encoding:'utf8'});
 const replay=join(out,'replay.txt');await writeFile(replay,command+'\n\n'+transcript);
 await page.goto('file://'+replay);await shot('09-replay','Actual CLI output from the downloaded JSON. Replay recomputes baselines and validates metrics; it does not rerun CP-SAT.',20);
 await page.goto(origin+'/preparedness/');await page.getByRole('button',{name:'Enable or check offline kit'}).click();
 await expect(page.getByText('Offline kit ready on this device',{exact:true})).toBeVisible();
 await page.getByRole('combobox',{name:/^Fictional scenario/}).selectOption('syn-missing');
 await page.getByRole('button',{name:'Save this demo snapshot'}).click();
 await expect(page.getByText('Fictional snapshot saved explicitly',{exact:false})).toBeVisible();
 await page.reload();await stop();await context.setOffline(true);await page.goto(origin+'/preparedness/');
 await page.getByRole('button',{name:'Open saved snapshot'}).click();
 await expect(page.getByText('Historical fictional snapshot',{exact:true})).toBeVisible();
 await expect(page.getByLabel('Prepared milestone')).toBeDisabled();
 await page.locator('.fictional-area').scrollIntoViewIfNeeded();
 await shot('10-offline','Actual server shutdown and browser networking disabled. Only the reviewed kit and explicitly saved historical fiction remain. No browser numerical engine or live outage awareness.',30);
 const video=page.video();await context.close();context=null;await video.saveAs(join(out,'gridguide-1.1.0-rc.webm'));await browser.close();
 await writeFile(join(out,'shots.json'),JSON.stringify({version:'1.1.0',capture:'actual release-candidate browser; silent, unedited',shots},null,2)+'\n');
 await writeFile(join(out,'captions.vtt'),'WEBVTT\n\n'+shots.map((s,i)=>`${i+1}\n${timestamp(s.start)} --> ${timestamp(s.end)}\n${s.caption}\n`).join('\n'));
 console.log(JSON.stringify({shots:shots.length,seconds:shots.at(-1).end,video:join(out,'gridguide-1.1.0-rc.webm')}));
}finally{if(context)await context.close();await stop();}
